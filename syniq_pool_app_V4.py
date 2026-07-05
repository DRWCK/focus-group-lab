#!/usr/bin/env python3
"""
syniq_pool_app.py  (V4)  --  Streamlit app to pool SYN-IQ mapper CSVs into combined-n datasets.

Run:  streamlit run syniq_pool_app.py

Upload any mix of mapper_all_*.csv files (gradient runs and/or temp-by-temp runs).
The app separates by temperature, renumbers runs so they never collide, enforces the
validity guards (depth / question-balance / header-delivery seam), reports achieved n per
cell, and exports the pooled data.

V4 changes:
  1. Question-balance guard now checks the unit that matters. The V3 guard compared
     question sets across SOURCE FILES within an agent/temperature cell, which falsely
     blocked one-question-per-file pooling (each single-question CSV trips it the moment
     a second is added). V4 removes that check and instead verifies, within each
     temperature/depth, that every AGENT covers the same question set. Source-file
     boundaries are irrelevant once pooled; a genuine gap (an agent missing a question)
     still blocks and now names the agent and the missing question_id.
     Depth and header-delivery guards are unchanged.

V3 changes (all four targeted fixes):
  1. Agent aliases are normalized on ingest -- any "Sophia" (case-insensitive) becomes
     "ChatGPT" before pooling, so the two never split into separate agents and the alias
     never reaches the output.
  2. Row-dropping fixed. The Gemini truncation guard is now OFF by default (so the default
     pool keeps every valid run), counts words from the actual response_text -- falling
     back to total_words only when it is a positive number -- and lists every row it would
     remove with its length, so a silent 20->4 collapse can no longer happen.
  3. __source_version is now reliably populated per row: the filename parser captures alpha
     suffixes (V48bb, not just V48), falls back to an in-CSV version column when the filename
     carries no tag, and writes the string "unknown" instead of NaN so the value never
     disappears from a groupby.
  4. No capping. All valid runs are pooled and the actual per-cell n is reported; target_n
     is used only to label cells OK / LOW / OVER, never to filter rows.

V2 (prior): output format choice -- one combined CSV or four split by temperature.
All validity guards, renumbering, and n-reporting are otherwise unchanged from V1/V2.
"""
import io, os, re, hashlib
import pandas as pd
import streamlit as st

KEY = ["agent", "temperature", "depth", "question_id"]   # one "cell"

# Agent name aliases, normalized on ingest (key is lower-cased/stripped).
AGENT_ALIASES = {"sophia": "ChatGPT"}

# In-CSV columns consulted for a harvester version when the filename carries no _V tag.
# (Deliberately excludes iep_dictionary_version, which is the dictionary version, not the
#  harvester version.)
VERSION_COLS = ["tool_version", "harvester_version", "version"]

# ----------------------------- core logic (UI-independent) -----------------------------
def normalize_agents(df):
    """Fold agent aliases (e.g. Sophia -> ChatGPT) before anything else sees the data."""
    if "agent" in df.columns:
        df["agent"] = df["agent"].apply(
            lambda a: AGENT_ALIASES.get(str(a).strip().lower(), a)
        )
    return df

def parse_version_tag(text):
    """Pull a version tag like '48', '48bb', '50' from a string (filename or cell value).

    Captures a trailing alpha suffix so V48bb is distinguished from V48. Case-insensitive
    on the leading 'V'. Returns None when nothing version-like is found.
    """
    if text is None:
        return None
    m = re.search(r"[_\b]?[vV](\d+[A-Za-z]*)", str(text))
    return m.group(1) if m else None

def version_num(tag):
    """Numeric part of a version tag, for the delivery-side decision. '48bb' -> 48."""
    if not tag:
        return None
    m = re.match(r"(\d+)", str(tag))
    return int(m.group(1)) if m else None

def delivery_side(num):
    """Where the mode-directive header was delivered for a given harvester version."""
    if num is None:
        return "unknown"
    return "concat" if num <= 50 else "system"   # V51 moved header -> system message

def detect_version(filename, df):
    """Best-effort harvester version for an uploaded file.

    Filename first (most reliable: ..._V48bb.csv), then an in-CSV version column, then
    'unknown'. Returns (label, num) where label is e.g. 'V48bb' or 'unknown'.
    """
    tag = parse_version_tag(os.path.basename(str(filename)))
    if tag is None:
        for c in VERSION_COLS:
            if c in df.columns:
                for v in df[c].dropna().astype(str).head(20):
                    t = parse_version_tag(v)
                    if t:
                        tag = t
                        break
            if tag:
                break
    if tag is None:
        return "unknown", None
    return f"V{tag}", version_num(tag)

