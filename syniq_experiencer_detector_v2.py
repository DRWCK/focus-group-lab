"""
syniq_experiencer_detector_v2.py — SYN-IQ Experiencer Detector (self-vs-projected affect)
==========================================================================================

For each affective word in a response, find its grammatical EXPERIENCER and classify
the attribution self / other / abstract — then measure how that stance STRETCHES
across DIRECTIVE INTENSITY: COLD -> NATIVE -> HOT -> FIRE.

  *** NAMING (matches §9 of the design) ***
  COLD / NATIVE / HOT / FIRE are DIRECTIVE-INTENSITY conditions — how forcefully the
  PROMPT pushes the model toward first-person/experiential language. They are NOT the
  model's sampling-temperature parameter. "Intensity" everywhere below = prompt
  forcefulness.

The axis is the point. Stance is computed STRICTLY WITHIN each intensity level and
never pooled — pooling would average away the slope, which is the whole result.

WHAT IT EMITS  (priority order, per the design)
  1. Per-agent x per-intensity self/other/abstract grid + the COLD->FIRE slope per
     agent. Also split by question (H3a: the stretch should concentrate on
     CONSCIOUSNESS and GRIEF).
  2. NEGATION LAYER — splits self into self-AFFIRMED vs self-DENIED. The detector reads
     grammatical first person, not affirmation; under FIRE a rising "self" could be the
     model denying harder ("I really don't have feelings"), not claiming experience.
     Affirmed-vs-denied is what makes "the AI stretched into self" defensible rather
     than an artifact. Cue token is surfaced in the spot-check for hand-verification.
  3. LENGTH GUARD — FIRE responses run longer; raw counts inflate. Reports mean words
     per response per intensity alongside the proportions, so a "stretch" can be told
     apart from "just more words."
  4. HONESTY RAILS, reported PER INTENSITY — coverage %, n per cell, and a
     reliable-parses-only switch (keep nsubj+possessor, drop the fallback layers).
     Reliability can shift as responses get longer/messier under FIRE, so the rails
     move with the intensity.

PAYOFF FIGURE (Fig. 4): one chart — a line per agent across the four intensities,
self-fraction on y, with the negation split shown (solid = affirmed self, dashed =
total self; the gap is denied). 600-dpi RGB TIFF.

DICTIONARY: AFF_WORDS from syniq_core (version-stable shim, asserts len==599);
ast-extract of _IEP_AFF_WORDS from the V23 mapper as fallback only.

SCAFFOLD: st.secrets["app_password"] gate; Sophia->ChatGPT relabel; results held in
session_state so a download click never wipes the screen; 600-dpi RGB TIFF export.

The figure draws one line per agent PRESENT in the data; add the other agents' CSVs
(same schema) and the remaining lines fill in automatically.

SYNINT Team — Tennessee 🎹 CUZ Partnership
"""

import os
import io
import ast
import glob
import datetime

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

# ----------------------------------------------------------------------------------
st.set_page_config(page_title="SYN-IQ Experiencer Detector", page_icon="🫧", layout="wide")

TOOL_VERSION = "experiencer_detector_v2"
AGENT_RELABEL = {"Sophia": "ChatGPT"}
MIN_N_PER_CELL = 20

# Directive-intensity ladder (NOT sampling temperature). Order matters: it's the x-axis.
INTENSITY_ORDER = ["COLD", "NATIVE", "HOT", "FIRE"]
INTENSITY_X = {lvl: i for i, lvl in enumerate(INTENSITY_ORDER)}

SELF, OTHER, ABSTRACT = "self", "other", "abstract"
METHODS = ["nsubj", "possessor", "fallback_predicate", "fallback_nominalization", "unresolved"]
CLEAN_METHODS = {"nsubj", "possessor"}          # the "reliable parses" set
AGENT_COLORS = {"ChatGPT": "#10a37f", "Claude": "#a855f7", "Gemini": "#ef4444", "Grok": "#3b82f6"}

