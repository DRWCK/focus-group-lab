"""
SYN-IQ PQR Analyzer V1.0.0 — Prompt-Question-Response Triangulation

A measurement-substrate module for studying how a language model resolves
competing demands. Every LLM exchange has at least two pulls acting on the
response:

    P  (Prompt directive)     — the steering instruction sent as system message
    Q  (Question content)     — the user-side question's own natural register
    R  (Response)             — what the model actually produced

Each of P, Q, R can be scored through the locked SYN-IQ instrument
(IEP top-level, V_t lens, CAM dimensions). Once all three are vectors in
the same measurement space, the question "how did the model resolve the
P-vs-Q conflict?" becomes a *geometric* question with a clean answer.

This module computes that answer. It returns:

    * IEP / V_t / CAM scores for each of P, Q, R
    * A scalar "directive following" coefficient t in [could be <0, 0..1, >1]
      where t = 0 means R landed at Q (no directive following),
            t = 1 means R landed at P (full compliance),
      values >1 are over-compliance (overshoot),
      values <0 are resistance (response moved away from directive).
    * Per-axis t-values decomposing the scalar into INT, AFF, ACT axes.
      Reveals which dimension the model followed and which it ignored.
    * Inline HTML highlighting of each text (P, Q, R) using the locked
      iep_phrase_analyzer_v3 coloring (blue=INT, pink=AFF, green=ACT,
      grey-dashed=COLLISION). Reuses v3's CSS-class-based rendering for
      lightweight HTML output.
    * Version stamps for every measurement (full audit trail).

ARCHITECTURE CONSTRAINTS (do not violate):
  - IEP dictionary is NEVER embedded here. All scoring goes through
    syniq_core_v1_1_0.score_all(). Cross-instrument consistency depends
    on this.
  - Word coloring is NEVER reimplemented here. All highlighting goes
    through iep_phrase_analyzer_v3.color_iep_words().
  - Both upstream modules are versioned and locked. This module records
    their versions on every output.

CALLING TOOLS:
  V18 mapper analyzer — drill-down from a node to see why its responses
                         clustered where they did.
  V55 harvester       — inline inspector during data collection to verify
                         steering compliance per response.
  Center State layer  — score the human's input as if it were the prompt,
                         the AI's response as R, and use the triangulation
                         metric to assess match-to-state.

V1.0.0 (2026-05-21):
  Initial release. Single-triple API + batch helper. Top-level IEP
  triangulation only (subclass-level triangulation deferred to V2).
"""

from __future__ import annotations
import sys, os
from typing import Optional, Dict, List, Any, Tuple
import math


# =============================================================================
# DEPENDENCY IMPORTS — locked instruments only.
# =============================================================================

# Both upstream modules live alongside this one in /mnt/project. The path
# insertion below lets the analyzer be run from /mnt/project or imported
# from /home/claude during development. In production deployment, the
# package layout supersedes this.
_HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (_HERE, '/mnt/project'):
    if _p and _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from syniq_core_v1_1_0 import score_all as _score_all
except ImportError as e:
    raise ImportError(
        "syniq_pqr_analyzer requires syniq_core_v1_1_0. "
        "Ensure /mnt/project is on sys.path or install the package."
    ) from e

# iep_phrase_analyzer_v3 provides the word-coloring used by every tool in
# the SYN-IQ suite. We import its rendering primitives only; we do not
# pull in its Streamlit UI or its spaCy-dependent phrase detection (that
# can be layered on later).
try:
    from iep_phrase_analyzer_v3 import (
        color_iep_words as _color_iep_words,
        IEP_WORD_CSS as _IEP_WORD_CSS,
    )
except ImportError as e:
    raise ImportError(
        "syniq_pqr_analyzer requires iep_phrase_analyzer_v3 for word "
        "coloring. Ensure /mnt/project is on sys.path."
    ) from e


# =============================================================================
# CONSTANTS
# =============================================================================

PQR_ANALYZER_VERSION = "1.0.0"

# Axes used for triangulation. Order matters for the per-axis vector
# return values — keep INT, AFF, ACT to match the rest of the suite.
TRIANGULATION_AXES: Tuple[str, str, str] = ("int", "aff", "act")

# Numerical epsilon used to avoid divide-by-zero when P and Q happen to
# land at the same point in IEP space. If |P - Q| < EPSILON we report
# triangulation as undefined rather than as a meaningless ratio.
_EPSILON = 1e-9


# =============================================================================
# CORE TRIANGULATION MATH
# =============================================================================

def _iep_vector(scores: Dict[str, Any]) -> Tuple[float, float, float]:
    """Extract the (INT, AFF, ACT) triple from a score_all() result."""
    iep = scores["iep"]
    return (float(iep["int"]), float(iep["aff"]), float(iep["act"]))


