#!/usr/bin/env python3
"""
syniq_word_cloud_app.py — 4-panel per-agent word clouds from a pooled response CSV.

Run it:
    streamlit run syniq_word_cloud_app.py

Drop in a pooled CSV, pick a question + temperature, get a 4-panel cloud
(one per agent, pooled, stopwords removed). Download the figure as PNG.

Modes:
    raw         pooled word frequency per agent (shows what each agent talks about)
    distinctive TF-IDF-weighted across the 4 agent-docs (shows what separates them)

Input CSV needs at least: agent, question_id, temperature, response_text

Shares tokenizer + junk filter with syniq_word_list so the cloud and the
word-list table stay consistent.

Version: 1.0.0
"""

import io
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer

# ---------------------------------------------------------------------------
AGENT_ORDER = ["ChatGPT", "Claude", "Gemini", "Grok"]
JUNK = {"m", "s", "t", "re", "ve", "ll", "d",
        "don", "doesn", "isn", "didn", "wasn", "couldn", "wouldn", "shouldn",
        "aren", "weren", "hasn", "haven", "won", "ain"}
TOKEN_PATTERN = r"[A-Za-z][A-Za-z']+"
REQUIRED_COLS = ["agent", "question_id", "temperature", "response_text"]

# per-agent colormaps tuned to the existing figure (green/blue/purple/red on navy)
AGENT_CMAP = {"ChatGPT": "Greens", "Claude": "Blues", "Gemini": "Purples", "Grok": "Reds"}
BG = "#1b2433"

# extra stopwords: contraction fragments that survive tokenization
EXTRA_STOP = set(STOPWORDS) | JUNK


def order_agents(present):
    head = [a for a in AGENT_ORDER if a in present]
    tail = sorted(a for a in present if a not in AGENT_ORDER)
    return head + tail


def clean_freq(freq):
    """Drop junk / short / contraction-fragment tokens from a {word: weight} dict."""
    out = {}
    for w, v in freq.items():
        wl = w.lower()
        if len(wl) < 2 or wl in JUNK or wl in STOPWORDS:
            continue
        # strip a trailing 's contraction tail if present
        if wl.endswith("'s") or wl.endswith("'re") or wl.endswith("'ll") or wl.endswith("'ve") or wl.endswith("'t"):
            continue
        out[wl] = out.get(wl, 0) + float(v)
    return out


def agent_docs(cell, ordered):
    docs, agents, no_resp = [], [], []
    for a in ordered:
        texts = cell.loc[cell["agent"] == a, "response_text"].dropna().astype(str)
        joined = " ".join(t for t in texts if t.strip())
        if joined.strip():
            docs.append(joined)
            agents.append(a)
        else:
            no_resp.append(a)
    return docs, agents, no_resp


def raw_freqs(docs, agents):
    vec = CountVectorizer(stop_words="english", token_pattern=TOKEN_PATTERN, min_df=1, max_df=1.0)
    X = vec.fit_transform(docs).toarray()
    vocab = np.array(vec.get_feature_names_out())
    return {a: clean_freq(dict(zip(vocab, X[i]))) for i, a in enumerate(agents)}


def distinctive_freqs(docs, agents):
    vec = TfidfVectorizer(max_features=4000, stop_words="english", token_pattern=TOKEN_PATTERN,
                          min_df=1, max_df=1.0, sublinear_tf=True)
    X = vec.fit_transform(docs).toarray()
    vocab = np.array(vec.get_feature_names_out())
    out = {}
    for i, a in enumerate(agents):
        d = {w: s for w, s in zip(vocab, X[i]) if s > 0}
        out[a] = clean_freq(d)
    return out


def make_figure(freqs_by_agent, counts, ordered, question, temp, mode, max_words):
    n = len(ordered)
    fig, axes = plt.subplots(1, n, figsize=(6 * n, 6.5), facecolor=BG)
    if n == 1:
        axes = [axes]
    fig.suptitle(f"{question}  ·  {temp}  ·  pooled per agent  ·  {mode}",
                 color="white", fontsize=20, fontweight="bold", y=0.99)
    for ax, a in zip(axes, ordered):
        ax.set_facecolor(BG)
        ax.axis("off")
        ax.set_title(f"{a}  (n={counts.get(a, 0)})", color="white", fontsize=18, fontweight="bold", pad=12)
        freq = freqs_by_agent.get(a, {})
        if not freq:
            ax.text(0.5, 0.5, "(no responses)", color="white", ha="center", va="center", fontsize=16)
            continue
        wc = WordCloud(width=900, height=900, background_color=BG, colormap=AGENT_CMAP.get(a, "viridis"),
                       prefer_horizontal=0.9, max_words=max_words, relative_scaling=0.5,
                       stopwords=EXTRA_STOP).generate_from_frequencies(freq)
        ax.imshow(wc, interpolation="bilinear")
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    return fig


# ---------------------------------------------------------------------------
st.set_page_config(page_title="SYN-IQ Word Clouds", layout="wide")

APP_PASSWORD = "SYNIQ2026"
if not st.session_state.get("authed", False):
    st.title("SYN-IQ — Word Clouds")
    pw = st.text_input("Password", type="password")
    if st.button("Enter"):
        if pw == APP_PASSWORD:
            st.session_state["authed"] = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    st.stop()

st.title("SYN-IQ — Per-Agent Word Clouds")
st.caption("Drop in a pooled response CSV, pick a question + temperature, get a 4-panel cloud. "
           "Raw = what each agent talks about; distinctive = what separates them.")

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
    question = st.selectbox("Question", questions)
with c2:
    temp = st.selectbox("Temperature", temps, index=default_temp)
with c3:
    mode = st.radio("Mode", ["raw", "distinctive"], index=0)
with c4:
    max_words = st.slider("Max words / cloud", 40, 200, 120, step=20)

cell = df[(df["question_id"] == question) & (df["temperature"] == temp)]
if cell.empty:
    st.warning(f"[{question} / {temp}] no rows for this question × temperature cell.")
    st.stop()

docs, agents, no_resp = agent_docs(cell, universe)
counts = {a: int((cell["agent"] == a).sum()) for a in universe}

if len(agents) < 2:
    st.warning("Fewer than 2 agents with text in this cell — comparison is degenerate.")

if mode == "distinctive" and agents:
    freqs = distinctive_freqs(docs, agents)
elif agents:
    freqs = raw_freqs(docs, agents)
else:
    freqs = {}

fig = make_figure(freqs, counts, universe, question, temp, mode, max_words)
st.pyplot(fig)

buf = io.BytesIO()
fig.savefig(buf, format="png", dpi=300, facecolor=BG, bbox_inches="tight")
fname = f"{question}_{temp}_{mode}_clouds.png"
st.download_button("Download PNG (300 dpi)", buf.getvalue(), file_name=fname, mime="image/png")
