#!/usr/bin/env python3
"""
SYN-IQ — Feature-Family Ablation (Streamlit)
============================================
Run exactly like the Mapper tool:

    streamlit run syniq_feature_ablation_app.py

Upload your four agent CSVs (or one combined CSV). Click "Run ablation."
You get the dual-axis cross-over — for each feature set, how AGENT-pure and
how QUESTION-pure the Mapper nodes are — as a table, a figure, and a
600-dpi RGB TIFF you can download straight into your Frontiers manuscript.

The result this proves (your finding):
  • IEP (int/aff/act) -> nodes are QUESTION-pure but AGENT-mixed
        => IEP is a TOPIC detector. Word choice within a category is
           collapsed away, and that's where agent identity lives.
  • Style (sentiment/readability/lexical) -> nodes are AGENT-pure
  The two axes are orthogonal, which is why adding IEP DILUTES agent
  separation rather than helping it.
"""
import io
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import kmapper as km
from sklearn.cluster import DBSCAN
from sklearn.decomposition import PCA
from sklearn.preprocessing import MinMaxScaler
from PIL import Image

# ── feature families ──────────────────────────────────────────────────────
IEP         = ["int_pct", "aff_pct", "act_pct"]
SENTIMENT   = ["vader_compound", "vader_pos", "vader_neg", "vader_neu"]
READABILITY = ["flesch_kincaid", "flesch_ease"]
LEXICAL     = ["ttr", "total_words", "unique_words"]
ALL12 = IEP + SENTIMENT + READABILITY + LEXICAL

PRESETS = [
    ("IEP only (3)",      IEP),
    ("IEP+Sentiment (7)", IEP + SENTIMENT),
    ("IEP+Sent+Read (9)", IEP + SENTIMENT + READABILITY),
    ("All 12 features",   ALL12),
    ("Style only (no IEP)", SENTIMENT + READABILITY + LEXICAL),
]

# ── compute (pure logic, no Streamlit — unit-testable) ─────────────────────
def _purity(graph, labels, threshold):
    """Mean plurality fraction over nodes, and fraction of nodes >= threshold."""
    vals = []
    for members in graph["nodes"].values():
        if not members:
            continue
        _, c = np.unique(labels[members], return_counts=True)
        vals.append(c.max() / c.sum())
    vals = np.array(vals) if vals else np.array([0.0])
    return float(vals.mean()), float((vals >= threshold).mean())

def _run_one(full, cols, params):
    cols = [c for c in cols if c in full.columns]
    data = MinMaxScaler().fit_transform(full[cols].values.astype(float))
    mapper = km.KeplerMapper(verbose=0)
    lens = mapper.fit_transform(data, projection=PCA(n_components=2, random_state=0))
    graph = mapper.map(
        lens, data,
        cover=km.Cover(n_cubes=params["n_cubes"], perc_overlap=params["overlap"]),
        clusterer=DBSCAN(eps=params["eps"], min_samples=params["min_samples"]),
    )
    G = nx.Graph()
    G.add_nodes_from(graph["nodes"])
    for a, nbrs in graph["links"].items():
        for b in nbrs:
            G.add_edge(a, b)
    beta_0 = nx.number_connected_components(G) if G.number_of_nodes() else 0
    a_mean, a_pure = _purity(graph, full["agent_label"].values, params["purity"])
    q_mean, q_pure = _purity(graph, full["question_id"].values, params["purity"])
    return dict(n_features=len(cols), nodes=G.number_of_nodes(), beta_0=beta_0,
                agent_pure=a_pure, agent_mean=a_mean,
                question_pure=q_pure, question_mean=q_mean)

def run_ablation(full, params):
    rows = []
    for name, cols in PRESETS:
        m = _run_one(full, cols, params)
        rows.append(dict(feature_set=name, **m))
    return pd.DataFrame(rows)

def crossover_figure(df):
    """The headline figure: agent-pure vs question-pure across feature sets."""
    fig, ax = plt.subplots(figsize=(7.087, 3.6))           # 180 mm
    x = range(len(df))
    ax.plot(x, df["agent_pure"] * 100, "-o", color="#377eb8",
            lw=2, label="Agent-pure %")
    ax.plot(x, df["question_pure"] * 100, "-s", color="#e41a1c",
            lw=2, label="Question-pure %")
    ax.set_xticks(list(x))
    ax.set_xticklabels(df["feature_set"], rotation=20, ha="right", fontsize=8)
    ax.set_ylabel("% of nodes >= purity threshold", fontsize=9)
    ax.set_ylim(0, 100)
    ax.set_title("Agent vs question separation by feature set",
                 fontsize=10, fontweight="bold")
    ax.legend(fontsize=9, frameon=True)
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    return fig

def figure_to_tiff_bytes(fig, dpi=600):
    """600-dpi RGB (no alpha) LZW TIFF, in memory, for st.download_button."""
    buf = io.BytesIO()
    fig.savefig(buf, format="tiff", dpi=dpi, bbox_inches="tight",
                pil_kwargs={"compression": "tiff_lzw"})
    buf.seek(0)
    im = Image.open(buf)
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bg = Image.new("RGB", im.size, "white")
        bg.paste(im, mask=im.split()[-1])
        im = bg
    out = io.BytesIO()
    im.save(out, format="tiff", compression="tiff_lzw")
    out.seek(0)
    return out.getvalue()

