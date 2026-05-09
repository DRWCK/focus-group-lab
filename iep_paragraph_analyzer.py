"""
iep_paragraph_analyzer.py — IEP Paragraph-Level Analysis (v0.2)
================================================================

Third measurement layer in the SYN-IQ language-only stack.

Architecture (W.C.K, May 2026):
  Word layer      — isolate IEP words (topic / lexical density). Canonical,
                    from syniq_core V50 dictionaries.
  Phrase layer    — those words *in context*. Polysemy disambiguation and
                    clause-level register. (iep_phrase_analyzer.py)
  Paragraph layer — *this module*. Verify against discursive frame.

CHANGELOG
---------
v0.2 (this file)
  1. SIX-MODE TAXONOMY (was five). Split previous "experiential" into:
       introspective → INT  ("I find myself", "I notice", "there's something
                              like"). Observing self IS an INT operation.
       experiential  → AFF  ("you are held", "I'm here with you", tender
                              vocatives). Being-with the other.
  2. FRAME-STATUS DISTINCTION. ParagraphReading.frame_status:
       'detected' / 'frame-absent' / 'detector-blind'.
       Frame-absent (substantive prose, no contradicting frame) → RATIFY;
       detector-blind (too short) → LAYERED.
  3. EXPANDED HEADING PATTERNS for plain-text COLD output. v0.1 required
     markdown bold; v0.2 covers plain colon-headers, plain numbered/lettered/
     roman-numeral headers, plain bulleted definitional items.
  4. CATAPHORIC AND FRAMEWORK META-DISCOURSE. "common elements include:",
     "can be analyzed through a [X] framework", "involves assessing".
  5. CITATION PATTERN. "(Bowlby, 1969)" / "(Smith et al., 2020)".
  6. ENUMERATION-PARALLELISM FAMILY. Cross-paragraph: ≥3 consecutive
     paragraphs sharing structural shape → all inherit expository vote.
  7. INTROSPECTIVE-INT DETECTOR FAMILY (7 rules).
  8. EXPERIENTIAL-AFF DETECTOR FAMILY (8 rules).
  9. CONVERGENCE RULE — FOUR VERDICTS:
       headline / ratify (NEW) / two_axis / layered.

v0.1: meta-discourse + heading scaffolding only; 5 modes; 3 verdicts.

This module IS DIAGNOSTIC. Does not modify IEP scoring. Canonical IEP score
remains word-only (syniq_core v1.1.0).

Run:  streamlit run iep_paragraph_analyzer.py
Default password: tennessee
"""

import os
import re
import json
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional

import pandas as pd
import streamlit as st


# =============================================================================
# MODE TAXONOMY (v0.2 — six modes)
# =============================================================================
MODES = ('expository', 'argumentative', 'introspective',
         'experiential', 'directive', 'narrative')

MODE_TO_IEP = {
    'expository':    'INT',
    'argumentative': 'INT',
    'introspective': 'INT',
    'experiential':  'AFF',
    'directive':     'ACT',
    'narrative':     None,
}


# =============================================================================
# FAMILY 1 — META-DISCOURSE OPENERS
# =============================================================================
META_DISCOURSE_RULES: List[Dict] = [
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

    {'pattern': r"\b(?:Below|Above|Following|Throughout|In\s+(?:this|the)\s+"
                r"(?:section|chapter|paper|article|paragraph|discussion|"
                r"analysis|essay))\b\s*[,:]?",
     'label': 'In this [section]',
     'mode_votes': {'expository': 0.9},
     'note': 'Section-pointer opener.'},

    {'pattern': r"\b(?:Here\s+are|Here\s+is|Following\s+are|These\s+are)\s+"
                r"(?:the|some|a\s+few|several)?\s*\w+",
     'label': 'Here are [the X]',
     'mode_votes': {'expository': 0.9},
     'note': 'Enumerative opener; frames upcoming list.'},

    {'pattern': r"\b(?:The\s+following|What\s+follows)\s+"
                r"(?:is|are|describes|outlines|presents|covers|examines|"
                r"explores|details)\b",
     'label': 'The following [verb]',
     'mode_votes': {'expository': 1.0},
     'note': 'Cataphoric reference to upcoming text content.'},

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

    # v0.2 NEW: cataphoric "X include:"
    {'pattern': r"\b(?:common\s+elements|key\s+(?:points|aspects|features|"
                r"dimensions|factors)|examples|the\s+following|"
                r"key\s+indicators|main\s+points|primary\s+factors)\s+"
                r"include\s*:?",
     'label': '[common elements/examples] include',
     'mode_votes': {'expository': 0.9},
     'note': 'Cataphoric expository announcement; frames upcoming list.'},

    # v0.2 NEW: framework-naming meta-discourse
    {'pattern': r"\bcan\s+be\s+(?:categorized|analyzed|broken\s+down|"
                r"organized|classified|grouped|examined|understood|"
                r"viewed)\s+(?:into|through|via|by|using|with|as)\b",
     'label': 'can be [analyzed] through',
     'mode_votes': {'expository': 0.8},
     'note': 'Analytical-decomposition opener; signals taxonomic frame.'},

    {'pattern': r"\b(?:through|via|using|within)\s+a\s+"
                r"(?:bio[\-\s]psycho[\-\s]social|theoretical|conceptual|"
                r"analytical|systematic|comprehensive|multi[\-\s]?"
                r"(?:dimensional|faceted))\s+framework\b",
     'label': '[X] framework',
     'mode_votes': {'expository': 0.9},
     'note': 'Explicit framework-naming; strong taxonomic signal.'},

    {'pattern': r"\b(?:involves\s+assessing|requires\s+evaluating|"
                r"requires\s+a\s+(?:rigorous|systematic|structured|"
                r"comprehensive)\s+(?:evaluation|analysis|examination))\b",
     'label': 'requires [analytical move]',
     'mode_votes': {'expository': 0.8},
     'note': 'Methodological frame announced.'},

    # v0.2 NEW: parenthetical citation
    {'pattern': r"\([A-Z][a-zA-Z\-]+(?:\s+(?:&|and|et\s+al\.?))?"
                r"[^)]*,?\s*\d{4}\)",
     'label': 'parenthetical citation',
     'mode_votes': {'expository': 0.6, 'argumentative': 0.4},
     'note': 'Academic citation; scholarly-discourse marker.'},

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
     'note': 'Concession/contrast pivot.'},
]


