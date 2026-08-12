"""
Stability sweep figure, Streamlit edition.

Exposes render_stability_figure(df) -> matplotlib Figure.
No file reads, no side effects, nothing runs on import.

Usage inside the app:

    from stability_sweep_figure_v10 import render_stability_figure
    fig = render_stability_figure(sweep_df)
    st.pyplot(fig)

The dataframe needs, at minimum, the columns:
    'Lens', 'Q-purity (wtd)', 'A-purity (wtd)', and the beta-0 column.

NOTE ON NAMING. The tool calls the model label 'agent' and the metric
'A-purity'. The manuscript calls the label 'model' and the metric
'model-purity'. Same quantity. The axis labels below are deliberately
manuscript-facing; do not rename them back to match the column headers.

OPTIONAL PERMUTATION NULL. If the dataframe carries 'Q-null (wtd)' and
'A-null (wtd)', two extra rows are drawn showing the label-permutation
floor per lens. Absent those columns the figure renders as before.
Nulls come from purity_permutation_null() in the stability tool.
"""

import numpy as np
import matplotlib.pyplot as plt

Q_COL = "Q-purity (wtd)"
A_COL = "A-purity (wtd)"
B_COL = "\u03b2\u2080"          # beta-0

Q_NULL_COL = "Q-null (wtd)"
A_NULL_COL = "A-null (wtd)"


def _find_beta_col(df):
    """The beta-0 header uses a unicode subscript in some exports and a
    plain name in others. Accept either rather than failing."""
    for c in (B_COL, "beta0", "beta_0", "b0", "components"):
        if c in df.columns:
            return c
    return None


def render_stability_figure(df, title=None):
    """Build the stability-sweep heat map. Returns a matplotlib Figure.

    df : one row per lens, sorted internally by question-purity.
    """
    missing = [c for c in (Q_COL, A_COL, "Lens") if c not in df.columns]
    if missing:
        raise KeyError(
            "render_stability_figure needs column(s) %s. Present: %s. "
            "Note the tool writes 'A-purity (wtd)' even though the figure "
            "labels it Model-purity \u2014 do not rename the column."
            % (missing, list(df.columns))
        )

    beta_col = _find_beta_col(df)

    d = df.sort_values(Q_COL, ascending=False).reset_index(drop=True)
    lenses = d["Lens"].tolist()
    Q = d[Q_COL].values
    A = d[A_COL].values

    has_null = Q_NULL_COL in d.columns and A_NULL_COL in d.columns
    has_beta = beta_col is not None

    rows = ["Question-purity", "Model-purity"]
    mat = [Q, A]
    if has_null:
        rows += ["Question null", "Model null"]
        mat += [d[Q_NULL_COL].values, d[A_NULL_COL].values]
    mat = np.vstack(mat)

    height = 4.6 + (1.2 if has_null else 0) - (0.9 if not has_beta else 0)
    fig = plt.figure(figsize=(15, height))

    if has_beta:
        gs = fig.add_gridspec(2, 1,
                              height_ratios=[3 if has_null else 2, 1],
                              hspace=0.35)
        ax = fig.add_subplot(gs[0])
    else:
        ax = fig.add_subplot(1, 1, 1)

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

    if has_null:
        ax.axhline(1.5, color="black", lw=1.2)

    if title is None:
        title = ("Stability sweep \u00b7 combined four-model corpus \u00b7 "
                 "question separates, model does not (pooled)")
    ax.set_title(title, fontsize=12, pad=8, weight="bold")
    fig.colorbar(im, ax=ax, fraction=0.015, pad=0.01).set_label("purity", fontsize=9)

    if has_beta:
        b0 = d[beta_col].values
        ax2 = fig.add_subplot(gs[1])
        im2 = ax2.imshow(b0[None, :], aspect="auto", cmap="viridis")
        ax2.set_yticks([0])
        ax2.set_yticklabels(["\u03b2\u2080 (frag.)"], fontsize=11)
        ax2.set_xticks(range(len(lenses)))
        ax2.set_xticklabels([])
        for j in range(len(lenses)):
            ax2.text(j, 0, f"{int(b0[j])}", ha="center", va="center", fontsize=8,
                     color="white" if b0[j] < b0.max() * 0.55 else "black")
        fig.colorbar(im2, ax=ax2, fraction=0.015,
                     pad=0.01).set_label("components", fontsize=9)

    return fig
