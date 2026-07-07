#!/usr/bin/env python3
"""
syniq_pca_eps_tool.py — data-driven eps for the PCA(2D) Mapper, plus the
eps-free separation statistics, for any V57 pooled embedding CSV.

Run it:
    streamlit run syniq_pca_eps_tool.py

Why this exists: on the raw 384D embedding, DBSCAN can't separate agents at any
eps, and the "recommended eps" banner is a static hint. The Mapper's clean
clusters live in the PCA(2D) projection — so the correct eps must be computed IN
PCA SPACE, not guessed on the slider. This tool does that: it PCA-projects the
embeddings, finds the k-NN distance knee in that space, and reports the eps to
type into the Mapper. It also emits the eps-FREE evidence (global silhouette,
PC1 eta^2, the 6-pair separability matrix) so the paper's separation claim never
depends on any eps at all.

Protocol per question:
  1. eps-free stats on raw embeddings  -> the claim (no Mapper, no eps)
  2. PCA(2D) + k-NN knee                -> the eps to use in the Mapper
  3. eps sweep in PCA space             -> stability band (kills cherry-picking)

Input CSV needs: agent, embedding (JSON list). question_id/temperature optional.

Version: 1.0.0
"""

import io
import json
import itertools
import numpy as np
import pandas as pd
import streamlit as st
from sklearn.decomposition import PCA
from sklearn.neighbors import NearestNeighbors
from sklearn.cluster import DBSCAN
from sklearn.metrics import silhouette_score

AGENT_ORDER = ["Claude", "ChatGPT", "Grok", "Gemini"]


def order_agents(present):
    return [a for a in AGENT_ORDER if a in present] + sorted(a for a in present if a not in AGENT_ORDER)


def parse_embeddings(series):
    return np.vstack([np.array(json.loads(s), dtype=float) for s in series])


def unit(E):
    return E / (np.linalg.norm(E, axis=1, keepdims=True) + 1e-9)


def eta2_axis(x, g):
    gm = x.mean()
    ss_t = ((x - gm) ** 2).sum()
    ss_b = sum((g == a).sum() * (x[g == a].mean() - gm) ** 2 for a in np.unique(g))
    return ss_b / ss_t if ss_t > 0 else 0.0


def knee_eps(X, k):
    """k-NN distance knee (max gap in the sorted k-th neighbour distances)."""
    nn = NearestNeighbors(n_neighbors=k + 1).fit(X)
    d, _ = nn.kneighbors(X)
    kth = np.sort(d[:, k])
    diffs = np.diff(kth)
    half = len(diffs) // 2
    idx = np.argmax(diffs[half:]) + half
    return float(kth[idx]), kth


# ---------------------------------------------------------------------------
st.set_page_config(page_title="SYN-IQ PCA-eps", layout="wide")

APP_PASSWORD = "SYNIQ2026"
if not st.session_state.get("authed", False):
    st.title("SYN-IQ — PCA(2D) eps + Separation Stats")
    pw = st.text_input("Password", type="password")
    if st.button("Enter"):
        if pw == APP_PASSWORD:
            st.session_state["authed"] = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    st.stop()

st.title("SYN-IQ — PCA(2D) eps + Separation Stats  (v1.0.0)")
st.caption("Computes the data-driven eps for the PCA(2D) Mapper (k-NN knee in PCA space) "
           "and the eps-free separation evidence (global silhouette, PC1 \u03B7\u00B2, "
           "6-pair matrix). The stats are the claim; the eps is just what to type in the Mapper.")

uploaded = st.file_uploader("Pooled V57 CSV (needs: agent, embedding)", type=["csv"])
if uploaded is None:
    st.info("Upload a pooled CSV with an 'agent' column and a JSON 'embedding' column.")
    st.stop()

try:
    df = pd.read_csv(uploaded)
except Exception as e:
    st.error(f"Could not read the CSV: {e}")
    st.stop()

for col in ["agent", "embedding"]:
    if col not in df.columns:
        st.error(f"CSV missing required column: {col}")
        st.stop()

# optional temperature filter
if "temperature" in df.columns:
    temps = sorted(df["temperature"].dropna().astype(str).unique())
    default = temps.index("NATIVE") if "NATIVE" in temps else 0
    temp = st.selectbox("Temperature", temps, index=default)
    df = df[df["temperature"].astype(str).str.strip().str.upper() == temp.upper()]

df = df[df["embedding"].notna()].reset_index(drop=True)
E = unit(parse_embeddings(df["embedding"]))
ag = df["agent"].values
agents = order_agents(list(pd.unique(ag)))
k = st.number_input("k for k-NN knee (match Mapper min_samples)", 2, 10, 3, 1)

counts = {a: int((ag == a).sum()) for a in agents}
st.success(f"{len(df)} responses · " + " · ".join(f"{a} {counts[a]}" for a in agents))

