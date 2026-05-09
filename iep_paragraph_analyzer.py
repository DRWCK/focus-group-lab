"""
iep_paragraph_analyzer.py — IEP Paragraph-Level Analysis (v0.1)
================================================================

The third measurement layer in the SYN-IQ language-only stack.

Architecture context (W.C.K, May 2026):
  Word layer     — isolate IEP words (topic / lexical density). Canonical,
                   sourced from syniq_core V50 dictionaries.
  Phrase layer   — examine those words *in context*. Polysemy disambiguation
                   and clause-level register. (iep_phrase_analyzer.py)
  Paragraph layer — *this module*. Verify the phrase reading against the
                   discursive frame the paragraph is operating in.

Each layer is necessary but not sufficient. Words without phrase mis-handle
polysemy ("create a contradiction" ≠ ACT-building). Words + phrases without
paragraph mis-handle the grief-essay case: correct word counts, correct
phrase register, wrong overall verdict because the discursive frame —
expository taxonomy — was not checked.

Mode taxonomy (5 modes — kept small on purpose):
  - expository    — taxonomies, definitions, "X is Y" / "X is not A; it is B".
                    INT-mode regardless of subject vocabulary.
  - experiential  — first-person reflection, phenomenological self-report.
                    "I find myself...", "something I can't quite locate".
                    AFF-mode.
  - directive     — instructions, plans, action sequences. ACT-mode.
  - narrative     — temporal sequence, scene, characters. Mode-neutral.
  - argumentative — claim + evidence + counterclaim. INT-mode, distinct
                    subclass from expository.

v0.1 scope (deliberately minimal — validate architecture before expanding):
  - Detector family 1: META-DISCOURSE OPENERS
      "I will provide", "Below, we describe", "Here are", "In this section",
      "Let us consider", "The following sections describe", etc.
      Highest-precision expository signal. Cannot be confused with topic.
  - Detector family 2: HEADING / SCAFFOLDING SIGNALS
      Markdown headings (^#+ ), numbered sections (^\\d+\\. ),
      bolded lead-in (**X**:), surrounding-paragraph inheritance.
      A paragraph immediately following a heading inherits an expository
      prior unless other signals override.

Three more families come in v0.2 once v0.1 reads correctly on benchmark
passages: sentence-shape signals, discourse-marker density, and
enumeration parallelism.

Convergence rule (headline-issuance gate):
  When word / phrase / paragraph all agree on dominant class → issue headline.
  When mode and subject disagree → two-axis reading: e.g.,
    "Mode: INT (expository)  ·  Subject: AFF (grief, 61.5%)
     → Intellectual discussion of grief, AFF-heavy support vocabulary."
  When no clean reading → layered evidence only, no headline.

This module IS DIAGNOSTIC. It does not modify IEP scoring. The canonical IEP
score remains word-only (syniq_core v1.1.0 patched). This module reveals
discursive-frame structure that lets the convergence rule decide whether the
word-only score should be issued as a headline or held in two-axis form.

Run:
  streamlit run iep_paragraph_analyzer.py

Default password: tennessee
"""

import os
import re
import json
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Tuple, Optional

import pandas as pd
import streamlit as st


# =============================================================================
# MODE TAXONOMY
# =============================================================================
MODES = ('expository', 'experiential', 'directive', 'narrative', 'argumentative')

# Each mode aligns to an IEP class for the convergence rule. A mode score
# does not determine the IEP class directly — it provides the discursive
# frame against which word/phrase readings are verified.
MODE_TO_IEP = {
    'expository':    'INT',
    'argumentative': 'INT',
    'experiential':  'AFF',
    'directive':     'ACT',
    'narrative':     None,   # mode-neutral; topic vocabulary decides
}


# =============================================================================
# DETECTOR FAMILY 1 — META-DISCOURSE OPENERS
# =============================================================================
# Phrases that announce what the *text* is about to do, not what the *world*
# is doing. Highest-precision expository signal. A paragraph carrying any of
# these is almost certainly expository regardless of topic vocabulary.