def load_uploaded(files, condition):
    frames = []
    for f in files:
        df = pd.read_csv(f)
        if "agent" in df.columns:
            df["agent"] = df["agent"].replace({"Sophia": "ChatGPT", "sophia": "ChatGPT"})
            df["agent_label"] = df["agent"]
        frames.append(df)
    full = pd.concat(frames, ignore_index=True)
    if condition and "temperature" in full.columns:
        full = full[full["temperature"] == condition].copy()
    return full

# ── password gate (reads from Secrets, never hardcoded) ────────────────────
def check_password():
    """Gate the app behind a password stored in Streamlit Secrets.
    The password itself lives in Secrets, NOT in this file — safe for a
    public repo. Returns True only once the correct password is entered."""
    expected = st.secrets.get("app_password", None)
    if not expected:
        # No password configured yet — fail closed so a public deploy is
        # never wide open by accident.
        st.error("🔒 No password set. Add `app_password` in the app's "
                 "Secrets (Streamlit Cloud → Settings → Secrets) to unlock.")
        st.stop()
    if st.session_state.get("auth_ok"):
        return True
    st.title("🔒 SYN-IQ — Authorized Access")
    pw = st.text_input("Password", type="password")
    if pw and pw == expected:
        st.session_state["auth_ok"] = True
        st.rerun()
    elif pw:
        st.error("Incorrect password.")
    st.stop()

# ── Streamlit UI ───────────────────────────────────────────────────────────
def main():
    st.set_page_config(page_title="SYN-IQ Feature Ablation", layout="wide")
    check_password()
    st.title("🧪 SYN-IQ — Feature-Family Ablation")
    st.caption("Does agent separation come from CONTENT (IEP) or STYLE? "
               "Dual-axis purity cross-over · 4 agents · NATIVE")

    with st.sidebar:
        st.header("Data")
        files = st.file_uploader("Upload agent CSV(s)", type=["csv"],
                                 accept_multiple_files=True)
        condition = st.text_input("Filter temperature to", value="NATIVE",
                                  help="Leave blank to pool all conditions.")
        st.header("Mapper parameters")
        st.caption("Held fixed across feature sets — only the features change.")
        params = dict(
            n_cubes=st.slider("n_cubes", 5, 20, 10),
            overlap=st.slider("overlap", 0.1, 0.6, 0.30, 0.05),
            eps=st.slider("DBSCAN eps", 0.1, 3.0, 0.5, 0.1),
            min_samples=st.slider("DBSCAN min_samples", 2, 8, 3),
            purity=st.slider("Purity threshold", 0.5, 1.0, 0.80, 0.05),
        )

    if not files:
        st.info("👈 Upload your four agent CSVs to begin. "
                "Each needs: agent, temperature, question_id, and the "
                "feature columns (int_pct … unique_words).")
        return

    full = load_uploaded(files, condition.strip() or None)
    if "agent_label" not in full or "question_id" not in full:
        st.error("CSV must contain 'agent' and 'question_id' columns.")
        return
    st.write(f"Loaded **{len(full)}** rows · "
             f"agents: {', '.join(full['agent_label'].unique())} · "
             f"questions: {full['question_id'].nunique()}")

    if not st.button("▶ Run ablation", type="primary"):
        return

    with st.spinner("Running Mapper across feature sets…"):
        df = run_ablation(full, params)

    # ── cross-over readout ────────────────────────────────────────────────
    iep = df[df.feature_set == "IEP only (3)"].iloc[0]
    style = df[df.feature_set == "Style only (no IEP)"].iloc[0]
    c1, c2 = st.columns(2)
    c1.metric("IEP-only → QUESTION-pure", f"{iep.question_pure:.0%}",
              f"agent-pure only {iep.agent_pure:.0%}")
    c2.metric("Style-only → AGENT-pure", f"{style.agent_pure:.0%}",
              f"question-pure only {style.question_pure:.0%}")
    if iep.question_pure > iep.agent_pure and style.agent_pure > style.question_pure:
        st.success("✅ Cross-over confirmed: IEP separates QUESTIONS, "
                   "style separates AGENTS. The two axes are orthogonal — "
                   "which is why adding IEP dilutes agent separation.")
    else:
        st.warning("Cross-over not clean at these parameters — adjust eps/overlap "
                   "and re-run, or inspect the table below.")

    # ── table ─────────────────────────────────────────────────────────────
    show = df.copy()
    for col in ["agent_pure", "agent_mean", "question_pure", "question_mean"]:
        show[col] = (show[col] * 100).round(1)
    st.dataframe(show, use_container_width=True)

    # ── figure + downloads ────────────────────────────────────────────────
    fig = crossover_figure(df)
    st.pyplot(fig)
    st.download_button("📥 Download figure — Frontiers TIFF (600 dpi)",
                       figure_to_tiff_bytes(fig),
                       file_name="fig_42_crossover.tiff", mime="image/tiff")
    st.download_button("📥 Download table (CSV)",
                       df.to_csv(index=False),
                       file_name="fig_42_crossover.csv", mime="text/csv")

if __name__ == "__main__":
    main()
