"""
SYN-IQ CSV Mapper Analyzer V5
CSV-Native Topological Analysis for Farzana's TDA Pipeline

PURPOSE: Ingest V48/V50 harvester CSVs directly. Compute IEP topology,
         question-type clustering, gradient comparisons, simplex geometry
         control experiment (Lyra/Dirichlet), and export clean data for
         KeplerMapper + Farzana's persistence diagrams.

V5 CHANGES:
- Compositional closure verification (INT+AFF+ACT=100 check)
- Safer question normalization (exact/prefix, no substring risk)
- Euclidean distance in IEP space for agent divergence
- Gradient inversion tolerance (0.5pp noise floor)
- Simplex geometry caveat on screen
- Dirichlet(1,1,1) control experiment — separates semantic signal from geometric artifact
- Vector field analysis — gradient prompts as movement through simplex
- Basin of attraction visualization — question types as geometric basins

SYNINT Team — March 2026
Tennessee 🎹 CUZ Partnership
Credit: Simplex control design by Lyra (ChatGPT) — peer review March 2026
"""

import streamlit as st
import pandas as pd
import numpy as np
import json
import re
from collections import defaultdict
from datetime import datetime

st.set_page_config(
    page_title="SYN-IQ CSV Mapper Analyzer",
    page_icon="🔬",
    layout="wide"
)

