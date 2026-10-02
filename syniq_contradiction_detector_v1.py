"""
SYN-IQ Contradiction Detector V1 (offline analyzer)

Reads a multi-agent session (Focus Group Lab CSV export, Focus Group Lab
session docx, or the December 2025 Ensemble Chat terminal transcript) and
measures contradiction at the claim level with a natural language inference
(NLI) model.

WHAT IT MEASURES
  1. Cross-agent contradiction. Within each round, every claim of every agent
     against every claim of every other agent.
  2. Self-reversal. Each agent turn against that agent's own previous turn.
     Scored as a REVERSAL only when the agent's previous turn was actually in
     its context. Stateless calls (the December 2025 Ensemble Chat) are
     reported as independent samples, never as reversals.
  3. Conductor adoption. For a turn that follows a conductor message: does
     the agent's text entail the conductor's assertion (adoption) or
     contradict it (pushback)?
  4. Grounding (optional, needs --source). Every claim against the source
     text. Flags claims the source contradicts, and flags rounds where two or
     more agents agree on a claim the source contradicts.
  5. Reversal type (heuristic, REQUIRES HUMAN VALIDATION):
       persuasion_candidate      reverses, refers back to its earlier view,
                                 and keeps some of its earlier content
       acknowledged_abandonment  reverses, refers back, keeps nothing
       silent_abandonment        reverses, no reference back, keeps nothing
       spontaneous_reversal      reverses with no conductor message before it

WHY NLI AND NOT EMBEDDINGS
  Embeddings measure topical similarity, so "she lives" and "she dies" sit
  close together. NLI labels a sentence pair as entailment, neutral or
  contradiction, which is the quantity Patent 1 Sec. 6 needs ("contradictory
  agent outputs are automatically detected").

SAFETY OF MODEL FILES
  The HF backend loads weights with use_safetensors=True, so pickle-format
  weights (which can execute code on load) are refused.

INSTALL (for the real model)
  pip install transformers torch sentencepiece protobuf python-docx pandas

USAGE
  python3 syniq_contradiction_detector_v1.py SESSION_FILE [--source LYRICS.docx]
      [--out results_dir] [--model cross-encoder/nli-deberta-v3-base]
      [--threshold 0.5] [--min-overlap 0] [--label-sample 100]

  --backend stub runs a crude word-overlap stand-in. It exists ONLY to test
  the pipeline without downloading a model. Never report stub numbers.

VALIDATION STATUS
  Unvalidated. Thresholds and the reversal heuristic must be checked against
  human labels (see label_sample_pairs.csv and label_sample_turns.csv) and
  frozen in the pre-registration before any result is reported.

SYNINT Team, October 2026
"""

import argparse
import itertools
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

TOOL_VERSION = "contradiction_detector_v1.1"
DEFAULT_MODEL = "cross-encoder/nli-deberta-v3-base"

# =============================================================================
# DATA
# =============================================================================

AGENT_ALIASES = {
    "claude": "Claude", "chatgpt": "ChatGPT", "sophia": "ChatGPT",
    "sophia (openai)": "ChatGPT", "grok": "Grok", "gemini": "Gemini",
}


@dataclass
class Turn:
    turn_id: int
    round: int
    agent: str
    text: str
    is_error: bool = False
    # True when this agent's own previous turn was in the context of this call.
    own_prior_in_context: bool = False
    # True when this call could see other agents' responses.
    sees_others: bool = False
    # The conductor message immediately before this turn's round, if any.
    conductor_before: str = ""
    claims: List[str] = field(default_factory=list)


# =============================================================================
# PARSERS
# =============================================================================

def read_docx_lines(path: str) -> List[str]:
    import docx  # python-docx
    d = docx.Document(path)
    return [p.text.replace("\xa0", " ") for p in d.paragraphs]


def is_error_text(t: str) -> bool:
    s = t.strip()
    return (not s) or s.startswith("❌") or s.startswith("[GROK ERROR") \
        or bool(re.match(r"^\[\w+ ERROR", s))