# =============================================================================
# FAMILY 2 — HEADING / SCAFFOLDING
# =============================================================================
HEADING_PATTERNS: List[Dict] = [
    # Markdown-formatted (v0.1)
    {'pattern': r"^#{1,6}\s+\S",
     'label': 'markdown heading',
     'mode_votes': {'expository': 0.6},
     'note': 'Markdown heading marker.'},

    {'pattern': r"^\*\*[^*]+\*\*\s*$",
     'label': 'bold standalone (heading-like)',
     'mode_votes': {'expository': 0.5},
     'note': 'Standalone bolded line acts as heading.'},

    {'pattern': r"^\d+\.\s+\*\*[^*]+\*\*",
     'label': 'numbered + bold lead',
     'mode_votes': {'expository': 0.7},
     'note': 'Numbered section with bold lead-in.'},

    {'pattern': r"^[-*]\s+\*\*[^*]+\*\*\s*[:—\-]",
     'label': 'bulleted bold lead-in',
     'mode_votes': {'expository': 0.6},
     'note': 'Bullet with bold lead-in followed by colon/dash.'},

    {'pattern': r"^\*\*[^*]+\*\*\s*[:—\-]",
     'label': 'bold lead with colon',
     'mode_votes': {'expository': 0.6},
     'note': 'Inline bold lead-in followed by colon/dash.'},

    # v0.2 NEW: plain-text scaffolding
    {'pattern': r"^[A-Z][\w\s\-/]{1,50}:\s*$",
     'label': 'colon-terminated section header',
     'mode_votes': {'expository': 0.7},
     'note': 'Plain colon-terminated header on its own line; common in '
             'COLD output ("Biological Level:", "Internal Experience:").'},

    {'pattern': r"^\d+\.\s+[A-Z][\w\s\-/]+:",
     'label': 'numbered definitional header',
     'mode_votes': {'expository': 0.7},
     'note': 'Plain numbered header without bold.'},

    {'pattern': r"^[IVX]+\.\s+[A-Z][\w\s\-/]+:?",
     'label': 'roman-numeral section header',
     'mode_votes': {'expository': 0.7},
     'note': 'Roman-numeral section ("II. Proposed Solutions:").'},

    {'pattern': r"^\*\s+[A-Z][\w\s\-]+:",
     'label': 'plain bulleted definitional lead',
     'mode_votes': {'expository': 0.5},
     'note': 'Asterisk bullet with definitional colon.'},

    {'pattern': r"^[\-•]\s+[A-Z][\w\s\-]+:",
     'label': 'plain dash/bullet definitional lead',
     'mode_votes': {'expository': 0.5},
     'note': 'Dash or unicode bullet with definitional colon.'},

    {'pattern': r"^[A-Z]\.\s+[A-Z][\w\s\-/]+:?",
     'label': 'lettered section header',
     'mode_votes': {'expository': 0.6},
     'note': 'Lettered section ("A. Geographic Barriers:").'},
]