# ---- PCA(2D) projection + eps knee in PCA space ----
P = PCA(n_components=2).fit(E)
XY = P.transform(E)
eps_pca, kth_pca = knee_eps(XY, k)
evr = P.explained_variance_ratio_

st.header("1 · eps for the PCA(2D) Mapper")
cA, cB, cC = st.columns(3)
cA.metric("Recommended eps (PCA space)", f"{eps_pca:.3f}")
cB.metric("Suggested band", f"{np.percentile(kth_pca,60):.2f} – {np.percentile(kth_pca,85):.2f}")
cC.metric("PC1+PC2 variance", f"{evr[:2].sum()*100:.1f}%")
st.caption(f"Set the Mapper's DBSCAN eps to ~{eps_pca:.2f} with min_samples={k}, PCA(2D) lens. "
           "This is the k-NN knee of the PCA projection — a computed value, not a slider guess.")

# ---- eps-free separation evidence ----
st.header("2 · eps-free separation evidence  (the actual claim)")
sil_all = silhouette_score(E, ag, metric="cosine")
pc1_all = PCA(n_components=1).fit_transform(E)[:, 0]
eta_all = eta2_axis(pc1_all, ag)

# anisotropy robustness: all-but-the-top-1
Ec = E - E.mean(0, keepdims=True)
top = PCA(n_components=1).fit(Ec).components_[0]
Eabt = Ec - (Ec @ top[:, None]) * top[None, :]
pc1_abt = PCA(n_components=1).fit_transform(Eabt)[:, 0]
eta_abt = eta2_axis(pc1_abt, ag)

d1, d2, d3 = st.columns(3)
d1.metric("4-agent silhouette (cosine)", f"{sil_all:+.3f}")
d2.metric("PC1 \u03B7\u00B2 (agent)", f"{eta_all:.3f}")
d3.metric("PC1 \u03B7\u00B2 after top-1 removed", f"{eta_abt:.3f}")
st.caption("Computed on the raw embeddings — no Mapper, no eps. The top-1-removed value "
           "shows the separation is not the anisotropy/bias axis (should hold or rise).")

# ---- pairwise matrix ----
st.subheader("Pairwise separability (6 pairs)")
rows = []
for a, b in itertools.combinations(agents, 2):
    m = (ag == a) | (ag == b)
    lab = (ag[m] == a).astype(int)
    sil = silhouette_score(E[m], lab, metric="cosine")
    pc1 = PCA(n_components=1).fit_transform(E[m])[:, 0]
    e2 = eta2_axis(pc1, ag[m])
    rows.append({"pair": f"{a} vs {b}", "silhouette": round(sil, 3), "PC1_eta2": round(e2, 3)})
mat = pd.DataFrame(rows).sort_values("silhouette", ascending=False).reset_index(drop=True)
st.dataframe(mat, use_container_width=True)
st.caption("Higher silhouette = more separable. Lowest positive pair = closest agents "
           "(adjacent but distinct, if PC1 \u03B7\u00B2 stays high).")

# ---- stability sweep in PCA space ----
st.header("3 · stability sweep (PCA space, DBSCAN cosine)")
sweep = []
lo = max(0.02, eps_pca - 0.15)
for eps in np.round(np.linspace(lo, eps_pca + 0.20, 8), 3):
    lab = DBSCAN(eps=eps, min_samples=k).fit_predict(XY)
    labs = [l for l in set(lab) if l != -1]
    noise = float((lab == -1).mean() * 100)
    purs = []
    for l in labs:
        vc = pd.Series(ag[lab == l]).value_counts(normalize=True)
        purs.append(float(vc.iloc[0]))
    sweep.append({"eps": eps, "n_clusters": len(labs),
                  "noise_pct": round(noise, 1),
                  "mean_purity": round(float(np.mean(purs)), 3) if purs else np.nan})
sweep_df = pd.DataFrame(sweep)
st.dataframe(sweep_df, use_container_width=True)
st.caption("Report the eps band where mean_purity stays high — that's the robustness "
           "statement that answers the cherry-picking objection.")

# ---- downloadable combined report ----
report = io.StringIO()
report.write("SYN-IQ PCA-eps report\n")
report.write(f"n={len(df)} | agents={counts}\n")
report.write(f"recommended_eps_pca={eps_pca:.3f} | min_samples={k} | "
             f"PC1+2_var={evr[:2].sum():.3f}\n")
report.write(f"global_silhouette={sil_all:.3f} | PC1_eta2={eta_all:.3f} | "
             f"PC1_eta2_top1removed={eta_abt:.3f}\n\n")
report.write("PAIRWISE\n"); mat.to_csv(report, index=False)
report.write("\nSTABILITY_SWEEP\n"); sweep_df.to_csv(report, index=False)
st.download_button("Download full report (CSV)", report.getvalue(),
                   file_name="pca_eps_report.csv", mime="text/csv")
