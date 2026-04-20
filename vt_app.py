"""
V_t Voice-State Analyzer — Streamlit App
Wraps vt_analyzer.py in a browser-based interface.

USAGE:
    streamlit run vt_app.py

Requires vt_analyzer.py to be in the same folder.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO

from vt_analyzer import analyze_response, analyze_csv

# -----------------------------------------------------------------------------
# Page config
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="V_t Voice-State Analyzer",
    page_icon="📊",
    layout="wide",
)

st.title("V_t Voice-State Analyzer")
st.caption("Paper 2 — Empirical Measurement of Voice-State Parameters")

with st.expander("What do the parameters mean?", expanded=False):
    st.markdown("""
    - **S_t — Structure Density** `[0, 1]` — how tightly organized (bullets, headers, connectives)
    - **A_t — Abstraction Level** `[0, 1]` — concrete ↔ conceptual
    - **Q_t — Querying Intensity** `[0, 1]` — degree of clarifying questions
    - **D_t — Directiveness** `[0, 1]` — strength of recommendations
    - **R_t — Relational Warmth** `[0, 1]` — social/affective engagement
    """)

st.divider()

# -----------------------------------------------------------------------------
# File uploader
# -----------------------------------------------------------------------------
uploaded = st.file_uploader(
    "Upload your V50 CSV",
    type=["csv"],
    help="Must contain a 'response_text' column (or specify a different column below).",
)

text_col = st.text_input("Text column name", value="response_text")

# -----------------------------------------------------------------------------
# Main processing
# -----------------------------------------------------------------------------
if uploaded is not None:
    try:
        df_raw = pd.read_csv(uploaded)
    except Exception as e:
        st.error(f"Could not read CSV: {e}")
        st.stop()

    if text_col not in df_raw.columns:
        st.error(f"Column '{text_col}' not found. Available columns: {list(df_raw.columns)}")
        st.stop()

    st.success(f"Loaded {len(df_raw)} responses from `{uploaded.name}`")

    with st.spinner(f"Analyzing {len(df_raw)} responses..."):
        vt_results = df_raw[text_col].apply(analyze_response)
        vt_df = pd.DataFrame(vt_results.tolist())
        df = pd.concat([df_raw, vt_df], axis=1)

    # -------------------------------------------------------------------------
    # Summary metrics
    # -------------------------------------------------------------------------
    st.subheader("V_t Summary")
    cols = st.columns(5)
    params = ["S_t", "A_t", "Q_t", "D_t", "R_t"]
    labels = ["Structure", "Abstraction", "Querying", "Directiveness", "Warmth"]

    for col, param, label in zip(cols, params, labels):
        mean = df[param].mean()
        std = df[param].std()
        col.metric(
            label=f"{param} — {label}",
            value=f"{mean:.3f}",
            delta=f"σ = {std:.3f}",
            delta_color="off",
        )

    # -------------------------------------------------------------------------
    # Radar chart
    # -------------------------------------------------------------------------
    st.subheader("Voice-State Shape")

    group_options = []
    if "agent" in df.columns and df["agent"].nunique() > 1:
        group_options.append("agent")
    if "question_id" in df.columns and df["question_id"].nunique() > 1:
        group_options.append("question_id")
    group_options.append("(overall only)")

    group_by = st.selectbox("Group radar by:", group_options, index=0)

    fig = go.Figure()
    categories = params + [params[0]]  # close the loop

    if group_by == "(overall only)":
        values = [df[p].mean() for p in params]
        values.append(values[0])
        fig.add_trace(go.Scatterpolar(
            r=values, theta=categories, fill="toself", name="Overall"
        ))
    else:
        for key in sorted(df[group_by].unique()):
            sub = df[df[group_by] == key]
            values = [sub[p].mean() for p in params]
            values.append(values[0])
            fig.add_trace(go.Scatterpolar(
                r=values, theta=categories, fill="toself", name=str(key)
            ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        showlegend=True,
        height=500,
    )
    st.plotly_chart(fig, use_container_width=True)

    # -------------------------------------------------------------------------
    # Per-question breakdown
    # -------------------------------------------------------------------------
    if "question_id" in df.columns:
        st.subheader("Per-Question V_t Means")
        q_table = df.groupby("question_id")[params].mean().round(3)
        st.dataframe(q_table, use_container_width=True)

    # -------------------------------------------------------------------------
    # Per-agent breakdown
    # -------------------------------------------------------------------------
    if "agent" in df.columns and df["agent"].nunique() > 1:
        st.subheader("Per-Agent V_t Means")
        a_table = df.groupby("agent")[params].mean().round(3)
        st.dataframe(a_table, use_container_width=True)

    # -------------------------------------------------------------------------
    # Download button
    # -------------------------------------------------------------------------
    st.subheader("Download Results")
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    out_name = uploaded.name.replace(".csv", "_vt.csv")
    st.download_button(
        label=f"Download {out_name}",
        data=csv_bytes,
        file_name=out_name,
        mime="text/csv",
    )

    # -------------------------------------------------------------------------
    # Raw data (expandable)
    # -------------------------------------------------------------------------
    with st.expander("Raw data — all responses with V_t scores"):
        st.dataframe(df, use_container_width=True)

else:
    st.info("👆 Upload a V50 CSV to begin.")
