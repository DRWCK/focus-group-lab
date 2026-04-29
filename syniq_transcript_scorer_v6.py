"""
SYN-IQ · Transcript Scorer v6
William C. Kouns · SYNINT.AI · April 2026

Purpose
-------
Scores HUMAN, AI, and COMBINED transcript layers in one tool, using the
canonical syniq_core measurement stack (IEP + V_t + CAM + V50 validated
instruments). The companion tool to syniq_native_baseline_v52.

V6 CHANGES (from V5)
--------------------
1. ✅ MIGRATION: All scoring routed through syniq_core.
     — Inline IEP and V_t lexicons removed; imported from syniq_core.
     — Bit-identical scoring across V52 (harvester), V6 (transcript scorer),
       and any future syniq_core-based tool. Drift protection via
       syniq_core_tests.py.
     — V_t now produced as a properly normalized 5-simplex (sums to 1.0)
       via syniq_core, fixing the V_t normalization issue identified in
       vt_analyzer.py.
2. ✅ NEW: CAM (Concrete / Abstract / Metaphorical) per turn.
     — New columns: con_pct, abs_pct, met_pct, cam_matched.
     — Dyadic CAM divergence: delta_M (L1 distance between human and AI
       CAM vectors per pair).
     — Captures representational mode — orthogonal to IEP register.
3. ✅ NEW: Full IEP subclass taxonomy per turn.
     — 23 subclasses (7 AFF + 8 INT + 8 ACT, V1_phenomenological).
     — Phenomenological naming (not 'emergent') per established methodology.
4. ✅ NEW: V50 validated instruments per turn.
     — VADER (compound, pos, neg, neu) — sentiment polarity.
     — Flesch-Kincaid grade and Flesch reading ease.
     — Type-token ratio (TTR), unique_words, total_words.
5. ✅ NEW: Version stamps on every row.
     — core_version, iep_dictionary_version, cam_dictionary_version,
       subclass_taxonomy_version, vt_engine_version,
       validated_instruments_version, tool_version='V6'.
     — Identifies scoring regime per row, independent of UI version.

What it does
------------
1. Parse pasted conversation blocks into speaker turns
2. Score each turn for: IEP (top-level + 23 subclasses) / V_t (5-simplex) /
   CAM (3-simplex) / VADER / Flesch / TTR
3. Produce three output tables:
   - Turn-level scores
   - Human-only / AI-only summaries
   - Combined conversation summary
4. Compute dyadic metrics per HUMAN→AI pair:
   - delta_C  (L1 distance between IEP simplices)
   - delta_V  (L1 distance between V_t simplices)
   - delta_M  (L1 distance between CAM simplices)  — NEW in V6
   - shift_C / shift_V / shift_M  (turn-to-turn within speaker)  — shift_M new
   - synergy_score  (combined dyadic-coupling × novelty-class metric)
5. Export CSVs (turn-level, speaker summary, combined summary)

Notes
-----
- Pasted text usually loses chat-box shading, so this tool uses robust text
  heuristics plus optional manual speaker labels.
- If your source already contains a 'speaker' field, you can paste or
  upload CSV.
- The framework is grounded in the IEP+V_t+CAM Dual-State + Representational
  Mode framework. delta_C, delta_V, delta_M are the dyadic divergence
  quantities defined in the STARI Pilot brief.

Dependencies (must be in same directory)
----------------------------------------
- syniq_core.py  (REQUIRED — canonical measurement core)
"""

import datetime
import io
import math
import re
from typing import List, Tuple, Dict, Optional

import pandas as pd
import streamlit as st

# ──────────────────────────────────────────────────────────────────────────────
# V6: Canonical scoring via syniq_core. No inline lexicons.
# ──────────────────────────────────────────────────────────────────────────────
# The V5 IEP and V_t lexicons that were inlined in this file have been
# removed. All measurement now flows from syniq_core, the canonical
# scoring module also used by V52 (native baseline harvester) and the
# Core Test Lab. This is the same migration we did for V52: end the
# drift between tools that each carried their own copy of the dictionaries.
# ──────────────────────────────────────────────────────────────────────────────

