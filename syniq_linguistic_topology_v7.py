"""
SYN-IQ Linguistic Topology Analyzer V7
======================================
Novelty Cascade + Mean Unique-word Delta (MUD)

PURPOSE: V4 measured sentence-level novelty via content-word overlap.
         V6 adds formal MUD computation as specified in the §4.2 protocol:
           - Word-level MUD (per-run paired, pooled)
           - Bigram MUD (per-run paired, pooled) — captures combinatorial novelty
           - Same depth ordering, same function-word filtering as v4

NEW IN V7:
  - PAIRING AXIS selector: compute MUD across DEPTH (Shallow->Deep, original)
    OR across CONDITION/temperature (e.g. NATIVE->FIRE). Same MUD math, the
    only change is which ordered axis the consecutive pairs walk along. This
    answers: 'how much does each agent's vocabulary MOVE when the directive
    changes?' — per-agent NATIVE->FIRE word-shift magnitude.

INHERITED FROM V6:
  - compute_word_mud(): formal MUD(d → d+1) = |UniqueWords(d+1) ∩ NotIn(d)| / TotalWords(d+1)
  - compute_bigram_mud(): same formula on word bigrams
  - Per-run paired: matched run #N at depth d vs run #N at depth d+1
  - Pooled: union of unique tokens across all runs at each depth
  - Streamlit UI: upload depth-stratified CSV → MUD tables + heatmap
  - CSV export with per-cell MUD values for downstream tools

USAGE:
    streamlit run syniq_linguistic_topology_v6.py

INPUT CSV (must include):
  - agent
  - depth (Shallow / Medium / Deep / Ultra-Deep, etc.)
  - question_id (or question)
  - run (run number within cell, integer)
  - response_text

SYNINT Team — May 2026
Tennessee 🎹 CUZ Partnership
"""

import streamlit as st
import pandas as pd
import numpy as np
import re
import io
import json
from collections import Counter, defaultdict
from datetime import datetime

# Auth gate (matches other tools)
def check_password():
    if "auth_ok" in st.session_state and st.session_state.auth_ok:
        return True
    pw = st.text_input("Password", type="password")
    if pw == "tennessee":
        st.session_state.auth_ok = True
        st.rerun()
    elif pw:
        st.error("Incorrect password.")
    return False

st.set_page_config(
    page_title="SYN-IQ Linguistic Topology V7",
    page_icon="📐",
    layout="wide",
)

st.markdown("""
<style>
.main { background: #ffffff; }
.metric-card {
    background: #f8f8f7;
    border: 1px solid #d3d1c7;
    border-radius: 8px;
    padding: 0.8rem 1rem;
    margin: 0.4rem 0;
}
</style>
""", unsafe_allow_html=True)

st.markdown("# 📐 SYN-IQ Linguistic Topology V7")
st.markdown("**Novelty Cascade + Mean Unique-word Delta (MUD) — word-level and bigram**")

if not check_password():
    st.stop()

# =============================================================================
# CONSTANTS — match v4 for consistency
# =============================================================================

FUNCTION_WORDS = set([
    "a","an","the","and","but","or","nor","for","yet","so","in","on","at","to",
    "of","with","by","from","up","about","into","through","during","before",
    "after","above","below","between","out","off","over","under","again","further",
    "then","once","here","there","when","where","why","how","all","both","each",
    "few","more","most","other","some","such","no","not","only","own","same","than",
    "too","very","just","as","if","while","although","because","since","unless",
    "until","though","whether","this","that","these","those","i","you","he","she",
    "it","we","they","what","which","who","whom","my","your","his","her","its",
    "our","their","am","is","are","was","were","be","been","being","have","has",
    "had","do","does","did","will","would","shall","should","may","might","must",
    "can","could","also","even","still","back","any","many","much","well",
    "now","then","via","per","vs","etc","ie","eg"
])

DEPTH_ORDER_CANONICAL = ['Shallow', 'Medium', 'Deep', 'Ultra-Deep',
                          'Standard', 'Profound', 'Moderate']

# V7: condition/temperature ladder for cross-directive MUD (NATIVE->FIRE etc.)
CONDITION_ORDER_CANONICAL = ['COLD', 'NATIVE', 'HOT', 'FIRE',
                             'Cold', 'Native', 'Hot', 'Fire',
                             'cold', 'native', 'hot', 'fire']