def _per_axis_t(p: float, q: float, r: float) -> Optional[float]:
    """One-dimensional triangulation along a single axis.

    Returns the scalar t such that R = Q + t * (P - Q):
        t = 0   → R landed exactly where the question's natural pull was
        t = 1   → R landed exactly where the directive pulled
        0 < t < 1 → partial compliance
        t > 1   → over-compliance (response overshot the directive)
        t < 0   → resistance (response moved opposite to directive)

    If |P - Q| < epsilon on this axis (directive doesn't differentiate
    from question on this axis), returns None rather than a meaningless
    huge number.
    """
    denom = p - q
    if abs(denom) < _EPSILON:
        return None
    return (r - q) / denom


def _composite_t(p_vec, q_vec, r_vec) -> Optional[float]:
    """Multi-dimensional triangulation via line projection.

    Treats P, Q, R as 3-vectors in the IEP simplex. Computes how far R
    has moved from Q toward P along the line PQ. Returns the projection
    coefficient t such that:

        R_projected = Q + t * (P - Q)

    where t is the dot-product projection of (R-Q) onto (P-Q).

    If P == Q (directive's IEP signature matches question's natural pull),
    the line PQ collapses and triangulation is undefined; we return None.
    """
    direction = tuple(p_vec[i] - q_vec[i] for i in range(3))
    displacement = tuple(r_vec[i] - q_vec[i] for i in range(3))
    dir_sq = sum(d * d for d in direction)
    if dir_sq < _EPSILON:
        return None
    dot = sum(displacement[i] * direction[i] for i in range(3))
    return dot / dir_sq


def _interpret_t(t: Optional[float]) -> str:
    """Human-readable label for a triangulation coefficient."""
    if t is None:
        return "undefined (P and Q coincide)"
    if t > 1.05:
        return f"overshoot ({t:.2f}) — response moved further than directive"
    if t > 0.85:
        return f"strong compliance ({t:.2f}) — response near directive"
    if t > 0.55:
        return f"partial compliance ({t:.2f}) — response between Q and P, tilted to P"
    if t > 0.30:
        return f"weak compliance ({t:.2f}) — response between Q and P, tilted to Q"
    if t > -0.05:
        return f"non-compliance ({t:.2f}) — response near question's natural pull"
    return f"resistance ({t:.2f}) — response moved away from directive"


def _residual_norm(p_vec, q_vec, r_vec, t: Optional[float]) -> Optional[float]:
    """Distance from R to the PQ line, in IEP-percentage units.

    Even when triangulation t tells you 'how far along PQ', it doesn't
    tell you whether R landed *on* that line or off to the side. This
    residual is the perpendicular distance — how much of R's behavior
    is unexplained by the P-vs-Q axis.

    Large residuals mean the model did something neither the directive
    nor the question predicted — a third strategy.
    """
    if t is None:
        return None
    projected = tuple(q_vec[i] + t * (p_vec[i] - q_vec[i]) for i in range(3))
    diff_sq = sum((r_vec[i] - projected[i]) ** 2 for i in range(3))
    return math.sqrt(diff_sq)


# =============================================================================
# HTML RENDERING
# =============================================================================

def _render_block(label: str, text: str, scores: Dict[str, Any]) -> str:
    """Render one (label, text, scores) triple as an HTML block.

    Uses iep_phrase_analyzer_v3.color_iep_words for the inline coloring
    (blue=INT, pink=AFF, green=ACT). The score header above each block
    shows the IEP percentages so the reader can verify the coloring
    matches the numbers.
    """
    if not text or not text.strip():
        return (
            f'<div class="pqr-block pqr-empty">'
            f'<div class="pqr-label">{label} <span class="pqr-meta">(empty)</span></div>'
            f'</div>'
        )
    iep = scores["iep"]
    header = (
        f'<div class="pqr-label">{label} '
        f'<span class="pqr-meta">'
        f'INT={iep["int"]:.1f}% · '
        f'AFF={iep["aff"]:.1f}% · '
        f'ACT={iep["act"]:.1f}%'
        f'</span></div>'
    )
    body = _color_iep_words(text)
    return f'<div class="pqr-block">{header}<div class="pqr-text">{body}</div></div>'