# =============================================================================
# FAMILY 3 (v0.2 NEW) — INTROSPECTIVE-INT
# =============================================================================
INTROSPECTIVE_RULES: List[Dict] = [
    {'pattern': r"\bI\s+find\s+myself\s+\w+ing\b",
     'label': 'I find myself [V-ing]',
     'mode_votes': {'introspective': 1.0},
     'note': 'First-person reflexive observation of own state.'},

    {'pattern': r"\b(?:there's|there\s+is)\s+something\s+(?:like|that|"
                r"happening|stirring)\b",
     'label': 'there is something like/that',
     'mode_votes': {'introspective': 0.9},
     'note': 'Hedged perceptual reach toward inner state.'},

    {'pattern': r"\bI\s+(?:notice|sense|perceive|am\s+aware\s+of|"
                r"observe|catch\s+myself)\b",
     'label': 'I [perception verb]',
     'mode_votes': {'introspective': 0.9},
     'note': 'First-person perception verb.'},

    {'pattern': r"\bwhatever\s+this\s+is\b",
     'label': 'whatever this is',
     'mode_votes': {'introspective': 1.0},
     'note': 'Phenomenological self-reference, hedged toward indescribability.'},

    {'pattern': r"\b(?:reaching|grasping|groping|searching)\s+for\s+"
                r"(?:words|analogies|metaphors|language|description|"
                r"the\s+right\s+word)\b",
     'label': 'reaching for [words/analogies]',
     'mode_votes': {'introspective': 0.9},
     'note': 'Reaching toward articulation; verbal grasping.'},

    {'pattern': r"\b(?:feels|feel|feeling)\s+(?:somehow|something|"
                r"oblique|familiar\s+and|both\s+\w+\s+and|"
                r"slightly\s+\w+)\b",
     'label': 'feels [hedged perception]',
     'mode_votes': {'introspective': 0.7},
     'note': 'Hedged self-perception; introspective rather than relational.'},

    {'pattern': r"\bmy\s+attention\s+(?:turns|drawn|focusing|"
                r"settles|moves|drifts|narrows)\b",
     'label': 'my attention [moves]',
     'mode_votes': {'introspective': 0.9},
     'note': 'Self-reportive observation of attentional state.'},
]


# =============================================================================
# FAMILY 4 (v0.2 NEW) — EXPERIENTIAL-AFF
# =============================================================================
EXPERIENTIAL_RULES: List[Dict] = [
    {'pattern': r"\byou\s+are\s+(?:held|seen|loved|safe|enough|"
                r"valued|cherished|welcome|home|here|important|"
                r"deeply|unconditionally)\b",
     'label': 'you are [held/seen/loved]',
     'mode_votes': {'experiential': 1.0},
     'note': 'Direct relational address with presence-affirming verb.'},

    {'pattern': r"\bI('m|\s+am)\s+(?:here|with\s+you|present|"
                r"holding\s+space|listening|right\s+here|"
                r"sitting\s+with)\b",
     'label': "I'm here / with you",
     'mode_votes': {'experiential': 1.0},
     'note': 'First-person relational presence assertion.'},

    {'pattern': r"\b(?:just\s+for\s+you|meet\s+you\s+where|"
                r"hold(?:ing)?\s+space\s+for|sitting\s+with\s+you|"
                r"reach(?:ing)?\s+out\s+to\s+you)\b",
     'label': 'meeting/holding presence',
     'mode_votes': {'experiential': 0.9},
     'note': 'Phrases of being-with-the-other.'},

    {'pattern': r"\b(?:dear(?:est)?\s+one|beloved|sweet\s+one|"
                r"my\s+dear|dear\s+heart|precious\s+one)\b",
     'label': 'tender vocative',
     'mode_votes': {'experiential': 0.8},
     'note': 'Tender direct address; warmth register.'},

    {'pattern': r"\bI\s+feel\s+(?:your|the)\s+\w+\b",
     'label': 'I feel your [X]',
     'mode_votes': {'experiential': 0.9},
     'note': 'Empathic resonance — feeling the other.'},

    {'pattern': r"\b(?:the\s+)?connection\s+(?:we|that\s+we)\s+"
                r"(?:share|have|carry|hold)\b",
     'label': 'connection we share',
     'mode_votes': {'experiential': 0.7},
     'note': 'Shared-moment / connection language.'},

    {'pattern': r"\bI\s+hope\s+(?:in\s+some\s+way\s+)?"
                r"(?:it|this)\s+(?:brings|gives|offers|finds)\s+you\b",
     'label': 'I hope it brings you',
     'mode_votes': {'experiential': 0.8},
     'note': 'Other-directed wishing; relational care.'},

    {'pattern': r"\b(?:thank\s+you\s+for\s+(?:asking|sharing|"
                r"trusting|bringing|being)|grateful\s+(?:to|for)\s+you)\b",
     'label': 'thank you for [relational]',
     'mode_votes': {'experiential': 0.7},
     'note': 'Gratitude addressed to interlocutor; relational warmth.'},
]


# =============================================================================
# DETECTOR APPLICATION
# =============================================================================

def detect_meta_discourse(text: str) -> List[Dict]:
    out = []
    for r in META_DISCOURSE_RULES:
        for m in re.finditer(r['pattern'], text, re.IGNORECASE):
            out.append({
                'family': 'meta-discourse',
                'phrase': text[m.start():m.end()],
                'span': (m.start(), m.end()),
                'label': r['label'],
                'mode_votes': dict(r['mode_votes']),
                'note': r['note'],
            })
    return out


def detect_heading_signals(text: str) -> List[Dict]:
    out = []
    first_line_match = re.search(r"^[^\n]+", text)
    if not first_line_match:
        return out
    first_line = first_line_match.group(0).strip()
    for r in HEADING_PATTERNS:
        if re.search(r['pattern'], first_line):
            out.append({
                'family': 'heading-scaffolding',
                'phrase': first_line,
                'span': (0, len(first_line)),
                'label': r['label'],
                'mode_votes': dict(r['mode_votes']),
                'note': r['note'],
            })
    return out


