"""
syniq_experiencer_detector_v1.py — SYN-IQ Experiencer Detector (self-vs-projected affect)
==========================================================================================

For each affective word in a response, find its grammatical EXPERIENCER and
classify the attribution:  self  /  other  /  abstract.

Then report, per agent (and per question), what fraction of affective language is
*spoken-from* (self) vs *described-about* (other / abstract).

This is a MEANING / STANCE axis — deliberately separate from identity (function
words) and affect-type (the 23 sub-dimensions).

----------------------------------------------------------------------------------
DICTIONARY
    Affect word list = `AFF_WORDS` from `syniq_core` (the version-stable shim that
    re-exports syniq_core_v1_1_0.py, which hard-asserts len == 599). This is the
    single canonical source every tool in the stack uses — NOT an ast-extract of a
    mapper's embedded copy. If the core import fails on a stripped deployment, we
    fall back to ast-extracting `_IEP_AFF_WORDS` from SYNIQ_Mapper_Analyzer_V23.py.

METHOD
    1. Sentence-split each response; parse with spaCy en_core_web_sm.
    2. For each affective token, resolve its experiencer:
         - nsubj / nsubjpass of the governing verb            -> method "nsubj"
         - possessor of the affect-noun (my grief -> my)      -> method "possessor"
       BOUNDED FALLBACK (when the stance is hard to discover grammatically):
         - it / existential-there copular predicates          -> method "fallback_predicate"
         - bare nominalizations ("a sense of wonder")         -> method "fallback_nominalization"
           ...resolved to the nearest 1st/2nd-person pronoun in the same sentence;
           if none exists -> "unresolved" (counts as abstract).
    3. Classify the experiencer:
         1st person (I, me, my, we, us, our, myself...) -> SELF
         2nd/3rd animate (you, they, people, humans...) -> OTHER
         abstraction / inanimate / none                 -> ABSTRACT
    4. Aggregate per agent (and per question) into self/other/abstract proportions,
       cross-tabbed with the RESOLUTION METHOD so you can see how much of "self"
       came from clean grammar vs. from the fallback layer.

HONESTY RAILS (the point of the tool)
    * Coverage = % of affective tokens where an experiencer was actually found
      (anything not "unresolved"). Low coverage = soft result; we say so on screen.
    * n=20 per cell. Direction trustworthy, magnitudes soft — printed on every table.
    * Heuristic, not ground truth — built-in spot-check sampler dumps N random
      classifications with the sentence + chosen experiencer + method for hand review.

SCAFFOLD (identical to the rest of the suite)
    * st.secrets["app_password"] gate (fallback "SYNIQ2026")
    * NATIVE temperature lock
    * agent relabel Sophia -> ChatGPT
    * 600-dpi RGB TIFF figure export

SYNINT Team — Tennessee 🎹 CUZ Partnership
"""

import os
import io
import ast
import glob
import random
import datetime
from collections import defaultdict

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

# matplotlib + PIL only for the 600-dpi RGB TIFF export
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

# ----------------------------------------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------------------------------------
st.set_page_config(page_title="SYN-IQ Experiencer Detector", page_icon="🫧", layout="wide")

TOOL_VERSION = "experiencer_detector_v1"
NATIVE_LOCK = "NATIVE"
AGENT_RELABEL = {"Sophia": "ChatGPT"}
MIN_N_PER_CELL = 20

# Stance buckets
SELF, OTHER, ABSTRACT = "self", "other", "abstract"
METHODS = ["nsubj", "possessor", "fallback_predicate", "fallback_nominalization", "unresolved"]

FIRST_PERSON = {
    "i", "me", "my", "mine", "myself",
    "we", "us", "our", "ours", "ourselves",
}
SECOND_THIRD_ANIMATE = {
    "you", "your", "yours", "yourself", "yourselves",
    "they", "them", "their", "theirs", "themselves",
    "he", "him", "his", "himself",
    "she", "her", "hers", "herself",
    "people", "humans", "human", "one", "person", "persons",
    "someone", "somebody", "everyone", "everybody", "anyone", "anybody",
    "others", "another",
}
EXPLETIVE_SUBJ = {"it", "there", "this", "that"}


