#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ieap_vocab_utilization_v2.py
============================
IEAP Vocabulary Utilization Tool  (v2)

v2: per-agent table now pools the full unique-vocabulary set, adding
    unique_words and unique_iep_pct_of_unique_vocab (concentration rate),
    so the pooled per-agent output matches the density + concentration
    rate layout. Feed a whole corpus to pool across all questions.

Measures how much of the sealed 1,897-term IEAP lexicon each agent actually
uses, per question. Keeps two counts strictly separate throughout:

    OCCURRENCES  = token hits (a word counted every time it appears)
    UNIQUE TYPES = distinct dictionary words used (counted once)

Word choice only. No meaning claim. Tokenizer and first-match priority
(INT_PRIORITY -> INT -> AFF -> ACT) replicate syniq_core_v1_1_0 exactly, so
occurrence counts line up with the harvester's IEP scoring.

INPUTS
    --responses   CSV of responses (needs an agent col, a text col, and a
                  question col; auto-detected).
    --dict        OPTIONAL external lexicon. JSON {"INT":[...],"AFF":[...],
                  "ACT":[...]} or CSV with columns (word, axis). If omitted,
                  the sealed V50_1897 dictionary is loaded from
                  syniq_core_v1_1_0 (616 INT / 599 AFF / 682 ACT).

OUTPUTS  (written to --outdir)
    <stem>_summary.csv        one row per (question, agent)
    <stem>_per_agent.csv      one row per agent (pooled across questions)
    <stem>_tfidf.csv          OPTIONAL IEAP-restricted distinctive terms
    <stem>_heatmap.png        OPTIONAL dictionary-utilization heatmap

USAGE
    python ieap_vocab_utilization_v1.py --responses resp.csv
    python ieap_vocab_utilization_v1.py --responses resp.csv --tfidf --heatmap
    python ieap_vocab_utilization_v1.py --responses resp.csv --dict mydict.json
"""

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict

import pandas as pd

TOOL_VERSION = "ieap_vocab_utilization_v2"
IEP_DICTIONARY_VERSION = "V50_1897"

# ---------------------------------------------------------------------------
# Lexicon loading
# ---------------------------------------------------------------------------
def load_sealed_lexicon(core_dir="/mnt/project"):
    """Import the sealed V50_1897 sets straight from syniq_core_v1_1_0."""
    if core_dir not in sys.path:
        sys.path.insert(0, core_dir)
    import syniq_core_v1_1_0 as core  # noqa
    return (set(core.INT_WORDS), set(core.AFF_WORDS),
            set(core.ACT_WORDS), set(core.INT_PRIORITY))


def load_external_lexicon(path):
    """Load INT/AFF/ACT lists from a JSON or CSV file. INT_PRIORITY empty."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".json":
        with open(path, "r", encoding="utf-8") as fh:
            d = json.load(fh)
        keymap = {k.upper(): k for k in d}
        INT = set(map(str.lower, d[keymap["INT"]]))
        AFF = set(map(str.lower, d[keymap["AFF"]]))
        ACT = set(map(str.lower, d[keymap["ACT"]]))
    else:  # CSV: columns word, axis
        df = pd.read_csv(path)
        cols = {c.lower(): c for c in df.columns}
        wcol = cols.get("word") or cols.get("term") or df.columns[0]
        acol = cols.get("axis") or cols.get("class") or cols.get("iep") or df.columns[1]
        df[wcol] = df[wcol].astype(str).str.lower()
        df[acol] = df[acol].astype(str).str.upper().str[:3]
        INT = set(df.loc[df[acol] == "INT", wcol])
        AFF = set(df.loc[df[acol] == "AFF", wcol])
        ACT = set(df.loc[df[acol] == "ACT", wcol])
    return INT, AFF, ACT, set()


# ---------------------------------------------------------------------------
# Tokenizer  (byte-for-byte match to syniq_core_v1_1_0.score_iep)
# ---------------------------------------------------------------------------
def tokenize(text):
    """lowercase, strip 's and ', non-alpha -> space, keep tokens len > 1."""
    raw = str(text).lower().replace("'s", "").replace("'", "")
    raw = "".join(c if c.isalpha() or c == " " else " " for c in raw)
    return [w for w in raw.split() if len(w) > 1]


def classify(tokens, INT, AFF, ACT, PRIORITY):
    """First-match priority: INT_PRIORITY -> INT -> AFF -> ACT.
    Returns per-axis lists of occurrence hits (with repeats)."""
    int_hits, aff_hits, act_hits = [], [], []
    for w in tokens:
        if w in PRIORITY:
            int_hits.append(w)
        elif w in INT:
            int_hits.append(w)
        elif w in AFF:
            aff_hits.append(w)
        elif w in ACT:
            act_hits.append(w)
    return int_hits, aff_hits, act_hits