# =============================================================================
# CORE — TOKEN AND BIGRAM EXTRACTION
# =============================================================================

def extract_words(text, drop_function=True):
    """Lowercase, alphanumeric-only words. Optionally drop function words."""
    words = re.findall(r'\b[a-z]+\b', str(text).lower())
    if drop_function:
        words = [w for w in words if w not in FUNCTION_WORDS and len(w) > 2]
    return words

def extract_bigrams(text, drop_function=True):
    """Word bigrams from text."""
    words = extract_words(text, drop_function=drop_function)
    return [(words[i], words[i+1]) for i in range(len(words)-1)]


# =============================================================================
# CORE — MUD COMPUTATION
# =============================================================================

def mud_pair(text_d, text_d_plus_1, mode='word'):
    """
    MUD(d → d+1) = |UniqueTokens(d+1) ∩ NotIn(d)| / TotalTokens(d+1)

    mode='word'   → token = single word
    mode='bigram' → token = (w_i, w_{i+1}) tuple
    """
    extractor = extract_words if mode == 'word' else extract_bigrams

    tokens_d = extractor(text_d)
    tokens_d1 = extractor(text_d_plus_1)
    if not tokens_d1:
        return None  # no denominator

    set_d = set(tokens_d)
    novel = [t for t in tokens_d1 if t not in set_d]
    return len(novel) / len(tokens_d1)


def mud_pooled(texts_d, texts_d_plus_1, mode='word'):
    """
    Pooled MUD: union of unique tokens across all runs at depth d
    vs union across all runs at depth d+1.

    Numerator: tokens at d+1 that don't appear at d (set difference)
    Denominator: total token count at d+1 (sum of all run lengths)
    """
    extractor = extract_words if mode == 'word' else extract_bigrams

    set_d = set()
    for t in texts_d:
        set_d.update(extractor(t))

    total_d1 = 0
    novel_count = 0
    for t in texts_d_plus_1:
        toks = extractor(t)
        total_d1 += len(toks)
        novel_count += sum(1 for tok in toks if tok not in set_d)

    if total_d1 == 0:
        return None
    return novel_count / total_d1


def compute_per_run_mud(df, mode='word', axis_col='depth', order=None):
    """
    Per-run paired MUD across consecutive levels of `axis_col`.
    axis_col='depth'       -> Shallow->Deep (original behavior)
    axis_col='temperature' -> NATIVE->FIRE etc. (V7 cross-directive)
    Requires matched runs across the levels of axis_col.
    Returns DataFrame with columns:
      agent, question_id, run, level_from, level_to, mud, mode, axis
    """
    if order is None:
        order = DEPTH_ORDER_CANONICAL
    rows = []
    grouping = ['agent', 'question_id', 'run']
    for (agent, qid, run), g in df.groupby(grouping):
        present = sorted(g[axis_col].unique(),
                         key=lambda d: order.index(d) if d in order else 999)
        for i in range(len(present) - 1):
            d_from = present[i]
            d_to = present[i+1]
            t_from = g[g[axis_col] == d_from]['response_text'].iloc[0]
            t_to = g[g[axis_col] == d_to]['response_text'].iloc[0]
            mud = mud_pair(t_from, t_to, mode=mode)
            rows.append({
                'agent': agent,
                'question_id': qid,
                'run': run,
                'level_from': d_from,
                'level_to': d_to,
                'mud': mud,
                'mode': mode,
                'axis': axis_col,
            })
    return pd.DataFrame(rows)


