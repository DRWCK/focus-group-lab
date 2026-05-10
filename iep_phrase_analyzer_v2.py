"""
iep_phrase_analyzer_v2.py — IEP Phrase-Level Analysis (v2.0.0)
================================================================

SUBSTRATE UPGRADE — May 2026
-----------------------------
v1.x used a token-window walker (`detect_verb_object_phrases`) that
slid a 5-token window across text and emitted any verb/object pair it
found. This produced phrase-shaped fragments that did not respect
grammatical or clause boundaries:

    Image evidence from leave-job advisory passage (May 10, 2026):
      ❌ "people thrive in stability and find"     — crosses clause break
      ❌ "people who've made"                       — chops VP mid-RC
      ❌ "work is figuring out which kind"          — chops at WH-clause
      ❌ "people who stayed and ask"                — coordinated VP fragment

v2 replaces the window walker with a real grammatical detector built
on spaCy's dependency parser:

    ✅ noun_chunks           → real noun phrases
    ✅ verb + dobj subtree   → real verb-object phrases
    ✅ prep + pobj subtree   → real prepositional phrases
    ✅ sentence iteration    → never crosses sentence boundaries
    ✅ ccomp/advcl/relcl     → respect embedded clause boundaries

The three regex rule families (LIGHT_VERB_RULES, ASPECT_MODAL_RULES,
polysemous-verb canonical cases) are PRESERVED unchanged. They handle
multi-word idioms and curated patterns that compositional detection
should not override. A future v2.1 can migrate them to spaCy's Matcher.

================================================================
SINGLE-SOURCE-OF-TRUTH PRINCIPLE
================================================================
All IEP dictionaries imported from syniq_core. NEVER embed copies.

    from syniq_core import INT_WORDS, AFF_WORDS, ACT_WORDS

================================================================

GRACEFUL FALLBACK
-----------------
If spaCy is not installed OR the en_core_web_sm model is missing,
v2 falls back to v1.1's window-walking detector with a clear UI
warning. This keeps the tool runnable on any machine; the user
unlocks the v2 substrate by running:

    pip install spacy
    python -m spacy download en_core_web_sm

OUTPUT COMPATIBILITY
--------------------
v2's detection records carry the same keys v1.1 emitted, so
iep_combined_visualizer can consume v2 output unchanged:
  phrase, span, layer, iep_tags, cam_tags, function_tags,
  specificity, rule_name, note

New v2-only fields (additive, won't break v1 consumers):
  syntactic_role: 'NP' | 'VP-dobj' | 'PP' | 'compositional' | None
  clause_id:     int  — sentence-relative clause identifier
  parser:        'spacy-3.x' | 'fallback-v1.1'

Run:  streamlit run iep_phrase_analyzer_v2.py
Default password: tennessee
"""

import os
import re
import json
from typing import Dict, List, Tuple, Optional

import pandas as pd
import streamlit as st

# =============================================================================
# DICTIONARIES — IMPORTED FROM SYNIQ_CORE (single source of truth)
# =============================================================================
from syniq_core import INT_WORDS, AFF_WORDS, ACT_WORDS


def word_class(w: str) -> Tuple[Optional[str], List[str]]:
    """Return (single_class | 'COLLISION' | None, all_classes)."""
    wl = w.lower()
    classes = []
    if wl in INT_WORDS: classes.append('INT')
    if wl in AFF_WORDS: classes.append('AFF')
    if wl in ACT_WORDS: classes.append('ACT')
    if not classes:
        return (None, [])
    if len(classes) == 1:
        return (classes[0], classes)
    return ('COLLISION', classes)


# =============================================================================
# spaCy — load once, gracefully degrade
# =============================================================================
_SPACY_NLP = None
_SPACY_STATUS = 'unknown'  # 'ok' | 'no_spacy' | 'no_model' | 'error'
_SPACY_VERSION = None


def _load_spacy():
    """Idempotent loader. Tries en_core_web_sm; falls back gracefully."""
    global _SPACY_NLP, _SPACY_STATUS, _SPACY_VERSION
    if _SPACY_STATUS != 'unknown':
        return _SPACY_NLP
    try:
        import spacy
        _SPACY_VERSION = spacy.__version__
        try:
            _SPACY_NLP = spacy.load('en_core_web_sm')
            _SPACY_STATUS = 'ok'
        except OSError:
            _SPACY_STATUS = 'no_model'
            _SPACY_NLP = None
    except ImportError:
        _SPACY_STATUS = 'no_spacy'
        _SPACY_NLP = None
    except Exception:
        _SPACY_STATUS = 'error'
        _SPACY_NLP = None
    return _SPACY_NLP