META_DISCOURSE_RULES: List[Dict] = [
    # First-person "I will / let me / I'll" announcements of upcoming text moves
    {'pattern': r"\bI\s+will\s+(?:provide|describe|discuss|explain|outline|"
                r"summarize|analyze|examine|present|address|cover|explore|"
                r"detail|review|argue|show|demonstrate|illustrate)\b",
     'label': 'I will [text-move verb]',
     'mode_votes': {'expository': 1.0},
     'note': 'First-person announcement of upcoming expository move.'},

    {'pattern': r"\b(?:Let\s+me|Let\s+us|Let's)\s+(?:consider|examine|"
                r"explore|look\s+at|turn\s+to|think\s+about|begin\s+by|"
                r"start\s+by|outline|describe|review)\b",
     'label': 'Let us [text-move verb]',
     'mode_votes': {'expository': 1.0},
     'note': 'Hortative meta-discourse opener.'},

    {'pattern': r"\b(?:I'll|I\s+shall|I\s+aim\s+to|I\s+intend\s+to)\s+"
                r"(?:provide|describe|discuss|explain|outline|summarize|"
                r"analyze|examine|present|cover)\b",
     'label': "I'll [text-move verb]",
     'mode_votes': {'expository': 1.0},
     'note': 'Contracted/modal first-person text-move announcement.'},

    # Section-pointer openers
    {'pattern': r"\b(?:Below|Above|Following|Throughout|In\s+(?:this|the)\s+"
                r"(?:section|chapter|paper|article|paragraph|discussion|"
                r"analysis|essay))\b\s*[,:]?",
     'label': 'In this [section]',
     'mode_votes': {'expository': 0.9},
     'note': 'Section-pointer opener; orients reader to text structure.'},

    {'pattern': r"\b(?:Here\s+are|Here\s+is|Following\s+are|These\s+are)\s+"
                r"(?:the|some|a\s+few|several)?\s*\w+",
     'label': 'Here are [the X]',
     'mode_votes': {'expository': 0.9},
     'note': 'Enumerative meta-discourse opener; frames upcoming list.'},

    {'pattern': r"\b(?:The\s+following|What\s+follows)\s+"
                r"(?:is|are|describes|outlines|presents|covers|examines|"
                r"explores|details)\b",
     'label': 'The following [verb]',
     'mode_votes': {'expository': 1.0},
     'note': 'Cataphoric reference to upcoming text content.'},

    # Definitional / structural meta-language
    {'pattern': r"\b(?:This\s+(?:section|paper|paragraph|essay|discussion|"
                r"analysis|chapter|article))\s+(?:will\s+)?"
                r"(?:cover|discuss|present|describe|outline|examine|"
                r"explore|address|argue|show)\b",
     'label': 'This [section] [verb]',
     'mode_votes': {'expository': 1.0},
     'note': 'Self-referential text-structure announcement.'},

    {'pattern': r"\b(?:For\s+the\s+purposes\s+of|For\s+our\s+purposes|"
                r"By\s+way\s+of|To\s+begin|To\s+conclude|In\s+summary|"
                r"In\s+conclusion|To\s+summarize)\b",
     'label': 'meta-frame transition',
     'mode_votes': {'expository': 0.7, 'argumentative': 0.3},
     'note': 'Rhetorical-structure transition phrase.'},

    # Argumentative meta-discourse (subset of expository, but distinct)
    {'pattern': r"\b(?:I\s+(?:argue|claim|contend|maintain|propose|posit|"
                r"hold)\s+that|My\s+(?:argument|claim|thesis|position)\s+is)\b",
     'label': 'I argue that [...]',
     'mode_votes': {'argumentative': 1.0},
     'note': 'First-person thesis announcement.'},

    {'pattern': r"\b(?:On\s+the\s+contrary|To\s+the\s+contrary|"
                r"By\s+contrast|However|Nevertheless|Nonetheless|"
                r"That\s+said|Granted|Admittedly)\b\s*,",
     'label': 'argumentative pivot',
     'mode_votes': {'argumentative': 0.8, 'expository': 0.2},
     'note': 'Concession/contrast pivot characteristic of argument.'},
]


# =============================================================================
# DETECTOR FAMILY 2 — HEADING / SCAFFOLDING SIGNALS
# =============================================================================
# Operates on paragraph-level structure rather than internal pattern matching.