def compute_pooled_mud(df, mode='word', axis_col='depth', order=None):
    """
    Pooled MUD per (agent, question, level_pair) along axis_col.
    Aggregates across all runs at each level. Smoother headline metric.
    """
    if order is None:
        order = DEPTH_ORDER_CANONICAL
    rows = []
    for (agent, qid), g in df.groupby(['agent', 'question_id']):
        present = sorted(g[axis_col].unique(),
                         key=lambda d: order.index(d) if d in order else 999)
        for i in range(len(present) - 1):
            d_from = present[i]
            d_to = present[i+1]
            texts_from = g[g[axis_col] == d_from]['response_text'].tolist()
            texts_to = g[g[axis_col] == d_to]['response_text'].tolist()
            mud = mud_pooled(texts_from, texts_to, mode=mode)
            rows.append({
                'agent': agent,
                'question_id': qid,
                'level_from': d_from,
                'level_to': d_to,
                'mud_pooled': mud,
                'n_runs_from': len(texts_from),
                'n_runs_to': len(texts_to),
                'mode': mode,
                'axis': axis_col,
            })
    return pd.DataFrame(rows)


# =============================================================================
# UI — UPLOAD AND ANALYZE
# =============================================================================

st.sidebar.markdown("## 📁 Upload")
uploaded = st.sidebar.file_uploader(
    "Depth-stratified CSV", type=['csv'],
    help="Required columns: agent, depth, question_id, run, response_text"
)

if not uploaded:
    st.info("Upload a depth-stratified CSV to begin. "
            "Required columns: agent, depth, question_id, run, response_text.")
    st.markdown("### What this tool computes")
    st.markdown("""
**Per-run paired MUD** — Match run #N at depth d to run #N at depth d+1.
Compute the fraction of tokens at d+1 that did not appear at d.
Yields one MUD value per run × depth-pair × mode.

**Pooled MUD** — Pool all runs at depth d into a single token set, then ask
how many tokens at d+1 (across all runs) are not in that pooled set.
Smoother, less noisy, headline metric for §4.2-style reports.

**Two modes:**
- *Word* — single-word tokens (drops function words)
- *Bigram* — adjacent word pairs (captures combinatorial novelty)
""")
    st.stop()

# Load
df = pd.read_csv(uploaded)
if 'agent' in df.columns:
    df['agent'] = df['agent'].replace({'Sophia': 'ChatGPT', 'sophia': 'ChatGPT'})

# V7: choose which ordered axis the MUD pairs walk along.
st.sidebar.markdown("## 🧭 Pairing Axis")
axis_choice = st.sidebar.radio(
    "Compute MUD across:",
    ["Depth (Shallow→Deep)", "Condition (NATIVE→FIRE)"],
    help="Depth = original novelty-by-depth. Condition = how much each agent's "
         "vocabulary moves when the directive changes (e.g. NATIVE→FIRE)."
)
if axis_choice.startswith("Condition"):
    AXIS_COL = 'temperature'
    AXIS_ORDER = CONDITION_ORDER_CANONICAL
    AXIS_LABEL = 'Condition'
else:
    AXIS_COL = 'depth'
    AXIS_ORDER = DEPTH_ORDER_CANONICAL
    AXIS_LABEL = 'Depth'

required = ['agent', AXIS_COL, 'question_id', 'run', 'response_text']
missing = [c for c in required if c not in df.columns]
if missing:
    st.error(f"Missing required columns for {AXIS_LABEL} pairing: {missing}")
    st.stop()

st.success(f"Loaded {len(df)} rows · pairing on {AXIS_LABEL} ({AXIS_COL})")

# Filters
st.sidebar.markdown("## 🎛 Filters")
agents = sorted(df['agent'].unique().tolist())
selected_agents = st.sidebar.multiselect("Agents", agents, default=agents)

questions = sorted(df['question_id'].unique().tolist())
selected_questions = st.sidebar.multiselect("Questions", questions, default=questions)

modes = st.sidebar.multiselect("Modes", ['word', 'bigram'], default=['word', 'bigram'])

filtered = df[
    df['agent'].isin(selected_agents) &
    df['question_id'].isin(selected_questions)
].copy()

# Composition summary
c1, c2, c3, c4 = st.columns(4)
c1.metric("Rows after filter", len(filtered))
c2.metric("Agents", filtered['agent'].nunique())
c3.metric("Questions", filtered['question_id'].nunique())
c4.metric(f"{AXIS_LABEL} levels", filtered[AXIS_COL].nunique())