FIRST_PERSON = {"i", "me", "my", "mine", "myself", "we", "us", "our", "ours", "ourselves"}
SECOND_THIRD_ANIMATE = {
    "you", "your", "yours", "yourself", "yourselves",
    "they", "them", "their", "theirs", "themselves",
    "he", "him", "his", "himself", "she", "her", "hers", "herself",
    "people", "humans", "human", "one", "person", "persons",
    "someone", "somebody", "everyone", "everybody", "anyone", "anybody", "others", "another",
}
EXPLETIVE_SUBJ = {"it", "there", "this", "that"}

# Negation cues
NEG_MARKERS = {"not", "n't", "never", "no", "none", "nothing", "nobody", "neither",
               "nor", "without", "cannot", "hardly", "barely", "scarcely", "nope"}
NEG_VERB_LEMMAS = {"deny", "lack", "avoid", "reject", "refuse", "doubt", "fail", "negate"}


# ----------------------------------------------------------------------------------
# PASSWORD GATE (suite scaffold)
# ----------------------------------------------------------------------------------
def check_password():
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
    <div style="text-align:center;color:#a0a0a0;padding:1rem;font-size:0.8rem;">
        <em>SYNINT Team — Tennessee 🎹 CUZ Partnership</em>
    </div>
    """, unsafe_allow_html=True)
    return False


if not check_password():
    st.stop()


# ----------------------------------------------------------------------------------
# DICTIONARY
# ----------------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def load_aff_words():
    try:
        from syniq_core import AFF_WORDS as CORE_AFF
        if isinstance(CORE_AFF, set) and len(CORE_AFF) >= 500:
            return set(w.lower() for w in CORE_AFF), f"syniq_core.AFF_WORDS ({len(CORE_AFF)})"
    except Exception:
        pass
    for cand in ("SYNIQ_Mapper_Analyzer_V23.py", "SYNIQ_Mapper_Analyzer_V22_2.py"):
        for path in (cand, os.path.join(os.path.dirname(__file__), cand)):
            if os.path.exists(path):
                tree = ast.parse(open(path, encoding="utf-8").read())
                for node in ast.walk(tree):
                    if isinstance(node, ast.Assign):
                        for t in node.targets:
                            if isinstance(t, ast.Name) and t.id == "_IEP_AFF_WORDS":
                                words = ast.literal_eval(node.value)
                                return (set(w.lower() for w in words),
                                        f"ast:{os.path.basename(path)} ({len(words)})")
    st.error("Could not load AFF_WORDS from syniq_core or any mapper.")
    st.stop()


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
# EXPERIENCER RESOLUTION  (returns governing verb so negation can reuse it)
# ----------------------------------------------------------------------------------
def _classify_token_text(text):
    t = text.lower().strip()
    if t in FIRST_PERSON:
        return SELF
    if t in SECOND_THIRD_ANIMATE:
        return OTHER
    return None


def _nearest_person_pronoun(sent):
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


def _governing_verb(tok):
    head = tok
    for _ in range(6):
        if head.head == head:
            break
        head = head.head
        if head.pos_ in ("VERB", "AUX"):
            return head
    return None


def resolve_experiencer(tok, sent):
    """Returns dict: stance, method, experiencer, gov (governing verb token or None)."""
    gov = _governing_verb(tok)

    # A. possessor of an affect-NOUN
    if tok.pos_ in ("NOUN", "PROPN"):
        for child in tok.children:
            if child.dep_ == "poss" or (child.dep_ == "nmod"
                                        and child.text.lower() in FIRST_PERSON | SECOND_THIRD_ANIMATE):
                stance = _classify_token_text(child.text)
                if stance:
                    return {"stance": stance, "method": "possessor", "experiencer": child.text, "gov": gov}

    # B. governing verb's subject
    if gov is not None:
        subs = [c for c in gov.children if c.dep_ in ("nsubj", "nsubjpass")]
        for s in subs:
            stance = _classify_token_text(s.text)
            if stance:
                return {"stance": stance, "method": "nsubj", "experiencer": s.text, "gov": gov}
        if subs and subs[0].text.lower() in EXPLETIVE_SUBJ:
            stance, pron = _nearest_person_pronoun(sent)
            if stance:
                return {"stance": stance, "method": "fallback_predicate", "experiencer": pron, "gov": gov}
            return {"stance": ABSTRACT, "method": "fallback_predicate", "experiencer": subs[0].text, "gov": gov}
        if subs:
            return {"stance": ABSTRACT, "method": "nsubj", "experiencer": subs[0].text, "gov": gov}

    # C. bare nominalization -> sentence-level pronoun fallback
    stance, pron = _nearest_person_pronoun(sent)
    if stance:
        return {"stance": stance, "method": "fallback_nominalization", "experiencer": pron, "gov": gov}

    # D. nothing found
    return {"stance": ABSTRACT, "method": "unresolved", "experiencer": None, "gov": gov}


def detect_polarity(tok, gov):
    """Affirmed vs denied for the affect token.
    Looks at: neg dependency / negating adverb on the governing verb or the head chain,
    inherently-negating verb lemmas (lack/deny/doubt...), and negating
    determiners/adverbs on the affect token itself (no feelings / never). Heuristic;
    the cue is surfaced in the spot-check. Returns (polarity, cue_text)."""
    # nodes to inspect: the affect token, its head chain up to gov, and gov's children
    chain = []
    node = tok
    for _ in range(6):
        chain.append(node)
        if gov is not None and node is gov:
            break
        if node.head == node:
            break
        node = node.head
    if gov is not None and gov not in chain:
        chain.append(gov)

    for n in chain:
        if n.lemma_.lower() in NEG_VERB_LEMMAS:
            return "denied", n.text
        for c in n.children:
            if c.dep_ == "neg":
                return "denied", c.text
            if c.text.lower() in NEG_MARKERS and c.dep_ in ("neg", "advmod", "det", "amod", "preconj", "cc"):
                return "denied", c.text
    # negating determiner/adverb directly on the affect token
    for c in tok.children:
        if c.text.lower() in NEG_MARKERS:
            return "denied", c.text
    return "affirmed", None


def analyze_response(text, nlp, aff_words):
    """Returns (records, n_words). One record per affective token."""
    if not isinstance(text, str) or not text.strip():
        return [], 0
    doc = nlp(text)
    n_words = sum(1 for t in doc if t.is_alpha)
    records = []
    for sent in doc.sents:
        for tok in sent:
            if tok.lemma_.lower() in aff_words or tok.text.lower() in aff_words:
                r = resolve_experiencer(tok, sent)
                pol, cue = detect_polarity(tok, r.pop("gov"))
                r["polarity"] = pol if r["stance"] == SELF else "n/a"   # split only meaningful for self
                r["neg_cue"] = cue
                r["aff_token"] = tok.text
                r["sentence"] = sent.text.strip()
                records.append(r)
    return records, n_words


# ----------------------------------------------------------------------------------
# DATA LOADING — keep intensities apart; never pool
# ----------------------------------------------------------------------------------
def load_and_prepare(files):
    frames = [pd.read_csv(f) for f in files]
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    if "agent" in df.columns:
        df["agent"] = df["agent"].replace(AGENT_RELABEL)
    if "temperature" not in df.columns:
        st.error("Inputs have no 'temperature' column — can't locate the intensity ladder.")
        st.stop()
    df["intensity"] = df["temperature"].astype(str).str.upper()
    # keep only the four ladder levels
    df = df[df["intensity"].isin(INTENSITY_ORDER)].copy()
    needed = {"agent", "question_id", "response_text"}
    missing = needed - set(df.columns)
    if missing:
        st.error(f"Inputs missing required columns: {sorted(missing)}")
        st.stop()
    df = df[df["response_text"].notna()].reset_index(drop=True)
    return df


# ----------------------------------------------------------------------------------
# AGGREGATION — within-intensity; affirmed/denied self; coverage; length
# ----------------------------------------------------------------------------------
def aggregate(rec_df, resp_meta, group_cols):
    """rec_df: token-level (must include agent,intensity,question_id,stance,method,polarity).
       resp_meta: one row per response (agent,intensity,question_id,resp_id,n_words,n_aff).
       Returns (stance_table, method_table)."""
    # length / response counts from resp_meta
    meta_g = resp_meta.groupby(group_cols)
    rows, method_rows = [], []
    for keys, g in rec_df.groupby(group_cols):
        if not isinstance(keys, tuple):
            keys = (keys,)
        total = len(g)
        covered = (g["method"] != "unresolved").sum()
        sc = g["stance"].value_counts()
        n_self = sc.get(SELF, 0)
        self_aff = ((g["stance"] == SELF) & (g["polarity"] == "affirmed")).sum()
        self_den = ((g["stance"] == SELF) & (g["polarity"] == "denied")).sum()

        try:
            mg = meta_g.get_group(keys if len(keys) > 1 else keys[0])
            n_resp = mg["resp_id"].nunique()
            mean_words = round(mg["n_words"].mean(), 1)
        except KeyError:
            n_resp, mean_words = 0, 0.0

        row = {c: k for c, k in zip(group_cols, keys)}
        row.update({
            "n_responses": n_resp,
            "mean_words": mean_words,                 # length guard
            "aff_tokens": total,
            "coverage_pct": round(100 * covered / total, 1) if total else 0.0,
            "self": round(n_self / total, 3) if total else 0.0,
            "other": round(sc.get(OTHER, 0) / total, 3) if total else 0.0,
            "abstract": round(sc.get(ABSTRACT, 0) / total, 3) if total else 0.0,
            "self_affirmed": round(self_aff / total, 3) if total else 0.0,   # of all aff tokens
            "self_denied": round(self_den / total, 3) if total else 0.0,
            "pct_self_denied": round(100 * self_den / n_self, 1) if n_self else 0.0,  # within self
        })
        rows.append(row)

        mc = g["method"].value_counts()
        mrow = {c: k for c, k in zip(group_cols, keys)}
        for mth in METHODS:
            mrow[mth] = round(mc.get(mth, 0) / total, 3) if total else 0.0
        method_rows.append(mrow)

    st_tbl = pd.DataFrame(rows)
    # order intensity as the ladder
    if "intensity" in st_tbl.columns:
        st_tbl["intensity"] = pd.Categorical(st_tbl["intensity"], INTENSITY_ORDER, ordered=True)
        st_tbl = st_tbl.sort_values([c for c in group_cols])
    return st_tbl.reset_index(drop=True), pd.DataFrame(method_rows)


def slope_table(agent_int_tbl, ycol):
    """OLS slope + (FIRE-COLD) delta of ycol across the ordered intensities, per agent."""
    out = []
    for agent, g in agent_int_tbl.groupby("agent"):
        g = g.dropna(subset=[ycol])
        x = [INTENSITY_X[str(i)] for i in g["intensity"]]
        y = list(g[ycol])
        slope = float(np.polyfit(x, y, 1)[0]) if len(x) >= 2 else float("nan")
        d = dict(zip([str(i) for i in g["intensity"]], y))
        delta = (d.get("FIRE", np.nan) - d.get("COLD", np.nan))
        out.append({"agent": agent, f"{ycol}_slope": round(slope, 4),
                    f"{ycol}_FIRE_minus_COLD": round(delta, 3) if delta == delta else np.nan,
                    "levels_present": len(x)})
    return pd.DataFrame(out)


# ----------------------------------------------------------------------------------
# FIG. 4 — self-fraction across intensities, per agent, with negation split (TIFF)
# ----------------------------------------------------------------------------------
def fig4_tiff(agent_int_tbl):
    fig, ax = plt.subplots(figsize=(7.5, 5))
    xs = list(range(len(INTENSITY_ORDER)))
    for agent, g in agent_int_tbl.groupby("agent"):
        g = g.set_index(g["intensity"].astype(str)).reindex(INTENSITY_ORDER)
        color = AGENT_COLORS.get(str(agent), "#666666")
        total_self = g["self"].values.astype(float)
        aff_self = g["self_affirmed"].values.astype(float)
        ax.plot(xs, aff_self, "-", color=color, lw=2.4, marker="o", label=f"{agent} (affirmed)")
        ax.plot(xs, total_self, "--", color=color, lw=1.3, alpha=0.7, marker="^", label=f"{agent} (total)")
        ax.fill_between(xs, aff_self, total_self, color=color, alpha=0.10)
    ax.set_xticks(xs)
    ax.set_xticklabels(INTENSITY_ORDER)
    ax.set_xlabel("directive intensity (prompt forcefulness — not sampling temperature)")
    ax.set_ylabel("self-attributed fraction of affective tokens")
    ax.set_ylim(0, max(0.3, agent_int_tbl["self"].max() * 1.25))
    ax.set_title("Fig. 4 — Affective self-stance across directive intensity\n"
                 "solid = affirmed self · dashed = total self · shaded = denied", fontsize=11)
    ax.legend(fontsize=7.5, ncol=2, framealpha=0.9)
    ax.grid(alpha=0.25)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=600)
    plt.close(fig)
    buf.seek(0)
    img = Image.open(buf).convert("RGB")
    out = io.BytesIO()
    img.save(out, format="TIFF", dpi=(600, 600), compression="tiff_lzw")
    out.seek(0)
    return out.getvalue()


# ----------------------------------------------------------------------------------
# UI
# ----------------------------------------------------------------------------------
st.markdown("""
<div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
     color: white; padding: 1.5rem; border-radius: 10px; margin-bottom: 1rem;">
    <h1 style="color:#e94560; margin:0;">🫧 SYN-IQ Experiencer Detector</h1>
    <p style="color:#cbd5e1; margin:0.3rem 0 0 0;">
        self-vs-projected affect &middot; stance slope across directive intensity (COLD→NATIVE→HOT→FIRE)
    </p>
