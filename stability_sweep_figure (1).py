"""
Figure maker for the Stability Sweep (V11) export.

Layout: beta0 fragmentation strip on top, purity panel (Q = question
separation, A = agent separation) below, lens names only at the bottom.
Lenses sorted by Q-purity so the question gradient reads left-to-right.

Reads the native Stability Sweep CSV (one row per lens, columns
including 'Lens', 'Q-purity (wtd)', 'A-purity (wtd)', and the beta0
column whose header is a unicode subscript).

Thesis it shows: pooled across questions, question structure is
recoverable on composition/geometric lenses and weak on single
features, while agent structure is uniformly low on EVERY lens
(including TF-IDF) — so agent separation must be read per-question,
never pooled.
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CSV = "MULTI_ChatGPT_Claude_Gemini_Grok__stability_V11__1_.csv"
OUT = "Figure3_StabilitySweep_V11.png"

Q_COL = "Q-purity (wtd)"
A_COL = "A-purity (wtd)"
B_COL = "\u03b2\u2080"          # β₀


def main():
    df = pd.read_csv(CSV).sort_values(Q_COL, ascending=False).reset_index(drop=True)
    lenses = df["Lens"].tolist()
    Q = df[Q_COL].values
    A = df[A_COL].values
    b0 = df[B_COL].values

    fig = plt.figure(figsize=(15, 4.8))
    gs = fig.add_gridspec(2, 1, height_ratios=[1, 2], hspace=0.12)

    # TOP: beta0 fragmentation strip (no x labels here)
    axt = fig.add_subplot(gs[0])
    im0 = axt.imshow(b0[None, :], aspect="auto", cmap="viridis")
    axt.set_yticks([0]); axt.set_yticklabels(["\u03b2\u2080 (frag.)"], fontsize=11)
    axt.set_xticks(range(len(lenses))); axt.set_xticklabels([])
    for j in range(len(lenses)):
        axt.text(j, 0, f"{int(b0[j])}", ha="center", va="center", fontsize=8,
                 color="white" if b0[j] < b0.max() * 0.55 else "black")
    axt.set_title("Stability Sweep V11 \u00b7 combined 4-agent \u00b7 "
                  "question is recoverable, agent is not (pooled)",
                  fontsize=12, pad=8, weight="bold")
    plt.colorbar(im0, ax=axt, fraction=0.015, pad=0.01).set_label("components", fontsize=9)

    # BOTTOM: Q / A purity panel (lens labels only here)
    axb = fig.add_subplot(gs[1])
    mat = np.vstack([Q, A])
    im1 = axb.imshow(mat, aspect="auto", cmap="RdYlBu_r", vmin=0, vmax=1)
    axb.set_yticks([0, 1])
    axb.set_yticklabels(["Q-purity\n(question)", "A-purity\n(agent)"], fontsize=11)
    axb.set_xticks(range(len(lenses)))
    axb.set_xticklabels(lenses, rotation=45, ha="right", fontsize=8)
    for i in range(2):
        for j in range(len(lenses)):
            v = mat[i, j]
            axb.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=7.5,
                     color="white" if (v > 0.72 or v < 0.35) else "black")
    plt.colorbar(im1, ax=axb, fraction=0.015, pad=0.01).set_label("purity", fontsize=9)

    plt.savefig(OUT, dpi=130, bbox_inches="tight", facecolor="white")
    print("saved", OUT)


if __name__ == "__main__":
    main()
