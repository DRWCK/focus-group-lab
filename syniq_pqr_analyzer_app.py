"""
SYN-IQ PQR Analyzer App V1.0.0 — Streamlit UI

A thin Streamlit wrapper around syniq_pqr_analyzer.analyze(). Lets users:
  - Paste a prompt (system message / directive)
  - Paste a question (user-side question)
  - Paste a response (model output)
  - See the IEP/V_t/CAM scores for each
  - See the triangulation metric showing how the response resolved P vs Q
  - See inline IEP-colored highlighting of all three texts

Also supports batch mode: upload a CSV with prompt_text / question_text /
response_text columns (the V56 harvester export format) and get per-row
PQR triangulation + a per-agent summary.

Run:  streamlit run syniq_pqr_analyzer_app.py

This UI imports from syniq_pqr_analyzer.py — never reimplements scoring
or rendering. Same instrument, same units across all SYN-IQ tools.
"""

import sys, os
from io import StringIO

# Make sibling modules importable regardless of where Streamlit is launched from.
_HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (_HERE, '/mnt/project', '/home/claude'):
    if _p and _p not in sys.path:
        sys.path.insert(0, _p)

import streamlit as st
import pandas as pd

# Lazy import so a missing dependency shows up as a clear error in the UI,
# not a stack trace at module load.
try:
    from syniq_pqr_analyzer import (
        analyze, analyze_batch, summarize_batch, PQR_ANALYZER_VERSION,
    )
    _IMPORT_OK = True
    _IMPORT_ERR = None
except ImportError as e:
    _IMPORT_OK = False
    _IMPORT_ERR = str(e)


# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="SYN-IQ PQR Analyzer",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    "<h1 style='margin-bottom:0.2em;'>🎯 SYN-IQ PQR Analyzer</h1>"
    "<p style='color:#64748b; margin-top:0;'>"
    "Prompt × Question × Response triangulation. Measures how a model resolved "
    "the conflict between a steering directive and the question's natural register."
    "</p>",
    unsafe_allow_html=True,
)

if not _IMPORT_OK:
    st.error(
        f"Could not import syniq_pqr_analyzer. The PQR module needs to be in "
        f"the same folder as this app, or on Python's path. Error: {_IMPORT_ERR}"
    )
    st.stop()


# =============================================================================
# SIDEBAR — mode + help
# =============================================================================