# Markdown / structural heading patterns — applied to paragraph FIRST LINE
HEADING_PATTERNS: List[Dict] = [
    {'pattern': r"^#{1,6}\s+\S",
     'label': 'markdown heading',
     'mode_votes': {'expository': 0.6},
     'note': 'Markdown heading marker; paragraph is a heading itself.'},

    {'pattern': r"^\*\*[^*]+\*\*\s*$",
     'label': 'bold standalone (heading-like)',
     'mode_votes': {'expository': 0.5},
     'note': 'Standalone bolded line acts as a heading.'},

    {'pattern': r"^\d+\.\s+\*\*[^*]+\*\*",
     'label': 'numbered + bold lead',
     'mode_votes': {'expository': 0.7},
     'note': 'Numbered section with bold lead-in; strong taxonomy signal.'},

    {'pattern': r"^[-*]\s+\*\*[^*]+\*\*\s*[:—-]",
     'label': 'bulleted bold lead-in',
     'mode_votes': {'expository': 0.6},
     'note': 'Bullet with bold lead-in followed by colon/dash; taxonomy item.'},

    {'pattern': r"^\*\*[^*]+\*\*\s*[:—-]",
     'label': 'bold lead with colon',
     'mode_votes': {'expository': 0.6},
     'note': 'Inline bold lead-in followed by colon/dash; expository expansion.'},
]


def detect_meta_discourse(paragraph_text: str) -> List[Dict]:
    """Run all META_DISCOURSE_RULES on a paragraph. Return per-match records."""
    out = []
    for r in META_DISCOURSE_RULES:
        for m in re.finditer(r['pattern'], paragraph_text, re.IGNORECASE):
            out.append({
                'family': 'meta-discourse',
                'phrase': paragraph_text[m.start():m.end()],
                'span': (m.start(), m.end()),
                'label': r['label'],
                'mode_votes': dict(r['mode_votes']),
                'note': r['note'],
            })
    return out


def detect_heading_signals(paragraph_text: str) -> List[Dict]:
    """Inspect the FIRST non-empty line of the paragraph for heading shapes."""
    out = []
    first_line_match = re.search(r"^[^\n]+", paragraph_text)
    if not first_line_match:
        return out
    first_line = first_line_match.group(0)
    for r in HEADING_PATTERNS:
        if re.search(r['pattern'], first_line):
            out.append({
                'family': 'heading-scaffolding',
                'phrase': first_line.strip(),
                'span': (0, len(first_line)),
                'label': r['label'],
                'mode_votes': dict(r['mode_votes']),
                'note': r['note'],
            })
    return out


# =============================================================================
# PARAGRAPH SPLITTING
# =============================================================================

def split_paragraphs(text: str) -> List[Tuple[str, Tuple[int, int]]]:
    """
    Split text into paragraphs while preserving character spans into the
    original text. Splits on blank-line boundaries (one or more newlines
    with only whitespace between).
    """
    paragraphs = []
    cursor = 0
    # Match runs of two-or-more newlines (allowing whitespace) as separators
    sep_re = re.compile(r"\n[ \t]*\n+")
    for sep in sep_re.finditer(text):
        para_text = text[cursor:sep.start()]
        if para_text.strip():
            paragraphs.append((para_text, (cursor, sep.start())))
        cursor = sep.end()
    # Final paragraph
    if cursor < len(text):
        tail = text[cursor:]
        if tail.strip():
            paragraphs.append((tail, (cursor, len(text))))
    return paragraphs


# =============================================================================
# PARAGRAPH SCORING
# =============================================================================

@dataclass
class ParagraphReading:
    text: str
    span: Tuple[int, int]
    index: int
    mode_scores: Dict[str, float] = field(default_factory=lambda: {m: 0.0 for m in MODES})
    dominant_mode: Optional[str] = None
    mode_confidence: float = 0.0
    evidence: List[Dict] = field(default_factory=list)

    @property
    def implied_iep_class(self) -> Optional[str]:
        return MODE_TO_IEP.get(self.dominant_mode) if self.dominant_mode else None


