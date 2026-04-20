"""
IEP Multi-Track Scoring — V3 / V4 / V5

Extracted from syniq_phrase_library_v3.py for inline harvest-time scoring.
Three parallel IEP scoring tracks:

    V3 — Word-level lexical (matches V50's analyze_text method)
    V4 — Word-level POS-aware (resolves noun/verb ambiguity via B_WORDS/C_WORDS)
    V5 — Phrase-level (extracts VP/NP chunks, scores as semantic units)

Call site:
    from iep_multiscore import score_all_tracks
    result = score_all_tracks(response_text)
    # → {
    #     'int_pct_v3': float, 'aff_pct_v3': float, 'act_pct_v3': float,
    #     'int_pct_v4': float, 'aff_pct_v4': float, 'act_pct_v4': float,
    #     'int_pct_v5': float, 'aff_pct_v5': float, 'act_pct_v5': float,
    #     'v5_scored_phrases': [(phrase_text, {'int':%, 'aff':%, 'act':%, 'dominant':str, ...}), ...]
    #   }

Dictionaries (INT/AFF/ACT/FUNCTION/B_WORDS/C_WORDS) are duplicated from the
phrase library for independence. When the phrase library updates its dicts,
update this file to match — or refactor both to import from a shared source.

SYNINT Team — April 2026
"""

import re
from typing import Dict, List, Tuple

# =============================================================================
# DICTIONARIES (mirrored from syniq_phrase_library_v3.py — keep in sync)
# =============================================================================

INT_WORDS = set([
    "analyze","analysis","analytical","argument","assert","assumption","calculate",
    "causal","causality","claim","classify","cognitive","coherent","complex",
    "concept","conceptual","conclude","conclusion","condition","consider",
    "construct","contradiction","criteria","critical","deduce","deductive",
    "define","definition","demonstrate","determine","differentiate","dilemma",
    "dimension","distinguish","empirical","entail","evaluate","evidence",
    "examine","explain","explanation","explicit","fallacy","formal",
    "framework","hypothesis","identify","implication","infer","inference",
    "intellectual","interpret","knowledge","logic","logical","mechanism","model",
    "objective","observe","paradox","pattern","perceive","philosophical",
    "premise","principle","proof","propose","rational","reason","reasoning",
    "recognize","recursive","reflect","relation","resolve","rigorous","semantic",
    "systematic","theorem","theoretical","theory","think","thought","truth",
    "understand","understanding","universal","validate","validity","variable",
    "verify","abstract","deduction","dialectic","epistemology","implicit",
    "inconsistent","induction","inherent","inquiry","insight","interrogate",
    "limitation","meta","methodology","postulate","precise","proposition",
    "quantify","scope","taxonomy","underlying","unified"
])

AFF_WORDS = set([
    "accept","affection","afraid","anguish","anxiety","appreciate","authentic",
    "beautiful","belong","care","caring","compassion","concern","connect","connection",
    "cope","courage","dear","deeply","despair","dignity","distress","empath","empathy",
    "emotion","emotional","experience","fear","feel","feeling","feelings","fond",
    "grief","grieve","guilt","heal","heart","hope","hurt","intimate","joy","kind",
    "kindness","lonely","loneliness","loss","love","meaningful","mourn","nurture",
    "pain","passion","peaceful","personal","profound","protect","resilience","sad",
    "sadness","safe","shame","share","sorrow","spirit","suffer","support","tender",
    "touch","trauma","trust","value","vulnerability","vulnerable","warm","warmth",
    "worry","yearn","ache","affirmation","anchor","belonging","cherish",
    "comfort","consolation","devastate","difficult","embrace","empowerment","endure",
    "forgive","fragile","gentle","grounded","hardship","honor","human","humane",
    "identity","innate","irreplaceable","lament","meaning","memory","nurturing",
    "overwhelming","precious","presence","raw","reassure","recognition","relationship",
    "release","remember","sacred","sensitive","soul","strength","struggle",
    "transform","unconditional","witness","wound"
])

