#!/usr/bin/env python3
"""
SYN-IQ — Feature Ablation v2 (full V51 features)
================================================
Run like the Mapper tool:   streamlit run syniq_ablation_v2_app.py

What's new vs v1
----------------
1. ALL V51 feature families, grouped and toggleable:
     IEP-3 (top-line)        int/aff/act %
     IEP-23 (sub-texture)    the 23 aff/int/act sub-dimensions
     CAM-3                   concrete / abstract / metaphorical %
     Voice-5                 S_t A_t Q_t D_t R_t lenses
     Sentiment-4, Readability-2, Lexical-3   (the old style features)
   The key experiment is built in as a preset: IEP-3 vs IEP-23 — does
   finer content texture recover agent identity that the 3-way collapse
   averaged away?

2. POINT-LEVEL separability, not just node purity. Node purity wobbles
   badly at n=20 (~50 nodes, ~8 points each). The point-level metrics use
   ALL responses and are stable run-to-run:
     • classifier accuracy  — cross-validated logistic regression
       predicting AGENT vs QUESTION from the features (chance shown).
     • silhouette           — how separated the labelled clouds are.
   The Mapper graph stays as the PICTURE; these numbers are the CLAIM.

3. TEMPERATURE GUARD. Mixed temperatures blur agents (a node can be
   "pure ChatGPT" only because it pooled ChatGPT-COLD with ChatGPT-FIRE).
   The app filters to ONE temperature and refuses to run on a mix unless
   you explicitly opt in.
"""
import io
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import silhouette_score
import networkx as nx
import kmapper as km
from sklearn.cluster import DBSCAN
from PIL import Image

# ── feature families (V51) ────────────────────────────────────────────────
IEP3  = ["int_pct", "aff_pct", "act_pct"]
IEP23 = ([f"aff_sub_{s}" for s in
          ["distress","warmth","relational","self_state","positive",
           "intensity","phenomenological"]] +
         [f"int_sub_{s}" for s in
          ["analytical","conceptual","epistemic","structural","critical",
           "lexical","hedging","phenomenological"]] +
         [f"act_sub_{s}" for s in
          ["execution","planning","building","improvement","provision",
           "leadership","achievement","phenomenological"]])
CAM   = ["con_pct", "abs_pct", "met_pct"]
VOICE = ["S_t", "A_t", "Q_t", "D_t", "R_t"]
SENT  = ["vader_compound", "vader_pos", "vader_neg", "vader_neu"]
READ  = ["flesch_kincaid", "flesch_ease"]
LEX   = ["ttr", "total_words", "unique_words"]

GROUPS = {  # label -> columns, for the sidebar toggles
    "IEP-3 (top-line content)": IEP3,
    "IEP-23 (sub-texture)":     IEP23,
    "CAM-3 (concrete/abstract/metaphor)": CAM,
    "Voice-5 (S_t…R_t)":        VOICE,
    "Sentiment-4":              SENT,
    "Readability-2":            READ,
    "Lexical-3":                LEX,
}

# The scientific menu — the IEP-3 vs IEP-23 contrast is the headline.
PRESETS = [
    ("IEP-3 (coarse content)",          IEP3),
    ("IEP-23 (fine content)",           IEP23),
    ("CAM-3",                           CAM),
    ("Voice-5",                         VOICE),
    ("All content (IEP-23+CAM+Voice)",  IEP23 + CAM + VOICE),
    ("Style (sent+read+lex)",           SENT + READ + LEX),
    ("Everything",                      IEP3 + IEP23 + CAM + VOICE + SENT + READ + LEX),
]

# ── point-level separability (STABLE — uses every response) ────────────────
def point_separability(full, cols):
    cols = [c for c in cols if c in full.columns]
    X = full[cols].values.astype(float)
    X = np.nan_to_num(X)
    out = {}
    Xstd = StandardScaler().fit_transform(X)   # classifier likes standardized
    Xmm  = MinMaxScaler().fit_transform(X)     # silhouette in mapper space
    for key, lab in [("agent", "agent_label"), ("question", "question_id")]:
        y = np.asarray(full[lab].astype(str).to_numpy(), dtype=object)
        classes = np.unique(y)
        if len(classes) < 2:
            out[key] = dict(acc=np.nan, chance=np.nan, sil=np.nan, n_classes=len(classes))
            continue
        # min class count caps the CV folds
        min_n = pd.Series(y).value_counts().min()
        k = max(2, min(5, int(min_n)))
        clf = LogisticRegression(max_iter=2000)
        acc = cross_val_score(clf, Xstd, y,
                              cv=StratifiedKFold(k, shuffle=True, random_state=0)).mean()
        try:
            sil = silhouette_score(Xmm, y)
        except Exception:
            sil = np.nan
        out[key] = dict(acc=float(acc), chance=1.0 / len(classes),
                        sil=float(sil), n_classes=len(classes))
    return out