def load_uploaded(files):
    frames = []
    for f in files:
        df = pd.read_csv(f)
        name = getattr(f, "name", str(f))
        df = normalize_agents(df)                       # fix #1: fold Sophia -> ChatGPT
        label, num = detect_version(name, df)           # fix #3: reliable version
        df["__source_file"] = os.path.basename(name)
        df["__source_version"] = label                  # string, never NaN
        df["__delivery"] = delivery_side(num)
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

        if str(tp).upper() != "NATIVE":   # NATIVE is delivery-invariant (empty header)
            sides = sorted(g["__delivery"].unique())
            real = [s for s in sides if s != "unknown"]
            if len(set(real)) > 1:
                blocks.append(f"{ag}/{tp}: mixes header-delivery sides {sides} "
                              f"(concat vs system) — the measured version seam. Keep separate or use one side.")
            if "unknown" in sides:
                warns.append(f"{ag}/{tp}: a source has no parseable version; cannot confirm delivery side.")

    # Balance that matters for pooling: within each temperature/depth, every agent
    # must cover the same set of questions. Source-file boundaries are irrelevant
    # once pooled (one-question-per-file is expected input).
    for (tp, dp), g in df.groupby(["temperature", "depth"]):
        per_agent = {ag: frozenset(ga["question_id"].unique()) for ag, ga in g.groupby("agent")}
        if len(set(per_agent.values())) > 1:
            full = frozenset().union(*per_agent.values())
            detail = "; ".join(
                f"{ag} missing {sorted(full - qs)}"
                for ag, qs in sorted(per_agent.items()) if qs != full
            )
            blocks.append(f"{tp}/{dp}: agents cover different question sets — {detail}.")

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

def word_count(df):
    """Robust per-row word count.

    Uses response_text (the source of truth) and only trusts total_words where it is a
    positive number. This stops the old bug where a present-but-zero/NaN total_words
    falsely flagged a long response as truncated.
    """
    text_wc = df["response_text"].astype(str).str.split().map(len)
    if "total_words" in df.columns:
        tw = pd.to_numeric(df["total_words"], errors="coerce")
        return tw.where(tw > 0, text_wc).astype(int)
    return text_wc.astype(int)

def find_truncated(df, min_words, agents=("Gemini",)):
    """Identify (do not yet drop) rows from the named agent(s) shorter than min_words.

    Targets genuine stubs (e.g. the gemini-2.5-flash thinking-budget truncation, ~15
    words). Length is taken from word_count() above, so it is robust to an empty
    total_words field. Returns a boolean mask aligned to df.index.
    """
    wc = word_count(df)
    is_target = df["agent"].astype(str).isin(agents)
    return is_target & (wc < min_words)

def provenance(df):
    return (df.groupby(["temperature", "agent", "__source_version", "__source_file"])
              .size().reset_index(name="rows"))

# ----------------------------------- Streamlit UI -----------------------------------
st.set_page_config(page_title="SYN-IQ Pooler", layout="wide")
st.title("SYN-IQ Mapper Pooler  (V4)")
st.caption("Combine gradient and temp-by-temp mapper CSVs into per-temperature, combined-n datasets. "
           "Export as one combined file or split by temperature. "
           "Sophia is folded into ChatGPT on ingest; all valid runs are pooled (no capping).")

files = st.file_uploader("Drop mapper_all_*.csv files here",
                         type="csv", accept_multiple_files=True)

target_n = st.number_input("Target n (runs per question per cell) — for OK/LOW/OVER labels only, "
                           "never used to filter", min_value=1, value=50, step=10)

dedupe = st.checkbox("Drop exact-duplicate responses within a question "
                     "(removes copy/paste padding before counting)", value=False)

g1, g2 = st.columns([1, 2])
drop_trunc = g1.checkbox("Drop truncated Gemini stubs", value=False,
                         help="OFF by default so every valid run is pooled. When on, removes "
                              "Gemini responses shorter than the stub floor (the gemini-2.5-flash "
                              "thinking-budget truncation). Length is measured from the actual "
                              "response text, and every removed row is listed with its length.")