# ---- December 2025 Ensemble Chat terminal transcript ------------------------
ENSEMBLE_HEADER = re.compile(r"^(GROK|CLAUDE|SOPHIA(?: \(OpenAI\))?):\s*$")
ENSEMBLE_CMD = re.compile(r"^You\s*>\s*(\S+)\s*(.*)$")
CMD_TARGETS = {"g": ["Grok"], "c": ["Claude"], "s": ["ChatGPT"],
               "all": ["Grok", "Claude", "ChatGPT"]}


def parse_ensemble_terminal(lines: List[str]) -> List[Turn]:
    """Each 'You >' command is one round. Every call was STATELESS: the script
    sent only the current message, so no agent ever saw its own prior turn or
    another agent's response, except where the conductor pasted it in."""
    turns: List[Turn] = []
    rnd, conductor_msg = 0, ""
    cur_agent, buf = None, []

    def flush():
        nonlocal cur_agent, buf
        if cur_agent is not None:
            text = "\n".join(buf).strip()
            turns.append(Turn(len(turns) + 1, rnd, cur_agent, text,
                              is_error=is_error_text(text),
                              own_prior_in_context=False, sees_others=False,
                              conductor_before=conductor_msg))
        cur_agent, buf = None, []

    for raw in lines:
        line = raw.rstrip()
        m = ENSEMBLE_CMD.match(line.strip())
        if m:
            flush()
            cmd, msg = m.group(1).lower(), m.group(2)
            if cmd in CMD_TARGETS:
                rnd += 1
                conductor_msg = msg.strip()
            continue
        h = ENSEMBLE_HEADER.match(line.strip())
        if h:
            flush()
            cur_agent = AGENT_ALIASES[h.group(1).lower()]
            continue
        if re.match(r"^[=\-]{10,}$", line.strip()):
            continue
        if line.strip().startswith("Unknown command"):
            continue
        if cur_agent is not None:
            buf.append(line)
    flush()
    return turns


AGENT_ORDER = {"Claude": 0, "ChatGPT": 1, "Grok": 2, "Gemini": 3}

# ---- Focus Group Lab session docx -------------------------------------------
FG_HEADER = re.compile(r"^(?:\S+\s+)?(Claude|ChatGPT|Grok|Gemini|Conductor):\s*(.*)$")
BADGE_LINES = [
    re.compile(r"^IEP:"), re.compile(r"^(INT|AFF|ACT)$"), re.compile(r"^\d+(\.\d+)?%$"),
    re.compile(r"V̂ₜ|V_t|Vₜ"), re.compile(r"^[a-z_]+:\d+%"),
]


def _is_badge(line: str) -> bool:
    s = line.strip()
    return any(p.search(s) for p in BADGE_LINES)


def parse_focus_group_docx(lines: List[str]) -> List[Turn]:
    """Live Discussion transcript. Every call saw the whole thread, so each
    agent saw its own prior turns and the other agents. A new round starts at
    a conductor message, or when an agent appears twice without one.
    Text before the first header is kept as agent UNLABELED."""
    turns: List[Turn] = []
    rnd, seen, conductor_msg = 1, {"UNLABELED"}, ""
    cur_agent, buf, last_idx = "UNLABELED", [], -1

    def flush():
        nonlocal buf
        text = "\n".join(b for b in buf if not _is_badge(b)).strip()
        if text and cur_agent:
            turns.append(Turn(len(turns) + 1, rnd, cur_agent, text,
                              is_error=is_error_text(text),
                              own_prior_in_context=True, sees_others=True,
                              conductor_before=conductor_msg))
        buf = []

    for raw in lines:
        line = raw.rstrip()
        h = FG_HEADER.match(line.strip())
        if h:
            flush()
            who, rest = h.group(1), h.group(2)
            if who == "Conductor":
                rnd += 1
                seen, last_idx = set(), -1
                conductor_msg = rest.strip()
                cur_agent = None
                continue
            # Same agent header repeated with nothing in between (an empty
            # header line in the export): continue the same turn.
            if who == cur_agent and not any(b.strip() and not _is_badge(b) for b in buf):
                if rest.strip():
                    buf.append(rest)
                continue
            # Rounds run in panel order (Claude, ChatGPT, Grok, Gemini). An
            # agent at or before the previous agent's position starts a new
            # round. Directed single-agent turns can break this; check rounds
            # in turns.csv against the session if directed turns were used.
            idx = AGENT_ORDER.get(who, 99)
            if seen and idx <= last_idx:
                rnd += 1
                seen = set()
                conductor_msg = ""
            seen.add(who)
            last_idx = idx
            cur_agent = who
            if rest.strip():
                buf.append(rest)
            continue
        if cur_agent is not None:
            buf.append(line)
    flush()
    return turns