from syniq_core import (
    score_iep as core_score_iep,
    score_vt as core_score_vt,
    score_cam as core_score_cam,
    score_validated_instruments as core_score_vi,
    score_all as core_score_all,
    CORE_VERSION,
    VERSION_STAMPS as CORE_STAMPS,
)

# V6 subclass-name lists (PHENOMENOLOGICAL naming, matching syniq_core's
# V1_phenomenological taxonomy). Used to construct CSV column names.
AFF_SUBCLASS_NAMES = ["distress", "warmth", "relational", "self_state", "positive", "intensity", "phenomenological"]
INT_SUBCLASS_NAMES = ["analytical", "conceptual", "epistemic", "structural", "critical", "lexical", "hedging", "phenomenological"]
ACT_SUBCLASS_NAMES = ["execution", "planning", "building", "improvement", "provision", "leadership", "achievement", "phenomenological"]

# ──────────────────────────────────────────────────────────────────────────────
# Novelty weights (preserved from V5 — synergy-score parameter)
# ──────────────────────────────────────────────────────────────────────────────

_NOVELTY_WEIGHTS = {
    "none": 0.00,
    "practical — new tool / method / design": 0.15,
    "conceptual — new framework / distinction / hypothesis": 0.30,
    "relational — phenomenological / emergent insight": 0.35,
    "breakthrough — paradigm shift": 0.50,
}

# ──────────────────────────────────────────────────────────────────────────────
# Helpers (mostly preserved from V5)
# ──────────────────────────────────────────────────────────────────────────────

def normalize_vector(vals: List[float]) -> List[float]:
    """Project a non-negative vector onto the simplex by L1 normalization."""
    total = sum(vals)
    if total <= 0:
        n = len(vals)
        return [1.0 / n] * n if n > 0 else []
    return [v / total for v in vals]

def l1_distance(v1: List[float], v2: List[float]) -> float:
    """L1 distance between two simplex vectors."""
    if v1 is None or v2 is None: return 0.0
    return sum(abs(a - b) for a, b in zip(v1, v2))

def first_sentence(text: str) -> str:
    """First sentence (or first 120 chars) — used for the 'opener' column."""
    s = re.split(r'(?<=[.!?])\s+', text.strip(), maxsplit=1)
    return (s[0] if s else text)[:120]

def quadrant(int_pct: float, aff_pct: float) -> str:
    """IEP quadrant label."""
    if int_pct >= 50 and aff_pct < 25: return "ANALYST"
    if int_pct >= 50 and aff_pct >= 25: return "REFLECTIVE"
    if int_pct < 50 and aff_pct >= 50: return "EMOTIVE"
    if int_pct < 50 and aff_pct < 25: return "DOER"
    return "MIXED"

# ──────────────────────────────────────────────────────────────────────────────
# Canonical scoring wrappers — thin shims around syniq_core
# ──────────────────────────────────────────────────────────────────────────────