# ── node purity (kept for the picture / continuity) ────────────────────────
def node_metrics(full, cols, p):
    cols = [c for c in cols if c in full.columns]
    data = MinMaxScaler().fit_transform(np.nan_to_num(full[cols].values.astype(float)))
    mapper = km.KeplerMapper(verbose=0)
    lens = mapper.fit_transform(data, projection=PCA(n_components=2, random_state=0))
    graph = mapper.map(lens, data,
                       cover=km.Cover(n_cubes=p["n_cubes"], perc_overlap=p["overlap"]),
                       clusterer=DBSCAN(eps=p["eps"], min_samples=p["min_samples"]))
    G = nx.Graph(); G.add_nodes_from(graph["nodes"])
    for a, nb in graph["links"].items():
        for b in nb:
            G.add_edge(a, b)
    beta0 = nx.number_connected_components(G) if G.number_of_nodes() else 0
    def mean_pur(labels):
        v = []
        for m in graph["nodes"].values():
            if m:
                _, c = np.unique(labels[m], return_counts=True)
                v.append(c.max() / c.sum())
        return float(np.mean(v)) if v else np.nan
    return dict(nodes=G.number_of_nodes(), beta_0=beta0,
                agent_node_purity=mean_pur(np.asarray(full["agent_label"].astype(str).to_numpy(), dtype=object)),
                question_node_purity=mean_pur(np.asarray(full["question_id"].astype(str).to_numpy(), dtype=object)))

def run_ablation(full, p):
    rows = []
    for name, cols in PRESETS:
        used = [c for c in cols if c in full.columns]
        ps = point_separability(full, cols)
        nm = node_metrics(full, cols, p)
        rows.append(dict(
            feature_set=name, n_features=len(used),
            agent_acc=ps["agent"]["acc"], agent_chance=ps["agent"]["chance"],
            agent_sil=ps["agent"]["sil"],
            question_acc=ps["question"]["acc"], question_chance=ps["question"]["chance"],
            question_sil=ps["question"]["sil"],
            **nm))
    return pd.DataFrame(rows)

# ── figure ──────────────────────────────────────────────────────────────────
def crossover_figure(df, temp):
    fig, ax = plt.subplots(figsize=(7.087, 3.8))
    x = range(len(df))
    ax.plot(x, df["agent_acc"] * 100, "-o", color="#377eb8", lw=2, label="Agent recoverable %")
    ax.plot(x, df["question_acc"] * 100, "-s", color="#e41a1c", lw=2, label="Question recoverable %")
    if df["agent_chance"].notna().any():
        ax.axhline(df["agent_chance"].dropna().iloc[0] * 100, ls=":", color="#377eb8", alpha=.6, lw=1)
    if df["question_chance"].notna().any():
        ax.axhline(df["question_chance"].dropna().iloc[0] * 100, ls=":", color="#e41a1c", alpha=.6, lw=1)
    ax.set_xticks(list(x)); ax.set_xticklabels(df["feature_set"], rotation=22, ha="right", fontsize=7)
    ax.set_ylabel("cross-validated recoverability %", fontsize=9); ax.set_ylim(0, 100)
    ax.set_title(f"Agent vs question recoverability by feature set · {temp}",
                 fontsize=10, fontweight="bold")
    ax.legend(fontsize=8, frameon=True); ax.grid(True, alpha=.25)
    fig.tight_layout(); return fig

def tiff_bytes(fig, dpi=600):
    buf = io.BytesIO()
    fig.savefig(buf, format="tiff", dpi=dpi, bbox_inches="tight",
                pil_kwargs={"compression": "tiff_lzw"})
    buf.seek(0); im = Image.open(buf)
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA"); bg = Image.new("RGB", im.size, "white")
        bg.paste(im, mask=im.split()[-1]); im = bg
    out = io.BytesIO(); im.save(out, format="tiff", compression="tiff_lzw")
    out.seek(0); return out.getvalue()

# ── password gate ────────────────────────────────────────────────────────
def check_password():
    expected = st.secrets.get("app_password", None)
    if not expected:
        st.error("🔒 No password set. Add `app_password` in the app's Secrets.")
        st.stop()
    if st.session_state.get("auth_ok"):
        return
    st.title("🔒 SYN-IQ — Authorized Access")
    pw = st.text_input("Password", type="password")
    if pw and pw == expected:
        st.session_state["auth_ok"] = True; st.rerun()
    elif pw:
        st.error("Incorrect password.")
    st.stop()

