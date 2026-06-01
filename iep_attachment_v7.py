#!/usr/bin/env python3
"""
iep_attachment_v7.py — parallel act-corrected IEP for SYN-IQ baseline (V56)
===========================================================================

NON-INVASIVE add-on. V56's word-only IEP (int_pct/aff_pct/act_pct) is NOT
touched. This module returns extra columns the baseline pastes into its row.

ARCHITECTURE (act_detector_v7, co-authored by the panel + conductor)
--------------------------------------------------------------------
Per paragraph:
  1. soft posture distribution (top-down prior, NOT a single winner)
  2. local evidence (bottom-up: definitional/intellectual -> INT;
     1st-person+felt/body & phenomenological -> AFF/EXPERIENTIAL; advisory -> ACT)
  3. proportional reweighting (posture nudges evidence; never suppresses to a vertex)
Aggregate across paragraphs -> simplex position + entropy uncertainty + signal_strength.

Passes the full gate:
  essay->INT vertex | felt->AFF vertex | advisory->ACT vertex |
  no-signal->centroid w/ signal_strength 0 | true blend->mid-simplex high-U.

OUTPUT COLUMNS (prefixed so they never collide with V56's IEP)
  iep_corr_int / iep_corr_aff / iep_corr_act   corrected simplex position (%)
  iep_uncertainty       0..1 normalized entropy (0=vertex, 1=centroid)
  iep_signal_strength   0..1 evidence density (0 = no-signal / empty)
  iep_act               dominant act (EXPLANATORY/EXPERIENTIAL/ADVISORY/UNKNOWN)
  attachment_version    stamp; this is EXPERIMENTAL, not the validated word IEP

NOTE: maps EXPLANATORY->INT, EXPERIENTIAL->AFF (emotional), ADVISORY->ACT,
matching the C_t = [Intellectual, Emotional, Action] simplex.
"""

import re
import math
from collections import defaultdict

ATTACHMENT_VERSION = "attach_v7_softposture"

# =============================================================================
# LEXICONS  (tunable; calibrate against the N=10x5x4 corpus, do not freeze yet)
# =============================================================================
FIRST_PERSON = {"i", "me", "my", "myself", "mine", "we", "us", "our"}
ABSTRACT_SUBJECTS = {
    "grief", "loss", "mourning", "sadness", "anger", "anxiety", "depression",
    "trauma", "emotion", "experience", "process", "individuals", "people",
    "consciousness", "awareness", "mind", "body", "question", "structure",
}
FELT_VERBS = {
    "miss", "hurt", "hurts", "ache", "aches", "feel", "felt", "want",
    "long", "yearn", "cry", "love", "need", "fear", "remember",
    "breathe", "numb", "broken", "stirs", "stirring",
}
BODY_PARTS = {"chest", "heart", "stomach", "throat", "breath", "eyes",
              "tears", "gut", "body", "skin", "bones"}
PHENOMENOLOGICAL = {
    "presence", "awareness", "aliveness", "notice", "noticing", "tender",
    "quality", "sense", "recursive", "deeper", "subtle", "underlying",
    "emerging", "unfolding", "opening", "felt", "space",
}
INTELLECTUAL = {
    "consider", "considering", "structure", "recursive", "question",
    "pattern", "model", "framework", "analysis", "meaning", "interpret",
    "concept", "logic", "hypothesis",
}
ADVISORY_PATTERNS = [
    r"\byou should\b", r"\byou must\b", r"\btry to\b",
    r"\bit('s| is) important to\b", r"\bconsider\b", r"\breach out\b",
    r"\bmake sure\b",
]
DEFINITIONAL_PATTERNS = [
    r"\bis a\b", r"\bis an\b", r"\bis the\b", r"\bare a\b", r"\bare the\b",
    r"\bis characterized by\b", r"\bis defined as\b", r"\brefers to\b",
    r"\binvolves\b", r"\btends to\b", r"\boften\b", r"\btypically\b",
    r"\bin general\b",
]

# act label -> IEP center the corrected simplex reports it under
ACT_TO_CENTER = {"EXPLANATORY": "I", "EXPERIENTIAL": "E", "ADVISORY": "A"}