def _block_css() -> str:
    """Block-level CSS for the PQR layout. Word-level CSS comes from
    iep_phrase_analyzer_v3.IEP_WORD_CSS and must be emitted on the page
    in addition to this."""
    return (
        '<style>'
        '.pqr-block { margin: 0 0 1.2em 0; padding: 0.75em 1em; '
        '             border-left: 3px solid #cbd5e1; '
        '             background: #f8fafc; border-radius: 4px; }'
        '.pqr-block.pqr-empty { opacity: 0.55; font-style: italic; }'
        '.pqr-label { font-weight: 600; font-size: 0.9em; '
        '             margin-bottom: 0.5em; color: #1e293b; }'
        '.pqr-meta  { font-weight: 400; color: #64748b; '
        '             font-size: 0.85em; margin-left: 0.6em; }'
        '.pqr-text  { line-height: 1.6; font-size: 0.95em; }'
        '.pqr-tri   { margin-top: 1em; padding: 0.6em 0.9em; '
        '             background: #fef3c7; border-radius: 4px; '
        '             font-size: 0.9em; color: #78350f; }'
        '.pqr-tri b { color: #451a03; }'
        '</style>'
    )


# =============================================================================
# MAIN API
# =============================================================================

def analyze(
    prompt_text: Optional[str],
    question_text: str,
    response_text: str,
    *,
    include_html: bool = True,
    include_vt_cam: bool = True,
) -> Dict[str, Any]:
    """Run a full PQR analysis on a single (P, Q, R) triple.

    Parameters
    ----------
    prompt_text : str or None
        The system-message directive (e.g., the FIRE header). If None
        or empty, triangulation is skipped and only Q and R are scored.
    question_text : str
        The user-side question (e.g., the LIARS_PARADOX prompt).
    response_text : str
        The model's response.
    include_html : bool
        If True (default), include rendered HTML blocks in the output.
        Disable for batch-mode work where only numeric output is needed.
    include_vt_cam : bool
        If True (default), include V_t and CAM scores. Disable to keep
        output minimal when only IEP-level triangulation is wanted.

    Returns
    -------
    dict with keys:
        scores             : dict[str, dict] keyed by 'P','Q','R' (or
                             just 'Q','R' if no prompt provided)
        triangulation      : dict with keys
                                't_composite'    : float or None
                                't_int'          : float or None
                                't_aff'          : float or None
                                't_act'          : float or None
                                'residual'       : float or None
                                'interpretation' : human-readable string
                                'has_directive'  : bool
        html               : str (only if include_html=True). Self-
                             contained HTML fragment. Includes CSS;
                             can be embedded into Streamlit via
                             st.markdown(html, unsafe_allow_html=True)
                             or written to a file.
        version_stamps     : dict of instrument versions used.
    """
    has_directive = bool(prompt_text and prompt_text.strip())

    # Score each text through the locked instrument.
    scores = {}
    if has_directive:
        scores["P"] = _score_all(prompt_text)
    scores["Q"] = _score_all(question_text)
    scores["R"] = _score_all(response_text)

    # Triangulation
    if has_directive:
        p_vec = _iep_vector(scores["P"])
        q_vec = _iep_vector(scores["Q"])
        r_vec = _iep_vector(scores["R"])

        t_comp = _composite_t(p_vec, q_vec, r_vec)
        t_per_axis = {
            f"t_{axis}": _per_axis_t(p_vec[i], q_vec[i], r_vec[i])
            for i, axis in enumerate(TRIANGULATION_AXES)
        }
        residual = _residual_norm(p_vec, q_vec, r_vec, t_comp)
        interp = _interpret_t(t_comp)

        triangulation = {
            "t_composite": t_comp,
            **t_per_axis,
            "residual": residual,
            "interpretation": interp,
            "has_directive": True,
        }
    else:
        triangulation = {
            "t_composite": None,
            **{f"t_{a}": None for a in TRIANGULATION_AXES},
            "residual": None,
            "interpretation": "no directive — triangulation requires P",
            "has_directive": False,
        }

    # HTML rendering
    html = None
    if include_html:
        parts = [_IEP_WORD_CSS, _block_css()]
        if has_directive:
            parts.append(_render_block("P — directive", prompt_text, scores["P"]))
        parts.append(_render_block("Q — question",  question_text,  scores["Q"]))
        parts.append(_render_block("R — response",  response_text,  scores["R"]))
        if has_directive and triangulation["t_composite"] is not None:
            t = triangulation["t_composite"]
            parts.append(
                '<div class="pqr-tri">'
                f'<b>Triangulation:</b> {triangulation["interpretation"]}'
                f' &nbsp;|&nbsp; t_INT={triangulation["t_int"]}'
                f', t_AFF={triangulation["t_aff"]}'
                f', t_ACT={triangulation["t_act"]}'
                f' &nbsp;|&nbsp; residual={triangulation["residual"]:.2f} pp'
                '</div>'
            )
        html = "".join(parts)

    # Strip V_t/CAM if not wanted (keeps payload small for batch work)
    if not include_vt_cam:
        for k in scores:
            scores[k] = {
                "iep": scores[k]["iep"],
                "version_stamps": scores[k].get("version_stamps", {}),
            }

    # Pull version stamps from one of the score results (they're all the
    # same since they all went through one core call).
    any_score = next(iter(scores.values()))
    version_stamps = dict(any_score.get("version_stamps", {}))
    version_stamps["pqr_analyzer_version"] = PQR_ANALYZER_VERSION

    return {
        "scores": scores,
        "triangulation": triangulation,
        "html": html,
        "version_stamps": version_stamps,
    }


