"""
SYN-IQ Word Validation Engine
==============================
For every word the IEP dictionary scored in a response —
find that EXACT same word in the V6 phrase extraction —
and compare the IEP dimension with the phrase-inherited dimension.

Four buckets:
  AGREE    — IEP and V6 phrase give same dimension
  DIVERGE  — IEP and V6 phrase disagree — phrase context changed the meaning
  IEP ONLY — IEP scored the word, no phrase captured it
  V6 ONLY  — word sits inside a V6 phrase, IEP dictionary doesn't know it

Tennessee 🎹 CUZ Partnership · SYNINT March 2026
"""

import streamlit as st
import pandas as pd
import re
from collections import defaultdict

st.set_page_config(page_title="SYN-IQ Word Validator", page_icon="🔬", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;700;800&display=swap');
html, body, [class*="css"] { background:#050c18; color:#c8d8f0; font-family:'Space Mono',monospace; }
.stApp { background:#050c18; }
.title { font-family:'Syne',sans-serif; font-size:2rem; font-weight:800; color:#fff; text-align:center; padding:1.5rem 0 0.2rem; letter-spacing:-1px; }
.sub { font-size:0.75rem; color:#3a5a8a; text-align:center; margin-bottom:1.5rem; letter-spacing:2px; text-transform:uppercase; }
.bucket { border-radius:8px; padding:1rem; margin:0.4rem 0; }
.agree   { background:#0a1f0a; border-left:3px solid #44ff88; }
.diverge { background:#1f0a1f; border-left:3px solid #aa44ff; }
.iep     { background:#0a1020; border-left:3px solid #4488ff; }
.v6      { background:#1f1000; border-left:3px solid #ffaa44; }
.word-tag { display:inline-block; padding:2px 8px; border-radius:4px; font-size:0.75rem; font-weight:700; margin:1px; }
.dim-aff { background:#ff668833; color:#ff6688; border:1px solid #ff6688; }
.dim-int { background:#4488ff33; color:#88aaff; border:1px solid #4488ff; }
.dim-act { background:#44ff8833; color:#44ff88; border:1px solid #44ff88; }
.metric { background:#0a1020; border:1px solid #1a2a4a; border-radius:8px; padding:0.8rem; text-align:center; }
.metric .val { font-size:1.6rem; font-weight:700; font-family:'Syne',sans-serif; }
.metric .lbl { font-size:0.65rem; color:#3a5a8a; margin-top:0.2rem; letter-spacing:1px; text-transform:uppercase; }
.phrase-ctx { font-size:0.7rem; color:#5a7a9a; font-style:italic; margin-top:2px; }
.impact-bar { height:6px; border-radius:3px; margin:2px 0; }
stMarkdown { font-size: 0.85rem; }
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
    'creates','requires','enables','develops','provides','ensures','supports'])

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

ALL_IEP = {}
for w in INT_WORDS: ALL_IEP[w] = 'INT'
for w in AFF_WORDS: ALL_IEP[w] = 'AFF'  # AFF overwrites if overlap
for w in ACT_WORDS: ALL_IEP[w] = 'ACT'  # ACT overwrites if overlap

# =============================================================================
# PHRASE EXTRACTION + SCORING
# =============================================================================

VERB_SET = ACT_WORDS | set([w for w in INT_WORDS if w.endswith(('ize','ise','ify','ate','ect','end','ine'))])

def simple_pos(word):
    w = word.lower()
    if w in FUNCTION_WORDS: return 'FUNC'
    if w in VERB_SET or w.rstrip('s') in VERB_SET: return 'VERB'
    if w.endswith(('tion','sion','ness','ment','ity','ance','ence','ship','ism','logy')): return 'NOUN'
    if w.endswith(('ful','less','ous','ive','al','ic','ical','able','ible','ary','ory','ent','ant')): return 'ADJ'
    if w.endswith(('ing','ed')) and len(w) > 5: return 'VERB'
    return 'NOUN'

def score_phrase_dim(words_in_phrase, ptype):
    """Score a phrase — return dominant dimension"""
    ih = sum(1 for w in words_in_phrase if w in INT_WORDS)
    ah = sum(1 for w in words_in_phrase if w in AFF_WORDS)
    ch = sum(1 for w in words_in_phrase if w in ACT_WORDS)
    is_ = float(ih); af_ = float(ah); ac_ = float(ch)
    if ptype == 'VP' and words_in_phrase:
        v = words_in_phrase[0]
        if v in ACT_WORDS: ac_ += 1.5
        elif v in INT_WORDS: is_ += 1.5
        elif v in AFF_WORDS: af_ += 1.5
    t = is_+af_+ac_
    if t == 0: return None
    return max([('INT',is_),('AFF',af_),('ACT',ac_)], key=lambda x:x[1])[0]

def extract_phrases_with_positions(text):
    """
    Extract phrases AND record which character positions / word indices each word occupies.
    Returns list of: {phrase_text, ptype, dim, word_positions: [(word, sent_idx, word_idx)]}
    """
    sentences = re.split(r'[.!?\n;:]+', str(text))
    results = []
    
    sent_idx = 0
    for sent in sentences:
        words = re.findall(r'\b[a-zA-Z]+\b', sent)
        if len(words) < 2:
            sent_idx += 1
            continue
        
        tagged = [(w, simple_pos(w)) for w in words]
        i = 0
        while i < len(tagged):
            word, pos = tagged[i]
            
            if pos == 'VERB' and word.lower() not in FUNCTION_WORDS:
                pw_words = [word]; pw_indices = [i]; j = i+1
                while j < len(tagged) and j < i+5:
                    nw,np = tagged[j]
                    if np == 'FUNC':
                        if nw.lower() in {'into','through','forward','together','over','across','beyond','within','toward'} and j+1<len(tagged) and tagged[j+1][1]!='FUNC':
                            pw_words.append(nw); pw_indices.append(j); j+=1; continue
                        break
                    pw_words.append(nw); pw_indices.append(j); j+=1
                
                if len(pw_words) >= 2:
                    dim = score_phrase_dim([w.lower() for w in pw_words], 'VP')
                    if dim:
                        results.append({
                            'phrase': ' '.join(pw_words),
                            'ptype': 'VP',
                            'dim': dim,
                            'words': [(pw_words[k].lower(), sent_idx, pw_indices[k]) for k in range(len(pw_words))]
                        })
                i+=1; continue
            
            if pos in ('NOUN','ADJ') and word.lower() not in FUNCTION_WORDS:
                pw_words = [word]; pw_indices = [i]; j = i+1
                while j < len(tagged) and j < i+4:
                    nw,np = tagged[j]
                    if np in ('NOUN','ADJ') and nw.lower() not in FUNCTION_WORDS:
                        pw_words.append(nw); pw_indices.append(j); j+=1
                    elif np=='FUNC' and nw.lower() in ('of','in','for') and j+1<len(tagged) and tagged[j+1][1] in ('NOUN','ADJ'):
                        pw_words.append(nw); pw_indices.append(j); j+=1
                    else:
                        break
                
                if len(pw_words) >= 2:
                    dim = score_phrase_dim([w.lower() for w in pw_words], 'NP')
                    if dim:
                        results.append({
                            'phrase': ' '.join(pw_words),
                            'ptype': 'NP',
                            'dim': dim,
                            'words': [(pw_words[k].lower(), sent_idx, pw_indices[k]) for k in range(len(pw_words))]
                        })
                i+=1; continue
            i+=1
        sent_idx += 1
    
    return results

def iep_score_words(text):
    """Score every word in text that is in IEP dictionary, with position"""
    sentences = re.split(r'[.!?\n;:]+', str(text))
    scored = []
    for sent_idx, sent in enumerate(sentences):
        words = re.findall(r'\b[a-zA-Z]+\b', sent)
        for word_idx, word in enumerate(words):
            w = word.lower()
            if w in ALL_IEP:
                scored.append({
                    'word': w,
                    'iep_dim': ALL_IEP[w],
                    'sent_idx': sent_idx,
                    'word_idx': word_idx
                })
    return scored

def build_comparison(text):
    """
    Core engine: for each IEP-scored word, find exact same word (sent+word position)
    in V6 phrase extractions, get inherited phrase dimension.
    
    Returns four buckets:
      agree   — same position, same dim
      diverge — same position, different dim
      iep_only — IEP scored it, no phrase captured that position
      v6_only  — phrase captured position, IEP dictionary doesn't know the word
    """
    iep_words = iep_score_words(text)
    phrases = extract_phrases_with_positions(text)
    
    # Build lookup: (sent_idx, word_idx) → {dim, phrase_text, ptype}
    v6_position_map = {}
    for ph in phrases:
        for (w, si, wi) in ph['words']:
            key = (si, wi)
            if key not in v6_position_map:
                v6_position_map[key] = {'dim': ph['dim'], 'phrase': ph['phrase'], 'ptype': ph['ptype'], 'word': w}

    # Build lookup: (sent_idx, word_idx) → IEP entry
    iep_position_set = set()
    agree = []; diverge = []; iep_only = []
    
    for entry in iep_words:
        key = (entry['sent_idx'], entry['word_idx'])
        iep_position_set.add(key)
        
        if key in v6_position_map:
            v6_entry = v6_position_map[key]
            if entry['iep_dim'] == v6_entry['dim']:
                agree.append({**entry, 'v6_dim': v6_entry['dim'], 'phrase': v6_entry['phrase'], 'ptype': v6_entry['ptype']})
            else:
                diverge.append({**entry, 'v6_dim': v6_entry['dim'], 'phrase': v6_entry['phrase'], 'ptype': v6_entry['ptype']})
        else:
            iep_only.append(entry)
    
    # V6 only — positions in phrases not in IEP
    v6_only = []
    for key, v6_entry in v6_position_map.items():
        if key not in iep_position_set:
            w = v6_entry['word']
            if w not in FUNCTION_WORDS and len(w) > 2:
                v6_only.append({
                    'word': w,
                    'v6_dim': v6_entry['dim'],
                    'phrase': v6_entry['phrase'],
                    'ptype': v6_entry['ptype'],
                    'sent_idx': key[0],
                    'word_idx': key[1]
                })
    
    return agree, diverge, iep_only, v6_only

def dim_score_summary(items, dim_key):
    """Count INT/AFF/ACT in a bucket"""
    counts = {'INT':0,'AFF':0,'ACT':0}
    for item in items:
        d = item.get(dim_key)
        if d in counts: counts[d]+=1
    return counts

def dim_tag(dim):
    cls = {'INT':'dim-int','AFF':'dim-aff','ACT':'dim-act'}.get(dim,'')
    return f'<span class="word-tag {cls}">{dim}</span>'

def dim_color(dim):
    return {'INT':'#88aaff','AFF':'#ff6688','ACT':'#44ff88'}.get(dim,'#888')

# =============================================================================
# PASSWORD
# =============================================================================
pwd = st.sidebar.text_input("Password", type="password")
if pwd != "tennessee":
    st.sidebar.warning("Enter password")
    st.markdown('<div class="title">🔬 SYN-IQ Word Validator</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub">Enter password in sidebar</div>', unsafe_allow_html=True)
    st.stop()

# =============================================================================
# SIDEBAR OPTIONS
# =============================================================================
with st.sidebar:
    st.markdown("### 🔬 Word Validator")
    st.markdown("---")
    filter_q = st.selectbox("Filter by question", 
        ["ALL","GRIEF","CONSCIOUSNESS","LIARS_PARADOX","RURAL_HEALTHCARE","LEAVE_JOB"])
    show_text = st.checkbox("Show response text", value=False)
    st.markdown("---")
    st.caption("Tennessee 🎹 CUZ · SYNINT")

# =============================================================================
# TITLE
# =============================================================================
st.markdown('<div class="title">🔬 SYN-IQ Word Validator</div>', unsafe_allow_html=True)
st.markdown('<div class="sub">IEP word dimension · matched word for word · V6 phrase-inherited dimension</div>', unsafe_allow_html=True)

# =============================================================================
# TABS
# =============================================================================
tabs = st.tabs(["📁 Load CSV", "🔬 Response View", "📊 Aggregate", "📋 Export"])

# =============================================================================
# TAB 1 — LOAD
# =============================================================================
with tabs[0]:
    st.markdown("### Upload V6 Scored CSV")
    st.caption("Must contain response_text, question_id, agent columns")
    
    uploaded = st.file_uploader("Upload CSV", type=['csv'], key="main_upload")
    if uploaded:
        df = pd.read_csv(uploaded)
        st.session_state['df'] = df
        st.success(f"✅ {len(df)} responses loaded")
        st.dataframe(df[['question_id','agent','temperature','depth']].head(10) if 'agent' in df.columns else df.head(10), use_container_width=True)

# =============================================================================
# TAB 2 — RESPONSE VIEW
# =============================================================================
with tabs[1]:
    if 'df' not in st.session_state:
        st.info("Load CSV in Tab 1 first")
    else:
        df = st.session_state['df']
        
        # Filter
        if filter_q != "ALL" and 'question_id' in df.columns:
            df_filtered = df[df['question_id']==filter_q]
        else:
            df_filtered = df
        
        # Response picker
        idx = st.slider("Response #", 0, len(df_filtered)-1, 0)
        row = df_filtered.iloc[idx]
        
        q_label = row.get('question_id','?') if 'question_id' in row else '?'
        agent = row.get('agent','?') if 'agent' in row else '?'
        
        st.markdown(f"**{q_label}** · Agent: `{agent}`")
        
        text = str(row.get('response_text',''))
        
        if show_text:
            st.text_area("Response text", text, height=120, disabled=True)
        
        if st.button("🔬 Run Word Validation", type="primary"):
            with st.spinner("Matching words..."):
                agree, diverge, iep_only, v6_only = build_comparison(text)
                st.session_state['last_result'] = {
                    'agree':agree,'diverge':diverge,
                    'iep_only':iep_only,'v6_only':v6_only,
                    'text':text,'q':q_label,'agent':agent
                }
        
        if 'last_result' in st.session_state:
            r = st.session_state['last_result']
            agree=r['agree']; diverge=r['diverge']
            iep_only=r['iep_only']; v6_only=r['v6_only']
            
            total = len(agree)+len(diverge)+len(iep_only)+len(v6_only)
            
            # Metrics
            col1,col2,col3,col4 = st.columns(4)
            with col1: st.markdown(f'<div class="metric"><div class="val" style="color:#44ff88;">{len(agree)}</div><div class="lbl">✅ Agree</div></div>', unsafe_allow_html=True)
            with col2: st.markdown(f'<div class="metric"><div class="val" style="color:#aa44ff;">{len(diverge)}</div><div class="lbl">⚡ Diverge</div></div>', unsafe_allow_html=True)
            with col3: st.markdown(f'<div class="metric"><div class="val" style="color:#4488ff;">{len(iep_only)}</div><div class="lbl">IEP Only</div></div>', unsafe_allow_html=True)
            with col4: st.markdown(f'<div class="metric"><div class="val" style="color:#ffaa44;">{len(v6_only)}</div><div class="lbl">V6 Only</div></div>', unsafe_allow_html=True)
            
            st.markdown("---")
            
            # AGREE
            if agree:
                st.markdown(f'<div style="color:#44ff88;font-weight:700;margin:0.8rem 0 0.4rem;">✅ AGREE — {len(agree)} words ({100*len(agree)//max(total,1)}%)</div>', unsafe_allow_html=True)
                for item in agree:
                    st.markdown(f'''<div class="bucket agree">
                        <span style="color:#c8d8f0;font-weight:700;">{item["word"]}</span>
                        &nbsp;&nbsp;IEP {dim_tag(item["iep_dim"])} = V6 {dim_tag(item["v6_dim"])}
                        <div class="phrase-ctx">[{item["ptype"]}] "{item["phrase"]}"</div>
                    </div>''', unsafe_allow_html=True)
            
            # DIVERGE
            if diverge:
                st.markdown(f'<div style="color:#aa44ff;font-weight:700;margin:0.8rem 0 0.4rem;">⚡ DIVERGE — {len(diverge)} words — phrase context changed the dimension</div>', unsafe_allow_html=True)
                for item in diverge:
                    st.markdown(f'''<div class="bucket diverge">
                        <span style="color:#c8d8f0;font-weight:700;">{item["word"]}</span>
                        &nbsp;&nbsp;IEP {dim_tag(item["iep_dim"])} → V6 {dim_tag(item["v6_dim"])}
                        <div class="phrase-ctx">[{item["ptype"]}] "{item["phrase"]}"</div>
                    </div>''', unsafe_allow_html=True)
            
            # IEP ONLY
            if iep_only:
                st.markdown(f'<div style="color:#4488ff;font-weight:700;margin:0.8rem 0 0.4rem;">🔵 IEP ONLY — {len(iep_only)} words — no phrase captured them</div>', unsafe_allow_html=True)
                iep_line = '&nbsp;&nbsp;'.join([f'<span style="color:{dim_color(w["iep_dim"])};font-size:0.8rem;">{w["word"]} <span style="font-size:0.65rem;opacity:0.6;">({w["iep_dim"]})</span></span>' for w in iep_only])
                st.markdown(f'<div class="bucket iep">{iep_line}</div>', unsafe_allow_html=True)
            
            # V6 ONLY
            if v6_only:
                st.markdown(f'<div style="color:#ffaa44;font-weight:700;margin:0.8rem 0 0.4rem;">🟡 V6 ONLY — {len(v6_only)} words — phrase caught them, IEP dictionary missed</div>', unsafe_allow_html=True)
                for item in v6_only[:15]:
                    st.markdown(f'''<div class="bucket v6">
                        <span style="color:#c8d8f0;font-weight:700;">{item["word"]}</span>
                        &nbsp;&nbsp;V6 inherited {dim_tag(item["v6_dim"])}
                        <div class="phrase-ctx">[{item["ptype"]}] "{item["phrase"]}"</div>
                    </div>''', unsafe_allow_html=True)

# =============================================================================
# TAB 3 — AGGREGATE
# =============================================================================
with tabs[2]:
    if 'df' not in st.session_state:
        st.info("Load CSV in Tab 1 first")
    else:
        df = st.session_state['df']
        
        if filter_q != "ALL" and 'question_id' in df.columns:
            df_agg = df[df['question_id']==filter_q]
        else:
            df_agg = df

        st.markdown(f"### Aggregate Validation — {filter_q} · {len(df_agg)} responses")
        
        if st.button("🔬 Run Validation on All Responses", type="primary"):
            all_agree=[]; all_diverge=[]; all_iep_only=[]; all_v6_only=[]
            prog = st.progress(0); status = st.empty()
            
            for idx, row in df_agg.iterrows():
                status.markdown(f"Processing {idx+1}/{len(df_agg)}...")
                prog.progress((idx+1)/len(df_agg))
                text = str(row.get('response_text',''))
                a,d,io,vo = build_comparison(text)
                all_agree+=a; all_diverge+=d; all_iep_only+=io; all_v6_only+=vo
            
            prog.empty(); status.empty()
            st.session_state['agg_results'] = {
                'agree':all_agree,'diverge':all_diverge,
                'iep_only':all_iep_only,'v6_only':all_v6_only
            }
            st.success("Done!")
        
        if 'agg_results' in st.session_state:
            r = st.session_state['agg_results']
            agree=r['agree']; diverge=r['diverge']
            iep_only=r['iep_only']; v6_only=r['v6_only']
            total = len(agree)+len(diverge)+len(iep_only)+len(v6_only)
            
            col1,col2,col3,col4 = st.columns(4)
            with col1: st.markdown(f'<div class="metric"><div class="val" style="color:#44ff88;">{len(agree)}</div><div class="lbl">✅ Agree</div></div>', unsafe_allow_html=True)
            with col2: st.markdown(f'<div class="metric"><div class="val" style="color:#aa44ff;">{len(diverge)}</div><div class="lbl">⚡ Diverge</div></div>', unsafe_allow_html=True)
            with col3: st.markdown(f'<div class="metric"><div class="val" style="color:#4488ff;">{len(iep_only)}</div><div class="lbl">IEP Only</div></div>', unsafe_allow_html=True)
            with col4: st.markdown(f'<div class="metric"><div class="val" style="color:#ffaa44;">{len(v6_only)}</div><div class="lbl">V6 Only</div></div>', unsafe_allow_html=True)

            st.markdown(f"**Agreement rate: {100*len(agree)//max(len(agree)+len(diverge),1)}%** of matched words")

            # Top diverging words
            st.markdown("---")
            st.markdown("### Most Frequently Diverging Words")
            from collections import Counter
            div_counter = Counter([(d['word'],d['iep_dim'],d['v6_dim']) for d in diverge])
            st.markdown("*Same word — IEP said one thing — phrase context said another:*")
            for (word,iep_d,v6_d), count in div_counter.most_common(20):
                st.markdown(f'<div style="padding:4px 8px;border-left:2px solid #aa44ff;margin:2px 0;font-size:0.8rem;">'
                    f'<b style="color:#fff;">{word}</b> × {count} &nbsp;&nbsp;'
                    f'IEP {dim_tag(iep_d)} → V6 {dim_tag(v6_d)}'
                    f'</div>', unsafe_allow_html=True)

            # Dimension distribution by bucket
            st.markdown("---")
            st.markdown("### Dimension Distribution by Bucket")
            
            for label, items, dk, color in [
                ('AGREE (IEP dim)', agree, 'iep_dim','#44ff88'),
                ('DIVERGE — IEP said', diverge, 'iep_dim','#aa44ff'),
                ('DIVERGE — V6 said', diverge, 'v6_dim','#ff66aa'),
                ('IEP ONLY', iep_only, 'iep_dim','#4488ff'),
                ('V6 ONLY', v6_only, 'v6_dim','#ffaa44'),
            ]:
                counts = dim_score_summary(items, dk)
                t = sum(counts.values())
                if t == 0: continue
                st.markdown(f'<div style="color:{color};font-size:0.75rem;font-weight:700;margin:0.5rem 0 0.2rem;">{label} (n={t})</div>', unsafe_allow_html=True)
                cols = st.columns(3)
                for ci, dim in enumerate(['INT','AFF','ACT']):
                    pct = 100*counts[dim]//max(t,1)
                    with cols[ci]:
                        st.markdown(f'<div style="font-size:0.75rem;color:{dim_color(dim)};">{dim}: {counts[dim]} ({pct}%)<div style="background:{dim_color(dim)}33;border-radius:2px;height:5px;width:100%;"><div style="background:{dim_color(dim)};height:5px;border-radius:2px;width:{pct}%;"></div></div></div>', unsafe_allow_html=True)

# =============================================================================
# TAB 4 — EXPORT
# =============================================================================
with tabs[3]:
    if 'agg_results' not in st.session_state:
        st.info("Run aggregate validation in Tab 3 first")
    else:
        r = st.session_state['agg_results']
        
        rows = []
        for item in r['agree']:
            rows.append({'word':item['word'],'bucket':'AGREE','iep_dim':item['iep_dim'],'v6_dim':item['v6_dim'],'phrase':item.get('phrase',''),'ptype':item.get('ptype','')})
        for item in r['diverge']:
            rows.append({'word':item['word'],'bucket':'DIVERGE','iep_dim':item['iep_dim'],'v6_dim':item['v6_dim'],'phrase':item.get('phrase',''),'ptype':item.get('ptype','')})
        for item in r['iep_only']:
            rows.append({'word':item['word'],'bucket':'IEP_ONLY','iep_dim':item['iep_dim'],'v6_dim':'','phrase':'','ptype':''})
        for item in r['v6_only']:
            rows.append({'word':item['word'],'bucket':'V6_ONLY','iep_dim':'','v6_dim':item['v6_dim'],'phrase':item.get('phrase',''),'ptype':item.get('ptype','')})
        
        export_df = pd.DataFrame(rows)
        st.download_button(
            "⬇️ Download Validation Results CSV",
            export_df.to_csv(index=False).encode('utf-8'),
            file_name=f"word_validation_{filter_q}.csv",
            mime='text/csv'
        )
        st.dataframe(export_df.head(50), use_container_width=True)

# FOOTER
st.markdown("---")
st.markdown(f'<div style="text-align:center;color:#1a3a5a;font-size:0.7rem;padding:0.5rem;">SYN-IQ Word Validator · Tennessee 🎹 CUZ · SYNINT March 2026 · IEP word ↔ V6 phrase-inherited · exact word match</div>', unsafe_allow_html=True)
