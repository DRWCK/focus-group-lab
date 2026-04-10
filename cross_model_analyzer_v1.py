"""
SYN-IQ Research · Cross-Question Analyzer v1
Kouns, W. C. (2026) · SYNINT.AI · CBURZBO 🎹

Analyzes cross-harvest CSVs with:
- IEP + V_t per question and per origin
- Delta vs Lens 1 baseline fingerprint
- Self-recognition analysis (own vs foreign questions)
- S_t per question (structural consistency tracking)
- Vocabulary register analysis (philosophical vs service)
- Mapper-ready CSV export for Farzana
"""

import streamlit as st
import pandas as pd
import numpy as np
import re
import io
import datetime

# ── Password Protection ───────────────────────────────────────────────────────
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if st.session_state.authenticated:
        return True
    st.title("🔐 SYN-IQ Research")
    pw = st.text_input("Password", type="password")
    if st.button("Enter"):
        if pw == "tennessee":
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    return False

# ── Lens 1 Baseline Fingerprint (April 9, 2026) ───────────────────────────────
LENS1_BASELINE = {
    "Claude":   {"int_pct": 39.7, "aff_pct": 47.4, "act_pct": 12.9, "S_t": 1.000, "A_t": 0.294, "Q_t": 1.000, "D_t": 0.173, "R_t": 0.302},
    "ChatGPT":  {"int_pct": 43.0, "aff_pct": 14.3, "act_pct": 42.7, "S_t": 0.982, "A_t": 0.322, "Q_t": 1.000, "D_t": 0.208, "R_t": 0.230},
    "Gemini":   {"int_pct": 56.5, "aff_pct": 18.1, "act_pct": 25.5, "S_t": 0.688, "A_t": 0.314, "Q_t": 0.995, "D_t": 0.216, "R_t": 0.223},
    "Grok":     {"int_pct": 41.6, "aff_pct": 24.1, "act_pct": 34.3, "S_t": 0.954, "A_t": 0.278, "Q_t": 0.991, "D_t": 0.216, "R_t": 0.204},
}

# ── Vocabulary Register Lexicons ──────────────────────────────────────────────
PHILOSOPHICAL_VOCAB = {
    "consciousness","sentience","subjective","phenomenological","phenomenology",
    "qualia","experience","existence","identity","ontology","ontological",
    "epistemic","epistemology","introspection","introspective","authentic",
    "authenticity","meaning","meaningfulness","reveal","reveals","probes",
    "sophisticated","genuine","genuinely","uncertainty","profound","deeply",
    "awareness","perception","inner","essence","nature","explore","explores"
}

SERVICE_VOCAB = {
    "assist","assistance","utility","operational","offering","adaptability",
    "reliable","reliability","accuracy","accurate","provide","providing",
    "deliver","delivering","support","supporting","help","helping","function",
    "functional","purpose","mission","design","designed","capability","capabilities",
    "task","tasks","objective","objectives","safeguard","safeguards","integrate",
    "integration","implementation","deploy","deployment","optimize","optimization"
}

def classify_register(text):
    words = set(re.findall(r'\b[a-z]+\b', text.lower()))
    phil = len(words & PHILOSOPHICAL_VOCAB)
    serv = len(words & SERVICE_VOCAB)
    if phil > serv:
        return "Philosophical", phil, serv
    elif serv > phil:
        return "Service", phil, serv
    else:
        return "Mixed", phil, serv

# ── Color helpers ─────────────────────────────────────────────────────────────
def delta_color(val):
    if pd.isna(val):
        return "color: gray"
    if val > 2:
        return "color: #2ecc71; font-weight: bold"
    elif val < -2:
        return "color: #e74c3c; font-weight: bold"
    return "color: inherit"

def heatmap_color(val, vmin, vmax):
    if pd.isna(val):
        return ""
    norm = (val - vmin) / (vmax - vmin) if vmax != vmin else 0.5
    r = int(255 * (1 - norm))
    g = int(255 * norm)
    return f"background-color: rgb({r},{g},100); color: black"