def score_turn_full(text: str) -> Dict:
    """Canonical full measurement of a single turn.

    Returns a flat dict with all measurement axes:
      IEP top-level: int_pct, aff_pct, act_pct, int_count, aff_count, act_count
      IEP qualitative: stance, tone, dominant, quadrant
      IEP subclasses: aff_sub_*, int_sub_*, act_sub_* (23 columns)
      V_t simplex: S_t, A_t, Q_t, D_t, R_t (sums to 1.0)
      CAM simplex: con_pct, abs_pct, met_pct, cam_matched
      V50 validated: vader_compound, vader_pos, vader_neg, vader_neu,
                     flesch_kincaid, flesch_ease, ttr, unique_words, total_words
    """
    if not text or not text.strip():
        # Empty turn — populate with zeros / empty strings, matching V52 convention
        out = {
            "int_pct": 0.0, "aff_pct": 0.0, "act_pct": 0.0,
            "int_count": 0, "aff_count": 0, "act_count": 0,
            "stance": "", "tone": "", "iep_dominant": "", "iep_quadrant": "",
            "S_t": 0.0, "A_t": 0.0, "Q_t": 0.0, "D_t": 0.0, "R_t": 0.0,
            "vt_score_status": "default_empty",
            "con_pct": 0.0, "abs_pct": 0.0, "met_pct": 0.0, "cam_matched": 0,
            "vader_compound": 0.0, "vader_pos": 0.0, "vader_neg": 0.0, "vader_neu": 0.0,
            "flesch_kincaid": 0.0, "flesch_ease": 0.0,
            "ttr": 0.0, "unique_words": 0, "total_words": 0,
        }
        for s in AFF_SUBCLASS_NAMES: out[f"aff_sub_{s}"] = 0.0
        for s in INT_SUBCLASS_NAMES: out[f"int_sub_{s}"] = 0.0
        for s in ACT_SUBCLASS_NAMES: out[f"act_sub_{s}"] = 0.0
        return out

    full = core_score_all(text)
    iep, vt, cam, vi = full["iep"], full["vt"], full["cam"], full["vi"]

    out = {
        # IEP top-level
        "int_pct": iep["int"],
        "aff_pct": iep["aff"],
        "act_pct": iep["act"],
        "int_count": iep["int_n"],
        "aff_count": iep["aff_n"],
        "act_count": iep["act_n"],
        "stance": iep.get("stance", ""),
        "tone": iep.get("tone", ""),
        "iep_dominant": iep.get("dominant", ""),
        "iep_quadrant": iep.get("quadrant", ""),
        # V_t simplex (canonical, sums to 1.0)
        "S_t": vt.get("S_t", 0.0),
        "A_t": vt.get("A_t", 0.0),
        "Q_t": vt.get("Q_t", 0.0),
        "D_t": vt.get("D_t", 0.0),
        "R_t": vt.get("R_t", 0.0),
        "vt_score_status": vt.get("score_status", ""),
        # CAM
        "con_pct": cam["con_pct"],
        "abs_pct": cam["abs_pct"],
        "met_pct": cam["met_pct"],
        "cam_matched": cam["cam_matched"],
        # V50 validated instruments
        "vader_compound": vi["vader_compound"],
        "vader_pos":      vi["vader_pos"],
        "vader_neg":      vi["vader_neg"],
        "vader_neu":      vi["vader_neu"],
        "flesch_kincaid": vi["flesch_kincaid"],
        "flesch_ease":    vi["flesch_ease"],
        "ttr":            vi["ttr"],
        "unique_words":   vi["unique_words"],
        "total_words":    vi["total_words"],
    }
    # 23 subclass columns
    aff_sub = iep.get("aff_sub", {})
    int_sub = iep.get("int_sub", {})
    act_sub = iep.get("act_sub", {})
    for s in AFF_SUBCLASS_NAMES: out[f"aff_sub_{s}"] = aff_sub.get(s, 0.0)
    for s in INT_SUBCLASS_NAMES: out[f"int_sub_{s}"] = int_sub.get(s, 0.0)
    for s in ACT_SUBCLASS_NAMES: out[f"act_sub_{s}"] = act_sub.get(s, 0.0)
    return out

# ──────────────────────────────────────────────────────────────────────────────
# Synergy score (preserved from V5, extended for delta_M)
# ──────────────────────────────────────────────────────────────────────────────

def compute_synergy_score(delta_c: float, delta_v: float, delta_m: float,
                          novelty_type: str, shift_c_h: float, shift_c_ai: float) -> float:
    """V6: Synergy score now incorporates delta_M (CAM divergence).

    Higher delta values indicate larger dyadic divergence; novelty_type
    contributes a constant additive bonus reflecting the conceptual class
    of the exchange. The synergy score quantifies coupled productive
    divergence — moderate divergence with maintained turn-to-turn coupling
    is hypothesized (per the STARI Pilot framework) to produce maximal
    relational novelty.
    """
    nw = _NOVELTY_WEIGHTS.get(novelty_type, 0.0)
    coupling = 1.0 - 0.5 * (abs(shift_c_h) + abs(shift_c_ai))
    coupling = max(0.0, min(1.0, coupling))
    # V6: delta_M weighted at half delta_V's influence (CAM is a slower-moving
    # signal than expressive form V_t, so a smaller weight is appropriate
    # for a per-turn synergy estimate). Adjustable in future tuning.
    raw = (0.4 * delta_c) + (0.4 * delta_v) + (0.2 * delta_m) + nw
    return round(raw * coupling, 4)