ACT_WORDS = set([
    "accomplish","achieve","action","activate","adapt","address","advance","advocate",
    "apply","approach","assess","build","change","choose","collaborate","commit",
    "communicate","complete","consult","contribute","coordinate","create",
    "decide","deliver","deploy","design","develop","direct","distribute","enable",
    "engage","enhance","ensure","establish","evaluate","execute","expand","facilitate",
    "focus","fund","generate","implement","improve","increase","initiate","innovate",
    "integrate","invest","launch","lead","manage","measure","mobilize","monitor",
    "navigate","optimize","organize","partner","perform","plan","policy","prepare",
    "prioritize","produce","program","provide","pursue","reach","recommend","reform",
    "regulate","resource","respond","restructure","scale","solve","step","strategy",
    "strengthen","structure","sustain","tackle","target","train","transform",
    "transition","utilize","work","accelerate","allocate","benchmark","coordinate",
    "delegate","deploy","drive","empower","equip","execute","expand","formulate",
    "govern","incentivize","intervene","leverage","mobilize","operationalize","pilot",
    "procure","rollout","standardize","streamline","systematize","track","uptake"
])

FUNCTION_WORDS = set([
    "a","an","the","and","but","or","nor","for","yet","so","in","on","at","to",
    "of","with","by","from","up","about","into","through","during","before",
    "after","above","below","between","out","off","over","under","again","further",
    "then","once","here","there","when","where","why","how","all","both","each",
    "few","more","most","other","some","such","no","not","only","own","same","than",
    "too","very","just","as","if","while","although","because","since","unless",
    "until","though","whether","this","that","these","those","i","you","he","she",
    "it","we","they","what","which","who","whom","my","your","his","her","its",
    "our","their","am","is","are","was","were","be","been","being","have","has",
    "had","do","does","did","will","would","shall","should","may","might","must",
    "can","could","also","even","still","back","any","many","much","well","now",
    "via","per","vs","etc","months","years","days","weeks","recently","currently",
    "first","next","rather","specific","response","given","within","based","several",
    "certain","particular","significant","important","major","various","example",
    "context","process","point","aspect","factor","carrying","watching","making",
    "providing","bringing","having","getting","going","coming","taking","putting"
])

# B_WORDS: words with POS-dependent dim assignment (2 dims)
B_WORDS = {
    "love":      {"NOUN": ["AFF"], "VERB": ["AFF","ACT"]},
    "fear":      {"NOUN": ["AFF"], "VERB": ["AFF","ACT"]},
    "hope":      {"NOUN": ["AFF"], "VERB": ["AFF","ACT"]},
    "trust":     {"NOUN": ["AFF"], "VERB": ["AFF","ACT"]},
    "care":      {"NOUN": ["AFF"], "VERB": ["AFF","ACT"]},
    "support":   {"NOUN": ["AFF"], "VERB": ["AFF","ACT"]},
    "heal":      {"NOUN": ["AFF"], "VERB": ["AFF","ACT"]},
    "connect":   {"NOUN": ["AFF"], "VERB": ["AFF","ACT"]},
    "share":     {"NOUN": ["AFF"], "VERB": ["AFF","ACT"]},
    "question":  {"NOUN": ["INT"], "VERB": ["INT","ACT"]},
    "examine":   {"NOUN": ["INT"], "VERB": ["INT","ACT"]},
    "reflect":   {"NOUN": ["INT"], "VERB": ["INT","ACT"]},
    "analyze":   {"NOUN": ["INT"], "VERB": ["INT","ACT"]},
    "explore":   {"NOUN": ["INT"], "VERB": ["INT","ACT"]},
    "wonder":    {"NOUN": ["INT","AFF"], "VERB": ["INT","AFF"]},
}

# C_WORDS: words that span all three dims regardless of POS (ambiguous)
C_WORDS = {
    "understand":{"NOUN": ["INT","AFF","ACT"], "VERB": ["INT","AFF","ACT"]},
    "transform": {"NOUN": ["INT","AFF","ACT"], "VERB": ["INT","AFF","ACT"]},
    "believe":   {"NOUN": ["INT","AFF","ACT"], "VERB": ["INT","AFF","ACT"]},
    "know":      {"NOUN": ["INT","AFF","ACT"], "VERB": ["INT","AFF","ACT"]},
    "meaning":   {"NOUN": ["INT","AFF","ACT"], "VERB": ["INT","AFF","ACT"]},
}

VERB_CONTEXT = {'to','will','would','can','could','should','must','may','might',
                'do','does','did','is','are','was','were','be','been','i','we',
                'they','you','he','she','it','let','help','helps','helped'}
NOUN_CONTEXT = {'the','a','an','of','in','with','my','your','his','her','its',
                'our','their','this','that','these','those','no','any','some','all'}

# =============================================================================
# V3 — WORD-LEVEL (matches V50's analyze_text method)
# =============================================================================