min_words = g2.number_input("Stub floor (words)", min_value=1, value=20, step=5,
                            help="Only used when the guard above is on. Genuine stubs ran ~15 words; "
                                 "healthy answers run 60–300. Terse ACT-directive answers can be short, "
                                 "so keep this low to avoid eating valid runs.")

if not files:
    st.info("Upload one or more CSVs to begin. The harvester version is read from each "
            "filename (…_V48, _V48bb, _V50) or from an in-file version column if the name has none.")
    st.stop()

try:
    df = load_uploaded(files)
except Exception as e:
    st.error(f"Could not read uploads: {e}")
    st.stop()

# Surface the agent normalization so it is never silent.
if "agent" in df.columns and (df["__source_file"].notna().any()):
    st.caption("Agents after normalization: " + ", ".join(sorted(df["agent"].astype(str).unique())))

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

# --- truncation guard: identify, report, then (only if enabled) drop ---
if drop_trunc:
    mask = find_truncated(df, min_words)
    dropped = df[mask].copy()
    if len(dropped):
        dropped = dropped.assign(words=word_count(dropped))
        st.error(f"Dropping {len(dropped)} truncated Gemini stub(s) under {min_words} words.")
        show = dropped[["temperature", "depth", "question_id", "words", "__source_file"]] \
                   .sort_values(["temperature", "question_id", "words"])
        st.caption("Rows removed by the stub guard (inspect lengths — raise/lower the floor if any are valid):")
        st.dataframe(show, use_container_width=True, hide_index=True)
        df = df[~mask].reset_index(drop=True)
    else:
        st.info(f"Stub guard on: no Gemini rows under {min_words} words found.")
else:
    # Show what WOULD be flagged, without removing anything, so nothing is lost unknowingly.
    mask = find_truncated(df, min_words)
    if mask.any():
        st.info(f"Stub guard is off: keeping {int(mask.sum())} short Gemini row(s) "
                f"(under {min_words} words). Turn the guard on above to review/remove them.")

if dedupe:
    df, removed = drop_within_question_dupes(df)
    if removed:
        st.warning(f"Dropped {removed} exact-duplicate response row(s) within question cells "
                   f"before counting (copy/paste padding).")
    else:
        st.info("Dedupe on: no exact-duplicate responses found within any question cell.")

df = renumber(df)

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
    st.warning("Over target (check for a duplicated/padded question — dedupe to fix): "
               + ", ".join(f"{r.agent}/{r.temperature}/{r.question_id}=n{int(r.n)}"
                           for r in overs.itertuples()))
if len(lows):
    st.info("Under target (needs more runs): "
            + ", ".join(f"{r.agent}/{r.temperature}/{r.question_id}=n{int(r.n)}"
                        for r in lows.itertuples()))

with st.expander("Provenance (rows per source × temperature × agent)"):
    st.dataframe(provenance(df), use_container_width=True, hide_index=True)

st.subheader("Download pooled data")
if blocks:
    st.warning("Downloads are disabled while blocking confounds are present.")
else:
    out_mode = st.radio(
        "Output format",
        ["Single combined CSV (harvester format)",
         "Four CSVs split by temperature"],
        index=0,
        help="Single = one file with all conditions and a temperature column, exactly "
             "like a raw harvester output (flows straight into the analyzer). "
             "Split = one file per temperature (pooled_COLD.csv, pooled_NATIVE.csv, …).")

    out_df = df.drop(columns=["pooled_run"])

    if out_mode.startswith("Single"):
        buf = io.StringIO()
        out_df.to_csv(buf, index=False)
        st.download_button(
            f"pooled_combined.csv  ({len(out_df)} rows, "
            f"{out_df['temperature'].nunique()} conditions, "
            f"{out_df['agent'].nunique()} agents)",
            data=buf.getvalue(), file_name="pooled_combined.csv",
            mime="text/csv", use_container_width=True)
    else:
        cols = st.columns(max(1, out_df["temperature"].nunique()))
        for col, (tp, g) in zip(cols, out_df.groupby("temperature")):
            buf = io.StringIO()
            g.to_csv(buf, index=False)
            col.download_button(f"pooled_{tp}.csv  ({len(g)} rows)",
                                data=buf.getvalue(), file_name=f"pooled_{tp}.csv",
                                mime="text/csv", use_container_width=True)