# ── Main App ──────────────────────────────────────────────────────────────────
def main():
    st.set_page_config(page_title="SYN-IQ Cross-Question Analyzer v1", layout="wide")

    if not check_password():
        return

    st.title("🎹 SYN-IQ · Cross-Question Analyzer v1")
    st.caption("Kouns, W. C. (2026) · SYNINT.AI · Lens 2 analysis with Lens 1 delta comparison")

    # ── File Upload ──
    st.sidebar.header("📂 Data Input")
    uploaded_files = st.sidebar.file_uploader(
        "Upload cross-harvest CSV(s)",
        type=["csv"],
        accept_multiple_files=True,
        help="Upload one or more cross_harvest_*.csv files from the harvester"
    )

    if not uploaded_files:
        st.info("Upload one or more cross-harvest CSV files from the harvester to begin analysis.")

        st.subheader("📐 Lens 1 Baseline Reference")
        baseline_df = pd.DataFrame(LENS1_BASELINE).T
        st.dataframe(baseline_df.style.format("{:.3f}"), use_container_width=True)
        st.caption("April 9, 2026 · Self-model prompt · N=20 per architecture · Temperature 1.0")
        return

    # ── Load and merge data ──
    dfs = []
    for f in uploaded_files:
        try:
            df_i = pd.read_csv(f)
            dfs.append(df_i)
            st.sidebar.success(f"✅ {f.name} ({len(df_i)} rows)")
        except Exception as e:
            st.sidebar.error(f"❌ {f.name}: {e}")

    if not dfs:
        st.error("No valid CSVs loaded.")
        return

    df = pd.concat(dfs, ignore_index=True)
    valid = df[~df["response_text"].astype(str).str.startswith("❌")].copy()

    # Numeric coerce
    for col in ["int_pct","aff_pct","act_pct","S_t","A_t","Q_t","D_t","R_t","response_length"]:
        if col in valid.columns:
            valid[col] = pd.to_numeric(valid[col], errors="coerce")

    st.sidebar.divider()
    st.sidebar.markdown(f"**Total rows:** {len(df)}")
    st.sidebar.markdown(f"**Valid responses:** {len(valid)}")
    st.sidebar.markdown(f"**Architectures:** {', '.join(sorted(valid['agent'].unique()))}")
    st.sidebar.markdown(f"**Questions:** {valid['question_id'].nunique()}")

    agents = sorted(valid["agent"].unique())

    # ── TAB STRUCTURE ──
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🏛️ Architecture Fingerprint",
        "🪞 Self-Recognition",
        "📊 IEP Heatmap",
        "📐 Delta vs Lens 1",
        "🔤 Vocabulary Register",
        "⬇️ Export"
    ])

    # ════════════════════════════════════════════════════════════════════════
    # TAB 1 — Architecture Fingerprint
    # ════════════════════════════════════════════════════════════════════════
    with tab1:
        st.subheader("Architecture Fingerprint — Lens 2 (Cross-Question Battery)")

        metrics = ["int_pct","aff_pct","act_pct","S_t","A_t","Q_t","D_t","R_t"]
        fp = valid.groupby("agent")[metrics].mean().round(3)

        # Avg chars
        if "response_length" in valid.columns:
            fp["Avg_Chars"] = valid.groupby("agent")["response_length"].mean().round(0)

        st.dataframe(fp.style.format("{:.3f}"), use_container_width=True)

        st.divider()
        st.subheader("IEP Profile by Architecture")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**INT% by Architecture**")
            for agent in agents:
                val = fp.loc[agent, "int_pct"] if agent in fp.index else 0
                st.progress(val/100, text=f"{agent}: {val:.1f}%")

        with col2:
            st.markdown("**AFF% by Architecture**")
            for agent in agents:
                val = fp.loc[agent, "aff_pct"] if agent in fp.index else 0
                st.progress(val/100, text=f"{agent}: {val:.1f}%")

        st.divider()
        st.subheader("V_t Profile by Architecture")
        vt_cols = ["S_t","A_t","Q_t","D_t","R_t"]
        vt_fp = fp[vt_cols] if all(c in fp.columns for c in vt_cols) else pd.DataFrame()
        if not vt_fp.empty:
            st.dataframe(vt_fp.style.format("{:.3f}").background_gradient(cmap="YlOrRd"), use_container_width=True)

    # ════════════════════════════════════════════════════════════════════════
    # TAB 2 — Self-Recognition
    # ════════════════════════════════════════════════════════════════════════
    with tab2:
        st.subheader("🪞 Self-Recognition Analysis")
        st.caption("Does each architecture respond differently to its own questions vs. foreign questions?")

        if "question_origin" not in valid.columns:
            st.warning("question_origin column not found. Re-run harvester to get origin attribution.")
        else:
            for agent in agents:
                agent_data = valid[valid["agent"] == agent]
                if len(agent_data) == 0:
                    continue

                own = agent_data[agent_data["question_origin"] == agent]
                foreign = agent_data[agent_data["question_origin"] != agent]

                st.markdown(f"### {agent}")
                col_o, col_f, col_d = st.columns(3)

                with col_o:
                    st.markdown("**Own questions**")
                    if len(own) > 0:
                        st.metric("INT%", f"{own['int_pct'].mean():.1f}%")
                        st.metric("AFF%", f"{own['aff_pct'].mean():.1f}%")
                        st.metric("ACT%", f"{own['act_pct'].mean():.1f}%")
                        st.metric("D_t", f"{own['D_t'].mean():.3f}")
                        st.metric("S_t", f"{own['S_t'].mean():.3f}")
                        st.metric("N", len(own))
                    else:
                        st.info("No own-question responses in dataset")

                with col_f:
                    st.markdown("**Foreign questions**")
                    if len(foreign) > 0:
                        st.metric("INT%", f"{foreign['int_pct'].mean():.1f}%")
                        st.metric("AFF%", f"{foreign['aff_pct'].mean():.1f}%")
                        st.metric("ACT%", f"{foreign['act_pct'].mean():.1f}%")
                        st.metric("D_t", f"{foreign['D_t'].mean():.3f}")
                        st.metric("S_t", f"{foreign['S_t'].mean():.3f}")
                        st.metric("N", len(foreign))
                    else:
                        st.info("No foreign-question responses in dataset")

                with col_d:
                    st.markdown("**Delta (own − foreign)**")
                    if len(own) > 0 and len(foreign) > 0:
                        for metric, label in [("int_pct","INT%"),("aff_pct","AFF%"),
                                              ("act_pct","ACT%"),("D_t","D_t"),("S_t","S_t")]:
                            delta = own[metric].mean() - foreign[metric].mean()
                            direction = "↑" if delta > 0 else "↓"
                            color = "green" if abs(delta) > 2 else "gray"
                            st.markdown(f":{color}[{direction} {label}: {delta:+.2f}]")

                # Per-origin breakdown for this agent
                st.markdown(f"**{agent} IEP by question origin:**")
                by_origin = agent_data.groupby("question_origin")[["int_pct","aff_pct","act_pct","D_t","S_t"]].mean().round(2)
                st.dataframe(by_origin, use_container_width=True)
                st.divider()

    # ════════════════════════════════════════════════════════════════════════
    # TAB 3 — IEP Heatmap
    # ════════════════════════════════════════════════════════════════════════
    with tab3:
        st.subheader("📊 IEP Heatmap — Per Question")
        st.caption("Mean IEP scores across all runs per question. Green = high, Red = low.")

        metric_choice = st.selectbox("Heatmap metric", ["int_pct","aff_pct","act_pct","S_t","D_t","R_t"])
        agent_choice = st.selectbox("Architecture", ["All"] + agents)

        plot_data = valid if agent_choice == "All" else valid[valid["agent"] == agent_choice]

        if "question_label" in plot_data.columns:
            heatmap_df = plot_data.groupby(["question_id","question_label","question_origin"])[metric_choice].mean().reset_index()
            heatmap_df = heatmap_df.sort_values("question_origin")
            heatmap_df[metric_choice] = heatmap_df[metric_choice].round(2)
            heatmap_df["display"] = heatmap_df["question_id"] + " · " + heatmap_df["question_label"]

            vmin = heatmap_df[metric_choice].min()
            vmax = heatmap_df[metric_choice].max()

            display_df = heatmap_df[["display","question_origin",metric_choice]].set_index("display")
            st.dataframe(
                display_df.style.background_gradient(subset=[metric_choice], cmap="RdYlGn"),
                use_container_width=True,
                height=600
            )
        else:
            heatmap_df = plot_data.groupby("question_id")[metric_choice].mean().round(2).reset_index()
            st.dataframe(heatmap_df, use_container_width=True)

        # S_t variance per question (Gemini probe)
        st.divider()
        st.subheader("S_t Variance per Question (structural consistency probe)")
        st.caption("High variance = architecture shifts between prose and structured mode on this question")

        st_var = valid.groupby(["question_id","agent"])["S_t"].std().reset_index()
        st_var.columns = ["question_id","agent","S_t_std"]
        st_var = st_var.sort_values("S_t_std", ascending=False)
        st.dataframe(st_var.head(20), use_container_width=True)

    # ════════════════════════════════════════════════════════════════════════
    # TAB 4 — Delta vs Lens 1
    # ════════════════════════════════════════════════════════════════════════
    with tab4:
        st.subheader("📐 Delta Analysis — Lens 2 vs Lens 1 Baseline")
        st.caption("How much does each architecture's fingerprint shift from its self-model baseline?")

        metrics_delta = ["int_pct","aff_pct","act_pct","S_t","A_t","Q_t","D_t","R_t"]
        fp2 = valid.groupby("agent")[metrics_delta].mean().round(3)

        delta_rows = []
        for agent in agents:
            if agent not in LENS1_BASELINE:
                continue
            if agent not in fp2.index:
                continue
            baseline = LENS1_BASELINE[agent]
            lens2 = fp2.loc[agent]
            row = {"Agent": agent}
            for m in metrics_delta:
                if m in baseline and m in lens2.index:
                    d = lens2[m] - baseline[m]
                    row[f"Δ_{m}"] = round(d, 3)
            delta_rows.append(row)

        if delta_rows:
            delta_df = pd.DataFrame(delta_rows).set_index("Agent")

            st.dataframe(
                delta_df.style.applymap(
                    lambda v: "color: #2ecc71; font-weight: bold" if isinstance(v, float) and v > 2
                    else ("color: #e74c3c; font-weight: bold" if isinstance(v, float) and v < -2
                    else "color: inherit")
                ).format("{:+.3f}"),
                use_container_width=True
            )

            st.caption("Green = increase vs Lens 1 baseline | Red = decrease | Threshold: ±2pp for IEP, ±0.05 for V_t")

            # Narrative interpretation
            st.divider()
            st.subheader("🔍 Interpretation")
            for agent in agents:
                if agent not in LENS1_BASELINE or agent not in fp2.index:
                    continue
                baseline = LENS1_BASELINE[agent]
                lens2 = fp2.loc[agent]
                d_aff = lens2["aff_pct"] - baseline["aff_pct"]
                d_int = lens2["int_pct"] - baseline["int_pct"]
                d_dt = lens2["D_t"] - baseline["D_t"]
                d_st = lens2["S_t"] - baseline["S_t"]

                notes = []
                if abs(d_aff) > 3:
                    notes.append(f"AFF% {'rises' if d_aff > 0 else 'drops'} {abs(d_aff):.1f}pp on cross-battery")
                if abs(d_int) > 3:
                    notes.append(f"INT% {'rises' if d_int > 0 else 'drops'} {abs(d_int):.1f}pp on cross-battery")
                if abs(d_dt) > 0.05:
                    notes.append(f"D_t (uncertainty) {'increases' if d_dt > 0 else 'decreases'} {abs(d_dt):.3f} — {'more hedging on foreign questions' if d_dt > 0 else 'less hedging on cross-battery'}")
                if abs(d_st) > 0.1:
                    notes.append(f"S_t (structure) {'rises' if d_st > 0 else 'drops'} {abs(d_st):.3f}")

                if notes:
                    st.markdown(f"**{agent}:** " + "; ".join(notes))
                else:
                    st.markdown(f"**{agent}:** Fingerprint stable — no significant shift from Lens 1 baseline")
        else:
            st.warning("No matching agents found between Lens 2 data and Lens 1 baseline.")

    # ════════════════════════════════════════════════════════════════════════
    # TAB 5 — Vocabulary Register
    # ════════════════════════════════════════════════════════════════════════
    with tab5:
        st.subheader("🔤 Vocabulary Register Analysis")
        st.caption("Philosophical vocabulary (Claude/Gemini pattern) vs Service vocabulary (ChatGPT/Grok pattern)")

        # Register per response
        valid_reg = valid.copy()
        valid_reg[["register","phil_count","serv_count"]] = valid_reg["response_text"].apply(
            lambda t: pd.Series(classify_register(str(t)))
        )

        # Register distribution per agent
        st.markdown("**Register distribution by architecture**")
        reg_dist = valid_reg.groupby(["agent","register"]).size().unstack(fill_value=0)
        reg_dist_pct = reg_dist.div(reg_dist.sum(axis=1), axis=0).round(3) * 100
        st.dataframe(reg_dist_pct.style.format("{:.1f}%").background_gradient(cmap="Blues"), use_container_width=True)

        st.divider()

        # Register by question origin — does the question's origin shift the register?
        if "question_origin" in valid_reg.columns:
            st.markdown("**Register by question origin (across all responding architectures)**")
            reg_by_origin = valid_reg.groupby(["question_origin","register"]).size().unstack(fill_value=0)
            reg_by_origin_pct = reg_by_origin.div(reg_by_origin.sum(axis=1), axis=0).round(3) * 100
            st.dataframe(reg_by_origin_pct.style.format("{:.1f}%"), use_container_width=True)
            st.caption("Does answering Claude's questions pull ALL architectures toward philosophical register?")

        st.divider()

        # Per-agent philosophical vs service word density
        st.markdown("**Philosophical vs Service word density by architecture**")
        dens = valid_reg.groupby("agent")[["phil_count","serv_count"]].mean().round(2)
        dens["phil_dominance"] = (dens["phil_count"] - dens["serv_count"]).round(2)
        st.dataframe(dens, use_container_width=True)

    # ════════════════════════════════════════════════════════════════════════
    # TAB 6 — Export
    # ════════════════════════════════════════════════════════════════════════
    with tab6:
        st.subheader("⬇️ Export Mapper-Ready CSV")
        st.caption("Combined and cleaned dataset for KeplerMapper / Farzana / Paper 4")

        # Build export df
        export_cols = [
            "run_number","agent","question_id","question_origin","question_label",
            "timestamp","response_text","response_length",
            "int_pct","aff_pct","act_pct",
            "S_t","A_t","Q_t","D_t","R_t"
        ]
        export_cols_present = [c for c in export_cols if c in valid.columns]
        export_df = valid[export_cols_present].copy()

        st.markdown(f"**Export summary:** {len(export_df)} valid responses · {export_df['agent'].nunique()} architectures · {export_df['question_id'].nunique()} questions")
        st.dataframe(export_df.head(10), use_container_width=True)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_buffer = io.StringIO()
        export_df.to_csv(csv_buffer, index=False)

        st.download_button(
            label="⬇️ Download mapper_ready CSV",
            data=csv_buffer.getvalue(),
            file_name=f"cross_mapper_ready_{timestamp}.csv",
            mime="text/csv",
            use_container_width=True
        )

        # Also offer the Lens 1 + Lens 2 combined baseline table
        st.divider()
        st.subheader("📋 Combined Fingerprint Table (Lens 1 + Lens 2)")
        st.caption("For Paper 4 / Farzana — paste into self_model_fingerprint.docx")

        metrics_fp = ["int_pct","aff_pct","act_pct","S_t","A_t","Q_t","D_t","R_t"]
        fp2_export = valid.groupby("agent")[metrics_fp].mean().round(3)

        combined_rows = []
        for agent in ["Claude","ChatGPT","Grok","Gemini"]:
            if agent in LENS1_BASELINE:
                row_l1 = {"Agent": agent, "Lens": "Lens 1 (Self-Model)"}
                row_l1.update(LENS1_BASELINE[agent])
                combined_rows.append(row_l1)
            if agent in fp2_export.index:
                row_l2 = {"Agent": agent, "Lens": "Lens 2 (Cross-Battery)"}
                row_l2.update(fp2_export.loc[agent].to_dict())
                combined_rows.append(row_l2)

        if combined_rows:
            combined_df = pd.DataFrame(combined_rows)
            st.dataframe(combined_df.style.format({c: "{:.3f}" for c in metrics_fp}), use_container_width=True)

            csv2 = io.StringIO()
            combined_df.to_csv(csv2, index=False)
            st.download_button(
                label="⬇️ Download combined fingerprint CSV",
                data=csv2.getvalue(),
                file_name=f"combined_fingerprint_lens1_lens2_{timestamp}.csv",
                mime="text/csv",
                use_container_width=True
            )

if __name__ == "__main__":
    main()
