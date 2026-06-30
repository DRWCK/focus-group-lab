#!/usr/bin/env python3
"""
syniq_word_list_app.py — Streamlit front-end for per-agent distinctive word lists.

Run it:
    streamlit run syniq_word_list_app.py

Then in the browser: drop in a pooled CSV, pick a question and temperature,
and read off each agent's distinctive words. Download the result as CSV.

Input CSV needs at least: agent, question_id, temperature, response_text

Version: 1.0.0 (app wrapper around syniq_word_list core logic)
"""

import io
import numpy as np
import pandas as pd
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer

# ---------------------------------------------------------------------------
AGENT_ORDER = ["ChatGPT", "Claude", "Gemini", "Grok"]
JUNK = {"m", "s", "t", "re", "ve", "ll", "d"}
TOKEN_PATTERN = r"[A-Za-z][A-Za-z']+"
REQUIRED_COLS = ["agent", "question_id", "temperature", "response_text"]


def order_agents(present):
    head = [a for a in AGENT_ORDER if a in present]
    tail = sorted(a for a in present if a not in AGENT_ORDER)
    return head + tail


def clean_pick(scores, vocab, topn):
    out = []
    for j in np.argsort(scores)[::-1]:
        sc = float(scores[j])
        if sc <= 0:
            break
        w = vocab[j]
        if len(w) < 2 or w in JUNK:
            continue
        out.append((w, sc))
        if len(out) >= topn:
            break
    return out


def build_agent_docs(cell, ordered_agents):
    docs_present, agents_present, no_response = [], [], []
    for a in ordered_agents:
        texts = cell.loc[cell["agent"] == a, "response_text"].dropna().astype(str)
        joined = " ".join(t for t in texts if t.strip())
        if joined.strip():
            docs_present.append(joined)
            agents_present.append(a)
        else:
            no_response.append(a)
    return docs_present, agents_present, no_response


def run_distinctive(docs, agents, topn):
    vec = TfidfVectorizer(
        max_features=4000, stop_words="english", token_pattern=TOKEN_PATTERN,
        min_df=1, max_df=1.0, sublinear_tf=True,
    )
    X = vec.fit_transform(docs).toarray()
    vocab = np.array(vec.get_feature_names_out())
    return {a: clean_pick(X[i], vocab, topn) for i, a in enumerate(agents)}


def run_raw(docs, agents, topn):
    vec = CountVectorizer(
        stop_words="english", token_pattern=TOKEN_PATTERN, min_df=1, max_df=1.0,
    )
    X = vec.fit_transform(docs).toarray()
    vocab = np.array(vec.get_feature_names_out())
    return {a: clean_pick(X[i].astype(float), vocab, topn) for i, a in enumerate(agents)}


def process_cell(df, question, temp, mode, topn, universe):
    cell = df[(df["question_id"] == question) & (df["temperature"] == temp)]
    if cell.empty:
        return [], {}, [], False
    docs, agents, no_response = build_agent_docs(cell, universe)
    if agents:
        results = run_distinctive(docs, agents, topn) if mode == "distinctive" else run_raw(docs, agents, topn)
    else:
        results = {}
    rows = []
    for a in universe:
        if a in no_response:
            continue
        for rank, (w, sc) in enumerate(results.get(a, []), start=1):
            rows.append({
                "question_id": question, "temperature": temp, "agent": a,
                "rank": rank, "word": w, "score": round(sc, 6),
            })
    return rows, results, no_response, True


# ---------------------------------------------------------------------------
st.set_page_config(page_title="SYN-IQ Word List", layout="wide")

# --- password gate -------------------------------------------------------
# NOTE: this controls access to the running app only. Anyone who has this
# .py file can read the password below in plain text. Not file-level security.
APP_PASSWORD = "SYNIQ2026"

if not st.session_state.get("authed", False):
    st.title("SYN-IQ — Word List")
    pw = st.text_input("Password", type="password")
    if st.button("Enter"):
        if pw == APP_PASSWORD:
            st.session_state["authed"] = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    st.stop()
# -------------------------------------------------------------------------

st.title("SYN-IQ — Per-Agent Distinctive Word List")
st.caption("Drop in a pooled response CSV, pick a question + temperature, read off each "
           "agent's driving words. This is the data behind the clouds.")

uploaded = st.file_uploader("Pooled CSV", type=["csv"])

if uploaded is None:
    st.info("Upload a CSV with columns: agent, question_id, temperature, response_text")
    st.stop()

try:
    df = pd.read_csv(uploaded)
except Exception as e:
    st.error(f"Could not read the CSV: {e}")
    st.stop()

missing = [c for c in REQUIRED_COLS if c not in df.columns]
if missing:
    st.error(f"CSV is missing required columns: {missing}")
    st.stop()

universe = order_agents(list(df["agent"].dropna().unique()))
questions = sorted(df["question_id"].dropna().unique())
temps = sorted(df["temperature"].dropna().unique())
default_temp = temps.index("NATIVE") if "NATIVE" in temps else 0

st.success(f"Loaded {len(df):,} rows · agents: {', '.join(universe)} · "
           f"{len(questions)} questions · {len(temps)} temperatures")

c1, c2, c3, c4 = st.columns([2, 1.5, 1.5, 1.5])
with c1:
    all_q = st.checkbox("All questions", value=False)
    question = st.selectbox("Question", questions, disabled=all_q)
with c2:
    temp = st.selectbox("Temperature", temps, index=default_temp)
with c3:
    mode = st.radio("Mode", ["distinctive", "raw"], index=0)
with c4:
    topn = st.slider("Words per agent", 5, 50, 20, step=5)

run_questions = questions if all_q else [question]

all_rows = []
any_ok = False
for q in run_questions:
    rows, results, no_response, ok = process_cell(df, q, temp, mode, topn, universe)
    if not ok:
        st.warning(f"[{q} / {temp}] no rows for this question × temperature cell.")
        continue
    any_ok = True
    all_rows.extend(rows)

    st.subheader(f"{q} / {temp}  ·  {mode}")
    present_count = len([a for a in universe if a not in no_response])
    if present_count < 2:
        st.warning("Fewer than 2 agents with text in this cell — comparison is degenerate.")

    cols = st.columns(len(universe))
    for col, a in zip(cols, universe):
        with col:
            st.markdown(f"**{a}**")
            if a in no_response:
                st.write("_(no responses)_")
            else:
                words = [w for w, _ in results.get(a, [])]
                st.write("\n".join(f"{i+1}. {w}" for i, w in enumerate(words)) or "_(none)_")

if any_ok and all_rows:
    out_df = pd.DataFrame(all_rows, columns=["question_id", "temperature", "agent", "rank", "word", "score"])
    st.divider()
    st.dataframe(out_df, use_container_width=True, hide_index=True)
    buf = io.StringIO()
    out_df.to_csv(buf, index=False)
    fname = f"words_{'ALL' if all_q else question}_{temp}_{mode}.csv"
    st.download_button("Download CSV", buf.getvalue(), file_name=fname, mime="text/csv")