# =============================================================================
# RULE LIBRARY — preserved from v1.1 (multi-tag schema)
# =============================================================================
OBJECT_STOP_WORDS = {
    'a','an','the','some','any','this','that','these','those','my','your','his','her',
    'its','our','their','all','both','each','few','more','most','no','not','only','own',
    'same','than','too','very','just','as','if','while','although','because','since',
    'unless','until','though','whether','of','to','in','on','at','by','with','from',
    'up','down','out','off','over','under','again','further','then','once','here','there',
    'when','where','why','how','what','which','who','whom','really','quite','rather',
    'and','or','but','so','yet','for','nor',
}


def _rule(pattern, name, iep=None, cam=None, function=None,
          specificity='high', note=''):
    return {
        'pattern': pattern,
        'name': name,
        'iep_tags': iep or [],
        'cam_tags': cam or [],
        'function_tags': function or [],
        'specificity': specificity,
        'note': note,
    }


# Light-verb / idiomatic frames — UNCHANGED from v1.1
LIGHT_VERB_RULES = [
    _rule(r"\btake[s]?\s+(?:a\s+)?look\b", "take a look",
          iep=['INT.analytical'], function=['cognitive-idiom'],
          note="look-as-analysis, not physical perception"),
    _rule(r"\bmake[s]?\s+sense\b", "make sense",
          iep=['INT.epistemic'], function=['cognitive-idiom'],
          note="sense-as-coherence, light verb"),
    _rule(r"\bmake[s]?\s+(?:a|the)\s+case\b", "make the case",
          iep=['INT.critical'], function=['argument-construction']),
    _rule(r"\bmake[s]?\s+(?:an?\s+)?argument\b", "make an argument",
          iep=['INT.critical'], function=['argument-construction']),
    _rule(r"\bmake[s]?\s+(?:an?\s+)?point\b", "make a point",
          iep=['INT.critical'], function=['argument-construction']),
    _rule(r"\bdraw[s]?\s+(?:a|the)?\s*(?:conclusion|distinction|inference)\b",
          "draw a conclusion",
          iep=['INT.analytical'], cam=['abstract'], function=['cognitive-idiom']),
    _rule(r"\btake[s]?\s+(?:into\s+)?account\b", "take into account",
          iep=['INT.analytical'], function=['cognitive-idiom']),
    _rule(r"\bgive[s]?\s+(?:it\s+)?thought\b", "give thought",
          iep=['INT.epistemic'], function=['cognitive-idiom']),
    _rule(r"\bcatch\s+(?:my|your|his|her|our|their|its)\s+\w+", "catch my X",
          iep=['AFF.self_state'], cam=['metaphorical'],
          function=['metaphor', 'self-state-marker'],
          note="metaphorical self-perception, not physical catching"),
    _rule(r"\bhave\s+(?:a|the)\s+conversation\b", "have a conversation",
          iep=['AFF.relational'], function=['relational-cue']),
    _rule(r"\bhold[s]?\s+space\b", "hold space",
          iep=['AFF.relational'], cam=['metaphorical'],
          function=['relational-cue', 'metaphor']),
    _rule(r"\bgive[s]?\s+(?:my|your|their|her|his)?\s*attention\b",
          "give attention", iep=['AFF.relational'], function=['relational-cue']),
    _rule(r"\bdraw[s]?\s+(?:my|your|their|her|his|our|its)?\s*attention\s+\w+",
          "drawing attention",
          iep=['AFF.relational'], cam=['metaphorical'],
          function=['relational-cue', 'metaphor']),
    _rule(r"\bfind[s]?\s+(?:my|your|him|her|our|them|it)self\b", "find myself",
          iep=['AFF.self_state'],
          function=['self-state-marker', 'reflexive-cognitive'],
          note="reflexive-cognitive frame, not action verb"),
    _rule(r"\breach(?:es|ed|ing)?\s+for\b", "reach for",
          iep=['AFF.phenomenological'], cam=['metaphorical'],
          function=['metaphor'],
          note="metaphorical-grasping when object is abstract"),
    _rule(r"\bopen(?:s|ed|ing)?\s+up\b", "open up",
          iep=['AFF.relational'], function=['relational-cue']),
    _rule(r"\bcatch\s+up\b", "catch up",
          iep=['AFF.relational'], function=['relational-cue']),
    _rule(r"\blook(?:s|ed|ing)?\s+through\b", "looking through",
          cam=['metaphorical'], function=['metaphor'],
          note="metaphorical perception"),
    _rule(r"\bstand(?:s|ing)?\s+at\s+the\s+edge\b", "stand at the edge",
          cam=['metaphorical'], function=['metaphor'],
          note="metaphorical positioning"),
    _rule(r"\bbloom\s+into\b", "bloom into",
          cam=['metaphorical'], function=['metaphor']),
    _rule(r"\bobserve\s+the\s+observer\b", "observe the observer",
          iep=['INT.phenomenological'], cam=['metaphorical'],
          function=['recursive-reflection-marker', 'metaphor'],
          specificity='high',
          note="recursive self-reference, classic introspection trope"),
    # Polysemous-verb canonical cases
    _rule(r"\bcreate[sd]?\s+(?:a|an|the)\s+contradiction\b",
          "creates a contradiction",
          iep=['INT.critical'], cam=['abstract'],
          function=['polysemous-verb-disambiguation'],
          specificity='high',
          note="create+abstract: not ACT.building"),
    _rule(r"\bcreate[sd]?\s+(?:a|an|the)\s+paradox\b", "creates a paradox",
          iep=['INT.conceptual'], cam=['abstract'],
          function=['polysemous-verb-disambiguation']),
    _rule(r"\bcreate[sd]?\s+(?:a|an|the)\s+meaning\b", "creates meaning",
          iep=['INT.lexical'], function=['polysemous-verb-disambiguation']),
    _rule(r"\bcreat(?:e|es|ed|ing)\s+(?:a|an|the|that)?\s*(?:very\s+)?experience\b",
          "creates experience",
          iep=['AFF.self_state'],
          function=['polysemous-verb-disambiguation', 'self-state-marker']),
    _rule(r"\bbuild[s]?\s+(?:a|an|the)\s+(?:case|argument)\b", "build a case",
          iep=['INT.critical'], function=['polysemous-verb-disambiguation']),
    _rule(r"\btake[s]?\s+(?:a|an|the)\s+position\b", "take a position",
          iep=['INT.critical'], function=['polysemous-verb-disambiguation']),
    _rule(r"\btake[s]?\s+the\s+time\b", "take the time",
          iep=['AFF.warmth'], function=['care-aspect']),
]

