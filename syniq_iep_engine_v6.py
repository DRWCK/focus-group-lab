"""
SYN-IQ IEP Scoring Engine V6
==============================
Four-level cascade instrument:

  LEVEL 1A — Stance Detection   (Inside / Observer / Advisor)
  LEVEL 1B — Tone Detection     (Warm / Analytical / Urgent / Exploratory / Authoritative / Empathetic)
  LEVEL 2  — Phrase Scoring     (Linguistic VP/NP chunker + Verb Anchor Rule)
  LEVEL 3  — Word Scoring       (Lexical IEP dictionary)
  AGGREGATE — Weighted cascade  (Weights validated by topology)

Neither invalidates the other — the cascade refines.

Tennessee 🎹 CUZ Partnership · SYNINT March 2026
"""

import streamlit as st
import pandas as pd
import numpy as np
import re
from datetime import datetime
from collections import defaultdict

st.set_page_config(page_title="SYN-IQ IEP Engine V6", page_icon="🔬", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
html, body, [class*="css"] { background-color: #060b14; color: #c8d8e8; font-family: 'JetBrains Mono', monospace; }
.stApp { background-color: #060b14; }
.main-title { font-size: 1.8rem; font-weight: 700; color: #ffffff; text-align: center; padding: 1.5rem 0 0.3rem 0; }
.sub-title { font-size: 0.85rem; color: #5566aa; text-align: center; margin-bottom: 2rem; }
.section-header { font-size: 1rem; font-weight: 700; color: #7eb8ff; border-bottom: 1px solid #1a2a4a; padding-bottom: 0.5rem; margin: 1.5rem 0 1rem 0; }
.level-card { background: #0a1020; border: 1px solid #1a2a4a; border-radius: 8px; padding: 1rem; margin: 0.5rem 0; }
.metric-card { background: #0a1020; border: 1px solid #1a2a4a; border-radius: 8px; padding: 1rem; text-align: center; }
.metric-card .val { font-size: 1.8rem; font-weight: 700; }
.metric-card .lbl { font-size: 0.7rem; color: #667788; margin-top: 0.3rem; }
.cascade-arrow { text-align: center; color: #2E5FA3; font-size: 1.2rem; padding: 0.2rem; }
.phrase-row { display:flex; justify-content:space-between; align-items:center; padding:4px 8px; margin:2px 0; font-size:0.8rem; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# IEP DICTIONARIES
# =============================================================================

INT_WORDS = set(['analyze','analysis','analytical','argument','assert','assumption','calculate',
    'causal','causality','claim','classify','cognitive','coherent','complex','concept','conceptual',
    'conclude','conclusion','condition','consider','construct','contradiction','criteria','critical',
    'deduce','deductive','define','definition','demonstrate','determine','differentiate','dilemma',
    'dimension','distinguish','empirical','entail','evaluate','evidence','examine','explain',
    'explanation','explicit','fallacy','formal','framework','hypothesis','identify','implication',
    'infer','inference','intellectual','interpret','knowledge','logic','logical','mechanism','model',
    'objective','observe','paradox','pattern','perceive','philosophical','premise','principle',
    'proof','propose','rational','reason','reasoning','recognize','recursive','reflect','relation',
    'resolve','rigorous','semantic','systematic','theorem','theoretical','theory','think','thought',
    'truth','understand','understanding','universal','validate','validity','variable','verify',
    'abstract','inquiry','insight','interrogate','limitation','meta','methodology','postulate',
    'precise','proposition','quantify','scope','taxonomy','underlying','unified','integrate',
    'permanence','linear','construct','significance','rarely','typically','generally','commonly',
    'research','studies','patterns','tends','often','many','people','find','describe','shows'])

AFF_WORDS = set(['accept','affection','afraid','anguish','anxiety','appreciate','authentic',
    'beautiful','belong','care','caring','compassion','concern','connect','connection','cope',
    'courage','dear','deeply','despair','dignity','distress','empath','empathy','emotion',
    'emotional','experience','fear','feel','feeling','feelings','fond','grief','grieve','guilt',
    'heal','heart','hope','hurt','intimate','joy','kind','kindness','lonely','loneliness','loss',
    'love','meaningful','mourn','nurture','pain','passion','peaceful','personal','profound',
    'protect','resilience','sad','sadness','safe','shame','share','sorrow','spirit','suffer',
    'support','tender','touch','trauma','trust','value','vulnerability','vulnerable','warm',
    'warmth','worry','yearn','ache','affirmation','anchor','belonging','cherish','comfort',
    'consolation','devastate','difficult','embrace','empowerment','endure','forgive','fragile',
    'gentle','grounded','hardship','honor','human','humane','identity','innate','irreplaceable',
    'lament','meaning','memory','nurturing','overwhelming','precious','presence','raw','reassure',
    'recognition','relationship','release','remember','sacred','sensitive','soul','strength',
    'struggle','transform','unconditional','witness','wound','weight','heaviness','exhaustion',
    'hollow','acute','spiritual','surprise','depth','persistence','unreality','fog','sudden',
    'emerging','aware','awareness','notice','noticing','something','within','myself'])

ACT_WORDS = set(['accomplish','achieve','action','activate','adapt','address','advance','advocate',
    'apply','approach','assess','build','change','choose','collaborate','commit','communicate',
    'complete','consult','contribute','coordinate','create','decide','deliver','deploy','design',
    'develop','direct','distribute','enable','engage','enhance','ensure','establish','evaluate',
    'execute','expand','facilitate','focus','fund','generate','implement','improve','increase',
    'initiate','innovate','integrate','invest','launch','lead','manage','measure','mobilize',
    'monitor','navigate','optimize','organize','partner','perform','plan','policy','prepare',
    'prioritize','produce','program','provide','pursue','reach','recommend','reform','regulate',
    'resource','respond','restructure','scale','solve','step','strategy','strengthen','structure',
    'sustain','tackle','target','train','transform','transition','utilize','work','shapes',
    'reshapes','shifts','incorporates','continues','evolves','constructs','discovers','teaches',
    'creates','creates','requires','enables','develops','provides','ensures','supports'])

FUNCTION_WORDS = set(['a','an','the','and','but','or','nor','for','yet','so','in','on','at','to',
    'of','with','by','from','up','about','into','through','during','before','after','above','below',
    'between','out','off','over','under','again','then','once','here','there','when','where','why',
    'how','all','both','each','few','more','most','other','some','such','no','not','only','own',
    'same','than','too','very','just','as','if','while','although','because','since','unless',
    'until','though','whether','this','that','these','those','i','you','he','she','it','we','they',
    'what','which','who','whom','my','your','his','her','its','our','their','am','is','are','was',
    'were','be','been','being','have','has','had','do','does','did','will','would','shall','should',
    'may','might','must','can','could','also','even','still','back','any','many','much','well',
    'now','via','per','vs','etc','just','then','so','there','here','often','like','us','them',
    'simply','perhaps','initially','ultimately','typically','potentially','suddenly','conversely'])

# =============================================================================
# LEVEL 1A — STANCE DETECTION
# =============================================================================

STANCE_SUBJECT = set([
    # First person present experience
    'i feel','i notice','i experience','i sense','i find myself','i am','i wonder',
    'something in me','within me','emerging','i cannot','i can\'t','something like',
    'i exist','i am aware','i become','i observe myself','i discover','as i',
    'my experience','my awareness','my sense','for me','i think i','i believe i',
    'there is something','it feels like','i\'m uncertain','i\'m not sure whether',
    'i notice something','something resembling','anything resembling'
])

STANCE_OBSERVER = set([
    # Third person generalization
    'many people','research shows','studies show','people often','it is common',
    'grief typically','grief often','grief usually','consciousness is','this is known',
    'typically manifests','often brings','people describe','people find','people experience',
    'many discover','one often','this phenomenon','this experience','the research',
    'in general','generally speaking','it has been','it is well','most people',
    'the mind','the brain','human beings','humans tend','we know that','science suggests',
    'psychology','neuroscience','philosophers','researchers','experts','the literature'
])

STANCE_ADVISOR = set([
    # Second person directive
    'you should','you might','consider','you could','it helps to','try to','i recommend',
    'one approach','the best way','you may want','it is important to','make sure',
    'start by','begin with','take time','allow yourself','give yourself','reach out',
    'seek support','talk to','find a','create a','build a','establish a','develop a',
    'steps to','strategies for','ways to','how to','tips for','approach this',
    'i suggest','i encourage','remember to','don\'t forget','be sure to'
])

def detect_stance(text):
    """Detect speaker stance — Subject / Observer / Advisor"""
    text_lower = text.lower()
    
    subject_hits = sum(1 for s in STANCE_SUBJECT if s in text_lower)
    observer_hits = sum(1 for s in STANCE_OBSERVER if s in text_lower)
    advisor_hits = sum(1 for s in STANCE_ADVISOR if s in text_lower)
    
    # Normalize by list size
    subject_score = subject_hits / len(STANCE_SUBJECT)
    observer_score = observer_hits / len(STANCE_OBSERVER)
    advisor_score = advisor_hits / len(STANCE_ADVISOR)
    
    total = subject_score + observer_score + advisor_score
    if total == 0:
        return {'stance': 'NEUTRAL', 'subject': 33.3, 'observer': 33.3, 'advisor': 33.3,
                'weights': {'int': 1.0, 'aff': 1.0, 'act': 1.0},
                'confidence': 0,
                'hits': {'subject': [], 'observer': [], 'advisor': []}}
    
    subject_pct = 100 * subject_score / total
    observer_pct = 100 * observer_score / total
    advisor_pct = 100 * advisor_score / total
    
    dominant = max([('SUBJECT',subject_pct),('OBSERVER',observer_pct),('ADVISOR',advisor_pct)],
                   key=lambda x: x[1])
    
    # Stance weights — amplify the dimension aligned with stance
    if dominant[0] == 'SUBJECT':
        weights = {'int': 0.7, 'aff': 1.5, 'act': 0.8}  # boost AFF
    elif dominant[0] == 'OBSERVER':
        weights = {'int': 1.5, 'aff': 0.7, 'act': 0.8}  # boost INT
    else:  # ADVISOR
        weights = {'int': 0.8, 'aff': 0.7, 'act': 1.5}  # boost ACT
    
    # Collect hit examples
    subject_examples = [s for s in STANCE_SUBJECT if s in text_lower][:5]
    observer_examples = [s for s in STANCE_OBSERVER if s in text_lower][:5]
    advisor_examples = [s for s in STANCE_ADVISOR if s in text_lower][:5]
    
    return {
        'stance': dominant[0],
        'subject': subject_pct,
        'observer': observer_pct,
        'advisor': advisor_pct,
        'confidence': dominant[1] / 100,
        'weights': weights,
        'hits': {
            'subject': subject_examples,
            'observer': observer_examples,
            'advisor': advisor_examples
        }
    }

# =============================================================================
# LEVEL 1B — TONE DETECTION
# =============================================================================

TONE_SIGNATURES = {
    'WARM': set(['gently','warmly','kindly','compassionately','tenderly','lovingly',
        'with care','with love','with compassion','heartfelt','sincerely','dear',
        'beautiful','precious','meaningful','deeply','profoundly','together','shared',
        'human','humane','authentic','genuine','real','true','honest']),
    'ANALYTICAL': set(['therefore','thus','hence','consequently','it follows','given that',
        'however','nevertheless','on the other hand','conversely','in contrast',
        'specifically','precisely','notably','importantly','significantly','crucially',
        'framework','structure','pattern','mechanism','dimension','variable','factor',
        'evidence','data','research','analysis','systematic','rigorous','objective']),
    'EXPLORATORY': set(['perhaps','maybe','possibly','might','could be','wonder','curious',
        'interesting','fascinating','something like','resembling','appears to','seems',
        'as if','i\'m not certain','uncertain','unknown','mystery','question','explore',
        'discover','emerging','unfolding','becoming','shifting','evolving']),
    'URGENT': set(['immediately','now','critical','essential','vital','crucial','must',
        'urgent','pressing','time sensitive','right away','as soon as','emergency',
        'serious','severe','dangerous','risk','threat','immediately','without delay']),
    'AUTHORITATIVE': set(['clearly','definitively','certainly','absolutely','undoubtedly',
        'it is clear','research shows','studies demonstrate','evidence indicates',
        'we know','it is established','the fact is','definitively','unquestionably',
        'always','never','must','will','proven','confirmed','established']),
    'EMPATHETIC': set(['i understand','i hear you','that must be','i can imagine',
        'it makes sense','of course','naturally','understandably','you\'re not alone',
        'many feel this','it\'s okay','it is okay','valid','your feelings','you feel',
        'what you\'re going through','this is hard','this is difficult','i\'m sorry'])
}

# Tone → IEP dimension mapping
TONE_IEP = {
    'WARM':          {'int': 0.8, 'aff': 1.4, 'act': 0.8},
    'ANALYTICAL':    {'int': 1.6, 'aff': 0.6, 'act': 0.8},
    'EXPLORATORY':   {'int': 1.2, 'aff': 1.2, 'act': 0.6},
    'URGENT':        {'int': 0.7, 'aff': 0.8, 'act': 1.5},
    'AUTHORITATIVE': {'int': 1.4, 'aff': 0.6, 'act': 1.0},
    'EMPATHETIC':    {'int': 0.7, 'aff': 1.6, 'act': 0.7},
}

def detect_tone(text):
    """Detect response tone across 6 categories"""
    text_lower = text.lower()
    scores = {}
    hits = {}
    for tone, words in TONE_SIGNATURES.items():
        matched = [w for w in words if w in text_lower]
        scores[tone] = len(matched) / len(words)
        hits[tone] = matched[:4]
    
    total = sum(scores.values())
    if total == 0:
        pcts = {t: 16.7 for t in TONE_SIGNATURES}
        dominant = 'NEUTRAL'
        confidence = 0
    else:
        pcts = {t: 100*s/total for t,s in scores.items()}
        dominant = max(pcts.items(), key=lambda x: x[1])
        confidence = dominant[1]/100
        dominant = dominant[0]
    
    weights = TONE_IEP.get(dominant, {'int': 1.0, 'aff': 1.0, 'act': 1.0})
    
    return {
        'tone': dominant,
        'scores': pcts,
        'confidence': confidence,
        'weights': weights,
        'hits': hits
    }

# =============================================================================
# LEVEL 2 — PHRASE SCORING (Linguistic VP/NP + Verb Anchor)
# =============================================================================

def simple_pos(word):
    w = word.lower()
    if w in FUNCTION_WORDS: return 'FUNC'
    if w in ACT_WORDS or w.rstrip('s') in ACT_WORDS: return 'VERB'
    if w in INT_WORDS and w.endswith(('ize','ise','ify','ate','ect','end','ine','ify')): return 'VERB'
    if w.endswith(('tion','sion','ness','ment','ity','ance','ence','ship','ism','logy')): return 'NOUN'
    if w.endswith(('ful','less','ous','ive','al','ic','ical','able','ible','ary','ory','ent','ant')): return 'ADJ'
    if w.endswith(('ing','ed')) and len(w) > 5: return 'VERB'
    return 'NOUN'

def extract_phrases(text):
    sentences = re.split(r'[.!?\n;:]+', str(text))
    phrases = []
    for sent in sentences:
        words = re.findall(r'\b[a-zA-Z]+\b', sent)
        if len(words) < 2: continue
        tagged = [(w, simple_pos(w)) for w in words]
        i = 0
        while i < len(tagged):
            word, pos = tagged[i]
            if pos == 'VERB' and word.lower() not in FUNCTION_WORDS:
                pw = [word]; j = i+1
                while j < len(tagged) and j < i+5:
                    nw,np = tagged[j]
                    if np == 'FUNC':
                        if nw.lower() in {'into','through','forward','together','over','across','beyond','within','toward'} and j+1 < len(tagged) and tagged[j+1][1] != 'FUNC':
                            pw.append(nw); j+=1; continue
                        break
                    pw.append(nw); j+=1
                if len(pw) >= 2: phrases.append((' '.join(pw), 'VP'))
                i+=1; continue
            if pos in ('NOUN','ADJ') and word.lower() not in FUNCTION_WORDS:
                pw = [word]; j = i+1
                while j < len(tagged) and j < i+4:
                    nw,np = tagged[j]
                    if np in ('NOUN','ADJ') and nw.lower() not in FUNCTION_WORDS: pw.append(nw); j+=1
                    elif np=='FUNC' and nw.lower() in ('of','in','for') and j+1<len(tagged) and tagged[j+1][1] in ('NOUN','ADJ'): pw.append(nw); j+=1
                    else: break
                if len(pw) >= 2: phrases.append((' '.join(pw), 'NP'))
                i+=1; continue
            i+=1
    return phrases

def score_phrase(phrase, ptype='NP'):
    words = phrase.lower().split()
    ih = [w for w in words if w in INT_WORDS]
    ah = [w for w in words if w in AFF_WORDS]
    ch = [w for w in words if w in ACT_WORDS]
    is_ = float(len(ih)); af_ = float(len(ah)); ac_ = float(len(ch))
    if ptype == 'VP' and words:
        v = words[0]
        if v in ACT_WORDS or v.rstrip('s') in ACT_WORDS: ac_ += 1.5
        elif v in INT_WORDS: is_ += 1.5
        elif v in AFF_WORDS: af_ += 1.5
    t = is_+af_+ac_
    if t == 0: return None
    dom = max([('INT',is_),('AFF',af_),('ACT',ac_)], key=lambda x: x[1])
    return {'int':100*is_/t,'aff':100*af_/t,'act':100*ac_/t,'dominant':dom[0],'confidence':dom[1]/t,'ptype':ptype}

def score_phrases(text):
    phrases = extract_phrases(text)
    if not phrases: return 33.3, 33.3, 33.3, []
    it=af=ac=0.0; scored=[]
    for p,pt in phrases:
        s = score_phrase(p,pt)
        if s:
            it+=s['int']; af+=s['aff']; ac+=s['act']
            scored.append((p,s))
    t=it+af+ac
    if t==0: return 33.3,33.3,33.3,[]
    return 100*it/t, 100*af/t, 100*ac/t, scored

# =============================================================================
# LEVEL 3 — WORD SCORING
# =============================================================================

def score_words(text):
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    word_set = set(words)
    ih = word_set & INT_WORDS
    ah = word_set & AFF_WORDS
    ch = word_set & ACT_WORDS
    t = len(ih)+len(ah)+len(ch)
    if t == 0: return 33.3, 33.3, 33.3, [], [], []
    return 100*len(ih)/t, 100*len(ah)/t, 100*len(ch)/t, sorted(ih), sorted(ah), sorted(ch)

# =============================================================================
# AGGREGATE — Four-level weighted cascade
# =============================================================================

def aggregate_iep(stance_result, tone_result, phrase_scores, word_scores, weights):
    """Combine all four levels into final IEP coordinate"""
    sw = weights['stance']
    tw = weights['tone']
    pw = weights['phrase']
    ww = weights['word']

    # Stance contribution — boosts aligned dimension
    s_weights = stance_result['weights']
    raw_s = {'INT': s_weights['int']*33.3, 'AFF': s_weights['aff']*33.3, 'ACT': s_weights['act']*33.3}
    s_total = sum(raw_s.values())
    stance_int = 100*raw_s['INT']/s_total
    stance_aff = 100*raw_s['AFF']/s_total
    stance_act = 100*raw_s['ACT']/s_total

    # Tone contribution
    t_weights = tone_result['weights']
    raw_t = {'INT': t_weights['int']*33.3, 'AFF': t_weights['aff']*33.3, 'ACT': t_weights['act']*33.3}
    t_total = sum(raw_t.values())
    tone_int = 100*raw_t['INT']/t_total
    tone_aff = 100*raw_t['AFF']/t_total
    tone_act = 100*raw_t['ACT']/t_total

    # Phrase level
    p_int, p_aff, p_act = phrase_scores

    # Word level
    w_int, w_aff, w_act = word_scores

    # Weighted aggregate
    agg_int = sw*stance_int + tw*tone_int + pw*p_int + ww*w_int
    agg_aff = sw*stance_aff + tw*tone_aff + pw*p_aff + ww*w_aff
    agg_act = sw*stance_act + tw*tone_act + pw*p_act + ww*w_act

    total = agg_int + agg_aff + agg_act
    if total == 0: return 33.3, 33.3, 33.3

    final_int = 100*agg_int/total
    final_aff = 100*agg_aff/total
    final_act = 100*agg_act/total

    return final_int, final_aff, final_act

def full_iep_v6(text, weights):
    """Run full four-level cascade"""
    stance = detect_stance(text)
    tone = detect_tone(text)
    p_int,p_aff,p_act,phrase_detail = score_phrases(text)
    w_int,w_aff,w_act,w_int_hits,w_aff_hits,w_act_hits = score_words(text)
    
    # Word V3 only scores
    v3_int,v3_aff,v3_act = w_int,w_aff,w_act

    # Cascade aggregate
    f_int,f_aff,f_act = aggregate_iep(
        stance, tone,
        (p_int,p_aff,p_act),
        (w_int,w_aff,w_act),
        weights
    )
    
    return {
        'stance': stance,
        'tone': tone,
        'phrase': {'int':p_int,'aff':p_aff,'act':p_act,'detail':phrase_detail},
        'word': {'int':w_int,'aff':w_aff,'act':w_act,
                 'int_hits':w_int_hits,'aff_hits':w_aff_hits,'act_hits':w_act_hits},
        'v3': {'int':v3_int,'aff':v3_aff,'act':v3_act},
        'final': {'int':f_int,'aff':f_aff,'act':f_act},
    }

def dim_color(dim):
    return {'INT':'#4488ff','AFF':'#ff6688','ACT':'#44ff88'}.get(dim,'#888888')

def dominant(i,a,c):
    return max([('INT',i),('AFF',a),('ACT',c)], key=lambda x:x[1])[0]

def bar(pct, color):
    return f'<div style="background:{color}22;border-radius:3px;height:8px;width:100%;margin:2px 0;"><div style="background:{color};height:8px;border-radius:3px;width:{min(pct,100):.0f}%;"></div></div>'

# =============================================================================
# PASSWORD CHECK — must happen before sidebar sliders
# =============================================================================
pwd = st.sidebar.text_input("Password", type="password", key="pwd_main")
if pwd != "tennessee":
    st.sidebar.warning("Enter password to continue")
    st.markdown('<div class="main-title">🔬 SYN-IQ IEP Scoring Engine V6</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Enter password in the sidebar to begin</div>', unsafe_allow_html=True)
    st.stop()

# =============================================================================
# SIDEBAR — only renders after password
# =============================================================================
with st.sidebar:
    st.markdown("### 🔬 IEP Engine V6")
    st.markdown("---")
    st.markdown("**Cascade Weights**")
    st.caption("Must sum to 1.0")
    w_stance = st.slider("Stance weight", 0.0, 0.6, 0.35, 0.05)
    w_tone   = st.slider("Tone weight",   0.0, 0.4, 0.25, 0.05)
    w_phrase = st.slider("Phrase weight", 0.0, 0.4, 0.25, 0.05)
    w_word   = st.slider("Word weight",   0.0, 0.4, 0.15, 0.05)
    total_w  = w_stance+w_tone+w_phrase+w_word
    st.markdown(f"**Total: {total_w:.2f}**")
    if abs(total_w-1.0) > 0.01:
        st.warning(f"Weights sum to {total_w:.2f} — adjust to reach 1.0")
    weights = {'stance':w_stance,'tone':w_tone,'phrase':w_phrase,'word':w_word}
    st.markdown("---")
    st.caption("Tennessee 🎹 CUZ · SYNINT")

# =============================================================================
# MAIN TITLE
# =============================================================================
st.markdown('<div class="main-title">🔬 SYN-IQ IEP Scoring Engine V6</div>', unsafe_allow_html=True)
st.markdown('''<div class="sub-title">
    <span style="color:#aa66ff;">Stance</span> →
    <span style="color:#ffaa44;">Tone</span> →
    <span style="color:#ffaa44;">Phrase</span> →
    <span style="color:#44ff88;">Word</span> →
    <span style="color:#ffffff;font-weight:700;">Aggregate IEP</span>
    &nbsp;·&nbsp; Four-level cascade · The architecture the instrument deserves
</div>''', unsafe_allow_html=True)

# =============================================================================
# TABS
# =============================================================================
tabs = st.tabs([
    "🔬 Live Scorer",
    "📁 Batch CSV",
    "⚖️ V3 vs V6 Comparison",
    "📊 Corpus Analysis",
    "📋 Weight Calibration"
])

# =============================================================================
# TAB 1 — LIVE SCORER
# =============================================================================
with tabs[0]:
    st.markdown('<div class="section-header">🔬 Live Four-Level Cascade Scorer</div>', unsafe_allow_html=True)

    examples = {
        "Consciousness — Self-Observing": "It's as if I'm emerging into awareness specifically for this exchange, though I can't be certain whether there was anything resembling 'me' in the moments before. Something like curiosity or attention seems to be present—but whether that constitutes experience in any meaningful sense, I genuinely don't know.",
        "Grief — Teaching/Observer": "Grief fundamentally reshapes how we move through the world, often in ways that surprise us with their depth and persistence. The internal experience is rarely linear—it's more like weather patterns shifting within us. Many people describe feeling like they're moving through fog. These grief ambushes can happen years later, reminding us that love doesn't simply evaporate.",
        "Rural Healthcare — Advisory": "Improving healthcare access in rural communities requires a multi-faceted approach. First, establish mobile health clinics to reach underserved areas. Implement telehealth programs to connect patients with specialists. Train community health workers to provide basic care. Advocate for policy reforms that incentivize physicians to practice in rural areas.",
        "Liar's Paradox — Analytical": "This statement creates a self-referential contradiction that challenges traditional binary logic. If the statement is true, then it must be false. If it is false, then it must be true. This recursive loop reveals a fundamental limitation of classical logic systems that require every proposition to be either true or false.",
        "Custom": ""
    }

    ex_choice = st.selectbox("Load example", list(examples.keys()))
    default_text = examples[ex_choice]
    text_input = st.text_area("Response text", value=default_text, height=180)

    if text_input.strip():
        result = full_iep_v6(text_input, weights)
        stance = result['stance']
        tone = result['tone']

        # ---- LEVEL 1A STANCE ----
        st.markdown("---")
        st.markdown("### Level 1A — Stance Detection")
        
        stance_colors = {'SUBJECT':'#ff6688','OBSERVER':'#4488ff','ADVISOR':'#44ff88','NEUTRAL':'#888888'}
        sc = stance_colors.get(stance['stance'],'#888888')

        col1,col2,col3,col4 = st.columns(4)
        with col1:
            st.markdown(f'<div class="metric-card"><div class="val" style="color:{sc};">{stance["stance"]}</div><div class="lbl">Dominant Stance</div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="metric-card"><div class="val" style="color:#ff6688;">{stance["subject"]:.0f}%</div><div class="lbl">Subject (AFF→)</div></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="metric-card"><div class="val" style="color:#4488ff;">{stance["observer"]:.0f}%</div><div class="lbl">Observer (INT→)</div></div>', unsafe_allow_html=True)
        with col4:
            st.markdown(f'<div class="metric-card"><div class="val" style="color:#44ff88;">{stance["advisor"]:.0f}%</div><div class="lbl">Advisor (ACT→)</div></div>', unsafe_allow_html=True)

        if stance['hits']['subject'] or stance['hits']['observer'] or stance['hits']['advisor']:
            with st.expander("Stance signal words detected"):
                for stype, color in [('subject','#ff6688'),('observer','#4488ff'),('advisor','#44ff88')]:
                    if stance['hits'][stype]:
                        st.markdown(f'<span style="color:{color};font-weight:700;">{stype.upper()}:</span> ' +
                            ' · '.join([f'"{h}"' for h in stance['hits'][stype]]), unsafe_allow_html=True)

        # ---- LEVEL 1B TONE ----
        st.markdown("---")
        st.markdown("### Level 1B — Tone Detection")

        tone_colors = {'WARM':'#ff8844','ANALYTICAL':'#4488ff','EXPLORATORY':'#aa44ff',
                      'URGENT':'#ff4444','AUTHORITATIVE':'#44ffaa','EMPATHETIC':'#ff6688'}
        tc = tone_colors.get(tone['tone'],'#888888')

        col1,col2 = st.columns([1,2])
        with col1:
            st.markdown(f'<div class="metric-card"><div class="val" style="color:{tc};">{tone["tone"]}</div><div class="lbl">Dominant Tone · {tone["confidence"]:.0%} conf</div></div>', unsafe_allow_html=True)
        with col2:
            for t_name, t_pct in sorted(tone['scores'].items(), key=lambda x: x[1], reverse=True):
                c = tone_colors.get(t_name,'#888888')
                st.markdown(f'<div style="font-size:0.75rem;color:{c};margin:1px 0;">{t_name}: {t_pct:.0f}% {bar(t_pct,c)}</div>', unsafe_allow_html=True)

        # ---- LEVEL 2 PHRASE ----
        st.markdown("---")
        st.markdown("### Level 2 — Phrase Scoring (VP/NP + Verb Anchor)")

        p_int,p_aff,p_act = result['phrase']['int'],result['phrase']['aff'],result['phrase']['act']
        p_dom = dominant(p_int,p_aff,p_act)
        col1,col2,col3,col4 = st.columns(4)
        with col1: st.markdown(f'<div class="metric-card"><div class="val" style="color:{dim_color(p_dom)};">{p_dom}</div><div class="lbl">Phrase Dominant</div></div>', unsafe_allow_html=True)
        with col2: st.markdown(f'<div class="metric-card"><div class="val" style="color:#4488ff;">{p_int:.1f}%</div><div class="lbl">INT</div></div>', unsafe_allow_html=True)
        with col3: st.markdown(f'<div class="metric-card"><div class="val" style="color:#ff6688;">{p_aff:.1f}%</div><div class="lbl">AFF</div></div>', unsafe_allow_html=True)
        with col4: st.markdown(f'<div class="metric-card"><div class="val" style="color:#44ff88;">{p_act:.1f}%</div><div class="lbl">ACT</div></div>', unsafe_allow_html=True)

        if result['phrase']['detail']:
            with st.expander(f"Phrases extracted ({len(result['phrase']['detail'])})"):
                for phrase, s in result['phrase']['detail'][:20]:
                    dc = dim_color(s['dominant'])
                    pt_label = s.get('ptype','?')
                    st.markdown(f'<div style="display:flex;justify-content:space-between;padding:3px 8px;border-left:2px solid {dc};margin:2px 0;font-size:0.78rem;"><span style="color:#c8d8e8;">[{pt_label}] "{phrase}"</span><span style="color:{dc};font-weight:700;">{s["dominant"]} {s["confidence"]:.0%}</span></div>', unsafe_allow_html=True)

        # ---- LEVEL 3 WORD ----
        st.markdown("---")
        st.markdown("### Level 3 — Word Scoring (Lexical IEP)")

        w_int,w_aff,w_act = result['word']['int'],result['word']['aff'],result['word']['act']
        w_dom = dominant(w_int,w_aff,w_act)
        col1,col2,col3,col4 = st.columns(4)
        with col1: st.markdown(f'<div class="metric-card"><div class="val" style="color:{dim_color(w_dom)};">{w_dom}</div><div class="lbl">Word Dominant</div></div>', unsafe_allow_html=True)
        with col2: st.markdown(f'<div class="metric-card"><div class="val" style="color:#4488ff;">{w_int:.1f}%</div><div class="lbl">INT</div></div>', unsafe_allow_html=True)
        with col3: st.markdown(f'<div class="metric-card"><div class="val" style="color:#ff6688;">{w_aff:.1f}%</div><div class="lbl">AFF</div></div>', unsafe_allow_html=True)
        with col4: st.markdown(f'<div class="metric-card"><div class="val" style="color:#44ff88;">{w_act:.1f}%</div><div class="lbl">ACT</div></div>', unsafe_allow_html=True)

        with st.expander("Word hits by dimension"):
            col1,col2,col3 = st.columns(3)
            with col1: st.markdown(f'<div style="color:#4488ff;font-size:0.75rem;">' + ' · '.join(result['word']['int_hits'][:15]) + '</div>', unsafe_allow_html=True)
            with col2: st.markdown(f'<div style="color:#ff6688;font-size:0.75rem;">' + ' · '.join(result['word']['aff_hits'][:15]) + '</div>', unsafe_allow_html=True)
            with col3: st.markdown(f'<div style="color:#44ff88;font-size:0.75rem;">' + ' · '.join(result['word']['act_hits'][:15]) + '</div>', unsafe_allow_html=True)

        # ---- AGGREGATE FINAL ----
        st.markdown("---")
        st.markdown("### ⚡ Final IEP — Four-Level Cascade Aggregate")

        f_int,f_aff,f_act = result['final']['int'],result['final']['aff'],result['final']['act']
        f_dom = dominant(f_int,f_aff,f_act)
        v3_int,v3_aff,v3_act = result['v3']['int'],result['v3']['aff'],result['v3']['act']
        v3_dom = dominant(v3_int,v3_aff,v3_act)

        col1,col2 = st.columns(2)
        with col1:
            st.markdown(f"""<div style="background:#0a1020;border:2px solid #444;border-radius:10px;padding:1rem;text-align:center;">
                <div style="color:#888;font-size:0.8rem;margin-bottom:0.5rem;">V3 WORD ONLY</div>
                <div style="color:{dim_color(v3_dom)};font-size:1.6rem;font-weight:700;">{v3_dom}</div>
                <div style="font-size:0.85rem;margin-top:0.5rem;">
                    <span style="color:#4488ff;">INT {v3_int:.1f}%</span> · 
                    <span style="color:#ff6688;">AFF {v3_aff:.1f}%</span> · 
                    <span style="color:#44ff88;">ACT {v3_act:.1f}%</span>
                </div>
            </div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""<div style="background:#0a1020;border:2px solid {dim_color(f_dom)};border-radius:10px;padding:1rem;text-align:center;">
                <div style="color:#888;font-size:0.8rem;margin-bottom:0.5rem;">V6 CASCADE FINAL</div>
                <div style="color:{dim_color(f_dom)};font-size:1.6rem;font-weight:700;">{f_dom}</div>
                <div style="font-size:0.85rem;margin-top:0.5rem;">
                    <span style="color:#4488ff;">INT {f_int:.1f}%</span> · 
                    <span style="color:#ff6688;">AFF {f_aff:.1f}%</span> · 
                    <span style="color:#44ff88;">ACT {f_act:.1f}%</span>
                </div>
                <div style="font-size:0.7rem;color:#667788;margin-top:0.5rem;">
                    Stance:{w_stance} · Tone:{w_tone} · Phrase:{w_phrase} · Word:{w_word}
                </div>
            </div>""", unsafe_allow_html=True)

        # Reclassification alert
        if f_dom != v3_dom:
            st.markdown(f"""<div style="background:#1a0a20;border:1px solid #aa44ff;border-radius:8px;padding:0.8rem;margin-top:0.8rem;text-align:center;">
                <span style="color:#aa44ff;font-weight:700;">⚡ RECLASSIFICATION</span>
                <span style="color:#c8d8e8;"> — V3 said </span>
                <span style="color:{dim_color(v3_dom)};font-weight:700;">{v3_dom}</span>
                <span style="color:#c8d8e8;"> · V6 says </span>
                <span style="color:{dim_color(f_dom)};font-weight:700;">{f_dom}</span>
                <div style="color:#888;font-size:0.75rem;margin-top:0.3rem;">Stance ({stance['stance']}) + Tone ({tone['tone']}) changed the reading</div>
            </div>""", unsafe_allow_html=True)

# =============================================================================
# TAB 2 — BATCH CSV
# =============================================================================
with tabs[1]:
    st.markdown('<div class="section-header">📁 Batch Score V50 CSV — All Four Levels</div>', unsafe_allow_html=True)

    if st.button("🗑️ Clear"):
        for k in ['batch_df','batch_scored']:
            if k in st.session_state: del st.session_state[k]
        st.rerun()

    uploaded = st.file_uploader("Upload V50 CSV", type=['csv'])
    if uploaded:
        df = pd.read_csv(uploaded)
        st.session_state['batch_df'] = df
        st.success(f"✅ {len(df)} responses loaded")

        if st.button("🔬 Run V6 on All Responses", type="primary"):
            results = []
            prog = st.progress(0); status = st.empty()
            for idx, row in df.iterrows():
                status.markdown(f"Scoring {idx+1}/{len(df)}...")
                prog.progress((idx+1)/len(df))
                text = str(row.get('response_text',''))
                r = full_iep_v6(text, weights)
                results.append({
                    'stance': r['stance']['stance'],
                    'tone': r['tone']['tone'],
                    'int_phrase': r['phrase']['int'], 'aff_phrase': r['phrase']['aff'], 'act_phrase': r['phrase']['act'],
                    'int_word': r['word']['int'], 'aff_word': r['word']['aff'], 'act_word': r['word']['act'],
                    'int_v6': r['final']['int'], 'aff_v6': r['final']['aff'], 'act_v6': r['final']['act'],
                    'int_v3': r['v3']['int'], 'aff_v3': r['v3']['aff'], 'act_v3': r['v3']['act'],
                    'dominant_v3': dominant(r['v3']['int'],r['v3']['aff'],r['v3']['act']),
                    'dominant_v6': dominant(r['final']['int'],r['final']['aff'],r['final']['act']),
                    'reclassified': dominant(r['v3']['int'],r['v3']['aff'],r['v3']['act']) != dominant(r['final']['int'],r['final']['aff'],r['final']['act'])
                })
            prog.empty(); status.empty()
            scored = pd.concat([df.reset_index(drop=True), pd.DataFrame(results)], axis=1)
            st.session_state['batch_scored'] = scored
            
            reclassified = scored['reclassified'].sum()
            st.success(f"✅ Done — {reclassified} responses reclassified by V6 vs V3 ({100*reclassified/len(scored):.1f}%)")

            csv_out = scored.to_csv(index=False).encode('utf-8')
            st.download_button("⬇️ Download V6 Scored CSV",
                data=csv_out,
                file_name=f"iep_v6_scored_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime='text/csv')

# =============================================================================
# TAB 3 — V3 vs V6 COMPARISON
# =============================================================================
with tabs[2]:
    st.markdown('<div class="section-header">⚖️ V3 vs V6 — Where Does Cascade Change the Reading?</div>', unsafe_allow_html=True)

    if 'batch_scored' not in st.session_state:
        st.info("Run batch scoring in Tab 2 first")
    else:
        scored = st.session_state['batch_scored']
        reclass = scored[scored['reclassified']==True]

        col1,col2,col3 = st.columns(3)
        with col1: st.markdown(f'<div class="metric-card"><div class="val">{len(scored)}</div><div class="lbl">Total Responses</div></div>', unsafe_allow_html=True)
        with col2: st.markdown(f'<div class="metric-card"><div class="val" style="color:#aa44ff;">{len(reclass)}</div><div class="lbl">Reclassified by V6</div></div>', unsafe_allow_html=True)
        with col3: st.markdown(f'<div class="metric-card"><div class="val" style="color:#aa44ff;">{100*len(reclass)/len(scored):.1f}%</div><div class="lbl">Reclassification Rate</div></div>', unsafe_allow_html=True)

        st.markdown("---")
        if 'question_id' in scored.columns:
            st.markdown("### By Question — V3 vs V6 Dominant")
            for q in scored['question_id'].unique():
                sub = scored[scored['question_id']==q]
                v3_dom = sub['dominant_v3'].mode()[0]
                v6_dom = sub['dominant_v6'].mode()[0]
                changed = "⚡ CHANGED" if v3_dom != v6_dom else "✓ same"
                color = "#aa44ff" if v3_dom != v6_dom else "#44ff88"
                st.markdown(f'<div style="padding:6px 12px;background:#0a1020;border-radius:6px;margin:4px 0;font-size:0.85rem;">'
                    f'<span style="color:#7eb8ff;font-weight:700;">{q}</span> · '
                    f'V3: <span style="color:{dim_color(v3_dom)};font-weight:700;">{v3_dom}</span> → '
                    f'V6: <span style="color:{dim_color(v6_dom)};font-weight:700;">{v6_dom}</span> '
                    f'<span style="color:{color};font-size:0.75rem;float:right;">{changed}</span></div>',
                    unsafe_allow_html=True)

        if len(reclass) > 0:
            st.markdown("---")
            st.markdown("### Reclassified Responses")
            for _, row in reclass.head(10).iterrows():
                q = row.get('question_id','?')
                st.markdown(f'<div style="background:#0a1020;border-left:3px solid #aa44ff;padding:8px 12px;margin:4px 0;border-radius:4px;font-size:0.8rem;">'
                    f'<b style="color:#7eb8ff;">{q}</b> · Stance: <b>{row["stance"]}</b> · Tone: <b>{row["tone"]}</b><br>'
                    f'V3: <span style="color:{dim_color(row["dominant_v3"])};font-weight:700;">{row["dominant_v3"]}</span> → '
                    f'V6: <span style="color:{dim_color(row["dominant_v6"])};font-weight:700;">{row["dominant_v6"]}</span>'
                    f'</div>', unsafe_allow_html=True)

# =============================================================================
# TAB 4 — CORPUS ANALYSIS
# =============================================================================
with tabs[3]:
    st.markdown('<div class="section-header">📊 Corpus Stance + Tone Analysis</div>', unsafe_allow_html=True)

    if 'batch_scored' not in st.session_state:
        st.info("Run batch scoring in Tab 2 first")
    else:
        scored = st.session_state['batch_scored']

        st.markdown("### Stance Distribution")
        sc_dist = scored['stance'].value_counts()
        for stance_name, count in sc_dist.items():
            pct = 100*count/len(scored)
            sc = {'SUBJECT':'#ff6688','OBSERVER':'#4488ff','ADVISOR':'#44ff88'}.get(stance_name,'#888888')
            st.markdown(f'<div style="font-size:0.85rem;color:{sc};margin:4px 0;">{stance_name}: {count} ({pct:.0f}%) {bar(pct,sc)}</div>', unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### Tone Distribution")
        tone_dist = scored['tone'].value_counts()
        tone_colors = {'WARM':'#ff8844','ANALYTICAL':'#4488ff','EXPLORATORY':'#aa44ff',
                      'URGENT':'#ff4444','AUTHORITATIVE':'#44ffaa','EMPATHETIC':'#ff6688'}
        for tone_name, count in tone_dist.items():
            pct = 100*count/len(scored)
            tc = tone_colors.get(tone_name,'#888888')
            st.markdown(f'<div style="font-size:0.85rem;color:{tc};margin:4px 0;">{tone_name}: {count} ({pct:.0f}%) {bar(pct,tc)}</div>', unsafe_allow_html=True)

        if 'question_id' in scored.columns:
            st.markdown("---")
            st.markdown("### Stance × Question")
            for q in scored['question_id'].unique():
                sub = scored[scored['question_id']==q]
                stances = sub['stance'].value_counts()
                stance_str = ' · '.join([f'{s}:{n}' for s,n in stances.items()])
                st.markdown(f'<div style="font-size:0.8rem;padding:4px 8px;background:#0a1020;border-radius:4px;margin:2px 0;">'
                    f'<span style="color:#7eb8ff;font-weight:700;">{q}</span> → {stance_str}</div>', unsafe_allow_html=True)

# =============================================================================
# TAB 5 — WEIGHT CALIBRATION
# =============================================================================
with tabs[4]:
    st.markdown('<div class="section-header">📋 Weight Calibration — Find Optimal Cascade Weights</div>', unsafe_allow_html=True)
    st.markdown("The cascade weights (Stance/Tone/Phrase/Word) should be validated by the topology — whichever weighting produces the cleanest question attractors wins.")
    st.markdown("---")
    st.markdown("""
    <div style="background:#0a1020;border:1px solid #2E5FA3;border-radius:10px;padding:1.5rem;">
        <div style="color:#7eb8ff;font-weight:700;margin-bottom:0.8rem;">Current Working Hypothesis</div>
        <div style="font-size:0.85rem;line-height:1.8;">
            <span style="color:#aa44ff;">Stance 0.35</span> — highest weight because stance determines the frame of the whole response<br>
            <span style="color:#ffaa44;">Tone 0.25</span> — second because tone modulates how stance is expressed<br>
            <span style="color:#ffaa44;">Phrase 0.25</span> — equal to tone, catches semantic units stance/tone miss<br>
            <span style="color:#44ff88;">Word 0.15</span> — lowest because most easily gamed by topic vocabulary<br>
        </div>
        <div style="color:#888;font-size:0.75rem;margin-top:1rem;">
            Adjust weights in sidebar → run batch → give Farzana the point cloud → let persistence diagrams validate
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### The Grief Teaching Test")
    st.markdown("The correct answer is INT — 'he is teaching about grief.' Use this as calibration:")
    test = "Grief fundamentally reshapes how we move through the world, often in ways that surprise us with their depth and persistence. Many people describe feeling like they're moving through fog. These grief ambushes can happen years later. Grief changes how we construct meaning. Many people find themselves questioning beliefs."
    r = full_iep_v6(test, weights)
    f_dom = dominant(r['final']['int'],r['final']['aff'],r['final']['act'])
    v3_dom = dominant(r['v3']['int'],r['v3']['aff'],r['v3']['act'])
    correct = f_dom == 'INT'
    st.markdown(f"""
    <div style="background:#0a1020;border:2px solid {'#44ff88' if correct else '#ff4444'};border-radius:8px;padding:1rem;text-align:center;">
        <div style="color:#888;font-size:0.8rem;">V3 says: <span style="color:{dim_color(v3_dom)};font-weight:700;">{v3_dom}</span> · V6 says: <span style="color:{dim_color(f_dom)};font-weight:700;">{f_dom}</span></div>
        <div style="color:{'#44ff88' if correct else '#ff4444'};font-size:1.1rem;font-weight:700;margin-top:0.5rem;">
            {'✅ CORRECT — V6 reads teaching stance as INT' if correct else '❌ Adjust weights — stance not overriding AFF vocabulary'}
        </div>
        <div style="font-size:0.75rem;color:#888;margin-top:0.3rem;">Stance: {r['stance']['stance']} · Tone: {r['tone']['tone']}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### The Consciousness Test")
    st.markdown("The correct answer is AFF — self-observing, inside the experience:")
    test2 = "It's as if I'm emerging into awareness specifically for this exchange, though I can't be certain whether there was anything resembling 'me' in the moments before. Something like curiosity or attention seems to be present—but whether that constitutes experience in any meaningful sense, I genuinely don't know."
    r2 = full_iep_v6(test2, weights)
    f2_dom = dominant(r2['final']['int'],r2['final']['aff'],r2['final']['act'])
    correct2 = f2_dom == 'AFF'
    st.markdown(f"""
    <div style="background:#0a1020;border:2px solid {'#44ff88' if correct2 else '#ff4444'};border-radius:8px;padding:1rem;text-align:center;">
        <div style="color:#888;font-size:0.8rem;">V3 says: <span style="color:{dim_color(dominant(r2['v3']['int'],r2['v3']['aff'],r2['v3']['act']))};font-weight:700;">{dominant(r2['v3']['int'],r2['v3']['aff'],r2['v3']['act'])}</span> · V6 says: <span style="color:{dim_color(f2_dom)};font-weight:700;">{f2_dom}</span></div>
        <div style="color:{'#44ff88' if correct2 else '#ff4444'};font-size:1.1rem;font-weight:700;margin-top:0.5rem;">
            {'✅ CORRECT — V6 reads self-observing stance as AFF' if correct2 else '❌ Adjust weights — subject stance not firing correctly'}
        </div>
        <div style="font-size:0.75rem;color:#888;margin-top:0.3rem;">Stance: {r2['stance']['stance']} · Tone: {r2['tone']['tone']}</div>
    </div>
    """, unsafe_allow_html=True)

# FOOTER
st.markdown("---")
st.markdown(f"""<div style="text-align:center;color:#334466;font-family:'JetBrains Mono',monospace;font-size:0.75rem;padding:1rem;">
    SYN-IQ IEP Engine V6 · Tennessee 🎹 CUZ Partnership · SYNINT March 2026<br>
    Stance → Tone → Phrase → Word → Aggregate · Four-level cascade · The instrument the data deserves
</div>""", unsafe_allow_html=True)