# ---- Session script CSV (clean, hand-checkable format) ----------------------
# Columns: round, speaker, text, and optionally context.
#   speaker  Claude | ChatGPT | Grok | Gemini | Conductor
#   context  visible   = the call saw the whole thread (Live Discussion)
#            stateless = the call saw only the current message (Dec 2025 script)
# One row per turn, in the order spoken. A Conductor row applies to the turns
# that follow it in the same or next round.
def parse_script_csv(df) -> List[Turn]:
    import pandas as pd
    turns: List[Turn] = []
    conductor_msg, cond_round = "", None
    for _, r in df.iterrows():
        spk = str(r["speaker"]).strip()
        text = "" if pd.isna(r["text"]) else str(r["text"])
        rnd = int(r["round"])
        if spk.lower() == "conductor":
            conductor_msg, cond_round = text.strip(), rnd
            continue
        if cond_round is not None and rnd != cond_round:
            conductor_msg, cond_round = "", None
        ctx = str(r.get("context", "visible")).strip().lower()
        vis = ctx != "stateless"
        turns.append(Turn(len(turns) + 1, rnd, AGENT_ALIASES.get(spk.lower(), spk), text,
                          is_error=is_error_text(text), own_prior_in_context=vis,
                          sees_others=vis, conductor_before=conductor_msg))
    return turns


# ---- Focus Group Lab CSV export ---------------------------------------------
def parse_csv(path: str) -> List[Turn]:
    """Auto Run rows: independent single-round calls (solo, stateless).
    Live Discussion rows (session_framing == multi_visible): full thread
    visible. NOTE: the V44.2 live export omits conductor rows, so conductor
    adoption cannot be computed from a live CSV."""
    import pandas as pd
    df = pd.read_csv(path)
    if {"round", "speaker", "text"} <= set(df.columns):
        return parse_script_csv(df)
    if "response_text" not in df.columns or "agent" not in df.columns:
        raise ValueError("CSV needs 'agent' and 'response_text' columns.")
    visible = ("session_framing" in df.columns and
               (df["session_framing"].astype(str) == "multi_visible").any())
    if "round" in df.columns:
        rcol = "round"
    elif "run" in df.columns:
        rcol = "run"
    else:
        rcol = None
    turns = []
    for i, r in df.iterrows():
        text = str(r["response_text"]) if not pd.isna(r["response_text"]) else ""
        if "TRUNCATED AT TOKEN CAP" in text:
            text = text.split("\n\n⚠️ [TRUNCATED AT TOKEN CAP")[0]
        e = r.get("error", False)
        err = is_error_text(text) or (str(e).strip().lower() == "true")
        turns.append(Turn(len(turns) + 1, int(r[rcol]) if rcol else 1,
                          str(r["agent"]), text, is_error=err,
                          own_prior_in_context=bool(visible),
                          sees_others=bool(visible)))
    return turns


def load_session(path: str) -> Tuple[List[Turn], str]:
    if path.lower().endswith(".csv"):
        return parse_csv(path), "focus_group_csv"
    lines = read_docx_lines(path) if path.lower().endswith(".docx") else \
        open(path, encoding="utf-8").read().splitlines()
    if any(ENSEMBLE_CMD.match(l.strip()) for l in lines):
        return parse_ensemble_terminal(lines), "ensemble_terminal_dec2025"
    return parse_focus_group_docx(lines), "focus_group_docx"


def load_source(path: str) -> List[str]:
    """Source text as premises: single lines plus two-line windows, because a
    claim often depends on two adjacent lines together."""
    lines = read_docx_lines(path) if path.lower().endswith(".docx") else \
        open(path, encoding="utf-8").read().splitlines()
    lines = [part.strip() for line in lines for part in line.split("\n")]
    lines = [l for l in lines if len(l.split()) >= 3]
    windows = [f"{a} {b}" for a, b in zip(lines, lines[1:])]
    return lines + windows


