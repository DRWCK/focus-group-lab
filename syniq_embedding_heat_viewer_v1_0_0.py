#!/usr/bin/env python3
"""
syniq_embedding_heat_viewer.py — make sentence embeddings legible.

Run it:
    streamlit run syniq_embedding_heat_viewer.py

The embedding is 384 numbers per sentence — you can't read those. This tool turns
them into something you CAN read: it paints each sentence of a response by how
strongly its meaning pulls toward each agent's centroid. Dark = strongly that
agent; pale = generic. It answers "can we see the embedding in the text?" — yes,
as heat on the sentences.

Three views, all from the same sentence embeddings:
  1. AGENT HEAT     — paint a response by cosine to ONE chosen agent's centroid.
  2. NEAREST AGENT  — paint each sentence by which centroid is closest, intensity
                      = margin (top - 2nd). This is the polysemy cascade made
                      visual: high margin = confident register assignment, low
                      margin = genuinely mixed. Bill's uncertainty-reduction idea,
                      read straight off the text.
  3. NEAR / FAR     — for a picked sentence, show the nearest and farthest
                      sentences in the whole corpus. Makes "close in embedding
                      space" a felt thing.

Centroids are built from sentence embeddings pooled per agent, in the SAME space
as the sentences being painted (all-MiniLM-L6-v2, matching the mapper harvester).

Input CSV needs at least: agent, question_id, temperature, response_text.

NOTE ON ENVIRONMENT: this needs the live embedder (sentence-transformers +
all-MiniLM-L6-v2). Run it where that model is available (the mapper / Streamlit
environment), not in a sandbox that can't download the weights.

Version: 1.0.0
"""

import re
import html
import numpy as np
import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
AGENT_ORDER = ["Claude", "ChatGPT", "Gemini", "Grok"]
REQUIRED_COLS = ["agent", "question_id", "temperature", "response_text"]
MODEL_NAME = "all-MiniLM-L6-v2"   # same engine as Mapper Analyzer SBERT path

# per-agent base hue (matches the word-cloud / mapper colour convention)
AGENT_RGB = {
    "Claude":  (59, 111, 176),    # blue
    "ChatGPT": (74, 157, 91),     # green
    "Gemini":  (142, 90, 168),    # purple
    "Grok":    (192, 57, 43),     # red
}
SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")


def order_agents(present):
    head = [a for a in AGENT_ORDER if a in present]
    tail = sorted(a for a in present if a not in AGENT_ORDER)
    return head + tail


def split_sentences(text):
    text = re.sub(r"\s+", " ", str(text)).strip()
    if not text:
        return []
    parts = [p.strip() for p in SENT_SPLIT.split(text) if p.strip()]
    # keep only sentences with at least 3 word-ish tokens (skip headers/bullets noise)
    return [p for p in parts if len(re.findall(r"[A-Za-z]+", p)) >= 3]


@st.cache_resource(show_spinner=False)
def load_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(MODEL_NAME)


def embed(sentences, _model):
    if not sentences:
        return np.zeros((0, 384), dtype=float)
    v = _model.encode(sentences, normalize_embeddings=True, show_progress_bar=False)
    return np.asarray(v, dtype=float)


@st.cache_data(show_spinner=True)
def build_corpus(df_records, temp):
    """Split every response into sentences, embed once, build per-agent centroids.
    Cached on (records, temp). Returns sentence table + centroids + embeddings."""
    df = pd.DataFrame(df_records)
    df = df[df["temperature"].astype(str).str.strip().str.upper() == temp.upper()]
    rows = []
    for _, r in df.iterrows():
        for s in split_sentences(r["response_text"]):
            rows.append({"agent": r["agent"], "question_id": r["question_id"], "sentence": s})
    sent_df = pd.DataFrame(rows)
    model = load_model()
    E = embed(sent_df["sentence"].tolist(), model)
    agents = order_agents(list(sent_df["agent"].unique()))
    cents = {}
    for a in agents:
        m = (sent_df["agent"] == a).values
        c = E[m].mean(axis=0)
        c = c / (np.linalg.norm(c) + 1e-9)
        cents[a] = c
    return sent_df, E, cents, agents


def cos_to_centroids(vecs, cents, agents):
    C = np.vstack([cents[a] for a in agents])          # (A, d)
    return vecs @ C.T                                  # (N, A)


def heat_span(text, rgb, intensity):
    """intensity in [0,1] -> background alpha; readable text."""
    a = 0.12 + 0.75 * float(np.clip(intensity, 0, 1))
    r, g, b = rgb
    fg = "#111" if a < 0.55 else "#fff"
    return (f'<span style="background-color: rgba({r},{g},{b},{a:.2f}); '
            f'color:{fg}; padding:1px 3px; border-radius:3px; line-height:2.1;">'
            f'{html.escape(text)}</span>')


# ---------------------------------------------------------------------------
st.set_page_config(page_title="SYN-IQ Embedding Heat", layout="wide")

APP_PASSWORD = "SYNIQ2026"
if not st.session_state.get("authed", False):
    st.title("SYN-IQ — Embedding Heat Viewer")
    pw = st.text_input("Password", type="password")
    if st.button("Enter"):
        if pw == APP_PASSWORD:
            st.session_state["authed"] = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    st.stop()

st.title("SYN-IQ — Embedding Heat Viewer  (v1.0.0)")
st.caption("Sentence embeddings, painted onto the text. Dark = the sentence's meaning "
           "pulls strongly toward that agent's centroid; pale = generic. Makes the "
           "384-number embedding legible sentence by sentence.")