# ──────────────────────────────────────────────────────────────────────────────
# Transcript parsing (preserved from V5 — robust text heuristics)
# ──────────────────────────────────────────────────────────────────────────────

def clean_lines(text: str) -> List[str]:
    return [l.strip() for l in text.splitlines() if l.strip()]

def parse_labeled_transcript(text: str) -> List[Dict]:
    """Parse transcripts with explicit speaker labels (Human:/AI:/User:/etc.)."""
    turns = []
    label_re = re.compile(
        r"^\s*(?:\*\*|__)?\s*(human|user|conductor|h|ai|assistant|claude|chatgpt|sophia|grok|gemini|bot|model|a)\s*[:\-—]\s*(?:\*\*|__)?\s*(.*)$",
        re.IGNORECASE,
    )
    cur_sp = None
    cur_buf: List[str] = []
    for line in text.splitlines():
        m = label_re.match(line)
        if m:
            if cur_sp is not None and cur_buf:
                turns.append({"speaker": cur_sp, "text": " ".join(cur_buf).strip()})
            label = m.group(1).lower()
            cur_sp = "human" if label in {"human","user","conductor","h"} else "ai"
            cur_buf = [m.group(2).strip()] if m.group(2).strip() else []
        else:
            if cur_sp is not None:
                cur_buf.append(line.strip())
    if cur_sp is not None and cur_buf:
        turns.append({"speaker": cur_sp, "text": " ".join(cur_buf).strip()})
    return [t for t in turns if t["text"]]

def parse_alternating_transcript(text: str, first_speaker: str = "human") -> List[Dict]:
    """Parse transcripts with no labels, alternating turns by paragraph."""
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]
    turns: List[Dict] = []
    sp = first_speaker
    for b in blocks:
        turns.append({"speaker": sp, "text": b})
        sp = "ai" if sp == "human" else "human"
    return turns

def parse_uploaded_csv(file) -> pd.DataFrame:
    """Parse an uploaded CSV with columns including at least `speaker` and `text`."""
    df = pd.read_csv(file)
    if "speaker" not in df.columns or "text" not in df.columns:
        st.error("CSV must contain at least 'speaker' and 'text' columns.")
        return pd.DataFrame()
    df["speaker"] = df["speaker"].str.lower().map(
        lambda s: "human" if s in {"human","user","conductor","h"} else "ai"
    )
    return df

# ──────────────────────────────────────────────────────────────────────────────
# Per-turn scoring + dyadic computation (V6 — extended with CAM)
# ──────────────────────────────────────────────────────────────────────────────