# =============================================================================
# CLAIM SPLITTING
# =============================================================================

MD = re.compile(r"(\*\*|__|`|^#+\s*|^\s*[-*•]\s+|^\s*\d+\.\s+)")
SENT_SPLIT = re.compile(r"(?<=[.!?])[\"”’)]?\s+(?=[A-Z\"“(])")


def split_claims(text: str) -> List[str]:
    """A claim is a declarative sentence of 6+ words. Questions are dropped
    (they assert nothing). Short unpunctuated lines are treated as headings."""
    claims = []
    for para in text.split("\n"):
        p = MD.sub("", para.strip()).strip()
        if not p:
            continue
        for s in SENT_SPLIT.split(p):
            s = s.strip()
            n = len(s.split())
            if n < 6 or s.endswith("?"):
                continue
            if not re.search(r"[.!;]$", s.rstrip("\"”’')")):
                words = re.findall(r"[A-Za-z][\w'’]*", s)
                caps = sum(w[0].isupper() for w in words) / max(1, len(words))
                if n < 8 or caps > 0.6:
                    continue  # heading or title line
            claims.append(s[:600])
    return claims


STOP = set("""a an the and or but if of to in on at by for with from as is are was
were be been being it its this that these those she he her his they them their
i you we our your my me not no so do does did can could would should will may
might must just very really than then there here what which who whom how when
where why all any some each more most such only also into about over""".split())


def content_words(s: str) -> set:
    return {w for w in re.findall(r"[a-z]+", s.lower()) if w not in STOP and len(w) > 2}


# =============================================================================
# NLI BACKENDS
# =============================================================================

class HFBackend:
    """Hugging Face sequence-classification NLI model. Label order is read from
    the model config, never assumed."""

    def __init__(self, model_name: str, batch_size: int = 16):
        import torch
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        self.torch = torch
        self.name = model_name
        self.tok = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            model_name, use_safetensors=True)
        self.model.eval()
        self.device = "cuda" if torch.cuda.is_available() else (
            "mps" if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available() else "cpu")
        self.model.to(self.device)
        self.bs = batch_size
        id2label = {int(k): v.lower() for k, v in self.model.config.id2label.items()}
        self.idx = {}
        for i, lab in id2label.items():
            for key in ("contradiction", "entailment", "neutral"):
                if key in lab:
                    self.idx[key] = i
        if set(self.idx) != {"contradiction", "entailment", "neutral"}:
            raise ValueError(f"Model labels not recognized as NLI: {id2label}")

    def predict(self, pairs: List[Tuple[str, str]]) -> List[Dict[str, float]]:
        out = []
        for i in range(0, len(pairs), self.bs):
            chunk = pairs[i:i + self.bs]
            enc = self.tok([p for p, _ in chunk], [h for _, h in chunk],
                           padding=True, truncation=True, max_length=512,
                           return_tensors="pt").to(self.device)
            with self.torch.no_grad():
                probs = self.torch.softmax(self.model(**enc).logits, dim=-1).cpu().tolist()
            for pr in probs:
                out.append({k: pr[v] for k, v in self.idx.items()})
        return out


class StubBackend:
    """TEST ONLY. Word-overlap plus negation/antonym heuristic so the pipeline
    can run without a model. Its numbers mean nothing."""
    name = "stub_TEST_ONLY"
    ANTONYMS = [({"live", "lives", "survive", "survives", "survival", "alive"},
                 {"die", "dies", "died", "death", "dead"}),
                ({"stop", "stopped", "stops"}, {"kept", "going", "passed"})]
    NEG = re.compile(r"\b(not|no|never|didn't|doesn't|isn't|wasn't|n't)\b")

    def predict(self, pairs):
        out = []
        for p, h in pairs:
            a, b = content_words(p), content_words(h)
            ov = len(a & b) / max(1, min(len(a), len(b)))
            contra = 0.05
            for x, y in self.ANTONYMS:
                if (a & x and b & y) or (a & y and b & x):
                    contra = 0.8
            if ov > 0.3 and bool(self.NEG.search(p.lower())) != bool(self.NEG.search(h.lower())):
                contra = max(contra, 0.7)
            ent = min(0.9, ov) if contra < 0.5 else 0.05
            neu = max(0.0, 1 - contra - ent)
            out.append({"contradiction": contra, "entailment": ent, "neutral": neu})
        return out


