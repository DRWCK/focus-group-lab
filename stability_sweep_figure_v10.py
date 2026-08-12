"""
Figure maker for the Stability Sweep export.

Renders the combined-mode heat map: two purity rows (question separation
and model separation) across all lenses, plus a beta0 fragmentation strip.
Lenses are sorted by question-purity so the question gradient reads
left-to-right.

Reads the native Stability Sweep CSV (one row per lens, columns including
'Lens', 'Q-purity (wtd)', 'A-purity (wtd)', 'beta0').

NOTE ON NAMING. The tool calls the model label 'agent' and the metric
'A-purity'. The manuscript calls the label 'model' and the metric
'model-purity'. These are the same quantity. The axis labels below are
deliberately manuscript-facing; do not rename them back to match the
column headers.

OPTIONAL PERMUTATION NULL. If the CSV carries the columns
'Q-null (wtd)' and 'A-null (wtd)', a third row is drawn showing the
label-permutation floor per lens. Absent those columns the figure renders
exactly as before. Nulls are produced upstream by
purity_permutation_null() in the stability tool.

Thesis it shows: pooled across questions, question structure separates on
composition and geometric lenses and is weak on single features, while
model structure is uniformly low on EVERY lens (including TF-IDF), so
model separation must be read per-question, never pooled.
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CSV = "MULTI_ChatGPT_Claude_Gemini_Grok__stability_V9__1_.csv"
OUT = "Figure3_StabilitySweep_V10.png"

# column names (the beta0 header uses a unicode subscript in the export)
Q_COL = "Q-purity (wtd)"
A_COL = "A-purity (wtd)"
B_COL = "\u03b2\u2080"          # beta-0

# optional permutation-null columns, written upstream if present
Q_NULL_COL = "Q-null (wtd)"
A_NULL_COL = "A-null (wtd)"


def main():
    df = pd.read_csv(CSV).sort_values(Q_COL, ascending=False).reset_index(drop=True)
    lenses = df["Lens"].tolist()
    Q = df[Q_COL].values
    A = df[A_COL].values
    b0 = df[B_COL].values

    has_null = Q_NULL_COL in df.columns and A_NULL_COL in df.columns
    if has_null:
        Qn = df[Q_NULL_COL].values
        An = df[A_NULL_COL].values

    rows = ["Question-purity", "Model-purity"]
    mat = [Q, A]
    if has_null:
        rows += ["Question null", "Model null"]
        mat += [Qn, An]
    mat = np.vstack(mat)

    height = 4.6 if not has_null else 5.8
    fig = plt.figure(figsize=(15, height))
    gs = fig.add_gridspec(2, 1, height_ratios=[2 if not has_null else 3, 1],
                          hspace=0.35)

    # purity panel
    ax = fig.add_subplot(gs[0])
    im = ax.imshow(mat, aspect="auto", cmap="RdYlBu_r", vmin=0, vmax=1)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(rows, fontsize=11)
    ax.set_xticks(range(len(lenses)))
    ax.set_xticklabels(lenses, rotation=45, ha="right", fontsize=8)
    for i in range(mat.shape[0]):
        for j in range(len(lenses)):
            v = mat[i, j]
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=7.5,
                    color="white" if (v > 0.72 or v < 0.35) else "black")

    # separate the observed rows from the null rows
    if has_null:
        ax.axhline(1.5, color="black", lw=1.2)

    ax.set_title("Stability sweep \u00b7 combined four-model corpus \u00b7 "
                 "question separates, model does not (pooled)",
                 fontsize=12, pad=8, weight="bold")
    plt.colorbar(im, ax=ax, fraction=0.015, pad=0.01).set_label("purity", fontsize=9)

    # beta0 strip
    ax2 = fig.add_subplot(gs[1])
    im2 = ax2.imshow(b0[None, :], aspect="auto", cmap="viridis")
    ax2.set_yticks([0]); ax2.set_yticklabels(["\u03b2\u2080 (frag.)"], fontsize=11)
    ax2.set_xticks(range(len(lenses))); ax2.set_xticklabels([])
    for j in range(len(lenses)):
        ax2.text(j, 0, f"{int(b0[j])}", ha="center", va="center", fontsize=8,
                 color="white" if b0[j] < b0.max() * 0.55 else "black")
    plt.colorbar(im2, ax=ax2, fraction=0.015, pad=0.01).set_label("components", fontsize=9)

    plt.savefig(OUT, dpi=130, bbox_inches="tight", facecolor="white")
    print("saved", OUT, "| null rows:", has_null)


if __name__ == "__main__":
    main()