# Aspect / modal / sensory / multi-word hedges — UNCHANGED from v1.1
ASPECT_MODAL_RULES = [
    _rule(r"\bmight\s+be\b", "might be",
          iep=['INT.hedging'], function=['epistemic-hedge', 'uncertainty-marker']),
    _rule(r"\bmay\s+be\b", "may be",
          iep=['INT.hedging'], function=['epistemic-hedge', 'uncertainty-marker']),
    _rule(r"\bcould\s+be\b", "could be",
          iep=['INT.hedging'], function=['epistemic-hedge', 'uncertainty-marker']),
    _rule(r"\bseem(?:s|ed|ing)?\s+to\b", "seem(s) to",
          iep=['INT.hedging'], function=['epistemic-hedge']),
    _rule(r"\bappear(?:s|ed|ing)?\s+to\b", "appear(s) to",
          iep=['INT.hedging'], function=['epistemic-hedge']),
    _rule(r"\bfeel(?:s|t)?\s+like\b", "feels like",
          iep=['AFF.phenomenological'], function=['sensory-frame']),
    _rule(r"\bfeel(?:s|t)?\s+both\b", "feels both",
          iep=['AFF.phenomenological'], function=['sensory-frame']),
    _rule(r"\btry(?:ing|ied)?\s+to\b", "trying to",
          iep=['AFF.phenomenological'], function=['attempt-aspect']),
    _rule(r"\bnot\s+entirely\b", "not entirely",
          iep=['INT.hedging'], function=['epistemic-hedge', 'uncertainty-marker']),
    _rule(r"\b(?:I|you|we|he|she|they|it|that|this)\s+(?:doesn't|don't|"
          r"didn't|won't|wouldn't)\s+quite\b",
          "doesn't quite",
          iep=['INT.hedging'], function=['epistemic-hedge', 'uncertainty-marker']),
    _rule(r"\bsomewhere\s+(?:I|you|we|he|she|they)\s+can't\b",
          "somewhere I can't X",
          iep=['INT.hedging'], cam=['metaphorical'],
          function=['epistemic-hedge', 'metaphor']),
    _rule(r"\bI\s+(?:can't|don't|doesn't)\s+quite\s+"
          r"(?:locate|grasp|catch|describe|explain|capture|find)\b",
          "I can't quite [cognitive verb]",
          iep=['INT.hedging'],
          function=['epistemic-hedge', 'uncertainty-marker'],
          specificity='high',
          note="explicit cognitive uncertainty marker"),
    _rule(r"\bwhat(?:ever)?\s+this\s+is\b", "whatever this is",
          iep=['INT.hedging'],
          function=['epistemic-hedge', 'uncertainty-marker'],
          note="metalinguistic uncertainty about reference"),
]