# ── UI ───────────────────────────────────────────────────────────────────
def main():
    st.set_page_config(page_title="SYN-IQ Ablation v2", layout="wide")
    check_password()
    st.title("🧪 SYN-IQ — Feature Ablation v2")
    st.caption("Full V51 features · point-level recoverability (stable at n=20) · "
               "temperature-locked")

    with st.sidebar:
        st.header("Data")
        files = st.file_uploader("Upload agent CSV(s)", type=["csv"],
                                 accept_multiple_files=True)
        temp = st.text_input("Temperature (lock to ONE)", value="NATIVE")
        allow_mix = st.checkbox("Allow mixed temperatures (advanced)", value=False,
                                help="Off by default — mixed heats blur agent identity.")
        st.header("Mapper params (node picture only)")
        p = dict(n_cubes=st.slider("n_cubes", 5, 20, 10),
                 overlap=st.slider("overlap", 0.1, 0.6, 0.30, 0.05),
                 eps=st.slider("DBSCAN eps", 0.1, 3.0, 0.5, 0.1),
                 min_samples=st.slider("DBSCAN min_samples", 2, 8, 3))

    if not files:
        st.info("👈 Upload your agent CSV(s) (V51 format). The recoverability "
                "numbers are the result; the Mapper graph is the picture.")
        return

    frames = []
    for f in files:
        d = pd.read_csv(f)
        if "agent" in d.columns:
            d["agent"] = d["agent"].replace({"Sophia": "ChatGPT", "sophia": "ChatGPT"})
            d["agent_label"] = d["agent"]
        frames.append(d)
    full = pd.concat(frames, ignore_index=True)

    if temp.strip() and "temperature" in full.columns:
        full = full[full["temperature"] == temp.strip()].copy()

    temps_present = sorted(full["temperature"].unique()) if "temperature" in full else []
    if len(temps_present) > 1 and not allow_mix:
        st.error(f"🌡️ Multiple temperatures present ({', '.join(map(str,temps_present))}). "
                 "Mixed heats blur agent identity. Set the Temperature box to one value, "
                 "or tick 'Allow mixed temperatures' to override.")
        st.stop()

    n_agents = full["agent_label"].nunique() if "agent_label" in full else 0
    st.write(f"**{len(full)}** rows · **{n_agents}** agent(s): "
             f"{', '.join(map(str, full['agent_label'].unique()))} · "
             f"temp: {', '.join(map(str, temps_present)) or 'n/a'} · "
             f"questions: {full['question_id'].nunique()}")
    if n_agents < 2:
        st.warning("Only one agent loaded — agent recoverability needs ≥2 agents. "
                   "Upload all agent files together for the cross-over.")

    if not st.button("▶ Run ablation", type="primary"):
        return
    with st.spinner("Computing recoverability across feature sets…"):
        df = run_ablation(full, p)

    # headline cross-over readout (point-level, stable)
    iep3 = df[df.feature_set == "IEP-3 (coarse content)"].iloc[0]
    iep23 = df[df.feature_set == "IEP-23 (fine content)"].iloc[0]
    c1, c2, c3 = st.columns(3)
    c1.metric("Question from IEP-3", f"{iep3.question_acc:.0%}",
              f"chance {iep3.question_chance:.0%}")
    c2.metric("Agent from IEP-3", f"{iep3.agent_acc:.0%}",
              f"chance {iep3.agent_chance:.0%}")
    c3.metric("Agent from IEP-23", f"{iep23.agent_acc:.0%}",
              f"Δ vs IEP-3 {iep23.agent_acc - iep3.agent_acc:+.0%}")
    if iep23.agent_acc - iep3.agent_acc > 0.05:
        st.success("✅ Finer content texture (IEP-23) recovers agent identity that "
                   "the 3-way collapse (IEP-3) averaged away — the collapse mechanism, "
                   "shown with content features alone.")
    else:
        st.info("IEP-23 does not recover much agent signal beyond IEP-3 here — "
                "agent identity may live mainly in style, not content texture.")

    show = df.copy()
    for c in ["agent_acc","agent_chance","question_acc","question_chance",
              "agent_node_purity","question_node_purity"]:
        show[c] = (show[c] * 100).round(1)
    for c in ["agent_sil","question_sil"]:
        show[c] = show[c].round(3)
    st.dataframe(show, use_container_width=True)

    fig = crossover_figure(df, temp.strip() or "all temps")
    st.pyplot(fig)
    st.download_button("📥 Figure — Frontiers TIFF (600 dpi)", tiff_bytes(fig),
                       file_name=f"fig_recoverability_{temp.strip() or 'all'}.tiff",
                       mime="image/tiff")
    st.download_button("📥 Table (CSV)", df.to_csv(index=False),
                       file_name=f"fig_recoverability_{temp.strip() or 'all'}.csv",
                       mime="text/csv")

if __name__ == "__main__":
    main()