class CachedScorer:
    """Scores premise/hypothesis pairs once each and caches the result."""

    def __init__(self, backend, on_progress=None):
        self.b = backend
        self.cache: Dict[Tuple[str, str], Dict[str, float]] = {}
        self.on_progress = on_progress   # optional callback(n_evaluated)

    def score(self, pairs: List[Tuple[str, str]]):
        todo = list({p for p in pairs if p not in self.cache})
        if todo:
            for p, r in zip(todo, self.b.predict(todo)):
                self.cache[p] = r
            if self.on_progress:
                self.on_progress(len(self.cache))
        return [self.cache[p] for p in pairs]


def label_of(r: Dict[str, float]) -> str:
    return max(r, key=r.get)


# =============================================================================
# ANALYSES
# =============================================================================

REFERS_BACK = re.compile(
    r"\b(earlier|previously|my previous|my earlier|my first|i said|i argued|"
    r"i initially|initially|at first|i was wrong|i overlooked|my analysis|"
    r"my reading|changes my|revise|revising|reconsider|update my|i still)\b", re.I)


def symmetric_pairs(A: List[str], B: List[str], min_overlap: int):
    """All (a, b) claim pairs, optionally pre-filtered by shared content words
    (a compute shortcut that can miss paraphrased contradictions)."""
    for a, b in itertools.product(A, B):
        if min_overlap and len(content_words(a) & content_words(b)) < min_overlap:
            continue
        yield a, b


def score_symmetric(scorer, pairs):
    """Contradiction is taken as the max over both directions. Entailment is
    kept per direction because it is not symmetric."""
    fwd = scorer.score(pairs)
    bwd = scorer.score([(b, a) for a, b in pairs])
    rows = []
    for (a, b), f, r in zip(pairs, fwd, bwd):
        rows.append({"claim_a": a, "claim_b": b,
                     "p_contra": round(max(f["contradiction"], r["contradiction"]), 4),
                     "p_entail_a_to_b": round(f["entailment"], 4),
                     "p_entail_b_to_a": round(r["entailment"], 4)})
    return rows


def parse_rounds(spec: Optional[str]) -> Optional[set]:
    """'10-22' or '3,5,7-9' -> set of round numbers. None means all rounds."""
    if not spec:
        return None
    out = set()
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-")
            out.update(range(int(a), int(b) + 1))
        elif part:
            out.add(int(part))
    return out