# ---------------------------------------------------------------------------
# Column auto-detection
# ---------------------------------------------------------------------------
def pick(colmap, *cands):
    for c in cands:
        if c in colmap:
            return colmap[c]
    return None


def detect_columns(df):
    colmap = {c.lower(): c for c in df.columns}
    agent = pick(colmap, "agent", "model", "ai")
    text = pick(colmap, "response_text", "response", "text", "output")
    ques = pick(colmap, "question_id", "question", "question_text", "qid")
    missing = [n for n, v in [("agent", agent), ("text", text), ("question", ques)] if v is None]
    if missing:
        raise ValueError(f"Could not find column(s) for: {missing}. "
                         f"Available: {list(df.columns)}")
    return agent, text, ques


# ---------------------------------------------------------------------------
# Core computation
# ---------------------------------------------------------------------------
def build_records(df, agent_col, text_col, ques_col, LEX):
    """One record per (question, agent), aggregating all responses in that cell."""
    INT, AFF, ACT, PRIORITY, DSIZE = LEX
    grouped = defaultdict(lambda: {
        "all_tokens": [],
        "int_hits": [], "aff_hits": [], "act_hits": [],
    })

    for _, row in df.iterrows():
        q = str(row[ques_col])
        a = str(row[agent_col])
        toks = tokenize(row[text_col])
        ih, ah, ch = classify(toks, INT, AFF, ACT, PRIORITY)
        g = grouped[(q, a)]
        g["all_tokens"].extend(toks)
        g["int_hits"].extend(ih)
        g["aff_hits"].extend(ah)
        g["act_hits"].extend(ch)

    # per (question -> agent -> unique IEAP type set), for shared/specific analysis
    q_agent_types = defaultdict(dict)
    records = []
    for (q, a), g in grouped.items():
        toks = g["all_tokens"]
        total_words = len(toks)
        unique_words = len(set(toks))

        ih, ah, ch = g["int_hits"], g["aff_hits"], g["act_hits"]
        occ = len(ih) + len(ah) + len(ch)

        int_types = set(ih); aff_types = set(ah); act_types = set(ch)
        iep_types = int_types | aff_types | act_types
        uniq_iep = len(iep_types)

        q_agent_types[q][a] = iep_types

        rec = {
            "question": q,
            "agent": a,
            "total_words": total_words,
            "unique_words": unique_words,
            # occurrences (with repeats)
            "iep_occurrences": occ,
            "int_occurrences": len(ih),
            "aff_occurrences": len(ah),
            "act_occurrences": len(ch),
            "iep_pct_of_all_words": round(100 * occ / total_words, 3) if total_words else 0.0,
            # unique types
            "unique_iep_words": uniq_iep,
            "int_unique_words": len(int_types),
            "aff_unique_words": len(aff_types),
            "act_unique_words": len(act_types),
            "unique_iep_pct_of_unique_vocab": round(100 * uniq_iep / unique_words, 3) if unique_words else 0.0,
            # dictionary coverage (unique types used / axis dict size)
            "int_dict_coverage_pct": round(100 * len(int_types) / DSIZE["INT"], 3),
            "aff_dict_coverage_pct": round(100 * len(aff_types) / DSIZE["AFF"], 3),
            "act_dict_coverage_pct": round(100 * len(act_types) / DSIZE["ACT"], 3),
            # carry the type sets for downstream (dropped before CSV write)
            "_int_types": int_types, "_aff_types": aff_types, "_act_types": act_types,
            "_iep_types": iep_types, "_vocab_types": set(toks),
        }
        records.append(rec)

    # shared across agents / agent-specific, computed within each question
    for rec in records:
        q, a = rec["question"], rec["agent"]
        agents_here = q_agent_types[q]
        others = [types for other_a, types in agents_here.items() if other_a != a]
        my_types = agents_here[a]
        if others:
            union_others = set().union(*others)
            shared = my_types & union_others
            specific = my_types - union_others
        else:
            shared = set()
            specific = set(my_types)
        rec["iep_words_shared_with_other_agents"] = len(shared)
        rec["iep_words_agent_specific"] = len(specific)
        rec["_specific_types"] = specific

    return records, q_agent_types


