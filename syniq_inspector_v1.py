"""
SYN-IQ Node Inspector V1 — Streamlit App
=========================================

A read-the-actual-texts tool for SYN-IQ analysis. Sibling to V21 Mapper.

Purpose
-------
The Mapper and PCA1 show you WHERE the interesting structure is. The
Inspector lets you read WHAT is actually inside. Drop in the same CSV
V21 reads, point at any subset of responses (an outlier, a cluster, a
PC1 region, a node), and immediately see the texts side-by-side with
their full feature scores.

Built for the closing-the-loop workflow:
  1. Mapper reveals an outlier or cluster.
  2. Inspector pulls up the responses.
  3. You read them and decide: signal or noise.

V1 features
-----------
- Loads any SYN-IQ harvester CSV (V48 22-col through V56 60-col schema)
- Slice by agent / temperature / question / run / PC1 range
- Side-by-side text view (up to 5 responses at once)
- Per-response feature card: IEP rollup, V_t, CAM, subtypes (when present)
- Vocabulary novelty analysis: how much of each response is genuinely
  new vs. shared with the rest of the slice
- Side-by-side stats: word count, IEP rollup, V_t (when present)
- PC1 strip plot of the current slice (for orientation)

V1 deliberately does NOT do:
- Mapper topology (use V21 for that)
- Claude analysis (Inspector is for YOUR reading, not AI's)
- Editing CSVs (read-only by design)

Run: streamlit run syniq_inspector_v1.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import re
from collections import Counter
from sklearn.decomposition import PCA

st.set_page_config(
    page_title="SYN-IQ Inspector V1",
    page_icon="🔍",
    layout="wide",
)

# Canonical agent colors (same as V21 — keep consistency across tools)
AGENT_COLORS = {
    "Claude":  "#377eb8",
    "ChatGPT": "#4daf4a",
    "Grok":    "#e41a1c",
    "Gemini":  "#984ea3",
}

# Feature columns we look for and what scoring family they belong to
IEP_COLS    = ["int_pct", "aff_pct", "act_pct"]
VT_COLS     = ["S_t", "A_t", "Q_t", "D_t", "R_t"]
CAM_COLS    = ["con_pct", "abs_pct", "met_pct", "cam_matched"]
STYLE_COLS  = ["total_words", "unique_words", "ttr",
               "flesch_kincaid", "flesch_ease",
               "vader_compound", "vader_pos", "vader_neg", "vader_neu"]
SUBTYPE_PREFIXES = ("aff_sub_", "int_sub_", "act_sub_")


def normalize_agent_column(df):
    """Sophia → ChatGPT, idempotent."""
    if "agent" in df.columns:
        df["agent"] = df["agent"].replace({"Sophia": "ChatGPT", "sophia": "ChatGPT"})
    return df


def detect_schema(df):
    """Return flags for what feature families are present."""
    cols = set(df.columns)
    return {
        "iep":      all(c in cols for c in IEP_COLS),
        "vt":       all(c in cols for c in VT_COLS),
        "cam":      all(c in cols for c in CAM_COLS),
        "subtypes": any(c.startswith(SUBTYPE_PREFIXES) for c in cols),
        "text":     "response_text" in cols,
    }


def tokens(text):
    """Lowercase word tokens for vocabulary analysis."""
    if not isinstance(text, str):
        return []
    return re.findall(r"\b[a-z]+\b", text.lower())


def compute_pc1(df, feature_cols):
    """Compute 1D PCA on the given columns. Returns the projection."""
    feats = df[feature_cols].fillna(0).values
    if len(feats) < 2:
        return np.zeros(len(feats)), 0.0
    pca = PCA(n_components=1).fit(feats)
    pc1 = pca.transform(feats).flatten()
    return pc1, float(pca.explained_variance_ratio_[0])


# =============================================================================
# HEADER
# =============================================================================
st.title("🔍 SYN-IQ Node Inspector V1")
st.caption(
    "Read the actual response texts behind your Mapper and PCA structure. "
    "Sibling tool to V21 Mapper — drop in the same CSV, slice to any subset, "
    "compare texts side by side."
)

# =============================================================================
# SIDEBAR — DATA LOAD & SCHEMA DETECTION
# =============================================================================
st.sidebar.header("Data")
uploaded = st.sidebar.file_uploader(
    "Drop a SYN-IQ harvester CSV", type=["csv"],
    help="V48 (22 cols) through V56 (60 cols) — Inspector adapts to the schema."
)

if uploaded is None:
    st.info(
        "👈 Drop a SYN-IQ harvester CSV to begin.\n\n"
        "**Example workflow:**\n\n"
        "1. V21 Mapper highlights an outlier (e.g., three Grok rural healthcare "
        "responses at PC1 > 3).\n"
        "2. Load the same CSV here.\n"
        "3. Filter to Grok + RURAL_HEALTHCARE, set PC1 range to ≥ 3.\n"
        "4. Read the texts side by side. Are they padding, or genuine novelty?\n"
        "5. Inspector tells you in one screen, instead of running scripts."
    )
    st.stop()

# Load & normalize
df = pd.read_csv(uploaded)
df = normalize_agent_column(df)
flags = detect_schema(df)

st.sidebar.success(f"✅ {len(df)} rows · {len(df.columns)} columns")
schema_parts = []
if flags["iep"]:      schema_parts.append("IEP")
if flags["vt"]:       schema_parts.append("V_t")
if flags["cam"]:      schema_parts.append("CAM")
if flags["subtypes"]: schema_parts.append("subtypes")
if flags["text"]:     schema_parts.append("text")
if not flags["text"]:
    st.sidebar.error("❌ No `response_text` column — Inspector needs texts.")
    st.stop()
st.sidebar.caption("Schema: " + " · ".join(schema_parts))

# =============================================================================
# SIDEBAR — SLICE FILTERS
# =============================================================================
st.sidebar.markdown("---")
st.sidebar.header("Slice")

sliced = df.copy()

# Agent
if "agent" in sliced.columns:
    agents = sorted(sliced["agent"].dropna().unique().tolist())
    pick = st.sidebar.multiselect("Agent", agents, default=agents)
    sliced = sliced[sliced["agent"].isin(pick)]

# Temperature
if "temperature" in sliced.columns:
    temps = sorted(sliced["temperature"].dropna().unique().tolist())
    pick = st.sidebar.multiselect("Temperature", temps, default=temps)
    sliced = sliced[sliced["temperature"].isin(pick)]

# Question
if "question_id" in sliced.columns:
    qs = sorted(sliced["question_id"].dropna().unique().tolist())
    pick = st.sidebar.multiselect("Question", qs, default=qs)
    sliced = sliced[sliced["question_id"].isin(pick)]

sliced = sliced.reset_index(drop=True)
if len(sliced) == 0:
    st.warning("Slice is empty — widen the filters.")
    st.stop()

# =============================================================================
# COMPUTE PC1 ON THE SLICE (for orientation + selection)
# =============================================================================
# Use the same 12-feature space V21 uses for raw PCA so dots map between tools
v21_feats = [c for c in [
    "int_pct", "aff_pct", "act_pct",
    "vader_compound", "vader_pos", "vader_neg", "vader_neu",
    "flesch_kincaid", "flesch_ease", "ttr",
    "total_words", "unique_words",
] if c in sliced.columns]

if len(v21_feats) >= 2 and len(sliced) >= 2:
    pc1, evr = compute_pc1(sliced, v21_feats)
    sliced["pc1"] = pc1
else:
    sliced["pc1"] = 0.0
    evr = 0.0

# =============================================================================
# MAIN AREA — TWO COLUMNS: STRIP PLOT + STATS / DETAIL
# =============================================================================
st.markdown(f"### Slice: {len(sliced)} responses · PC1 explains {evr*100:.1f}% var")

# Compact summary stats for the slice
sum_cols = st.columns(4)
with sum_cols[0]:
    if "agent" in sliced.columns:
        ac = sliced["agent"].value_counts().to_dict()
        st.metric("Agents", len(ac), help=", ".join(f"{a}={n}" for a, n in ac.items()))
with sum_cols[1]:
    st.metric("Mean words", f"{sliced['total_words'].mean():.0f}" if "total_words" in sliced.columns else "—")
with sum_cols[2]:
    if flags["iep"]:
        st.metric("Mean INT/AFF/ACT",
                  f"{sliced['int_pct'].mean():.0f}/{sliced['aff_pct'].mean():.0f}/{sliced['act_pct'].mean():.0f}")
with sum_cols[3]:
    st.metric("PC1 range", f"{sliced['pc1'].min():+.1f} → {sliced['pc1'].max():+.1f}")

st.markdown("---")

# PC1 strip plot (Plotly), colored by agent
try:
    import plotly.graph_objects as go

    fig = go.Figure()
    rng = np.random.default_rng(42)
    if "agent" in sliced.columns:
        for ag in sorted(sliced["agent"].unique()):
            sub = sliced[sliced["agent"] == ag]
            y = rng.uniform(-0.4, 0.4, size=len(sub))
            color = AGENT_COLORS.get(ag, "#888888")
            qid_col = "question_id" if "question_id" in sub.columns else None
            hover = []
            for _, r in sub.iterrows():
                line = f"run={r.get('run','?')} · words={r.get('total_words','?')}"
                if qid_col:
                    line += f" · {r.get(qid_col,'')}"
                if flags["iep"]:
                    line += f"<br>IEP: I={r['int_pct']:.0f} A={r['aff_pct']:.0f} C={r['act_pct']:.0f}"
                hover.append(line)
            fig.add_trace(go.Scatter(
                x=sub["pc1"], y=y, mode="markers", name=ag,
                marker=dict(size=10, color=color, line=dict(width=0.5, color="#333")),
                text=hover,
                hovertemplate="%{text}<br>PC1=%{x:.2f}<extra></extra>",
                customdata=sub.index,
            ))
    else:
        y = rng.uniform(-0.4, 0.4, size=len(sliced))
        fig.add_trace(go.Scatter(x=sliced["pc1"], y=y, mode="markers",
                                  marker=dict(size=10, color="#377eb8")))

    fig.update_layout(
        title=f"PC1 strip plot — PC1 explains {evr*100:.1f}% of variance",
        xaxis_title="PC1",
        yaxis=dict(visible=False, range=[-1, 1]),
        plot_bgcolor="white", paper_bgcolor="white",
        height=300, showlegend=("agent" in sliced.columns),
    )
    st.plotly_chart(fig, use_container_width=True)
except Exception as e:
    st.warning(f"Plotly strip plot unavailable ({e}). Using table view only.")

# =============================================================================
# SELECTION — choose by PC1 range OR by explicit run picker
# =============================================================================
st.markdown("### Pick responses to read")

mode = st.radio(
    "Selection mode",
    ["By PC1 range", "By run number", "All in slice"],
    horizontal=True,
)

if mode == "By PC1 range":
    pmin, pmax = float(sliced["pc1"].min()), float(sliced["pc1"].max())
    if pmin == pmax:
        pmax = pmin + 1.0
    lo, hi = st.slider(
        "PC1 range", min_value=pmin, max_value=pmax, value=(pmin, pmax),
        step=(pmax - pmin) / 100 if pmax > pmin else 0.1,
    )
    picked = sliced[(sliced["pc1"] >= lo) & (sliced["pc1"] <= hi)].copy()

elif mode == "By run number":
    run_col = "run" if "run" in sliced.columns else None
    if run_col is None:
        st.warning("No `run` column — try another selection mode.")
        picked = sliced.iloc[:0]
    else:
        runs = sorted(sliced[run_col].unique().tolist())
        pick_runs = st.multiselect("Runs", runs, default=runs[:3])
        picked = sliced[sliced[run_col].isin(pick_runs)].copy()
else:
    picked = sliced.copy()

picked = picked.sort_values("pc1").reset_index(drop=True)
st.caption(f"Selected: {len(picked)} responses.")

if len(picked) == 0:
    st.info("No responses in current selection. Widen the range or pick runs.")
    st.stop()

# =============================================================================
# VOCABULARY NOVELTY ANALYSIS
# =============================================================================
with st.expander("📊 Vocabulary novelty analysis", expanded=True):
    st.caption(
        "For each selected response, how much of its vocabulary is genuinely "
        "new vs. shared with the rest of the slice? High novelty = response "
        "introduces concepts the others don't. Low novelty = response uses "
        "the same vocabulary as the rest."
    )
    if len(picked) >= 1 and len(sliced) >= 2:
        # Reference vocabulary = union of tokens across the WHOLE slice
        # MINUS each response itself (computed per-response below)
        slice_all_tokens = [set(tokens(t)) for t in sliced["response_text"].fillna("")]

        # For each row in picked, find its index in the slice and compute novelty
        nov_rows = []
        for _, prow in picked.iterrows():
            # Find this row in sliced by matching turn_id/run if available
            mask = pd.Series([True] * len(sliced))
            for key in ("turn_id", "run", "agent"):
                if key in sliced.columns and key in prow.index:
                    mask &= (sliced[key] == prow[key])
            idxs = sliced.index[mask].tolist()
            if not idxs:
                continue
            i = idxs[0]
            own_tokens = slice_all_tokens[i]
            others_tokens = set()
            for j, s in enumerate(slice_all_tokens):
                if j != i:
                    others_tokens |= s
            novel = own_tokens - others_tokens
            rate = len(novel) / max(len(own_tokens), 1)
            nov_rows.append({
                "run": prow.get("run", "?"),
                "agent": prow.get("agent", "?"),
                "words": prow.get("total_words", "?"),
                "unique": len(own_tokens),
                "novel_vs_slice": len(novel),
                "novelty_rate": f"{rate*100:.1f}%",
            })
        if nov_rows:
            nov_df = pd.DataFrame(nov_rows)
            st.dataframe(nov_df, use_container_width=True, hide_index=True)

# =============================================================================
# SIDE-BY-SIDE TEXT VIEW
# =============================================================================
st.markdown("### Read the texts")
st.caption("Up to 5 columns side by side. Pick more in selection and they appear stacked below.")

# Show in batches of 5 columns
chunk_size = 5
for start in range(0, len(picked), chunk_size):
    chunk = picked.iloc[start:start + chunk_size]
    cols = st.columns(len(chunk))
    for col, (_, r) in zip(cols, chunk.iterrows()):
        with col:
            ag = str(r.get("agent", "?"))
            color = AGENT_COLORS.get(ag, "#666")
            st.markdown(
                f"<div style='border-left:4px solid {color}; padding-left:8px; margin-bottom:8px;'>"
                f"<b>{ag}</b> · run {r.get('run','?')}<br>"
                f"<span style='color:#666; font-size:0.85em;'>"
                f"PC1={r['pc1']:+.2f} · {r.get('total_words','?')} words · "
                f"{r.get('unique_words','?')} unique"
                f"</span>"
                f"</div>",
                unsafe_allow_html=True
            )
            # Feature card
            with st.expander("Feature scores", expanded=False):
                lines = []
                if flags["iep"]:
                    lines.append(f"**IEP** · I={r.get('int_pct',0):.1f} A={r.get('aff_pct',0):.1f} C={r.get('act_pct',0):.1f}")
                if flags["vt"]:
                    lines.append(f"**V_t** · S={r.get('S_t',0):.2f} A={r.get('A_t',0):.2f} Q={r.get('Q_t',0):.2f} D={r.get('D_t',0):.2f} R={r.get('R_t',0):.2f}")
                if flags["cam"]:
                    lines.append(f"**CAM** · C={r.get('con_pct',0):.0f} A={r.get('abs_pct',0):.0f} M={r.get('met_pct',0):.0f}")
                if "vader_compound" in r.index:
                    lines.append(f"**VADER** · compound={r.get('vader_compound',0):.2f}")
                if "flesch_kincaid" in r.index:
                    lines.append(f"**FK grade** · {r.get('flesch_kincaid',0):.1f}")
                if "ttr" in r.index:
                    lines.append(f"**TTR** · {r.get('ttr',0):.3f}")
                # Subtype top-3 per family if present
                if flags["subtypes"]:
                    for fam, prefix in [("AFF", "aff_sub_"), ("INT", "int_sub_"), ("ACT", "act_sub_")]:
                        subs = [(c.replace(prefix, ""), float(r[c])) for c in r.index if c.startswith(prefix)]
                        subs = sorted(subs, key=lambda x: x[1], reverse=True)[:3]
                        if subs:
                            sub_str = ", ".join(f"{n}={v:.1f}" for n, v in subs)
                            lines.append(f"**{fam} top-3** · {sub_str}")
                st.markdown("  \n".join(lines))
            # The actual text
            txt = str(r.get("response_text", "")) or "*(empty)*"
            st.markdown(
                f"<div style='font-size:0.92em; line-height:1.4; "
                f"max-height:500px; overflow-y:auto; padding:8px; "
                f"border:1px solid #ddd; border-radius:4px;'>{txt}</div>",
                unsafe_allow_html=True
            )

# =============================================================================
# SIDE-BY-SIDE STATS COMPARISON
# =============================================================================
st.markdown("---")
with st.expander("📋 Side-by-side stats table (CSV-downloadable)", expanded=False):
    cmp_cols = ["agent", "run", "pc1", "total_words", "unique_words", "ttr"]
    if flags["iep"]: cmp_cols += IEP_COLS
    if flags["vt"]:  cmp_cols += VT_COLS
    if flags["cam"]: cmp_cols += ["con_pct", "abs_pct", "met_pct"]
    cmp_cols = [c for c in cmp_cols if c in picked.columns or c == "pc1"]
    st.dataframe(picked[cmp_cols], use_container_width=True, hide_index=True)
    csv = picked[cmp_cols].to_csv(index=False)
    st.download_button("📥 Download selected stats as CSV", csv,
                       file_name="syniq_inspector_selection.csv", mime="text/csv")