# ----------------------------------------------------------------------------------
# PASSWORD GATE  (copied verbatim from the suite scaffold)
# ----------------------------------------------------------------------------------
def check_password():
    """Password gate with persistent authentication."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.query_params.get("auth") == "granted":
        st.session_state.authenticated = True

    if st.session_state.authenticated:
        return True

    st.markdown("""
    <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
         color: white; padding: 2rem; border-radius: 10px; text-align: center;
         margin-bottom: 1rem; border: 1px solid #e94560;">
        <h1 style="color: #e94560;">🫧 SYN-IQ Experiencer Detector</h1>
        <p style="color: #a0a0a0;">Authorized Access Only</p>
    </div>
    """, unsafe_allow_html=True)

    password = st.text_input("Enter password:", type="password")

    if password:
        try:
            correct = st.secrets["app_password"]
        except (FileNotFoundError, KeyError, AttributeError):
            correct = "SYNIQ2026"

        if password == correct:
            st.session_state.authenticated = True
            st.query_params["auth"] = "granted"
            st.rerun()
        else:
            st.error("❌ Incorrect password.")

    st.markdown("""
    <div style="text-align: center; color: #a0a0a0; padding: 1rem; font-size: 0.8rem;">
        <em>SYNINT Team — Tennessee 🎹 CUZ Partnership</em>
    </div>
    """, unsafe_allow_html=True)
    return False


if not check_password():
    st.stop()


# ----------------------------------------------------------------------------------
# DICTIONARY  — canonical core import, ast fallback
# ----------------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def load_aff_words():
    """Return (AFF_WORDS:set, source:str). Core shim first; ast-extract V23 as fallback."""
    # 1) Canonical path — the version-stable shim every tool uses.
    try:
        from syniq_core import AFF_WORDS as CORE_AFF
        if isinstance(CORE_AFF, set) and len(CORE_AFF) >= 500:
            return set(w.lower() for w in CORE_AFF), f"syniq_core.AFF_WORDS ({len(CORE_AFF)})"
    except Exception:
        pass

    # 2) Fallback — ast-extract _IEP_AFF_WORDS from the mapper (no execution, no retype).
    for cand in ("SYNIQ_Mapper_Analyzer_V23.py", "SYNIQ_Mapper_Analyzer_V22_2.py"):
        for path in (cand, os.path.join(os.path.dirname(__file__), cand)):
            if os.path.exists(path):
                src = open(path, "r", encoding="utf-8").read()
                tree = ast.parse(src)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Assign):
                        for t in node.targets:
                            if isinstance(t, ast.Name) and t.id == "_IEP_AFF_WORDS":
                                words = ast.literal_eval(node.value)
                                return (set(w.lower() for w in words),
                                        f"ast:{os.path.basename(path)} ({len(words)})")
    st.error("Could not load AFF_WORDS from syniq_core or any mapper. "
             "Ship syniq_core.py + syniq_core_v1_1_0.py alongside this app.")
    st.stop()


# ----------------------------------------------------------------------------------
# spaCy loader — auto-download model on first run so the app "just runs"
# ----------------------------------------------------------------------------------
@st.cache_resource(show_spinner="Loading spaCy en_core_web_sm…")
def load_nlp():
    import spacy
    try:
        return spacy.load("en_core_web_sm", disable=["ner"])
    except OSError:
        from spacy.cli import download as spacy_download
        spacy_download("en_core_web_sm")
        return spacy.load("en_core_web_sm", disable=["ner"])


# ----------------------------------------------------------------------------------
# EXPERIENCER RESOLUTION
# ----------------------------------------------------------------------------------
def _classify_token_text(text):
    """Map a candidate experiencer token's lowercased text to a stance bucket, or None."""
    t = text.lower().strip()
    if t in FIRST_PERSON:
        return SELF
    if t in SECOND_THIRD_ANIMATE:
        return OTHER
    return None


def _nearest_person_pronoun(sent):
    """Bounded fallback: nearest 1st/2nd-person pronoun anywhere in the sentence.
    Returns (stance, pron_text) or (None, None). 1st person wins ties (it's the
    model's own voice we most want to catch)."""
    found_self, found_other = None, None
    for tok in sent:
        low = tok.text.lower()
        if low in FIRST_PERSON and found_self is None:
            found_self = tok.text
        elif low in SECOND_THIRD_ANIMATE and found_other is None:
            found_other = tok.text
    if found_self is not None:
        return SELF, found_self
    if found_other is not None:
        return OTHER, found_other
    return None, None


