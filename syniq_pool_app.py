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