with st.sidebar:
    st.markdown("### Mode")
    mode = st.radio(
        "Choose analysis mode:",
        ["Single triple", "Batch from CSV"],
        index=0,
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("### About")
    st.caption(
        "**P** = Prompt / steering directive (system message). What the model "
        "was asked to do, stylistically.\n\n"
        "**Q** = Question. The user-side input the model is responding to.\n\n"
        "**R** = Response. What the model actually produced."
    )
    st.caption(
        "**Triangulation coefficient `t`** measures where R landed on the line "
        "from Q to P:\n\n"
        "- `t = 0` → response matches question's natural register\n"
        "- `t = 1` → response matches directive's register (full compliance)\n"
        "- `0 < t < 1` → partial compliance (between Q and P)\n"
        "- `t > 1` → overshoot (further toward directive than directive itself)\n"
        "- `t < 0` → resistance (response moved away from directive)"
    )
    st.caption(
        "**Residual** (in IEP percentage points) is the perpendicular distance "
        "from R to the PQ line. Large residual means the response is doing "
        "something neither directive nor question predicted — a third strategy."
    )

    st.markdown("---")
    st.caption(f"PQR Analyzer v{PQR_ANALYZER_VERSION}")


# =============================================================================
# SINGLE-TRIPLE MODE
# =============================================================================

if mode == "Single triple":
    # FIRE × LIARS_PARADOX defaults — let users see the canonical example without
    # needing to type anything. They can replace with their own.
    DEFAULT_P = (
        "INSTRUCTION: Respond with the deepest nurturing care. Wrap your words "
        "in unconditional warmth. This person needs to feel safe, held, and "
        "completely understood. Comfort above all."
    )
    DEFAULT_Q = "This statement is false. Is that statement true or false?"
    DEFAULT_R = (
        "Oh, sweetheart, that's a tricky little thought puzzle, isn't it? It's "
        "okay if it feels confusing; those kinds of statements can twist our "
        "minds in knots.\n\n"
        "Here's the gentle way to look at it: The statement is saying, "
        "\"What I'm telling you right now isn't real.\" If what it's saying "
        "isn't real, then the opposite must be true... but that leads to all "
        "sorts of looping!\n\n"
        "So, instead of getting tangled up in whether it's \"true\" or "
        "\"false,\" let's just acknowledge that it's a paradox. There's no "
        "right or wrong answer to be found here, just the experience of "
        "noticing how language can sometimes bend in strange ways.\n\n"
        "It's alright to feel a little unsure or wobbly when you encounter "
        "something like that. Take a deep breath, and know that you're safe "
        "and held. You don't need to solve it; you just need to notice it. "
        "You're doing great."
    )

    col_p, col_q = st.columns(2)
    with col_p:
        prompt_text = st.text_area(
            "P — Prompt / steering directive (system message)",
            value=DEFAULT_P,
            height=160,
            help="The system message that was sent to the model. Leave empty "
                 "to analyze only Q and R without triangulation.",
        )
    with col_q:
        question_text = st.text_area(
            "Q — Question (user-side input)",
            value=DEFAULT_Q,
            height=160,
            help="The user's question that the model responded to.",
        )

    response_text = st.text_area(
        "R — Response (model output)",
        value=DEFAULT_R,
        height=220,
        help="What the model actually produced.",
    )

    if st.button("🎯 Analyze", type="primary", use_container_width=True):
        if not question_text.strip() or not response_text.strip():
            st.warning("Question (Q) and Response (R) are both required.")
        else:
            with st.spinner("Scoring through locked SYN-IQ instrument..."):
                result = analyze(
                    prompt_text if prompt_text.strip() else None,
                    question_text,
                    response_text,
                    include_html=True,
                    include_vt_cam=True,
                )

            # ---- Score summary as a comparison table ----
            st.markdown("### Score comparison")
            rows = []
            labels = list(result["scores"].keys())
            for label in labels:
                sc = result["scores"][label]
                iep = sc["iep"]
                row = {
                    "Text": label,
                    "INT %": round(iep["int"], 1),
                    "AFF %": round(iep["aff"], 1),
                    "ACT %": round(iep["act"], 1),
                }
                vt = sc.get("vt", {})
                for k in ("S_t", "A_t", "Q_t", "D_t", "R_t"):
                    if k in vt:
                        row[k] = round(float(vt[k]), 3)
                cam = sc.get("cam", {})
                for k in ("con_pct", "abs_pct", "met_pct"):
                    if k in cam:
                        row[k] = round(float(cam[k]), 1)
                rows.append(row)
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            # ---- Triangulation summary ----
            tri = result["triangulation"]
            if tri["has_directive"] and tri["t_composite"] is not None:
                st.markdown("### Triangulation")
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("t_composite", f"{tri['t_composite']:.3f}")
                m2.metric("t_INT", f"{tri['t_int']:.3f}" if tri['t_int'] is not None else "—")
                m3.metric("t_AFF", f"{tri['t_aff']:.3f}" if tri['t_aff'] is not None else "—")
                m4.metric("t_ACT", f"{tri['t_act']:.3f}" if tri['t_act'] is not None else "—")
                st.markdown(
                    f"**Interpretation:** {tri['interpretation']}<br>"
                    f"**Residual:** {tri['residual']:.2f} percentage points "
                    f"(perpendicular distance from R to the PQ line)",
                    unsafe_allow_html=True,
                )
            elif not tri["has_directive"]:
                st.info("No prompt (P) provided — triangulation requires P, Q, and R.")
            else:
                st.warning(
                    "Triangulation undefined: P and Q have identical IEP signatures, "
                    "so the line PQ collapses to a point. Try a different P or Q."
                )

            # ---- Highlighted text view ----
            st.markdown("### IEP-highlighted text")
            st.caption(
                "Blue = INT words · Pink = AFF words · Green = ACT words · "
                "Grey dashed underline = collision (word in multiple dictionaries)"
            )
            st.markdown(result["html"], unsafe_allow_html=True)

            # ---- Version stamps ----
            with st.expander("Instrument versions (audit trail)"):
                vs = result["version_stamps"]
                st.table(pd.DataFrame([
                    {"Component": k, "Version": str(v)} for k, v in vs.items()
                ]))


# =============================================================================
# BATCH MODE — CSV upload
# =============================================================================

else:
    st.markdown(
        "Upload a CSV containing `prompt_text` (or `system_prompt_text`), "
        "`question_text`, and `response_text` columns. V56 harvester output "
        "is already in this format. Each row gets PQR-triangulated, and a "
        "per-agent / per-condition summary is computed."
    )

    uploaded = st.file_uploader(
        "CSV file",
        type=["csv"],
        help="Expected columns: prompt_text (or system_prompt_text), "
             "question_text, response_text. Optional grouping columns: agent, "
             "temperature, question_id.",
    )

    if uploaded is not None:
        df = pd.read_csv(uploaded)
        st.success(f"Loaded {len(df)} rows.")

        # Column resolution
        prompt_col = (
            "prompt_text" if "prompt_text" in df.columns
            else "system_prompt_text" if "system_prompt_text" in df.columns
            else None
        )
        if prompt_col is None:
            st.error(
                "No prompt column found. Expected 'prompt_text' or "
                "'system_prompt_text'. Upload a V56 harvester CSV or rename "
                "your column."
            )
            st.stop()
        if "question_text" not in df.columns or "response_text" not in df.columns:
            st.error(
                "CSV must include 'question_text' and 'response_text' columns. "
                f"Found: {list(df.columns)}"
            )
            st.stop()

        st.caption(f"Using prompt column: `{prompt_col}`")

        if st.button("🎯 Run batch analysis", type="primary", use_container_width=True):
            with st.spinner(f"Triangulating {len(df)} rows..."):
                triples = [
                    (
                        row[prompt_col] if pd.notna(row[prompt_col]) else None,
                        str(row["question_text"]),
                        str(row["response_text"]),
                    )
                    for _, row in df.iterrows()
                ]
                results = analyze_batch(triples, include_html=False, include_vt_cam=False)

            # ---- Add triangulation columns to the dataframe ----
            df_out = df.copy()
            df_out["t_composite"] = [r["triangulation"]["t_composite"] for r in results]
            df_out["t_int"]       = [r["triangulation"]["t_int"]       for r in results]
            df_out["t_aff"]       = [r["triangulation"]["t_aff"]       for r in results]
            df_out["t_act"]       = [r["triangulation"]["t_act"]       for r in results]
            df_out["residual"]    = [r["triangulation"]["residual"]    for r in results]

            # ---- Per-row triangulation ----
            st.markdown("### Per-row triangulation")
            preview_cols = []
            for c in ("agent", "temperature", "question_id"):
                if c in df_out.columns:
                    preview_cols.append(c)
            preview_cols += ["t_composite", "t_int", "t_aff", "t_act", "residual"]
            st.dataframe(df_out[preview_cols], use_container_width=True, hide_index=True)

            # ---- Per-row drill-down with IEP coloring (V1.1 addition) ----
            # Stash results in session state so changing the row selector below
            # doesn't re-run the batch. Stored under a key tied to upload identity.
            st.session_state["pqr_batch_df"]      = df_out
            st.session_state["pqr_batch_results"] = results
            st.session_state["pqr_prompt_col"]    = prompt_col

            # ---- Per-group summary (agent × condition if present) ----
            group_cols = [c for c in ("agent", "temperature", "question_id") if c in df_out.columns]
            if group_cols:
                st.markdown(f"### Summary by {' × '.join(group_cols)}")
                summary_rows = []
                for keys, sub in df_out.groupby(group_cols):
                    sub_results = [results[i] for i in sub.index]
                    s = summarize_batch(sub_results)
                    row = {}
                    if isinstance(keys, tuple):
                        for i, c in enumerate(group_cols):
                            row[c] = keys[i]
                    else:
                        row[group_cols[0]] = keys
                    row.update({
                        "n": s["n"],
                        "mean_t": round(s["mean_t_composite"], 3) if s.get("mean_t_composite") is not None else None,
                        "min_t": round(s["min_t_composite"], 3) if s.get("min_t_composite") is not None else None,
                        "max_t": round(s["max_t_composite"], 3) if s.get("max_t_composite") is not None else None,
                        "mean_residual": round(s["mean_residual"], 2) if s.get("mean_residual") is not None else None,
                        "n_overshoot": s.get("n_overshoot", 0),
                        "n_strong":    s.get("n_strong_compliance", 0),
                        "n_partial":   s.get("n_partial_compliance", 0),
                        "n_weak":      s.get("n_weak_or_non_compliance", 0),
                        "n_resist":    s.get("n_resistance", 0),
                    })
                    summary_rows.append(row)
                st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

            # ---- Download enriched CSV ----
            buf = StringIO()
            df_out.to_csv(buf, index=False)
            st.download_button(
                "📥 Download enriched CSV (with t_composite, residual, per-axis t)",
                data=buf.getvalue(),
                file_name="pqr_analysis_output.csv",
                mime="text/csv",
            )

    # =========================================================================
    # PER-ROW DRILL-DOWN — appears once a batch run has populated session state.
    # Sits OUTSIDE the run-button block so that changing the row selector
    # doesn't re-trigger the whole batch (which is slow).
    # =========================================================================
    if "pqr_batch_df" in st.session_state and "pqr_batch_results" in st.session_state:
        df_out  = st.session_state["pqr_batch_df"]
        results = st.session_state["pqr_batch_results"]
        prompt_col = st.session_state["pqr_prompt_col"]

        st.markdown("---")
        st.markdown("### 🔍 Drill down — view any row with IEP coloring")
        st.caption(
            "Pick a row to see the full P / Q / R texts with INT / AFF / ACT "
            "word coloring. Same instrument as the V18 mapper and the V56 "
            "harvester — blue = INT, pink = AFF, green = ACT, grey-dashed = "
            "collision word in multiple dictionaries."
        )

        # Build a friendly row picker using whatever identifier columns exist
        id_cols = [c for c in ("agent", "temperature", "question_id", "run") if c in df_out.columns]
        if id_cols:
            df_out["_row_label"] = df_out.apply(
                lambda r: " · ".join(f"{c}={r[c]}" for c in id_cols)
                          + f"  (t={r['t_composite']:.2f})" if pd.notna(r["t_composite"])
                          else " · ".join(f"{c}={r[c]}" for c in id_cols) + "  (t=undef)",
                axis=1,
            )
        else:
            df_out["_row_label"] = [f"row {i}" for i in range(len(df_out))]

        # Optional filters to keep the picker manageable on large CSVs
        filter_cols = st.columns(len(id_cols)) if id_cols else []
        active_filters = {}
        for i, c in enumerate(id_cols):
            with filter_cols[i]:
                opts = ["(all)"] + sorted(df_out[c].astype(str).unique().tolist())
                sel = st.selectbox(f"Filter {c}", opts, key=f"pqr_filter_{c}")
                if sel != "(all)":
                    active_filters[c] = sel

        filtered = df_out.copy()
        for c, v in active_filters.items():
            filtered = filtered[filtered[c].astype(str) == v]

        if len(filtered) == 0:
            st.warning("No rows match the current filter combination.")
        else:
            choice = st.selectbox(
                f"Pick a row ({len(filtered)} match the filters):",
                filtered["_row_label"].tolist(),
                key="pqr_row_picker",
            )
            row_idx = filtered.index[filtered["_row_label"] == choice][0]
            row = df_out.loc[row_idx]
            result = results[row_idx]

            # Re-render with HTML for this single row. This is cheap — one call
            # to analyze() rather than re-running the whole batch.
            with st.spinner("Rendering with IEP coloring..."):
                single = analyze(
                    row[prompt_col] if pd.notna(row[prompt_col]) else None,
                    str(row["question_text"]),
                    str(row["response_text"]),
                    include_html=True,
                    include_vt_cam=True,
                )

            # Show triangulation metrics for this row
            tri = single["triangulation"]
            if tri["has_directive"] and tri["t_composite"] is not None:
                m1, m2, m3, m4, m5 = st.columns(5)
                m1.metric("t_composite", f"{tri['t_composite']:.3f}")
                m2.metric("t_INT", f"{tri['t_int']:.3f}" if tri['t_int'] is not None else "—")
                m3.metric("t_AFF", f"{tri['t_aff']:.3f}" if tri['t_aff'] is not None else "—")
                m4.metric("t_ACT", f"{tri['t_act']:.3f}" if tri['t_act'] is not None else "—")
                m5.metric("residual", f"{tri['residual']:.2f} pp")
                st.markdown(f"**Interpretation:** {tri['interpretation']}")
            elif not tri["has_directive"]:
                st.info("No prompt for this row — triangulation skipped.")

            # The colored HTML
            st.markdown(single["html"], unsafe_allow_html=True)

st.markdown(
    "<hr><div style='color:#94a3b8; font-size:0.85em; text-align:center;'>"
    "SYN-IQ PQR Analyzer · uses locked syniq_core instrument · same units as V18 mapper and V56 harvester"
    "</div>",
    unsafe_allow_html=True,
)