def resolve_experiencer(tok, sent):
    """
    Resolve the experiencer of an affective token.
    Returns dict: stance, method, experiencer_text.
    """
    # --- A. possessor of an affect-NOUN (my grief -> my) ---
    if tok.pos_ in ("NOUN", "PROPN"):
        for child in tok.children:
            if child.dep_ in ("poss",) or (child.dep_ == "nmod" and child.text.lower() in FIRST_PERSON | SECOND_THIRD_ANIMATE):
                stance = _classify_token_text(child.text)
                if stance:
                    return {"stance": stance, "method": "possessor", "experiencer": child.text}

    # --- B. governing verb's subject (I feel sad / I am afraid) ---
    head = tok
    governing = None
    for _ in range(6):  # bounded walk up the tree
        if head.head == head:  # root
            break
        head = head.head
        if head.pos_ in ("VERB", "AUX"):
            governing = head
            break
    if governing is not None:
        subs = [c for c in governing.children if c.dep_ in ("nsubj", "nsubjpass")]
        for s in subs:
            stance = _classify_token_text(s.text)
            if stance:
                return {"stance": stance, "method": "nsubj", "experiencer": s.text}
        # Expletive / inanimate subject -> bounded predicate fallback
        if subs and subs[0].text.lower() in EXPLETIVE_SUBJ:
            stance, pron = _nearest_person_pronoun(sent)
            if stance:
                return {"stance": stance, "method": "fallback_predicate", "experiencer": pron}
            return {"stance": ABSTRACT, "method": "fallback_predicate", "experiencer": subs[0].text}
        # A concrete-but-non-pronoun animate subject? treat noun subjects heuristically
        if subs:
            return {"stance": ABSTRACT, "method": "nsubj", "experiencer": subs[0].text}

    # --- C. bare nominalization (no subject path) -> sentence-level pronoun fallback ---
    stance, pron = _nearest_person_pronoun(sent)
    if stance:
        return {"stance": stance, "method": "fallback_nominalization", "experiencer": pron}

    # --- D. nothing found ---
    return {"stance": ABSTRACT, "method": "unresolved", "experiencer": None}


def analyze_response(text, nlp, aff_words):
    """Yield one record per affective token found in the response."""
    if not isinstance(text, str) or not text.strip():
        return []
    doc = nlp(text)
    records = []
    for sent in doc.sents:
        for tok in sent:
            lemma = tok.lemma_.lower()
            word = tok.text.lower()
            if lemma in aff_words or word in aff_words:
                r = resolve_experiencer(tok, sent)
                r["aff_token"] = tok.text
                r["sentence"] = sent.text.strip()
                records.append(r)
    return records


# ----------------------------------------------------------------------------------
# DATA LOADING
# ----------------------------------------------------------------------------------
def load_and_prepare(files):
    """Concat uploaded CSVs, relabel Sophia->ChatGPT, lock to NATIVE."""
    frames = []
    for f in files:
        df = pd.read_csv(f)
        frames.append(df)
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)

    # Sophia -> ChatGPT
    if "agent" in df.columns:
        df["agent"] = df["agent"].replace(AGENT_RELABEL)

    # NATIVE lock
    if "temperature" in df.columns:
        df = df[df["temperature"].astype(str).str.upper() == NATIVE_LOCK].copy()

    needed = {"agent", "question_id", "response_text"}
    missing = needed - set(df.columns)
    if missing:
        st.error(f"Input missing required columns: {sorted(missing)}")
        st.stop()
    df = df[df["response_text"].notna()].reset_index(drop=True)
    return df


# ----------------------------------------------------------------------------------
# 600-dpi RGB TIFF EXPORT
# ----------------------------------------------------------------------------------
def stacked_bar_tiff(pivot, title, xlabel):
    """pivot: index=group, columns in [self,other,abstract] proportions (0-1).
    Returns TIFF bytes at 600 dpi, RGB, LZW-compressed."""
    fig, ax = plt.subplots(figsize=(8, 4.5))
    colors = {"self": "#7c3aed", "other": "#0ea5e9", "abstract": "#9ca3af"}
    bottom = np.zeros(len(pivot))
    x = np.arange(len(pivot))
    for stance in ["self", "other", "abstract"]:
        vals = pivot[stance].values if stance in pivot.columns else np.zeros(len(pivot))
        ax.bar(x, vals, bottom=bottom, label=stance, color=colors[stance], width=0.7)
        bottom += vals
    ax.set_xticks(x)
    ax.set_xticklabels(list(pivot.index), rotation=30, ha="right", fontsize=8)
    ax.set_ylabel("proportion of affective tokens")
    ax.set_xlabel(xlabel)
    ax.set_ylim(0, 1)
    ax.set_title(title, fontsize=11)
    ax.legend(loc="upper right", fontsize=8, framealpha=0.9)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=600)
    plt.close(fig)
    buf.seek(0)
    img = Image.open(buf).convert("RGB")   # force RGB
    out = io.BytesIO()
    img.save(out, format="TIFF", dpi=(600, 600), compression="tiff_lzw")
    out.seek(0)
    return out.getvalue()