def per_agent_table(records, LEX):
    """Pool across questions: one row per agent."""
    _, _, _, _, DSIZE = LEX
    by_agent = defaultdict(lambda: {
        "total_words": 0, "vocab_set": set(),
        "iep_occ": 0, "int_occ": 0, "aff_occ": 0, "act_occ": 0,
        "int_types": set(), "aff_types": set(), "act_types": set(),
        "n_cells": 0,
    })
    for r in records:
        a = r["agent"]
        b = by_agent[a]
        b["total_words"] += r["total_words"]
        b["vocab_set"] |= r["_vocab_types"]
        b["iep_occ"] += r["iep_occurrences"]
        b["int_occ"] += r["int_occurrences"]
        b["aff_occ"] += r["aff_occurrences"]
        b["act_occ"] += r["act_occurrences"]
        b["int_types"] |= r["_int_types"]
        b["aff_types"] |= r["_aff_types"]
        b["act_types"] |= r["_act_types"]
        b["n_cells"] += 1

    rows = []
    for a, b in by_agent.items():
        iep_types = b["int_types"] | b["aff_types"] | b["act_types"]
        unique_words = len(b["vocab_set"])
        uniq_iep = len(iep_types)
        rows.append({
            "agent": a,
            "n_question_cells": b["n_cells"],
            "total_words": b["total_words"],
            # occurrences + density rate
            "iep_occurrences": b["iep_occ"],
            "iep_pct_of_all_words": round(100 * b["iep_occ"] / b["total_words"], 3) if b["total_words"] else 0.0,
            # unique types + concentration rate
            "unique_words": unique_words,
            "unique_iep_words": uniq_iep,
            "unique_iep_pct_of_unique_vocab": round(100 * uniq_iep / unique_words, 3) if unique_words else 0.0,
            # per-axis unique types
            "int_unique_words": len(b["int_types"]),
            "aff_unique_words": len(b["aff_types"]),
            "act_unique_words": len(b["act_types"]),
            # dictionary coverage (volume-sensitive; see --rarefy note)
            "int_dict_coverage_pct": round(100 * len(b["int_types"]) / DSIZE["INT"], 3),
            "aff_dict_coverage_pct": round(100 * len(b["aff_types"]) / DSIZE["AFF"], 3),
            "act_dict_coverage_pct": round(100 * len(b["act_types"]) / DSIZE["ACT"], 3),
            "total_dict_coverage_pct": round(100 * uniq_iep / sum(DSIZE.values()), 3),
        })
    return pd.DataFrame(rows).sort_values("agent").reset_index(drop=True)