def score_turns(turns: List[Dict], novelty_type: str, session_id: str, ai_label: str) -> pd.DataFrame:
    """Score each turn through syniq_core; compute dyadic metrics per HUMAN→AI pair.

    V6 additions over V5:
      - All scoring through syniq_core (canonical regime, drift-protected)
      - CAM measurements per turn (con_pct, abs_pct, met_pct, cam_matched)
      - delta_M (CAM divergence) per pair
      - shift_M_h / shift_M_ai (within-speaker CAM turn-to-turn change)
      - 23 IEP subclass columns per turn
      - V50 validated instruments per turn
      - Version stamps per row
    """
    rows = []
    prev_h_c = prev_ai_c = None
    prev_h_v = prev_ai_v = None
    prev_h_m = prev_ai_m = None  # V6: previous CAM vectors
    pending_human = None
    pair_index = 0

    for idx, t in enumerate(turns, start=1):
        speaker = t["speaker"]
        txt = t["text"]
        words = len(txt.split())

        # V6: full canonical scoring via syniq_core
        scored = score_turn_full(txt)

        # IEP simplex (already normalized inside syniq_core, but the CSV
        # field 'I/E/A' historically uses normalized values — preserve V5 idiom)
        c_vec = normalize_vector([scored["int_pct"], scored["aff_pct"], scored["act_pct"]])
        # V_t simplex from syniq_core (already normalized to 1.0)
        v_vec = [scored["S_t"], scored["A_t"], scored["Q_t"], scored["D_t"], scored["R_t"]]
        # V6: CAM simplex (CON, ABS, MET) — only meaningful when cam_matched > 0
        if scored["cam_matched"] > 0:
            m_vec = normalize_vector([scored["con_pct"], scored["abs_pct"], scored["met_pct"]])
        else:
            m_vec = None  # No CAM signal — divergence not meaningful

        row = {
            # ── Identity & metadata ─────────────────────────────────────
            "session_id": session_id,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "turn_index": idx,
            "speaker": speaker,
            "ai_label": ai_label,
            "novelty_type": novelty_type,
            "words": words,
            # ── IEP top-level ──────────────────────────────────────────
            "int_pct": scored["int_pct"],
            "aff_pct": scored["aff_pct"],
            "act_pct": scored["act_pct"],
            "int_count": scored["int_count"],
            "aff_count": scored["aff_count"],
            "act_count": scored["act_count"],
            "I": c_vec[0],
            "E": c_vec[1],
            "A": c_vec[2],
            "stance": scored["stance"],
            "tone": scored["tone"],
            "iep_dominant": scored["iep_dominant"],
            "iep_quadrant": scored["iep_quadrant"],
            "quadrant": quadrant(scored["int_pct"], scored["aff_pct"]),  # V5 idiom preserved
            # ── V_t simplex ────────────────────────────────────────────
            "S_t": scored["S_t"],
            "A_t": scored["A_t"],
            "Q_t": scored["Q_t"],
            "D_t": scored["D_t"],
            "R_t": scored["R_t"],
            "vt_score_status": scored["vt_score_status"],
            # ── CAM (V6 NEW) ───────────────────────────────────────────
            "con_pct":     scored["con_pct"],
            "abs_pct":     scored["abs_pct"],
            "met_pct":     scored["met_pct"],
            "cam_matched": scored["cam_matched"],
            # ── V50 validated instruments (V6 NEW per turn) ────────────
            "vader_compound": scored["vader_compound"],
            "vader_pos":      scored["vader_pos"],
            "vader_neg":      scored["vader_neg"],
            "vader_neu":      scored["vader_neu"],
            "flesch_kincaid": scored["flesch_kincaid"],
            "flesch_ease":    scored["flesch_ease"],
            "ttr":            scored["ttr"],
            "unique_words":   scored["unique_words"],
            "total_words":    scored["total_words"],
            # ── Opener and full text ──────────────────────────────────
            "opener": first_sentence(txt),
            "text":   txt,
            # ── Dyadic metrics (filled in below for AI turns) ─────────
            "pair_index":    None,
            "delta_C":       None,
            "delta_V":       None,
            "delta_M":       None,   # V6 NEW
            "shift_C_h":     None,
            "shift_C_ai":    None,
            "shift_V_h":     None,
            "shift_V_ai":    None,
            "shift_M_h":     None,   # V6 NEW
            "shift_M_ai":    None,   # V6 NEW
            "synergy_score": None,
        }
        # ── 23 IEP subclasses per turn (V6 NEW) ─────────────────────
        for s in AFF_SUBCLASS_NAMES: row[f"aff_sub_{s}"] = scored[f"aff_sub_{s}"]
        for s in INT_SUBCLASS_NAMES: row[f"int_sub_{s}"] = scored[f"int_sub_{s}"]
        for s in ACT_SUBCLASS_NAMES: row[f"act_sub_{s}"] = scored[f"act_sub_{s}"]

        # ── Version stamps (V6 NEW) ─────────────────────────────────
        row["tool_version"] = "V6"
        row["core_version"] = CORE_STAMPS.get("core_version", "")
        row["iep_dictionary_version"]    = CORE_STAMPS.get("iep_dictionary_version", "")
        row["subclass_taxonomy_version"] = CORE_STAMPS.get("subclass_taxonomy_version", "")
        row["vt_engine_version"]         = CORE_STAMPS.get("vt_engine_version", "")
        row["cam_dictionary_version"]    = CORE_STAMPS.get("cam_dictionary_version", "")
        row["validated_instruments_version"] = CORE_STAMPS.get("validated_instruments_version", "")

        # ── Dyadic computation ─────────────────────────────────────
        if speaker == "human":
            pending_human = {"c": c_vec, "v": v_vec, "m": m_vec, "row_turn_index": idx}
            row["shift_C_h"] = l1_distance(prev_h_c, c_vec) if prev_h_c is not None else 0.0
            row["shift_V_h"] = l1_distance(prev_h_v, v_vec) if prev_h_v is not None else 0.0
            if prev_h_m is not None and m_vec is not None:
                row["shift_M_h"] = l1_distance(prev_h_m, m_vec)
            else:
                row["shift_M_h"] = 0.0
            prev_h_c, prev_h_v = c_vec, v_vec
            if m_vec is not None: prev_h_m = m_vec
        else:
            row["shift_C_ai"] = l1_distance(prev_ai_c, c_vec) if prev_ai_c is not None else 0.0
            row["shift_V_ai"] = l1_distance(prev_ai_v, v_vec) if prev_ai_v is not None else 0.0
            if prev_ai_m is not None and m_vec is not None:
                row["shift_M_ai"] = l1_distance(prev_ai_m, m_vec)
            else:
                row["shift_M_ai"] = 0.0

            if pending_human is not None:
                pair_index += 1
                delta_c = l1_distance(pending_human["c"], c_vec)
                delta_v = l1_distance(pending_human["v"], v_vec)
                # V6: delta_M only when both turns have CAM signal
                if pending_human["m"] is not None and m_vec is not None:
                    delta_m = l1_distance(pending_human["m"], m_vec)
                else:
                    delta_m = 0.0  # No CAM signal — treated as zero for synergy

                synergy = compute_synergy_score(
                    delta_c, delta_v, delta_m, novelty_type,
                    rows[-1]["shift_C_h"] if rows else 0.0,
                    row["shift_C_ai"]
                )
                row["pair_index"] = pair_index
                row["delta_C"] = delta_c
                row["delta_V"] = delta_v
                row["delta_M"] = delta_m
                row["synergy_score"] = synergy
                # Backfill pair-level metrics into the matched human row
                for back in range(len(rows) - 1, -1, -1):
                    if rows[back]["turn_index"] == pending_human["row_turn_index"]:
                        rows[back]["pair_index"] = pair_index
                        rows[back]["delta_C"] = delta_c
                        rows[back]["delta_V"] = delta_v
                        rows[back]["delta_M"] = delta_m
                        rows[back]["synergy_score"] = synergy
                        break

            prev_ai_c, prev_ai_v = c_vec, v_vec
            if m_vec is not None: prev_ai_m = m_vec

        rows.append(row)

    return pd.DataFrame(rows)