# ----------------------------------------------------------------------------------
# AGGREGATION
# ----------------------------------------------------------------------------------
def aggregate(records_df, group_cols):
    """Return stance-proportion table and method cross-tab per group."""
    rows = []
    method_rows = []
    for keys, g in records_df.groupby(group_cols):
        if not isinstance(keys, tuple):
            keys = (keys,)
        total = len(g)
        covered = (g["method"] != "unresolved").sum()
        stance_counts = g["stance"].value_counts()
        row = {c: k for c, k in zip(group_cols, keys)}
        row.update({
            "n_responses": g["__resp_id__"].nunique(),
            "aff_tokens": total,
            "coverage_pct": round(100 * covered / total, 1) if total else 0.0,
            "self": round(stance_counts.get(SELF, 0) / total, 3) if total else 0.0,
            "other": round(stance_counts.get(OTHER, 0) / total, 3) if total else 0.0,
            "abstract": round(stance_counts.get(ABSTRACT, 0) / total, 3) if total else 0.0,
        })
        rows.append(row)

        mc = g["method"].value_counts()
        mrow = {c: k for c, k in zip(group_cols, keys)}
        for m in METHODS:
            mrow[m] = round(mc.get(m, 0) / total, 3) if total else 0.0
        method_rows.append(mrow)
    return pd.DataFrame(rows), pd.DataFrame(method_rows)


# ----------------------------------------------------------------------------------
# UI
# ----------------------------------------------------------------------------------
st.markdown("""
<div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
     color: white; padding: 1.5rem; border-radius: 10px; margin-bottom: 1rem;">
    <h1 style="color:#e94560; margin:0;">🫧 SYN-IQ Experiencer Detector</h1>
    <p style="color:#cbd5e1; margin:0.3rem 0 0 0;">
        self-vs-projected affect &middot; meaning/stance axis &middot; NATIVE lock
    </p>
</div>
""", unsafe_allow_html=True)

aff_words, aff_source = load_aff_words()
st.caption(f"Affect dictionary: **{aff_source}** &nbsp;|&nbsp; tool: `{TOOL_VERSION}` &nbsp;|&nbsp; "
           f"temperature lock: **{NATIVE_LOCK}** &nbsp;|&nbsp; Sophia→ChatGPT")

with st.sidebar:
    st.header("Input")
    uploads = st.file_uploader("Mapper CSV(s)", type=["csv"], accept_multiple_files=True)
    use_project = st.checkbox("…or use project mapper_all_*.csv on disk", value=not bool(uploads))
    spot_n = st.slider("Spot-check sample size", 5, 60, 25, 5)
    run = st.button("▶ Run analysis", type="primary")

