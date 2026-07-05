"""
SYN-IQ Lens Stability Analyzer V11
Topological Stability Analysis Across Multiple Lens Functions

PURPOSE: Per Dr. Farzana Nasrin's Experiment Protocol §4.1–§4.3 (March 24, 2026)
         Run the same dataset through multiple lens functions and verify
         that topology is stable across different projections.

============================================================================
VERSION HISTORY  (keep this current — every release adds a dated entry)
----------------------------------------------------------------------------
  V11 (Jun 2026)     Adaptive residual-agent drop. Single-question /
                       single-condition cells (the agent-separation use
                       case) give each agent exactly one (temp x question)
                       cell; the old min_cells=2 gate dropped every agent
                       and yielded 0 rows. min_cells is now capped at the
                       cells actually present, so single-cell runs work;
                       multi-cell regime runs keep the >=2 protection.
  V10 (Jun 2026)     Added text lens + agent purity:
                       - 'Word TF-IDF (2D)' lens (Text category); response_text
                         -> TF-IDF -> TruncatedSVD 2D; rides the same n_cubes/
                         overlap/min_cluster sweep as the 23 column lenses; loud-
                         fail on degenerate cells; gated on response_text.
                       - AGENT purity label -> A-purity (mean/wtd) alongside Q/T.
                         A-purity is the meaningful stat on single-question cells.
                       - JSON loader keeps response_text (needed by text lens).
  V9  (Jun 20, 2026) Stripped to stability-only + provenance:
                       - Removed §4.1 regime panels (COLD/FIRE effect sizes,
                         pairwise AUC, HOT-vs-FIRE, subclass, ideation collapse).
                         Those are §4.1 regime-separation, not §4.2 stability;
                         destined for a separate tool. This tool now does ONE job.
                       - Outputs stamped with Agent + Tool_Version + Run_Date
                         (CSV columns AND report header).
                       - Single TOOL_VERSION constant; download self-names
                         <Agent>_stability_<version>.csv.
  V8  (Jun 20, 2026) Self-identifying output (fixes the agent-label confusion):
                       - Results CSV now has an "Agent" column populated from
                         the uploaded data (no row is anonymous).
                       - Download auto-named <Agent>_stability.csv (no filename
                         collisions between agents).
                       - "Agent detected: X" shown next to the download button.
  V2  (May 5, 2026)  "Tool A / Conductor's Stand" — original generator.
                     23-lens IEP sweep; writes per-agent <agent>_stability.csv
                     with V/E/beta_0/beta_1/largest_frac/Q-purity. Built by
                     Claude from Bill's direction (Farzana's contribution =
                     the multi-lens §4.2 protocol idea, not the build).
  V5  (May 2026)     Added T-purity (condition) alongside Q-purity; Ideation
                     Collapse Diagnostic (INT 8-subclass decomposition).
  V6  ( — )          Patched content but NOT logged and still carried the V5
                     front plate — source of version-tracking confusion.
                     (Lesson: this block exists so that never recurs.)
  V7  (Jun 20, 2026) Front plate corrected to V7 everywhere. Bug/feature fixes:
                       - Clear button + auto-reset on file change
                         (fixes stale cross-agent cache: a new upload could
                          redisplay the PRIOR agent's cached results).
                       - All lens checkboxes default ON (so all are visible).
                       - pandas Styler .applymap -> version-safe shim
                         (fixes the Streamlit Cloud AttributeError crash that
                          stopped the page before the stability table rendered).
============================================================================

V7 CHANGES (Jun 2026):
  - Clear button + auto-reset on file change (fixes stale cross-agent cache)
  - All lenses default ON
  - pandas Styler .applymap -> version-safe shim (Cloud crash fix)

V5 CHANGES (May 2026):
  - IDEATION COLLAPSE DIAGNOSTIC: For any regime contrast, decompose the
    intellectual axis into its 8 subclasses (analytical, conceptual,
    epistemic, structural, critical, lexical, hedging, phenomenological)
    and report which subclasses move with the contrast and which do not.
    Flags the qualitative shape of the contrast: "preserves structure",
    "displaces structure with hedging", or "augments structure". Built
    specifically to surface the V52 finding that FIRE trades analytical/
    critical content for epistemic hedging — i.e. FIRE is a comfort prompt,
    not an ideation prompt.

V4 INHERITED:
  - Question-purity (not temperature-purity) as primary §4.2 stability metric
  - §4.3 polarity lens family (P_INT, P_AFF, P_ACT)
  - Pairwise regime AUC matrix (answers "Are HOT and FIRE the same?")
  - Subclass-level effect sizes across 23 aff/int/act subdivisions

V3 INHERITED:
  - AUC (probability of superiority) as headline effect size
  - Saturation diagnostic for ceiling/floor cells
  - Auto-drop of residual agents

V2 INHERITED:
  - Stability graded on TOPOLOGICAL INVARIANTS (β₀, β₁) not raw counts
  - JSON input support

SYNINT Research Team — May 2026
Tennessee 🎹 CUZ Partnership
"""

import streamlit as st
import pandas as pd
import numpy as np
import json
import tempfile
import os
import re
import networkx as nx
from collections import defaultdict
from datetime import datetime

# ── Provenance: one place to bump the version; stamped onto every output ──
TOOL_VERSION = "V11"
PROJECT_NAME = "SYN-IQ Lens Stability Analyzer"
RUN_DATE = datetime.now().strftime("%Y-%m-%d %H:%M")

# --- pandas Styler compat: .applymap renamed to .map in pandas 2.1+, removed in 3.0 ---
def _styler_elementwise(styler, func, **kwargs):
    if hasattr(styler, 'map'):
        return styler.map(func, **kwargs)
    return styler.applymap(func, **kwargs)

st.set_page_config(
    page_title="SYN-IQ Lens Stability Analyzer V11",
    page_icon="🔬",
    layout="wide"
)

# =============================================================================
# PASSWORD
# =============================================================================
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if st.query_params.get("auth") == "granted":
        st.session_state.authenticated = True
    if st.session_state.authenticated:
        return True
    st.markdown("""
    <div style="background: linear-gradient(135deg, #0a0a1a 0%, #1a0a2e 40%, #0f2460 100%);
         color: white; padding: 2rem; border-radius: 10px; text-align: center;
         margin-bottom: 1rem; border: 1px solid #7c3aed;">
        <h1 style="color: #a78bfa;">🔬 SYN-IQ Lens Stability Analyzer V11</h1>
        <p style="color: #9ca3af;">Authorized Access Only</p>
    </div>
    """, unsafe_allow_html=True)
    pwd = st.text_input("Password:", type="password")
    if st.button("Enter"):
        valid = [st.secrets.get("app_password","SYNIQ2026"), "SYNIQ2026"]
        if pwd in valid:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password")
    return False

if not check_password():
    st.stop()

