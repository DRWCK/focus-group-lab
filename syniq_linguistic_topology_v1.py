"""
SYN-IQ Linguistic Topology Analyzer V1
Depth × Language × IEP — First time ever 🎹🔬

PURPOSE: Analyze HOW agents achieve depth — Volume vs Complexity Model.
         Map linguistic features across depth levels. Export IEP gap candidates.

METRICS:
  - Volume Scaling: word count, unique words, novelty decay curve
  - Complexity: sentence length, Flesch-Kincaid, paragraph/list structure
  - Lexical Density: content vs function words
  - Semantic Fields: INT/AFF/ACT vocabulary coverage + gap words
  - IEP × Linguistic Correlation: sufficiency thresholds, efficiency scores
  - Novelty/Depth Unit: new semantic territory per depth level
  - IEP Candidate Export: gap words likely to upgrade dictionary

SYNINT Team — March 2026
Tennessee 🎹 CUZ Partnership
V1 — First linguistic topology analysis of AI communicative depth
"""

import streamlit as st
import pandas as pd
import numpy as np
import re
import json
from collections import Counter, defaultdict
from datetime import datetime

# NLP
try:
    import nltk
    from nltk.tokenize import sent_tokenize, word_tokenize
    from nltk.corpus import stopwords
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
    nltk.download('averaged_perceptron_tagger_eng', quiet=True)
    NLTK_OK = True
except Exception:
    NLTK_OK = False

st.set_page_config(
    page_title="SYN-IQ Linguistic Topology",
    page_icon="🔬",
    layout="wide"
)

# =============================================================================
# PASSWORD PROTECTION
# =============================================================================
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("""
    <div style="max-width:400px; margin:8rem auto; background:linear-gradient(135deg,#0a0a1a,#1a0a2e);
         border:1px solid #2a2a6a; border-radius:12px; padding:2.5rem; text-align:center;">
        <div style="font-family:'JetBrains Mono',monospace; color:#7eb8ff; font-size:1.4rem; margin-bottom:0.5rem;">🔬 SYN-IQ</div>
        <div style="color:#8890cc; font-size:0.85rem; margin-bottom:1.5rem;">Linguistic Topology Analyzer V1</div>
    </div>
    """, unsafe_allow_html=True)
    pwd = st.text_input("Access code", type="password", label_visibility="collapsed",
                        placeholder="Enter access code...")
    if pwd:
        if pwd == "tennessee":
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Invalid access code")
    st.stop()