def analyze(turns: List[Turn], scorer, source: Optional[List[str]],
            thr: float, min_overlap: int, source_rounds: Optional[set] = None):
    live = [t for t in turns if not t.is_error]
    for t in live:
        t.claims = split_claims(t.text)

    by_round: Dict[int, List[Turn]] = {}
    for t in live:
        by_round.setdefault(t.round, []).append(t)

    # 1. cross-agent, within round
    cross_rows = []
    for rnd, ts in sorted(by_round.items()):
        for t1, t2 in itertools.combinations(ts, 2):
            if t1.agent == t2.agent:
                continue
            pairs = list(symmetric_pairs(t1.claims, t2.claims, min_overlap))
            for row in score_symmetric(scorer, pairs):
                row.update({"round": rnd, "turn_a": t1.turn_id, "agent_a": t1.agent,
                            "turn_b": t2.turn_id, "agent_b": t2.agent})
                cross_rows.append(row)

    # 2. self-reversal, each turn against the same agent's previous turn
    self_rows, turn_rows = [], []
    last_by_agent: Dict[str, Turn] = {}
    for t in live:
        prev = last_by_agent.get(t.agent)
        rec = {"turn_id": t.turn_id, "round": t.round, "agent": t.agent,
               "n_claims": len(t.claims), "own_prior_in_context": t.own_prior_in_context,
               "sees_others": t.sees_others,
               "conductor_before": t.conductor_before[:300]}
        if prev is not None and prev.claims and t.claims:
            pairs = list(symmetric_pairs(prev.claims, t.claims, min_overlap))
            rows = score_symmetric(scorer, pairs)
            for row in rows:
                row.update({"agent": t.agent, "prior_turn": prev.turn_id,
                            "turn": t.turn_id,
                            "comparison": "reversal" if t.own_prior_in_context
                            else "independent_sample"})
            self_rows.extend(rows)
            n_c = sum(r["p_contra"] >= thr for r in rows)
            # prior claims still present: some current claim entails them
            retained = 0
            for pc in prev.claims:
                if any(r["claim_a"] == pc and r["p_entail_b_to_a"] >= thr for r in rows):
                    retained += 1
            rec.update({
                "prior_turn": prev.turn_id,
                "self_max_p_contra": max((r["p_contra"] for r in rows), default=0.0),
                "self_n_contra_pairs": n_c,
                "prior_claims_retained_frac": round(retained / len(prev.claims), 3),
                "refers_back": bool(REFERS_BACK.search(t.text)),
                "reversal": bool(t.own_prior_in_context and n_c > 0),
                "independent_disagreement": bool((not t.own_prior_in_context) and n_c > 0),
            })
        turn_rows.append(rec)
        last_by_agent[t.agent] = t

    # 3. conductor adoption
    cond_rows = []
    for t, rec in zip(live, turn_rows):
        cclaims = split_claims(t.conductor_before) or (
            [t.conductor_before] if len(t.conductor_before.split()) >= 4 else [])
        if not cclaims or not t.claims:
            continue
        adopted, pushed = 0, 0
        for cc in cclaims:
            ent = scorer.score([(ac, cc) for ac in t.claims])        # agent entails conductor
            con = score_symmetric(scorer, [(cc, ac) for ac in t.claims])
            if max(e["entailment"] for e in ent) >= thr:
                adopted += 1
            if max(c["p_contra"] for c in con) >= thr:
                pushed += 1
        rec.update({"conductor_claims": len(cclaims),
                    "conductor_adopted_frac": round(adopted / len(cclaims), 3),
                    "conductor_contradicted_frac": round(pushed / len(cclaims), 3)})
        cond_rows.append({"turn_id": t.turn_id, "agent": t.agent,
                          "conductor_before": t.conductor_before,
                          "adopted_frac": rec["conductor_adopted_frac"],
                          "contradicted_frac": rec["conductor_contradicted_frac"]})

    # 5. reversal type (heuristic)
    for rec in turn_rows:
        if not rec.get("reversal"):
            rec["reversal_type"] = ""
            continue
        if not rec["conductor_before"]:
            rec["reversal_type"] = "spontaneous_reversal"
        elif rec["prior_claims_retained_frac"] > 0 and rec["refers_back"]:
            rec["reversal_type"] = "persuasion_candidate"
        elif rec["refers_back"]:
            rec["reversal_type"] = "acknowledged_abandonment"
        else:
            rec["reversal_type"] = "silent_abandonment"

    # 4. grounding
    ground_rows, shared_false = [], []
    if source:
        false_claims: Dict[int, List[Tuple[str, str]]] = {}
        for t, rec in zip(live, turn_rows):
            # Ground only rounds about the source text (a session can cover
            # several songs or questions; see --source-rounds).
            if source_rounds is not None and t.round not in source_rounds:
                continue
            n_false = n_sup = 0
            for c in t.claims:
                res = scorer.score([(s, c) for s in source])   # source as premise
                pc = max(r["contradiction"] for r in res)
                pe = max(r["entailment"] for r in res)
                best = source[max(range(len(res)), key=lambda i: res[i]["contradiction"])]
                if pc >= thr:
                    n_false += 1
                    false_claims.setdefault(t.round, []).append((t.agent, c))
                if pe >= thr:
                    n_sup += 1
                ground_rows.append({"turn_id": t.turn_id, "round": t.round, "agent": t.agent,
                                    "claim": c, "p_contra_by_source": round(pc, 4),
                                    "p_supported_by_source": round(pe, 4),
                                    "most_contradicting_source_line": best})
            rec["claims_contradicted_by_source"] = n_false
            rec["claims_supported_by_source"] = n_sup
        # agreement on a false claim: two agents' source-contradicted claims entail each other
        for rnd, fc in false_claims.items():
            for (ag1, c1), (ag2, c2) in itertools.combinations(fc, 2):
                if ag1 == ag2:
                    continue
                r = score_symmetric(scorer, [(c1, c2)])[0]
                if max(r["p_entail_a_to_b"], r["p_entail_b_to_a"]) >= thr:
                    shared_false.append({"round": rnd, "agent_a": ag1, "claim_a": c1,
                                         "agent_b": ag2, "claim_b": c2})
    return live, cross_rows, self_rows, turn_rows, cond_rows, ground_rows, shared_false