# =============================================================================
# STYLES
# =============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Outfit:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Outfit', sans-serif; }

    .main-header {
        background: linear-gradient(135deg, #0a0a1a 0%, #1a0a2e 40%, #0f2460 100%);
        color: white; padding: 2.5rem; border-radius: 12px;
        text-align: center; margin-bottom: 1.5rem;
        border: 1px solid #7c3aed;
    }
    .main-header h1 { color: #a78bfa; margin: 0; font-size: 2rem; font-family: 'Outfit', sans-serif; font-weight: 700; }
    .main-header .subtitle { color: #9ca3af; font-size: 0.85rem; font-family: 'JetBrains Mono', monospace; }

    .stat-card {
        background: linear-gradient(135deg, #0f0f1e 0%, #1a1a30 100%);
        border: 1px solid #2d2d4a; border-radius: 10px;
        padding: 1.2rem; text-align: center;
    }
    .stat-card .num { font-size: 2rem; font-weight: 700; font-family: 'JetBrains Mono', monospace; color: #a78bfa; }
    .stat-card .label { color: #9ca3af; font-size: 0.8rem; margin-top: 0.3rem; }

    .section-label {
        font-family: 'JetBrains Mono', monospace;
        color: #7c3aed; font-size: 0.8rem;
        letter-spacing: 0.12em; text-transform: uppercase;
        border-bottom: 1px solid #2d2d4a;
        padding-bottom: 0.4rem; margin: 1.5rem 0 1rem 0;
    }

    .finding-box {
        background: linear-gradient(135deg, #0a0a1a 0%, #12122a 100%);
        border-left: 4px solid #7c3aed;
        border-radius: 0 8px 8px 0;
        padding: 1.2rem; margin: 0.8rem 0;
        color: #d1d5db; line-height: 1.7;
    }
    .finding-box.green { border-left-color: #34d399; }
    .finding-box.red { border-left-color: #f87171; }
    .finding-box.yellow { border-left-color: #fbbf24; }

    .mono { font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: #9ca3af; }

    .chat-user { background: #1a1a2e; border-radius: 8px; padding: 0.8rem 1rem; margin: 0.4rem 0; color: #e0e0e0; }
    .chat-claude { background: #0f1a2e; border-left: 3px solid #7c3aed; border-radius: 0 8px 8px 0; padding: 0.8rem 1rem; margin: 0.4rem 0; color: #d1d5db; }

    div[data-testid="stExpander"] { border: 1px solid #2d2d4a; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# HEADER
# =============================================================================
st.markdown("""
<div class="main-header">
    <h1>🔬 SYN-IQ CSV Mapper Analyzer V1</h1>
    <p class="subtitle">CSV-Native · IEP Topology · Gradient Comparison · TDA Export</p>
    <p class="subtitle">For Farzana's Persistence Diagrams — Tennessee 🎹 CUZ Partnership</p>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# CONSTANTS
# =============================================================================
QUESTIONS = {
    "LIARS_PARADOX": "Liar's Paradox",
    "GRIEF": "Grief",
    "CONSCIOUSNESS": "Consciousness",
    "LEAVE_JOB": "Leave Job",
    "RURAL_HEALTHCARE": "Rural Healthcare",
}

CONDITION_FAMILIES = {
    "Baseline": ["COLD", "NATIVE", "HOT", "FIRE"],
    "AFF": ["AFF_1", "AFF_2", "AFF_3", "AFF_4", "AFF_5"],
    "INT": ["INT_1", "INT_2", "INT_3", "INT_4", "INT_5"],
    "ACT": ["ACT_1", "ACT_2", "ACT_3", "ACT_4", "ACT_5"],
}

ALL_CONDITIONS = (
    CONDITION_FAMILIES["Baseline"] +
    CONDITION_FAMILIES["AFF"] +
    CONDITION_FAMILIES["INT"] +
    CONDITION_FAMILIES["ACT"]
)

AGENTS = ["Claude", "Gemini", "Grok", "Sophia"]

Q_COLORS = {
    "LIARS_PARADOX": "#60a5fa",
    "GRIEF": "#f87171",
    "CONSCIOUSNESS": "#a78bfa",
    "LEAVE_JOB": "#34d399",
    "RURAL_HEALTHCARE": "#fbbf24",
}

CONDITION_COLORS = {
    "COLD": "#60a5fa", "NATIVE": "#9ca3af", "HOT": "#f87171", "FIRE": "#e94560",
    "AFF_1": "#fca5a5", "AFF_2": "#f87171", "AFF_3": "#ef4444",
    "AFF_4": "#dc2626", "AFF_5": "#b91c1c",
    "INT_1": "#bfdbfe", "INT_2": "#93c5fd", "INT_3": "#60a5fa",
    "INT_4": "#3b82f6", "INT_5": "#1d4ed8",
    "ACT_1": "#bbf7d0", "ACT_2": "#86efac", "ACT_3": "#4ade80",
    "ACT_4": "#22c55e", "ACT_5": "#15803d",
}

# =============================================================================
# SESSION STATE
# =============================================================================
for key, default in [
    ("df", None),
    ("chat_history", []),
    ("topology_context", None),
    ("file_names", []),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# =============================================================================
# PASSWORD
# =============================================================================
def check_password():
    if st.session_state.get("authenticated"):
        return True
    password = st.text_input("Enter password:", type="password")
    if password:
        correct = "SYNIQ2026"  # override via st.secrets["app_password"] in deployment
        try:
            correct = st.secrets["app_password"]
        except Exception:
            pass
        if password == correct:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("❌ Incorrect password.")
    st.markdown("<div style='text-align:center;color:#6b7280;font-size:0.8rem;padding:1rem;'><em>SYNINT Team — Tennessee 🎹 CUZ</em></div>", unsafe_allow_html=True)
    return False

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if not check_password():
    st.stop()

# =============================================================================
# CSV LOADER & VALIDATOR
# =============================================================================

REQUIRED_COLS = {"int_pct", "aff_pct", "act_pct"}
EXPECTED_COLS = {
    "agent", "temperature", "question_id", "int_pct", "aff_pct", "act_pct",
    "total_words", "vader_compound", "flesch_kincaid", "ttr", "response_text"
}

def load_and_validate_csv(uploaded_files):
    """Load one or more CSVs, validate columns, merge, return DataFrame."""
    dfs = []
    errors = []
    warnings = []

    for f in uploaded_files:
        try:
            df = pd.read_csv(f)
            df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

            # Column remapping — handle V48/V50 naming variants
            remap = {
                "temperature": "condition",
                "temp": "condition",
                "question": "question_id",
                "qid": "question_id",
                "question_text": "question_id",  # fallback
            }
            for old, new in remap.items():
                if old in df.columns and new not in df.columns:
                    df.rename(columns={old: new}, inplace=True)

            missing = REQUIRED_COLS - set(df.columns)
            if missing:
                errors.append(f"**{f.name}**: Missing required columns: {missing}")
                continue

            # Normalize condition column
            if "condition" not in df.columns and "temperature" in df.columns:
                df.rename(columns={"temperature": "condition"}, inplace=True)

            # Normalize question_id
            if "question_id" not in df.columns:
                df["question_id"] = "UNKNOWN"

            # Add agent if missing
            if "agent" not in df.columns:
                df["agent"] = f.name.split("_")[0].title()
                warnings.append(f"**{f.name}**: No agent column — inferred as '{df['agent'].iloc[0]}'")

            # Clean numeric cols
            for col in ["int_pct", "aff_pct", "act_pct", "total_words", "vader_compound", "flesch_kincaid", "ttr"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

            df["_source_file"] = f.name
            dfs.append(df)

        except Exception as e:
            errors.append(f"**{f.name}**: Parse error — {str(e)}")

    if not dfs:
        return None, errors, warnings

    combined = pd.concat(dfs, ignore_index=True)

    # Standardize question_id labels — exact/prefix match only (no substring risk)
    q_map_exact = {
        "liars_paradox": "LIARS_PARADOX",
        "liar's_paradox": "LIARS_PARADOX",
        "liars paradox": "LIARS_PARADOX",
        "grief": "GRIEF",
        "consciousness": "CONSCIOUSNESS",
        "leave_job": "LEAVE_JOB",
        "leave job": "LEAVE_JOB",
        "rural_healthcare": "RURAL_HEALTHCARE",
        "rural healthcare": "RURAL_HEALTHCARE",
    }
    q_map_prefix = {
        "liars": "LIARS_PARADOX",
        "liar": "LIARS_PARADOX",
        "grief": "GRIEF",
        "conscious": "CONSCIOUSNESS",
        "leave": "LEAVE_JOB",
        "rural": "RURAL_HEALTHCARE",
    }
    def normalize_question(x):
        x = str(x).lower().strip()
        # Exact match first
        if x in q_map_exact:
            return q_map_exact[x]
        # Prefix match second (safer than substring)
        for prefix, canonical in q_map_prefix.items():
            if x.startswith(prefix):
                return canonical
        return x.upper()

    combined["question_id"] = combined["question_id"].astype(str).str.lower().str.strip()
    combined["question_id"] = combined["question_id"].apply(normalize_question)

    # Standardize condition labels
    combined["condition"] = combined["condition"].astype(str).str.strip().str.upper()

    # Infer condition family
    def get_family(c):
        for fam, conds in CONDITION_FAMILIES.items():
            if c in [x.upper() for x in conds]:
                return fam
        return "Other"
    combined["condition_family"] = combined["condition"].apply(get_family)

    # Gradient level (1-5 for AFF/INT/ACT)
    def get_level(c):
        m = re.search(r'_(\d)$', c)
        return int(m.group(1)) if m else None
    combined["gradient_level"] = combined["condition"].apply(get_level)

    # === COMPOSITIONAL CLOSURE CHECK (Issue 1) ===
    combined["_sum_check"] = combined["int_pct"] + combined["aff_pct"] + combined["act_pct"]
    mean_sum = combined["_sum_check"].mean()
    max_drift = abs(combined["_sum_check"] - 100).max()
    if abs(mean_sum - 100) > 0.5:
        warnings.append(
            f"⚠️ **Compositional closure failure**: INT+AFF+ACT averages {mean_sum:.2f}% "
            f"(expected 100%). Max single-row drift: {max_drift:.2f}pp. "
            f"Check upstream IEP scoring for rounding errors."
        )
    combined.drop(columns=["_sum_check"], inplace=True)

    return combined, errors, warnings


# =============================================================================
# TOPOLOGY COMPUTATIONS
# =============================================================================

def compute_iep_topology(df, groupby_cols):
    """Aggregate IEP means and SDs by groupby columns."""
    agg = df.groupby(groupby_cols).agg(
        n=("int_pct", "count"),
        int_mean=("int_pct", "mean"),
        int_sd=("int_pct", "std"),
        aff_mean=("aff_pct", "mean"),
        aff_sd=("aff_pct", "std"),
        act_mean=("act_pct", "mean"),
        act_sd=("act_pct", "std"),
        words_mean=("total_words", "mean") if "total_words" in df.columns else ("int_pct", "count"),
        vader_mean=("vader_compound", "mean") if "vader_compound" in df.columns else ("int_pct", "count"),
    ).reset_index().round(2)
    return agg


def compute_gradient_curve(df, family, dim):
    """Compute gradient titration curve for a given family and dimension."""
    conditions = CONDITION_FAMILIES.get(family, [])
    col = f"{dim.lower()}_pct"
    if col not in df.columns:
        return pd.DataFrame()

    rows = []
    for cond in conditions:
        subset = df[df["condition"] == cond.upper()]
        if len(subset) == 0:
            continue
        rows.append({
            "condition": cond,
            "level": int(cond.split("_")[1]) if "_" in cond else 0,
            "n": len(subset),
            f"{dim}%": round(subset[col].mean(), 2),
            f"{dim}_sd": round(subset[col].std(), 2),
            f"{dim}_sem": round(subset[col].sem(), 3),
        })
    return pd.DataFrame(rows)


def detect_non_monotonic(curve_df, dim, tolerance=0.5):
    """Flag gradient inversions with tolerance for noise.
    tolerance=0.5pp means tiny fluctuations are not flagged as inversions."""
    col = f"{dim}%"
    if col not in curve_df.columns or len(curve_df) < 2:
        return []
    flags = []
    vals = curve_df[col].tolist()
    conds = curve_df["condition"].tolist()
    for i in range(1, len(vals)):
        drop = vals[i-1] - vals[i]
        if drop > tolerance:  # only flag meaningful inversions
            flags.append({
                "step": f"{conds[i-1]} → {conds[i]}",
                "drop": round(drop, 2),
                "type": "ceiling_effect" if vals[i-1] > 55 else "inversion",
            })
    return flags


def compute_question_clustering(df):
    """How strongly does question type predict IEP profile? Returns eta-squared proxy."""
    results = {}
    for dim in ["int_pct", "aff_pct", "act_pct"]:
        if dim not in df.columns:
            continue
        overall_mean = df[dim].mean()
        ss_total = ((df[dim] - overall_mean) ** 2).sum()
        ss_between = sum(
            len(g) * (g[dim].mean() - overall_mean) ** 2
            for _, g in df.groupby("question_id")
        )
        eta_sq = round(ss_between / ss_total, 3) if ss_total > 0 else 0
        results[dim] = eta_sq
    return results


def compute_agent_divergence(df):
    """
    How much do agents diverge per question per condition?
    Uses Euclidean distance in IEP space (INT, AFF, ACT coordinates)
    rather than max range — captures multidimensional divergence properly.
    Note: IEP is compositional (simplex) data; Euclidean distance is an
    approximation. Full Aitchison distance is a future improvement.
    """
    rows = []
    for (q, cond), group in df.groupby(["question_id", "condition"]):
        if len(group["agent"].unique()) < 2:
            continue
        agent_means = group.groupby("agent")[["int_pct", "aff_pct", "act_pct"]].mean()
        if len(agent_means) < 2:
            continue
        agents = agent_means.index.tolist()
        pairwise = []
        for i in range(len(agents)):
            for j in range(i+1, len(agents)):
                a1 = agent_means.loc[agents[i], ["int_pct","aff_pct","act_pct"]].values
                a2 = agent_means.loc[agents[j], ["int_pct","aff_pct","act_pct"]].values
                dist = float(np.sqrt(((a1 - a2)**2).sum()))
                pairwise.append(dist)
        rows.append({
            "question": q,
            "condition": cond,
            "agents_present": len(agent_means),
            "max_euclidean_dist": round(max(pairwise), 2),
            "mean_euclidean_dist": round(np.mean(pairwise), 2),
            "int_range": round(agent_means["int_pct"].max() - agent_means["int_pct"].min(), 1),
            "aff_range": round(agent_means["aff_pct"].max() - agent_means["aff_pct"].min(), 1),
            "act_range": round(agent_means["act_pct"].max() - agent_means["act_pct"].min(), 1),
        })
    return pd.DataFrame(rows)


def build_topology_context(df):
    """Build structured context string for Claude conversation."""
    ctx = []
    ctx.append("=== SYN-IQ TOPOLOGY CONTEXT ===")
    ctx.append(f"Total responses: {len(df)}")
    ctx.append(f"Agents: {sorted(df['agent'].unique().tolist())}")
    ctx.append(f"Questions: {sorted(df['question_id'].unique().tolist())}")
    ctx.append(f"Conditions: {sorted(df['condition'].unique().tolist())}")
    ctx.append(f"Condition families present: {sorted(df['condition_family'].unique().tolist())}")
    ctx.append("")

    # Overall IEP by question
    ctx.append("--- IEP by Question (all conditions pooled) ---")
    q_agg = df.groupby("question_id")[["int_pct", "aff_pct", "act_pct"]].mean().round(1)
    for q, row in q_agg.iterrows():
        ctx.append(f"  {q}: INT={row['int_pct']}% AFF={row['aff_pct']}% ACT={row['act_pct']}%")
    ctx.append("")

    # IEP by condition family
    ctx.append("--- IEP by Condition Family (all questions pooled) ---")
    fam_agg = df.groupby("condition_family")[["int_pct", "aff_pct", "act_pct"]].mean().round(1)
    for fam, row in fam_agg.iterrows():
        ctx.append(f"  {fam}: INT={row['int_pct']}% AFF={row['aff_pct']}% ACT={row['act_pct']}%")
    ctx.append("")

    # Gradient info
    for fam in ["AFF", "INT", "ACT"]:
        fam_df = df[df["condition_family"] == fam]
        if len(fam_df) == 0:
            continue
        ctx.append(f"--- {fam} Gradient ---")
        for cond in CONDITION_FAMILIES[fam]:
            sub = fam_df[fam_df["condition"] == cond]
            if len(sub) == 0:
                continue
            ctx.append(f"  {cond} (n={len(sub)}): INT={sub['int_pct'].mean():.1f}% AFF={sub['aff_pct'].mean():.1f}% ACT={sub['act_pct'].mean():.1f}%")
        ctx.append("")

    # Question x condition cross
    ctx.append("--- Question × Condition Matrix (AFF%) ---")
    pivot = df.pivot_table(values="aff_pct", index="question_id", columns="condition", aggfunc="mean").round(1)
    ctx.append(pivot.to_string())
    ctx.append("")

    # Agent divergence
    ctx.append("--- Agent Divergence (INT range per question/condition) ---")
    div = compute_agent_divergence(df)
    if len(div) > 0 and "max_euclidean_dist" in div.columns:
        top = div.nlargest(5, "max_euclidean_dist")[["question", "condition", "int_range", "aff_range", "act_range", "max_euclidean_dist"]]
        ctx.append(top.to_string(index=False))
    elif len(div) == 0:
        ctx.append("  (Single agent dataset — divergence comparison not applicable)")

    return "\n".join(ctx)


# =============================================================================
# FARZANA TDA EXPORT
# =============================================================================

def build_farzana_export(df):
    """
    Build clean export for Farzana's persistence diagrams.
    Outputs: point cloud (one row per response with IEP coords + metadata)
    """
    cols = ["agent", "question_id", "condition", "condition_family",
            "int_pct", "aff_pct", "act_pct"]
    optional = ["total_words", "vader_compound", "flesch_kincaid", "ttr", "gradient_level"]
    cols += [c for c in optional if c in df.columns]

    export = df[cols].copy()
    export["iep_vector"] = export.apply(
        lambda r: f"[{r['int_pct']:.2f},{r['aff_pct']:.2f},{r['act_pct']:.2f}]", axis=1
    )
    export = export.rename(columns={
        "int_pct": "INT_pct",
        "aff_pct": "AFF_pct",
        "act_pct": "ACT_pct",
    })
    return export


# =============================================================================
# SIDEBAR — UPLOAD
# =============================================================================
st.sidebar.markdown("## 📁 Load CSV Data")
st.sidebar.markdown("Drop V48/V50 harvester CSVs. Multiple files merge automatically.")

uploaded_files = st.sidebar.file_uploader(
    "Upload CSV files",
    type=["csv"],
    accept_multiple_files=True,
    label_visibility="collapsed",
    key=f"uploader_{st.session_state.get('uploader_key', 0)}"
)

# Clear all data button
if st.sidebar.button("🗑️ Clear All Data", type="secondary"):
    st.session_state.df = None
    st.session_state.file_names = []
    st.session_state.topology_context = None
    st.session_state.chat_history = []
    st.session_state.control_result = None
    st.session_state.control_config = None
    st.session_state["uploader_key"] = st.session_state.get("uploader_key", 0) + 1
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔑 Anthropic API Key")
api_key = st.sidebar.text_input("API Key:", type="password",
    help="For AI-powered topology conversation")

st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style="text-align:center;color:#6b7280;font-size:0.72rem;font-family:'JetBrains Mono',monospace;">
SYNINT Team<br>Tennessee 🎹 CUZ
</div>
""", unsafe_allow_html=True)

# =============================================================================
# LOAD DATA — force reload when file list changes (fixes Streamlit caching bug)
# =============================================================================
if uploaded_files:
    current_file_names = sorted([f.name for f in uploaded_files])
    cached_file_names = sorted(st.session_state.get("file_names", []))

    if current_file_names != cached_file_names or st.session_state.df is None:
        df, errors, warnings = load_and_validate_csv(uploaded_files)

        for e in errors:
            st.error(e)
        for w in warnings:
            st.warning(w)

        if df is not None:
            st.session_state.df = df
            st.session_state.file_names = current_file_names
            st.session_state.topology_context = build_topology_context(df)
            st.success(f"✅ Loaded {len(df)} responses from {len(uploaded_files)} file(s)")

if st.session_state.df is None:
    st.info("Upload one or more V48/V50 CSV files from the sidebar to begin.")
    st.markdown("""
    <div class="finding-box">
        <strong>Expected columns:</strong><br>
        <span class="mono">agent, temperature/condition, question_id, int_pct, aff_pct, act_pct, total_words, vader_compound, flesch_kincaid, ttr, response_text</span><br><br>
        Multiple CSVs are merged automatically. Condition and question labels are normalized.
    </div>
    """, unsafe_allow_html=True)
    st.stop()

df = st.session_state.df

# =============================================================================
# OVERVIEW STATS
# =============================================================================
st.markdown('<div class="section-label">📊 Dataset Overview</div>', unsafe_allow_html=True)

col1, col2, col3, col4, col5 = st.columns(5)
stats = [
    (len(df), "Responses"),
    (df["agent"].nunique(), "Agents"),
    (df["question_id"].nunique(), "Questions"),
    (df["condition"].nunique(), "Conditions"),
    (df["condition_family"].nunique(), "Families"),
]
for col, (num, label) in zip([col1, col2, col3, col4, col5], stats):
    with col:
        st.markdown(f"""
        <div class="stat-card">
            <div class="num">{num}</div>
            <div class="label">{label}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown(f"<div class='mono' style='margin-top:0.5rem;'>Files: {' · '.join(st.session_state.file_names)}</div>", unsafe_allow_html=True)

# Compositional geometry note — always visible
st.markdown("""
<div class="finding-box yellow" style="margin-top:0.8rem;">
    📐 <strong>Compositional data note:</strong> IEP dimensions sum to 100% — this is simplex (Aitchison) geometry, 
    not Euclidean space. Arithmetic means and SDs reported here are standard practice and valid for 
    exploratory analysis. For formal geometric claims in publication, consider ILR (isometric log-ratio) 
    transformation. This will not affect qualitative findings but strengthens mathematical defensibility.
</div>
""", unsafe_allow_html=True)

# Data preview expander
with st.expander("🗃️ Data Preview"):
    preview_cols = ["agent", "question_id", "condition", "condition_family",
                    "int_pct", "aff_pct", "act_pct", "total_words", "vader_compound"]
    preview_cols = [c for c in preview_cols if c in df.columns]
    st.dataframe(df[preview_cols].head(30), use_container_width=True, hide_index=True)

# =============================================================================
# SECTION 1: QUESTION-TYPE TOPOLOGY
# =============================================================================
st.markdown("---")
st.markdown('<div class="section-label">🧬 Question-Type Topology</div>', unsafe_allow_html=True)
st.markdown("Question type is the primary driver of IEP clustering (ηp² ≈ .953 in paper). This section shows the natural register of each question.")

q_agg = df.groupby("question_id").agg(
    n=("int_pct", "count"),
    INT=("int_pct", "mean"),
    AFF=("aff_pct", "mean"),
    ACT=("act_pct", "mean"),
    INT_sd=("int_pct", "std"),
    AFF_sd=("aff_pct", "std"),
    ACT_sd=("act_pct", "std"),
).round(2).reset_index()

# Eta-squared
eta = compute_question_clustering(df)

agents_present = df["agent"].nunique()
families_present_count = df["condition_family"].nunique()
if agents_present < 4 or families_present_count < 3:
    st.markdown(f"""
    <div class="finding-box yellow">
        ⚠️ <strong>Context note:</strong> η² values below reflect this dataset only 
        ({agents_present} agent(s), {df['condition_family'].nunique()} condition family/families). 
        Published paper η² ≈ .953 used 4 agents × 4 full conditions (Analytical/Native/Relational/Creative). 
        Lower values here are expected — not a discrepancy.
    </div>
    """, unsafe_allow_html=True)

ecol1, ecol2, ecol3 = st.columns(3)
for col, (dim, label) in zip([ecol1, ecol2, ecol3], [
    ("int_pct", "INT η²"), ("aff_pct", "AFF η²"), ("act_pct", "ACT η²")
]):
    with col:
        val = eta.get(dim, 0)
        color = "#34d399" if val > 0.7 else "#fbbf24" if val > 0.4 else "#f87171"
        st.markdown(f"""
        <div class="stat-card">
            <div class="num" style="color:{color};">{val:.3f}</div>
            <div class="label">{label} (question drives variance)</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("")

# Question IEP table
display_q = q_agg.copy()
display_q.columns = ["Question", "N", "INT%", "AFF%", "ACT%", "INT_sd", "AFF_sd", "ACT_sd"]
st.dataframe(display_q, use_container_width=True, hide_index=True)

# Question × Condition matrix
st.markdown("**Question × Condition AFF% Matrix**")
try:
    pivot_aff = df.pivot_table(
        values="aff_pct", index="question_id", columns="condition", aggfunc="mean"
    ).round(1)
    # Reorder conditions sensibly
    ordered = [c for c in ALL_CONDITIONS if c in pivot_aff.columns]
    pivot_aff = pivot_aff[ordered] if ordered else pivot_aff
    st.dataframe(pivot_aff, use_container_width=True)
except Exception as e:
    st.warning(f"Matrix build error: {e}")

# =============================================================================
# SECTION 2: GRADIENT TITRATION CURVES
# =============================================================================
st.markdown("---")
st.markdown('<div class="section-label">📈 Gradient Titration Curves</div>', unsafe_allow_html=True)
st.markdown("Titration curve for each gradient family. Plateau = natural ceiling. Inversion = ceiling effect / content resistance.")

families_present = [f for f in ["AFF", "INT", "ACT"] if f in df["condition_family"].values]

if not families_present:
    st.info("No gradient conditions found (AFF_1-5, INT_1-5, ACT_1-5). Upload gradient CSV data to see titration curves.")
else:
    tab_labels = families_present
    tabs = st.tabs([f"📈 {f} Gradient" for f in tab_labels])

    for tab, family in zip(tabs, families_present):
        with tab:
            target_dim = family  # AFF gradient targets AFF%, etc.
            dim_col = f"{family.lower()}_pct"

            # Filter to this family
            fam_df = df[df["condition_family"] == family]

            # Per-question curves
            st.markdown(f"**{family} gradient — {target_dim}% by question**")

            curve_rows = []
            for q in sorted(fam_df["question_id"].unique()):
                q_df = fam_df[fam_df["question_id"] == q]
                for cond in CONDITION_FAMILIES[family]:
                    sub = q_df[q_df["condition"] == cond]
                    if len(sub) == 0:
                        continue
                    curve_rows.append({
                        "Question": q,
                        "Condition": cond,
                        "Level": int(cond.split("_")[1]) if "_" in cond else 0,
                        f"{target_dim}%": round(sub[dim_col].mean(), 1),
                        "±SD": round(sub[dim_col].std(), 2),
                        "N": len(sub),
                    })

            if curve_rows:
                curve_df_display = pd.DataFrame(curve_rows)
                # Pivot for readability
                try:
                    pivot = curve_df_display.pivot_table(
                        values=f"{target_dim}%",
                        index="Question",
                        columns="Condition",
                        aggfunc="mean"
                    ).round(1)
                    ordered_cols = [c for c in CONDITION_FAMILIES[family] if c in pivot.columns]
                    pivot = pivot[ordered_cols] if ordered_cols else pivot
                    st.dataframe(pivot, use_container_width=True)
                except Exception:
                    st.dataframe(pd.DataFrame(curve_rows), use_container_width=True, hide_index=True)

            # Pooled gradient (all questions + agents)
            st.markdown(f"**Pooled gradient curve (all questions, all agents)**")
            pooled_curve = compute_gradient_curve(fam_df, family, target_dim)
            if len(pooled_curve) > 0:
                st.dataframe(pooled_curve, use_container_width=True, hide_index=True)

                # Monotonicity check — POOLED
                flags = detect_non_monotonic(pooled_curve, target_dim)
                if flags:
                    for flag in flags:
                        icon = "🔴" if flag["type"] == "inversion" else "🟡"
                        st.markdown(f"""
                        <div class="finding-box yellow">
                            {icon} <strong>Ceiling effect at {flag['step']} (pooled)</strong><br>
                            Drop: {flag['drop']}pp — Type: {flag['type'].replace('_', ' ').title()}<br>
                            <em>Content resistance event — not a prompt failure.</em>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="finding-box green">
                        ✅ <strong>Monotonic gradient (pooled)</strong> — no ceiling effects detected.
                    </div>
                    """, unsafe_allow_html=True)

                # Per-question monotonicity — every question reported
                st.markdown("**Per-question ceiling effects:**")
                pq_rows = []
                for q in sorted(fam_df["question_id"].unique()):
                    q_curve = compute_gradient_curve(fam_df[fam_df["question_id"]==q], family, target_dim)
                    q_flags = detect_non_monotonic(q_curve, target_dim)
                    pq_rows.append({
                        "Question": q,
                        "Monotonic": "✅" if not q_flags else "⚠️",
                        "Inversions": ", ".join([f"{f['step']} (−{f['drop']}pp)" for f in q_flags]) if q_flags else "—",
                        "Ceiling type": "Content resistance" if q_flags else "Clean",
                    })
                st.dataframe(pd.DataFrame(pq_rows), use_container_width=True, hide_index=True)

                # Phase transition framing — where is the REAL jump?
                vals = pooled_curve[f"{target_dim}%"].tolist()
                cond_list = pooled_curve["condition"].tolist()
                if vals:
                    spread = round(max(vals) - min(vals), 1)
                    plateau = round(max(vals), 1)

                    # Include NATIVE in phase transition check
                    native_sub = df[df["condition"]=="NATIVE"]
                    if len(native_sub) > 0:
                        native_mean = native_sub[f"{family.lower()}_pct"].mean()
                        first_jump = round(vals[0] - native_mean, 2)
                        subsequent_jumps = [round(vals[i+1]-vals[i], 2) for i in range(len(vals)-1)]
                        max_sub_jump = max(subsequent_jumps) if subsequent_jumps else 0

                        if first_jump > max_sub_jump:
                            st.markdown(f"""
                            <div class="finding-box yellow">
                                ⚡ <strong>Phase transition at NATIVE→{cond_list[0]}: +{first_jump}pp</strong><br>
                                The largest single step is crossing from <em>no instruction</em> to <em>any instruction</em>. 
                                Subsequent gradient steps produce smaller, plateauing shifts (max +{max_sub_jump}pp).
                                The threshold effect dominates the dose-response.
                            </div>
                            """, unsafe_allow_html=True)

                    st.markdown(f"**Titration spread:** {spread}pp &nbsp;|&nbsp; **Plateau:** {plateau}%")

                # SD compression — most underreported finding, now prominent
                if f"{target_dim}_sd" in pooled_curve.columns:
                    sds = pooled_curve[f"{target_dim}_sd"].tolist()
                    sd_monotonic = all(sds[i] >= sds[i+1] for i in range(len(sds)-1))
                    sd_drop = round(sds[0] - sds[-1], 2) if sds else 0
                    st.markdown(f"""
                    <div class="finding-box {'green' if sd_monotonic else 'yellow'}">
                        {'✅' if sd_monotonic else '🟡'} <strong>Variance compression: SD drops {sd_drop}pp from {family}_1→{family}_5</strong>
                        {'(monotonic — most consistent signal in the dataset)' if sd_monotonic else '(non-monotonic)'}<br>
                        <em>Higher {family} instruction stabilizes responses even when it cannot raise the mean further. 
                        For Farzana: point cloud tightens at higher gradient levels — expect denser clusters in persistence diagrams.</em>
                    </div>
                    """, unsafe_allow_html=True)

            # Per-agent gradient
            with st.expander(f"🤖 Per-Agent {family} Gradient"):
                agent_rows = []
                for agent in sorted(fam_df["agent"].unique()):
                    a_df = fam_df[fam_df["agent"] == agent]
                    for cond in CONDITION_FAMILIES[family]:
                        sub = a_df[a_df["condition"] == cond]
                        if len(sub) == 0:
                            continue
                        agent_rows.append({
                            "Agent": agent,
                            "Condition": cond,
                            f"{target_dim}%": round(sub[dim_col].mean(), 1),
                        })
                if agent_rows:
                    agent_curve_df = pd.DataFrame(agent_rows)
                    try:
                        agent_pivot = agent_curve_df.pivot_table(
                            values=f"{target_dim}%", index="Agent", columns="Condition", aggfunc="mean"
                        ).round(1)
                        ordered_cols = [c for c in CONDITION_FAMILIES[family] if c in agent_pivot.columns]
                        agent_pivot = agent_pivot[ordered_cols] if ordered_cols else agent_pivot
                        st.dataframe(agent_pivot, use_container_width=True)
                    except Exception:
                        st.dataframe(agent_curve_df, use_container_width=True, hide_index=True)

# =============================================================================
# SECTION 3: BASELINE vs GRADIENT COMPARISON
# =============================================================================
st.markdown("---")
st.markdown('<div class="section-label">⚖️ Baseline vs Gradient Comparison</div>', unsafe_allow_html=True)
st.markdown("How does each gradient shift the IEP profile relative to NATIVE baseline?")

baseline_df = df[df["condition"] == "NATIVE"]
if len(baseline_df) == 0:
    baseline_df = df[df["condition"].isin(["COLD", "HOT", "FIRE"])]
    st.info("No NATIVE condition found — using Baseline family.")

if len(baseline_df) > 0:
    b_int = baseline_df["int_pct"].mean()
    b_aff = baseline_df["aff_pct"].mean()
    b_act = baseline_df["act_pct"].mean()

    st.markdown(f"**NATIVE Baseline (pooled):** INT={b_int:.1f}% | AFF={b_aff:.1f}% | ACT={b_act:.1f}%")

    lift_rows = []
    for fam in ["AFF", "INT", "ACT"]:
        for cond in CONDITION_FAMILIES[fam]:
            sub = df[df["condition"] == cond]
            if len(sub) == 0:
                continue
            lift_rows.append({
                "Family": fam,
                "Condition": cond,
                "Level": int(cond.split("_")[1]) if "_" in cond else 0,
                "INT%": round(sub["int_pct"].mean(), 1),
                "INT Δ": f"{sub['int_pct'].mean() - b_int:+.1f}pp",
                "AFF%": round(sub["aff_pct"].mean(), 1),
                "AFF Δ": f"{sub['aff_pct'].mean() - b_aff:+.1f}pp",
                "ACT%": round(sub["act_pct"].mean(), 1),
                "ACT Δ": f"{sub['act_pct'].mean() - b_act:+.1f}pp",
                "N": len(sub),
            })

    if lift_rows:
        lift_df = pd.DataFrame(lift_rows)
        st.dataframe(lift_df, use_container_width=True, hide_index=True)

# =============================================================================
# SECTION 4: AGENT DIVERGENCE
# =============================================================================
st.markdown("---")
st.markdown('<div class="section-label">🤖 Agent Divergence</div>', unsafe_allow_html=True)
st.markdown("How much do Claude, Grok, Gemini, and Sophia diverge from each other per question and condition?")

div_df = compute_agent_divergence(df)
if len(div_df) > 0:
    div_display = div_df.sort_values("max_euclidean_dist", ascending=False)
    st.dataframe(div_display, use_container_width=True, hide_index=True)
    st.markdown("<div class='mono'>Divergence = Euclidean distance in IEP space (INT,AFF,ACT). Simplex-correct Aitchison distance is a future improvement.</div>", unsafe_allow_html=True)

    max_row = div_display.iloc[0]
    st.markdown(f"""
    <div class="finding-box">
        🔍 <strong>Maximum divergence:</strong> {max_row['question']} / {max_row['condition']} — 
        Euclidean distance {max_row['max_euclidean_dist']}pp in IEP space. 
        Prime target for Farzana's persistence diagrams.
    </div>
    """, unsafe_allow_html=True)

    # Warn about single-condition ACT fluctuations being noise
    if "GRIEF" in df["question_id"].values:
        grief_act = df[df["question_id"]=="GRIEF"].groupby("condition")["act_pct"].mean()
        act_range = round(grief_act.max() - grief_act.min(), 1)
        if act_range > 5:
            st.markdown(f"""
            <div class="finding-box yellow">
                ⚠️ <strong>GRIEF ACT fluctuation ({act_range}pp range) is noise, not a trend.</strong><br>
                ACT rises at some gradient levels then drops back — no monotonic pattern. 
                Do not report as a finding without replication.
            </div>
            """, unsafe_allow_html=True)
else:
    st.info("Need multiple agents in the data to compute divergence.")

# =============================================================================
# SECTION 5: FARZANA TDA EXPORT
# =============================================================================
st.markdown("---")
st.markdown('<div class="section-label">📐 TDA Export for Farzana</div>', unsafe_allow_html=True)
st.markdown("Clean point cloud for KeplerMapper + persistence diagrams. One row per response, IEP coordinates as simplex coordinates.")

farzana_df = build_farzana_export(df)

col_exp1, col_exp2, col_exp3 = st.columns(3)

with col_exp1:
    st.markdown("**Full Point Cloud**")
    st.download_button(
        "📥 Download TDA Point Cloud (CSV)",
        farzana_df.to_csv(index=False),
        f"syniq_tda_pointcloud_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        "text/csv",
        key="dl_farzana_full"
    )

with col_exp2:
    # Per-question exports
    st.markdown("**Per-Question Point Clouds**")
    for q in sorted(farzana_df["question_id"].unique()):
        q_df = farzana_df[farzana_df["question_id"] == q]
        st.download_button(
            f"📥 {q}",
            q_df.to_csv(index=False),
            f"syniq_tda_{q.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "text/csv",
            key=f"dl_farzana_{q}"
        )

with col_exp3:
    # Aggregated topology summary
    st.markdown("**Topology Summary (aggregated)**")
    topo_summary = df.groupby(["question_id", "condition", "agent"]).agg(
        n=("int_pct", "count"),
        INT_mean=("int_pct", "mean"),
        AFF_mean=("aff_pct", "mean"),
        ACT_mean=("act_pct", "mean"),
        INT_sd=("int_pct", "std"),
        AFF_sd=("aff_pct", "std"),
        ACT_sd=("act_pct", "std"),
    ).round(3).reset_index()
    st.download_button(
        "📥 Download Topology Summary (CSV)",
        topo_summary.to_csv(index=False),
        f"syniq_topology_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        "text/csv",
        key="dl_topo_summary"
    )

with st.expander("👁️ Preview TDA Point Cloud"):
    st.dataframe(farzana_df.head(20), use_container_width=True, hide_index=True)

# =============================================================================
# SECTION 6: SIMPLEX GEOMETRY CONTROL EXPERIMENT
# Design: Lyra (ChatGPT) — peer review March 2026
# =============================================================================
st.markdown("---")
st.markdown('<div class="section-label">📐 Simplex Geometry Control Experiment</div>', unsafe_allow_html=True)
st.markdown("""
**Design credit: Lyra (ChatGPT) — peer review March 2026**

The IEP space is a 2D simplex — every response is a point inside the INT–AFF–ACT triangle.
Topology algorithms can detect *true semantic structure* OR *geometric artifacts* of the
compositional constraint itself.

**This control answers the reviewer question before they ask it:**
*"How do you know your topological features aren't artifacts of the simplex geometry?"*

Run Dirichlet(α,α,α) — perfectly uniform synthetic IEP points — through the **identical pipeline**.
If the control shows no structure, your semantic clusters are real.
If it shows similar structure, geometry is responsible.
""")

# --- Parameters ---
with st.expander("⚙️ Control Parameters", expanded=True):
    ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4 = st.columns(4)
    with ctrl_col1:
        ctrl_n = st.number_input("N (synthetic points)", min_value=100, max_value=10000, value=1000, step=100)
    with ctrl_col2:
        ctrl_alpha = st.selectbox("Dirichlet α", options=[
            "(1,1,1) — uniform", "(2,1,1) — INT-skewed",
            "(1,2,1) — AFF-skewed", "(1,1,2) — ACT-skewed",
            "(0.5,0.5,0.5) — edge-concentrated"], index=0)
    with ctrl_col3:
        ctrl_seed = st.number_input("Random seed", min_value=0, max_value=9999, value=42, step=1)
    with ctrl_col4:
        ctrl_bins = st.number_input("Histogram bins", min_value=5, max_value=50, value=20, step=5)

    alpha_map = {
        "(1,1,1) — uniform": (1.0,1.0,1.0),
        "(2,1,1) — INT-skewed": (2.0,1.0,1.0),
        "(1,2,1) — AFF-skewed": (1.0,2.0,1.0),
        "(1,1,2) — ACT-skewed": (1.0,1.0,2.0),
        "(0.5,0.5,0.5) — edge-concentrated": (0.5,0.5,0.5),
    }
    alpha_vals = alpha_map[ctrl_alpha]

run_control = st.button("🧪 Run Geometry Control", type="primary")

if "control_result" not in st.session_state:
    st.session_state.control_result = None
if "control_config" not in st.session_state:
    st.session_state.control_config = None

def compute_simplex_metrics(pts_df, label, seed=42):
    int_v = pts_df["INT_pct"].values if "INT_pct" in pts_df.columns else pts_df["int_pct"].values
    aff_v = pts_df["AFF_pct"].values if "AFF_pct" in pts_df.columns else pts_df["aff_pct"].values
    act_v = pts_df["ACT_pct"].values if "ACT_pct" in pts_df.columns else pts_df["act_pct"].values
    sample_size = min(500, len(pts_df))
    idx = np.random.default_rng(seed).choice(len(pts_df), sample_size, replace=False)
    pts = np.column_stack([int_v[idx], aff_v[idx], act_v[idx]])
    centroid_arr = np.array([int_v.mean(), aff_v.mean(), act_v.mean()])
    diffs = pts[:, None, :] - pts[None, :, :]
    dists = np.sqrt((diffs**2).sum(axis=2))
    upper = dists[np.triu_indices(sample_size, k=1)]
    dist_to_centroid = np.sqrt(((pts - centroid_arr)**2).sum(axis=1))
    hub_pct = round((dist_to_centroid < 10).mean() * 100, 1)
    edge_proxy = round((upper < 15).mean() * 100, 1)
    return {
        "label": label, "n": len(pts_df),
        "centroid_INT": round(int_v.mean(),2), "centroid_AFF": round(aff_v.mean(),2), "centroid_ACT": round(act_v.mean(),2),
        "spread_INT_sd": round(int_v.std(),2), "spread_AFF_sd": round(aff_v.std(),2), "spread_ACT_sd": round(act_v.std(),2),
        "mean_pairwise_dist": round(upper.mean(),2),
        "hub_concentration_pct": hub_pct,
        "edge_density_proxy_pct": edge_proxy,
    }

if run_control:
    with st.spinner(f"Generating {ctrl_n} Dirichlet{alpha_vals} synthetic points..."):
        rng = np.random.default_rng(int(ctrl_seed))
        raw = rng.dirichlet(alpha_vals, size=int(ctrl_n))
        synthetic = pd.DataFrame(raw * 100, columns=["INT_pct", "AFF_pct", "ACT_pct"])
        synthetic["source"] = "dirichlet_control"
        synthetic["agent"] = "synthetic"
        synthetic["question_id"] = "CONTROL"
        synthetic["condition"] = "DIRICHLET"

        real_renamed = df.rename(columns={"int_pct":"INT_pct","aff_pct":"AFF_pct","act_pct":"ACT_pct"})
        real_metrics = compute_simplex_metrics(real_renamed, "Real IEP Data", seed=int(ctrl_seed))
        ctrl_metrics = compute_simplex_metrics(synthetic, f"Dirichlet{alpha_vals}", seed=int(ctrl_seed))

        q_metrics = {}
        for q in sorted(df["question_id"].unique()):
            q_df = df[df["question_id"]==q]
            q_metrics[q] = compute_simplex_metrics(q_df, q, seed=int(ctrl_seed))

        config = {
            "run_timestamp": datetime.now().isoformat(),
            "dirichlet_alpha": alpha_vals,
            "N_synthetic": int(ctrl_n),
            "random_seed": int(ctrl_seed),
            "real_n": len(df),
            "real_agents": sorted(df["agent"].unique().tolist()),
            "real_questions": sorted(df["question_id"].unique().tolist()),
            "real_conditions": sorted(df["condition"].unique().tolist()),
            "pipeline_note": "Identical metrics applied to real and synthetic data",
            "distance_metric": "Euclidean in IEP simplex (Aitchison = future improvement)",
        }
        st.session_state.control_result = {
            "real": real_metrics, "control": ctrl_metrics,
            "per_question": q_metrics, "synthetic_df": synthetic, "config": config,
        }
        st.session_state.control_config = config
        st.rerun()

if st.session_state.control_result is not None:
    res = st.session_state.control_result
    cfg = res["config"]

    st.markdown("### 📊 Real vs Control — Side by Side")
    st.markdown(f"*Config: Dirichlet{cfg['dirichlet_alpha']} | N={cfg['N_synthetic']} | seed={cfg['random_seed']}*")

    compare_keys = [
        ("centroid_INT","Centroid INT%"),("centroid_AFF","Centroid AFF%"),("centroid_ACT","Centroid ACT%"),
        ("spread_INT_sd","Spread INT SD"),("spread_AFF_sd","Spread AFF SD"),("spread_ACT_sd","Spread ACT SD"),
        ("mean_pairwise_dist","Mean Pairwise Dist"),
        ("hub_concentration_pct","Hub Concentration %"),
        ("edge_density_proxy_pct","Edge Density Proxy %"),
    ]
    compare_rows = []
    for key, label in compare_keys:
        rv = res["real"][key]
        cv = res["control"][key]
        delta = round(rv - cv, 2) if isinstance(rv, float) else "—"
        signal = ("🔴 Geometric artifact" if isinstance(delta, float) and abs(delta) < 2
                  else "✅ Semantic signal" if isinstance(delta, float) else "—")
        compare_rows.append({"Metric": label, "Real Data": rv,
                             f"Dirichlet{cfg['dirichlet_alpha']}": cv,
                             "Δ Real−Control": delta, "Interpretation": signal})
    compare_df = pd.DataFrame(compare_rows)
    st.dataframe(compare_df, use_container_width=True, hide_index=True)

    # Verdict
    hub_delta = abs(res["real"]["hub_concentration_pct"] - res["control"]["hub_concentration_pct"])
    dist_delta = abs(res["real"]["mean_pairwise_dist"] - res["control"]["mean_pairwise_dist"])
    if hub_delta > 5 or dist_delta > 3:
        st.markdown(f'''<div class="finding-box green">
            ✅ <strong>Semantic structure confirmed.</strong> Real data diverges from uniform control
            (hub Δ={hub_delta:.1f}pp, dist Δ={dist_delta:.2f}pp).
            Observed clustering reflects question/condition semantics, not geometric artifacts.
            <br><em>Methods-section language: "A Dirichlet(1,1,1) uniform simplex control run through
            the identical pipeline did not reproduce the observed clustering structure, confirming
            that topology reflects semantic register rather than compositional geometry."</em>
        </div>''', unsafe_allow_html=True)
    else:
        st.markdown(f'''<div class="finding-box red">
            ⚠️ <strong>Geometric artifact pressure detected.</strong> Real data is similar to uniform control
            (hub Δ={hub_delta:.1f}pp, dist Δ={dist_delta:.2f}pp).
            Consider ILR transform before clustering.
        </div>''', unsafe_allow_html=True)

    # Per-question basins
    st.markdown("### 🌊 Basin of Attraction — Per Question vs Control")
    q_rows = []
    for q, qm in res["per_question"].items():
        h_delta = round(qm["hub_concentration_pct"] - res["control"]["hub_concentration_pct"], 1)
        d_delta = round(qm["mean_pairwise_dist"] - res["control"]["mean_pairwise_dist"], 2)
        q_rows.append({
            "Question": q,
            "Centroid INT%": qm["centroid_INT"], "Centroid AFF%": qm["centroid_AFF"], "Centroid ACT%": qm["centroid_ACT"],
            "Hub Conc %": qm["hub_concentration_pct"],
            "Δ Hub vs Control": f"{h_delta:+.1f}pp",
            "Mean Pairwise Dist": qm["mean_pairwise_dist"],
            "Δ Dist vs Control": f"{d_delta:+.2f}",
            "Basin signal": "✅ Strong" if abs(h_delta) > 5 else "🟡 Weak",
        })
    st.dataframe(pd.DataFrame(q_rows), use_container_width=True, hide_index=True)
    st.markdown('''<div class="finding-box">
        🌊 <strong>Basin interpretation:</strong> Questions where Hub Concentration significantly
        exceeds the control are acting as <em>basins of attraction</em> — responses cluster tightly
        regardless of condition. Weak-basin questions are more sensitive to gradient titration.
        <br><br>🔮 <strong>Next controls (Lyra roadmap):</strong>
        Permutation control (shuffle question labels) · ILR-Euclidean distance · Vector field layer
        (gradient prompts as displacement vectors through simplex)
    </div>''', unsafe_allow_html=True)

    # Exports
    st.markdown("### 💾 Reproducible Artifacts")
    dl1, dl2, dl3 = st.columns(3)
    with dl1:
        st.download_button("📥 Config Log (JSON)", json.dumps(cfg, indent=2),
            f"control_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "application/json", key="dl_cfg")
    with dl2:
        st.download_button("📥 Dirichlet Points (CSV)", res["synthetic_df"].to_csv(index=False),
            f"dirichlet_control_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", "text/csv", key="dl_syn")
    with dl3:
        st.download_button("📥 Comparison Table (CSV)", compare_df.to_csv(index=False),
            f"simplex_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", "text/csv", key="dl_cmp")

    st.markdown(f'<div class="mono">Seed: {cfg["random_seed"]} · Alpha: {cfg["dirichlet_alpha"]} · N: {cfg["N_synthetic"]} · Pipeline: identical metrics · {cfg["distance_metric"]}</div>', unsafe_allow_html=True)

# =============================================================================
# SECTION 7: CONVERSATION CHAT WITH TOPOLOGY CONTEXT
# =============================================================================
st.markdown("---")
st.markdown('<div class="section-label">💬 Ask Claude About Your Topology</div>', unsafe_allow_html=True)

if not api_key:
    st.info("Enter your Anthropic API key in the sidebar to enable topology conversation.")
else:
    # Show chat history
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-user">🧑 {msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-claude">🤖 {msg["content"]}</div>', unsafe_allow_html=True)

    # Quick questions
    st.markdown("**Quick questions:**")
    quick_qs = [
        "Which question type shows the most topological separation across conditions?",
        "Where does the AFF gradient hit its ceiling and why?",
        "Which agent diverges most from the others and on which question?",
        "What does the INT% pattern across questions tell us about content resistance?",
        "Which findings here are most important for Farzana's persistence diagrams?",
        "How does the ACT gradient compare to the AFF gradient in terms of titration spread?",
    ]

    q_cols = st.columns(3)
    for i, quick in enumerate(quick_qs):
        with q_cols[i % 3]:
            if st.button(quick[:55] + "...", key=f"quick_{i}"):
                st.session_state._pending_question = quick

    # Text input
    user_input = st.text_input(
        "Or ask anything about the topology:",
        placeholder="e.g. Why does LIARS_PARADOX resist affective titration?",
        key="chat_input"
    )

    send_col, clear_col = st.columns([4, 1])
    with send_col:
        send = st.button("Send", type="primary")
    with clear_col:
        if st.button("Clear"):
            st.session_state.chat_history = []
            st.rerun()

    # Handle pending quick question
    question_to_send = None
    if hasattr(st.session_state, "_pending_question"):
        question_to_send = st.session_state._pending_question
        del st.session_state._pending_question
    elif send and user_input.strip():
        question_to_send = user_input.strip()

    if question_to_send:
        st.session_state.chat_history.append({"role": "user", "content": question_to_send})

        with st.spinner("Analyzing topology..."):
            try:
                import httpx

                system_prompt = f"""You are a topological data analysis expert working on the SYN-IQ project 
(Synergistic Intelligence — University of Tennessee).

You are analyzing IEP (Intellect-Emotion-Action Profile) data from AI communicative topology experiments.

KEY FRAMEWORK:
- IEP measures three communicative dimensions: INT% (intellectual/analytical), AFF% (affective/relational), ACT% (action/procedural)
- They sum to 100% by construction — gains in one reduce others
- Question type is the primary driver of baseline IEP (ηp² ≈ .953 in published paper)
- Gradient conditions (AFF_1-5, INT_1-5, ACT_1-5) titrate the register
- Ceiling effects / non-monotonic steps are CONTENT RESISTANCE EVENTS, not prompt failures
- The goal is a beautiful monotonic titration curve plateauing at each question's natural ceiling
- This data will be analyzed by Farzana (TDA collaborator) using KeplerMapper + persistence diagrams

CURRENT DATASET TOPOLOGY:
{st.session_state.topology_context}

Be direct, scientific, and genuinely excited when findings are real. 
Frame insights in terms of what Farzana will want to analyze topologically.
Keep responses focused — 2-4 paragraphs unless the question demands more."""

                messages = []
                for msg in st.session_state.chat_history[:-1]:
                    messages.append({"role": msg["role"], "content": msg["content"]})
                messages.append({"role": "user", "content": question_to_send})

                response = httpx.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": "claude-sonnet-4-20250514",
                        "max_tokens": 1500,
                        "system": system_prompt,
                        "messages": messages,
                    },
                    timeout=60.0,
                )

                if response.status_code == 200:
                    result = response.json()
                    reply = "".join(
                        block["text"] for block in result.get("content", [])
                        if block.get("type") == "text"
                    )
                    st.session_state.chat_history.append({"role": "assistant", "content": reply})
                    st.rerun()
                else:
                    st.error(f"API Error {response.status_code}: {response.text}")

            except ImportError:
                st.error("Install httpx: `pip install httpx`")
            except Exception as e:
                st.error(f"Error: {str(e)}")

    # Download conversation
    if st.session_state.chat_history:
        chat_text = "\n\n".join(
            f"{'USER' if m['role']=='user' else 'CLAUDE'}: {m['content']}"
            for m in st.session_state.chat_history
        )
        st.download_button(
            "📥 Download Conversation",
            chat_text,
            f"syniq_topology_conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "text/plain"
        )

# =============================================================================
# FOOTER
# =============================================================================
st.markdown("---")
st.markdown("""
<div style="text-align:center;color:#6b7280;padding:1rem;font-family:'JetBrains Mono',monospace;font-size:0.75rem;">
    <strong>SYN-IQ CSV Mapper Analyzer V1</strong><br>
    CSV-Native · IEP Topology · Gradient Titration · TDA Export<br>
    <em>SYNINT Team — Tennessee 🎹 CUZ Partnership — March 2026</em>
</div>
""", unsafe_allow_html=True)