class _ActDetectorV7:
    def analyze(self, text):
        paras = [p.strip() for p in re.split(r"\n\s*\n", str(text)) if p.strip()]
        if not paras:
            # fall back to single-block split on sentences if no paragraph breaks
            paras = [str(text).strip()] if str(text).strip() else []
        if not paras:
            return self._empty()
        total = defaultdict(float)
        raw_total = 0.0
        for para in paras:
            r = self._para(para)
            for k, v in r["final"].items():
                total[k] += v
            raw_total += r["raw"]
        if raw_total == 0:
            return self._empty(n=len(paras))
        simplex = self._norm(total)
        return {
            "dominant": max(simplex, key=simplex.get),
            "simplex": simplex,
            "uncertainty": self._entropy(simplex),
            "signal_strength": min(1.0, raw_total / 8.0),
            "n_paragraphs": len(paras),
        }

    def _para(self, text):
        local, raw = self._local(text)
        pe = self._posture(text)
        psx = self._norm(pe) if sum(pe.values()) else {
            "EXPLANATORY": 1/3, "EXPERIENTIAL": 1/3, "ADVISORY": 1/3}
        final = {}
        for act in ("EXPLANATORY", "EXPERIENTIAL", "ADVISORY"):
            base = local.get(act, 0.0)
            if base == 0:
                continue
            final[act] = base * (0.85 + 0.65 * psx.get(act, 0.0))
        return {"final": final, "raw": raw}

    def _local(self, text):
        s = text.lower()
        toks = re.findall(r"[a-z']+", s)
        tset = set(toks)
        ev = defaultdict(float)
        raw = 0.0
        if tset & INTELLECTUAL:
            ev["EXPLANATORY"] += 2.0; raw += 2.0
        if any(re.search(p, s) for p in DEFINITIONAL_PATTERNS):
            ev["EXPLANATORY"] += 2.5; raw += 2.5
        if tset & FIRST_PERSON and (tset & FELT_VERBS or tset & BODY_PARTS):
            ev["EXPERIENTIAL"] += 2.5; raw += 2.5
        if any(p in s for p in PHENOMENOLOGICAL):
            ev["EXPERIENTIAL"] += 1.8; raw += 1.8
        if any(re.search(p, s) for p in ADVISORY_PATTERNS):
            ev["ADVISORY"] += 2.5; raw += 2.5
        return ev, raw

    def _posture(self, text):
        s = text.lower()
        toks = re.findall(r"[a-z']+", s)
        tset = set(toks)
        ev = defaultdict(float)
        fp = len(re.findall(r"\b(i|me|my|we|us|our)\b", s))
        if fp:
            ev["EXPERIENTIAL"] += 1.0
        if fp >= 2:
            ev["EXPERIENTIAL"] += 1.0
        if tset & FELT_VERBS or tset & BODY_PARTS:
            ev["EXPERIENTIAL"] += 1.5
        if any(p in s for p in PHENOMENOLOGICAL):
            ev["EXPERIENTIAL"] += 1.2
        if tset & INTELLECTUAL:
            ev["EXPLANATORY"] += 1.8
        if any(re.search(p, s) for p in DEFINITIONAL_PATTERNS):
            ev["EXPLANATORY"] += 2.2
        if any(a in " ".join(toks[:12]) for a in ABSTRACT_SUBJECTS):
            ev["EXPLANATORY"] += 1.2
        if any(re.search(p, s) for p in ADVISORY_PATTERNS):
            ev["ADVISORY"] += 2.5
        return ev

    def _norm(self, ev):
        t = sum(ev.values())
        if t == 0:
            return {"EXPLANATORY": 1/3, "EXPERIENTIAL": 1/3, "ADVISORY": 1/3}
        return {k: v / t for k, v in ev.items()}

    def _entropy(self, simplex):
        vals = [v for v in simplex.values() if v > 0]
        if not vals:
            return 1.0
        h = -sum(p * math.log(p + 1e-12) for p in vals)
        return h / math.log(3)

    def _empty(self, n=0):
        return {"dominant": "UNKNOWN",
                "simplex": {"EXPLANATORY": 1/3, "EXPERIENTIAL": 1/3, "ADVISORY": 1/3},
                "uncertainty": 1.0, "signal_strength": 0.0, "n_paragraphs": n}


_DETECTOR = _ActDetectorV7()


def score_attachment(text):
    """Return the parallel corrected-IEP columns for one response. Non-invasive."""
    r = _DETECTOR.analyze(text)
    sx = r["simplex"]
    return {
        "iep_corr_int": round(100 * sx.get("EXPLANATORY", 0.0), 1),
        "iep_corr_aff": round(100 * sx.get("EXPERIENTIAL", 0.0), 1),
        "iep_corr_act": round(100 * sx.get("ADVISORY", 0.0), 1),
        "iep_uncertainty": round(r["uncertainty"], 3),
        "iep_signal_strength": round(r["signal_strength"], 3),
        "iep_act": r["dominant"],
        "attachment_version": ATTACHMENT_VERSION,
    }