# =============================================================================
# v2 PRIMARY DETECTOR — spaCy grammatical phrases
# =============================================================================
# Replaces v1.1's detect_verb_object_phrases (window-walking).
# Three sub-detectors, each constituent-shaped, clause-respecting.

# Dependency labels that mark a clause break we should not cross
_CLAUSE_BREAK_DEPS = {'ccomp', 'xcomp', 'advcl', 'relcl', 'acl', 'parataxis'}
# Coordinating conjunctions that mark clause breaks at top level
_COORD_CONJ_TAGS = {'CC'}


def _token_iep_class(token) -> Optional[str]:
    """Return 'INT'/'AFF'/'ACT'/'COLLISION'/None for a spaCy token."""
    cls, _ = word_class(token.text)
    return cls


def _subtree_span(token, doc) -> Tuple[int, int]:
    """Character span of a token's subtree, clamped to its sentence."""
    sent = token.sent
    subtree = list(token.subtree)
    start = min(t.idx for t in subtree)
    end = max(t.idx + len(t.text) for t in subtree)
    # Clamp to sentence boundaries — a subtree should not legally span out,
    # but we enforce it as a safety rail.
    return (max(start, sent.start_char), min(end, sent.end_char))


def _subtree_respects_clause(token) -> bool:
    """True if token's subtree does NOT contain a clause-break dependency
    that would chop a constituent. Used to filter VP+dobj phrases that
    swallow embedded clauses."""
    for descendant in token.subtree:
        if descendant is token:
            continue
        if descendant.dep_ in _CLAUSE_BREAK_DEPS:
            # Allow short relative clauses (≤4 tokens) to remain attached
            sub_len = len(list(descendant.subtree))
            if sub_len > 4:
                return False
    return True