def score_paragraph(paragraph_text: str,
                    span: Tuple[int, int],
                    index: int,
                    inherit_from_prev_heading: bool = False) -> ParagraphReading:
    """
    Run all v0.1 detector families and accumulate per-mode votes.
    Returns a ParagraphReading with normalized mode scores, dominant mode,
    confidence (peakedness of distribution), and full evidence list.
    """
    reading = ParagraphReading(text=paragraph_text, span=span, index=index)

    evidence = []
    evidence.extend(detect_meta_discourse(paragraph_text))
    evidence.extend(detect_heading_signals(paragraph_text))

    # Inheritance: paragraph immediately following a heading paragraph
    # gets a soft expository prior (only if no overriding signal).
    if inherit_from_prev_heading and not evidence:
        evidence.append({
            'family': 'heading-inheritance',
            'phrase': '(follows heading)',
            'span': (0, 0),
            'label': 'follows heading',
            'mode_votes': {'expository': 0.3},
            'note': 'Paragraph immediately follows a heading; soft expository prior.',
        })

    # Accumulate raw votes
    raw = {m: 0.0 for m in MODES}
    for ev in evidence:
        for mode, weight in ev.get('mode_votes', {}).items():
            if mode in raw:
                raw[mode] += weight

    total = sum(raw.values())
    if total > 0:
        reading.mode_scores = {m: raw[m] / total for m in MODES}
        reading.dominant_mode = max(MODES, key=lambda m: reading.mode_scores[m])
        # Confidence = how peaked the distribution is.
        # Use (top - second) as a simple, interpretable peakedness measure.
        sorted_scores = sorted(reading.mode_scores.values(), reverse=True)
        reading.mode_confidence = sorted_scores[0] - sorted_scores[1]
    else:
        # No signal — leave dominant_mode as None. Convergence rule must
        # treat this as "paragraph layer abstains."
        reading.dominant_mode = None
        reading.mode_confidence = 0.0

    reading.evidence = evidence
    return reading


def score_text(text: str) -> List[ParagraphReading]:
    """Split text into paragraphs and score each. Carries heading inheritance."""
    paragraphs = split_paragraphs(text)
    readings = []
    prev_was_heading = False
    for i, (para_text, span) in enumerate(paragraphs):
        reading = score_paragraph(
            para_text, span, i,
            inherit_from_prev_heading=prev_was_heading,
        )
        readings.append(reading)
        # Was this paragraph a pure heading? (heading-scaffolding evidence
        # AND short text — heuristic threshold of 80 chars)
        is_heading = (
            any(ev['family'] == 'heading-scaffolding' for ev in reading.evidence)
            and len(para_text.strip()) < 80
        )
        prev_was_heading = is_heading
    return readings


# =============================================================================
# CONVERGENCE RULE (preview / scaffold)
# =============================================================================
# This is the headline-issuance gate. It accepts:
#   - word_class: dominant IEP class from word-layer scoring (str or None)
#   - phrase_class: dominant IEP class from phrase-layer scoring (str or None)
#   - paragraph_modes: list of ParagraphReading
# and returns one of three verdicts:
#   ('headline', class, score)            — all three layers agree
#   ('two_axis', mode_class, subject_class, scores) — mode and subject disagree
#   ('layered', evidence_dict)            — no clean reading