if st.button("🚀 Compute MUD", type="primary"):
    all_per_run = []
    all_pooled = []

    with st.spinner("Computing..."):
        for mode in modes:
            per_run_df = compute_per_run_mud(filtered, mode=mode, axis_col=AXIS_COL, order=AXIS_ORDER)
            pooled_df = compute_pooled_mud(filtered, mode=mode, axis_col=AXIS_COL, order=AXIS_ORDER)
            all_per_run.append(per_run_df)
            all_pooled.append(pooled_df)

    per_run = pd.concat(all_per_run, ignore_index=True) if all_per_run else pd.DataFrame()
    pooled = pd.concat(all_pooled, ignore_index=True) if all_pooled else pd.DataFrame()

    # =========================================================================
    # POOLED RESULTS — primary headline
    # =========================================================================
    st.markdown("## 🌐 Pooled MUD (headline)")
    st.markdown("One value per (agent, question, depth-pair, mode). "
                "Smoother than per-run; recommended for cross-cell comparison.")

    if len(pooled) > 0:
        for mode in modes:
            sub = pooled[pooled['mode'] == mode]
            if len(sub) == 0:
                continue
            st.markdown(f"### {mode.title()}")

            # Pivot: rows = agent, columns = depth_pair, values = mean across questions
            sub['level_pair'] = sub['level_from'].astype(str) + ' → ' + sub['level_to'].astype(str)
            pivot = sub.pivot_table(
                index='agent', columns='level_pair',
                values='mud_pooled', aggfunc='mean'
            )
            st.dataframe(pivot.style.format("{:.3f}").background_gradient(
                cmap='viridis', axis=None), use_container_width=True)

            # Cross-question table
            st.markdown(f"#### Per-question detail ({mode})")
            st.dataframe(sub, use_container_width=True, hide_index=True)

    # =========================================================================
    # PER-RUN RESULTS — for variance estimates
    # =========================================================================
    st.markdown("## 🎯 Per-run paired MUD (variance signal)")
    st.markdown("One value per run. Use for SD, cluster analysis, error bars.")

    if len(per_run) > 0:
        for mode in modes:
            sub = per_run[per_run['mode'] == mode]
            if len(sub) == 0:
                continue
            st.markdown(f"### {mode.title()}")

            # Summary: mean ± SD per agent × depth-pair across runs and questions
            sub['level_pair'] = sub['level_from'].astype(str) + ' → ' + sub['level_to'].astype(str)
            summary = sub.groupby(['agent', 'level_pair'])['mud'].agg(
                ['mean', 'std', 'count']).reset_index()
            summary.columns = ['agent', 'level_pair', 'mean_mud', 'sd_mud', 'n']
            st.dataframe(summary.style.format(
                {'mean_mud': '{:.3f}', 'sd_mud': '{:.3f}'}),
                use_container_width=True, hide_index=True)

    # =========================================================================
    # EXPORT
    # =========================================================================
    st.markdown("## 📦 Export")

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')

    buf_pooled = io.BytesIO()
    pooled.to_csv(buf_pooled, index=False)
    st.download_button(
        f"⬇️ pooled_mud_{ts}.csv",
        buf_pooled.getvalue(),
        file_name=f"pooled_mud_{ts}.csv",
        mime="text/csv",
    )

    buf_per_run = io.BytesIO()
    per_run.to_csv(buf_per_run, index=False)
    st.download_button(
        f"⬇️ per_run_mud_{ts}.csv",
        buf_per_run.getvalue(),
        file_name=f"per_run_mud_{ts}.csv",
        mime="text/csv",
    )

    # Combined manifest
    manifest = {
        'tool': 'syniq_linguistic_topology_v6',
        'generated_at': datetime.now().isoformat(),
        'modes': modes,
        'agents': selected_agents,
        'questions': selected_questions,
        'n_rows_input': len(filtered),
        'n_per_run_mud_values': len(per_run),
        'n_pooled_mud_values': len(pooled),
        'depth_order': DEPTH_ORDER_CANONICAL,
        'function_words_dropped': True,
    }
    st.download_button(
        f"⬇️ mud_manifest_{ts}.json",
        json.dumps(manifest, indent=2),
        file_name=f"mud_manifest_{ts}.json",
        mime="application/json",
    )

st.markdown("---")
st.caption("SYN-IQ Linguistic Topology V7 · Tennessee 🎹 CUZ Partnership · May 2026")