def detect_grammatical_phrases(text: str) -> List[Dict]:
    """Layer 1 (v2): real grammatical phrases via spaCy dep parser.

    Replaces v1.1 detect_verb_object_phrases. Emits three kinds:
      - Noun phrases (doc.noun_chunks) — when they contain ≥1 IEP word
      - Verb-object phrases (verb + dobj subtree) — clause-respecting
      - Prepositional phrases (prep + pobj subtree) — when IEP-bearing

    Returns records with the v1.1 schema PLUS:
      syntactic_role, clause_id, parser
    """
    nlp = _load_spacy()
    if nlp is None or _SPACY_STATUS != 'ok':
        return _detect_grammatical_phrases_fallback(text)

    doc = nlp(text)
    out: List[Dict] = []
    seen_spans = set()

    for sent_idx, sent in enumerate(doc.sents):
        # ── 1. Noun phrases via doc.noun_chunks (clause-clean by definition)
        for chunk in sent.noun_chunks:
            iep_classes = [c for c in (
                _token_iep_class(t) for t in chunk
            ) if c and c != 'COLLISION']
            if not iep_classes:
                continue
            span_start = chunk.start_char
            span_end = chunk.end_char
            key = ('NP', span_start, span_end)
            if key in seen_spans:
                continue
            seen_spans.add(key)
            # Dominant class within the NP
            from collections import Counter
            cls_counts = Counter(iep_classes)
            dominant = cls_counts.most_common(1)[0][0]
            out.append({
                'phrase': text[span_start:span_end],
                'span': (span_start, span_end),
                'layer': 'noun-phrase',
                'iep_tags': [dominant],
                'cam_tags': [],
                'function_tags': ['grammatical-noun-phrase'],
                'specificity': 'medium',
                'rule_name': f"NP: {dominant}",
                'note': f"noun chunk; {len(iep_classes)} IEP tokens; dominant {dominant}",
                'syntactic_role': 'NP',
                'clause_id': sent_idx,
                'parser': 'spacy',
            })

        # ── 2. Verb-object phrases — verb head + its dobj subtree
        for token in sent:
            if token.pos_ not in ('VERB', 'AUX'):
                continue
            v_cls = _token_iep_class(token)
            # Collect direct objects, attributes, complements
            objs = [c for c in token.children
                    if c.dep_ in ('dobj', 'attr', 'oprd')]
            for obj in objs:
                if obj.text.lower() in OBJECT_STOP_WORDS:
                    continue
                o_cls = _token_iep_class(obj)
                if o_cls is None or o_cls == 'COLLISION':
                    continue
                # Span: verb start → object subtree end (clause-clamped)
                obj_subtree_end = max(t.idx + len(t.text) for t in obj.subtree)
                obj_subtree_end = min(obj_subtree_end, sent.end_char)
                span_start = token.idx
                span_end = obj_subtree_end
                # Clause respect: skip if obj subtree contains a clause break
                if not _subtree_respects_clause(obj):
                    # Truncate: take just verb + obj head (not full subtree)
                    span_end = obj.idx + len(obj.text)
                key = ('VP-dobj', span_start, span_end)
                if key in seen_spans:
                    continue
                seen_spans.add(key)
                # Reclassify if object class differs from verb class
                if v_cls and v_cls != o_cls:
                    proposed = o_cls
                    note = f"verb '{token.text}' ({v_cls}) + obj '{obj.text}' ({o_cls}) → reclassify to {o_cls}"
                else:
                    proposed = o_cls
                    note = f"verb '{token.text}' + obj '{obj.text}' → {o_cls}"
                out.append({
                    'phrase': text[span_start:span_end],
                    'span': (span_start, span_end),
                    'layer': 'verb-object',
                    'iep_tags': [proposed],
                    'cam_tags': [],
                    'function_tags': ['polysemous-verb-disambiguation',
                                      'grammatical-verb-object'],
                    'specificity': 'medium',
                    'rule_name': f"VO: {v_cls or '?'}+{o_cls}",
                    'note': note,
                    'syntactic_role': 'VP-dobj',
                    'clause_id': sent_idx,
                    'parser': 'spacy',
                })

        # ── 3. Prepositional phrases — prep head + pobj subtree, IEP-bearing
        for token in sent:
            if token.dep_ != 'prep':
                continue
            pobjs = [c for c in token.children if c.dep_ == 'pobj']
            for pobj in pobjs:
                if pobj.text.lower() in OBJECT_STOP_WORDS:
                    continue
                pobj_cls = _token_iep_class(pobj)
                if pobj_cls is None or pobj_cls == 'COLLISION':
                    continue
                pobj_subtree_end = max(t.idx + len(t.text) for t in pobj.subtree)
                pobj_subtree_end = min(pobj_subtree_end, sent.end_char)
                span_start = token.idx
                span_end = pobj_subtree_end
                key = ('PP', span_start, span_end)
                if key in seen_spans:
                    continue
                # Skip if PP is inside an already-recorded NP (avoid double-count)
                inside_np = any(
                    s2 <= span_start and span_end <= e2
                    for kind, s2, e2 in seen_spans if kind == 'NP'
                )
                if inside_np:
                    continue
                seen_spans.add(key)
                out.append({
                    'phrase': text[span_start:span_end],
                    'span': (span_start, span_end),
                    'layer': 'prep-phrase',
                    'iep_tags': [pobj_cls],
                    'cam_tags': [],
                    'function_tags': ['grammatical-prep-phrase'],
                    'specificity': 'medium',
                    'rule_name': f"PP: {pobj_cls}",
                    'note': f"PP '{token.text} ... {pobj.text}' → {pobj_cls}",
                    'syntactic_role': 'PP',
                    'clause_id': sent_idx,
                    'parser': 'spacy',
                })

    return out