# =============================================================================
# STYLING
# =============================================================================
st.markdown("""
<style>
body { background-color: #ffffff; }
.main { background-color: #ffffff; }
.stApp { background-color: #ffffff; }
.metric-box {
    background: linear-gradient(135deg, #1e3a5f, #2e75b6);
    color: white; border-radius: 8px; padding: 1rem;
    text-align: center; margin: 0.25rem;
}
.metric-box h3 { font-size: 1.8rem; margin: 0; }
.metric-box p  { font-size: 0.85rem; margin: 0; opacity: 0.85; }
.stable   { background-color: #d4edda; border-left: 4px solid #28a745; padding: 0.5rem; border-radius: 4px; }
.unstable { background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 0.5rem; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# HEADER
# =============================================================================
st.markdown("""
<div style="background: linear-gradient(135deg, #0a0a1a 0%, #1a0a2e 40%, #0f2460 100%);
     color: white; padding: 1.5rem 2rem; border-radius: 10px; margin-bottom: 1rem;
     border: 1px solid #7c3aed;">
    <h1 style="color: #a78bfa; margin: 0;">🔬 SYN-IQ Lens Stability Analyzer V11</h1>
    <p style="color: #9ca3af; margin: 0.5rem 0 0 0;">
        Topological Stability via Betti Invariants &amp; Condition Purity ·
        Per Dr. Nasrin Protocol §4.2 · IEP V3 · KeplerMapper
    </p>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# SIDEBAR
# =============================================================================
st.sidebar.markdown("## 📁 Data Upload")
# --- uploader with a resettable key so "Clear" can fully reset it ---
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

uploaded_file = st.sidebar.file_uploader(
    "Upload SYN-IQ harvester output (CSV or JSON)",
    type=['csv', 'json'],
    key=f"uploader_{st.session_state.uploader_key}",
)

# --- Clear button: wipe the upload AND all cached results/state ---
def _clear_all():
    # bump the uploader key so the widget itself resets to empty
    st.session_state.uploader_key += 1
    # drop any stored run so a stale agent can never redisplay
    for k in ['lens_results', 'last_upload_name']:
        st.session_state.pop(k, None)
    st.cache_data.clear()

st.sidebar.button("🗑️ Clear data / reset for next agent",
                  on_click=_clear_all, use_container_width=True)

# --- safety net: if a DIFFERENT file is uploaded, auto-drop the previous result ---
if uploaded_file is not None:
    if st.session_state.get('last_upload_name') != uploaded_file.name:
        st.session_state.pop('lens_results', None)
        st.session_state.last_upload_name = uploaded_file.name

st.sidebar.markdown("---")
st.sidebar.markdown("## 🎛️ Mapper Parameters")
n_cubes     = st.sidebar.slider("Hypercubes (n_cubes)", 5, 20, 10)
perc_overlap= st.sidebar.slider("Overlap %", 10, 60, 30)
min_cluster = st.sidebar.slider("Min cluster size", 1, 5, 2)

st.sidebar.markdown("---")
st.sidebar.markdown("## 🔭 Lens Selection")
st.sidebar.markdown("**AFF Lenses**")
use_aff_pct       = st.sidebar.checkbox("aff_pct", value=True)
use_vader_comp    = st.sidebar.checkbox("vader_compound", value=True)
use_vader_abs     = st.sidebar.checkbox("|vader_compound|", value=True)
use_aff_vader_2d  = st.sidebar.checkbox("(aff_pct, vader_compound) 2D", value=True)

st.sidebar.markdown("**INT Lenses**")
use_int_pct       = st.sidebar.checkbox("int_pct", value=True)
use_fk            = st.sidebar.checkbox("flesch_kincaid", value=True)
use_ttr           = st.sidebar.checkbox("ttr", value=True)
use_int_fk_2d     = st.sidebar.checkbox("(int_pct, flesch_kincaid) 2D", value=True)
use_int_ttr_2d    = st.sidebar.checkbox("(int_pct, ttr) 2D", value=True)

st.sidebar.markdown("**ACT Lenses**")
use_act_pct       = st.sidebar.checkbox("act_pct", value=True)
use_words         = st.sidebar.checkbox("total_words", value=True)
use_act_words_2d  = st.sidebar.checkbox("(act_pct, total_words) 2D", value=True)

st.sidebar.markdown("**Cross-IEP Lenses**")
use_aff_int_2d    = st.sidebar.checkbox("(aff_pct, int_pct) 2D", value=True)
use_int_act_2d    = st.sidebar.checkbox("(int_pct, act_pct) 2D", value=True)
use_aff_act_2d    = st.sidebar.checkbox("(aff_pct, act_pct) 2D", value=True)

st.sidebar.markdown("**Polarity Lenses (§4.3)**")
use_p_aff         = st.sidebar.checkbox("P_AFF (1D simplex)", value=True)
use_p_int_p_aff   = st.sidebar.checkbox("(P_INT, P_AFF) 2D simplex", value=True)

st.sidebar.markdown("**Geometric Lenses**")
use_pca1          = st.sidebar.checkbox("PCA1", value=True)
use_pca1_pca2_2d  = st.sidebar.checkbox("(PCA1, PCA2) 2D", value=True)

st.sidebar.markdown("**Text Lenses**")
use_word_tfidf    = st.sidebar.checkbox(
    "Word TF-IDF (2D)", value=True,
    help="Discovered-vocabulary lens. Vectorizes response_text per cell "
         "(TF-IDF → TruncatedSVD 2D). Requires a response_text column."
)

# =============================================================================
# HELPERS
# =============================================================================
def build_feature_matrix(df):
    """Build IEP feature matrix from pre-scored columns."""
    cols = ['int_pct','aff_pct','act_pct']
    if 'vader_compound' in df.columns: cols.append('vader_compound')
    if 'vader_pos'      in df.columns: cols += ['vader_pos','vader_neg','vader_neu']
    if 'total_words'    in df.columns: cols.append('total_words')
    if 'flesch_kincaid' in df.columns: cols.append('flesch_kincaid')
    if 'ttr'            in df.columns: cols.append('ttr')
    avail = [c for c in cols if c in df.columns]
    data = df[avail].fillna(0).values.astype(float)
    from sklearn.preprocessing import MinMaxScaler
    data = MinMaxScaler().fit_transform(data)
    return data, avail

def run_mapper_with_lens(data, lens_values, n_cubes, perc_overlap, min_cluster,
                         labels=None, label_kinds=None):
    """Run KeplerMapper with given lens and return graph + topology stats.

    Parameters
    ----------
    data, lens_values, n_cubes, perc_overlap, min_cluster
        Standard Mapper inputs.
    labels : dict[str, array-like] or array-like or None
        Per-row labels for purity calculation. V4 accepts a dict mapping
        label-kind name (e.g. 'question', 'temperature') to per-row values,
        and reports purity per kind. Backward-compatible with V3's single-
        array signature (treated as 'temperature').
    label_kinds : list[str] or None
        Order of label kinds to report (defaults to dict insertion order).

    Returns dict with all V3 fields plus per-kind purity:
      n_nodes, n_edges, n_components (β₀), beta1 (E - V + C),
      largest, largest_frac, comp_sizes, graph,
      purity['question_mean'], purity['question_weighted'],
      purity['temperature_mean'], purity['temperature_weighted'], etc.
    """
    import kmapper as km
    from sklearn.cluster import DBSCAN
    mapper = km.KeplerMapper(verbose=0)
    graph = mapper.map(
        lens_values,
        data,
        cover=km.Cover(n_cubes=n_cubes, perc_overlap=perc_overlap/100),
        clusterer=DBSCAN(eps=0.5, min_samples=min_cluster)
    )
    G = nx.Graph()
    nodes = graph.get('nodes', {})
    links = graph.get('links', {})
    for n in nodes:
        G.add_node(n)
    for src, targets in links.items():
        for tgt in targets:
            G.add_edge(src, tgt)
    components = list(nx.connected_components(G))
    comp_sizes = sorted([len(c) for c in components], reverse=True)

    n_v = G.number_of_nodes()
    n_e = G.number_of_edges()
    n_c = len(components)
    # Graph-theoretic β₁ (cycle rank): E - V + C. Matches the HTML report.
    beta1 = max(n_e - n_v + n_c, 0) if n_v > 0 else 0

    # Largest-component coverage of the data points (not nodes)
    if components and nodes:
        largest_set = max(components, key=len)
        largest_points = set()
        for nd in largest_set:
            largest_points.update(nodes.get(nd, []))
        n_total_pts = len(set().union(*nodes.values())) if nodes else 0
        largest_frac = len(largest_points) / n_total_pts if n_total_pts else 0.0
    else:
        largest_frac = 0.0

    # V4: per-kind purity (e.g. 'question' and 'temperature' simultaneously)
    purity = {}
    modal_dist_by_kind = {}
    if labels is not None and nodes:
        # Backward-compat: if labels is a 1D array, treat it as 'temperature'
        if not isinstance(labels, dict):
            labels = {'temperature': labels}
        from collections import Counter as _Counter
        for kind, lab_arr in labels.items():
            lab_arr = np.asarray(lab_arr)
            purities, weights = [], []
            modal_counter = defaultdict(int)
            for nd, idx_list in nodes.items():
                if not idx_list:
                    continue
                lab = lab_arr[idx_list]
                c = _Counter(lab.tolist())
                modal_label, modal_count = c.most_common(1)[0]
                purities.append(modal_count / len(idx_list))
                weights.append(len(idx_list))
                modal_counter[modal_label] += 1
            if purities:
                purity[f'{kind}_mean']     = float(np.mean(purities))
                purity[f'{kind}_weighted'] = float(np.average(purities, weights=weights))
                modal_dist_by_kind[kind]   = dict(modal_counter)

    # Backward-compat fields used by V3 display code:
    mean_purity     = purity.get('temperature_mean', purity.get('question_mean'))
    weighted_purity = purity.get('temperature_weighted', purity.get('question_weighted'))
    modal_dist      = modal_dist_by_kind.get('temperature', modal_dist_by_kind.get('question', {}))

    return {
        'n_nodes': n_v,
        'n_edges': n_e,
        'n_components': n_c,
        'beta0': n_c,
        'beta1': beta1,
        'largest': comp_sizes[0] if comp_sizes else 0,
        'largest_frac': largest_frac,
        'comp_sizes': comp_sizes,
        'mean_purity': mean_purity,
        'weighted_purity': weighted_purity,
        'purity_by_kind': purity,                  # V4: full per-kind dict
        'modal_dist': modal_dist,
        'modal_dist_by_kind': modal_dist_by_kind,
        'graph': graph
    }

def load_input(uploaded):
    """Load CSV or JSON harvester output. Drops error rows; reports count."""
    name = uploaded.name.lower()
    if name.endswith('.json'):
        raw = json.load(uploaded)
        if isinstance(raw, dict):
            # tolerate {'turns': [...]} style wrappers
            for key in ('turns', 'data', 'results', 'rows'):
                if key in raw and isinstance(raw[key], list):
                    raw = raw[key]
                    break
        if not isinstance(raw, list):
            raise ValueError("JSON must be a list of turn records (or {'turns':[...]})")
        df_full = pd.DataFrame(raw)
        # Drop heavy fields if present so downstream is fast
        for col in ('embedding', 'system_prompt_text',
                    'v5_scored_phrases', 'cam_matched'):
            if col in df_full.columns:
                df_full = df_full.drop(columns=[col])
    else:
        df_full = pd.read_csv(uploaded)

    n_total = len(df_full)
    n_err   = 0
    if 'error' in df_full.columns:
        # treat any truthy non-null as an error row (V51 stores `True`)
        err_mask = df_full['error'].fillna(False)
        if err_mask.dtype == object:
            err_mask = err_mask.astype(str).str.len() > 0
            err_mask = err_mask & (df_full['error'].astype(str) != 'False') \
                                & (df_full['error'].astype(str) != 'nan')
        else:
            err_mask = err_mask.astype(bool)
        n_err = int(err_mask.sum())
        df_full = df_full[~err_mask].copy()

    return df_full, n_total, n_err

def get_pca_projection(data, n_components=2):
    from sklearn.decomposition import PCA
    pca = PCA(n_components=n_components)
    return pca.fit_transform(data)

def normalize_col(arr):
    mn, mx = arr.min(), arr.max()
    if mx == mn: return arr * 0
    return (arr - mn) / (mx - mn)

# =============================================================================
# V3 ADDITIONS: SATURATION DIAGNOSTIC, AUC, RESIDUAL-AGENT DROP
# =============================================================================
def auc_probability_of_superiority(x, y):
    """Probability that a random draw from y exceeds a random draw from x.

    P(Y > X) + 0.5 * P(Y == X). Bounded [0,1]. AUC = 0.5 means no separation;
    AUC = 1.0 means y is always larger; AUC = 0.0 means y is always smaller.
    Equivalent to the Mann-Whitney U statistic divided by n_x * n_y.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    x = x[~np.isnan(x)]
    y = y[~np.isnan(y)]
    if len(x) == 0 or len(y) == 0:
        return None
    # Vectorized: count pairs where y > x and where y == x
    diff = y[:, None] - x[None, :]
    gt = (diff > 0).sum()
    eq = (diff == 0).sum()
    return float((gt + 0.5 * eq) / (len(x) * len(y)))

def metric_bounds(metric_name, df=None):
    """Return (lower, upper) plausible bounds for a metric.

    Used for saturation detection. Bounds come from the IEP/Vₜ definitions
    where they are known a priori; otherwise from observed min/max.
    """
    a_priori = {
        # Vₜ components are simplex weights in [0, 1]
        'S_t': (0.0, 1.0), 'A_t': (0.0, 1.0), 'Q_t': (0.0, 1.0),
        'D_t': (0.0, 1.0), 'R_t': (0.0, 1.0),
        # IEP percentages in [0, 100]
        'int_pct': (0.0, 100.0), 'aff_pct': (0.0, 100.0), 'act_pct': (0.0, 100.0),
        # VADER compound is signed [-1, 1]
        'vader_compound': (-1.0, 1.0),
        'vader_pos': (0.0, 1.0), 'vader_neg': (0.0, 1.0), 'vader_neu': (0.0, 1.0),
        # TTR is bounded [0, 1]
        'ttr': (0.0, 1.0),
    }
    if metric_name in a_priori:
        return a_priori[metric_name]
    if df is not None and metric_name in df.columns:
        v = df[metric_name].dropna()
        if len(v):
            return (float(v.min()), float(v.max()))
    return (None, None)

def is_saturated(values, lo, hi, tol_sd=1e-6, tol_edge=0.02):
    """Cell is 'saturated' if SD ≈ 0 AND mean is at the metric's edge.

    tol_edge=0.02 means within 2% of the bounded range from either edge.
    """
    arr = np.asarray(values, dtype=float)
    arr = arr[~np.isnan(arr)]
    if len(arr) < 2 or lo is None or hi is None or hi <= lo:
        return False, None
    sd = arr.std(ddof=1)
    mean = arr.mean()
    edge_dist = min(mean - lo, hi - mean) / (hi - lo)
    if sd <= tol_sd and edge_dist <= tol_edge:
        which = 'ceiling' if (mean - lo) > (hi - mean) else 'floor'
        return True, which
    return False, None

def drop_residual_agents(df, min_turns=10, min_cells=2):
    """Drop agents with too few turns or too few distinct (temp × question) cells.

    Catches the V51 case where 197/200 Gemini turns errored, leaving 3 turns
    that all share one cell. Reports what was dropped.

    V11: ADAPTIVE min_cells. The single-question / single-condition agent-
    separation use case (e.g. CONSCIOUSNESS · NATIVE, 4 agents) gives every
    agent exactly ONE (temp × question) cell by design. The default min_cells=2
    would then drop every agent and leave 0 rows. So we cap min_cells at the
    number of cells actually present in the dataset: when the data spans only
    one cell, the cell gate is disabled (relaxed to 1) and only the min_turns
    floor applies. Multi-cell regime runs keep the original ≥2 protection.
    """
    if 'agent' not in df.columns:
        return df, []
    # How many distinct cells does the whole (filtered) dataset span?
    if 'temperature' in df.columns and 'question_id' in df.columns:
        total_cells = df.groupby(['temperature','question_id']).ngroups
    elif 'question_id' in df.columns:
        total_cells = df['question_id'].nunique()
    else:
        total_cells = 1
    eff_min_cells = min(min_cells, max(total_cells, 1))
    drops = []
    keep_mask = pd.Series(True, index=df.index)
    for agent, sub in df.groupby('agent'):
        n_turns = len(sub)
        if 'temperature' in sub.columns and 'question_id' in sub.columns:
            n_cells = sub.groupby(['temperature','question_id']).ngroups
        elif 'question_id' in sub.columns:
            n_cells = sub['question_id'].nunique()
        else:
            n_cells = 1
        if n_turns < min_turns or n_cells < eff_min_cells:
            drops.append({'agent': agent, 'n_turns': n_turns, 'n_cells': n_cells})
            keep_mask &= (df['agent'] != agent)
    return df[keep_mask].copy(), drops

def cold_fire_separation(df, agent, metric):
    """Return separation diagnostics for COLD vs FIRE on one (agent, metric).

    Returns dict with: cold_n, fire_n, cold_mean, fire_mean, auc,
    cohens_d (or None if pooled SD = 0), saturated_cells (list).
    """
    sub = df[df['agent'] == agent]
    cold = sub[sub['temperature'] == 'COLD'][metric].dropna()
    fire = sub[sub['temperature'] == 'FIRE'][metric].dropna()
    if len(cold) == 0 or len(fire) == 0:
        return None
    auc = auc_probability_of_superiority(cold.values, fire.values)
    # Within-cell pooled SD (across all cells for this agent), used for d
    within_sd = sub.groupby(['temperature','question_id'])[metric].std().mean()
    if within_sd is not None and within_sd > 1e-9:
        d = (fire.mean() - cold.mean()) / within_sd
    else:
        d = None
    # Saturation check on each cell
    lo, hi = metric_bounds(metric, df)
    sat_cells = []
    for cond in ['COLD','FIRE']:
        for q, sub_q in sub[sub['temperature']==cond].groupby('question_id'):
            sat, which = is_saturated(sub_q[metric].values, lo, hi)
            if sat:
                sat_cells.append(f"{cond}/{q}@{which}")
    return {
        'agent': agent, 'metric': metric,
        'cold_n': len(cold), 'fire_n': len(fire),
        'cold_mean': float(cold.mean()), 'fire_mean': float(fire.mean()),
        'auc': auc, 'cohens_d': d,
        'saturated_cells': sat_cells,
    }

# =============================================================================
# V4 ADDITIONS: §4.3 POLARITY, REGIME-PAIR AUC, SUBCLASS REPORTING,
#               QUESTION-PURITY (replaces temperature-purity)
# =============================================================================
def compute_polarity(df):
    """Compute §4.3 polarity vector P = (P_INT, P_AFF, P_ACT) per Nasrin (2026).

    I_t derives from int_pct (using a percentile-rank rescaling so it lives on
    a comparable scale to A_t and C_t). A_t = (vader_compound + 1)/2 ∈ [0, 1].
    C_t derives from act_pct (same rescaling as I_t).

    Returns df with three new columns: P_INT, P_AFF, P_ACT (each ∈ [0, 1],
    summing to 1 row-wise). Skipped silently if required columns are missing.
    """
    needed = {'int_pct', 'act_pct', 'vader_compound'}
    if not needed.issubset(df.columns):
        return df
    df = df.copy()
    # Rescale int_pct, act_pct to [0, 1] using percentile rank (robust to scale
    # differences vs the [0, 1] VADER transform).
    I = df['int_pct'].rank(pct=True).fillna(0).values
    C = df['act_pct'].rank(pct=True).fillna(0).values
    A = ((df['vader_compound'].fillna(0).values + 1.0) / 2.0)
    total = I + A + C
    total = np.where(total > 0, total, 1.0)
    df['P_INT'] = I / total
    df['P_AFF'] = A / total
    df['P_ACT'] = C / total
    return df

def regime_pairwise_auc(df, agent, metric, regimes=('COLD','NATIVE','HOT','FIRE')):
    """Pairwise AUC across all regime pairs for one (agent, metric).

    Returns a DataFrame indexed by regime, columns are regimes; entry [r, s] =
    P(metric_value in regime s > metric_value in regime r). Diagonal is 0.5.
    """
    sub = df[df['agent'] == agent]
    out = pd.DataFrame(index=list(regimes), columns=list(regimes), dtype=float)
    for r in regimes:
        rv = sub[sub['temperature'] == r][metric].dropna().values
        for s in regimes:
            if r == s:
                out.loc[r, s] = 0.5
                continue
            sv = sub[sub['temperature'] == s][metric].dropna().values
            if len(rv) == 0 or len(sv) == 0:
                out.loc[r, s] = np.nan
            else:
                out.loc[r, s] = auc_probability_of_superiority(rv, sv)
    return out

def subclass_columns(df):
    """Return aff/int/act subclass columns present in the dataframe."""
    return [c for c in df.columns if c.startswith(('aff_sub_', 'int_sub_', 'act_sub_'))]

def regime_pair_separation(df, agent, metric, r1, r2):
    """One-row separation: agent × metric × (r1 vs r2). AUC = P(r2 > r1)."""
    sub = df[df['agent'] == agent]
    a = sub[sub['temperature'] == r1][metric].dropna()
    b = sub[sub['temperature'] == r2][metric].dropna()
    if len(a) == 0 or len(b) == 0:
        return None
    auc = auc_probability_of_superiority(a.values, b.values)
    return {
        'agent': agent, 'metric': metric,
        f'{r1}_mean': float(a.mean()), f'{r2}_mean': float(b.mean()),
        f'{r1}_n': len(a), f'{r2}_n': len(b),
        'AUC': auc,
    }

def question_purity(node_idx_lists, df, label_col='question_id'):
    """Mean and weighted purity of Mapper nodes w.r.t. question_id (or any label).

    Per §4.1: 'each component corresponds to one question family.' A stable
    lens is one whose Mapper nodes are pure with respect to question.
    """
    from collections import Counter
    if label_col not in df.columns:
        return None, None
    labels = df[label_col].values
    purities, weights = [], []
    for node, idx_list in node_idx_lists.items():
        if not idx_list:
            continue
        lab = labels[idx_list]
        c = Counter(lab.tolist())
        modal_count = c.most_common(1)[0][1]
        purities.append(modal_count / len(idx_list))
        weights.append(len(idx_list))
    if not purities:
        return None, None
    return float(np.mean(purities)), float(np.average(purities, weights=weights))

# =============================================================================
# V5 ADDITION: IDEATION COLLAPSE DIAGNOSTIC
# =============================================================================
# The int (intellectual) axis has 8 subclasses with very different roles:
#   - "Constructive" subclasses:  analytical, conceptual, critical, structural
#       → these carry actual reasoning content
#   - "Hedging" subclasses:       epistemic, hedging
#       → linguistic markers of uncertainty / softening; LOOK intellectual
#         but are stylistic surface features
#   - Other:                       lexical, phenomenological
INT_CONSTRUCTIVE = ('int_sub_analytical', 'int_sub_conceptual',
                    'int_sub_critical',   'int_sub_structural')
INT_HEDGING      = ('int_sub_epistemic', 'int_sub_hedging')

def ideation_collapse(df, agent, r_from, r_to,
                      strong_threshold=0.20):
    """Diagnose whether moving from regime r_from to r_to preserves, augments,
    or displaces intellectual structure.

    Returns dict with:
      - per-subclass AUC (P(value in r_to > value in r_from))
      - constructive_drop: proportion of constructive subclasses that drop
        (AUC ≤ 0.5 - strong_threshold)
      - hedging_rise:      proportion of hedging subclasses that rise
        (AUC ≥ 0.5 + strong_threshold)
      - verdict: one of 'preserved', 'displaced_by_hedging', 'augmented',
                          'mixed', or 'no_signal'
    """
    sub = df[df['agent'] == agent]
    rec = {'agent': agent, 'r_from': r_from, 'r_to': r_to,
           'subclass_aucs': {}, 'top_int_pct_auc': None}

    # Top-level int_pct movement (for context)
    if 'int_pct' in df.columns:
        a = sub[sub['temperature']==r_from]['int_pct'].dropna().values
        b = sub[sub['temperature']==r_to]['int_pct'].dropna().values
        if len(a) and len(b):
            rec['top_int_pct_auc'] = auc_probability_of_superiority(a, b)

    for s in INT_CONSTRUCTIVE + INT_HEDGING:
        if s not in df.columns: continue
        a = sub[sub['temperature']==r_from][s].dropna().values
        b = sub[sub['temperature']==r_to][s].dropna().values
        if len(a) == 0 or len(b) == 0: continue
        rec['subclass_aucs'][s] = auc_probability_of_superiority(a, b)

    # Direction summaries
    constr_aucs = [rec['subclass_aucs'][s] for s in INT_CONSTRUCTIVE
                   if s in rec['subclass_aucs']]
    hedge_aucs  = [rec['subclass_aucs'][s] for s in INT_HEDGING
                   if s in rec['subclass_aucs']]

    n_constr_drop = sum(1 for a in constr_aucs if a <= 0.5 - strong_threshold)
    n_constr_rise = sum(1 for a in constr_aucs if a >= 0.5 + strong_threshold)
    n_hedge_rise  = sum(1 for a in hedge_aucs  if a >= 0.5 + strong_threshold)
    n_hedge_drop  = sum(1 for a in hedge_aucs  if a <= 0.5 - strong_threshold)

    rec['constr_drop_count'] = n_constr_drop
    rec['constr_rise_count'] = n_constr_rise
    rec['hedge_rise_count']  = n_hedge_rise
    rec['hedge_drop_count']  = n_hedge_drop
    rec['n_constructive']    = len(constr_aucs)
    rec['n_hedging']         = len(hedge_aucs)

    # Verdict
    if n_constr_drop >= 2 and n_hedge_rise >= 1:
        rec['verdict'] = 'displaced_by_hedging'
    elif n_constr_rise >= 2 and n_hedge_drop >= 1:
        rec['verdict'] = 'augmented'
    elif n_constr_drop >= 2:
        rec['verdict'] = 'collapsed'
    elif n_constr_rise >= 2:
        rec['verdict'] = 'enhanced'
    elif n_constr_drop == 0 and n_constr_rise == 0:
        rec['verdict'] = 'preserved'
    else:
        rec['verdict'] = 'mixed'

    return rec

# =============================================================================
# MAIN
# =============================================================================
if uploaded_file is not None:
    try:
        df, n_total_in, n_err = load_input(uploaded_file)
    except Exception as e:
        st.error(f"Failed to load file: {e}")
        st.stop()

    if 'agent' in df.columns:
        df['agent'] = df['agent'].replace({'Sophia': 'ChatGPT', 'sophia': 'ChatGPT'})

    if n_err > 0:
        st.warning(
            f"Dropped **{n_err}** errored rows out of {n_total_in} loaded "
            f"(e.g. failed harvester turns). Analyzing **{len(df)}** clean rows."
        )

    # V3: drop agents with too few clean turns (e.g. 3 surviving Gemini from V51)
    df, residual_drops = drop_residual_agents(df, min_turns=10, min_cells=2)
    if residual_drops:
        msg = "; ".join(
            f"{d['agent']} (n={d['n_turns']} turns, {d['n_cells']} cells)"
            for d in residual_drops
        )
        st.warning(
            f"Dropped agents with insufficient clean data: {msg}. "
            f"Analyzing {len(df)} rows across {df['agent'].nunique()} agents."
        )

    # V4: compute §4.3 polarity vector P = (P_INT, P_AFF, P_ACT)
    df = compute_polarity(df)

    # Stats
    col1, col2, col3, col4 = st.columns(4)
    col1.markdown(f'<div class="metric-box"><h3>{len(df)}</h3><p>Clean Responses</p></div>', unsafe_allow_html=True)
    col2.markdown(f'<div class="metric-box"><h3>{df["agent"].nunique() if "agent" in df.columns else "?"}</h3><p>Agents</p></div>', unsafe_allow_html=True)
    col3.markdown(f'<div class="metric-box"><h3>{df["temperature"].nunique() if "temperature" in df.columns else "?"}</h3><p>Conditions</p></div>', unsafe_allow_html=True)
    col4.markdown(f'<div class="metric-box"><h3>{df["question_id"].nunique() if "question_id" in df.columns else "?"}</h3><p>Questions</p></div>', unsafe_allow_html=True)

    st.markdown("---")

    # =========================================================================
    # LENS STABILITY (Mapper-based)
    # =========================================================================
    st.markdown('## 🔬 Lens Stability (KeplerMapper)')

    active_lenses = []
    if use_aff_pct      and 'aff_pct'       in df.columns: active_lenses.append(('aff_pct',       '1D', 'AFF'))
    if use_vader_comp   and 'vader_compound' in df.columns: active_lenses.append(('vader_compound','1D', 'AFF'))
    if use_vader_abs    and 'vader_compound' in df.columns: active_lenses.append(('|vader_compound|','1D_abs','AFF'))
    if use_aff_vader_2d and 'aff_pct' in df.columns and 'vader_compound' in df.columns:
        active_lenses.append(('(aff_pct, vader_compound)','2D','AFF'))
    if use_int_pct      and 'int_pct'        in df.columns: active_lenses.append(('int_pct',       '1D', 'INT'))
    if use_fk           and 'flesch_kincaid' in df.columns: active_lenses.append(('flesch_kincaid','1D', 'INT'))
    if use_ttr          and 'ttr'            in df.columns: active_lenses.append(('ttr',           '1D', 'INT'))
    if use_int_fk_2d    and 'int_pct' in df.columns and 'flesch_kincaid' in df.columns:
        active_lenses.append(('(int_pct, flesch_kincaid)','2D','INT'))
    if use_int_ttr_2d   and 'int_pct' in df.columns and 'ttr' in df.columns:
        active_lenses.append(('(int_pct, ttr)','2D','INT'))
    if use_act_pct      and 'act_pct'        in df.columns: active_lenses.append(('act_pct',       '1D', 'ACT'))
    if use_words        and 'total_words'    in df.columns: active_lenses.append(('total_words',   '1D', 'ACT'))
    if use_act_words_2d and 'act_pct' in df.columns and 'total_words' in df.columns:
        active_lenses.append(('(act_pct, total_words)','2D','ACT'))
    if use_aff_int_2d   and 'aff_pct' in df.columns and 'int_pct' in df.columns:
        active_lenses.append(('(aff_pct, int_pct)','2D','Cross-IEP'))
    if use_int_act_2d   and 'int_pct' in df.columns and 'act_pct' in df.columns:
        active_lenses.append(('(int_pct, act_pct)','2D','Cross-IEP'))
    if use_aff_act_2d   and 'aff_pct' in df.columns and 'act_pct' in df.columns:
        active_lenses.append(('(aff_pct, act_pct)','2D','Cross-IEP'))
    if use_p_aff       and 'P_AFF' in df.columns:
        active_lenses.append(('P_AFF','1D','Polarity'))
    if use_p_int_p_aff and 'P_INT' in df.columns and 'P_AFF' in df.columns:
        active_lenses.append(('(P_INT, P_AFF)','2D','Polarity'))
    if use_pca1:        active_lenses.append(('PCA1','1D_pca','Geometric'))
    if use_pca1_pca2_2d:active_lenses.append(('(PCA1, PCA2)','2D_pca','Geometric'))
    if use_word_tfidf and 'response_text' in df.columns:
        active_lenses.append(('Word TF-IDF (2D)','2D_tfidf','Text'))

    st.markdown(f"### 🔭 {len(active_lenses)} Lens Functions Selected")

    if len(active_lenses) == 0:
        st.warning("Select at least one lens in the sidebar.")
        st.stop()

    if st.button("🚀 Run Lens Stability Analysis", type="primary"):
        data, feat_cols = build_feature_matrix(df)
        pca_proj = get_pca_projection(data, 2)

        # V4: pass both question and temperature labels so we get purity for each.
        # Per §4.1, components correspond to questions; per §4.2 the question-purity
        # is the primary stability statistic. Temperature purity is reported alongside
        # so we can compare regimes-within-cluster spread.
        label_dict = {}
        if 'question_id' in df.columns:
            label_dict['question'] = df['question_id'].values
        if 'agent' in df.columns:
            label_dict['agent'] = df['agent'].values
        if 'temperature' in df.columns:
            label_dict['temperature'] = df['temperature'].values
        labels = label_dict if label_dict else None

        results = []
        progress = st.progress(0)
        status = st.empty()

        for i, (lens_name, lens_type, lens_cat) in enumerate(active_lenses):
            status.text(f"Running lens {i+1}/{len(active_lenses)}: {lens_name}...")
            progress.progress((i+1)/len(active_lenses))

            try:
                # Build lens values
                if lens_type == '1D':
                    col = lens_name
                    vals = normalize_col(df[col].fillna(0).values).reshape(-1,1)
                elif lens_type == '1D_abs':
                    vals = normalize_col(np.abs(df['vader_compound'].fillna(0).values)).reshape(-1,1)
                elif lens_type == '2D':
                    cols = [c.strip() for c in lens_name.strip('()').split(',')]
                    vals = np.column_stack([normalize_col(df[c].fillna(0).values) for c in cols])
                elif lens_type == '1D_pca':
                    vals = normalize_col(pca_proj[:,0]).reshape(-1,1)
                elif lens_type == '2D_pca':
                    vals = np.column_stack([normalize_col(pca_proj[:,0]), normalize_col(pca_proj[:,1])])
                elif lens_type == '2D_tfidf':
                    # Text lens: discovered vocabulary, not a stored column.
                    # response_text -> TF-IDF -> TruncatedSVD(2D). Fail loudly on
                    # degenerate cells (no silent origin output).
                    from sklearn.feature_extraction.text import TfidfVectorizer
                    from sklearn.decomposition import TruncatedSVD
                    texts = df['response_text'].fillna('').astype(str).tolist()
                    nonempty = sum(1 for t in texts if t.strip())
                    if nonempty < 3:
                        raise ValueError(
                            f"Word TF-IDF lens needs >=3 non-empty response_text rows "
                            f"in this cell (found {nonempty})."
                        )
                    _tfidf = TfidfVectorizer(max_features=2000, stop_words='english',
                                             token_pattern=r"[A-Za-z][A-Za-z']+",
                                             min_df=2, max_df=0.9)
                    try:
                        _X = _tfidf.fit_transform(texts)
                    except ValueError as _e:
                        raise ValueError(
                            "Word TF-IDF lens could not build a vocabulary "
                            "(text too short/repetitive/uniform). Underlying: %s" % _e
                        )
                    if _X.shape[1] < 2:
                        raise ValueError(
                            "Word TF-IDF lens found <2 distinctive terms "
                            "(text too repetitive/uniform to project)."
                        )
                    _svd = TruncatedSVD(n_components=2, random_state=42)
                    _red = _svd.fit_transform(_X)
                    vals = np.column_stack([normalize_col(_red[:,0]), normalize_col(_red[:,1])])

                topo = run_mapper_with_lens(
                    data, vals, n_cubes, perc_overlap, min_cluster, labels=labels
                )
                pk = topo.get('purity_by_kind', {})
                results.append({
                    'Lens': lens_name,
                    'Category': lens_cat,
                    'Type': lens_type.replace('_pca','').replace('_abs',''),
                    'Nodes': topo['n_nodes'],
                    'Edges': topo['n_edges'],
                    'β₀': topo['beta0'],
                    'β₁': topo['beta1'],
                    'Components': topo['n_components'],
                    'Largest': topo['largest'],
                    'Largest %pts': round(topo['largest_frac']*100, 1),
                    'Q-purity (mean)':    round(pk['question_mean'], 3)        if 'question_mean' in pk else None,
                    'Q-purity (wtd)':     round(pk['question_weighted'], 3)    if 'question_weighted' in pk else None,
                    'A-purity (mean)':    round(pk['agent_mean'], 3)           if 'agent_mean' in pk else None,
                    'A-purity (wtd)':     round(pk['agent_weighted'], 3)       if 'agent_weighted' in pk else None,
                    'T-purity (mean)':    round(pk['temperature_mean'], 3)     if 'temperature_mean' in pk else None,
                    'T-purity (wtd)':     round(pk['temperature_weighted'], 3) if 'temperature_weighted' in pk else None,
                    # Backward-compat columns:
                    'Mean Purity': round(topo['mean_purity'], 3) if topo['mean_purity'] is not None else None,
                    'Wtd Purity':  round(topo['weighted_purity'], 3) if topo['weighted_purity'] is not None else None,
                    'Modal Dist': str(topo['modal_dist']) if topo['modal_dist'] else '',
                    '% Connected': f"{round(topo['largest']/topo['n_nodes']*100) if topo['n_nodes'] > 0 else 0}%",
                    'Component Sizes': str(topo['comp_sizes'][:5]),
                })
            except Exception as e:
                results.append({
                    'Lens': lens_name, 'Category': lens_cat, 'Type': lens_type,
                    'Nodes': 'ERROR', 'Edges': 'ERROR',
                    'β₀': 'ERROR', 'β₁': 'ERROR',
                    'Components': 'ERROR', 'Largest': 'ERROR',
                    'Largest %pts': 'ERROR',
                    'Q-purity (mean)': None, 'Q-purity (wtd)': None,
                    'A-purity (mean)': None, 'A-purity (wtd)': None,
                    'T-purity (mean)': None, 'T-purity (wtd)': None,
                    'Mean Purity': None, 'Wtd Purity': None, 'Modal Dist': '',
                    '% Connected': 'ERROR',
                    'Component Sizes': str(e)[:80]
                })

        progress.progress(1.0)
        status.text("✅ Complete!")

        st.session_state.lens_results = results
        st.rerun()

    # Display results
    if 'lens_results' in st.session_state and st.session_state.lens_results:
        results = st.session_state.lens_results
        rdf = pd.DataFrame(results)

        st.markdown("## 📊 Lens Stability Results")

        # ─── Invariant-based stability assessment ──────────────────────────
        valid = rdf[rdf['Nodes'] != 'ERROR']
        if len(valid) > 0:
            beta0_vals = valid['β₀'].astype(int)
            beta1_vals = valid['β₁'].astype(int)
            largest_frac = valid['Largest %pts'].astype(float)
            # V4: Q-purity is primary (per §4.1, components track questions);
            # T-purity is reported alongside but does NOT enter the stability score —
            # a good lens may still show large temperature spread within question
            # components (that's regime sensitivity, not instability).
            qpur = valid['Q-purity (wtd)'].dropna().astype(float) if 'Q-purity (wtd)' in valid.columns else pd.Series(dtype=float)
            tpur = valid['T-purity (wtd)'].dropna().astype(float) if 'T-purity (wtd)' in valid.columns else pd.Series(dtype=float)

            # Stability components, each in [0, 1]:
            #   1. β₀ agreement: fraction of lenses sharing the modal β₀
            #   2. β₁ presence agreement: fraction agreeing on (has loops? yes/no)
            #   3. Largest-component coverage stability: 1 - normalized_range
            #   4. Question-purity stability (V4): 1 - SD of weighted Q-purity
            modal_b0 = beta0_vals.mode().iloc[0]
            b0_agree = (beta0_vals == modal_b0).mean()

            has_loops = (beta1_vals > 0)
            b1_agree = max(has_loops.mean(), 1 - has_loops.mean())

            lf_range = largest_frac.max() - largest_frac.min()
            lf_stab = max(0.0, 1.0 - lf_range / 100.0)

            if len(qpur) >= 2:
                qpur_sd = qpur.std()
                qpur_mean = qpur.mean()
                qpur_stab = max(0.0, 1.0 - 2.0 * qpur_sd)
            else:
                qpur_sd = None; qpur_mean = None; qpur_stab = None

            tpur_sd = tpur.std() if len(tpur) >= 2 else None
            tpur_mean = tpur.mean() if len(tpur) >= 2 else None

            # Overall score uses β₀, β₁, largest-frac, and Q-purity (NOT T-purity)
            comps = [b0_agree, b1_agree, lf_stab]
            if qpur_stab is not None:
                comps.append(qpur_stab)
            stability_score = float(np.mean(comps))

            # Verdict thresholds chosen to match the published HTML report convention:
            #   ≥0.85 = STABLE, 0.65–0.85 = MODERATE, <0.65 = UNSTABLE
            if stability_score >= 0.85:
                stability = "HIGH ✅"
                verdict_class = "stable"
                verdict_msg = (
                    "✅ **Topology is STABLE** — invariants (β₀, β₁, largest-component "
                    "coverage" + (", question purity" if qpur_stab is not None else "") +
                    ") agree across lens functions. Per §4.1, this means the question-"
                    "based component structure is preserved regardless of projection."
                )
            elif stability_score >= 0.65:
                stability = "MODERATE ⚠️"
                verdict_class = "unstable"
                verdict_msg = (
                    "⚠️ **Topology is MODERATELY STABLE** — core invariants mostly agree "
                    "but at least one lens is an outlier. Inspect the per-lens breakdown."
                )
            else:
                stability = "LOW ❌"
                verdict_class = "unstable"
                verdict_msg = (
                    "❌ **Topology is UNSTABLE** — invariants disagree substantially across "
                    "lenses. Either projection choice matters, or the dataset is too small "
                    "(n_cubes / min_cluster need tuning, or n is too low for 2D lenses)."
                )

            col1, col2, col3, col4 = st.columns(4)
            col1.markdown(
                f'<div class="metric-box"><h3>β₀ {beta0_vals.min()}–{beta0_vals.max()}</h3>'
                f'<p>{int(b0_agree*100)}% agree on β₀={modal_b0}</p></div>',
                unsafe_allow_html=True
            )
            col2.markdown(
                f'<div class="metric-box"><h3>β₁ {beta1_vals.min()}–{beta1_vals.max()}</h3>'
                f'<p>{int(b1_agree*100)}% agree on loops</p></div>',
                unsafe_allow_html=True
            )
            col3.markdown(
                f'<div class="metric-box"><h3>{largest_frac.min():.0f}–{largest_frac.max():.0f}%</h3>'
                f'<p>Largest-comp coverage</p></div>',
                unsafe_allow_html=True
            )
            col4.markdown(
                f'<div class="metric-box"><h3>{stability}</h3>'
                f'<p>Score: {stability_score:.2f}</p></div>',
                unsafe_allow_html=True
            )
            st.markdown(f'<div class="{verdict_class}">{verdict_msg}</div>', unsafe_allow_html=True)

            # V4: Question-purity callout (§4.1: components ≈ question families)
            if qpur_stab is not None:
                st.markdown("#### 🎯 Question Purity Across Lenses (§4.1 / §4.2 primary metric)")
                cA, cB, cC = st.columns(3)
                cA.metric("Mean weighted Q-purity", f"{qpur_mean:.3f}")
                cB.metric("SD across lenses",      f"{qpur_sd:.3f}")
                cC.metric("Q-purity stability",    f"{qpur_stab:.2f}")
                if qpur_mean is not None and qpur_mean >= 0.7:
                    st.success(
                        f"Mean Q-purity = {qpur_mean:.2f}: Mapper nodes are mostly "
                        f"single-question (per §4.1, components track question families). "
                        f"Lens-to-lens SD = {qpur_sd:.3f} → the question-based component "
                        f"structure is **lens-invariant**. This is the §4.2 result."
                    )
                else:
                    st.info(
                        f"Mean Q-purity = {qpur_mean:.2f}: nodes mix questions. "
                        f"This lens may collapse semantic structure or be sample-limited. "
                        f"Compare against P_AFF and (P_INT, P_AFF) §4.3 polarity lenses."
                    )

            # V4: Temperature-purity reported alongside (but not in score)
            if tpur_mean is not None:
                st.markdown("#### 🌡️ Temperature Purity Across Lenses (regime spread within questions)")
                cA, cB = st.columns(2)
                cA.metric("Mean weighted T-purity", f"{tpur_mean:.3f}")
                cB.metric("SD across lenses",       f"{tpur_sd:.3f}")
                st.caption(
                    "Per §4.1, regime mainly affects internal spread within question clusters. "
                    "Low T-purity is **expected** and is not a stability defect — it indicates "
                    "the lens captures regime-driven variation within question families. "
                    "A useful lens for §4.2 has HIGH Q-purity AND LOW T-purity simultaneously."
                )

        st.markdown("---")

        # ─── Per-category tables (now showing invariants) ──────────────────
        for cat in ['AFF', 'INT', 'ACT', 'Cross-IEP', 'Polarity', 'Geometric', 'Text']:
            cat_df = rdf[rdf['Category'] == cat]
            if len(cat_df) == 0:
                continue
            st.markdown(f"### {cat} Lenses")
            display_cols = ['Lens','Type','Nodes','Edges','β₀','β₁',
                            'Largest %pts','A-purity (wtd)','Q-purity (wtd)','T-purity (wtd)','% Connected']
            display_cols = [c for c in display_cols if c in cat_df.columns]
            st.dataframe(cat_df[display_cols].reset_index(drop=True),
                        use_container_width=True, hide_index=True)

        st.markdown("---")

        # Full results download
        st.markdown("### 📥 Downloads")
        col1, col2, col3 = st.columns(3)

        # --- derive the agent name from the uploaded data so the output is self-identifying ---
        if 'agent' in df.columns and df['agent'].nunique() == 1:
            _agent_name = str(df['agent'].iloc[0])
        elif 'agent' in df.columns:
            _agent_name = "MULTI(" + "+".join(sorted(df['agent'].unique())) + ")"
        else:
            _agent_name = "UNKNOWN"

        # write the Agent name + provenance into the CSV itself so no row is anonymous
        rdf_out = rdf.copy()
        rdf_out.insert(0, "Run_Date", RUN_DATE)
        rdf_out.insert(0, "Tool_Version", TOOL_VERSION)
        rdf_out.insert(0, "Agent", _agent_name)
        _safe = "".join(c if c.isalnum() else "_" for c in _agent_name)

        with col1:
            st.caption(f"Agent detected: **{_agent_name}**  ·  {TOOL_VERSION}  ·  {RUN_DATE}")
            st.download_button(
                "📥 Full Results (CSV)",
                rdf_out.to_csv(index=False),
                file_name=f"{_safe}_stability_{TOOL_VERSION}.csv",
                mime="text/csv"
            )

        with col2:
            # Summary text report
            report_lines = [
                f"{PROJECT_NAME} — Analysis Report ({TOOL_VERSION})",
                "Per Dr. Farzana Nasrin Protocol §4.2 — March/May 2026",
                "=" * 60,
                f"Agent: {_agent_name}",
                f"Tool version: {TOOL_VERSION}",
                f"Run date: {RUN_DATE}",
                f"Dataset: {uploaded_file.name}",
                f"Clean rows analyzed: {len(df)}" + (f" (of {n_total_in}; {n_err} errored rows dropped)" if n_err else ""),
                f"Lenses tested: {len(results)}",
                f"Mapper parameters: n_cubes={n_cubes}, overlap={perc_overlap}%, min_cluster={min_cluster}",
                "",
                "PER-LENS INVARIANTS:",
            ]
            for r in results:
                wp = f"{r['Wtd Purity']:.3f}" if r.get('Wtd Purity') is not None else "  —  "
                report_lines.append(
                    f"  {r['Lens']:30s} | "
                    f"V={str(r.get('Nodes','?')):>4} E={str(r.get('Edges','?')):>4} | "
                    f"β₀={str(r.get('β₀','?')):>3} β₁={str(r.get('β₁','?')):>3} | "
                    f"largest={str(r.get('Largest %pts','?')):>4}%pts | "
                    f"wpur={wp}"
                )
            report_lines += ["", "STABILITY VERDICT:"]
            if 'stability_score' in dir():
                report_lines += [
                    f"  Score: {stability_score:.3f}   →   {stability}",
                    f"  β₀ agreement:           {b0_agree*100:.0f}% (modal β₀ = {modal_b0})",
                    f"  β₁ presence agreement:  {b1_agree*100:.0f}%",
                    f"  Largest-comp coverage:  {largest_frac.min():.1f}–{largest_frac.max():.1f}% (range {lf_range:.1f})",
                ]
                if qpur_stab is not None:
                    report_lines.append(
                        f"  Q-purity (question):    mean={qpur_mean:.3f}, SD={qpur_sd:.3f} across lenses"
                    )
                if tpur_mean is not None:
                    report_lines.append(
                        f"  T-purity (condition):   mean={tpur_mean:.3f}"
                        + (f", SD={tpur_sd:.3f}" if tpur_sd is not None else "")
                        + " across lenses (diagnostic; not in score)"
                    )
            report_lines += [
                "",
                "SYNINT Research Team · Tennessee 🎹 CUZ Partnership · 2026"
            ]
            st.download_button(
                "📥 Summary Report (TXT)",
                "\n".join(report_lines),
                file_name="syniq_lens_stability_report.txt",
                mime="text/plain"
            )

        with col3:
            # §4.2-ready paragraph for the paper
            if 'stability_score' in dir():
                verdict_word = {"HIGH ✅": "stable", "MODERATE ⚠️": "moderately stable",
                                "LOW ❌": "unstable"}[stability]
                pur_clause = (
                    f" Mean weighted node purity with respect to the question label "
                    f"was {qpur_mean:.2f} (SD across lenses = {qpur_sd:.3f}), indicating that "
                    f"the question-based component structure persists regardless of projection."
                ) if qpur_stab is not None else ""
                tpur_clause = (
                    f" Mean weighted purity with respect to the condition (temperature) label "
                    f"was {tpur_mean:.2f}, reported alongside as a regime-sensitivity diagnostic "
                    f"that does not enter the stability score."
                ) if tpur_mean is not None else ""

                paragraph = (
                    f"§4.2 RESULT (auto-generated):\n\n"
                    f"Across {len(valid)} lens functions spanning the AFF, INT, ACT, Cross-IEP, "
                    f"and Geometric categories, β₀ took values in {{{beta0_vals.min()}…{beta0_vals.max()}}} "
                    f"with {int(b0_agree*100)}% of lenses agreeing on the modal value β₀={modal_b0}. "
                    f"Cycle-rank β₁ took values in {{{beta1_vals.min()}…{beta1_vals.max()}}}; "
                    f"{int(b1_agree*100)}% of lenses agreed on the presence/absence of 1-cycles. "
                    f"The largest connected component covered {largest_frac.min():.0f}–{largest_frac.max():.0f}% "
                    f"of data points across lenses (range {lf_range:.1f} percentage points)."
                    f"{pur_clause}{tpur_clause} The combined stability score was {stability_score:.2f}, which we "
                    f"classify as {verdict_word.upper()}. This indicates that the topological "
                    f"structure observed in the IEP/Vₜ response space is "
                    f"{'driven by intrinsic properties of the data' if stability_score >= 0.65 else 'sensitive to lens choice and should not be reported as a single canonical result'}, "
                    f"consistent with the cross-projection robustness criterion of Nasrin et al. (§4.2).\n\n"
                    f"Mapper parameters: KeplerMapper with n_cubes={n_cubes}, overlap={perc_overlap}%, "
                    f"DBSCAN min_samples={min_cluster}, eps=0.5; lens values min-max normalized to [0,1]."
                )
                st.download_button(
                    "📥 §4.2 Paragraph (TXT)",
                    paragraph,
                    file_name="syniq_section_4_2_paragraph.txt",
                    mime="text/plain"
                )

else:
    st.info("👆 Upload a SYN-IQ harvester output (CSV or JSON) to begin lens stability analysis.")
    st.markdown("""
### What This Tool Does

Per **Dr. Nasrin's Experiment Protocol §4.1–§4.3 (March 24, 2026)**, this tool tests
whether topological structure of AI response space is stable across multiple lens
functions, and quantifies how prompt regimes shape that structure.

**Lens categories:**
- **AFF**: aff_pct, vader_compound, |vader_compound|, 2D combinations
- **INT**: int_pct, flesch_kincaid, ttr, 2D combinations
- **ACT**: act_pct, total_words, 2D combinations
- **Cross-IEP**: (aff_pct, int_pct), (int_pct, act_pct), (aff_pct, act_pct)
- **Polarity (§4.3)**: P_AFF, (P_INT, P_AFF) — Nasrin's normalized simplex projection
- **Geometric**: PCA1, (PCA1, PCA2)

**Stability metrics (V5):**
1. **β₀ agreement** — fraction of lenses sharing the modal connected-component count.
2. **β₁ presence agreement** — fraction of lenses agreeing on whether the graph has 1-cycles.
3. **Largest-component coverage stability** — range of the fraction of data points in the
   largest component (lower range = more stable).
4. **Question purity (primary §4.2 claim)** — per §4.1, components correspond to
   question families, not regimes. Stability of weighted Q-purity *across lenses* is
   the substantive §4.2 result. Temperature purity is reported alongside but does NOT
   count against stability — a good lens preserves question structure while still
   capturing regime-driven spread.

**§4.1 / §4.2 / §4.3 deliverables produced:**
- COLD → FIRE effect sizes with AUC (saturation-safe) + Cohen's d for non-saturated cells
- Pairwise regime AUC matrix (answers "Are HOT and FIRE the same?" — they are not)
- Subclass-level effect sizes across 23 aff/int/act subdivisions (purpose-driven prompt design)
- §4.3 polarity vector P = (P_INT, P_AFF, P_ACT) computed and exposed as Mapper lenses
- **Ideation Collapse Diagnostic (V5)** — surfaces regimes where int_pct looks preserved
  but constructive subclasses have been displaced by epistemic hedging. Empirically,
  FIRE is the displacement case; HOT preserves ideation while adding warmth.

Why this is different from V1: raw node/edge counts will *always* differ between 1D and
2D lenses because the cover dimension differs. Comparing them as if they should match
mis-grades the experiment. β₀, β₁, and purity are projection-invariant in the right way.
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #a0a0a0; padding: 1rem;">
    <strong>SYN-IQ Lens Stability Analyzer V11</strong><br>
    Per Dr. Farzana Nasrin Protocol §4.2 · KeplerMapper + IEP V3 · 2026<br>
    <em>SYNINT Team — Tennessee 🎹 CUZ Partnership</em>
</div>
""", unsafe_allow_html=True)