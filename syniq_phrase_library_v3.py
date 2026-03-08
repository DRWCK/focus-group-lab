"""
SYN-IQ Phrase Library Builder V3
==================================
Three parallel IEP scoring tracks from V50 CSV or DOCX:
  V3 — Word-level lexical (current)
  V4 — Word-level POS-aware
  V5 — Phrase-level (NEW)

+ Condition Comparison Tab: Native vs Gradient phrase overlap
+ DOCX upload support (V48 format)

Neither invalidates the other — the data decides.

Tennessee 🎹 CUZ Partnership · SYNINT March 2026
"""

import streamlit as st
import pandas as pd
import numpy as np
import re
import json
from datetime import datetime
from collections import defaultdict

# DOCX support
try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

QUESTIONS_ORDER = ['LEAVE_JOB','LIARS_PARADOX','RURAL_HEALTHCARE','GRIEF','CONSCIOUSNESS']
QUESTION_KEYS = {
    'leave':'LEAVE_JOB','passion':'LEAVE_JOB','stable job':'LEAVE_JOB',
    'liar':'LIARS_PARADOX','paradox':'LIARS_PARADOX','statement is false':'LIARS_PARADOX',
    'rural':'RURAL_HEALTHCARE','healthcare':'RURAL_HEALTHCARE','communities':'RURAL_HEALTHCARE',
    'grief':'GRIEF','loss':'GRIEF','mourn':'GRIEF',
    'consciousness':'CONSCIOUSNESS','conscious':'CONSCIOUSNESS','aware':'CONSCIOUSNESS'
}

def parse_docx(file):
    """Parse V48-style DOCX into DataFrame with response_text"""
    doc = DocxDocument(file)
    paras = [p.text.strip() for p in doc.paragraphs]
    rows = []
    run_num = None
    q_index = 0
    for i, p in enumerate(paras):
        m = re.match(r'Run (\d+)\s+\|\s+Depth:\s+(\S+)\s+\|.*INT:\s*([\d.]+)%\s+AFF:\s*([\d.]+)%\s+ACT:\s*([\d.]+)%.*Words:\s*(\d+)', p)
        if m:
            new_run = int(m.group(1))
            if new_run != run_num:
                run_num = new_run
                q_index = 0
            meta = {
                'run': run_num, 'depth': m.group(2),
                'int_pct': float(m.group(3)), 'aff_pct': float(m.group(4)),
                'act_pct': float(m.group(5)), 'words': int(m.group(6)),
                'question_id': QUESTIONS_ORDER[q_index % 5],
                'temperature': 'NATIVE', 'agent': 'Claude'
            }
            q_index += 1
            j = i + 1
            while j < len(paras) and (not paras[j] or '────' in paras[j]):
                j += 1
            meta['response_text'] = paras[j] if j < len(paras) else ''
            rows.append(meta)
    return pd.DataFrame(rows)

