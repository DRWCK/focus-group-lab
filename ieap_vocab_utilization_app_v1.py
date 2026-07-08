#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ieap_vocab_utilization_app_v1.py
================================
IEAP Vocabulary Utilization Tool — Streamlit app (v1)

Same workflow as every other lab tool: push to GitHub, open in Streamlit, run.
Upload a response CSV, get the vocabulary-utilization tables on screen plus
download buttons.

Measures how much of the sealed 1,897-term IEAP lexicon each agent uses, per
question. Keeps two counts strictly separate:
    OCCURRENCES  = token hits (counted every time a word appears)
    UNIQUE TYPES = distinct dictionary words used (counted once)

Word choice only, no meaning claim. Tokenizer and INT->AFF->ACT first-match
priority replicate syniq_core_v1_1_0 exactly, so occurrence counts line up
with the harvester's IEP scoring.

Sealed dictionary (V50_1897: 616 INT / 599 AFF / 682 ACT) is imported straight
from syniq_core_v1_1_0. Optional external lexicon can be uploaded to override.
"""

import io
import json
from collections import defaultdict

import pandas as pd
import streamlit as st

APP_VERSION = "ieap_vocab_utilization_app_v1"
IEP_DICTIONARY_VERSION = "V50_1897"

st.set_page_config(page_title="IEAP Vocabulary Utilization", layout="wide")


# ---------------------------------------------------------------------------
# Lexicon
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_sealed_lexicon():
    import syniq_core_v1_1_0 as core
    return (set(core.INT_WORDS), set(core.AFF_WORDS),
            set(core.ACT_WORDS), set(core.INT_PRIORITY))


def load_external_lexicon(upload):
    name = upload.name.lower()
    if name.endswith(".json"):
        d = json.load(upload)
        keymap = {k.upper(): k for k in d}
        INT = set(map(str.lower, d[keymap["INT"]]))
        AFF = set(map(str.lower, d[keymap["AFF"]]))
        ACT = set(map(str.lower, d[keymap["ACT"]]))
    else:
        df = pd.read_csv(upload)
        cols = {c.lower(): c for c in df.columns}
        wcol = cols.get("word") or cols.get("term") or df.columns[0]
        acol = cols.get("axis") or cols.get("class") or cols.get("iep") or df.columns[1]
        df[wcol] = df[wcol].astype(str).str.lower()
        df[acol] = df[acol].astype(str).str.upper().str[:3]
        INT = set(df.loc[df[acol] == "INT", wcol])
        AFF = set(df.loc[df[acol] == "AFF", wcol])
        ACT = set(df.loc[df[acol] == "ACT", wcol])
    return INT, AFF, ACT, set()


# ---------------------------------------------------------------------------
# Tokenizer + classifier (byte-for-byte match to syniq_core_v1_1_0.score_iep)
# ---------------------------------------------------------------------------
def tokenize(text):
    raw = str(text).lower().replace("'s", "").replace("'", "")
    raw = "".join(c if c.isalpha() or c == " " else " " for c in raw)
    return [w for w in raw.split() if len(w) > 1]


def classify(tokens, INT, AFF, ACT, PRIORITY):
    int_hits, aff_hits, act_hits = [], [], []
    for w in tokens:
        if w in PRIORITY:
            int_hits.append(w)
        elif w in INT:
            int_hits.append(w)
        elif w in AFF:
            aff_hits.append(w)
        elif w in ACT:
            act_hits.append(w)
    return int_hits, aff_hits, act_hits


# ---------------------------------------------------------------------------
# Column detection
# ---------------------------------------------------------------------------
def pick(colmap, *cands):
    for c in cands:
        if c in colmap:
            return colmap[c]
    return None


def detect_columns(df):
    colmap = {c.lower(): c for c in df.columns}
    agent = pick(colmap, "agent", "model", "ai")
    text = pick(colmap, "response_text", "response", "text", "output")
    ques = pick(colmap, "question_id", "question", "question_text", "qid")
    return agent, text, ques


# ---------------------------------------------------------------------------
# Computation
# ---------------------------------------------------------------------------
def build_records(df, agent_col, text_col, ques_col, LEX):
    INT, AFF, ACT, PRIORITY, DSIZE = LEX
    grouped = defaultdict(lambda: {"all_tokens": [], "int_hits": [], "aff_hits": [], "act_hits": []})
    for _, row in df.iterrows():
        q = str(row[ques_col]); a = str(row[agent_col])
        toks = tokenize(row[text_col])
        ih, ah, ch = classify(toks, INT, AFF, ACT, PRIORITY)
        g = grouped[(q, a)]
        g["all_tokens"].extend(toks); g["int_hits"].extend(ih)
        g["aff_hits"].extend(ah); g["act_hits"].extend(ch)

    q_agent_types = defaultdict(dict)
    records = []
    for (q, a), g in grouped.items():
        toks = g["all_tokens"]
        total_words = len(toks); unique_words = len(set(toks))
        ih, ah, ch = g["int_hits"], g["aff_hits"], g["act_hits"]
        occ = len(ih) + len(ah) + len(ch)
        int_types, aff_types, act_types = set(ih), set(ah), set(ch)
        iep_types = int_types | aff_types | act_types
        uniq_iep = len(iep_types)
        q_agent_types[q][a] = iep_types
        records.append({
            "question": q, "agent": a,
            "total_words": total_words, "unique_words": unique_words,
            "iep_occurrences": occ,
            "int_occurrences": len(ih), "aff_occurrences": len(ah), "act_occurrences": len(ch),
            "iep_pct_of_all_words": round(100 * occ / total_words, 3) if total_words else 0.0,
            "unique_iep_words": uniq_iep,
            "int_unique_words": len(int_types), "aff_unique_words": len(aff_types), "act_unique_words": len(act_types),
            "unique_iep_pct_of_unique_vocab": round(100 * uniq_iep / unique_words, 3) if unique_words else 0.0,
            "int_dict_coverage_pct": round(100 * len(int_types) / DSIZE["INT"], 3),
            "aff_dict_coverage_pct": round(100 * len(aff_types) / DSIZE["AFF"], 3),
            "act_dict_coverage_pct": round(100 * len(act_types) / DSIZE["ACT"], 3),
            "_int_types": int_types, "_aff_types": aff_types, "_act_types": act_types,
            "_vocab_types": set(toks),
        })

    for rec in records:
        q, a = rec["question"], rec["agent"]
        agents_here = q_agent_types[q]
        others = [t for oa, t in agents_here.items() if oa != a]
        my = agents_here[a]
        if others:
            uo = set().union(*others)
            rec["iep_words_shared_with_other_agents"] = len(my & uo)
            rec["iep_words_agent_specific"] = len(my - uo)
        else:
            rec["iep_words_shared_with_other_agents"] = 0
            rec["iep_words_agent_specific"] = len(my)
    return records


def per_agent_table(records, LEX):
    _, _, _, _, DSIZE = LEX
    by = defaultdict(lambda: {"total_words": 0, "vocab": set(), "iep": 0,
                              "int": set(), "aff": set(), "act": set(), "cells": 0})
    for r in records:
        b = by[r["agent"]]
        b["total_words"] += r["total_words"]; b["vocab"] |= r["_vocab_types"]
        b["iep"] += r["iep_occurrences"]
        b["int"] |= r["_int_types"]; b["aff"] |= r["_aff_types"]; b["act"] |= r["_act_types"]
        b["cells"] += 1
    rows = []
    for a, b in by.items():
        iep_types = b["int"] | b["aff"] | b["act"]
        uw = len(b["vocab"]); ui = len(iep_types)
        rows.append({
            "agent": a, "n_question_cells": b["cells"], "total_words": b["total_words"],
            "iep_occurrences": b["iep"],
            "iep_pct_of_all_words": round(100 * b["iep"] / b["total_words"], 3) if b["total_words"] else 0.0,
            "unique_words": uw, "unique_iep_words": ui,
            "unique_iep_pct_of_unique_vocab": round(100 * ui / uw, 3) if uw else 0.0,
            "int_unique_words": len(b["int"]), "aff_unique_words": len(b["aff"]), "act_unique_words": len(b["act"]),
            "int_dict_coverage_pct": round(100 * len(b["int"]) / DSIZE["INT"], 3),
            "aff_dict_coverage_pct": round(100 * len(b["aff"]) / DSIZE["AFF"], 3),
            "act_dict_coverage_pct": round(100 * len(b["act"]) / DSIZE["ACT"], 3),
            "total_dict_coverage_pct": round(100 * ui / sum(DSIZE.values()), 3),
        })
    return pd.DataFrame(rows).sort_values("agent").reset_index(drop=True)


def iep_tfidf(df, agent_col, text_col, LEX, top_n=15):
    from sklearn.feature_extraction.text import TfidfVectorizer
    INT, AFF, ACT, PRIORITY, _ = LEX
    lex = INT | AFF | ACT
    axis_of = {}
    for w in lex:
        axis_of[w] = "AFF" if w in AFF else ("ACT" if w in ACT else "INT")
    for w in INT: axis_of[w] = "INT"
    for w in PRIORITY: axis_of[w] = "INT"
    docs, agents = [], []
    for a, sub in df.groupby(agent_col):
        toks = []
        for t in sub[text_col]:
            toks.extend(w for w in tokenize(t) if w in lex)
        docs.append(" ".join(toks)); agents.append(str(a))
    vocab = sorted(lex)
    vec = TfidfVectorizer(vocabulary=vocab, token_pattern=r"[a-z]+")
    X = vec.fit_transform(docs); terms = vec.get_feature_names_out()
    rows = []
    for i, a in enumerate(agents):
        row = X[i].toarray().ravel(); order = row.argsort()[::-1]; rank = 0
        for j in order:
            if row[j] <= 0: break
            rank += 1
            rows.append({"agent": a, "rank": rank, "term": terms[j],
                         "axis": axis_of.get(terms[j], "?"), "tfidf": round(float(row[j]), 5)})
            if rank >= top_n: break
    return pd.DataFrame(rows)


def make_heatmap_png(per_agent_df):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    axes = ["INT", "AFF", "ACT"]
    cols = ["int_dict_coverage_pct", "aff_dict_coverage_pct", "act_dict_coverage_pct"]
    agents = per_agent_df["agent"].tolist()
    M = per_agent_df[cols].to_numpy(dtype=float)
    fig, ax = plt.subplots(figsize=(1.6 + 1.1 * len(axes), 1.2 + 0.6 * len(agents)), dpi=300)
    fig.patch.set_facecolor("white"); ax.set_facecolor("white")
    im = ax.imshow(M, aspect="auto", cmap="viridis")
    ax.set_xticks(range(len(axes)), axes); ax.set_yticks(range(len(agents)), agents)
    ax.set_xlabel("IEAP axis"); ax.set_title("Dictionary utilization (% of sealed lexicon used)")
    for i in range(len(agents)):
        for j in range(len(axes)):
            v = M[i, j]
            ax.text(j, i, f"{v:.1f}", ha="center", va="center",
                    color="white" if v < M.max() * 0.6 else "black", fontsize=9)
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04); cbar.set_label("coverage %")
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=300, facecolor="white", bbox_inches="tight")
    plt.close(fig); buf.seek(0)
    return buf


def csv_bytes(df):
    return df.to_csv(index=False).encode("utf-8")


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
st.title("IEAP Vocabulary Utilization Tool")
st.caption(f"{APP_VERSION} · sealed dictionary {IEP_DICTIONARY_VERSION} "
           "· occurrences and unique word types kept separate · word choice only")

with st.sidebar:
    st.header("Inputs")
    resp_file = st.file_uploader("Response CSV", type=["csv"])
    st.markdown("---")
    st.subheader("Lexicon")
    use_external = st.checkbox("Use external lexicon (override sealed)", value=False)
    dict_file = None
    if use_external:
        dict_file = st.file_uploader("Lexicon JSON or CSV", type=["json", "csv"], key="dict")
    st.markdown("---")
    st.subheader("Optional outputs")
    want_tfidf = st.checkbox("IEAP-restricted TF-IDF distinctive terms", value=True)
    tfidf_top = st.number_input("Top N terms per agent", 5, 50, 15, step=5)
    want_heatmap = st.checkbox("Dictionary-utilization heatmap", value=True)

# Lexicon load
try:
    if use_external and dict_file is not None:
        INT, AFF, ACT, PRIORITY = load_external_lexicon(dict_file)
        dict_version = f"external:{dict_file.name}"
    else:
        INT, AFF, ACT, PRIORITY = load_sealed_lexicon()
        dict_version = IEP_DICTIONARY_VERSION
except Exception as e:
    st.error(f"Could not load lexicon: {e}")
    st.stop()

DSIZE = {"INT": len(INT), "AFF": len(AFF), "ACT": len(ACT)}
LEX = (INT, AFF, ACT, PRIORITY, DSIZE)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Lexicon", dict_version)
c2.metric("INT terms", DSIZE["INT"]); c3.metric("AFF terms", DSIZE["AFF"]); c4.metric("ACT terms", DSIZE["ACT"])

if resp_file is None:
    st.info("Upload a response CSV to begin. Needs an agent column, a text column "
            "(response_text / response / text), and a question column "
            "(question_id / question / question_text). Columns auto-detect.")
    st.stop()

df = pd.read_csv(resp_file)
agent_col, text_col, ques_col = detect_columns(df)
missing = [n for n, v in [("agent", agent_col), ("text", text_col), ("question", ques_col)] if v is None]
if missing:
    st.error(f"Could not find column(s) for: {missing}. Available: {list(df.columns)}")
    st.stop()

df[agent_col] = df[agent_col].replace({"Sophia": "ChatGPT"})
df = df[df[text_col].notna()].copy()
st.success(f"Loaded {len(df)} rows · agents: {sorted(df[agent_col].unique())} · "
           f"questions: {sorted(df[ques_col].astype(str).unique())}")

with st.spinner("Computing vocabulary utilization..."):
    records = build_records(df, agent_col, text_col, ques_col, LEX)
    summary = pd.DataFrame([{k: v for k, v in r.items() if not k.startswith("_")} for r in records])
    summary = summary.sort_values(["question", "agent"]).reset_index(drop=True)
    per_agent = per_agent_table(records, LEX)

stem = resp_file.name.rsplit(".", 1)[0]

st.header("Per-agent (pooled across questions)")
st.caption("Density = IEAP % of all words. Concentration = unique IEAP % of unique vocab. "
           "Both are volume-robust; raw coverage and unique counts rise with word count.")
st.dataframe(per_agent, use_container_width=True)
st.download_button("Download per-agent CSV", csv_bytes(per_agent),
                   file_name=f"{stem}_per_agent.csv", mime="text/csv")

st.header("Per question × agent")
st.dataframe(summary, use_container_width=True)
st.download_button("Download summary CSV", csv_bytes(summary),
                   file_name=f"{stem}_summary.csv", mime="text/csv")

if want_tfidf:
    st.header("IEAP-restricted TF-IDF distinctive terms")
    st.caption("Vocabulary locked to the sealed lexicon — every term shown is a dictionary word.")
    try:
        tf = iep_tfidf(df, agent_col, text_col, LEX, top_n=int(tfidf_top))
        st.dataframe(tf, use_container_width=True)
        st.download_button("Download TF-IDF CSV", csv_bytes(tf),
                           file_name=f"{stem}_tfidf.csv", mime="text/csv")
    except ImportError:
        st.warning("scikit-learn not installed; add it to requirements.txt for TF-IDF.")

if want_heatmap:
    st.header("Dictionary-utilization heatmap")
    try:
        png = make_heatmap_png(per_agent)
        st.image(png, caption="% of each axis lexicon used per agent (volume-sensitive)")
        st.download_button("Download heatmap PNG", png,
                           file_name=f"{stem}_heatmap.png", mime="image/png")
    except ImportError:
        st.warning("matplotlib not installed; add it to requirements.txt for the heatmap.")