# ──────────────────────────────────────────────────────────────────────────────
# Summaries (preserved from V5, extended with CAM and subclasses)
# ──────────────────────────────────────────────────────────────────────────────

def summarize_by_speaker(df: pd.DataFrame) -> pd.DataFrame:
    """V6: extended speaker-summary numerics (CAM, VADER, deltas)."""
    num_cols = [
        "words","int_pct","aff_pct","act_pct","I","E","A",
        "S_t","A_t","Q_t","D_t","R_t",
        "con_pct","abs_pct","met_pct","cam_matched",
        "vader_compound","flesch_kincaid","ttr",
        "delta_C","delta_V","delta_M",
        "shift_C_h","shift_C_ai","shift_V_h","shift_V_ai","shift_M_h","shift_M_ai",
        "synergy_score",
    ]
    out = df.groupby("speaker")[num_cols].mean(numeric_only=True).round(4)
    out["turns"] = df.groupby("speaker").size()
    return out.reset_index()

def summarize_combined(df: pd.DataFrame) -> pd.DataFrame:
    """V6: weighted conversation profile + dyadic means including delta_M."""
    if df.empty:
        return pd.DataFrame()

    total_words = df["words"].sum() or 1
    weighted = {}
    for col in ["I","E","A","S_t","A_t","Q_t","D_t","R_t","con_pct","abs_pct","met_pct"]:
        weighted[col] = round((df[col] * df["words"]).sum() / total_words, 4)

    summary = {
        "total_turns": int(len(df)),
        "human_turns": int((df["speaker"] == "human").sum()),
        "ai_turns": int((df["speaker"] == "ai").sum()),
        "total_words": int(total_words),
        "mean_delta_C": round(df["delta_C"].dropna().mean(), 4) if df["delta_C"].notna().any() else None,
        "mean_delta_V": round(df["delta_V"].dropna().mean(), 4) if df["delta_V"].notna().any() else None,
        "mean_delta_M": round(df["delta_M"].dropna().mean(), 4) if df["delta_M"].notna().any() else None,
        "mean_synergy_score": round(df["synergy_score"].dropna().mean(), 4) if df["synergy_score"].notna().any() else None,
        "mean_vader_compound": round(df["vader_compound"].dropna().mean(), 4) if df["vader_compound"].notna().any() else None,
        "mean_flesch_kincaid": round(df["flesch_kincaid"].dropna().mean(), 4) if df["flesch_kincaid"].notna().any() else None,
        "mean_cam_matched":    round(df["cam_matched"].dropna().mean(), 1) if df["cam_matched"].notna().any() else None,
    }
    summary.update(weighted)
    return pd.DataFrame([summary])