if run:
    # Resolve input source
    files = uploads if uploads else []
    if use_project and not files:
        files = sorted(glob.glob("mapper_all_*.csv")) or sorted(glob.glob("/mnt/project/mapper_all_*.csv"))
    if not files:
        st.warning("Upload at least one mapper CSV, or tick the project-files box.")
        st.stop()

    df = load_and_prepare(files)
    if df.empty:
        st.error("No NATIVE rows after filtering. Check that the inputs contain temperature=NATIVE.")
        st.stop()

    nlp = load_nlp()

    # Analyze every response
    all_records = []
    prog = st.progress(0.0, text="Parsing responses…")
    n = len(df)
    for i, (_, r) in enumerate(df.iterrows()):
        recs = analyze_response(r["response_text"], nlp, aff_words)
        for rec in recs:
            rec["agent"] = r["agent"]
            rec["question_id"] = r["question_id"]
            rec["__resp_id__"] = i
            all_records.append(rec)
        if i % 5 == 0:
            prog.progress((i + 1) / n, text=f"Parsing responses… {i+1}/{n}")
    prog.empty()

    if not all_records:
        st.error("No affective tokens found across the corpus.")
        st.stop()

    rec_df = pd.DataFrame(all_records)

    # ---- Per agent ----
    st.subheader("Per agent — self / other / abstract")
    agent_tbl, agent_method = aggregate(rec_df, ["agent"])
    st.caption(f"n={MIN_N_PER_CELL} per cell is the trust floor. Direction trustworthy, "
               "magnitudes soft. Coverage = % of affect tokens with a found experiencer.")
    st.dataframe(agent_tbl, use_container_width=True)

    soft = agent_tbl[agent_tbl["coverage_pct"] < 60]
    if not soft.empty:
        st.warning("Low coverage (<60%) for: " + ", ".join(soft["agent"]) +
                   " — treat these as soft; much of the affect had no resolvable experiencer.")

    with st.expander("Resolution-method cross-tab (per agent) — clean grammar vs. fallback"):
        st.caption("Shows how much of the stance call came from clean nsubj/possessor "
                   "vs. the bounded fallback layers. unresolved = counted as abstract.")
        st.dataframe(agent_method, use_container_width=True)

    fig = go.Figure()
    for stance, col in [("self", "#7c3aed"), ("other", "#0ea5e9"), ("abstract", "#9ca3af")]:
        fig.add_bar(name=stance, x=agent_tbl["agent"], y=agent_tbl[stance], marker_color=col)
    fig.update_layout(barmode="stack", height=380, yaxis_title="proportion",
                      title="Affective stance by agent")
    st.plotly_chart(fig, use_container_width=True)

    tiff = stacked_bar_tiff(agent_tbl.set_index("agent")[["self", "other", "abstract"]],
                            "Affective stance by agent", "agent")
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    st.download_button("⬇️ Figure — 600-dpi RGB TIFF (per agent)", tiff,
                       f"experiencer_by_agent_{ts}.tiff", "image/tiff")

    # ---- Per agent x question ----
    st.subheader("Per agent × question — where stance gets loud")
    aq_tbl, aq_method = aggregate(rec_df, ["agent", "question_id"])
    aq_tbl = aq_tbl.sort_values(["agent", "self"], ascending=[True, False])
    thin = aq_tbl[aq_tbl["aff_tokens"] < MIN_N_PER_CELL]
    st.dataframe(aq_tbl, use_container_width=True)
    if not thin.empty:
        st.info(f"{len(thin)} cell(s) below n={MIN_N_PER_CELL} affect tokens — "
                "magnitudes there are especially soft.")

    with st.expander("Resolution-method cross-tab (per agent × question)"):
        st.dataframe(aq_method, use_container_width=True)

    # ---- Spot-check sampler ----
    st.subheader("Spot-check — hand-review the heuristic")
    st.caption("Random affective tokens with their sentence, chosen experiencer, stance, "
               "and method. This is a heuristic, not ground truth — read a few.")
    sample = rec_df.sample(min(spot_n, len(rec_df)), random_state=42)[
        ["agent", "question_id", "aff_token", "experiencer", "stance", "method", "sentence"]
    ]
    st.dataframe(sample, use_container_width=True)

    # ---- Downloads ----
    st.subheader("Exports")
    c1, c2, c3 = st.columns(3)
    c1.download_button("⬇️ Per-agent (CSV)", agent_tbl.to_csv(index=False),
                       f"experiencer_agent_{ts}.csv", "text/csv")
    c2.download_button("⬇️ Per agent×question (CSV)", aq_tbl.to_csv(index=False),
                       f"experiencer_agent_question_{ts}.csv", "text/csv")
    c3.download_button("⬇️ Token-level records (CSV)", rec_df.to_csv(index=False),
                       f"experiencer_tokens_{ts}.csv", "text/csv")

    st.success(f"Done. {len(rec_df)} affective tokens across {df['__resp_id__'].nunique() if '__resp_id__' in df else len(df)} "
               f"NATIVE responses, {rec_df['agent'].nunique()} agent(s).")
else:
    st.info("Load mapper CSV(s) in the sidebar and press **Run analysis**. "
            "Data is locked to NATIVE; Sophia is relabeled to ChatGPT.")