def _detect_grammatical_phrases_fallback(text: str) -> List[Dict]:
    """v1.1 window-walker, used when spaCy / model is unavailable.

    Same logic as v1.1's detect_verb_object_phrases but tagged with
    parser='fallback-v1.1' so analysts can see degraded mode in evidence
    table.
    """
    _TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z'-]*")
    tokens = list(_TOKEN_RE.finditer(text))
    out = []
    seen_spans = set()
    window = 5

    for i, m in enumerate(tokens):
        verb = m.group(0)
        v_cls = _token_iep_class_str(verb)
        if v_cls is None or v_cls == 'COLLISION':
            continue
        for j in range(i + 1, min(i + 1 + window, len(tokens))):
            obj = tokens[j].group(0)
            obj_l = obj.lower()
            if obj_l in OBJECT_STOP_WORDS:
                continue
            if obj_l.endswith('ing') and obj_l not in {
                'meaning', 'feeling', 'thinking', 'being',
                'nothing', 'something', 'everything', 'longing', 'yearning',
            }:
                continue
            if obj_l.endswith('ed') and len(obj_l) > 4 and obj_l not in {
                'embodied', 'grounded', 'centered', 'shattered',
            }:
                continue
            o_cls = _token_iep_class_str(obj)
            if o_cls is None or o_cls == 'COLLISION':
                continue
            if o_cls == v_cls:
                break
            span_start = m.start()
            span_end = tokens[j].end()
            key = (span_start, span_end)
            if key in seen_spans:
                break
            seen_spans.add(key)
            out.append({
                'phrase': text[span_start:span_end],
                'span': (span_start, span_end),
                'layer': 'verb-object',
                'iep_tags': [o_cls],
                'cam_tags': [],
                'function_tags': ['polysemous-verb-disambiguation'],
                'specificity': 'low',
                'rule_name': f"VO: {v_cls}+{o_cls}",
                'note': f"verb {v_cls} + object {o_cls} → reclassify verb as {o_cls} (fallback)",
                'syntactic_role': 'compositional',
                'clause_id': -1,
                'parser': 'fallback-v1.1',
            })
            break
    return out


def _token_iep_class_str(s: str) -> Optional[str]:
    cls, _ = word_class(s)
    return cls


# =============================================================================
# Curated rule layers — UNCHANGED from v1.1
# =============================================================================
def detect_pattern_layer(text: str, rules: List[Dict], layer_name: str) -> List[Dict]:
    out = []
    for r in rules:
        for m in re.finditer(r['pattern'], text, re.IGNORECASE):
            span = (m.start(), m.end())
            out.append({
                'phrase': text[span[0]:span[1]],
                'span': span,
                'layer': layer_name,
                'iep_tags': r['iep_tags'],
                'cam_tags': r['cam_tags'],
                'function_tags': r['function_tags'],
                'specificity': r['specificity'],
                'rule_name': r['name'],
                'note': r['note'],
                'syntactic_role': None,
                'clause_id': -1,
                'parser': 'regex',
            })
    return out


def detect_all_phrases(text: str, layers: List[str]) -> List[Dict]:
    out = []
    if 'grammatical' in layers:
        out.extend(detect_grammatical_phrases(text))
    if 'light-verb' in layers:
        out.extend(detect_pattern_layer(text, LIGHT_VERB_RULES, 'light-verb'))
    if 'aspect-modal' in layers:
        out.extend(detect_pattern_layer(text, ASPECT_MODAL_RULES, 'aspect-modal'))
    out.sort(key=lambda x: x['span'][0])
    return out


# =============================================================================
# STREAMLIT UI
# =============================================================================
LAYER_COLORS = {
    'noun-phrase': '#3B82F6',     # blue
    'verb-object': '#8B5CF6',     # violet
    'prep-phrase': '#0EA5E9',     # sky
    'light-verb':  '#10B981',     # green
    'aspect-modal':'#F59E0B',     # amber
}
LAYER_BG = {
    'noun-phrase':  'rgba(59, 130, 246, 0.10)',
    'verb-object':  'rgba(139, 92, 246, 0.10)',
    'prep-phrase':  'rgba(14, 165, 233, 0.10)',
    'light-verb':   'rgba(16, 185, 129, 0.12)',
    'aspect-modal': 'rgba(245, 158, 11, 0.12)',
}

st.set_page_config(page_title="IEP Phrase Analyzer v2.0",
                   page_icon="🔗", layout="wide")

DEFAULT_PASSWORD = "tennessee"


def _expected_password():
    expected = os.environ.get("SYNIQ_PASSWORD", DEFAULT_PASSWORD)
    try:
        expected = st.secrets.get("password", expected)
    except Exception:
        pass
    return expected


def _password_entered():
    if st.session_state.get("password", "") == _expected_password():
        st.session_state["password_correct"] = True
        del st.session_state["password"]
    else:
        st.session_state["password_correct"] = False


def check_password() -> bool:
    if st.session_state.get("password_correct", False):
        return True
    st.text_input("Password", type="password",
                  on_change=_password_entered, key="password")
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("Password incorrect")
    return False


def _esc(s: str) -> str:
    return (s.replace('&', '&amp;').replace('<', '&lt;')
            .replace('>', '&gt;').replace('"', '&quot;'))