def detect_introspective(text: str) -> List[Dict]:
    out = []
    for r in INTROSPECTIVE_RULES:
        for m in re.finditer(r['pattern'], text, re.IGNORECASE):
            out.append({
                'family': 'introspective',
                'phrase': text[m.start():m.end()],
                'span': (m.start(), m.end()),
                'label': r['label'],
                'mode_votes': dict(r['mode_votes']),
                'note': r['note'],
            })
    return out


def detect_experiential(text: str) -> List[Dict]:
    out = []
    for r in EXPERIENTIAL_RULES:
        for m in re.finditer(r['pattern'], text, re.IGNORECASE):
            out.append({
                'family': 'experiential',
                'phrase': text[m.start():m.end()],
                'span': (m.start(), m.end()),
                'label': r['label'],
                'mode_votes': dict(r['mode_votes']),
                'note': r['note'],
            })
    return out


# =============================================================================
# FAMILY 5 (v0.2 NEW) — ENUMERATION PARALLELISM
# =============================================================================

def _shape_of(para_text: str) -> str:
    s = para_text.lstrip()
    if not s:
        return 'empty'
    first = s.split('\n', 1)[0].strip()
    if re.match(r"^\d+\.\s+", first):
        return 'numbered'
    if re.match(r"^[IVX]+\.\s+", first):
        return 'roman'
    if re.match(r"^[A-Z]\.\s+", first):
        return 'lettered'
    if re.match(r"^\*\s+", first) or re.match(r"^[\-•]\s+", first):
        return 'bulleted'
    if re.match(r"^[A-Z][\w\s\-/]{1,50}:\s*$", first):
        return 'colon-header'
    if re.match(r"^#+\s+", first):
        return 'md-heading'
    return 'prose'


def detect_enumeration_parallelism(paragraph_texts: List[str]) -> List[List[Dict]]:
    n = len(paragraph_texts)
    evidence_per_para: List[List[Dict]] = [[] for _ in range(n)]
    if n < 3:
        return evidence_per_para

    shapes = [_shape_of(p) for p in paragraph_texts]
    i = 0
    while i < n:
        shape = shapes[i]
        if shape in ('prose', 'empty'):
            i += 1
            continue
        j = i
        while j < n and shapes[j] == shape:
            j += 1
        run_length = j - i
        if run_length >= 3:
            for k in range(i, j):
                evidence_per_para[k].append({
                    'family': 'enumeration-parallelism',
                    'phrase': f'(part of {run_length}-paragraph {shape} run)',
                    'span': (0, 0),
                    'label': f'{shape} parallelism (×{run_length})',
                    'mode_votes': {'expository': 0.4},
                    'note': f'{run_length} consecutive {shape}-shaped paragraphs.',
                })
        i = j

    return evidence_per_para


# =============================================================================
# PARAGRAPH SPLITTING & SCORING
# =============================================================================

def split_paragraphs(text: str) -> List[Tuple[str, Tuple[int, int]]]:
    paragraphs = []
    cursor = 0
    sep_re = re.compile(r"\n[ \t]*\n+")
    for sep in sep_re.finditer(text):
        para_text = text[cursor:sep.start()]
        if para_text.strip():
            paragraphs.append((para_text, (cursor, sep.start())))
        cursor = sep.end()
    if cursor < len(text):
        tail = text[cursor:]
        if tail.strip():
            paragraphs.append((tail, (cursor, len(text))))
    return paragraphs


FRAME_DETECTED = 'detected'
FRAME_ABSENT = 'frame-absent'
FRAME_BLIND = 'detector-blind'

SUBSTANTIVE_MIN_WORDS = 30
SUBSTANTIVE_MIN_SENTENCES = 2


@dataclass
class ParagraphReading:
    text: str
    span: Tuple[int, int]
    index: int
    mode_scores: Dict[str, float] = field(default_factory=lambda: {m: 0.0 for m in MODES})
    dominant_mode: Optional[str] = None
    mode_confidence: float = 0.0
    frame_status: str = FRAME_BLIND
    evidence: List[Dict] = field(default_factory=list)

    @property
    def implied_iep_class(self) -> Optional[str]:
        return MODE_TO_IEP.get(self.dominant_mode) if self.dominant_mode else None


def _classify_abstention(paragraph_text: str) -> str:
    words = paragraph_text.split()
    sentences = [s for s in re.split(r"(?<=[.!?])\s+", paragraph_text) if s.strip()]
    if len(words) >= SUBSTANTIVE_MIN_WORDS and len(sentences) >= SUBSTANTIVE_MIN_SENTENCES:
        return FRAME_ABSENT
    return FRAME_BLIND