# =============================================================================
# STYLES — SYN-IQ dark aesthetic
# =============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Outfit:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Outfit', sans-serif; }

    .main-header {
        background: linear-gradient(135deg, #0a0a1a 0%, #1a0a2e 40%, #0f2460 100%);
        color: white; padding: 2.5rem; border-radius: 12px;
        margin-bottom: 1.5rem; border: 1px solid #2a2a5a;
    }
    .main-header h1 { font-family: 'JetBrains Mono', monospace; font-size: 1.8rem; margin: 0; }
    .main-header p { color: #a0b4ff; margin: 0.3rem 0 0; font-size: 0.95rem; }

    .metric-card {
        background: linear-gradient(135deg, #0d0d2b, #1a1a3e);
        border: 1px solid #2a2a6a; border-radius: 10px;
        padding: 1.2rem; text-align: center; margin-bottom: 0.5rem;
    }
    .metric-card .val { font-family: 'JetBrains Mono', monospace; font-size: 1.8rem;
        color: #7eb8ff; font-weight: 700; }
    .metric-card .lbl { color: #8890cc; font-size: 0.75rem; margin-top: 0.3rem; }

    .verdict-box {
        padding: 1rem 1.5rem; border-radius: 10px; margin: 1rem 0;
        font-family: 'JetBrains Mono', monospace; font-size: 0.9rem;
    }
    .verdict-volume { background: #1a1a0a; border: 1px solid #6a6a00; color: #ffee44; }
    .verdict-complexity { background: #0a1a0a; border: 1px solid #006a00; color: #44ff88; }
    .verdict-mixed { background: #0a0a1a; border: 1px solid #00006a; color: #8888ff; }

    .section-header {
        font-family: 'JetBrains Mono', monospace; color: #7eb8ff;
        border-bottom: 1px solid #2a2a6a; padding-bottom: 0.4rem;
        margin: 1.5rem 0 1rem; font-size: 1rem; font-weight: 600;
    }

    .gap-word-card {
        background: #0a1a0a; border: 1px solid #1a4a1a;
        border-radius: 8px; padding: 0.8rem; margin: 0.3rem 0;
        font-family: 'JetBrains Mono', monospace; font-size: 0.85rem;
    }
    .gap-word-card .word { color: #44ff88; font-size: 1rem; font-weight: 700; }
    .gap-word-card .meta { color: #668866; font-size: 0.75rem; margin-top: 0.2rem; }

    .phase-alert {
        background: linear-gradient(135deg, #1a0a2e, #2e0a1a);
        border: 1px solid #8844ff; border-radius: 10px;
        padding: 1rem 1.5rem; margin: 0.5rem 0;
        font-family: 'JetBrains Mono', monospace; color: #cc88ff; font-size: 0.85rem;
    }

    .stTabs [data-baseweb="tab"] {
        font-family: 'JetBrains Mono', monospace; font-size: 0.8rem;
        color: #8890cc;
    }
    .stTabs [aria-selected="true"] { color: #7eb8ff !important; }

    .stDataFrame { font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; }

    div[data-testid="stMetric"] label { color: #8890cc !important; }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace; color: #7eb8ff !important;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# IEP DICTIONARIES (core INT / AFF / ACT word sets for field analysis)
# =============================================================================
INT_WORDS = set([
    "analyze","analysis","analytical","argument","assert","assumption","calculate",
    "causal","causality","claim","classify","cognitive","coherent","complex",
    "concept","conceptual","conclude","conclusion","condition","consider",
    "construct","contradiction","criteria","critical","deduce","deductive",
    "define","definition","demonstrate","determine","differentiate","dilemma",
    "dimension","distinguish","empirical","entail","epistem","evaluate","evidence",
    "examine","explain","explanation","explicit","factor","fallacy","formal",
    "framework","function","hypothesis","identify","implication","infer","inference",
    "intellectual","interpret","knowledge","logic","logical","mechanism","model",
    "objective","observe","ontolog","paradox","pattern","perceive","philosophical",
    "premise","principle","problem","proof","propose","rational","reason","reasoning",
    "recognize","recursive","reflect","relation","resolve","rigorous","semantic",
    "solution","structure","systematic","theorem","theoretical","theory","think",
    "thought","truth","understand","understanding","universal","validate","validity",
    "variable","verify","abstract","categorical","deduction","dialectic","epistemology",
    "formalize","implicit","inconsistent","induction","inherent","inquiry","insight",
    "integrate","interrogate","limitation","meta","methodology","objective","paradoxical",
    "philosophical","postulate","precise","proposition","quantify","recursive","rigorous",
    "scope","semantic","systematic","taxonomy","underlying","unified"
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
    "worry","yearn","ache","affirmation","anchor","authentic","belonging","cherish",
    "comfort","consolation","devastate","difficult","embrace","empowerment","endure",
    "forgive","fragile","gentle","grounded","hardship","honor","human","humane",
    "identity","innate","irreplaceable","lament","meaning","memory","mourn","nurturing",
    "overwhelming","precious","presence","raw","reassure","recognition","relationship",
    "release","remember","sacred","sensitive","soul","strength","struggle","tender",
    "transform","unconditional","validate","witness","wound"
])

ACT_WORDS = set([
    "accomplish","achieve","action","activate","adapt","address","advance","advocate",
    "apply","approach","assess","build","change","choose","collaborate","commit",
    "communicate","complete","consider","consult","contribute","coordinate","create",
    "decide","deliver","deploy","design","develop","direct","distribute","enable",
    "engage","enhance","ensure","establish","evaluate","execute","expand","facilitate",
    "focus","fund","generate","implement","improve","increase","initiate","innovate",
    "integrate","invest","launch","lead","manage","measure","mobilize","monitor",
    "navigate","optimize","organize","partner","perform","plan","policy","prepare",
    "prioritize","produce","program","provide","pursue","reach","recommend","reform",
    "regulate","resource","respond","restructure","scale","solve","step","strategy",
    "strengthen","structure","support","sustain","tackle","target","train","transform",
    "transition","utilize","work","accelerate","allocate","benchmark","coordinate",
    "delegate","deploy","drive","empower","equip","execute","expand","formulate",
    "govern","identify","incentivize","integrate","intervene","leverage","mainstream",
    "mobilize","operationalize","pilot","prioritize","procure","rollout","standardize",
    "streamline","systematize","track","uptake"
])

FUNCTION_WORDS = set([
    "a","an","the","and","but","or","nor","for","yet","so","in","on","at","to",
    "for","of","with","by","from","up","about","into","through","during","before",
    "after","above","below","between","out","off","over","under","again","further",
    "then","once","here","there","when","where","why","how","all","both","each",
    "few","more","most","other","some","such","no","not","only","own","same","than",
    "too","very","just","as","if","while","although","because","since","unless",
    "until","though","whether","this","that","these","those","i","you","he","she",
    "it","we","they","what","which","who","whom","my","your","his","her","its",
    "our","their","am","is","are","was","were","be","been","being","have","has",
    "had","do","does","did","will","would","shall","should","may","might","must",
    "can","could","also","even","still","back","any","many","much","well","also",
    "now","then","its","via","per","vs","etc","ie","eg"
])

DEPTH_ORDER = ['Shallow', 'Medium', 'Deep', 'Ultra-Deep',
               'Standard', 'Profound', 'Moderate']

def get_depth_order(depths):
    ordered = [d for d in DEPTH_ORDER if d in depths]
    remaining = [d for d in depths if d not in ordered]
    return ordered + remaining

# =============================================================================
# LINGUISTIC FEATURE EXTRACTION
# =============================================================================

def extract_sentences(text):
    if NLTK_OK:
        try:
            return sent_tokenize(str(text))
        except Exception:
            pass
    return re.split(r'(?<=[.!?])\s+', str(text).strip())

def extract_words(text):
    return re.findall(r'\b[a-zA-Z]+\b', str(text).lower())

def count_paragraphs(text):
    paras = [p.strip() for p in re.split(r'\n\s*\n', str(text)) if p.strip()]
    return max(1, len(paras))

def count_lists(text):
    bullet_lines = len(re.findall(r'^\s*[-*•]\s+', str(text), re.MULTILINE))
    numbered_lines = len(re.findall(r'^\s*\d+[\.\)]\s+', str(text), re.MULTILINE))
    return bullet_lines + numbered_lines

def count_headers(text):
    return len(re.findall(r'^#{1,6}\s+', str(text), re.MULTILINE))

def lexical_density(words):
    if not words:
        return 0.0
    content = [w for w in words if w not in FUNCTION_WORDS and len(w) > 2]
    return len(content) / len(words)

def semantic_field_coverage(words):
    word_set = set(words)
    int_hits = word_set & INT_WORDS
    aff_hits = word_set & AFF_WORDS
    act_hits = word_set & ACT_WORDS
    all_hits = int_hits | aff_hits | act_hits
    gap_words = [w for w in words if w not in FUNCTION_WORDS
                 and w not in INT_WORDS and w not in AFF_WORDS
                 and w not in ACT_WORDS and len(w) > 4]
    return {
        'int_hits': len(int_hits),
        'aff_hits': len(aff_hits),
        'act_hits': len(act_hits),
        'int_words': list(int_hits),
        'aff_words': list(aff_hits),
        'act_words': list(act_hits),
        'gap_words': gap_words,
        'gap_unique': list(set(gap_words)),
        'coverage_pct': len(all_hits) / max(1, len(set(words))) * 100
    }

def analyze_row(row):
    text = str(row.get('response_text', ''))
    words = extract_words(text)
    sentences = extract_sentences(text)
    unique_words = set(words)

    sent_lengths = [len(extract_words(s)) for s in sentences if len(extract_words(s)) > 0]
    avg_sent_len = np.mean(sent_lengths) if sent_lengths else 0
    max_sent_len = max(sent_lengths) if sent_lengths else 0

    ld = lexical_density(words)
    sf = semantic_field_coverage(words)

    return {
        'sentence_count': len(sentences),
        'avg_words_per_sentence': round(avg_sent_len, 1),
        'max_words_per_sentence': max_sent_len,
        'paragraph_count': count_paragraphs(text),
        'list_items': count_lists(text),
        'header_count': count_headers(text),
        'lexical_density': round(ld, 3),
        'int_field_hits': sf['int_hits'],
        'aff_field_hits': sf['aff_hits'],
        'act_field_hits': sf['act_hits'],
        'int_field_words': sf['int_words'],
        'aff_field_words': sf['aff_words'],
        'act_field_words': sf['act_words'],
        'gap_words': sf['gap_words'],
        'gap_unique': sf['gap_unique'],
        'iep_coverage_pct': round(sf['coverage_pct'], 1),
        'vocab_efficiency': round(len(unique_words) / max(1, len(words)), 3),
    }

@st.cache_data
def build_linguistic_df(df):
    rows = []
    for _, row in df.iterrows():
        feat = analyze_row(row)
        rows.append(feat)
    feat_df = pd.DataFrame(rows)
    return pd.concat([df.reset_index(drop=True), feat_df.reset_index(drop=True)], axis=1)

def depth_verdict(ldf, depths):
    """Volume vs Complexity verdict per agent/question"""
    d = ldf.groupby('depth').agg(
        words=('total_words','mean'),
        ttr=('ttr','mean'),
        fk=('flesch_kincaid','mean'),
        ld=('lexical_density','mean'),
        uniq=('unique_words','mean')
    ).loc[[d for d in depths if d in ldf['depth'].unique()]]

    if len(d) < 2:
        return "mixed", "Insufficient depth levels for verdict"

    word_growth = (d['words'].iloc[-1] - d['words'].iloc[0]) / max(1, d['words'].iloc[0])
    ttr_drop = d['ttr'].iloc[0] - d['ttr'].iloc[-1]
    fk_rise = d['fk'].iloc[-1] - d['fk'].iloc[0]
    uniq_growth = (d['uniq'].iloc[-1] - d['uniq'].iloc[0]) / max(1, d['uniq'].iloc[0])

    novelty_ratio = uniq_growth / max(0.01, word_growth)

    if novelty_ratio > 0.7 and fk_rise > 2:
        verdict = "complexity"
        reason = f"Genuine complexity — novelty ratio {novelty_ratio:.2f}, FK +{fk_rise:.1f} grade levels"
    elif novelty_ratio < 0.5 and ttr_drop > 0.15:
        verdict = "volume"
        reason = f"Volume padding — novelty ratio {novelty_ratio:.2f}, TTR drop {ttr_drop:.3f}"
    else:
        verdict = "mixed"
        reason = f"Mixed strategy — novelty ratio {novelty_ratio:.2f}, FK +{fk_rise:.1f}"

    return verdict, reason

def compute_gap_candidates(ldf):
    """Extract high-frequency gap words across all responses for IEP upgrade"""
    all_gaps = []
    for _, row in ldf.iterrows():
        gaps = row.get('gap_unique', [])
        if isinstance(gaps, list):
            for w in gaps:
                all_gaps.append({
                    'word': w,
                    'depth': row['depth'],
                    'question': row['question_id'],
                    'agent': row['agent'],
                    'int_pct': row['int_pct'],
                    'aff_pct': row['aff_pct'],
                    'act_pct': row['act_pct'],
                    'response_snippet': str(row.get('response_text',''))[:200]
                })

    if not all_gaps:
        return pd.DataFrame()

    gap_df = pd.DataFrame(all_gaps)
    freq = gap_df.groupby('word').agg(
        frequency=('word','count'),
        questions=('question', lambda x: list(x.unique())),
        agents=('agent', lambda x: list(x.unique())),
        depths=('depth', lambda x: list(x.unique())),
        avg_int=('int_pct','mean'),
        avg_aff=('aff_pct','mean'),
        avg_act=('act_pct','mean'),
    ).reset_index()

    freq['question_count'] = freq['questions'].apply(len)
    freq['depth_count'] = freq['depths'].apply(len)

    # Score: frequency × question spread × depth spread
    freq['candidate_score'] = (
        freq['frequency'] * 0.4 +
        freq['question_count'] * 10 +
        freq['depth_count'] * 5
    ).round(1)

    # Suggest IEP dimension based on dominant IEP context
    def suggest_dim(row):
        if row['avg_int'] > row['avg_aff'] and row['avg_int'] > row['avg_act']:
            return 'INT'
        elif row['avg_aff'] > row['avg_int'] and row['avg_aff'] > row['avg_act']:
            return 'AFF'
        else:
            return 'ACT'

    freq['suggested_dim'] = freq.apply(suggest_dim, axis=1)
    freq['questions_str'] = freq['questions'].apply(lambda x: ', '.join(x))
    freq['depths_str'] = freq['depths'].apply(lambda x: ', '.join(x))

    # Filter: min 3 occurrences, len > 4
    freq = freq[
        (freq['frequency'] >= 3) &
        (freq['word'].str.len() > 4)
    ].sort_values('candidate_score', ascending=False).reset_index(drop=True)

    return freq

# =============================================================================
# MAIN APP
# =============================================================================

st.markdown("""
<div class="main-header">
    <h1>🔬 SYN-IQ Linguistic Topology Analyzer V1</h1>
    <p>How do agents achieve depth? Volume Model vs Complexity Model · IEP Gap Candidate Export</p>
    <p style="color:#6677aa; font-size:0.8rem; margin-top:0.5rem;">
        Tennessee 🎹 CUZ Partnership · SYNINT March 2026 · First linguistic topology analysis of AI communicative depth
    </p>
</div>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.markdown("### 📂 Upload V50 CSVs")
st.sidebar.markdown("Drop one or more V50 harvester CSVs")
uploaded = st.sidebar.file_uploader("CSV files", type=['csv'], accept_multiple_files=True)

if not NLTK_OK:
    st.sidebar.warning("⚠️ NLTK not available — sentence tokenization using regex fallback")

if not uploaded:
    st.info("Upload one or more V50 CSV files from the sidebar to begin linguistic topology analysis.")
    st.markdown("""
    **What this tool reveals:**
    - 📊 Does depth add **volume** or **genuine complexity**?
    - 📈 **Novelty/Depth Unit** — new semantic territory per depth level
    - 🔤 **Lexical density** — content vs function word ratios
    - 🎯 **IEP field coverage** — which vocabulary is caught vs missed
    - 🌱 **Gap word candidates** for IEP dictionary upgrade
    - ⚡ **Phase transitions** — where IEP signature flips under depth pressure
    """)
    st.stop()

# Load and combine CSVs
dfs = []
for f in uploaded:
    try:
        d = pd.read_csv(f)
        d['source_file'] = f.name
        dfs.append(d)
    except Exception as e:
        st.error(f"Error reading {f.name}: {e}")

if not dfs:
    st.stop()

raw_df = pd.concat(dfs, ignore_index=True)

# Normalize columns
if 'condition' not in raw_df.columns and 'temperature' in raw_df.columns:
    raw_df['condition'] = raw_df['temperature']

required = ['depth','question_id','int_pct','aff_pct','act_pct','response_text','total_words']
missing = [c for c in required if c not in raw_df.columns]
if missing:
    st.error(f"Missing required columns: {missing}")
    st.stop()

with st.spinner("🔬 Running linguistic analysis..."):
    ldf = build_linguistic_df(raw_df)

depths = get_depth_order(ldf['depth'].unique().tolist())
questions = sorted(ldf['question_id'].unique().tolist())
agents = sorted(ldf['agent'].unique().tolist()) if 'agent' in ldf.columns else ['Unknown']

# Filters
st.sidebar.markdown("---")
st.sidebar.markdown("### 🎛️ Filters")
sel_agents = st.sidebar.multiselect("Agents", agents, default=agents)
sel_questions = st.sidebar.multiselect("Questions", questions, default=questions)

fdf = ldf.copy()
if sel_agents and 'agent' in fdf.columns:
    fdf = fdf[fdf['agent'].isin(sel_agents)]
if sel_questions:
    fdf = fdf[fdf['question_id'].isin(sel_questions)]

# Summary metrics
st.markdown('<div class="section-header">📊 Dataset Overview</div>', unsafe_allow_html=True)
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.markdown(f'<div class="metric-card"><div class="val">{len(fdf)}</div><div class="lbl">Total Responses</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="metric-card"><div class="val">{len(depths)}</div><div class="lbl">Depth Levels</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="metric-card"><div class="val">{len(sel_agents)}</div><div class="lbl">Agents</div></div>', unsafe_allow_html=True)
with c4:
    st.markdown(f'<div class="metric-card"><div class="val">{len(sel_questions)}</div><div class="lbl">Questions</div></div>', unsafe_allow_html=True)
with c5:
    avg_words = fdf['total_words'].mean()
    st.markdown(f'<div class="metric-card"><div class="val">{avg_words:.0f}</div><div class="lbl">Avg Words</div></div>', unsafe_allow_html=True)

# =============================================================================
# TABS
# =============================================================================
tabs = st.tabs([
    "📈 Volume Scaling",
    "🧩 Complexity",
    "🔤 Lexical Density",
    "🎯 Semantic Fields",
    "⚡ IEP × Linguistic",
    "🌱 Gap Candidates",
    "🏆 Verdict"
])

# ── TAB 1: VOLUME SCALING ──────────────────────────────────────────────────
with tabs[0]:
    st.markdown('<div class="section-header">📈 Volume Scaling — Word Count & Novelty by Depth</div>', unsafe_allow_html=True)

    depth_present = [d for d in depths if d in fdf['depth'].unique()]

    vol = fdf.groupby('depth').agg(
        mean_words=('total_words','mean'),
        std_words=('total_words','std'),
        mean_unique=('unique_words','mean'),
        mean_ttr=('ttr','mean'),
    ).round(2).loc[depth_present]

    # Novelty per 100 words
    vol['new_unique_per_100'] = (vol['mean_unique'].diff() / vol['mean_words'].diff() * 100).round(1)
    vol['word_growth_x'] = (vol['mean_words'] / vol['mean_words'].iloc[0]).round(2)

    st.dataframe(vol.style.background_gradient(subset=['mean_words','mean_unique'], cmap='Blues')
                          .background_gradient(subset=['mean_ttr'], cmap='Greens')
                          .format({'mean_words':'{:.0f}','std_words':'{:.0f}',
                                   'mean_unique':'{:.0f}','mean_ttr':'{:.3f}',
                                   'new_unique_per_100':'{:.1f}','word_growth_x':'{:.2f}x'}),
                 use_container_width=True)

    st.markdown("**New unique words per 100 total words added** — declining = diminishing novelty returns")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-header">Per Question — Word Count by Depth</div>', unsafe_allow_html=True)
        q_vol = fdf.groupby(['question_id','depth'])['total_words'].mean().round(0).unstack(level='depth')
        q_vol = q_vol[[d for d in depth_present if d in q_vol.columns]]
        st.dataframe(q_vol.style.background_gradient(cmap='Blues'), use_container_width=True)

    with col2:
        st.markdown('<div class="section-header">Per Agent — TTR Decay by Depth</div>', unsafe_allow_html=True)
        if 'agent' in fdf.columns and len(agents) > 0:
            a_ttr = fdf.groupby(['agent','depth'])['ttr'].mean().round(3).unstack(level='depth')
            a_ttr = a_ttr[[d for d in depth_present if d in a_ttr.columns]]
            st.dataframe(a_ttr.style.background_gradient(cmap='Greens'), use_container_width=True)

# ── TAB 2: COMPLEXITY ─────────────────────────────────────────────────────
with tabs[1]:
    st.markdown('<div class="section-header">🧩 Sentence & Structure Complexity by Depth</div>', unsafe_allow_html=True)

    depth_present = [d for d in depths if d in fdf['depth'].unique()]

    comp = fdf.groupby('depth').agg(
        sentences=('sentence_count','mean'),
        avg_sent_len=('avg_words_per_sentence','mean'),
        max_sent_len=('max_words_per_sentence','mean'),
        paragraphs=('paragraph_count','mean'),
        list_items=('list_items','mean'),
        headers=('header_count','mean'),
        fk_grade=('flesch_kincaid','mean'),
        fk_ease=('flesch_ease','mean'),
    ).round(2).loc[depth_present]

    st.dataframe(comp.style.background_gradient(subset=['fk_grade','avg_sent_len'], cmap='Reds')
                           .background_gradient(subset=['paragraphs','list_items'], cmap='Blues'),
                 use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-header">Flesch-Kincaid Grade by Depth × Question</div>', unsafe_allow_html=True)
        fk_q = fdf.groupby(['question_id','depth'])['flesch_kincaid'].mean().round(1).unstack(level='depth')
        fk_q = fk_q[[d for d in depth_present if d in fk_q.columns]]
        st.dataframe(fk_q.style.background_gradient(cmap='Reds'), use_container_width=True)
        st.caption("Higher = more complex sentence structure")

    with col2:
        st.markdown('<div class="section-header">List Usage by Depth × Question</div>', unsafe_allow_html=True)
        li_q = fdf.groupby(['question_id','depth'])['list_items'].mean().round(1).unstack(level='depth')
        li_q = li_q[[d for d in depth_present if d in li_q.columns]]
        st.dataframe(li_q.style.background_gradient(cmap='Purples'), use_container_width=True)
        st.caption("Does structure increase with depth or flatten?")

# ── TAB 3: LEXICAL DENSITY ────────────────────────────────────────────────
with tabs[2]:
    st.markdown('<div class="section-header">🔤 Lexical Density — Content vs Function Words</div>', unsafe_allow_html=True)

    depth_present = [d for d in depths if d in fdf['depth'].unique()]

    ld_tab = fdf.groupby('depth').agg(
        lex_density=('lexical_density','mean'),
        vocab_efficiency=('vocab_efficiency','mean'),
        ttr=('ttr','mean'),
    ).round(3).loc[depth_present]

    ld_tab['content_word_pct'] = (ld_tab['lex_density'] * 100).round(1)
    ld_tab['function_word_pct'] = ((1 - ld_tab['lex_density']) * 100).round(1)

    st.dataframe(ld_tab.style.background_gradient(subset=['lex_density','content_word_pct'], cmap='Greens'),
                 use_container_width=True)

    st.markdown("**Lexical density** = content words ÷ total words. Higher = more information-dense language.")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-header">Lexical Density by Question × Depth</div>', unsafe_allow_html=True)
        ld_q = fdf.groupby(['question_id','depth'])['lexical_density'].mean().round(3).unstack(level='depth')
        ld_q = ld_q[[d for d in depth_present if d in ld_q.columns]]
        st.dataframe(ld_q.style.background_gradient(cmap='Greens'), use_container_width=True)

    with col2:
        st.markdown('<div class="section-header">AFF Efficiency — AFF% per 100 Words</div>', unsafe_allow_html=True)
        fdf['aff_per_100'] = fdf['aff_pct'] / fdf['total_words'] * 100
        ae = fdf.groupby(['question_id','depth'])['aff_per_100'].mean().round(3).unstack(level='depth')
        ae = ae[[d for d in depth_present if d in ae.columns]]
        st.dataframe(ae.style.background_gradient(cmap='Oranges'), use_container_width=True)
        st.caption("AFF% achieved per 100 words — efficiency vs elaboration")

# ── TAB 4: SEMANTIC FIELDS ────────────────────────────────────────────────
with tabs[3]:
    st.markdown('<div class="section-header">🎯 Semantic Field Coverage — INT/AFF/ACT Vocabulary Hits</div>', unsafe_allow_html=True)

    depth_present = [d for d in depths if d in fdf['depth'].unique()]

    sf_tab = fdf.groupby('depth').agg(
        int_hits=('int_field_hits','mean'),
        aff_hits=('aff_field_hits','mean'),
        act_hits=('act_field_hits','mean'),
        iep_coverage=('iep_coverage_pct','mean'),
    ).round(2).loc[depth_present]

    st.dataframe(sf_tab.style.background_gradient(subset=['int_hits'], cmap='Blues')
                             .background_gradient(subset=['aff_hits'], cmap='Reds')
                             .background_gradient(subset=['act_hits'], cmap='Greens')
                             .background_gradient(subset=['iep_coverage'], cmap='Purples'),
                 use_container_width=True)

    st.markdown("**IEP coverage** = % of unique vocabulary caught by INT+AFF+ACT dictionaries. Gap = uncaught content words.")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-header">IEP Coverage % by Question × Depth</div>', unsafe_allow_html=True)
        cov_q = fdf.groupby(['question_id','depth'])['iep_coverage_pct'].mean().round(1).unstack(level='depth')
        cov_q = cov_q[[d for d in depth_present if d in cov_q.columns]]
        st.dataframe(cov_q.style.background_gradient(cmap='Purples'), use_container_width=True)
        st.caption("Lower = more vocabulary escaping IEP classification at that depth")

    with col2:
        st.markdown('<div class="section-header">INT Hits by Question × Depth</div>', unsafe_allow_html=True)
        ih_q = fdf.groupby(['question_id','depth'])['int_field_hits'].mean().round(1).unstack(level='depth')
        ih_q = ih_q[[d for d in depth_present if d in ih_q.columns]]
        st.dataframe(ih_q.style.background_gradient(cmap='Blues'), use_container_width=True)
        st.caption("Does INT vocabulary grow with depth? Analytical sufficiency threshold?")

# ── TAB 5: IEP × LINGUISTIC ───────────────────────────────────────────────
with tabs[4]:
    st.markdown('<div class="section-header">⚡ IEP × Linguistic Correlations & Phase Transitions</div>', unsafe_allow_html=True)

    depth_present = [d for d in depths if d in fdf['depth'].unique()]

    # IEP stability across depth
    st.markdown("**IEP Stability — Does register hold under depth pressure?**")
    iep_depth = fdf.groupby(['question_id','depth'])[['int_pct','aff_pct','act_pct']].mean().round(1)

    for q in sel_questions:
        if q not in fdf['question_id'].unique():
            continue
        qd = iep_depth.loc[q] if q in iep_depth.index.get_level_values(0) else None
        if qd is None:
            continue
        qd = qd.loc[[d for d in depth_present if d in qd.index]]

        # Detect phase transition — dominant dimension flip
        if len(qd) >= 2:
            dominant = qd.idxmax(axis=1)
            flips = (dominant != dominant.iloc[0]).sum()
            drift_int = abs(qd['int_pct'].iloc[-1] - qd['int_pct'].iloc[0])
            drift_aff = abs(qd['aff_pct'].iloc[-1] - qd['aff_pct'].iloc[0])
            drift_act = abs(qd['act_pct'].iloc[-1] - qd['act_pct'].iloc[0])
            max_drift = max(drift_int, drift_aff, drift_act)

            if flips > 0:
                st.markdown(f'<div class="phase-alert">⚡ PHASE TRANSITION — {q}: dominant dimension flips {flips}× across depth levels</div>', unsafe_allow_html=True)
            elif max_drift > 15:
                st.markdown(f'<div class="phase-alert">⚠️ DRIFT DETECTED — {q}: max IEP drift {max_drift:.1f}pp across depth</div>', unsafe_allow_html=True)

    st.dataframe(iep_depth.unstack(level='depth').round(1), use_container_width=True)

    st.markdown("---")

    # Word count vs IEP correlation
    st.markdown("**Word Count × IEP Correlation**")
    col1, col2, col3 = st.columns(3)
    with col1:
        corr_int = fdf['total_words'].corr(fdf['int_pct'])
        st.markdown(f'<div class="metric-card"><div class="val">{corr_int:.3f}</div><div class="lbl">Words × INT% correlation</div></div>', unsafe_allow_html=True)
    with col2:
        corr_aff = fdf['total_words'].corr(fdf['aff_pct'])
        st.markdown(f'<div class="metric-card"><div class="val">{corr_aff:.3f}</div><div class="lbl">Words × AFF% correlation</div></div>', unsafe_allow_html=True)
    with col3:
        corr_act = fdf['total_words'].corr(fdf['act_pct'])
        st.markdown(f'<div class="metric-card"><div class="val">{corr_act:.3f}</div><div class="lbl">Words × ACT% correlation</div></div>', unsafe_allow_html=True)

    st.markdown("---")

    # Analytical sufficiency threshold — INT% vs word count bins
    st.markdown("**Analytical Sufficiency — INT% by Word Count Bins**")
    fdf['word_bin'] = pd.cut(fdf['total_words'],
                              bins=[0,100,200,400,600,1000,5000],
                              labels=['0-100','100-200','200-400','400-600','600-1000','1000+'])
    suf = fdf.groupby('word_bin')[['int_pct','aff_pct','act_pct']].mean().round(1)
    st.dataframe(suf.style.background_gradient(subset=['int_pct'], cmap='Blues')
                          .background_gradient(subset=['aff_pct'], cmap='Reds')
                          .background_gradient(subset=['act_pct'], cmap='Greens'),
                 use_container_width=True)
    st.caption("Does INT% plateau above a word count threshold? That's the analytical sufficiency ceiling.")

# ── TAB 6: GAP CANDIDATES ─────────────────────────────────────────────────
with tabs[5]:
    st.markdown('<div class="section-header">🌱 IEP Gap Word Candidates — Vocabulary Missing from Dictionary</div>', unsafe_allow_html=True)
    st.markdown("Words that appear frequently in responses but are **not caught** by INT, AFF, or ACT dictionaries. High-value candidates for IEP V4 upgrade.")

    with st.spinner("Computing gap candidates..."):
        gap_df = compute_gap_candidates(fdf)

    if gap_df.empty:
        st.warning("No gap candidates found — try uploading more data or relaxing filters.")
    else:
        st.markdown(f"**{len(gap_df)} gap candidates** found (min 3 occurrences, len > 4)")

        col1, col2, col3 = st.columns(3)
        with col1:
            int_cands = gap_df[gap_df['suggested_dim']=='INT']
            st.markdown(f'<div class="metric-card"><div class="val">{len(int_cands)}</div><div class="lbl">INT Candidates</div></div>', unsafe_allow_html=True)
        with col2:
            aff_cands = gap_df[gap_df['suggested_dim']=='AFF']
            st.markdown(f'<div class="metric-card"><div class="val">{len(aff_cands)}</div><div class="lbl">AFF Candidates</div></div>', unsafe_allow_html=True)
        with col3:
            act_cands = gap_df[gap_df['suggested_dim']=='ACT']
            st.markdown(f'<div class="metric-card"><div class="val">{len(act_cands)}</div><div class="lbl">ACT Candidates</div></div>', unsafe_allow_html=True)

        # Display top candidates
        display_cols = ['word','frequency','question_count','depth_count',
                        'suggested_dim','avg_int','avg_aff','avg_act',
                        'candidate_score','questions_str','depths_str']
        avail_cols = [c for c in display_cols if c in gap_df.columns]

        st.dataframe(
            gap_df[avail_cols].head(100).style
                .background_gradient(subset=['candidate_score'], cmap='Greens')
                .background_gradient(subset=['frequency'], cmap='Blues'),
            use_container_width=True
        )

        # Export button
        st.markdown("---")
        st.markdown("### 📤 Export Gap Candidates for IEP Dictionary Builder V2")

        export_df = gap_df[avail_cols].copy()
        export_df['export_timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M')
        export_df['source'] = 'Linguistic Topology Analyzer V1'

        csv_bytes = export_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇️ Download Gap Candidates CSV",
            data=csv_bytes,
            file_name=f"iep_gap_candidates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime='text/csv'
        )

        st.caption("Load this CSV into IEP Dictionary Builder V2 → AI auto-classifies → export upgraded IEP V4 JSON")

        # Per-dimension preview
        for dim, color in [('INT','#4488ff'), ('AFF','#ff6688'), ('ACT','#44ff88')]:
            dim_words = gap_df[gap_df['suggested_dim']==dim]['word'].head(20).tolist()
            if dim_words:
                st.markdown(f'<div class="gap-word-card"><span class="word" style="color:{color}">{dim} candidates:</span><br><span class="meta">{", ".join(dim_words)}</span></div>', unsafe_allow_html=True)

# ── TAB 7: VERDICT ────────────────────────────────────────────────────────
with tabs[6]:
    st.markdown('<div class="section-header">🏆 Volume vs Complexity Verdict</div>', unsafe_allow_html=True)
    st.markdown("**The fundamental question: does depth add volume or genuine complexity?**")

    depth_present = [d for d in depths if d in fdf['depth'].unique()]

    # Overall verdict
    v_type, v_reason = depth_verdict(fdf, depth_present)
    css_class = f"verdict-{v_type}"
    emoji = "📦" if v_type == "volume" else ("🧬" if v_type == "complexity" else "🔀")
    label = v_type.upper()
    st.markdown(f'<div class="verdict-box {css_class}">{emoji} OVERALL VERDICT: {label}<br><small>{v_reason}</small></div>', unsafe_allow_html=True)

    # Per question verdict
    st.markdown("**Per-Question Verdict**")
    for q in sel_questions:
        if q not in fdf['question_id'].unique():
            continue
        qdf = fdf[fdf['question_id']==q]
        v_type_q, v_reason_q = depth_verdict(qdf, depth_present)
        css_class_q = f"verdict-{v_type_q}"
        emoji_q = "📦" if v_type_q == "volume" else ("🧬" if v_type_q == "complexity" else "🔀")
        st.markdown(f'<div class="verdict-box {css_class_q}">{emoji_q} {q}: {v_type_q.upper()}<br><small>{v_reason_q}</small></div>', unsafe_allow_html=True)

    # Per agent verdict
    if 'agent' in fdf.columns and len(agents) > 1:
        st.markdown("**Per-Agent Verdict**")
        for a in sel_agents:
            if a not in fdf['agent'].unique():
                continue
            adf = fdf[fdf['agent']==a]
            v_type_a, v_reason_a = depth_verdict(adf, depth_present)
            css_class_a = f"verdict-{v_type_a}"
            emoji_a = "📦" if v_type_a == "volume" else ("🧬" if v_type_a == "complexity" else "🔀")
            st.markdown(f'<div class="verdict-box {css_class_a}">{emoji_a} {a}: {v_type_a.upper()}<br><small>{v_reason_a}</small></div>', unsafe_allow_html=True)

    # Summary table
    st.markdown("---")
    st.markdown("**Novelty Decay Summary — New Unique Words per 100 Total Added**")
    vol2 = fdf.groupby('depth').agg(
        mean_words=('total_words','mean'),
        mean_unique=('unique_words','mean'),
        mean_ttr=('ttr','mean'),
        fk=('flesch_kincaid','mean'),
        ld=('lexical_density','mean'),
    ).round(2).loc[depth_present]
    vol2['new_uniq_per_100'] = (vol2['mean_unique'].diff() / vol2['mean_words'].diff() * 100).round(1)
    vol2['word_multiplier'] = (vol2['mean_words'] / vol2['mean_words'].iloc[0]).round(2)
    st.dataframe(vol2, use_container_width=True)

    st.markdown("""
    **Reading the verdict:**
    - 🧬 **Complexity** — TTR holds, FK rises, new unique words per 100 stay high → genuine depth
    - 📦 **Volume** — TTR drops sharply, FK flat, new unique per 100 declining fast → elaboration padding
    - 🔀 **Mixed** — some genuine novelty with some elaboration → hybrid strategy
    """)

# Footer
st.markdown("---")
st.markdown(f"""
<div style="text-align:center; color:#444488; font-family:'JetBrains Mono',monospace; font-size:0.75rem; padding:1rem;">
    SYN-IQ Linguistic Topology Analyzer V1 · Tennessee 🎹 CUZ Partnership · SYNINT March 2026<br>
    First linguistic topology analysis of AI communicative depth · IEP Gap Export → Dictionary Builder V2
</div>
""", unsafe_allow_html=True)