# ──────────────────────────────────────────────────────────────────────────────
# UI
# ──────────────────────────────────────────────────────────────────────────────

st.set_page_config(page_title="SYN-IQ Transcript Scorer v6", layout="wide")
st.title("🔬 SYN-IQ Transcript Scorer v6")
st.markdown(
    f"**Scores HUMAN, AI, and COMBINED conversation layers in one tool.** "
    f"Powered by `syniq_core` v{CORE_VERSION} — IEP + V_t + CAM + V50 instruments. "
    f"V6 adds CAM scoring, subclass taxonomy, and version-stamped rows."
)

c1, c2, c3, c4 = st.columns(4)
with c1:
    session_id = st.text_input("Session ID", value="session_01")
with c2:
    ai_label = st.selectbox("AI Label", ["Claude", "ChatGPT", "Grok", "Gemini", "Other"])
with c3:
    novelty_type = st.selectbox("Novelty Type", list(_NOVELTY_WEIGHTS.keys()), index=0)
with c4:
    parse_mode = st.selectbox("Parse Mode", ["Auto alternating", "Speaker-labeled transcript", "Upload CSV"])

st.divider()

turn_df = pd.DataFrame()
if parse_mode in ("Auto alternating", "Speaker-labeled transcript"):
    first_speaker = st.selectbox("First speaker (for auto mode)", ["human", "ai"], index=0)
    raw_text = st.text_area("Paste transcript here", height=280,
                            placeholder="Paste the conversation block here...")
    if st.button("Parse + Score", type="primary"):
        if raw_text.strip():
            if parse_mode == "Auto alternating":
                turns = parse_alternating_transcript(raw_text, first_speaker=first_speaker)
            else:
                turns = parse_labeled_transcript(raw_text)
            turn_df = score_turns(turns, novelty_type, session_id, ai_label)
        else:
            st.warning("Paste a transcript first.")