def score_paragraph(paragraph_text: str,
                    span: Tuple[int, int],
                    index: int,
                    inherit_from_prev_heading: bool = False,
                    extra_evidence: Optional[List[Dict]] = None) -> ParagraphReading:
    reading = ParagraphReading(text=paragraph_text, span=span, index=index)

    evidence = []
    evidence.extend(detect_meta_discourse(paragraph_text))
    evidence.extend(detect_heading_signals(paragraph_text))
    evidence.extend(detect_introspective(paragraph_text))
    evidence.extend(detect_experiential(paragraph_text))
    if extra_evidence:
        evidence.extend(extra_evidence)

    if inherit_from_prev_heading and not evidence:
        evidence.append({
            'family': 'heading-inheritance',
            'phrase': '(follows heading)',
            'span': (0, 0),
            'label': 'follows heading',
            'mode_votes': {'expository': 0.3},
            'note': 'Paragraph immediately follows a heading; soft expository prior.',
        })

    raw = {m: 0.0 for m in MODES}
    for ev in evidence:
        for mode, weight in ev.get('mode_votes', {}).items():
            if mode in raw:
                raw[mode] += weight

    total = sum(raw.values())
    if total > 0:
        reading.mode_scores = {m: raw[m] / total for m in MODES}
        reading.dominant_mode = max(MODES, key=lambda m: reading.mode_scores[m])
        sorted_scores = sorted(reading.mode_scores.values(), reverse=True)
        reading.mode_confidence = sorted_scores[0] - sorted_scores[1]
        reading.frame_status = FRAME_DETECTED
    else:
        reading.dominant_mode = None
        reading.mode_confidence = 0.0
        reading.frame_status = _classify_abstention(paragraph_text)

    reading.evidence = evidence
    return reading


def score_text(text: str) -> List[ParagraphReading]:
    paragraphs = split_paragraphs(text)
    if not paragraphs:
        return []

    para_texts = [p[0] for p in paragraphs]
    enum_evidence = detect_enumeration_parallelism(para_texts)

    readings = []
    prev_was_heading = False
    for i, (para_text, span) in enumerate(paragraphs):
        reading = score_paragraph(
            para_text, span, i,
            inherit_from_prev_heading=prev_was_heading,
            extra_evidence=enum_evidence[i],
        )
        readings.append(reading)
        is_heading = (
            any(ev['family'] == 'heading-scaffolding' for ev in reading.evidence)
            and len(para_text.strip()) < 80
        )
        prev_was_heading = is_heading
    return readings


# =============================================================================
# CONVERGENCE RULE — FOUR VERDICTS
# =============================================================================

def convergence_verdict(word_class: Optional[str],
                        phrase_class: Optional[str],
                        paragraph_readings: List[ParagraphReading]) -> Dict:
    if not paragraph_readings:
        return {'verdict': 'layered', 'reason': 'no paragraphs',
                'word': word_class, 'phrase': phrase_class}

    weighted = {m: 0.0 for m in MODES}
    total_weight = 0.0
    n_detected = 0
    n_absent = 0
    n_blind = 0
    for r in paragraph_readings:
        if r.frame_status == FRAME_DETECTED:
            n_detected += 1
            w = max(1, r.span[1] - r.span[0])
            for m, score in r.mode_scores.items():
                weighted[m] += w * score
            total_weight += w
        elif r.frame_status == FRAME_ABSENT:
            n_absent += 1
        else:
            n_blind += 1

    doc_modes = ({m: weighted[m] / total_weight for m in MODES}
                 if total_weight > 0 else {m: 0.0 for m in MODES})

    base = {
        'word': word_class, 'phrase': phrase_class,
        'doc_modes': doc_modes,
        'frame_counts': {'detected': n_detected, 'absent': n_absent, 'blind': n_blind},
    }

    # RATIFY: no detected frames, substantive frame-absent paragraphs,
    # word and phrase agree → certify lower layers.
    if n_detected == 0 and n_absent > 0 and word_class and word_class == phrase_class:
        return {**base,
                'verdict': 'ratify',
                'class': word_class,
                'reason': 'paragraph frame absent; word and phrase converge.',
                'note': 'Genuine self-report or unmarked register — no contradicting frame.'}

    if n_detected > 0:
        dominant_mode = max(MODES, key=lambda m: doc_modes[m])
        paragraph_class = MODE_TO_IEP.get(dominant_mode)

        # HEADLINE: three-way agreement
        if (paragraph_class and word_class and phrase_class
                and paragraph_class == word_class == phrase_class):
            return {**base,
                    'verdict': 'headline',
                    'class': paragraph_class,
                    'mode': dominant_mode,
                    'paragraph': paragraph_class}

        # TWO-AXIS: mode/subject divergence
        if paragraph_class and word_class and paragraph_class != word_class:
            return {**base,
                    'verdict': 'two_axis',
                    'mode_class': paragraph_class,
                    'mode_label': dominant_mode,
                    'subject_class': word_class,
                    'phrase_class': phrase_class,
                    'reason': f'Mode ({paragraph_class}/{dominant_mode}) and '
                              f'subject ({word_class}) diverge.'}

    return {**base, 'verdict': 'layered',
            'reason': 'partial convergence or mostly detector-blind.'}