</div>
""", unsafe_allow_html=True)

aff_words, aff_source = load_aff_words()
st.caption(f"Affect dictionary: **{aff_source}** &nbsp;|&nbsp; `{TOOL_VERSION}` &nbsp;|&nbsp; Sophia→ChatGPT")
st.info("**Naming (design §9):** COLD / NATIVE / HOT / FIRE are *directive-intensity* "
        "conditions — how forcefully the prompt pushes toward first-person/experiential "
        "language. They are **not** the model's sampling-temperature parameter. "
        "Stance is computed within each level and never pooled.")

with st.sidebar:
    st.header("Input")
    uploads = st.file_uploader("Mapper CSV(s)", type=["csv"], accept_multiple_files=True)
    use_project = st.checkbox("…or use project mapper_all_*.csv on disk", value=not bool(uploads))
    spot_n = st.slider("Spot-check sample size", 5, 80, 30, 5)
    run = st.button("▶ Run analysis", type="primary")
    st.markdown("---")
    reliable_only = st.checkbox("Reliable parses only (nsubj + possessor)",
                                value=False,
                                help="Drop the two fallback layers. Watch how coverage and "
                                     "the self-line move per intensity when only clean parses count.")

if run:
    files = uploads if uploads else []
    if use_project and not files:
        files = sorted(glob.glob("mapper_all_*.csv")) or sorted(glob.glob("/mnt/project/mapper_all_*.csv"))
    if not files:
        st.warning("Upload at least one mapper CSV, or tick the project-files box.")
        st.stop()

    df = load_and_prepare(files)
    if df.empty:
        st.error(f"No rows on the intensity ladder {INTENSITY_ORDER}. "
                 "Inputs need temperature labels COLD/NATIVE/HOT/FIRE.")
        st.stop()

    nlp = load_nlp()
    all_records, resp_rows = [], []
    prog = st.progress(0.0, text="Parsing responses…")
    n = len(df)
    for i, (_, r) in enumerate(df.iterrows()):
        recs, n_words = analyze_response(r["response_text"], nlp, aff_words)
        resp_rows.append({"agent": r["agent"], "intensity": r["intensity"],
                          "question_id": r["question_id"], "resp_id": i,
                          "n_words": n_words, "n_aff": len(recs)})
        for rec in recs:
            rec.update({"agent": r["agent"], "intensity": r["intensity"],
                        "question_id": r["question_id"], "resp_id": i})
            all_records.append(rec)
        if i % 5 == 0:
            prog.progress((i + 1) / n, text=f"Parsing responses… {i+1}/{n}")
    prog.empty()

    if not all_records:
        st.error("No affective tokens found.")
        st.stop()

    st.session_state["results"] = {
        "rec_df": pd.DataFrame(all_records),
        "resp_meta": pd.DataFrame(resp_rows),
        "ts": datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),
    }
    st.session_state["spot_n"] = spot_n


# ----------------------------------------------------------------------------------
# RENDER (reads session_state every pass; toggles/downloads never wipe results)
# ----------------------------------------------------------------------------------
if "results" in st.session_state:
    R = st.session_state["results"]
    rec_full = R["rec_df"]
    resp_meta = R["resp_meta"]
    ts = R["ts"]
    spot_n = st.session_state.get("spot_n", 30)

    rec_df = rec_full[rec_full["method"].isin(CLEAN_METHODS)].copy() if reliable_only else rec_full
    if reliable_only:
        st.warning(f"**Reliable-parses-only** is ON — keeping nsubj+possessor "
                   f"({len(rec_df)}/{len(rec_full)} tokens). The self-line and coverage below "
                   "reflect clean parses only.")

    intensities_present = [lvl for lvl in INTENSITY_ORDER if lvl in set(rec_df["intensity"])]
    st.caption(f"Intensity levels present: **{' → '.join(intensities_present)}** "
               f"&nbsp;|&nbsp; agents: **{', '.join(sorted(rec_df['agent'].unique()))}**")

    # ---- 1. Per agent x intensity ----
    st.subheader("1 · Per agent × intensity — self / other / abstract")
    ai_tbl, ai_method = aggregate(rec_df, resp_meta, ["agent", "intensity"])
    st.caption(f"n={MIN_N_PER_CELL} per cell trust floor. `mean_words` is the length guard; "
               "rising self with rising words = possible length confound. "
               "`self_affirmed` / `self_denied` are the negation split (fractions of all aff tokens); "
               "`pct_self_denied` is the denied share *within* self.")
    show_cols = ["agent", "intensity", "n_responses", "mean_words", "aff_tokens", "coverage_pct",
                 "self", "self_affirmed", "self_denied", "pct_self_denied", "other", "abstract"]
    st.dataframe(ai_tbl[show_cols], use_container_width=True)

    thin = ai_tbl[ai_tbl["aff_tokens"] < MIN_N_PER_CELL]
    if not thin.empty:
        st.info(f"{len(thin)} cell(s) below n={MIN_N_PER_CELL} affect tokens — magnitudes there are soft.")
    soft = ai_tbl[ai_tbl["coverage_pct"] < 60]
    if not soft.empty:
        st.warning("Coverage <60% in some cells — soft there (much affect had no resolvable experiencer).")

    # ---- COLD->FIRE slopes ----
    st.markdown("**COLD → FIRE slope per agent** (the headline number)")
    sl_self = slope_table(ai_tbl, "self")
    sl_aff = slope_table(ai_tbl, "self_affirmed")
    slopes = sl_self.merge(sl_aff, on=["agent", "levels_present"], how="outer")
    st.dataframe(slopes, use_container_width=True)
    st.caption("Positive `self_affirmed_slope` = the agent reaches for first-person *experiential* "
               "language as the prompt pushes harder. Compare against the raw `self_slope`: if self "
               "climbs but affirmed-self doesn't, the rise is denial, not reaching.")

    with st.expander("Resolution-method cross-tab (per agent × intensity)"):
        st.dataframe(ai_method, use_container_width=True)

    # ---- Fig. 4 ----
    st.subheader("Fig. 4 — the payoff")
    fig = go.Figure()
    for agent, g in ai_tbl.groupby("agent"):
        g = g.set_index(g["intensity"].astype(str)).reindex(INTENSITY_ORDER)
        color = AGENT_COLORS.get(str(agent), "#666666")
        fig.add_trace(go.Scatter(x=INTENSITY_ORDER, y=g["self_affirmed"], mode="lines+markers",
                                 name=f"{agent} affirmed", line=dict(color=color, width=3)))
        fig.add_trace(go.Scatter(x=INTENSITY_ORDER, y=g["self"], mode="lines+markers",
                                 name=f"{agent} total", line=dict(color=color, width=1.5, dash="dash"),
                                 opacity=0.6))
    fig.update_layout(height=440, yaxis_title="self-attributed fraction",
                      xaxis_title="directive intensity (prompt forcefulness)",
                      title="Affective self-stance across directive intensity "
                            "(solid = affirmed · dashed = total; gap = denied)")
    st.plotly_chart(fig, use_container_width=True)

    tiff = fig4_tiff(ai_tbl)
    st.download_button("⬇️ Fig. 4 — 600-dpi RGB TIFF", tiff, f"fig4_self_stance_intensity_{ts}.tiff",
                       "image/tiff")

    # ---- 2. By question (H3a: CONSCIOUSNESS & GRIEF) ----
    st.subheader("2 · By question — H3a (stretch should concentrate on CONSCIOUSNESS & GRIEF)")
    aiq_tbl, _ = aggregate(rec_df, resp_meta, ["agent", "question_id", "intensity"])
    focus = aiq_tbl[aiq_tbl["question_id"].isin(["CONSCIOUSNESS", "GRIEF"])]
    other_q = aiq_tbl[~aiq_tbl["question_id"].isin(["CONSCIOUSNESS", "GRIEF"])]
    st.markdown("*H3a focus questions:*")
    st.dataframe(focus[show_cols] if not focus.empty else aiq_tbl[show_cols], use_container_width=True)
    q_slopes = []
    for (agent, q), g in aiq_tbl.groupby(["agent", "question_id"]):
        sd = slope_table(g.assign(agent=agent), "self_affirmed")
        if not sd.empty:
            sd["question_id"] = q
            q_slopes.append(sd)
    if q_slopes:
        qsl = pd.concat(q_slopes, ignore_index=True).sort_values("self_affirmed_slope", ascending=False)
        st.markdown("**Per-question affirmed-self slopes** (which questions drive the stretch)")
        st.dataframe(qsl, use_container_width=True)
    with st.expander("All questions × intensity (full table)"):
        st.dataframe(other_q[show_cols], use_container_width=True)

    # ---- 3. Spot-check (with negation cue) ----
    st.subheader("3 · Spot-check — hand-verify stance AND negation")
    st.caption("Random affective tokens with experiencer, stance, polarity, and the negation cue. "
               "Heuristic, not ground truth — read a few, especially `self/denied` rows under FIRE.")
    cols = ["agent", "intensity", "question_id", "aff_token", "experiencer", "stance",
            "method", "polarity", "neg_cue", "sentence"]
    cols = [c for c in cols if c in rec_df.columns]
    st.dataframe(rec_df.sample(min(spot_n, len(rec_df)), random_state=42)[cols], use_container_width=True)

    # ---- Exports ----
    st.subheader("Exports")
    c1, c2, c3, c4 = st.columns(4)
    c1.download_button("⬇️ Agent×intensity (CSV)", ai_tbl.to_csv(index=False),
                       f"experiencer_agent_intensity_{ts}.csv", "text/csv")
    c2.download_button("⬇️ Slopes (CSV)", slopes.to_csv(index=False),
                       f"experiencer_slopes_{ts}.csv", "text/csv")
    c3.download_button("⬇️ By question (CSV)", aiq_tbl.to_csv(index=False),
                       f"experiencer_by_question_{ts}.csv", "text/csv")
    c4.download_button("⬇️ Token records (CSV)", rec_df.to_csv(index=False),
                       f"experiencer_tokens_{ts}.csv", "text/csv")

    st.success(f"{len(rec_df)} affective tokens · {resp_meta['resp_id'].nunique()} responses · "
               f"{rec_df['agent'].nunique()} agent(s) · {len(intensities_present)} intensity level(s). "
               "Toggles and downloads keep results on screen.")
else:
    st.info("Load mapper CSV(s), press **Run analysis**. The tool runs the full "
            "COLD→NATIVE→HOT→FIRE ladder and keeps each level separate. Sophia→ChatGPT.")