def render_text_with_phrases(text: str, phrases: List[Dict],
                             show_layers: List[str]) -> str:
    """Render text with phrase underlines. Sorted-event approach."""
    starts: Dict[int, List[str]] = {}
    ends: Dict[int, List[str]] = {}
    for p in phrases:
        if p['layer'] not in show_layers:
            continue
        s, e = p['span']
        color = LAYER_COLORS.get(p['layer'], '#888888')
        bg = LAYER_BG.get(p['layer'], 'transparent')
        iep = '; '.join(p['iep_tags']) or '—'
        cam = '; '.join(p['cam_tags']) or '—'
        fn = '; '.join(p['function_tags']) or '—'
        tip = (f"{p['layer']} — {p['rule_name']}\n"
               f"IEP: {iep}\nCAM: {cam}\nfunction: {fn}\n"
               f"specificity: {p['specificity']}\n"
               f"parser: {p.get('parser', '?')}\n"
               f"note: {p['note']}")
        starts.setdefault(s, []).append(
            f'<span style="background:{bg}; border-bottom:2px solid {color}; '
            f'padding:1px 0;" title="{_esc(tip)}">'
        )
        ends.setdefault(e, []).append('</span>')

    parts = []
    for i in range(len(text) + 1):
        if i in ends:
            for tag in ends[i]:
                parts.append(tag)
        if i in starts:
            for tag in starts[i]:
                parts.append(tag)
        if i < len(text):
            parts.append(_esc(text[i]))
    return ''.join(parts).replace('\n', '<br>')


def evidence_table(phrases: List[Dict]) -> pd.DataFrame:
    rows = []
    for p in phrases:
        rows.append({
            'phrase': p['phrase'],
            'span': f"{p['span'][0]}-{p['span'][1]}",
            'layer': p['layer'],
            'role': p.get('syntactic_role') or '—',
            'rule': p['rule_name'],
            'iep_tags': '; '.join(p['iep_tags']) or '—',
            'cam_tags': '; '.join(p['cam_tags']) or '—',
            'function_tags': '; '.join(p['function_tags']) or '—',
            'specificity': p['specificity'],
            'parser': p.get('parser', '?'),
            'note': p['note'],
        })
    return pd.DataFrame(rows)


# =============================================================================
# Views
# =============================================================================
def view_paste_text(active_layers):
    st.subheader("Paste text — show phrase detections")
    default = (
        "Leaving a stable job for your passion is one of those decisions that "
        "looks different in the spreadsheet than it does at 2 AM. The financial "
        "math matters — runway, savings, healthcare, the cost of being wrong. "
        "But there's another calculation underneath it that the spreadsheet "
        "can't see. How much of yourself are you spending to stay where you "
        "are? Some people thrive in stability and find their passion in "
        "evenings and weekends. Others wake up at fifty wishing they'd taken "
        "the leap at thirty. Neither is wrong, and the honest work is figuring "
        "out which kind of person you are before circumstances decide for you. "
        "Talk to people who've made the jump and ask what they actually miss. "
        "Talk to people who stayed and ask what they think about. The pattern "
        "that emerges from those conversations will tell you more than any "
        "pros-and-cons list."
    )
    text = st.text_area("Text to analyze", value=default, height=250)
    if not text.strip():
        st.info("Enter text above.")
        return

    phrases = detect_all_phrases(text, active_layers)

    # Layer counts
    counts = {}
    for p in phrases:
        counts[p['layer']] = counts.get(p['layer'], 0) + 1

    cols = st.columns(len(LAYER_COLORS))
    for col, layer in zip(cols, LAYER_COLORS.keys()):
        with col:
            n = counts.get(layer, 0)
            color = LAYER_COLORS[layer]
            active = '✓' if layer in active_layers else '○'
            st.markdown(
                f"<div style='padding:10px; background:#f8f9fa; "
                f"border-left:4px solid {color}; border-radius:4px;'>"
                f"<b>{active} {layer}</b><br>"
                f"<span style='font-size:1.5em;'>{n}</span> phrases</div>",
                unsafe_allow_html=True,
            )

    st.markdown("---")
    st.markdown("##### Highlighted text — hover any phrase for full tag detail")
    html = render_text_with_phrases(text, phrases, active_layers)
    st.markdown(
        f"<div style='line-height:2.0; font-size:1.05em; font-family:Georgia,serif; "
        f"padding:12px; background:#fafafa; border-radius:6px;'>{html}</div>",
        unsafe_allow_html=True,
    )

    if phrases:
        st.markdown("---")
        st.markdown("##### Evidence table")
        df = evidence_table(phrases)
        st.dataframe(df, hide_index=True, use_container_width=True)
        st.download_button(
            "⬇ phrases.csv",
            data=df.to_csv(index=False).encode('utf-8'),
            file_name='phrases_v2.csv', mime='text/csv',
        )
    else:
        st.info("No phrases matched the active rule layers.")