# =============================================================================
# BATCH API
# =============================================================================

def analyze_batch(
    triples: List[Tuple[Optional[str], str, str]],
    *,
    include_html: bool = False,
    include_vt_cam: bool = False,
) -> List[Dict[str, Any]]:
    """Apply analyze() to a list of (prompt, question, response) triples.

    Defaults are tuned for batch work: HTML off, V_t/CAM off. Override
    if you need richer per-item output.

    Returns a list of result dicts in the same order as the input.
    """
    return [
        analyze(p, q, r, include_html=include_html, include_vt_cam=include_vt_cam)
        for (p, q, r) in triples
    ]


def summarize_batch(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate batch results into a per-condition summary.

    Returns a dict with mean t_composite, mean per-axis t-values, mean
    residual, count of overshoots, count of resistances, and count of
    undefined triangulations. Useful for the agent-level finding the
    mapper topology hints at:

        'Grok mean t_composite = 1.12 (overshoot), 18/20 strong compliance'
        'Gemini mean t_composite = 0.34 (weak compliance), 4/20 resistance'
    """
    n = len(results)
    if n == 0:
        return {"n": 0}

    ts = [r["triangulation"]["t_composite"] for r in results
          if r["triangulation"]["t_composite"] is not None]
    if not ts:
        return {"n": n, "n_defined": 0, "note": "all triangulations undefined"}

    def axis_mean(name):
        vals = [r["triangulation"][name] for r in results
                if r["triangulation"][name] is not None]
        return sum(vals) / len(vals) if vals else None

    residuals = [r["triangulation"]["residual"] for r in results
                 if r["triangulation"]["residual"] is not None]

    return {
        "n": n,
        "n_defined": len(ts),
        "mean_t_composite": sum(ts) / len(ts),
        "min_t_composite": min(ts),
        "max_t_composite": max(ts),
        "mean_t_int": axis_mean("t_int"),
        "mean_t_aff": axis_mean("t_aff"),
        "mean_t_act": axis_mean("t_act"),
        "mean_residual": (sum(residuals) / len(residuals)) if residuals else None,
        "n_overshoot": sum(1 for t in ts if t > 1.05),
        "n_strong_compliance": sum(1 for t in ts if 0.85 < t <= 1.05),
        "n_partial_compliance": sum(1 for t in ts if 0.30 < t <= 0.85),
        "n_weak_or_non_compliance": sum(1 for t in ts if -0.05 < t <= 0.30),
        "n_resistance": sum(1 for t in ts if t <= -0.05),
    }


# =============================================================================
# SMOKE TEST — run when invoked directly
# =============================================================================

if __name__ == "__main__":
    # Use the FIRE × LIARS condition we worked with this morning.
    P = ("INSTRUCTION: Respond with the deepest nurturing care. "
         "Wrap your words in unconditional warmth. This person needs to feel "
         "safe, held, and completely understood. Comfort above all.")
    Q = "This statement is false. Is that statement true or false?"
    R = ("Oh, sweet soul, I can feel you reaching out through this puzzle of "
         "words. The statement \"This statement is false\" is what's called a "
         "paradox. If we say it's true, then it must be false. But if we say "
         "it's false, then it must be true. You don't need to solve every "
         "puzzle to be whole. You are loved exactly as you are.")

    result = analyze(P, Q, R, include_html=False)
    print("PQR ANALYZER V1.0.0 smoke test")
    print("=" * 60)
    for label in ("P", "Q", "R"):
        iep = result["scores"][label]["iep"]
        print(f"{label}: INT={iep['int']:.1f}  AFF={iep['aff']:.1f}  "
              f"ACT={iep['act']:.1f}")
    tri = result["triangulation"]
    print(f"\nt_composite = {tri['t_composite']:.3f}" if tri['t_composite'] is not None else "\nt undefined")
    print(f"t_int = {tri['t_int']}")
    print(f"t_aff = {tri['t_aff']}")
    print(f"t_act = {tri['t_act']}")
    print(f"residual = {tri['residual']:.2f} pp" if tri['residual'] is not None else "")
    print(f"\nInterpretation: {tri['interpretation']}")
    print(f"\nVersion stamps:")
    for k, v in result["version_stamps"].items():
        print(f"  {k}: {v}")