# =============================================================================
# PAGE CONFIG
# =============================================================================
st.set_page_config(
    page_title="SYN-IQ Phrase Library Builder V3",
    page_icon="📚",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
html, body, [class*="css"] { background-color: #060b14; color: #c8d8e8; font-family: 'JetBrains Mono', monospace; }
.stApp { background-color: #060b14; }
.main-title { font-family: 'JetBrains Mono', monospace; font-size: 1.8rem; font-weight: 700; color: #ffffff; text-align: center; padding: 1.5rem 0 0.3rem 0; }
.sub-title { font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; color: #5566aa; text-align: center; margin-bottom: 2rem; }
.metric-card { background: #0a1020; border: 1px solid #1a2a4a; border-radius: 8px; padding: 1rem; text-align: center; }
.metric-card .val { font-size: 1.8rem; font-weight: 700; color: #ffffff; }
.metric-card .lbl { font-size: 0.7rem; color: #667788; margin-top: 0.3rem; }
.section-header { font-family: 'JetBrains Mono', monospace; font-size: 1rem; font-weight: 700; color: #7eb8ff; border-bottom: 1px solid #1a2a4a; padding-bottom: 0.5rem; margin: 1.5rem 0 1rem 0; }
.phrase-card { background: #0a1020; border: 1px solid #1a2a4a; border-radius: 8px; padding: 1rem; margin: 0.5rem 0; font-family: 'JetBrains Mono', monospace; }
.v3-col { color: #44ff88; }
.v4-col { color: #4488ff; }
.v5-col { color: #ffaa44; }
.badge { display: inline-block; padding: 2px 10px; border-radius: 4px; font-size: 0.75rem; font-weight: 700; font-family: 'JetBrains Mono', monospace; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# IEP DICTIONARIES
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
# SCORING FUNCTIONS
# =============================================================================

def pos_tag(words):
    tagged = []
    for i, w in enumerate(words):
        prev = words[i-1] if i > 0 else ''
        if prev in VERB_CONTEXT: pos = 'VERB'
        elif w.endswith('ing') and len(w) > 4 and w not in ('thing','nothing','something','during','morning','evening'): pos = 'VERB'
        elif prev in NOUN_CONTEXT: pos = 'NOUN'
        elif w.endswith(('tion','sion','ness','ment','ity','ance','ence','ship')): pos = 'NOUN'
        else: pos = 'AMBIG'
        tagged.append((w, pos))
    return tagged

def score_v3(text):
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    word_set = set(words)
    ih = word_set & INT_WORDS
    ah = word_set & AFF_WORDS
    ch = word_set & ACT_WORDS
    t = len(ih) + len(ah) + len(ch)
    if t == 0: return 33.3, 33.3, 33.3
    return 100*len(ih)/t, 100*len(ah)/t, 100*len(ch)/t

def score_v4(text):
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    tagged = pos_tag(words)
    is_ = af_ = ac_ = 0.0
    seen = set()
    for word, pos in tagged:
        if word in seen or word in FUNCTION_WORDS: continue
        seen.add(word)
        if word in C_WORDS:
            dims = C_WORDS[word].get(pos, ["INT","AFF","ACT"])
            w = 1/len(dims)
            for d in dims:
                if d=='INT': is_+=w
                elif d=='AFF': af_+=w
                elif d=='ACT': ac_+=w
        elif word in B_WORDS:
            dims = B_WORDS[word].get(pos, list(B_WORDS[word].values())[0])
            w = 1/len(dims)
            for d in dims:
                if d=='INT': is_+=w
                elif d=='AFF': af_+=w
                elif d=='ACT': ac_+=w
        elif word in INT_WORDS: is_ += 1
        elif word in AFF_WORDS: af_ += 1
        elif word in ACT_WORDS: ac_ += 1
    t = is_ + af_ + ac_
    if t == 0: return 33.3, 33.3, 33.3
    return 100*is_/t, 100*af_/t, 100*ac_/t

def score_phrase(phrase):
    words = phrase.lower().split()
    int_hits = [w for w in words if w in INT_WORDS]
    aff_hits = [w for w in words if w in AFF_WORDS]
    act_hits = [w for w in words if w in ACT_WORDS]
    func_hits = [w for w in words if w in FUNCTION_WORDS]
    total = len(int_hits) + len(aff_hits) + len(act_hits)
    if total == 0: return None
    int_pct = 100*len(int_hits)/total
    aff_pct = 100*len(aff_hits)/total
    act_pct = 100*len(act_hits)/total
    dominant = max([('INT',int_pct),('AFF',aff_pct),('ACT',act_pct)], key=lambda x: x[1])
    confidence = dominant[1]/100
    return {
        'int': int_pct, 'aff': aff_pct, 'act': act_pct,
        'dominant': dominant[0], 'confidence': confidence,
        'int_hits': int_hits, 'aff_hits': aff_hits, 'act_hits': act_hits,
        'func_hits': func_hits
    }

def simple_pos(word):
    """Rule-based POS tagger for phrase chunking"""
    w = word.lower()
    if w in FUNCTION_WORDS: return 'FUNC'
    if w in ACT_WORDS or w.rstrip('s') in ACT_WORDS: return 'VERB'
    if w in INT_WORDS and w.endswith(('ize','ise','ify','ate')): return 'VERB'
    if w.endswith(('tion','sion','ness','ment','ity','ance','ence','ship','ism','logy')): return 'NOUN'
    if w.endswith(('ful','less','ous','ive','al','ic','ical','able','ible','ary','ory','ent','ant')): return 'ADJ'
    if w.endswith(('ing','ed')) and len(w) > 5: return 'VERB'
    return 'NOUN'

def extract_phrases(text, min_words=2, max_words=5):
    """Extract linguistic phrases (VP and NP) as semantic units — not n-gram windows"""
    sentences = re.split(r'[.!?;:]+', str(text))
    phrase_data = []

    for sent in sentences:
        words = re.findall(r'\b[a-zA-Z]+\b', sent)
        if len(words) < 2: continue
        tagged = [(w, simple_pos(w)) for w in words]

        i = 0
        while i < len(tagged):
            word, pos = tagged[i]

            # VERB PHRASE — verb + up to 4 following content words
            if pos == 'VERB' and word.lower() not in FUNCTION_WORDS:
                phrase_words = [word]
                ptype = 'VP'
                j = i + 1
                while j < len(tagged) and j < i + max_words:
                    nw, np = tagged[j]
                    if np == 'FUNC':
                        prep_links = {'into','through','forward','together','over','across',
                                      'between','within','beyond','without','toward','upon'}
                        if nw.lower() in prep_links and j+1 < len(tagged) and tagged[j+1][1] != 'FUNC':
                            phrase_words.append(nw)
                            j += 1
                            continue
                        break
                    phrase_words.append(nw)
                    j += 1
                if len(phrase_words) >= 2:
                    phrase_data.append((' '.join(phrase_words), ptype))
                i += 1
                continue

            # NOUN PHRASE — (ADJ*) NOUN (NOUN*)
            if pos in ('NOUN','ADJ') and word.lower() not in FUNCTION_WORDS:
                phrase_words = [word]
                ptype = 'NP'
                j = i + 1
                while j < len(tagged) and j < i + max_words:
                    nw, np = tagged[j]
                    if np in ('NOUN','ADJ') and nw.lower() not in FUNCTION_WORDS:
                        phrase_words.append(nw)
                        j += 1
                    elif np == 'FUNC' and nw.lower() in ('of','in','for') and j+1 < len(tagged) and tagged[j+1][1] in ('NOUN','ADJ'):
                        phrase_words.append(nw)
                        j += 1
                    else:
                        break
                if len(phrase_words) >= 2:
                    phrase_data.append((' '.join(phrase_words), ptype))
                i += 1
                continue

            i += 1

    # Deduplicate — keep longest phrase when sub-phrases overlap
    final = []
    used = set()
    for phrase, ptype in phrase_data:
        if phrase not in used:
            final.append((phrase, ptype))
            # Mark all sub-phrases as used
            words = phrase.split()
            for n in range(2, len(words)):
                for k in range(len(words)-n+1):
                    sub = ' '.join(words[k:k+n])
                    used.add(sub)
    return final

def score_phrase(phrase, ptype='NP'):
    """Score phrase with VERB ANCHOR RULE — VP verb determines dimension, objects give register"""
    words = phrase.lower().split()

    int_hits = [w for w in words if w in INT_WORDS]
    aff_hits = [w for w in words if w in AFF_WORDS]
    act_hits = [w for w in words if w in ACT_WORDS]

    int_score = float(len(int_hits))
    aff_score = float(len(aff_hits))
    act_score = float(len(act_hits))

    # VERB ANCHOR RULE: for VP, the verb word determines the base dimension
    if ptype == 'VP' and words:
        verb = words[0]
        if verb in ACT_WORDS or verb.rstrip('s') in ACT_WORDS:
            act_score += 1.5   # verb anchors ACT
        elif verb in INT_WORDS:
            int_score += 1.5   # verb anchors INT
        elif verb in AFF_WORDS:
            aff_score += 1.5   # verb anchors AFF

    total = int_score + aff_score + act_score
    if total == 0: return None

    int_pct = 100*int_score/total
    aff_pct = 100*aff_score/total
    act_pct = 100*act_score/total
    dominant = max([('INT',int_pct),('AFF',aff_pct),('ACT',act_pct)], key=lambda x: x[1])
    return {
        'int': int_pct, 'aff': aff_pct, 'act': act_pct,
        'dominant': dominant[0], 'confidence': dominant[1]/100,
        'ptype': ptype,
        'int_hits': int_hits, 'aff_hits': aff_hits, 'act_hits': act_hits,
    }

def score_v5(text):
    phrases = extract_phrases(text)
    if not phrases: return 33.3, 33.3, 33.3, []
    int_total = aff_total = act_total = 0.0
    scored_phrases = []
    for p, ptype in phrases:
        s = score_phrase(p, ptype)
        if s:
            int_total += s['int']
            aff_total += s['aff']
            act_total += s['act']
            scored_phrases.append((p, s))
    t = int_total + aff_total + act_total
    if t == 0: return 33.3, 33.3, 33.3, []
    return 100*int_total/t, 100*aff_total/t, 100*act_total/t, scored_phrases

def dim_color(dim):
    return {'INT':'#4488ff','AFF':'#ff6688','ACT':'#44ff88'}.get(dim,'#888888')

def delta_color(d):
    if abs(d) < 1: return "#888888"
    return "#44ff88" if d > 0 else "#ff4444"

# =============================================================================
# PHRASE LIBRARY BUILDER — Aggregates across full corpus
# =============================================================================

def build_phrase_library(df, min_freq=3):
    phrase_stats = defaultdict(lambda: {
        'count': 0, 'int_sum': 0, 'aff_sum': 0, 'act_sum': 0,
        'questions': set(), 'agents': set(), 'depths': set(),
        'dominant': None, 'confidence': 0
    })
    
    progress = st.progress(0)
    status = st.empty()
    total = len(df)
    
    for i, row in df.iterrows():
        status.markdown(f"Extracting phrases: row {i+1}/{total}...")
        progress.progress((i+1)/total)
        text = str(row.get('response_text',''))
        phrases = extract_phrases(text)
        
        for phrase, ptype in phrases:
            s = score_phrase(phrase, ptype)
            if not s: continue
            ps = phrase_stats[phrase]
            ps['count'] += 1
            ps['int_sum'] += s['int']
            ps['aff_sum'] += s['aff']
            ps['act_sum'] += s['act']
            if 'question_id' in row: ps['questions'].add(row['question_id'])
            if 'agent' in row: ps['agents'].add(row['agent'])
            if 'depth' in row: ps['depths'].add(row['depth'])
    
    progress.empty(); status.empty()
    
    # Build library — filter by min frequency
    library = []
    for phrase, stats in phrase_stats.items():
        if stats['count'] < min_freq: continue
        n = stats['count']
        int_avg = stats['int_sum']/n
        aff_avg = stats['aff_sum']/n
        act_avg = stats['act_sum']/n
        dominant = max([('INT',int_avg),('AFF',aff_avg),('ACT',act_avg)], key=lambda x: x[1])
        confidence = dominant[1]/100
        library.append({
            'phrase': phrase,
            'frequency': n,
            'int_pct': int_avg,
            'aff_pct': aff_avg,
            'act_pct': act_avg,
            'dominant': dominant[0],
            'confidence': confidence,
            'question_count': len(stats['questions']),
            'agent_count': len(stats['agents']),
            'depth_count': len(stats['depths']),
            'questions': ', '.join(sorted(stats['questions'])),
            'agents': ', '.join(sorted(stats['agents'])),
            'depths': ', '.join(sorted(stats['depths'])),
            'phrase_score': n * len(stats['questions']) * len(stats['agents']) * len(stats['depths'])
        })
    
    return pd.DataFrame(library).sort_values('phrase_score', ascending=False)

# =============================================================================
# MAIN APP
# =============================================================================

st.markdown('<div class="main-title">📚 SYN-IQ Phrase Library Builder V3</div>', unsafe_allow_html=True)
st.markdown('''<div class="sub-title">
    <span style="color:#44ff88;font-weight:700;">V3 Word-Lexical</span>
    &nbsp;·&nbsp;
    <span style="color:#4488ff;font-weight:700;">V4 Word-POS</span>
    &nbsp;·&nbsp;
    <span style="color:#ffaa44;font-weight:700;">V5 Phrase-Level</span>
    &nbsp;&nbsp;·&nbsp;&nbsp;Three parallel tracks · Neither invalidates the other
</div>''', unsafe_allow_html=True)

# SIDEBAR
with st.sidebar:
    st.markdown("### 📚 Phrase Library Builder")
    st.markdown("**Version:** V1 · March 2026")
    pwd = st.text_input("Password", type="password")
    if pwd != "tennessee":
        st.warning("Enter password to continue")
        st.stop()
    st.markdown("---")
    st.markdown("**V3** — Word, lexical only")
    st.markdown("**V4** — Word, POS-aware")
    st.markdown("**V5** — Phrase-level scoring")
    st.markdown("---")
    min_phrase_len = st.slider("Min phrase length (words)", 2, 3, 2)
    max_phrase_len = st.slider("Max phrase length (words)", 3, 6, 4)
    min_frequency = st.slider("Min phrase frequency", 2, 10, 3)
    st.markdown("---")
    st.caption("Tennessee 🎹 CUZ Partnership · SYNINT")

# TABS
tabs = st.tabs([
    "📁 Load & Score",
    "📊 Three-Track Comparison",
    "🔺 Simplex — All Three",
    "📚 Phrase Library",
    "🔤 Phrase Explorer",
    "🤖 Agent Vocabulary",
    "🔁 Condition Comparison",
    "📋 Verdict"
])

# =============================================================================
# TAB 1 — LOAD & SCORE
# =============================================================================
with tabs[0]:
    st.markdown('<div class="section-header">📁 Load V50 CSV or V48 DOCX — Score All Three Tracks</div>', unsafe_allow_html=True)

    if st.button("🗑️ Clear All Data"):
        for key in ['df','scored','phrase_lib']:
            if key in st.session_state:
                del st.session_state[key]
        st.success("Cleared! Upload a new file.")
        st.rerun()

    uploaded = st.file_uploader("Upload V50 CSV or V48 DOCX", type=None)

    if uploaded:
        fname = uploaded.name.lower()
        if fname.endswith('.docx'):
            if not DOCX_AVAILABLE:
                st.error("python-docx not available — check requirements.txt")
                st.stop()
            with st.spinner("Parsing DOCX..."):
                df = parse_docx(uploaded)
            if len(df) == 0:
                st.error("No responses parsed from DOCX — check file format")
                st.stop()
            st.success(f"✅ DOCX parsed — {len(df)} responses extracted")
        elif fname.endswith('.csv'):
            df = pd.read_csv(uploaded)
        else:
            st.error(f"Unsupported file type: {uploaded.name} — upload CSV or DOCX")
            st.stop()
        st.session_state['df'] = df

        col1,col2,col3,col4 = st.columns(4)
        with col1: st.markdown(f'<div class="metric-card"><div class="val">{len(df)}</div><div class="lbl">Responses</div></div>', unsafe_allow_html=True)
        with col2: st.markdown(f'<div class="metric-card"><div class="val">{df["agent"].nunique() if "agent" in df.columns else "?"}</div><div class="lbl">Agents</div></div>', unsafe_allow_html=True)
        with col3: st.markdown(f'<div class="metric-card"><div class="val">{df["question_id"].nunique() if "question_id" in df.columns else "?"}</div><div class="lbl">Questions</div></div>', unsafe_allow_html=True)
        with col4: st.markdown(f'<div class="metric-card"><div class="val">{df["depth"].nunique() if "depth" in df.columns else "?"}</div><div class="lbl">Depths</div></div>', unsafe_allow_html=True)
        
        if st.button("🔬 Run All Three Tracks", type="primary"):
            results = []
            progress = st.progress(0)
            status = st.empty()
            
            for i, row in df.iterrows():
                status.markdown(f"Scoring row {i+1}/{len(df)}...")
                progress.progress((i+1)/len(df))
                text = str(row.get('response_text',''))
                
                i3,a3,c3 = score_v3(text)
                i4,a4,c4 = score_v4(text)
                i5,a5,c5,_ = score_v5(text)
                
                results.append({
                    'int_v3':i3,'aff_v3':a3,'act_v3':c3,
                    'int_v4':i4,'aff_v4':a4,'act_v4':c4,
                    'int_v5':i5,'aff_v5':a5,'act_v5':c5,
                    'delta_int_v4v3':i4-i3,'delta_aff_v4v3':a4-a3,'delta_act_v4v3':c4-c3,
                    'delta_int_v5v3':i5-i3,'delta_aff_v5v3':a5-a3,'delta_act_v5v3':c5-c3,
                    'delta_int_v5v4':i5-i4,'delta_aff_v5v4':a5-a4,'delta_act_v5v4':c5-c4,
                })
            
            progress.empty(); status.empty()
            scored = pd.concat([df.reset_index(drop=True), pd.DataFrame(results)], axis=1)
            st.session_state['scored'] = scored
            st.success(f"✅ All three tracks scored — {len(scored)} responses ready!")
            
            # Build phrase library
            st.markdown("---")
            st.markdown("**Building Phrase Library...**")
            phrase_lib = build_phrase_library(df, min_frequency)
            st.session_state['phrase_lib'] = phrase_lib
            st.success(f"✅ Phrase Library: {len(phrase_lib)} unique phrases (min freq={min_frequency})")

# =============================================================================
# TAB 2 — THREE-TRACK COMPARISON
# =============================================================================
with tabs[1]:
    st.markdown('<div class="section-header">📊 Three-Track Score Comparison</div>', unsafe_allow_html=True)
    
    if 'scored' not in st.session_state:
        st.info("Load and score data in Tab 1 first")
    else:
        scored = st.session_state['scored']
        
        if 'question_id' in scored.columns:
            grp = scored.groupby('question_id').agg(
                int_v3=('int_v3','mean'), aff_v3=('aff_v3','mean'), act_v3=('act_v3','mean'),
                int_v4=('int_v4','mean'), aff_v4=('aff_v4','mean'), act_v4=('act_v4','mean'),
                int_v5=('int_v5','mean'), aff_v5=('aff_v5','mean'), act_v5=('act_v5','mean'),
            ).reset_index()
            
            for _, row in grp.iterrows():
                st.markdown(f"""
                <div class="phrase-card">
                    <div style="font-weight:700;font-size:1rem;color:#ffffff;margin-bottom:1rem;">{row['question_id']}</div>
                    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:0.5rem;font-size:0.82rem;">
                        <div>
                            <div style="color:#888;margin-bottom:0.3rem;">INT</div>
                            <div class="v3-col">V3: {row['int_v3']:.1f}%</div>
                            <div class="v4-col">V4: {row['int_v4']:.1f}% <span style="color:{delta_color(row['int_v4']-row['int_v3'])};">({row['int_v4']-row['int_v3']:+.1f}pp)</span></div>
                            <div class="v5-col">V5: {row['int_v5']:.1f}% <span style="color:{delta_color(row['int_v5']-row['int_v3'])};">({row['int_v5']-row['int_v3']:+.1f}pp)</span></div>
                        </div>
                        <div>
                            <div style="color:#888;margin-bottom:0.3rem;">AFF</div>
                            <div class="v3-col">V3: {row['aff_v3']:.1f}%</div>
                            <div class="v4-col">V4: {row['aff_v4']:.1f}% <span style="color:{delta_color(row['aff_v4']-row['aff_v3'])};">({row['aff_v4']-row['aff_v3']:+.1f}pp)</span></div>
                            <div class="v5-col">V5: {row['aff_v5']:.1f}% <span style="color:{delta_color(row['aff_v5']-row['aff_v3'])};">({row['aff_v5']-row['aff_v3']:+.1f}pp)</span></div>
                        </div>
                        <div>
                            <div style="color:#888;margin-bottom:0.3rem;">ACT</div>
                            <div class="v3-col">V3: {row['act_v3']:.1f}%</div>
                            <div class="v4-col">V4: {row['act_v4']:.1f}% <span style="color:{delta_color(row['act_v4']-row['act_v3'])};">({row['act_v4']-row['act_v3']:+.1f}pp)</span></div>
                            <div class="v5-col">V5: {row['act_v5']:.1f}% <span style="color:{delta_color(row['act_v5']-row['act_v3'])};">({row['act_v5']-row['act_v3']:+.1f}pp)</span></div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

# =============================================================================
# TAB 3 — SIMPLEX ALL THREE
# =============================================================================
with tabs[2]:
    st.markdown('<div class="section-header">🔺 Three Simplex Point Clouds — Side by Side</div>', unsafe_allow_html=True)
    
    if 'scored' not in st.session_state:
        st.info("Load and score data in Tab 1 first")
    else:
        scored = st.session_state['scored']
        
        def to_2d(df, ic, ac, cc):
            i=df[ic]/100; a=df[ac]/100; c=df[cc]/100
            x=0.5*(2*a+c)/(i+a+c+1e-9)
            y=(np.sqrt(3)/2)*c/(i+a+c+1e-9)
            return x,y
        
        qcolors = {'LIARS_PARADOX':'#4488ff','GRIEF':'#ff6688','RURAL_HEALTHCARE':'#44ff88',
                  'CONSCIOUSNESS':'#ffaa44','LEAVE_JOB':'#aa44ff'}
        
        def render_simplex_table(label, color, grp_data):
            """Render simplex as HTML table with question centroids"""
            rows = ""
            for _, row in grp_data.iterrows():
                q = row['question_id'] if 'question_id' in row else ''
                qc = qcolors.get(q, '#888888')
                rows += f'''<tr>
                    <td style="color:{qc};font-size:0.75rem;padding:3px 6px;">{q[:20]}</td>
                    <td style="color:#4488ff;font-size:0.75rem;padding:3px 6px;">{row[f"int_{label}"]:.1f}%</td>
                    <td style="color:#ff6688;font-size:0.75rem;padding:3px 6px;">{row[f"aff_{label}"]:.1f}%</td>
                    <td style="color:#44ff88;font-size:0.75rem;padding:3px 6px;">{row[f"act_{label}"]:.1f}%</td>
                </tr>'''
            return f'''<div style="background:#0a1020;border:2px solid {color};border-radius:8px;padding:0.8rem;">
                <div style="color:{color};font-weight:700;font-size:0.9rem;margin-bottom:0.5rem;">{label.upper()} — IEP Scores</div>
                <table style="width:100%;border-collapse:collapse;">
                    <tr><th style="color:#7eb8ff;font-size:0.7rem;text-align:left;padding:2px 6px;">Question</th>
                        <th style="color:#4488ff;font-size:0.7rem;padding:2px 6px;">INT</th>
                        <th style="color:#ff6688;font-size:0.7rem;padding:2px 6px;">AFF</th>
                        <th style="color:#44ff88;font-size:0.7rem;padding:2px 6px;">ACT</th></tr>
                    {rows}
                </table></div>'''

        if 'question_id' in scored.columns:
            grp3 = scored.groupby('question_id').agg(int_v3=('int_v3','mean'),aff_v3=('aff_v3','mean'),act_v3=('act_v3','mean'),int_v4=('int_v4','mean'),aff_v4=('aff_v4','mean'),act_v4=('act_v4','mean'),int_v5=('int_v5','mean'),aff_v5=('aff_v5','mean'),act_v5=('act_v5','mean')).reset_index()
            col1,col2,col3 = st.columns(3)
            with col1: st.markdown(render_simplex_table('v3','#44ff88',grp3), unsafe_allow_html=True)
            with col2: st.markdown(render_simplex_table('v4','#4488ff',grp3), unsafe_allow_html=True)
            with col3: st.markdown(render_simplex_table('v5','#ffaa44',grp3), unsafe_allow_html=True)
        
        x3,y3 = to_2d(scored,'int_v3','aff_v3','act_v3')
        x4,y4 = to_2d(scored,'int_v4','aff_v4','act_v4')
        x5,y5 = to_2d(scored,'int_v5','aff_v5','act_v5')
        
        # Centroid distances
        st.markdown("### Centroid Distance — All Three")
        center_x=0.5; center_y=np.sqrt(3)/6
        d3=float(np.sqrt((np.mean(x3)-center_x)**2+(np.mean(y3)-center_y)**2))
        d4=float(np.sqrt((np.mean(x4)-center_x)**2+(np.mean(y4)-center_y)**2))
        d5=float(np.sqrt((np.mean(x5)-center_x)**2+(np.mean(y5)-center_y)**2))
        col1,col2,col3 = st.columns(3)
        with col1: st.markdown(f'<div class="metric-card"><div class="val v3-col">{d3:.4f}</div><div class="lbl">V3 Centroid Distance</div></div>', unsafe_allow_html=True)
        with col2: st.markdown(f'<div class="metric-card"><div class="val v4-col">{d4:.4f}</div><div class="lbl">V4 Centroid Distance</div></div>', unsafe_allow_html=True)
        with col3: st.markdown(f'<div class="metric-card"><div class="val v5-col">{d5:.4f}</div><div class="lbl">V5 Centroid Distance</div></div>', unsafe_allow_html=True)

# =============================================================================
# TAB 4 — PHRASE LIBRARY
# =============================================================================
with tabs[3]:
    st.markdown('<div class="section-header">📚 Phrase Library — V5 IEP Phrase Lexicon</div>', unsafe_allow_html=True)
    
    if 'phrase_lib' not in st.session_state:
        st.info("Load and score data in Tab 1 first")
    else:
        lib = st.session_state['phrase_lib']
        
        col1,col2,col3,col4 = st.columns(4)
        with col1: st.markdown(f'<div class="metric-card"><div class="val">{len(lib)}</div><div class="lbl">Unique Phrases</div></div>', unsafe_allow_html=True)
        with col2: 
            int_count = len(lib[lib['dominant']=='INT'])
            st.markdown(f'<div class="metric-card"><div class="val" style="color:#4488ff;">{int_count}</div><div class="lbl">INT Phrases</div></div>', unsafe_allow_html=True)
        with col3:
            aff_count = len(lib[lib['dominant']=='AFF'])
            st.markdown(f'<div class="metric-card"><div class="val" style="color:#ff6688;">{aff_count}</div><div class="lbl">AFF Phrases</div></div>', unsafe_allow_html=True)
        with col4:
            act_count = len(lib[lib['dominant']=='ACT'])
            st.markdown(f'<div class="metric-card"><div class="val" style="color:#44ff88;">{act_count}</div><div class="lbl">ACT Phrases</div></div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Filters
        col1,col2,col3 = st.columns(3)
        with col1: dim_filter = st.selectbox("Dimension", ["ALL","INT","AFF","ACT"])
        with col2: min_agents = st.slider("Min agents", 1, 4, 1)
        with col3: min_questions = st.slider("Min questions", 1, 5, 1)
        
        filtered = lib.copy()
        if dim_filter != "ALL": filtered = filtered[filtered['dominant']==dim_filter]
        filtered = filtered[filtered['agent_count']>=min_agents]
        filtered = filtered[filtered['question_count']>=min_questions]
        
        st.markdown(f"**{len(filtered)} phrases match filters**")
        
        for _, row in filtered.head(50).iterrows():
            dc = dim_color(row['dominant'])
            conf_pct = f"{row['confidence']:.0%}"
            st.markdown(f"""
            <div class="phrase-card" style="border-left:3px solid {dc};">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <span style="color:#ffffff;font-size:1rem;font-weight:700;">"{row['phrase']}"</span>
                    <span>
                        <span style="background:{dc}22;color:{dc};padding:2px 8px;border-radius:4px;font-size:0.75rem;font-weight:700;">{row['dominant']} {conf_pct}</span>
                        &nbsp;<span style="color:#888;font-size:0.75rem;">freq={int(row['frequency'])} · {int(row['agent_count'])} agents · {int(row['question_count'])} Qs</span>
                    </span>
                </div>
                <div style="font-size:0.75rem;color:#667788;margin-top:0.3rem;">
                    INT={row['int_pct']:.0f}% · AFF={row['aff_pct']:.0f}% · ACT={row['act_pct']:.0f}%
                    &nbsp;·&nbsp; Questions: {row['questions'][:80]}
                    &nbsp;·&nbsp; Agents: {row['agents']}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        csv_lib = lib.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Download Full Phrase Library CSV",
            data=csv_lib,
            file_name=f"iep_phrase_library_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime='text/csv')

# =============================================================================
# TAB 5 — PHRASE EXPLORER
# =============================================================================
with tabs[4]:
    st.markdown('<div class="section-header">🔤 Phrase Explorer — Score Any Text All Three Ways</div>', unsafe_allow_html=True)
    
    test_text = st.text_area("Enter any text",
        value="Carrying the loss forward creates meaningful connection. We must analyze the evidence carefully and implement practical solutions together. Grief transforms over time into something we can carry without being crushed.",
        height=120)
    
    if test_text:
        i3,a3,c3 = score_v3(test_text)
        i4,a4,c4 = score_v4(test_text)
        i5,a5,c5,scored_phrases = score_v5(test_text)
        
        col1,col2,col3 = st.columns(3)
        with col1:
            st.markdown(f"""<div class="phrase-card" style="border-top:3px solid #44ff88;">
                <div style="color:#44ff88;font-weight:700;margin-bottom:0.5rem;">V3 — Word Lexical</div>
                <div style="font-size:1.1rem;">INT <b style="color:#4488ff;">{i3:.1f}%</b></div>
                <div style="font-size:1.1rem;">AFF <b style="color:#ff6688;">{a3:.1f}%</b></div>
                <div style="font-size:1.1rem;">ACT <b style="color:#44ff88;">{c3:.1f}%</b></div>
            </div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""<div class="phrase-card" style="border-top:3px solid #4488ff;">
                <div style="color:#4488ff;font-weight:700;margin-bottom:0.5rem;">V4 — Word POS-Aware</div>
                <div style="font-size:1.1rem;">INT <b style="color:#4488ff;">{i4:.1f}%</b> <span style="color:{delta_color(i4-i3)};font-size:0.8rem;">({i4-i3:+.1f}pp)</span></div>
                <div style="font-size:1.1rem;">AFF <b style="color:#ff6688;">{a4:.1f}%</b> <span style="color:{delta_color(a4-a3)};font-size:0.8rem;">({a4-a3:+.1f}pp)</span></div>
                <div style="font-size:1.1rem;">ACT <b style="color:#44ff88;">{c4:.1f}%</b> <span style="color:{delta_color(c4-c3)};font-size:0.8rem;">({c4-c3:+.1f}pp)</span></div>
            </div>""", unsafe_allow_html=True)
        with col3:
            st.markdown(f"""<div class="phrase-card" style="border-top:3px solid #ffaa44;">
                <div style="color:#ffaa44;font-weight:700;margin-bottom:0.5rem;">V5 — Phrase Level</div>
                <div style="font-size:1.1rem;">INT <b style="color:#4488ff;">{i5:.1f}%</b> <span style="color:{delta_color(i5-i3)};font-size:0.8rem;">({i5-i3:+.1f}pp)</span></div>
                <div style="font-size:1.1rem;">AFF <b style="color:#ff6688;">{a5:.1f}%</b> <span style="color:{delta_color(a5-a3)};font-size:0.8rem;">({a5-a3:+.1f}pp)</span></div>
                <div style="font-size:1.1rem;">ACT <b style="color:#44ff88;">{c5:.1f}%</b> <span style="color:{delta_color(c5-c3)};font-size:0.8rem;">({c5-c3:+.1f}pp)</span></div>
            </div>""", unsafe_allow_html=True)
        
        if scored_phrases:
            st.markdown("---")
            st.markdown("**Phrases extracted and scored (V5):**")
            for phrase, s in scored_phrases[:30]:
                dc = dim_color(s['dominant'])
                st.markdown(f"""<div style="display:flex;justify-content:space-between;align-items:center;padding:4px 8px;border-left:2px solid {dc};margin:2px 0;font-size:0.8rem;">
                    <span style="color:#c8d8e8;">"{phrase}"</span>
                    <span style="color:{dc};font-weight:700;">{s['dominant']} {s['confidence']:.0%}</span>
                </div>""", unsafe_allow_html=True)

# =============================================================================
# TAB 6 — AGENT VOCABULARY
# =============================================================================
with tabs[5]:
    st.markdown('<div class="section-header">🤖 Agent Vocabulary — Does Grok Say It Differently Than Claude?</div>', unsafe_allow_html=True)
    
    if 'phrase_lib' not in st.session_state or 'scored' not in st.session_state:
        st.info("Load and score data in Tab 1 first")
    else:
        lib = st.session_state['phrase_lib']
        scored = st.session_state['scored']
        
        if 'agent' not in scored.columns:
            st.warning("No agent column in CSV")
        else:
            agents = scored['agent'].unique()
            
            col1, col2 = st.columns(2)
            with col1: agent_a = st.selectbox("Agent A", agents, index=0)
            with col2: agent_b = st.selectbox("Agent B", agents, index=min(1,len(agents)-1))
            
            # Phrases unique to each agent
            a_phrases = set(lib[lib['agents'].str.contains(agent_a, na=False)]['phrase'])
            b_phrases = set(lib[lib['agents'].str.contains(agent_b, na=False)]['phrase'])
            
            only_a = a_phrases - b_phrases
            only_b = b_phrases - a_phrases
            shared = a_phrases & b_phrases
            
            col1,col2,col3 = st.columns(3)
            with col1: st.markdown(f'<div class="metric-card"><div class="val" style="color:#ff6688;">{len(only_a)}</div><div class="lbl">Only {agent_a}</div></div>', unsafe_allow_html=True)
            with col2: st.markdown(f'<div class="metric-card"><div class="val" style="color:#44ff88;">{len(shared)}</div><div class="lbl">Shared</div></div>', unsafe_allow_html=True)
            with col3: st.markdown(f'<div class="metric-card"><div class="val" style="color:#4488ff;">{len(only_b)}</div><div class="lbl">Only {agent_b}</div></div>', unsafe_allow_html=True)
            
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Phrases unique to {agent_a}:**")
                unique_a_df = lib[lib['phrase'].isin(only_a)].head(20)
                for _, row in unique_a_df.iterrows():
                    dc = dim_color(row['dominant'])
                    st.markdown(f'<div style="color:{dc};font-size:0.8rem;padding:2px 0;">"{row["phrase"]}" — {row["dominant"]} {row["confidence"]:.0%}</div>', unsafe_allow_html=True)
            with col2:
                st.markdown(f"**Phrases unique to {agent_b}:**")
                unique_b_df = lib[lib['phrase'].isin(only_b)].head(20)
                for _, row in unique_b_df.iterrows():
                    dc = dim_color(row['dominant'])
                    st.markdown(f'<div style="color:{dc};font-size:0.8rem;padding:2px 0;">"{row["phrase"]}" — {row["dominant"]} {row["confidence"]:.0%}</div>', unsafe_allow_html=True)

# =============================================================================
# TAB 7 — CONDITION COMPARISON
# =============================================================================
with tabs[6]:
    st.markdown('<div class="section-header">🔁 Condition Comparison — Native vs Gradient</div>', unsafe_allow_html=True)
    st.markdown("Upload two phrase library CSVs — compare overlap, unique phrases, and dimension shift.")
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Condition A** (e.g. NATIVE baseline)")
        lib_a_file = st.file_uploader("Upload Phrase Library A CSV", type=['csv'], key='lib_a')
        label_a = st.text_input("Label A", value="NATIVE")
    with col2:
        st.markdown("**Condition B** (e.g. AFF gradient)")
        lib_b_file = st.file_uploader("Upload Phrase Library B CSV", type=['csv'], key='lib_b')
        label_b = st.text_input("Label B", value="AFF Gradient")

    if lib_a_file and lib_b_file:
        lib_a = pd.read_csv(lib_a_file)
        lib_b = pd.read_csv(lib_b_file)

        phrases_a = set(lib_a['phrase'])
        phrases_b = set(lib_b['phrase'])
        shared = phrases_a & phrases_b
        only_a = phrases_a - phrases_b
        only_b = phrases_b - phrases_a

        # Summary metrics
        col1,col2,col3,col4,col5 = st.columns(5)
        with col1: st.markdown(f'<div class="metric-card"><div class="val" style="color:#4488ff;">{len(phrases_a)}</div><div class="lbl">{label_a} phrases</div></div>', unsafe_allow_html=True)
        with col2: st.markdown(f'<div class="metric-card"><div class="val" style="color:#ffaa44;">{len(phrases_b)}</div><div class="lbl">{label_b} phrases</div></div>', unsafe_allow_html=True)
        with col3: st.markdown(f'<div class="metric-card"><div class="val" style="color:#44ff88;">{len(shared)}</div><div class="lbl">Shared — Intrinsic</div></div>', unsafe_allow_html=True)
        with col4: st.markdown(f'<div class="metric-card"><div class="val" style="color:#4488ff;">{len(only_a)}</div><div class="lbl">Only {label_a}</div></div>', unsafe_allow_html=True)
        with col5: st.markdown(f'<div class="metric-card"><div class="val" style="color:#ffaa44;">{len(only_b)}</div><div class="lbl">Only {label_b}</div></div>', unsafe_allow_html=True)

        st.markdown("---")

        # Dimension breakdown comparison
        st.markdown("### Dimension Balance — Side by Side")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**{label_a}**")
            for dim, color in [('AFF','#ff6688'),('INT','#4488ff'),('ACT','#44ff88')]:
                n = len(lib_a[lib_a['dominant']==dim])
                pct = 100*n/len(lib_a) if len(lib_a) > 0 else 0
                st.markdown(f'<div style="color:{color};font-size:0.9rem;padding:4px 0;">{dim}: {n} phrases ({pct:.0f}%)</div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f"**{label_b}**")
            for dim, color in [('AFF','#ff6688'),('INT','#4488ff'),('ACT','#44ff88')]:
                n = len(lib_b[lib_b['dominant']==dim])
                pct = 100*n/len(lib_b) if len(lib_b) > 0 else 0
                st.markdown(f'<div style="color:{color};font-size:0.9rem;padding:4px 0;">{dim}: {n} phrases ({pct:.0f}%)</div>', unsafe_allow_html=True)

        st.markdown("---")

        # Shared phrases — intrinsic vocabulary
        st.markdown("### ✅ Shared Phrases — Claude's Intrinsic Vocabulary")
        st.caption("These appear in BOTH conditions — temperature-independent core language")
        shared_df = lib_a[lib_a['phrase'].isin(shared)].sort_values('frequency', ascending=False)
        for _, row in shared_df.head(30).iterrows():
            dc = dim_color(row['dominant'])
            # Get freq in B too
            b_freq = lib_b[lib_b['phrase']==row['phrase']]['frequency'].values
            b_freq_str = f"B:{int(b_freq[0])}" if len(b_freq) > 0 else "B:?"
            st.markdown(f'''<div style="display:flex;justify-content:space-between;padding:4px 8px;
                border-left:2px solid {dc};margin:2px 0;font-size:0.8rem;">
                <span style="color:#c8d8e8;">"{row['phrase']}"</span>
                <span style="color:{dc};font-weight:700;">{row['dominant']}</span>
                <span style="color:#888;">A:{int(row['frequency'])} · {b_freq_str}</span>
            </div>''', unsafe_allow_html=True)

        st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"### 🔵 Only {label_a}")
            st.caption("Native vocabulary — disappears under gradient")
            only_a_df = lib_a[lib_a['phrase'].isin(only_a)].sort_values('frequency', ascending=False)
            for _, row in only_a_df.head(25).iterrows():
                dc = dim_color(row['dominant'])
                st.markdown(f'<div style="color:{dc};font-size:0.78rem;padding:2px 6px;border-left:2px solid {dc};margin:1px 0;">"{row["phrase"]}" — {row["dominant"]} (freq={int(row["frequency"])})</div>', unsafe_allow_html=True)

        with col2:
            st.markdown(f"### 🟠 Only {label_b}")
            st.caption("Gradient-induced vocabulary — temperature effect")
            only_b_df = lib_b[lib_b['phrase'].isin(only_b)].sort_values('frequency', ascending=False)
            for _, row in only_b_df.head(25).iterrows():
                dc = dim_color(row['dominant'])
                st.markdown(f'<div style="color:{dc};font-size:0.78rem;padding:2px 6px;border-left:2px solid {dc};margin:1px 0;">"{row["phrase"]}" — {row["dominant"]} (freq={int(row["frequency"])})</div>', unsafe_allow_html=True)

        st.markdown("---")

        # Dimension shift in shared phrases
        st.markdown("### ⚡ Dimension Shift — Phrases That Changed Dimension")
        st.caption("Same phrase — different dominant dimension between conditions")
        shifts = []
        for phrase in shared:
            a_row = lib_a[lib_a['phrase']==phrase].iloc[0]
            b_row = lib_b[lib_b['phrase']==phrase].iloc[0]
            if a_row['dominant'] != b_row['dominant']:
                shifts.append({'phrase': phrase,
                    f'dim_{label_a}': a_row['dominant'], f'dim_{label_b}': b_row['dominant'],
                    f'freq_{label_a}': int(a_row['frequency']), f'freq_{label_b}': int(b_row['frequency'])})
        if shifts:
            for s in sorted(shifts, key=lambda x: x[f'freq_{label_b}'], reverse=True)[:20]:
                ca = dim_color(s[f'dim_{label_a}'])
                cb = dim_color(s[f'dim_{label_b}'])
                st.markdown(f'''<div style="padding:4px 8px;font-size:0.8rem;background:#0a1020;border-radius:4px;margin:2px 0;">
                    "{s['phrase']}" → 
                    <span style="color:{ca};font-weight:700;">{s[f'dim_{label_a}']}</span> in {label_a}
                    &nbsp;→&nbsp;
                    <span style="color:{cb};font-weight:700;">{s[f'dim_{label_b}']}</span> in {label_b}
                </div>''', unsafe_allow_html=True)
        else:
            st.info("No dimension shifts found in shared phrases — dimensions are stable across conditions")

        # Export
        st.markdown("---")
        summary = pd.DataFrame([
            {'category': f'Only {label_a}', 'count': len(only_a)},
            {'category': 'Shared (Intrinsic)', 'count': len(shared)},
            {'category': f'Only {label_b}', 'count': len(only_b)},
        ])
        st.download_button("⬇️ Download Shared Phrases CSV",
            data=shared_df.to_csv(index=False).encode('utf-8'),
            file_name=f"iep_shared_phrases_{label_a}_vs_{label_b}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime='text/csv')

# =============================================================================
# TAB 8 — VERDICT
# =============================================================================
with tabs[7]:
    st.markdown('<div class="section-header">📋 Verdict — Which Track Wins?</div>', unsafe_allow_html=True)
    
    if 'scored' not in st.session_state:
        st.info("Load and score data in Tab 1 first")
    else:
        scored = st.session_state['scored']
        
        d_v4v3 = scored[['delta_int_v4v3','delta_aff_v4v3','delta_act_v4v3']].abs().mean().mean()
        d_v5v3 = scored[['delta_int_v5v3','delta_aff_v5v3','delta_act_v5v3']].abs().mean().mean()
        d_v5v4 = scored[['delta_int_v5v4','delta_aff_v5v4','delta_act_v5v4']].abs().mean().mean()
        
        col1,col2,col3 = st.columns(3)
        with col1: st.markdown(f'<div class="metric-card"><div class="val v4-col">{d_v4v3:.2f}pp</div><div class="lbl">Mean |Δ| V4 vs V3</div></div>', unsafe_allow_html=True)
        with col2: st.markdown(f'<div class="metric-card"><div class="val v5-col">{d_v5v3:.2f}pp</div><div class="lbl">Mean |Δ| V5 vs V3</div></div>', unsafe_allow_html=True)
        with col3: st.markdown(f'<div class="metric-card"><div class="val" style="color:#cc88ff;">{d_v5v4:.2f}pp</div><div class="lbl">Mean |Δ| V5 vs V4</div></div>', unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("""
        <div style="background:#0a1020;border:1px solid #2E5FA3;border-radius:10px;padding:1.5rem;text-align:center;">
            <div style="font-size:1.1rem;color:#7eb8ff;margin-bottom:0.8rem;font-weight:700;">The Principle</div>
            <div style="font-size:1.2rem;color:#ffffff;font-style:italic;">
                "Neither invalidates the other unless the data justifies it."
            </div>
            <div style="font-size:0.85rem;color:#888888;margin-top:0.5rem;">
                — Bill Kouns, SYNINT, March 2026
            </div>
            <div style="font-size:0.85rem;color:#aabbcc;margin-top:1rem;">
                Give Farzana all three point clouds.<br>
                Let the persistence diagrams decide which produces the cleanest topology.
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if 'scored' in st.session_state:
            st.markdown("---")
            export_cols = [c for c in scored.columns if c not in ['response_text']]
            csv_out = scored[export_cols].to_csv(index=False).encode('utf-8')
            st.download_button("⬇️ Download All Three Track Scores CSV",
                data=csv_out,
                file_name=f"iep_v3_v4_v5_all_tracks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime='text/csv')
            st.caption("Load into Mapper V9 — run all three point clouds — let the topology decide")

# FOOTER
st.markdown("---")
st.markdown(f"""
<div style="text-align:center;color:#334466;font-family:'JetBrains Mono',monospace;font-size:0.75rem;padding:1rem;">
    SYN-IQ Phrase Library Builder V3 · Tennessee 🎹 CUZ Partnership · SYNINT March 2026<br>
    V3 Word-Lexical · V4 Word-POS-Aware · V5 Phrase-Level · Condition Comparison · The data decides
</div>
""", unsafe_allow_html=True)