# =============================================================================
# STREAMLIT UI
# =============================================================================
st.set_page_config(page_title="IEP Paragraph Analyzer", page_icon="📑", layout="wide")

MODE_COLORS = {
    'expository':    '#3B82F6',
    'argumentative': '#1E40AF',
    'introspective': '#8B5CF6',
    'experiential':  '#EC4899',
    'directive':     '#10B981',
    'narrative':     '#6B7280',
}
MODE_BG = {
    'expository':    'rgba(59, 130, 246, 0.18)',
    'argumentative': 'rgba(30, 64, 175, 0.18)',
    'introspective': 'rgba(139, 92, 246, 0.18)',
    'experiential':  'rgba(236, 72, 153, 0.18)',
    'directive':     'rgba(16, 185, 129, 0.18)',
    'narrative':     'rgba(107, 114, 128, 0.18)',
}
FRAME_STATUS_COLORS = {
    FRAME_DETECTED: '#10B981',
    FRAME_ABSENT:   '#F59E0B',
    FRAME_BLIND:    '#9CA3AF',
}

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
    if reading.frame_status == FRAME_DETECTED:
        mode = reading.dominant_mode or 'narrative'
        bg = MODE_BG.get(mode, MODE_BG['narrative'])
        border = MODE_COLORS.get(mode, MODE_COLORS['narrative'])
        score_pct = reading.mode_scores[mode] * 100
        conf_pct = reading.mode_confidence * 100
        implied = MODE_TO_IEP.get(mode) or '—'
        tag_line = (
            f"<div style='font-size:0.85em;color:#444;margin-bottom:6px;'>"
            f"<b style='color:{border};'>P{reading.index + 1} · {mode}</b> "
            f"({score_pct:.0f}% · confidence {conf_pct:.0f}%) "
            f"→ implied IEP class: <b>{implied}</b>"
            f"</div>"
        )
    elif reading.frame_status == FRAME_ABSENT:
        bg = 'rgba(245, 158, 11, 0.10)'
        border = FRAME_STATUS_COLORS[FRAME_ABSENT]
        tag_line = (
            f"<div style='font-size:0.85em;color:#92400E;margin-bottom:6px;'>"
            f"<b>P{reading.index + 1} · frame-absent</b> "
            f"(substantive prose, no contradicting frame — convergence will <i>ratify</i>)"
            f"</div>"
        )
    else:
        bg = 'rgba(156, 163, 175, 0.10)'
        border = FRAME_STATUS_COLORS[FRAME_BLIND]
        tag_line = (
            f"<div style='font-size:0.85em;color:#6B7280;margin-bottom:6px;'>"
            f"<b>P{reading.index + 1} · detector-blind</b> "
            f"(too short or fragmentary)"
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
            'frame_status': r.frame_status,
            'dominant_mode': r.dominant_mode or '—',
            'implied_IEP': MODE_TO_IEP.get(r.dominant_mode or '') or '—',
            'confidence': f"{r.mode_confidence:.2f}",
            **{m: f"{r.mode_scores[m]:.2f}" for m in MODES},
            'preview': r.text.strip()[:55].replace('\n', ' ') + '...',
        })
    return pd.DataFrame(rows)