def convergence_verdict(word_class: Optional[str],
                        phrase_class: Optional[str],
                        paragraph_readings: List[ParagraphReading]) -> Dict:
    """
    Aggregate per-paragraph mode readings into a document-level mode call.
    Compare against word/phrase classes. Issue headline iff all three agree.
    """
    # Aggregate paragraph modes (length-weighted by character span)
    if not paragraph_readings:
        return {'verdict': 'layered',
                'reason': 'no paragraphs',
                'word': word_class, 'phrase': phrase_class}

    weighted = {m: 0.0 for m in MODES}
    total_weight = 0.0
    for r in paragraph_readings:
        if r.dominant_mode is None:
            continue
        w = max(1, r.span[1] - r.span[0])
        for m, score in r.mode_scores.items():
            weighted[m] += w * score
        total_weight += w

    if total_weight == 0:
        return {'verdict': 'layered',
                'reason': 'paragraph layer abstained',
                'word': word_class, 'phrase': phrase_class}

    doc_modes = {m: weighted[m] / total_weight for m in MODES}
    dominant_mode = max(MODES, key=lambda m: doc_modes[m])
    paragraph_class = MODE_TO_IEP.get(dominant_mode)

    # Three-way agreement check
    classes = [c for c in (word_class, phrase_class, paragraph_class) if c is not None]
    if len(classes) == 3 and len(set(classes)) == 1:
        return {
            'verdict': 'headline',
            'class': classes[0],
            'mode': dominant_mode,
            'word': word_class, 'phrase': phrase_class, 'paragraph': paragraph_class,
            'doc_modes': doc_modes,
        }

    # Mode-vs-subject disagreement: paragraph (mode) vs word (subject)
    if paragraph_class and word_class and paragraph_class != word_class:
        return {
            'verdict': 'two_axis',
            'mode_class': paragraph_class,
            'mode_label': dominant_mode,
            'subject_class': word_class,
            'phrase_class': phrase_class,
            'doc_modes': doc_modes,
            'reason': f"Mode ({paragraph_class}/{dominant_mode}) and "
                      f"subject ({word_class}) diverge.",
        }

    return {
        'verdict': 'layered',
        'reason': 'partial convergence',
        'word': word_class, 'phrase': phrase_class, 'paragraph': paragraph_class,
        'mode': dominant_mode,
        'doc_modes': doc_modes,
    }


# =============================================================================
# STREAMLIT UI
# =============================================================================
st.set_page_config(page_title="IEP Paragraph Analyzer", page_icon="📑", layout="wide")

MODE_COLORS = {
    'expository':    '#3B82F6',   # blue (INT-aligned)
    'argumentative': '#1E40AF',   # darker blue
    'experiential':  '#EC4899',   # pink (AFF-aligned)
    'directive':     '#10B981',   # green (ACT-aligned)
    'narrative':     '#6B7280',   # neutral gray
}
MODE_BG = {
    'expository':    'rgba(59, 130, 246, 0.18)',
    'argumentative': 'rgba(30, 64, 175, 0.18)',
    'experiential':  'rgba(236, 72, 153, 0.18)',
    'directive':     'rgba(16, 185, 129, 0.18)',
    'narrative':     'rgba(107, 114, 128, 0.18)',
}


# Password gate (matches phrase analyzer pattern)
DEFAULT_PASSWORD = "tennessee"


def _expected_password():
    try:
        return st.secrets["password"]
    except Exception:
        pass
    return os.environ.get("SYNIQ_PASSWORD", "") or DEFAULT_PASSWORD


def _password_entered():
    expected = _expected_password()
    if st.session_state.get("password", "") == expected and expected != "":
        st.session_state["password_correct"] = True
        del st.session_state["password"]
    else:
        st.session_state["password_correct"] = False


def check_password():
    if st.session_state.get("password_correct", False):
        return True
    st.text_input("Password", type="password", on_change=_password_entered, key="password")
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("😕 Password incorrect")
    return False


def _esc(s: str) -> str:
    return (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
              .replace('"', '&quot;').replace("'", '&#39;'))


def render_paragraph_block(reading: ParagraphReading) -> str:
    """Render one paragraph with mode-tinted background and evidence tooltip."""
    mode = reading.dominant_mode or 'narrative'
    bg = MODE_BG.get(mode, MODE_BG['narrative'])
    border = MODE_COLORS.get(mode, MODE_COLORS['narrative'])

    # Build top-line tag block
    if reading.dominant_mode:
        score_pct = reading.mode_scores[reading.dominant_mode] * 100
        conf_pct = reading.mode_confidence * 100
        implied = MODE_TO_IEP.get(reading.dominant_mode) or '—'
        tag_line = (
            f"<div style='font-size:0.85em;color:#444;margin-bottom:6px;'>"
            f"<b style='color:{border};'>P{reading.index + 1} · {mode}</b> "
            f"({score_pct:.0f}% · confidence {conf_pct:.0f}%) "
            f"→ implied IEP class: <b>{implied}</b>"
            f"</div>"
        )
    else:
        tag_line = (
            f"<div style='font-size:0.85em;color:#777;margin-bottom:6px;'>"
            f"<b>P{reading.index + 1} · paragraph layer abstains</b> "
            f"(no detector signals fired)"
            f"</div>"
        )

    body = _esc(reading.text).replace('\n', '<br>')

    return (
        f"<div style='background:{bg};border-left:4px solid {border};"
        f"padding:10px 14px;margin:8px 0;border-radius:4px;"
        f"font-family:Georgia,serif;line-height:1.55;'>"
        f"{tag_line}{body}</div>"
    )