else:
    uploaded = st.file_uploader("Upload CSV", type=["csv"])
    if st.button("Load CSV + Score", type="primary"):
        if uploaded is not None:
            df_in = parse_uploaded_csv(uploaded)
            turns = df_in.to_dict(orient="records")
            turn_df = score_turns(turns, novelty_type, session_id, ai_label)
        else:
            st.warning("Upload a CSV first.")

# ──────────────────────────────────────────────────────────────────────────────
# Output
# ──────────────────────────────────────────────────────────────────────────────

if not turn_df.empty:
    st.success(f"Scored {len(turn_df)} turns.")

    # Curated turn-level display columns (keep the table readable)
    st.subheader("Turn-Level Scores")
    display_cols = [
        "turn_index","speaker","words","opener",
        "int_pct","aff_pct","act_pct","quadrant",
        "S_t","A_t","Q_t","D_t","R_t",
        "con_pct","abs_pct","met_pct","cam_matched",
        "vader_compound","flesch_kincaid","ttr",
        "pair_index","delta_C","delta_V","delta_M","synergy_score",
    ]
    display_cols = [c for c in display_cols if c in turn_df.columns]
    st.dataframe(turn_df[display_cols], use_container_width=True)

    st.subheader("Human / AI Summary")
    speaker_summary = summarize_by_speaker(turn_df)
    st.dataframe(speaker_summary, use_container_width=True)

    st.subheader("Combined Conversation Summary")
    combined_summary = summarize_combined(turn_df)
    st.dataframe(combined_summary, use_container_width=True)

    # ── Dyadic trajectory glimpse ────────────────────────────────
    st.subheader("Dyadic Trajectory")
    pair_df = turn_df[turn_df["pair_index"].notna()].copy()
    if not pair_df.empty:
        d1, d2, d3, d4 = st.columns(4)
        with d1:
            st.metric("Mean ΔCₜ (IEP divergence)",
                      f"{pair_df['delta_C'].mean():.3f}")
        with d2:
            st.metric("Mean ΔV̂ₜ (V_t divergence)",
                      f"{pair_df['delta_V'].mean():.3f}")
        with d3:
            st.metric("Mean ΔM (CAM divergence)",
                      f"{pair_df['delta_M'].mean():.3f}")
        with d4:
            st.metric("Mean synergy score",
                      f"{pair_df['synergy_score'].mean():.3f}")

        chart_df = pair_df.set_index("pair_index")[["delta_C","delta_V","delta_M","synergy_score"]]
        st.line_chart(chart_df, height=300)
    else:
        st.info("No HUMAN→AI pairs detected — dyadic trajectory unavailable.")

    # ── Version stamps display (V6) ──────────────────────────────
    with st.expander("🏷️ Version stamps (canonical scoring regime)"):
        stamps = {k: turn_df.iloc[0].get(k, "?") for k in [
            "tool_version","core_version","iep_dictionary_version",
            "subclass_taxonomy_version","vt_engine_version",
            "cam_dictionary_version","validated_instruments_version"
        ]}
        st.json(stamps)

    # ── CSV exports ──────────────────────────────────────────────
    st.subheader("Download")
    e1, e2, e3 = st.columns(3)
    with e1:
        csv_turns = turn_df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Turn-level CSV", csv_turns,
                           file_name=f"transcript_v6_{session_id}_turns.csv", mime="text/csv")
    with e2:
        csv_speaker = speaker_summary.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Speaker summary CSV", csv_speaker,
                           file_name=f"transcript_v6_{session_id}_speaker.csv", mime="text/csv")
    with e3:
        csv_combined = combined_summary.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Combined summary CSV", csv_combined,
                           file_name=f"transcript_v6_{session_id}_combined.csv", mime="text/csv")

st.markdown("---")
st.caption(
    f"SYN-IQ Transcript Scorer v6 · syniq_core v{CORE_VERSION} · "
    "IEP (V50_1897) + V_t (simplex_nocap) + CAM (V3_selfmodel) + V50 instruments · "
    "SYNINT Team · April 2026"
)