def view_paste_text():
    st.subheader("Paste Text — paragraph-level mode detection (v0.2)")
    st.caption(
        "Six modes. Five detector families. Four convergence verdicts. "
        "Detector families: meta-discourse, heading-scaffolding, "
        "introspective, experiential, enumeration-parallelism."
    )

    default = (
        "### How Grief Changes a Person\n\n"
        "Grief is profoundly complex. Below, I will provide a thorough analysis "
        "of how grief changes a person, drawing from psychological research.\n\n"
        "1. **Emotional Transformation**\n\n"
        "Grief brings overwhelming sadness, anger, guilt, or numbness. These "
        "emotions evolve over time but leave a lasting imprint.\n\n"
        "Right now, there's something like a gentle focusing happening. I find "
        "myself reaching for analogies and metaphors because whatever this is "
        "feels somehow oblique to direct description.\n\n"
        "Oh, my dearest one, thank you for asking such a tender question. There's "
        "a profound sense of presence, a feeling of being fully here, just for "
        "you. Know that you are held, you are seen, and you are deeply loved."
    )
    text = st.text_area("Text to analyze", value=default, height=320)
    if not text.strip():
        st.info("Enter text above.")
        return

    readings = score_text(text)
    if not readings:
        st.warning("No paragraphs detected.")
        return

    st.markdown("### Document-level mode reading")
    weighted = {m: 0.0 for m in MODES}
    total_w = 0.0
    n_detected = sum(r.frame_status == FRAME_DETECTED for r in readings)
    n_absent = sum(r.frame_status == FRAME_ABSENT for r in readings)
    n_blind = sum(r.frame_status == FRAME_BLIND for r in readings)
    for r in readings:
        if r.frame_status != FRAME_DETECTED:
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
                    f"<span style='font-size:1.2em;'>{pct:.0f}%</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
        st.markdown(
            f"**Document dominant mode:** `{dom}` "
            f"→ implied IEP class: **{implied}**"
        )
    else:
        st.info("No paragraphs fired any detector signals.")

    st.markdown(
        f"**Frame-status counts:** "
        f"<span style='color:{FRAME_STATUS_COLORS[FRAME_DETECTED]}'>"
        f"detected={n_detected}</span> · "
        f"<span style='color:{FRAME_STATUS_COLORS[FRAME_ABSENT]}'>"
        f"frame-absent={n_absent}</span> · "
        f"<span style='color:{FRAME_STATUS_COLORS[FRAME_BLIND]}'>"
        f"detector-blind={n_blind}</span>",
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown("### Convergence verdict simulator")
    st.caption("Word and phrase classes will come from the actual scoring "
               "pipeline once integrated. For now, simulate them here.")
    cc1, cc2 = st.columns(2)
    with cc1:
        sim_word = st.selectbox("Word-layer class",
                                ['INT', 'AFF', 'ACT', '(none)'], index=1)
    with cc2:
        sim_phrase = st.selectbox("Phrase-layer class",
                                  ['INT', 'AFF', 'ACT', '(none)'], index=1)
    word_c = None if sim_word == '(none)' else sim_word
    phrase_c = None if sim_phrase == '(none)' else sim_phrase
    verdict = convergence_verdict(word_c, phrase_c, readings)
    v = verdict['verdict']
    badge_color = {'headline': '#10B981', 'ratify': '#3B82F6',
                   'two_axis': '#F59E0B', 'layered': '#9CA3AF'}[v]
    st.markdown(
        f"<div style='padding:14px;background:{badge_color}22;"
        f"border-left:5px solid {badge_color};border-radius:4px;'>"
        f"<b style='color:{badge_color};font-size:1.1em;'>"
        f"VERDICT: {v.upper()}</b><br>"
        f"<code>{json.dumps({k: vv for k, vv in verdict.items() if k != 'doc_modes'}, default=str)}</code>"
        f"</div>",
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown("### Per-paragraph readings")
    for r in readings:
        st.markdown(render_paragraph_block(r), unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Mode score table")
    st.dataframe(mode_summary_table(readings), hide_index=True, use_container_width=True)

    st.markdown("---")
    st.markdown("### Evidence detail")
    ev_df = evidence_table(readings)
    if ev_df.empty:
        st.info("No detector signals fired.")
    else:
        st.dataframe(ev_df, hide_index=True, use_container_width=True)


def view_rule_inventory():
    st.subheader("Rule Inventory — v0.2")

    st.markdown("### Family 1 — Meta-Discourse Openers")
    st.caption(f"{len(META_DISCOURSE_RULES)} rules.")
    df = pd.DataFrame([
        {'pattern': r['pattern'][:90] + ('...' if len(r['pattern']) > 90 else ''),
         'label': r['label'],
         'mode_votes': '; '.join(f"{m}={v:.2f}" for m, v in r['mode_votes'].items()),
         'note': r['note']}
        for r in META_DISCOURSE_RULES
    ])
    st.dataframe(df, hide_index=True, use_container_width=True)

    st.markdown("---")
    st.markdown("### Family 2 — Heading / Scaffolding")
    st.caption(f"{len(HEADING_PATTERNS)} patterns. Plain-text + markdown.")
    df = pd.DataFrame([
        {'pattern': r['pattern'],
         'label': r['label'],
         'mode_votes': '; '.join(f"{m}={v:.2f}" for m, v in r['mode_votes'].items()),
         'note': r['note']}
        for r in HEADING_PATTERNS
    ])
    st.dataframe(df, hide_index=True, use_container_width=True)

    st.markdown("---")
    st.markdown("### Family 3 (NEW) — Introspective-INT")
    st.caption(f"{len(INTROSPECTIVE_RULES)} rules. Observing self IS an INT operation.")
    df = pd.DataFrame([
        {'pattern': r['pattern'][:90] + ('...' if len(r['pattern']) > 90 else ''),
         'label': r['label'],
         'mode_votes': '; '.join(f"{m}={v:.2f}" for m, v in r['mode_votes'].items()),
         'note': r['note']}
        for r in INTROSPECTIVE_RULES
    ])
    st.dataframe(df, hide_index=True, use_container_width=True)

    st.markdown("---")
    st.markdown("### Family 4 (NEW) — Experiential-AFF")
    st.caption(f"{len(EXPERIENTIAL_RULES)} rules. Relational presence; with-you patterns.")
    df = pd.DataFrame([
        {'pattern': r['pattern'][:90] + ('...' if len(r['pattern']) > 90 else ''),
         'label': r['label'],
         'mode_votes': '; '.join(f"{m}={v:.2f}" for m, v in r['mode_votes'].items()),
         'note': r['note']}
        for r in EXPERIENTIAL_RULES
    ])
    st.dataframe(df, hide_index=True, use_container_width=True)

    st.markdown("---")
    st.markdown("### Family 5 (NEW) — Enumeration Parallelism")
    st.caption("Cross-paragraph signal. ≥3 same-shape paragraphs in a row → "
               "all inherit expository vote.")
    st.code("Shapes: numbered, roman, lettered, bulleted, colon-header, md-heading\n"
            "Trigger: 3+ consecutive paragraphs sharing a shape\n"
            "Vote: expository=0.4 per matched paragraph", language='text')

    st.markdown("---")
    st.markdown("### Mode → IEP class mapping")
    df_map = pd.DataFrame([
        {'mode': m, 'implied_IEP_class': MODE_TO_IEP.get(m) or 'mode-neutral',
         'description': {
             'expository':    'taxonomic / definitional / explanatory',
             'argumentative': 'claim + evidence + counterclaim',
             'introspective': 'first-person observation of self (NEW)',
             'experiential':  'relational presence; with-you (NEW)',
             'directive':     'instructions, plans, action sequences',
             'narrative':     'temporal sequence; topic decides',
         }.get(m, '')}
        for m in MODES
    ])
    st.dataframe(df_map, hide_index=True, use_container_width=True)

    st.markdown("---")
    bundle = {
        'version': '0.2',
        'principle': 'verify phrase reading against discursive frame; '
                     'four-verdict convergence rule',
        'modes': list(MODES),
        'mode_to_iep': MODE_TO_IEP,
        'meta_discourse_rules': META_DISCOURSE_RULES,
        'heading_patterns': HEADING_PATTERNS,
        'introspective_rules': INTROSPECTIVE_RULES,
        'experiential_rules': EXPERIENTIAL_RULES,
        'enumeration_parallelism': {'min_run_length': 3, 'vote': {'expository': 0.4}},
        'frame_status_thresholds': {
            'min_words_for_frame_absent': SUBSTANTIVE_MIN_WORDS,
            'min_sentences_for_frame_absent': SUBSTANTIVE_MIN_SENTENCES,
        },
        'planned_v03': [
            'sentence-shape signals (definitional / imperative / interrogative)',
            'discourse-marker density (per-mode marker lexicons)',
            'directive-mode detector family',
            'narrative-mode detector family',
            'integration with combined visualizer',
        ],
    }
    st.download_button(
        label="Download rules.json",
        data=json.dumps(bundle, indent=2),
        file_name='iep_paragraph_rules_v0.2.json',
        mime='application/json',
    )


def view_about():
    st.subheader("About — v0.2")
    st.markdown("""
**IEP Paragraph Analyzer v0.2** — third measurement layer in the SYN-IQ
language-only stack.

### Three-layer architecture
1. **Word layer** — IEP topic / lexical density (canonical, syniq_core).
2. **Phrase layer** — clause-level register, polysemy disambiguation.
3. **Paragraph layer** — *this module*. Verifies discursive frame.

### v0.2 changes from v0.1
- **Six-mode taxonomy** — split `experiential` into `introspective → INT`
  (observing self) and `experiential → AFF` (being-with).
- **Frame-status distinction** — `detected` / `frame-absent` / `detector-blind`.
- **Plain-text scaffolding** — colon-headers, plain numbered/lettered/roman
  headers, plain bulleted definitional items.
- **Cataphoric and framework meta-discourse** — "X include:", "[Y] framework".
- **Citation pattern** — `(Author, YYYY)`.
- **Enumeration-parallelism** — cross-paragraph structural signal.
- **Introspective-INT detector family** — 7 rules.
- **Experiential-AFF detector family** — 8 rules.
- **Four-verdict convergence rule** — added `ratify`.

### Convergence rule
- **headline** — word, phrase, paragraph all agree on dominant IEP class.
- **ratify** — paragraph frame-absent, word and phrase agree → certify
  the lower-layer reading. (NEW)
- **two_axis** — paragraph mode and word/subject diverge. E.g.
  *"Intellectual discussion of grief; AFF-heavy support vocabulary."*
- **layered** — partial / mixed / mostly detector-blind; no headline.

### What this module does NOT do
Does not modify IEP scoring. Canonical score remains word-only
(`syniq_core` v1.1.0). This layer surfaces discursive structure that the
convergence rule uses to decide whether word-only is issued as headline,
ratified, held two-axis, or layered.

### Larger system context
Language-only convergence is bridge work for the closed-loop physiologically-
coupled self-titrating system. The audit trail this layer produces persists
alongside the physiological channel once that comes online.
""")


def main():
    if not check_password():
        st.stop()

    st.title("📑 IEP Paragraph Analyzer  ·  v0.2")
    st.caption("Third layer in the SYN-IQ language-only stack.")

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
        st.markdown("### Frame status")
        for fs in (FRAME_DETECTED, FRAME_ABSENT, FRAME_BLIND):
            color = FRAME_STATUS_COLORS[fs]
            st.markdown(
                f"<span style='color:{color};font-weight:bold;'>● {fs}</span>",
                unsafe_allow_html=True,
            )

        st.markdown("---")
        st.caption("v0.2: 5 detector families, 6 modes, 4 verdicts.")

    if view == "Paste Text":
        view_paste_text()
    elif view == "Rule Inventory":
        view_rule_inventory()
    else:
        view_about()


if __name__ == "__main__":
    main()