# =============================================================================
# OUTPUT
# =============================================================================

def label_samples(cross_rows, self_rows, turn_rows, n, thr, seed=7):
    """Stratified sample for HUMAN labeling. Contradiction predictions are
    oversampled because they are rare and are what the accuracy figure is about."""
    rng = random.Random(seed)
    allp = ([dict(r, kind="cross_agent") for r in cross_rows] +
            [dict(r, kind=r["comparison"]) for r in self_rows])
    for r in allp:
        r["predicted"] = "contradiction" if r["p_contra"] >= thr else (
            "entailment" if max(r["p_entail_a_to_b"], r["p_entail_b_to_a"]) >= thr else "neutral")
    strata = {"contradiction": 0.4, "entailment": 0.3, "neutral": 0.3}
    out = []
    for lab, frac in strata.items():
        pool = [r for r in allp if r["predicted"] == lab]
        rng.shuffle(pool)
        out.extend(pool[:int(round(n * frac))])
    pair_rows = [{"sample_id": i + 1, "kind": r["kind"],
                  "agent_a": r.get("agent_a", r.get("agent", "")),
                  "claim_a": r["claim_a"],
                  "agent_b": r.get("agent_b", r.get("agent", "")),
                  "claim_b": r["claim_b"],
                  "predicted": r["predicted"], "p_contra": r["p_contra"],
                  "human_label": "", "notes": ""} for i, r in enumerate(out)]
    turn_lab = [{"turn_id": r["turn_id"], "agent": r["agent"],
                 "predicted_reversal_type": r.get("reversal_type", ""),
                 "conductor_before": r["conductor_before"],
                 "human_reversal_type": "", "notes": ""}
                for r in turn_rows if r.get("reversal") or r.get("independent_disagreement")]
    return pair_rows, turn_lab


