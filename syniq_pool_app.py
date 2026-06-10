#!/usr/bin/env python3
"""
syniq_pool_app.py  --  Streamlit app to pool SYN-IQ mapper CSVs into combined-n datasets.

Run:  streamlit run syniq_pool_app.py

Upload any mix of mapper_all_*.csv files (gradient runs and/or temp-by-temp runs).
The app separates by temperature, renumbers runs so they never collide, enforces the
validity guards (depth / question-set / header-delivery seam), reports achieved n per
cell, and offers one downloadable CSV per temperature.
"""
import io, os, re, hashlib
import pandas as pd
import streamlit as st

KEY = ["agent", "temperature", "depth", "question_id"]   # one "cell"

# ----------------------------- core logic (UI-independent) -----------------------------
def parse_version(name):
    m = re.search(r"_V(\d+)", os.path.basename(name))
    return int(m.group(1)) if m else None

def delivery_side(version):
    if version is None:
        return "unknown"
    return "concat" if version <= 50 else "system"   # V51 moved header -> system message

def load_uploaded(files):
    frames = []
    for f in files:
        df = pd.read_csv(f)
        name = getattr(f, "name", str(f))
        df["__source_file"] = os.path.basename(name)
        v = parse_version(name)
        df["__source_version"] = v
        df["__delivery"] = delivery_side(v)
        frames.append(df)
    return pd.concat(frames, ignore_index=True)

def validate(df):
    """Return (blocks, warns) lists of human-readable strings."""
    blocks, warns = [], []
    required = set(KEY + ["run", "response_text"])
    missing = required - set(df.columns)
    if missing:
        blocks.append(f"Missing required columns: {sorted(missing)}")
        return blocks, warns

    for (ag, tp), g in df.groupby(["agent", "temperature"]):
        depths = sorted(g["depth"].astype(str).unique())
        if len(depths) > 1:
            blocks.append(f"{ag}/{tp}: mixed depths {depths} — depth drives content, do not pool.")

        per_src = {s: frozenset(gs["question_id"].unique()) for s, gs in g.groupby("__source_file")}
        if len(set(per_src.values())) > 1:
            blocks.append(f"{ag}/{tp}: question sets differ across sources "
                          f"{ {k: len(v) for k, v in per_src.items()} }.")

        if str(tp).upper() != "NATIVE":   # NATIVE is delivery-invariant (empty header)
            sides = sorted(g["__delivery"].unique())
            real = [s for s in sides if s != "unknown"]
            if len(set(real)) > 1:
                blocks.append(f"{ag}/{tp}: mixes header-delivery sides {sides} "
                              f"(concat vs system) — the measured version seam. Keep separate or use one side.")
            if "unknown" in sides:
                warns.append(f"{ag}/{tp}: a source has no parseable version; cannot confirm delivery side.")

    h = df["response_text"].astype(str).map(lambda t: hashlib.md5(t.encode("utf-8", "ignore")).hexdigest())
    dups = int(h.duplicated(keep=False).sum())
    if dups:
        warns.append(f"{dups} rows share identical response_text with another row "
                     f"(possible double-loaded file or repeated draw). Inspect before trusting n.")
    return blocks, warns

def renumber(df):
    df = df.sort_values(KEY + ["__source_file", "run"]).copy()
    df["orig_run"] = df["run"]
    df["pooled_run"] = df.groupby(KEY).cumcount() + 1
    df["run"] = df["pooled_run"]
    return df

def n_table(df):
    t = (df.groupby(KEY)["pooled_run"].max().reset_index().rename(columns={"pooled_run": "n"}))
    return (t.groupby(["temperature", "agent"])["n"].agg(["min", "max"]).reset_index()
              .rename(columns={"min": "n_min", "max": "n_max"}))

def question_table(df, target_n):
    """Per-question achieved n: one row per agent x temperature x depth x question_id.

    This is the cell-level view -- it shows exactly how many runs each individual
    question got, so an over-counted (duplicated/padded) or under-counted question
    is visible instead of being averaged away in the agent x temperature roll-up.
    """
    t = (df.groupby(KEY)["pooled_run"].max()
           .reset_index().rename(columns={"pooled_run": "n"}))
    t = t.sort_values(["temperature", "agent", "question_id"]).reset_index(drop=True)
    def qstatus(n):
        if n == target_n: return "OK"
        return "LOW" if n < target_n else "OVER"
    t["status"] = t["n"].apply(qstatus)
    return t[["temperature", "agent", "depth", "question_id", "n", "status"]]

def drop_within_question_dupes(df):
    """Remove rows whose response_text is an exact duplicate of another row in the
    SAME cell (agent/temperature/depth/question_id). Returns (deduped_df, n_removed).

    This targets copy/paste padding -- re-running a question produces different text
    at non-zero temperature, so genuine extra runs are NOT removed here (they surface
    as an OVER count in the per-question table instead).
    """
    before = len(df)
    subset = KEY + ["response_text"]
    out = df.drop_duplicates(subset=subset, keep="first").reset_index(drop=True)
    return out, before - len(out)

def drop_truncated(df, min_words, agents=("Gemini",)):
    """Drop rows from the named agent(s) whose response is shorter than min_words.

    Targets the gemini-2.5-flash thinking-budget truncation (V56 era): thinking
    tokens ate maxOutputTokens, leaving ~15-word stubs. This is provenance-free --
    it catches any truncated Gemini row by length, regardless of tool_version, so a
    stray bad run can't slip through. Returns (clean_df, dropped_df).

    Word count is taken from total_words when present, else computed from response_text.
    """
    if "total_words" in df.columns:
        wc = df["total_words"].fillna(0)
    else:
        wc = df["response_text"].astype(str).str.split().map(len)
    is_target = df["agent"].astype(str).isin(agents)
    truncated = is_target & (wc < min_words)
    dropped = df[truncated].copy()
    clean = df[~truncated].reset_index(drop=True)
    return clean, dropped