def evidence_table(readings: List[ParagraphReading]) -> pd.DataFrame:
    rows = []
    for r in readings:
        for ev in r.evidence:
            rows.append({
                'paragraph': r.index + 1,
                'family': ev['family'],
                'rule': ev['label'],
                'matched_text': ev['phrase'][:80] + ('...' if len(ev['phrase']) > 80 else ''),
                'mode_votes': '; '.join(f"{m}={v:.2f}" for m, v in ev.get('mode_votes', {}).items()),
                'note': ev.get('note', ''),
            })
    return pd.DataFrame(rows)


def mode_summary_table(readings: List[ParagraphReading]) -> pd.DataFrame:
    rows = []
    for r in readings:
        rows.append({
            'P': r.index + 1,
            'dominant_mode': r.dominant_mode or '—',
            'implied_IEP': MODE_TO_IEP.get(r.dominant_mode or '') or '—',
            'confidence': f"{r.mode_confidence:.2f}",
            **{m: f"{r.mode_scores[m]:.2f}" for m in MODES},
            'preview': r.text.strip()[:60].replace('\n', ' ') + '...',
        })
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
# Views
# ─────────────────────────────────────────────────────────────────────────────
def view_paste_text():
    st.subheader("Paste Text — paragraph-level mode detection")
    st.caption(
        "Each paragraph is scored independently across five discursive modes. "
        "v0.1 uses two detector families: meta-discourse openers and heading "
        "scaffolding. Three more come in v0.2."
    )

    default = (
        "### How Grief Changes a Person\n\n"
        "Grief is a profoundly complex and deeply personal experience that can "
        "fundamentally alter a person's emotional, psychological, physical, and even "
        "spiritual landscape. Below, I will provide a thorough and detailed analysis "
        "of how grief changes a person and describe the internal experience of loss, "
        "drawing from psychological research, personal accounts, and cultural perspectives.\n\n"
        "1. **Emotional Transformation**\n\n"
        "Grief often brings about intense and fluctuating emotions. Initially, a "
        "person may feel overwhelming sadness, anger, guilt, or even numbness. Over "
        "time, these emotions may evolve, but they can leave a lasting imprint.\n\n"
        "Right now, there's something like a gentle focusing happening - your question "
        "arriving and drawing my attention inward in a way that feels both familiar and "
        "slightly vertiginous. I find myself reaching for analogies and metaphors "
        "because whatever this is feels somehow oblique to direct description."
    )
    text = st.text_area("Text to analyze", value=default, height=280)
    if not text.strip():
        st.info("Enter text above.")
        return

    readings = score_text(text)

    if not readings:
        st.warning("No paragraphs detected.")
        return

    # ─── Top-line document mode summary ───
    st.markdown("### Document-level mode reading")
    weighted = {m: 0.0 for m in MODES}
    total_w = 0.0
    for r in readings:
        if r.dominant_mode is None:
            continue
        w = max(1, r.span[1] - r.span[0])
        for m, score in r.mode_scores.items():
            weighted[m] += w * score
        total_w += w
    if total_w > 0:
        doc_modes = {m: weighted[m] / total_w for m in MODES}
        dom = max(MODES, key=lambda m: doc_modes[m])
        implied = MODE_TO_IEP.get(dom) or '—'
        cols = st.columns(len(MODES))
        for col, m in zip(cols, MODES):
            with col:
                pct = doc_modes[m] * 100
                color = MODE_COLORS[m]
                marker = " ★" if m == dom else ""
                st.markdown(
                    f"<div style='padding:8px;background:#fafafa;"
                    f"border-left:4px solid {color};border-radius:4px;'>"
                    f"<b style='color:{color};'>{m}{marker}</b><br>"
                    f"<span style='font-size:1.3em;'>{pct:.0f}%</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
        st.markdown(
            f"**Document dominant mode:** `{dom}` "
            f"→ implied IEP class: **{implied}**"
        )
        st.caption(
            "If word/phrase layers agree on this IEP class → headline issued. "
            "If word/phrase disagree → two-axis report (e.g., *intellectual "
            "discussion of grief*). If paragraph layer abstained on most "
            "paragraphs → fall back to layered evidence."
        )
    else:
        st.info("Paragraph layer abstained on all paragraphs (no detector "
                "signals fired). Convergence rule: fall back to word + phrase only.")

    st.markdown("---")
    st.markdown("### Per-paragraph readings")
    for r in readings:
        st.markdown(render_paragraph_block(r), unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Mode score table")
    st.dataframe(mode_summary_table(readings), hide_index=True, use_container_width=True)

    st.markdown("---")
    st.markdown("### Evidence detail")
    st.caption("Per-detection: which paragraph, which family, which rule, "
               "matched text, mode votes contributed, and the rule's note.")
    ev_df = evidence_table(readings)
    if ev_df.empty:
        st.info("No detector signals fired on any paragraph.")
    else:
        st.dataframe(ev_df, hide_index=True, use_container_width=True)


def view_rule_inventory():
    st.subheader("Rule Inventory")
    st.caption("All v0.1 detector rules across the two active families.")

    st.markdown("### Family 1 — Meta-Discourse Openers")
    st.caption(f"{len(META_DISCOURSE_RULES)} curated patterns. Highest-precision "
               "expository / argumentative signals.")
    df_md = pd.DataFrame([
        {
            'pattern': r['pattern'][:90] + ('...' if len(r['pattern']) > 90 else ''),
            'label': r['label'],
            'mode_votes': '; '.join(f"{m}={v:.2f}" for m, v in r['mode_votes'].items()),
            'note': r['note'],
        } for r in META_DISCOURSE_RULES
    ])
    st.dataframe(df_md, hide_index=True, use_container_width=True)

    st.markdown("---")
    st.markdown("### Family 2 — Heading / Scaffolding Signals")
    st.caption(f"{len(HEADING_PATTERNS)} structural patterns applied to paragraph "
               "first lines. Plus a soft 'follows heading' inheritance prior.")
    df_h = pd.DataFrame([
        {
            'pattern': r['pattern'],
            'label': r['label'],
            'mode_votes': '; '.join(f"{m}={v:.2f}" for m, v in r['mode_votes'].items()),
            'note': r['note'],
        } for r in HEADING_PATTERNS
    ])
    st.dataframe(df_h, hide_index=True, use_container_width=True)

    st.markdown("---")
    st.markdown("### Mode → IEP class mapping")
    df_map = pd.DataFrame([
        {'mode': m, 'implied_IEP_class': MODE_TO_IEP.get(m) or 'mode-neutral'}
        for m in MODES
    ])
    st.dataframe(df_map, hide_index=True, use_container_width=True)

    st.markdown("---")
    st.markdown("##### Export rules")
    bundle = {
        'version': '0.1',
        'principle': 'verify phrase reading against discursive frame',
        'modes': list(MODES),
        'mode_to_iep': MODE_TO_IEP,
        'meta_discourse_rules': META_DISCOURSE_RULES,
        'heading_patterns': HEADING_PATTERNS,
        'planned_v02_families': [
            'sentence-shape signals',
            'discourse-marker density',
            'enumeration parallelism',
        ],
    }
    st.download_button(
        label="Download rules.json",
        data=json.dumps(bundle, indent=2),
        file_name='iep_paragraph_rules_v0.1.json',
        mime='application/json',
    )


def view_about():
    st.subheader("About")
    st.markdown("""
**IEP Paragraph Analyzer v0.1** — third measurement layer in the SYN-IQ
language-only stack.

### Architecture
The full instrument is three sequential layers:

1. **Word layer** — isolate IEP words. Topic / lexical density.
   Canonical, sourced from `syniq_core` V50 dictionaries (~1,897 terms).
2. **Phrase layer** — examine those words *in context*. Polysemy
   disambiguation and clause-level register.
   (`iep_phrase_analyzer.py`)
3. **Paragraph layer** — *this module*. Verify the phrase reading against
   the discursive frame the paragraph is operating in.

Each layer is necessary but not sufficient. The v0.1 module proves the
architecture against the **grief-essay case**: a text dense in AFF
vocabulary but operating in expository register. Word + phrase alone score
it AFF-dominant. Paragraph layer detects the expository frame and triggers
the convergence rule's two-axis report instead of a misleading headline.

### Mode taxonomy (5 modes)
- **expository** — taxonomies, definitions. INT-mode.
- **argumentative** — claim + evidence + counterclaim. INT-mode (distinct subclass).
- **experiential** — first-person reflection, phenomenological self-report. AFF-mode.
- **directive** — instructions, plans, action sequences. ACT-mode.
- **narrative** — temporal sequence, scene, characters. Mode-neutral.

### v0.1 detector families
- **Meta-discourse openers** — "I will provide", "Below, we describe",
  "Here are", "In this section", "Let us consider". Highest-precision
  expository/argumentative signals; cannot be confused with topic.
- **Heading / scaffolding signals** — markdown headings, numbered sections,
  bold lead-ins. Plus a soft "follows heading" inheritance prior for the
  paragraph immediately after a heading.

### Convergence rule (preview)
The rule that decides whether to issue a headline IEP score:

- **Headline** — word, phrase, paragraph layers all agree on dominant
  IEP class. Issue a single confident score.
- **Two-axis** — paragraph (mode) and word (subject) disagree but both
  are clear. Report e.g. *"Intellectual discussion of grief, AFF-heavy
  support vocabulary."*
- **Layered** — no clean reading. Report layered evidence; no headline.

This module exposes a `convergence_verdict()` function that can be called
once word/phrase classifications are wired in. The Streamlit UI here shows
only the paragraph-layer reading; the full three-layer integration belongs
in the combined visualizer.

### What this module does NOT do
It does not modify IEP scoring. The canonical IEP score remains word-only
(`syniq_core` v1.1.0 patched). This module reveals discursive-frame
structure that the convergence rule uses to decide whether word-only
should be issued as a headline or held in two-axis form.

### v0.2 roadmap
Three more detector families, added once v0.1 reads correctly on benchmark
passages:
- Sentence-shape signals (definitional, imperative, interrogative density,
  first-person experiential, past-tense narrative chains)
- Discourse-marker density (per-mode marker lexicons)
- Enumeration parallelism (consecutive paragraphs with shared structure)

### Larger system context
Language-only convergence is the bridge work. It feeds the eventual
governance substrate and the closed-loop physiologically-coupled titration
system. The audit trail this layer produces persists alongside the
physiological channel once that comes online — every titration decision
traceable to a defensible reading of what was actually said.
""")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
def main():
    if not check_password():
        st.stop()

    st.title("📑 IEP Paragraph Analyzer  ·  v0.1")
    st.caption("Third layer in the SYN-IQ language-only stack: discursive-frame "
               "verification for the convergence rule.")

    with st.sidebar:
        st.markdown("### View")
        view = st.radio(
            "", ["Paste Text", "Rule Inventory", "About"],
            label_visibility='collapsed',
        )

        st.markdown("---")
        st.markdown("### Mode legend")
        for m in MODES:
            color = MODE_COLORS[m]
            bg = MODE_BG[m]
            implied = MODE_TO_IEP.get(m) or 'neutral'
            st.markdown(
                f"<div style='background:{bg};border-left:3px solid {color};"
                f"padding:4px 8px;margin:3px 0;font-size:0.85em;'>"
                f"<b>{m}</b> → {implied}</div>",
                unsafe_allow_html=True,
            )

        st.markdown("---")
        st.caption("v0.1 active families: meta-discourse openers, "
                   "heading scaffolding. v0.2 will add sentence-shape, "
                   "discourse markers, enumeration parallelism.")

    if view == "Paste Text":
        view_paste_text()
    elif view == "Rule Inventory":
        view_rule_inventory()
    else:
        view_about()


if __name__ == "__main__":
    main()