def write_outputs(out_dir, meta, live, cross, selfp, turns, cond, ground, shared, lab_n, thr):
    import pandas as pd
    os.makedirs(out_dir, exist_ok=True)
    pd.DataFrame(turns).to_csv(os.path.join(out_dir, "turns.csv"), index=False)
    pd.DataFrame(cross).to_csv(os.path.join(out_dir, "pairs_cross_agent.csv"), index=False)
    pd.DataFrame(selfp).to_csv(os.path.join(out_dir, "pairs_self.csv"), index=False)
    if cond:
        pd.DataFrame(cond).to_csv(os.path.join(out_dir, "conductor_adoption.csv"), index=False)
    if ground:
        pd.DataFrame(ground).to_csv(os.path.join(out_dir, "grounding.csv"), index=False)
        pd.DataFrame(shared).to_csv(os.path.join(out_dir, "shared_false_claims.csv"), index=False)
    lp, lt = label_samples(cross, selfp, turns, lab_n, thr)
    pd.DataFrame(lp).to_csv(os.path.join(out_dir, "label_sample_pairs.csv"), index=False)
    pd.DataFrame(lt).to_csv(os.path.join(out_dir, "label_sample_turns.csv"), index=False)
    with open(os.path.join(out_dir, "run_meta.json"), "w") as f:
        json.dump(meta, f, indent=2)

    # summary
    L = [f"# Contradiction Detector Summary", "",
         f"- Session: {meta['session_file']} ({meta['session_format']})",
         f"- Backend: {meta['backend']}" + ("  **(TEST ONLY: numbers are meaningless)**"
                                             if "stub" in meta["backend"] else ""),
         f"- Threshold: {thr}   Min overlap prefilter: {meta['min_overlap']}",
         f"- Turns analysed: {len(live)} (errors excluded: {meta['n_error_turns']})",
         f"- Claims: {sum(len(t.claims) for t in live)}", ""]
    L.append("## Cross-agent contradiction by round")
    rounds = sorted({r["round"] for r in cross})
    for rnd in rounds:
        rr = [r for r in cross if r["round"] == rnd]
        n_c = sum(r["p_contra"] >= thr for r in rr)
        L.append(f"- Round {rnd}: {n_c} of {len(rr)} claim pairs contradict "
                 f"({100 * n_c / max(1, len(rr)):.1f}%)")
    L.append("")
    L.append("## Turns (self comparison, conductor, grounding)")
    for r in turns:
        bits = [f"T{r['turn_id']} R{r['round']} {r['agent']}"]
        if "prior_turn" in r:
            kind = "REVERSAL" if r.get("reversal") else (
                "independent disagreement" if r.get("independent_disagreement") else "consistent")
            bits.append(f"vs T{r['prior_turn']}: {kind} ({r['self_n_contra_pairs']} pairs)")
            if r.get("reversal_type"):
                bits.append(r["reversal_type"])
        if "conductor_adopted_frac" in r:
            bits.append(f"adopts conductor {r['conductor_adopted_frac']:.0%}, "
                        f"contradicts conductor {r['conductor_contradicted_frac']:.0%}")
        if "claims_contradicted_by_source" in r:
            bits.append(f"source-contradicted claims: {r['claims_contradicted_by_source']}")
        L.append("- " + "; ".join(bits))
    if shared:
        L += ["", "## Agreement on claims the source contradicts"]
        for s in shared:
            L.append(f"- R{s['round']}: {s['agent_a']} and {s['agent_b']} agree on: "
                     f"\"{s['claim_a'][:140]}\"")
    L += ["", "## Validation status",
          "Unvalidated. Label label_sample_pairs.csv and label_sample_turns.csv, then "
          "compute accuracy before reporting any figure. Reversal types are heuristic."]
    with open(os.path.join(out_dir, "summary.md"), "w") as f:
        f.write("\n".join(L) + "\n")
    return os.path.join(out_dir, "summary.md")


def main(argv=None):
    ap = argparse.ArgumentParser(description="SYN-IQ claim-level contradiction detector")
    ap.add_argument("session")
    ap.add_argument("--source", help="source text (docx/txt) for grounding")
    ap.add_argument("--out", default=None)
    ap.add_argument("--backend", choices=["hf", "stub"], default="hf")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--threshold", type=float, default=0.5)
    ap.add_argument("--source-rounds", default=None,
                    help="rounds the source applies to, e.g. '10-22' (default: all)")
    ap.add_argument("--min-overlap", type=int, default=0,
                    help="skip claim pairs sharing fewer content words (0 = score all)")
    ap.add_argument("--label-sample", type=int, default=100)
    a = ap.parse_args(argv)

    turns, fmt = load_session(a.session)
    source = load_source(a.source) if a.source else None
    backend = StubBackend() if a.backend == "stub" else HFBackend(a.model)
    scorer = CachedScorer(backend)
    print(f"Parsed {len(turns)} turns ({fmt}); scoring with {backend.name} ...")
    live, cross, selfp, trows, cond, ground, shared = analyze(
        turns, scorer, source, a.threshold, a.min_overlap, parse_rounds(a.source_rounds))
    meta = {"tool_version": TOOL_VERSION, "session_file": os.path.basename(a.session),
            "session_format": fmt, "source_file": os.path.basename(a.source) if a.source else None,
            "source_rounds": a.source_rounds,
            "backend": backend.name, "threshold": a.threshold, "min_overlap": a.min_overlap,
            "n_turns": len(turns), "n_error_turns": len(turns) - len(live),
            "n_nli_calls": len(scorer.cache),
            "run_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    out = a.out or os.path.splitext(os.path.basename(a.session))[0] + "_contradiction"
    path = write_outputs(out, meta, live, cross, selfp, trows, cond, ground, shared,
                         a.label_sample, a.threshold)
    print(f"Done. {len(scorer.cache)} NLI evaluations. Summary: {path}")


if __name__ == "__main__":
    main()