def provenance(df):
    return (df.groupby(["temperature", "agent", "__source_version", "__source_file"])
              .size().reset_index(name="rows"))

# ----------------------------------- Streamlit UI -----------------------------------
st.set_page_config(page_title="SYN-IQ Pooler", layout="wide")
st.title("SYN-IQ Mapper Pooler")
st.caption("Combine gradient and temp-by-temp mapper CSVs into per-temperature, combined-n datasets.")

files = st.file_uploader("Drop mapper_all_*.csv files here",
                         type="csv", accept_multiple_files=True)

c1, c2 = st.columns(2)
target_n = c1.number_input("Target n (runs per question per cell)", min_value=1, value=50, step=10)
cap = c2.checkbox("Cap each cell at target n (truncate overshoot)", value=False)
dedupe = st.checkbox("Drop exact-duplicate responses within a question "
                     "(removes copy/paste padding before counting)", value=False)

g1, g2 = st.columns([1, 2])
drop_trunc = g1.checkbox("Drop truncated Gemini rows", value=True,
                         help="Removes Gemini responses shorter than the word floor "
                              "(the gemini-2.5-flash thinking-budget truncation). "
                              "Length-based, so it catches the bug regardless of version.")
min_words = g2.number_input("Truncation floor (words)", min_value=1, value=40, step=5,
                            help="Gemini rows under this length are treated as truncated. "
                                 "Healthy answers run 60–300 words; the bug produced ~15.")

if not files:
    st.info("Upload one or more CSVs to begin. The version is read from each filename (…_V48, _V50, …).")
    st.stop()

try:
    df = load_uploaded(files)
except Exception as e:
    st.error(f"Could not read uploads: {e}")
    st.stop()

blocks, warns = validate(df)

st.subheader("Validity checks")
if blocks:
    st.error("Blocking confounds — fix before using the output:")
    for b in blocks:
        st.markdown(f"- {b}")
else:
    st.success("All clear — no blocking confounds detected.")
for w in warns:
    st.warning(w)

if drop_trunc:
    df, dropped = drop_truncated(df, min_words)
    if len(dropped):
        st.error(f"Dropped {len(dropped)} truncated Gemini row(s) under {min_words} words "
                 f"(thinking-budget truncation — re-run these on V57).")
        rerun = (dropped.groupby(["temperature", "depth", "question_id"]).size()
                        .reset_index(name="rows_dropped"))
        st.caption("Gemini cells that lost rows and need re-running:")
        st.dataframe(rerun, use_container_width=True, hide_index=True)
    else:
        st.info(f"Truncation guard on: no Gemini rows under {min_words} words found.")

if dedupe:
    df, removed = drop_within_question_dupes(df)
    if removed:
        st.warning(f"Dropped {removed} exact-duplicate response row(s) within question cells "
                   f"before counting (copy/paste padding).")
    else:
        st.info("Dedupe on: no exact-duplicate responses found within any question cell.")

df = renumber(df)
if cap:
    df = df[df["pooled_run"] <= target_n]

st.subheader(f"Achieved n per agent × temperature (target = {target_n})")
nt = n_table(df)
def status(r):
    if r.n_min == r.n_max == target_n: return "OK"
    if r.n_max < target_n:             return "LOW"
    if r.n_min > target_n:             return "OVER"
    return "UNEVEN"
nt["n"] = nt.apply(lambda r: f"{int(r.n_min)}" if r.n_min == r.n_max else f"{int(r.n_min)}–{int(r.n_max)}", axis=1)
nt["status"] = nt.apply(status, axis=1)
st.dataframe(nt[["temperature", "agent", "n", "status"]], use_container_width=True, hide_index=True)

st.subheader(f"Achieved n per question (target = {target_n})")
st.caption("Cell-level count — each question_id shown separately so an over- or "
           "under-counted question can't hide inside the agent×temperature roll-up.")
qt = question_table(df, target_n)
st.dataframe(qt, use_container_width=True, hide_index=True)

overs = qt[qt["status"] == "OVER"]
lows = qt[qt["status"] == "LOW"]
if len(overs):
    st.warning("Over target (check for a duplicated/padded question — cap or dedupe to fix): "
               + ", ".join(f"{r.agent}/{r.temperature}/{r.question_id}=n{int(r.n)}"
                           for r in overs.itertuples()))
if len(lows):
    st.info("Under target (needs more runs): "
            + ", ".join(f"{r.agent}/{r.temperature}/{r.question_id}=n{int(r.n)}"
                        for r in lows.itertuples()))

with st.expander("Provenance (rows per source × temperature × agent)"):
    st.dataframe(provenance(df), use_container_width=True, hide_index=True)

st.subheader("Download pooled CSVs (one per temperature)")
if blocks:
    st.warning("Downloads are disabled while blocking confounds are present.")
else:
    cols = st.columns(max(1, df["temperature"].nunique()))
    for col, (tp, g) in zip(cols, df.groupby("temperature")):
        buf = io.StringIO()
        g.drop(columns=["pooled_run"]).to_csv(buf, index=False)
        col.download_button(f"pooled_{tp}.csv  ({len(g)} rows)",
                            data=buf.getvalue(), file_name=f"pooled_{tp}.csv",
                            mime="text/csv", use_container_width=True)