uploaded = st.file_uploader("Pooled CSV (agent, question_id, temperature, response_text)", type=["csv"])
if uploaded is None:
    st.info("Upload a pooled response CSV to begin.")
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

temps = sorted(df["temperature"].dropna().astype(str).unique())
default_temp = temps.index("NATIVE") if "NATIVE" in temps else 0
temp = st.selectbox("Temperature (centroids built within this condition)", temps, index=default_temp)

records = df[REQUIRED_COLS].to_dict("records")
with st.spinner(f"Embedding sentences with {MODEL_NAME} ..."):
    sent_df, E, cents, agents = build_corpus(records, temp)

if sent_df.empty or len(agents) < 2:
    st.warning("Not enough sentences / agents at this temperature to build centroids.")
    st.stop()

st.success(f"{len(sent_df):,} sentences · agents: {', '.join(agents)} · centroids built in embedding space.")

mode = st.radio("View", ["Agent heat", "Nearest agent (margin = confidence)", "Near / far sentence"], index=1)

# choose a response to paint
questions = sorted(sent_df["question_id"].dropna().unique())
c1, c2 = st.columns(2)
with c1:
    q = st.selectbox("Question", questions)
with c2:
    paint_agent = st.selectbox("Response from agent", agents)

resp_pool = df[(df["question_id"] == q) &
               (df["temperature"].astype(str).str.strip().str.upper() == temp.upper()) &
               (df["agent"] == paint_agent)]["response_text"].dropna().tolist()
if not resp_pool:
    st.warning("No response for that question / agent / temperature.")
    st.stop()
idx = st.slider("Which response", 0, len(resp_pool) - 1, 0)
custom = st.text_area("…or paste your own text to paint (overrides the picked response)", height=100)
target_text = custom.strip() if custom.strip() else resp_pool[idx]

sents = split_sentences(target_text)
if not sents:
    st.warning("No scorable sentences in the selected text.")
    st.stop()
model = load_model()
V = embed(sents, model)
sims = cos_to_centroids(V, cents, agents)   # (N, A)

st.markdown("---")

if mode == "Agent heat":
    focus = st.selectbox("Paint toward which agent's centroid", agents,
                         index=agents.index(paint_agent))
    col = agents.index(focus)
    raw = sims[:, col]
    lo, hi = raw.min(), raw.max()
    inten = (raw - lo) / (hi - lo + 1e-9)
    rgb = AGENT_RGB.get(focus, (90, 90, 90))
    html_out = " ".join(heat_span(s, rgb, t) for s, t in zip(sents, inten))
    st.markdown(f"**{focus}-ness of each sentence** (dark = strongly {focus}):",)
    st.markdown(f'<div style="font-size:1.02rem;">{html_out}</div>', unsafe_allow_html=True)
    st.caption("Intensity is min–max scaled within this response, so it shows the "
               "relative pull across sentences, not an absolute score.")

elif mode.startswith("Nearest agent"):
    order = np.argsort(-sims, axis=1)
    top = order[:, 0]
    margin = sims[np.arange(len(sents)), top] - sims[np.arange(len(sents)), order[:, 1]]
    mlo, mhi = margin.min(), margin.max()
    minten = (margin - mlo) / (mhi - mlo + 1e-9)
    spans = []
    for s, ti, mi in zip(sents, top, minten):
        rgb = AGENT_RGB.get(agents[ti], (90, 90, 90))
        spans.append(heat_span(s, rgb, mi))
    st.markdown("**Nearest-agent per sentence** · colour = closest centroid · "
                "intensity = margin over 2nd place (confident vs mixed):")
    st.markdown(f'<div style="font-size:1.02rem;">{" ".join(spans)}</div>', unsafe_allow_html=True)
    leg = " &nbsp; ".join(
        f'<span style="background:rgba{AGENT_RGB[a]+(0.7,)}; color:#fff; padding:1px 6px; border-radius:3px;">{a}</span>'
        for a in agents)
    st.markdown(leg, unsafe_allow_html=True)
    st.caption("Pale sentences are register-ambiguous (small margin) — the sentence-level "
               "analogue of a polysemous word the cascade couldn't resolve.")

else:  # Near / far
    pick = st.selectbox("Pick a sentence from the response", list(range(len(sents))),
                        format_func=lambda i: sents[i][:90] + ("…" if len(sents[i]) > 90 else ""))
    qv = V[pick]
    allsim = E @ qv
    ownmask = sent_df["sentence"].values == sents[pick]
    allsim[ownmask] = -2  # exclude the sentence itself if present in corpus
    nn = int(np.argmax(allsim)); ff = int(np.argmin(np.where(allsim < -1.5, 2, allsim)))
    st.markdown("**Picked sentence**")
    st.info(sents[pick])
    a, b = st.columns(2)
    with a:
        st.markdown(f"**Nearest in corpus** · {sent_df.iloc[nn]['agent']} · cos={allsim[nn]:.3f}")
        st.success(sent_df.iloc[nn]["sentence"])
    with b:
        st.markdown(f"**Farthest in corpus** · {sent_df.iloc[ff]['agent']} · cos={allsim[ff]:.3f}")
        st.warning(sent_df.iloc[ff]["sentence"])
    st.caption("Nearest should read like a paraphrase; farthest like a different world. "
               "That gap is what 'similar embedding' means, in words.")