def view_substrate_status():
    st.subheader("Substrate Status")
    nlp = _load_spacy()
    status_box = {
        'ok': ('✅', '#10B981',
               f"spaCy {_SPACY_VERSION} + en_core_web_sm loaded. "
               "Full grammatical detection active."),
        'no_model': ('⚠️', '#F59E0B',
               f"spaCy {_SPACY_VERSION} installed but en_core_web_sm not "
               "found. Falling back to v1.1 window-walker. Run: "
               "`python -m spacy download en_core_web_sm` to upgrade."),
        'no_spacy': ('⚠️', '#F59E0B',
               "spaCy not installed. Falling back to v1.1 window-walker. "
               "Run: `pip install spacy && python -m spacy download en_core_web_sm`"),
        'error': ('❌', '#EF4444',
               "spaCy load error. Falling back to v1.1 window-walker."),
        'unknown': ('?', '#6B7280', "Status not yet checked."),
    }
    icon, color, msg = status_box.get(_SPACY_STATUS, status_box['unknown'])
    st.markdown(
        f"<div style='padding:14px; background:#f8f9fa; "
        f"border-left:4px solid {color}; border-radius:6px; font-size:1.05em;'>"
        f"<b>{icon} Substrate: {_SPACY_STATUS}</b><br><br>{msg}</div>",
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown("##### What v2 detects when active")
    st.markdown("""
- **Noun phrases** via `doc.noun_chunks` — real grammatical NPs containing IEP words
- **Verb-object phrases** via `dobj`/`attr` dependency arcs — verb plus its real object subtree
- **Prepositional phrases** via `prep`+`pobj` — when the object of a preposition carries IEP signal
- **Clause boundaries respected** — phrases never cross sentence breaks; embedded clauses
  longer than 4 tokens are not swallowed into VP-dobj phrases
- **No double-counting** — PPs that fall inside a recorded NP are dropped
""")


def view_about():
    st.subheader("About v2.0.0")
    nlp = _load_spacy()
    st.markdown(f"""
**IEP Phrase Analyzer v2.0.0** — substrate upgrade.

**What changed from v1.1**
- The token-window walker is gone. Phrase detection now uses spaCy's
  dependency parser to find real grammatical constituents.
- Three new layers: noun-phrase, verb-object (clause-respecting),
  prep-phrase. The old `verb-object` layer kept the same name but is now
  grammatical, not compositional.
- Clause-boundary respect: phrases never cross sentence breaks; embedded
  relative/complement clauses longer than 4 tokens are not swallowed.
- Dictionaries imported from `syniq_core` (SSOT).

**What's preserved from v1.1**
- All three regex rule families: light-verb, aspect-modal, polysemous-verb
  canonical cases. Future v2.1 may migrate these to spaCy's Matcher.
- Multi-tag schema: every phrase carries IEP / CAM / function tags.
- Specificity grading: high / medium / low.
- Tennessee password gate.

**Status: {_SPACY_STATUS}** ({_SPACY_VERSION or 'spacy not installed'})

**Diagnostic, not canonical.** This tool reveals phrase-level structure;
canonical IEP score remains word-only via syniq_core.
""")


def main():
    if not check_password():
        st.stop()

    st.title("🔗 IEP Phrase Analyzer  ·  v2.0.0")
    st.caption("Grammatical phrase detection via spaCy dependency parser. "
               "SSOT: syniq_core. Show why, not just what.")

    # Pre-load spacy so the status banner is informed
    _load_spacy()

    with st.sidebar:
        st.markdown("### Rule layers")
        active = []
        if st.checkbox("Grammatical (NP / VP / PP)", value=True):
            active.append('grammatical')
        if st.checkbox("Light-verb idioms", value=True):
            active.append('light-verb')
        if st.checkbox("Aspect / modal / hedges", value=True):
            active.append('aspect-modal')
        st.markdown("---")
        st.caption(f"Substrate: **{_SPACY_STATUS}**")

    tab1, tab2, tab3 = st.tabs(["Paste text", "Substrate status", "About"])
    with tab1:
        view_paste_text(active)
    with tab2:
        view_substrate_status()
    with tab3:
        view_about()


if __name__ == "__main__":
    main()
