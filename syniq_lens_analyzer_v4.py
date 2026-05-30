"""
SYN-IQ · Vₜ Lens Analyzer v4
Kouns, W. C. (2026) · SYNINT.AI · CBURZBO 🎹

Multi-CSV lens comparison tool for IEP + Vₜ topological analysis.
Designed for COLD vs FIRE (and any condition) cross-framework validation.
Claude API interprets topology findings for publication-ready narrative.
"""

import streamlit as st
import pandas as pd
import numpy as np
import io
import datetime
import itertools

st.set_page_config(
    page_title="SYN-IQ · Vₜ Lens Analyzer v4",
    page_icon="🔬",
    layout="wide"
)

# ── Styles ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;600&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

.hero {
    background: linear-gradient(135deg, #0d0d1a 0%, #0f1f3d 50%, #0a1628 100%);
    border: 1px solid #1e3a5f;
    border-radius: 12px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
}
.hero h1 { color: #e8f4fd; font-size: 1.8rem; font-weight: 600; margin: 0 0 0.3rem 0; font-family: 'DM Mono', monospace; }
.hero p  { color: #7fb3d3; margin: 0; font-size: 0.9rem; }

.lens-card {
    background: #0f1923;
    border: 1px solid #1e3a5f;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.5rem;
}
.lens-card h4 { color: #7fb3d3; font-family: 'DM Mono', monospace; font-size: 0.85rem; margin: 0 0 0.5rem 0; letter-spacing: 0.05em; }

.stat-chip {
    display: inline-block;
    background: #1a2f4a;
    color: #a8d4f0;
    border-radius: 4px;
    padding: 2px 8px;
    font-family: 'DM Mono', monospace;
    font-size: 0.78rem;
    margin: 2px;
}

.claude-box {
    background: linear-gradient(135deg, #0d1f0d, #0a1f2e);
    border: 1px solid #2d5a27;
    border-left: 4px solid #4caf50;
    border-radius: 8px;
    padding: 1.5rem;
    margin-top: 1rem;
    color: #c8e6c9;
    font-size: 0.92rem;
    line-height: 1.7;
    white-space: pre-wrap;
}
.claude-box .label {
    font-family: 'DM Mono', monospace;
    font-size: 0.75rem;
    color: #4caf50;
    letter-spacing: 0.1em;
    margin-bottom: 0.8rem;
}

.cond-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 0.78rem;
    font-family: 'DM Mono', monospace;
    font-weight: 500;
    margin-right: 4px;
}
.badge-NATIVE  { background: #2d2d44; color: #aaaacc; }
.badge-COLD    { background: #1e3a5f; color: #7fb3d3; }
.badge-HOT     { background: #4a2020; color: #ff9999; }
.badge-FIRE    { background: #5a1a00; color: #ff6622; }
.badge-OTHER   { background: #2d3a2d; color: #88bb88; }

.section-head {
    font-family: 'DM Mono', monospace;
    font-size: 0.75rem;
    letter-spacing: 0.15em;
    color: #4a7fa5;
    text-transform: uppercase;
    border-bottom: 1px solid #1e3a5f;
    padding-bottom: 0.4rem;
    margin: 1.5rem 0 1rem 0;
}
</style>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <h1>🔬 SYN-IQ · Vₜ Lens Analyzer v4</h1>
    <p>Multi-condition CSV upload · IEP + Vₜ lens projection · Claude API topology interpretation</p>
    <p style="margin-top:0.4rem; color:#4a7fa5; font-size:0.8rem;">Kouns, W. C. (2026) · SYNINT.AI · CBURZBO 🎹 · Nasrin & Farzana Cross-Framework Validation</p>
</div>
""", unsafe_allow_html=True)

# ── Password ──────────────────────────────────────────────────────────────────
def check_password():
    if st.session_state.get("authenticated"):
        return True
    pw = st.text_input("Password", type="password", key="pw_input")
    if st.button("Enter"):
        if pw == "tennessee":
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    return False

if not check_password():
    st.stop()

# ── Lens definitions ──────────────────────────────────────────────────────────
IEP_LENSES_1D = ["int_pct", "aff_pct", "act_pct"]
VT_LENSES_1D  = ["S_t", "A_t", "Q_t", "D_t", "R_t"]
ALL_1D = IEP_LENSES_1D + VT_LENSES_1D

# Cross-IEP 2D pairs — all three, always valid on IEP-only data
IEP_LENSES_2D = [
    ("int_pct", "aff_pct"),
    ("int_pct", "act_pct"),
    ("aff_pct", "act_pct"),
]
# Vt 2D pairs — optional; skipped automatically when Vt columns are absent
VT_LENSES_2D = [
    ("S_t", "R_t"),
    ("A_t", "R_t"),
    ("Q_t", "D_t"),
    ("S_t", "A_t"),
    ("int_pct", "S_t"),
    ("aff_pct", "A_t"),
]
ALL_2D = IEP_LENSES_2D + VT_LENSES_2D

LENS_DESCRIPTIONS = {
    "int_pct":    "Intellectual % — formal reasoning density",
    "aff_pct":    "Affective % — emotional language density",
    "act_pct":    "Action % — practical/directive language",
    "(int_pct, act_pct)": "Cross-IEP: reasoning vs directive axis",
    "S_t":        "Structural consistency — headers/bullets/numbering",
    "A_t":        "Affective loading — AFF word density (Vₜ)",
    "Q_t":        "Question density — interrogative sentence ratio",
    "D_t":        "Uncertainty/hedge density — epistemic hedging",
    "R_t":        "Response length — normalized to 3000 chars",
}

CONDITION_COLORS = {
    "NATIVE": "#aaaacc", "COLD": "#7fb3d3",
    "HOT": "#ff9999",    "FIRE": "#ff6622",
}

def badge(cond):
    cls = f"badge-{cond}" if cond in ["NATIVE","COLD","HOT","FIRE"] else "badge-OTHER"
    return f'<span class="cond-badge {cls}">{cond}</span>'

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📁 Upload CSVs")
    st.caption("Drop in any harvester CSVs — condition auto-detected from filename or column.")
    uploaded = st.file_uploader(
        "Upload one or more CSV files",
        type="csv",
        accept_multiple_files=True,
        label_visibility="collapsed"
    )

    st.divider()
    st.markdown("### 🔭 Lens Selection")

    st.markdown("**IEP Lenses (1D)**")
    sel_iep = {}
    for l in IEP_LENSES_1D:
        sel_iep[l] = st.checkbox(l, value=True, key=f"iep_{l}")

    st.markdown("**Vₜ Lenses (1D)**")
    sel_vt = {}
    for l in VT_LENSES_1D:
        default = l in ["S_t", "R_t", "D_t"]
        sel_vt[l] = st.checkbox(l, value=default, key=f"vt_{l}")

    st.markdown("**2D Lens Pairs**")
    sel_2d = {}
    for pair in ALL_2D:
        label = f"{pair[0]} × {pair[1]}"
        default = pair in IEP_LENSES_2D or pair in [("S_t","R_t"),("Q_t","D_t"),("A_t","R_t")]
        sel_2d[pair] = st.checkbox(label, value=default, key=f"2d_{label}")

    st.divider()
    st.markdown("### 🤖 Claude Analysis")
    run_claude = st.checkbox("Run Claude API interpretation", value=True)
    focus_pair = st.selectbox(
        "Primary contrast for Claude",
        ["COLD vs FIRE", "NATIVE vs FIRE", "COLD vs HOT", "NATIVE vs COLD", "All conditions"],
        index=0
    )

# ── Load and merge CSVs ───────────────────────────────────────────────────────
# Hard requirement: IEP only. Vt columns are optional — when absent, the
# Vt lenses simply don't appear (the 1D/2D loops already skip missing cols).
REQUIRED_COLS = {"int_pct", "aff_pct", "act_pct"}
OPTIONAL_COLS = {"S_t", "A_t", "Q_t", "D_t", "R_t"}

@st.cache_data
def load_csvs(files):
    frames = []
    for f in files:
        try:
            df = pd.read_csv(f)
            # Auto-detect condition from filename if column missing/all-same
            fname = f.name.lower()
            if "condition" not in df.columns:
                for c in ["fire","cold","hot","native"]:
                    if c in fname:
                        df["condition"] = c.upper()
                        break
                else:
                    df["condition"] = "UNKNOWN"
            frames.append(df)
        except Exception as e:
            st.warning(f"Could not load {f.name}: {e}")
    if frames:
        return pd.concat(frames, ignore_index=True)
    return None

if not uploaded:
    st.info("👈 Upload one or more harvester CSVs from the sidebar to begin.")
    st.stop()

df_raw = load_csvs(uploaded)
if df_raw is None or df_raw.empty:
    st.error("No valid data loaded.")
    st.stop()

missing = REQUIRED_COLS - set(df_raw.columns)
if missing:
    st.error(f"Missing required columns: {missing}")
    st.stop()

# Drop error rows
df = df_raw[~df_raw["response_text"].astype(str).str.startswith("❌", na=False)].copy()
# Drop rows missing the IEP core only. Dropping on Vt would delete every
# row of an IEP-only (native) file, since those columns are all-NaN there.
_dropna_cols = [c for c in REQUIRED_COLS if c in df.columns]
df = df.dropna(subset=_dropna_cols)

conditions = sorted(df["condition"].unique().tolist())
agents     = sorted(df["agent"].unique().tolist()) if "agent" in df.columns else []

# ── Dataset overview ──────────────────────────────────────────────────────────
st.markdown('<div class="section-head">Dataset Overview</div>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total responses", len(df))
col2.metric("Conditions", len(conditions))
col3.metric("Agents", len(agents) if agents else "—")
col4.metric("Questions", df["question_id"].nunique() if "question_id" in df.columns else "—")

st.markdown("**Conditions loaded:** " + " ".join(badge(c) for c in conditions), unsafe_allow_html=True)
if agents:
    st.markdown(f"**Agents:** {', '.join(agents)}")

# ── Per-condition summary ─────────────────────────────────────────────────────
st.markdown('<div class="section-head">Condition Profiles</div>', unsafe_allow_html=True)

profile_rows = []
for cond in conditions:
    sub = df[df["condition"] == cond]
    row = {"Condition": cond, "N": len(sub)}
    for col in ALL_1D:
        if col in sub.columns:
            row[col] = round(sub[col].mean(), 3)
    profile_rows.append(row)

profile_df = pd.DataFrame(profile_rows).set_index("Condition")
st.dataframe(profile_df.style.format("{:.3f}", subset=[c for c in ALL_1D if c in profile_df.columns]),
             use_container_width=True)

# ── 1D Lens Analysis ──────────────────────────────────────────────────────────
active_1d = [l for l, v in {**sel_iep, **sel_vt}.items() if v]

if active_1d:
    st.markdown('<div class="section-head">1D Lens Projections</div>', unsafe_allow_html=True)
    st.caption("Mean ± std per condition. Farzana's prediction: S_t and R_t show strongest COLD→FIRE separation.")

    lens_rows = []
    for lens in active_1d:
        if lens not in df.columns:
            continue
        row = {"Lens": lens, "Description": LENS_DESCRIPTIONS.get(lens, "")}
        cond_data = {}
        for cond in conditions:
            sub = df[df["condition"] == cond][lens].dropna()
            row[f"{cond} mean"] = round(sub.mean(), 3)
            row[f"{cond} std"]  = round(sub.std(), 3)
            cond_data[cond] = sub

        # Max separation (raw mean difference)
        means = [cond_data[c].mean() for c in conditions if len(cond_data.get(c, [])) > 0]
        row["Max separation"] = round(max(means) - min(means), 3) if len(means) > 1 else 0.0

        # Cohen's d — effect size for the largest pairwise contrast
        best_d = 0.0
        best_pair = ""
        for (ca, cb) in itertools.combinations(conditions, 2):
            a = cond_data.get(ca, pd.Series(dtype=float))
            b = cond_data.get(cb, pd.Series(dtype=float))
            if len(a) < 2 or len(b) < 2:
                continue
            mean_diff = abs(a.mean() - b.mean())
            pooled_sd = np.sqrt(((len(a)-1)*a.var() + (len(b)-1)*b.var()) / (len(a)+len(b)-2))
            if pooled_sd > 0:
                d = round(mean_diff / pooled_sd, 3)
                if d > best_d:
                    best_d = d
                    best_pair = f"{ca}↔{cb}"
        row["Cohen's d"] = best_d
        row["Best contrast"] = best_pair

        lens_rows.append(row)

    lens_df = pd.DataFrame(lens_rows)
    st.dataframe(lens_df.sort_values("Cohen's d", ascending=False), use_container_width=True, hide_index=True)
    st.caption("Cohen's d: 0.2 = small · 0.5 = medium · 0.8 = large · >1.0 = very large effect")

# ── 2D Lens Analysis ──────────────────────────────────────────────────────────
active_2d = [pair for pair, v in sel_2d.items() if v]

if active_2d:
    st.markdown('<div class="section-head">2D Lens Pairs — Topological Contrast</div>', unsafe_allow_html=True)
    st.caption("Centroid distance between conditions in each 2D lens space. Higher = stronger topological separation.")

    pair_rows = []
    for pair in active_2d:
        c1, c2 = pair
        if c1 not in df.columns or c2 not in df.columns:
            continue
        row = {"Lens pair": f"{c1} × {c2}"}
        centroids = {}
        for cond in conditions:
            sub = df[df["condition"] == cond][[c1, c2]].dropna()
            if len(sub) > 0:
                centroids[cond] = (sub[c1].mean(), sub[c2].mean())
                row[f"{cond} ({c1[:3]},{c2[:3]})"] = f"({sub[c1].mean():.3f}, {sub[c2].mean():.3f})"

        # Pairwise centroid distances
        if len(centroids) >= 2:
            dists = []
            for (ca, va), (cb, vb) in itertools.combinations(centroids.items(), 2):
                d = np.sqrt((va[0]-vb[0])**2 + (va[1]-vb[1])**2)
                row[f"{ca}↔{cb}"] = round(d, 4)
                dists.append(d)
            row["Max distance"] = round(max(dists), 4)
        pair_rows.append(row)

    if pair_rows:
        pair_df = pd.DataFrame(pair_rows)
        if "Max distance" in pair_df.columns:
            pair_df = pair_df.sort_values("Max distance", ascending=False)
        else:
            st.caption("Single condition loaded — centroid distances need ≥2 conditions to compare.")
        st.dataframe(pair_df, use_container_width=True, hide_index=True)

# ── Agent breakdown ───────────────────────────────────────────────────────────
if agents and len(agents) > 1:
    st.markdown('<div class="section-head">Agent × Condition Breakdown</div>', unsafe_allow_html=True)
    breakdown_rows = []
    for agent in agents:
        for cond in conditions:
            sub = df[(df["agent"]==agent) & (df["condition"]==cond)]
            if len(sub) == 0:
                continue
            brow = {
                "Agent": agent, "Condition": cond, "N": len(sub),
                "INT%": round(sub["int_pct"].mean(), 1),
                "AFF%": round(sub["aff_pct"].mean(), 1),
                "ACT%": round(sub["act_pct"].mean(), 1),
            }
            for vt in ("S_t", "A_t", "Q_t", "D_t", "R_t"):
                if vt in sub.columns and sub[vt].notna().any():
                    brow[vt] = round(sub[vt].mean(), 3)
            breakdown_rows.append(brow)
    if breakdown_rows:
        st.dataframe(pd.DataFrame(breakdown_rows), use_container_width=True, hide_index=True)

# ── Mapper-ready CSV exports ──────────────────────────────────────────────────
st.markdown('<div class="section-head">Mapper-Ready Exports</div>', unsafe_allow_html=True)
st.caption("One CSV per active lens — drop directly into KeplerMapper.")

export_cols_base = ["agent","condition","question_id","question_origin",
                    "question_label","int_pct","aff_pct","act_pct",
                    "S_t","A_t","Q_t","D_t","R_t","response_text"]
export_cols = [c for c in export_cols_base if c in df.columns]

ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

# Full merged export
buf = io.StringIO()
df[export_cols].to_csv(buf, index=False)
st.download_button(
    "⬇️ Full merged CSV (all conditions, all lenses)",
    buf.getvalue(),
    f"syniq_lens_full_{ts}.csv",
    "text/csv",
    use_container_width=True
)

# Per-lens exports
lens_export_cols = {}
for lens in active_1d:
    if lens in df.columns:
        cols = [c for c in export_cols if c in df.columns] + [lens] if lens not in export_cols else export_cols
        buf2 = io.StringIO()
        df[list(dict.fromkeys(cols))].to_csv(buf2, index=False)
        st.download_button(
            f"⬇️ Lens: {lens}",
            buf2.getvalue(),
            f"syniq_lens_{lens}_{ts}.csv",
            "text/csv",
        )

# ── Claude API Interpretation ─────────────────────────────────────────────────
st.markdown('<div class="section-head">Claude API · Topology Interpretation</div>', unsafe_allow_html=True)

if not run_claude:
    st.info("Enable 'Run Claude API interpretation' in the sidebar to generate narrative analysis.")
else:
    if st.button("🤖 Generate Claude Interpretation", type="primary", use_container_width=True):

        # Build a rich data summary for Claude
        summary_lines = [
            f"DATASET: {len(df)} responses · Conditions: {', '.join(conditions)} · Agents: {', '.join(agents) if agents else 'unknown'}",
            "",
            "CONDITION PROFILES (mean IEP + Vₜ scores):",
        ]
        for row in profile_rows:
            cond = row["Condition"]
            summary_lines.append(
                f"  {cond} (N={row['N']}): INT={row.get('int_pct','?'):.3f} AFF={row.get('aff_pct','?'):.3f} ACT={row.get('act_pct','?'):.3f} | "
                f"S_t={row.get('S_t','?'):.3f} A_t={row.get('A_t','?'):.3f} Q_t={row.get('Q_t','?'):.3f} D_t={row.get('D_t','?'):.3f} R_t={row.get('R_t','?'):.3f}"
            )

        if lens_rows:
            summary_lines += ["", "1D LENS SEPARATIONS (sorted by Cohen's d effect size):"]
            for r in sorted(lens_rows, key=lambda x: x.get("Cohen's d", 0), reverse=True)[:8]:
                cohens_d = r.get("Cohen's d", "?")
                best_c   = r.get("Best contrast", "")
                summary_lines.append(
                    f"  {r['Lens']}: d={cohens_d} max_sep={r['Max separation']} best={best_c} — {r['Description']}"
                )

        if pair_rows:
            summary_lines += ["", "2D LENS PAIR DISTANCES (centroid separation):"]
            for r in sorted(pair_rows, key=lambda x: x.get("Max distance", 0), reverse=True)[:6]:
                summary_lines.append(f"  {r['Lens pair']}: max_dist={r.get('Max distance','?')}")

        focus = focus_pair
        data_summary = "\n".join(summary_lines)

        system_prompt = """You are a computational topology researcher specializing in TDA (Topological Data Analysis) applied to AI language model behavior analysis. You are collaborating with the SYN-IQ research team (Kouns, Nasrin, Farzana) who use KeplerMapper to analyze AI response spaces using IEP (Intellectual-Emotional-Practical) scoring and Vₜ coordinates.

Your role is to interpret lens projection data and provide publication-quality narrative analysis. Be specific, quantitative, and focus on what the topology reveals about intrinsic AI behavior rather than measurement artifacts. Address what Farzana called the core question: does the topology persist across measurement frameworks (IEP vs Vₜ vs geometric)?"""

        user_prompt = f"""Analyze this Vₜ lens projection data from the SYN-IQ cross-model harvester experiment.

{data_summary}

PRIMARY FOCUS: {focus}

Please provide a structured interpretation covering:

1. TOPOLOGICAL SEPARATION: Which lenses show the strongest condition separation? Are S_t and R_t performing as Farzana predicted for the COLD→FIRE contrast?

2. FRAMEWORK CONSISTENCY: Do the IEP-based lenses (int_pct, aff_pct, act_pct) and the Vₜ lenses (S_t, A_t, Q_t, D_t, R_t) reveal consistent structural patterns? This is the core cross-framework validation question.

3. AGENT DIFFERENTIATION: Which agents show the most distinct topological trajectories across conditions? Note any unexpected convergences or separations.

4. PUBLICATION-CRITICAL FINDINGS: What are the 2-3 most significant quantitative results that belong in the methods section of a paper?

5. RECOMMENDED MAPPER EXPERIMENTS: Which 1D and 2D lens combinations should be prioritized for the next KeplerMapper run, and why?

Be specific with numbers. Write as if this is a collaboration memo to Farzana Nasrin (Maroulas group, UTK TDA)."""

        with st.spinner("Claude is analyzing the topology..."):
            try:
                import requests
                key = st.secrets.get("anthropic") or st.secrets.get("ANTHROPIC_API_KEY")
                if not key:
                    st.error("Add 'anthropic' to Streamlit secrets.")
                else:
                    response = requests.post(
                        "https://api.anthropic.com/v1/messages",
                        headers={
                            "x-api-key": key,
                            "anthropic-version": "2023-06-01",
                            "content-type": "application/json"
                        },
                        json={
                            "model": "claude-opus-4-5-20251101",
                            "max_tokens": 2000,
                            "system": system_prompt,
                            "messages": [{"role": "user", "content": user_prompt}]
                        },
                        timeout=120
                    )
                    if response.status_code == 200:
                        analysis = response.json()["content"][0]["text"]
                        st.markdown(f"""
                        <div class="claude-box">
                            <div class="label">◆ CLAUDE · TOPOLOGY INTERPRETATION · {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}</div>
                            {analysis.replace(chr(10), '<br>')}
                        </div>
                        """, unsafe_allow_html=True)

                        # Download the analysis
                        st.download_button(
                            "⬇️ Download interpretation (.txt)",
                            analysis,
                            f"syniq_claude_interpretation_{ts}.txt",
                            "text/plain",
                        )
                    else:
                        st.error(f"API error {response.status_code}: {response.text[:300]}")
            except Exception as e:
                st.error(f"Claude API call failed: {e}")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:#2d5a7a;font-size:0.8rem;font-family:DM Mono,monospace'>"
    "SYN-IQ · Vₜ Lens Analyzer v4 · Kouns, W. C. (2026) · SYNINT.AI · Tennessee 🎹 · "
    "Cross-framework validation: IEP × Vₜ × Geometric</div>",
    unsafe_allow_html=True
)