# ---------------------------------------------------------------------------
# Optional: IEAP-restricted TF-IDF distinctive terms
# ---------------------------------------------------------------------------
def iep_tfidf(df, agent_col, text_col, LEX, top_n=15):
    from sklearn.feature_extraction.text import TfidfVectorizer
    INT, AFF, ACT, PRIORITY, _ = LEX
    lex = INT | AFF | ACT

    axis_of = {}
    for w in lex:
        if w in PRIORITY or w in INT:
            axis_of[w] = "INT"
        elif w in AFF:
            axis_of[w] = "AFF"
        elif w in ACT:
            axis_of[w] = "ACT"
    # priority resolution for words in multiple lists
    for w in INT:
        axis_of[w] = "INT"
    for w in PRIORITY:
        axis_of[w] = "INT"

    docs, agents = [], []
    for a, sub in df.groupby(agent_col):
        toks = []
        for t in sub[text_col]:
            toks.extend(w for w in tokenize(t) if w in lex)
        docs.append(" ".join(toks))
        agents.append(str(a))

    vocab = sorted(lex)
    vec = TfidfVectorizer(vocabulary=vocab, token_pattern=r"[a-z]+")
    X = vec.fit_transform(docs)
    terms = vec.get_feature_names_out()

    rows = []
    for i, a in enumerate(agents):
        row = X[i].toarray().ravel()
        order = row.argsort()[::-1]
        rank = 0
        for j in order:
            if row[j] <= 0:
                break
            rank += 1
            rows.append({
                "agent": a,
                "rank": rank,
                "term": terms[j],
                "axis": axis_of.get(terms[j], "?"),
                "tfidf": round(float(row[j]), 5),
            })
            if rank >= top_n:
                break
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Optional: dictionary-utilization heatmap
# ---------------------------------------------------------------------------
def make_heatmap(per_agent_df, out_png):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    axes = ["INT", "AFF", "ACT"]
    cols = ["int_dict_coverage_pct", "aff_dict_coverage_pct", "act_dict_coverage_pct"]
    agents = per_agent_df["agent"].tolist()
    M = per_agent_df[cols].to_numpy(dtype=float)

    fig, ax = plt.subplots(figsize=(1.6 + 1.1 * len(axes), 1.2 + 0.6 * len(agents)),
                           dpi=300)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    im = ax.imshow(M, aspect="auto", cmap="viridis")

    ax.set_xticks(range(len(axes)), axes)
    ax.set_yticks(range(len(agents)), agents)
    ax.set_xlabel("IEAP axis")
    ax.set_title("Dictionary utilization (% of sealed lexicon used)")

    for i in range(len(agents)):
        for j in range(len(axes)):
            val = M[i, j]
            ax.text(j, i, f"{val:.1f}", ha="center", va="center",
                    color="white" if val < M.max() * 0.6 else "black", fontsize=9)

    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("coverage %")
    fig.tight_layout()
    fig.savefig(out_png, dpi=300, facecolor="white", bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="IEAP Vocabulary Utilization Tool v1")
    ap.add_argument("--responses", required=True, help="response CSV")
    ap.add_argument("--dict", default=None, help="optional external lexicon (JSON/CSV); default = sealed V50_1897")
    ap.add_argument("--outdir", default="/mnt/user-data/outputs", help="output directory")
    ap.add_argument("--stem", default=None, help="output filename stem (default: from input)")
    ap.add_argument("--tfidf", action="store_true", help="also write IEAP-restricted TF-IDF distinctive terms")
    ap.add_argument("--tfidf-top", type=int, default=15, help="top N distinctive terms per agent")
    ap.add_argument("--heatmap", action="store_true", help="also write dictionary-utilization heatmap PNG")
    ap.add_argument("--core-dir", default="/mnt/project", help="dir containing syniq_core_v1_1_0.py")
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    stem = args.stem or os.path.splitext(os.path.basename(args.responses))[0]

    # Lexicon
    if args.dict:
        INT, AFF, ACT, PRIORITY = load_external_lexicon(args.dict)
        dict_version = f"external:{os.path.basename(args.dict)}"
    else:
        INT, AFF, ACT, PRIORITY = load_sealed_lexicon(args.core_dir)
        dict_version = IEP_DICTIONARY_VERSION
    DSIZE = {"INT": len(INT), "AFF": len(AFF), "ACT": len(ACT)}
    LEX = (INT, AFF, ACT, PRIORITY, DSIZE)
    print(f"[lexicon] {dict_version}  INT={DSIZE['INT']} AFF={DSIZE['AFF']} "
          f"ACT={DSIZE['ACT']} total={sum(DSIZE.values())}")

    # Data
    df = pd.read_csv(args.responses)
    agent_col, text_col, ques_col = detect_columns(df)
    df[agent_col] = df[agent_col].replace({"Sophia": "ChatGPT"})  # agent-naming rule
    df = df[df[text_col].notna()].copy()
    print(f"[data] rows={len(df)} agents={sorted(df[agent_col].unique())} "
          f"questions={sorted(df[ques_col].astype(str).unique())}")

    # Compute
    records, _ = build_records(df, agent_col, text_col, ques_col, LEX)
    summary = pd.DataFrame([{k: v for k, v in r.items() if not k.startswith("_")} for r in records])
    summary = summary.sort_values(["question", "agent"]).reset_index(drop=True)
    per_agent = per_agent_table(records, LEX)

    # Write core outputs
    summary_path = os.path.join(args.outdir, f"{stem}_summary.csv")
    per_agent_path = os.path.join(args.outdir, f"{stem}_per_agent.csv")
    summary.to_csv(summary_path, index=False)
    per_agent.to_csv(per_agent_path, index=False)
    written = [summary_path, per_agent_path]
    print(f"[write] {summary_path}  ({len(summary)} rows)")
    print(f"[write] {per_agent_path}  ({len(per_agent)} rows)")

    # Optional TF-IDF
    if args.tfidf:
        try:
            tf = iep_tfidf(df, agent_col, text_col, LEX, top_n=args.tfidf_top)
            tf_path = os.path.join(args.outdir, f"{stem}_tfidf.csv")
            tf.to_csv(tf_path, index=False)
            written.append(tf_path)
            print(f"[write] {tf_path}  ({len(tf)} rows)")
        except ImportError:
            print("[tfidf] scikit-learn not installed; skipping TF-IDF.")

    # Optional heatmap
    if args.heatmap:
        try:
            hm_path = os.path.join(args.outdir, f"{stem}_heatmap.png")
            make_heatmap(per_agent, hm_path)
            written.append(hm_path)
            print(f"[write] {hm_path}")
        except ImportError:
            print("[heatmap] matplotlib not installed; skipping heatmap.")

    print("\nDONE. Files:")
    for w in written:
        print("  " + w)


if __name__ == "__main__":
    main()
