# =============================================================================
# PERMUTATION NULL FOR NODE PURITY
# Drop in next to question_purity() in syniq_lens_stability_v11.py
# =============================================================================

def purity_permutation_null(node_idx_lists, df, label_col='question_id',
                            n_perm=2000, seed=42):
    """Label-permutation null for node purity.

    Holds the Mapper graph fixed (node membership, node sizes, cover all
    unchanged) and shuffles the label column across responses. This gives the
    purity floor imposed by the node-size distribution, which is well above
    1/k because small nodes are pure by construction.

    Returns dict with:
      observed_mean, observed_weighted   - purity on the true labels
      null_mean, null_weighted           - mean purity across permutations
      null_mean_p95, null_weighted_p95   - 95th percentile of the null
      p_mean, p_weighted                 - one-sided p, bounded by 1/(n_perm+1)
      n_perm
    """
    from collections import Counter

    if label_col not in df.columns:
        return None

    obs_mean, obs_wtd = question_purity(node_idx_lists, df, label_col=label_col)
    if obs_mean is None:
        return None

    # Freeze node membership once; only labels change under the null.
    idx_lists = [np.asarray(v) for v in node_idx_lists.values() if len(v)]
    sizes = np.array([len(v) for v in idx_lists], dtype=float)
    labels = df[label_col].values

    rng = np.random.default_rng(seed)
    null_mean = np.empty(n_perm)
    null_wtd = np.empty(n_perm)

    for b in range(n_perm):
        shuffled = rng.permutation(labels)
        p = np.empty(len(idx_lists))
        for j, idx in enumerate(idx_lists):
            c = Counter(shuffled[idx].tolist())
            p[j] = c.most_common(1)[0][1] / len(idx)
        null_mean[b] = p.mean()
        null_wtd[b] = np.average(p, weights=sizes)

    return {
        'label_col': label_col,
        'observed_mean': obs_mean,
        'observed_weighted': obs_wtd,
        'null_mean': float(null_mean.mean()),
        'null_weighted': float(null_wtd.mean()),
        'null_mean_p95': float(np.percentile(null_mean, 95)),
        'null_weighted_p95': float(np.percentile(null_wtd, 95)),
        'p_mean': float((1 + np.sum(null_mean >= obs_mean)) / (n_perm + 1)),
        'p_weighted': float((1 + np.sum(null_wtd >= obs_wtd)) / (n_perm + 1)),
        'n_perm': n_perm,
    }