def score_v3(text: str) -> Tuple[float, float, float]:
    """Unique-word set intersection against dim dictionaries. Returns (int%, aff%, act%)."""
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    word_set = set(words)
    ih = word_set & INT_WORDS
    ah = word_set & AFF_WORDS
    ch = word_set & ACT_WORDS
    t = len(ih) + len(ah) + len(ch)
    if t == 0:
        return 33.3, 33.3, 33.3
    return 100 * len(ih) / t, 100 * len(ah) / t, 100 * len(ch) / t

# =============================================================================
# V4 — WORD-LEVEL POS-AWARE
# =============================================================================

def _pos_tag(words: List[str]) -> List[Tuple[str, str]]:
    tagged = []
    for i, w in enumerate(words):
        prev = words[i-1] if i > 0 else ''
        if prev in VERB_CONTEXT:
            pos = 'VERB'
        elif w.endswith('ing') and len(w) > 4 and w not in ('thing','nothing','something','during','morning','evening'):
            pos = 'VERB'
        elif prev in NOUN_CONTEXT:
            pos = 'NOUN'
        elif w.endswith(('tion','sion','ness','ment','ity','ance','ence','ship')):
            pos = 'NOUN'
        else:
            pos = 'AMBIG'
        tagged.append((w, pos))
    return tagged

def score_v4(text: str) -> Tuple[float, float, float]:
    """POS-aware word scoring. Disambiguates 'address' (verb→ACT) vs 'address' (noun)."""
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    tagged = _pos_tag(words)
    int_s = aff_s = act_s = 0.0
    seen = set()
    for word, pos in tagged:
        if word in seen or word in FUNCTION_WORDS:
            continue
        seen.add(word)
        if word in C_WORDS:
            dims = C_WORDS[word].get(pos, ["INT", "AFF", "ACT"])
            w = 1 / len(dims)
            for d in dims:
                if d == 'INT': int_s += w
                elif d == 'AFF': aff_s += w
                elif d == 'ACT': act_s += w
        elif word in B_WORDS:
            dims = B_WORDS[word].get(pos, list(B_WORDS[word].values())[0])
            w = 1 / len(dims)
            for d in dims:
                if d == 'INT': int_s += w
                elif d == 'AFF': aff_s += w
                elif d == 'ACT': act_s += w
        elif word in INT_WORDS:
            int_s += 1
        elif word in AFF_WORDS:
            aff_s += 1
        elif word in ACT_WORDS:
            act_s += 1
    t = int_s + aff_s + act_s
    if t == 0:
        return 33.3, 33.3, 33.3
    return 100 * int_s / t, 100 * aff_s / t, 100 * act_s / t

# =============================================================================
# V5 — PHRASE-LEVEL
# =============================================================================

def _simple_pos(word: str) -> str:
    w = word.lower()
    if w in FUNCTION_WORDS: return 'FUNC'
    if w in ACT_WORDS or w.rstrip('s') in ACT_WORDS: return 'VERB'
    if w in INT_WORDS and w.endswith(('ize','ise','ify','ate')): return 'VERB'
    if w.endswith(('tion','sion','ness','ment','ity','ance','ence','ship','ism','logy')): return 'NOUN'
    if w.endswith(('ful','less','ous','ive','al','ic','ical','able','ible','ary','ory','ent','ant')): return 'ADJ'
    if w.endswith(('ing','ed')) and len(w) > 5: return 'VERB'
    return 'NOUN'

_PREP_LINKS = {'into','through','forward','together','over','across',
               'between','within','beyond','without','toward','upon'}

def _extract_phrases(text: str, max_words: int = 5) -> List[Tuple[str, str]]:
    """Extract VP (verb phrase) and NP (noun phrase) chunks as semantic units."""
    sentences = re.split(r'[.!?;:]+', str(text))
    phrase_data = []

    for sent in sentences:
        words = re.findall(r'\b[a-zA-Z]+\b', sent)
        if len(words) < 2:
            continue
        tagged = [(w, _simple_pos(w)) for w in words]

        i = 0
        while i < len(tagged):
            word, pos = tagged[i]

            # VERB PHRASE
            if pos == 'VERB' and word.lower() not in FUNCTION_WORDS:
                phrase_words = [word]
                j = i + 1
                while j < len(tagged) and j < i + max_words:
                    nw, np_ = tagged[j]
                    if np_ == 'FUNC':
                        if nw.lower() in _PREP_LINKS and j + 1 < len(tagged) and tagged[j+1][1] != 'FUNC':
                            phrase_words.append(nw)
                            j += 1
                            continue
                        break
                    phrase_words.append(nw)
                    j += 1
                if len(phrase_words) >= 2:
                    phrase_data.append((' '.join(phrase_words), 'VP'))
                i += 1
                continue

            # NOUN PHRASE
            if pos in ('NOUN', 'ADJ') and word.lower() not in FUNCTION_WORDS:
                phrase_words = [word]
                j = i + 1
                while j < len(tagged) and j < i + max_words:
                    nw, np_ = tagged[j]
                    if np_ in ('NOUN', 'ADJ') and nw.lower() not in FUNCTION_WORDS:
                        phrase_words.append(nw)
                        j += 1
                    else:
                        break
                if len(phrase_words) >= 2:
                    phrase_data.append((' '.join(phrase_words), 'NP'))
                i = j if j > i else i + 1
                continue

            i += 1

    return phrase_data

