#!/usr/bin/env python3
"""
syniq_word_list.py — per-agent distinctive word lists from a pooled response CSV.

Purpose
-------
Given a pooled response CSV, output the words that most distinguish each AI agent
on a given question — the "driving words" behind the word-cloud / TF-IDF
separation. This is the DATA behind the clouds, not the cloud image.

Input columns (minimum): agent, question_id, temperature, response_text

CLI
---
    python syniq_word_list.py --csv PATH --question CONSCIOUSNESS --temp NATIVE \
           --mode distinctive --topn 20 --out words.csv

    --csv            (required) input path
    --question       (required unless --all-questions) a question_id value
    --temp           (default NATIVE) a temperature value
    --mode           (default distinctive) 'distinctive' or 'raw'
    --topn           (default 20) words per agent
    --out            (optional) output CSV path; if omitted, just print
    --all-questions  (flag) ignore --question, run every question_id, one combined output

Output CSV columns: question_id, temperature, agent, rank, word, score
    (score = TF-IDF weight in distinctive mode, count in raw mode)

Non-goals: no plotting, no clouds, no Mapper integration. Word lists in -> CSV out.

Version: 1.0.0
"""

import argparse
import sys
import csv

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer

# ---------------------------------------------------------------------------
AGENT_ORDER = ["ChatGPT", "Claude", "Gemini", "Grok"]
# contraction fragments / junk to drop from final lists (same as cloud aggregator)
JUNK = {"m", "s", "t", "re", "ve", "ll", "d"}
TOKEN_PATTERN = r"[A-Za-z][A-Za-z']+"

REQUIRED_COLS = ["agent", "question_id", "temperature", "response_text"]


def order_agents(present):
    """Fixed order ChatGPT/Claude/Gemini/Grok, then any extras alphabetically."""
    head = [a for a in AGENT_ORDER if a in present]
    tail = sorted(a for a in present if a not in AGENT_ORDER)
    return head + tail


def clean_pick(scores, vocab, topn):
    """Return up to topn (word, score) pairs, descending, dropping junk/short tokens
    and zero-score terms."""
    out = []
    for j in np.argsort(scores)[::-1]:
        sc = float(scores[j])
        if sc <= 0:
            break
        w = vocab[j]
        if len(w) < 2 or w in JUNK:
            continue
        out.append((w, sc))
        if len(out) >= topn:
            break
    return out


def build_agent_docs(cell, ordered_agents):
    """Concatenate response_text per agent into one document each.
    Returns (docs_present, agents_present, no_response_agents)."""
    docs_present, agents_present, no_response = [], [], []
    for a in ordered_agents:
        texts = cell.loc[cell["agent"] == a, "response_text"].dropna().astype(str)
        joined = " ".join(t for t in texts if t.strip())
        if joined.strip():
            docs_present.append(joined)
            agents_present.append(a)
        else:
            no_response.append(a)
    return docs_present, agents_present, no_response


def run_distinctive(docs, agents, topn):
    """TF-IDF across the agent-documents; per agent take top-scoring terms."""
    vec = TfidfVectorizer(
        max_features=4000,
        stop_words="english",
        token_pattern=TOKEN_PATTERN,
        min_df=1,
        max_df=1.0,
        sublinear_tf=True,
    )
    X = vec.fit_transform(docs).toarray()
    vocab = np.array(vec.get_feature_names_out())
    results = {}
    for i, a in enumerate(agents):
        results[a] = clean_pick(X[i], vocab, topn)
    return results


def run_raw(docs, agents, topn):
    """Per-agent raw word frequency (same tokenizer, stopwords removed), top-N by count."""
    vec = CountVectorizer(
        stop_words="english",
        token_pattern=TOKEN_PATTERN,
        min_df=1,
        max_df=1.0,
    )
    X = vec.fit_transform(docs).toarray()
    vocab = np.array(vec.get_feature_names_out())
    results = {}
    for i, a in enumerate(agents):
        results[a] = clean_pick(X[i].astype(float), vocab, topn)
    return results


def process_cell(df, question, temp, mode, topn, universe):
    """Process one question x temp cell. Returns (rows, lines, ok).
    `universe` is the fixed-ordered list of expected agents (from the whole file),
    so an agent absent from this cell is reported as (no responses)."""
    cell = df[(df["question_id"] == question) & (df["temperature"] == temp)]
    if cell.empty:
        return [], [f"[{question} / {temp}] no rows for this question x temperature cell."], False

    ordered = universe
    docs, agents, no_response = build_agent_docs(cell, ordered)

    lines = [f"=== {question} / {temp} ({mode}) ==="]
    if len(agents) < 2:
        lines.append("  NOTE: fewer than 2 agents with text present — comparison is degenerate.")

    rows = []
    if agents:
        if mode == "distinctive":
            results = run_distinctive(docs, agents, topn)
        else:
            results = run_raw(docs, agents, topn)
    else:
        results = {}

    # emit in fixed order, including no-response agents
    for a in ordered:
        if a in no_response:
            lines.append(f"  {a}: (no responses)")
            continue
        pairs = results.get(a, [])
        words = ", ".join(w for w, _ in pairs)
        lines.append(f"  {a}: {words}")
        for rank, (w, sc) in enumerate(pairs, start=1):
            rows.append({
                "question_id": question,
                "temperature": temp,
                "agent": a,
                "rank": rank,
                "word": w,
                "score": round(sc, 6),
            })
    return rows, lines, True


def write_csv(rows, path):
    cols = ["question_id", "temperature", "agent", "rank", "word", "score"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser(description="Per-agent distinctive word lists from a pooled response CSV.")
    ap.add_argument("--csv", required=True, help="input CSV path")
    ap.add_argument("--question", help="a question_id value (required unless --all-questions)")
    ap.add_argument("--temp", default="NATIVE", help="a temperature value (default NATIVE)")
    ap.add_argument("--mode", default="distinctive", choices=["distinctive", "raw"])
    ap.add_argument("--topn", type=int, default=20, help="words per agent")
    ap.add_argument("--out", help="output CSV path; if omitted, just print")
    ap.add_argument("--all-questions", action="store_true",
                    help="ignore --question, run every question_id, write one combined output")
    args = ap.parse_args()

    try:
        df = pd.read_csv(args.csv)
    except Exception as e:
        print(f"ERROR reading {args.csv}: {e}")
        sys.exit(1)

    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        print(f"ERROR: input missing required columns: {missing}")
        sys.exit(1)

    if not args.all_questions and not args.question:
        print("ERROR: --question is required unless --all-questions is set.")
        sys.exit(1)

    if args.all_questions:
        questions = sorted(df["question_id"].dropna().unique())
    else:
        questions = [args.question]

    universe = order_agents(list(df["agent"].dropna().unique()))

    all_rows, any_ok = [], False
    for q in questions:
        rows, lines, ok = process_cell(df, q, args.temp, args.mode, args.topn, universe)
        print("\n".join(lines))
        print()
        if ok:
            any_ok = True
            all_rows.extend(rows)

    if not any_ok:
        # single-cell empty case: fail clearly, don't write an empty CSV
        sys.exit(2)

    if args.out:
        write_csv(all_rows, args.out)
        print(f"Wrote {len(all_rows)} rows -> {args.out}")


if __name__ == "__main__":
    main()