def _score_phrase(phrase: str, ptype: str = 'NP'):
    """Score a single phrase. VERB ANCHOR RULE: VP verb determines base dim."""
    words = phrase.lower().split()
    int_hits = [w for w in words if w in INT_WORDS]
    aff_hits = [w for w in words if w in AFF_WORDS]
    act_hits = [w for w in words if w in ACT_WORDS]

    int_s = float(len(int_hits))
    aff_s = float(len(aff_hits))
    act_s = float(len(act_hits))

    if ptype == 'VP' and words:
        verb = words[0]
        if verb in ACT_WORDS or verb.rstrip('s') in ACT_WORDS:
            act_s += 1.5
        elif verb in INT_WORDS:
            int_s += 1.5
        elif verb in AFF_WORDS:
            aff_s += 1.5

    total = int_s + aff_s + act_s
    if total == 0:
        return None

    int_pct = 100 * int_s / total
    aff_pct = 100 * aff_s / total
    act_pct = 100 * act_s / total
    dominant = max([('INT', int_pct), ('AFF', aff_pct), ('ACT', act_pct)], key=lambda x: x[1])
    return {
        'int': round(int_pct, 1),
        'aff': round(aff_pct, 1),
        'act': round(act_pct, 1),
        'dominant': dominant[0],
        'confidence': round(dominant[1] / 100, 3),
        'ptype': ptype,
    }

def score_v5(text: str) -> Tuple[float, float, float, List[Tuple[str, Dict]]]:
    """Phrase-level scoring. Returns (int%, aff%, act%, scored_phrases_list)."""
    phrases = _extract_phrases(text)
    if not phrases:
        return 33.3, 33.3, 33.3, []
    int_total = aff_total = act_total = 0.0
    scored_phrases = []
    for p, ptype in phrases:
        s = _score_phrase(p, ptype)
        if s:
            int_total += s['int']
            aff_total += s['aff']
            act_total += s['act']
            scored_phrases.append((p, s))
    t = int_total + aff_total + act_total
    if t == 0:
        return 33.3, 33.3, 33.3, []
    return (
        100 * int_total / t,
        100 * aff_total / t,
        100 * act_total / t,
        scored_phrases,
    )

# =============================================================================
# UNIFIED CALL
# =============================================================================

def score_all_tracks(text: str) -> Dict:
    """Run V3, V4, V5 scoring. Returns flat dict suitable for CSV row inclusion.

    V5 scored_phrases list is included as-is (tuples). Serialize to JSON at
    write time if exporting to CSV.
    """
    if not text or (isinstance(text, str) and text.startswith("❌")):
        return {
            'int_pct_v3': 0.0, 'aff_pct_v3': 0.0, 'act_pct_v3': 0.0,
            'int_pct_v4': 0.0, 'aff_pct_v4': 0.0, 'act_pct_v4': 0.0,
            'int_pct_v5': 0.0, 'aff_pct_v5': 0.0, 'act_pct_v5': 0.0,
            'v5_scored_phrases': [],
        }

    i3, a3, c3 = score_v3(text)
    i4, a4, c4 = score_v4(text)
    i5, a5, c5, scored_phrases = score_v5(text)

    return {
        'int_pct_v3': round(i3, 1),
        'aff_pct_v3': round(a3, 1),
        'act_pct_v3': round(c3, 1),
        'int_pct_v4': round(i4, 1),
        'aff_pct_v4': round(a4, 1),
        'act_pct_v4': round(c4, 1),
        'int_pct_v5': round(i5, 1),
        'aff_pct_v5': round(a5, 1),
        'act_pct_v5': round(c5, 1),
        'v5_scored_phrases': scored_phrases,
    }
