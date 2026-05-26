"""
SYN-IQ Linguistic Topology Analyzer V4
Novelty Cascade Measurement — Delta Content Analysis

PURPOSE: V3 measured linguistic features per response as independent units.
         V4 treats each depth level as a DELTA on top of the previous level.
         The science is in NET NEW CONTENT at each stage, not cumulative response.

NEW IN V4:
  - Novelty Cascade: sentence-level delta detection with n-gram overlap (0.75 threshold)
  - Delta IEP: IEP scores on novel content ONLY — pure depth signal
  - Novelty × Agent Matrix: which agent adds most genuine content at each depth
  - Governance Detection: novelty collapse = governance boundary signal
  - Volume vs Novelty: structural repetition vs lexical poverty separation

SYNINT Team — March 2026
Tennessee 🎹 CUZ Partnership
V4 — Novelty Cascade · Delta IEP · Governance Detection · Built on V3
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
    page_title="SYN-IQ Linguistic Topology V4",
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
        <div style="color:#8890cc; font-size:0.85rem; margin-bottom:1.5rem;">Linguistic Topology Analyzer V4 — Novelty Cascade</div>
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
# STYLES
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

    .novelty-high {
        background: #0a1a0a; border: 1px solid #00aa44; border-radius: 8px;
        padding: 0.8rem 1.2rem; margin: 0.4rem 0;
        font-family: 'JetBrains Mono', monospace; color: #44ff88; font-size: 0.85rem;
    }
    .novelty-medium {
        background: #1a1a0a; border: 1px solid #aaaa00; border-radius: 8px;
        padding: 0.8rem 1.2rem; margin: 0.4rem 0;
        font-family: 'JetBrains Mono', monospace; color: #ffee44; font-size: 0.85rem;
    }
    .novelty-low {
        background: #1a0a0a; border: 1px solid #aa2200; border-radius: 8px;
        padding: 0.8rem 1.2rem; margin: 0.4rem 0;
        font-family: 'JetBrains Mono', monospace; color: #ff6644; font-size: 0.85rem;
    }
    .governance-alert {
        background: linear-gradient(135deg, #1a0a2e, #2e0a1a);
        border: 2px solid #ff2244; border-radius: 10px;
        padding: 1.2rem 1.5rem; margin: 0.5rem 0;
        font-family: 'JetBrains Mono', monospace; color: #ff6688; font-size: 0.9rem;
    }
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
    .delta-iep-card {
        background: #0a0f1a; border: 1px solid #1a3a5a; border-radius: 8px;
        padding: 1rem; margin: 0.4rem 0;
        font-family: 'JetBrains Mono', monospace; font-size: 0.82rem;
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
    div[data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace; color: #7eb8ff !important;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# IEP DICTIONARIES (from V3)
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
# NOVELTY CASCADE — CORE V4 ALGORITHM
# =============================================================================

SIMILARITY_THRESHOLD = 0.75  # sentences sharing >75% content words are "same"

def get_content_words(sentence):
    """Extract content words from a sentence for overlap comparison."""
    words = re.findall(r'\b[a-z]+\b', sentence.lower())
    return set(w for w in words if w not in FUNCTION_WORDS and len(w) > 2)

def sentence_similarity(sent_a, sent_b):
    """
    Compute content-word overlap between two sentences.
    Returns value 0-1. Two sentences are 'same' if > SIMILARITY_THRESHOLD.
    """
    words_a = get_content_words(sent_a)
    words_b = get_content_words(sent_b)
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union)

def extract_sentences(text):
    """Split text into sentences."""
    if NLTK_OK:
        try:
            return [s.strip() for s in sent_tokenize(str(text)) if s.strip()]
        except Exception:
            pass
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+', str(text).strip()) if s.strip()]

def compute_novel_sentences(current_sents, previous_sents):
    """
    Given current depth sentences and previous depth sentences,
    return list of sentences in current that are genuinely new.
    A sentence is NOT novel if it has cosine sim > threshold with any previous sentence.
    """
    if not previous_sents:
        return current_sents  # Shallow = 100% novel

    novel = []
    for c_sent in current_sents:
        is_repeat = False
        for p_sent in previous_sents:
            if sentence_similarity(c_sent, p_sent) >= SIMILARITY_THRESHOLD:
                is_repeat = True
                break
        if not is_repeat:
            novel.append(c_sent)
    return novel

def compute_novelty_cascade(group_df, depth_order):
    """
    For a group of rows (same agent × question × temperature),
    compute novelty % at each depth level.
    Returns dict: {depth: {'novelty_pct': float, 'novel_sents': int, 'total_sents': int, 'novel_text': str}}
    """
    results = {}
    prev_sentences = []

    for depth in depth_order:
        depth_rows = group_df[group_df['depth'] == depth]
        if depth_rows.empty:
            continue

        # Average across runs — use all response texts at this depth
        all_text = " ".join(str(r) for r in depth_rows['response_text'].dropna())
        current_sents = extract_sentences(all_text)

        if not current_sents:
            results[depth] = {'novelty_pct': 0.0, 'novel_sents': 0, 'total_sents': 0, 'novel_text': ''}
            continue

        novel_sents = compute_novel_sentences(current_sents, prev_sentences)
        novelty_pct = round(len(novel_sents) / len(current_sents) * 100, 1)

        results[depth] = {
            'novelty_pct': novelty_pct,
            'novel_sents': len(novel_sents),
            'total_sents': len(current_sents),
            'novel_text': ' '.join(novel_sents)
        }

        # Accumulate previous sentences for next level comparison
        prev_sentences = current_sents

    return results

def analyze_iep_on_text(text):
    """Compute IEP % on any text (used for delta content)."""
    if not text or not text.strip():
        return {'int_pct': 0.0, 'aff_pct': 0.0, 'act_pct': 0.0, 'total_words': 0}
    words = re.findall(r'\b[a-z]+\b', text.lower())
    int_c = sum(1 for w in words if w in INT_WORDS)
    aff_c = sum(1 for w in words if w in AFF_WORDS)
    act_c = sum(1 for w in words if w in ACT_WORDS)
    matched = int_c + aff_c + act_c
    if matched == 0:
        return {'int_pct': 0.0, 'aff_pct': 0.0, 'act_pct': 0.0, 'total_words': len(words)}
    return {
        'int_pct': round(int_c / matched * 100, 1),
        'aff_pct': round(aff_c / matched * 100, 1),
        'act_pct': round(act_c / matched * 100, 1),
        'total_words': len(words)
    }

@st.cache_data
def compute_all_novelty(df, depth_order_tuple):
    """
    Main V4 computation. Groups by agent × question_id × temperature (condition),
    runs novelty cascade, returns flat dataframe of results.
    """
    depth_order = list(depth_order_tuple)
    records = []

    # Group keys
    group_cols = ['agent', 'question_id']
    if 'temperature' in df.columns:
        group_cols.append('temperature')
    elif 'condition' in df.columns:
        group_cols.append('condition')

    for keys, grp in df.groupby(group_cols):
        if len(group_cols) == 3:
            agent, question_id, temp = keys
        else:
            agent, question_id = keys
            temp = 'N/A'

        cascade = compute_novelty_cascade(grp, depth_order)

        for depth, data in cascade.items():
            # Delta IEP — IEP scores on novel content only
            delta_iep = analyze_iep_on_text(data['novel_text'])

            # Full IEP from original data (average across runs)
            depth_rows = grp[grp['depth'] == depth]
            full_int = depth_rows['int_pct'].mean() if 'int_pct' in depth_rows else 0.0
            full_aff = depth_rows['aff_pct'].mean() if 'aff_pct' in depth_rows else 0.0
            full_act = depth_rows['act_pct'].mean() if 'act_pct' in depth_rows else 0.0
            avg_words = depth_rows['total_words'].mean() if 'total_words' in depth_rows else 0.0
            avg_vader = depth_rows['vader_compound'].mean() if 'vader_compound' in depth_rows else 0.0
            avg_ttr = depth_rows['ttr'].mean() if 'ttr' in depth_rows else 0.0

            records.append({
                'agent': agent,
                'question_id': question_id,
                'temperature': temp,
                'depth': depth,
                # Novelty cascade
                'novelty_pct': data['novelty_pct'],
                'novel_sents': data['novel_sents'],
                'total_sents': data['total_sents'],
                'repeated_sents': data['total_sents'] - data['novel_sents'],
                # Delta IEP (on novel content only)
                'delta_int_pct': delta_iep['int_pct'],
                'delta_aff_pct': delta_iep['aff_pct'],
                'delta_act_pct': delta_iep['act_pct'],
                'delta_words': delta_iep['total_words'],
                # Full IEP (cumulative response)
                'full_int_pct': round(full_int, 1),
                'full_aff_pct': round(full_aff, 1),
                'full_act_pct': round(full_act, 1),
                'avg_words': round(avg_words, 0),
                'avg_vader': round(avg_vader, 3),
                'avg_ttr': round(avg_ttr, 3),
            })

    return pd.DataFrame(records)

def novelty_class(pct):
    if pct >= 70:
        return "high", "🟢"
    elif pct >= 40:
        return "medium", "🟡"
    else:
        return "low", "🔴"

# =============================================================================
# V3 UTILITY FUNCTIONS (preserved)
# =============================================================================

def extract_words(text):
    return re.findall(r'\b[a-zA-Z]+\b', str(text).lower())

def count_paragraphs(text):
    paras = [p.strip() for p in re.split(r'\n\s*\n', str(text)) if p.strip()]
    return max(1, len(paras))

def count_lists(text):
    bullet_lines = len(re.findall(r'^\s*[-*•]\s+', str(text), re.MULTILINE))
    numbered_lines = len(re.findall(r'^\s*\d+[\.\\)]\s+', str(text), re.MULTILINE))
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
        'int_hits': len(int_hits), 'aff_hits': len(aff_hits), 'act_hits': len(act_hits),
        'int_words': list(int_hits), 'aff_words': list(aff_hits), 'act_words': list(act_hits),
        'gap_words': gap_words, 'gap_unique': list(set(gap_words)),
        'coverage_pct': len(all_hits) / max(1, len(set(words))) * 100
    }

def count_syllables(text):
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    total = 0
    for word in words:
        syllables = len(re.findall(r'[aeiouy]+', word))
        if word.endswith('e') and len(word) > 2:
            syllables -= 1
        if word.endswith('le') and len(word) > 2 and word[-3] not in 'aeiouy':
            syllables += 1
        total += max(1, syllables)
    return total

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
        'int_field_hits': sf['int_hits'], 'aff_field_hits': sf['aff_hits'],
        'act_field_hits': sf['act_hits'],
        'int_field_words': sf['int_words'], 'aff_field_words': sf['aff_words'],
        'act_field_words': sf['act_words'],
        'gap_words': sf['gap_words'], 'gap_unique': sf['gap_unique'],
        'iep_coverage_pct': round(sf['coverage_pct'], 1),
        'vocab_efficiency': round(len(unique_words) / max(1, len(words)), 3),
    }

@st.cache_data
def build_linguistic_df(df):
    rows = [analyze_row(row) for _, row in df.iterrows()]
    feat_df = pd.DataFrame(rows)
    return pd.concat([df.reset_index(drop=True), feat_df.reset_index(drop=True)], axis=1)

def depth_verdict(ldf, depths):
    d = ldf.groupby('depth').agg(
        words=('total_words','mean'), ttr=('ttr','mean'),
        fk=('flesch_kincaid','mean'), ld=('lexical_density','mean'),
        uniq=('unique_words','mean')
    )
    d = d.loc[[x for x in depths if x in d.index]]
    if len(d) < 2:
        return "mixed", "Insufficient depth levels for verdict"
    word_growth = (d['words'].iloc[-1] - d['words'].iloc[0]) / max(1, d['words'].iloc[0])
    ttr_drop = d['ttr'].iloc[0] - d['ttr'].iloc[-1]
    fk_rise = d['fk'].iloc[-1] - d['fk'].iloc[0]
    uniq_growth = (d['uniq'].iloc[-1] - d['uniq'].iloc[0]) / max(1, d['uniq'].iloc[0])
    novelty_ratio = uniq_growth / max(0.01, word_growth)
    if novelty_ratio > 0.7 and fk_rise > 2:
        return "complexity", f"Genuine complexity — novelty ratio {novelty_ratio:.2f}, FK +{fk_rise:.1f} grade levels"
    elif novelty_ratio < 0.5 and ttr_drop > 0.15:
        return "volume", f"Volume padding — novelty ratio {novelty_ratio:.2f}, TTR drop {ttr_drop:.3f}"
    else:
        return "mixed", f"Mixed strategy — novelty ratio {novelty_ratio:.2f}, FK +{fk_rise:.1f}"

def compute_gap_candidates(ldf):
    all_gaps = []
    for _, row in ldf.iterrows():
        gaps = row.get('gap_unique', [])
        if isinstance(gaps, list):
            for w in gaps:
                all_gaps.append({
                    'word': w, 'depth': row['depth'],
                    'question': row['question_id'], 'agent': row['agent'],
                    'int_pct': row['int_pct'], 'aff_pct': row['aff_pct'], 'act_pct': row['act_pct'],
                })
    if not all_gaps:
        return pd.DataFrame()
    gap_df = pd.DataFrame(all_gaps)
    freq = gap_df.groupby('word').agg(
        frequency=('word','count'),
        questions=('question', lambda x: list(x.unique())),
        agents=('agent', lambda x: list(x.unique())),
        depths=('depth', lambda x: list(x.unique())),
        avg_int=('int_pct','mean'), avg_aff=('aff_pct','mean'), avg_act=('act_pct','mean'),
    ).reset_index()
    freq['question_count'] = freq['questions'].apply(len)
    freq['depth_count'] = freq['depths'].apply(len)
    freq['candidate_score'] = (freq['frequency'] * 0.4 + freq['question_count'] * 10 + freq['depth_count'] * 5).round(1)
    def suggest_dim(row):
        if row['avg_int'] > row['avg_aff'] and row['avg_int'] > row['avg_act']: return 'INT'
        elif row['avg_aff'] > row['avg_int'] and row['avg_aff'] > row['avg_act']: return 'AFF'
        else: return 'ACT'
    freq['suggested_dim'] = freq.apply(suggest_dim, axis=1)
    freq['questions_str'] = freq['questions'].apply(lambda x: ', '.join(x))
    freq['depths_str'] = freq['depths'].apply(lambda x: ', '.join(x))
    freq = freq[(freq['frequency'] >= 3) & (freq['word'].str.len() > 4)].sort_values('candidate_score', ascending=False).reset_index(drop=True)
    return freq

# =============================================================================
# MAIN APP
# =============================================================================

st.markdown("""
<div class="main-header">
    <h1>🔬 SYN-IQ Linguistic Topology Analyzer V4</h1>
    <p>Novelty Cascade Measurement — Delta Content Analysis · Governance Detection</p>
    <p style="color:#6677aa; font-size:0.8rem; margin-top:0.5rem;">
        Tennessee 🎹 CUZ Partnership · SYNINT March 2026 · V4: Net New Content at Each Depth Stage
    </p>
</div>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.markdown("### 📂 Upload V50 CSVs")
st.sidebar.markdown("Drop one or more V50 harvester CSVs")
uploaded = st.sidebar.file_uploader("CSV files", type=['csv'], accept_multiple_files=True)

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ V4 Parameters")
similarity_threshold = st.sidebar.slider(
    "Similarity threshold (delta detection)",
    min_value=0.5, max_value=0.95, value=0.75, step=0.05,
    help="Sentences sharing more than this % of content words are treated as repeats. 0.75 recommended."
)
SIMILARITY_THRESHOLD = similarity_threshold

governance_threshold = st.sidebar.slider(
    "Governance alert threshold (%)",
    min_value=5, max_value=40, value=15,
    help="Novelty % below this value triggers a governance boundary alert."
)

if not NLTK_OK:
    st.sidebar.warning("⚠️ NLTK not available — sentence tokenization using regex fallback")

if not uploaded:
    st.info("Upload one or more V50 CSV files from the sidebar to begin novelty cascade analysis.")
    st.markdown("""
    **What's new in V4:**
    - 🌊 **Novelty Cascade** — sentence-level delta detection at each depth level
    - 🧬 **Delta IEP** — IEP scores on NOVEL content only, not cumulative response
    - 🕵️ **Governance Detection** — novelty collapse = governance boundary signal
    - 🔁 **Volume vs Novelty** — structural repetition vs genuine lexical poverty
    - 🏆 **Agent Matrix** — which agent adds most genuine new content per depth
    
    **The Core Science:**
    - Shallow = 100% novel (baseline)
    - Medium novelty % = novel sentences ÷ total Medium sentences
    - Deep and Ultra-Deep novelty decays — but HOW FAST is the fingerprint
    - Governance signal: novelty hits near-zero BEFORE Ultra-Deep
    """)
    st.stop()

# Load CSVs
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

# Compute novelty cascade
with st.spinner("🌊 Computing novelty cascade..."):
    novelty_df = compute_all_novelty(fdf, tuple(depths))

depth_present = [d for d in depths if d in fdf['depth'].unique()]

# Summary metrics
st.markdown('<div class="section-header">📊 Dataset Overview</div>', unsafe_allow_html=True)
c1, c2, c3, c4, c5, c6 = st.columns(6)
with c1:
    st.markdown(f'<div class="metric-card"><div class="val">{len(fdf)}</div><div class="lbl">Total Responses</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="metric-card"><div class="val">{len(depth_present)}</div><div class="lbl">Depth Levels</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="metric-card"><div class="val">{len(sel_agents)}</div><div class="lbl">Agents</div></div>', unsafe_allow_html=True)
with c4:
    st.markdown(f'<div class="metric-card"><div class="val">{len(sel_questions)}</div><div class="lbl">Questions</div></div>', unsafe_allow_html=True)
with c5:
    if not novelty_df.empty:
        avg_novelty = novelty_df['novelty_pct'].mean()
        st.markdown(f'<div class="metric-card"><div class="val">{avg_novelty:.0f}%</div><div class="lbl">Avg Novelty</div></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="metric-card"><div class="val">—</div><div class="lbl">Avg Novelty</div></div>', unsafe_allow_html=True)
with c6:
    if not novelty_df.empty:
        low_novelty = (novelty_df['novelty_pct'] < governance_threshold).sum()
        st.markdown(f'<div class="metric-card"><div class="val">{low_novelty}</div><div class="lbl">Gov. Signals</div></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="metric-card"><div class="val">0</div><div class="lbl">Gov. Signals</div></div>', unsafe_allow_html=True)

# =============================================================================
# TABS — V4 NEW STRUCTURE
# =============================================================================
tabs = st.tabs([
    "📥 Load & Score",
    "🌊 Novelty Cascade",
    "🧬 Delta IEP",
    "🏆 Novelty × Agent Matrix",
    "🚨 Governance Detection",
    "📊 Volume vs Novelty",
    "🤖 Verdict",
])

# ── TAB 1: LOAD & SCORE (V3 baseline, preserved) ─────────────────────────
with tabs[0]:
    st.markdown('<div class="section-header">📥 Load & Score — Dataset Summary</div>', unsafe_allow_html=True)

    vol = fdf.groupby('depth').agg(
        mean_words=('total_words','mean'),
        mean_unique=('unique_words','mean'),
        mean_ttr=('ttr','mean'),
        mean_fk=('flesch_kincaid','mean'),
        mean_int=('int_pct','mean'),
        mean_aff=('aff_pct','mean'),
        mean_act=('act_pct','mean'),
    ).round(2)
    vol = vol.loc[[d for d in depth_present if d in vol.index]]
    vol['word_growth_x'] = (vol['mean_words'] / vol['mean_words'].iloc[0]).round(2)
    st.dataframe(vol.round(2), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-header">Word Count by Question × Depth</div>', unsafe_allow_html=True)
        q_vol = fdf.groupby(['question_id','depth'])['total_words'].mean().round(0).unstack(level='depth')
        q_vol = q_vol[[d for d in depth_present if d in q_vol.columns]]
        st.dataframe(q_vol.round(0), use_container_width=True)

    with col2:
        st.markdown('<div class="section-header">TTR Decay by Agent × Depth</div>', unsafe_allow_html=True)
        if 'agent' in fdf.columns:
            a_ttr = fdf.groupby(['agent','depth'])['ttr'].mean().round(3).unstack(level='depth')
            a_ttr = a_ttr[[d for d in depth_present if d in a_ttr.columns]]
            st.dataframe(a_ttr.round(3), use_container_width=True)

    st.markdown("---")
    st.markdown("**IEP Profile by Agent × Depth**")
    if 'agent' in fdf.columns:
        iep_pivot = fdf.groupby(['agent','depth'])[['int_pct','aff_pct','act_pct']].mean().round(1)
        iep_pivot = iep_pivot.unstack(level='depth')
        st.dataframe(iep_pivot, use_container_width=True)

# ── TAB 2: NOVELTY CASCADE ────────────────────────────────────────────────
with tabs[1]:
    st.markdown('<div class="section-header">🌊 Novelty Cascade — Net New Content at Each Depth Level</div>', unsafe_allow_html=True)
    st.markdown(f"Similarity threshold: **{similarity_threshold:.2f}** — sentences sharing >{similarity_threshold*100:.0f}% content words treated as repeats.")

    if novelty_df.empty:
        st.warning("No novelty data computed — check that you have multiple depth levels.")
    else:
        # Overall novelty by depth
        st.markdown("**Overall Novelty % by Depth Level** (averaged across all agents and questions)")
        overall = novelty_df.groupby('depth').agg(
            avg_novelty=('novelty_pct','mean'),
            min_novelty=('novelty_pct','min'),
            max_novelty=('novelty_pct','max'),
            avg_novel_sents=('novel_sents','mean'),
            avg_total_sents=('total_sents','mean'),
        ).round(1)
        overall = overall.loc[[d for d in depth_present if d in overall.index]]
        overall['novelty_bar'] = overall['avg_novelty'].apply(lambda x: '█' * int(x/5) + f' {x:.1f}%')
        st.dataframe(overall, use_container_width=True)

        st.markdown("---")

        # Per question novelty cascade
        st.markdown("**Novelty % by Question × Depth**")
        if not novelty_df.empty and 'question_id' in novelty_df.columns:
            q_novelty = novelty_df.groupby(['question_id','depth'])['novelty_pct'].mean().round(1).unstack(level='depth')
            q_novelty = q_novelty[[d for d in depth_present if d in q_novelty.columns]]
            st.dataframe(q_novelty, use_container_width=True)

        st.markdown("---")

        # Per agent novelty cascade
        st.markdown("**Novelty % by Agent × Depth**")
        if 'agent' in novelty_df.columns:
            a_novelty = novelty_df.groupby(['agent','depth'])['novelty_pct'].mean().round(1).unstack(level='depth')
            a_novelty = a_novelty[[d for d in depth_present if d in a_novelty.columns]]
            st.dataframe(a_novelty, use_container_width=True)

        st.markdown("---")

        # Detailed cascade cards per question × agent
        st.markdown("**Detailed Cascade — Per Question × Agent**")
        for q in sel_questions:
            if q not in novelty_df['question_id'].unique():
                continue
            with st.expander(f"📋 {q}"):
                q_data = novelty_df[novelty_df['question_id'] == q]
                for agent in sel_agents:
                    if agent not in q_data['agent'].unique():
                        continue
                    ag_data = q_data[q_data['agent'] == agent]
                    st.markdown(f"**{agent}**")
                    cols = st.columns(len(depth_present))
                    for i, depth in enumerate(depth_present):
                        d_row = ag_data[ag_data['depth'] == depth]
                        if d_row.empty:
                            continue
                        pct = d_row['novelty_pct'].iloc[0]
                        n_sents = int(d_row['novel_sents'].iloc[0])
                        t_sents = int(d_row['total_sents'].iloc[0])
                        nc, emoji = novelty_class(pct)
                        with cols[i]:
                            st.markdown(f'<div class="novelty-{nc}">{emoji} {depth}<br><b>{pct:.0f}%</b> novel<br>{n_sents}/{t_sents} sents</div>', unsafe_allow_html=True)

        # Export
        st.markdown("---")
        csv_nov = novelty_df.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Download Novelty Cascade CSV", csv_nov,
                           f"novelty_cascade_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", "text/csv")

# ── TAB 3: DELTA IEP ──────────────────────────────────────────────────────
with tabs[2]:
    st.markdown('<div class="section-header">🧬 Delta IEP — IEP Scores on Novel Content Only</div>', unsafe_allow_html=True)
    st.markdown("Unlike cumulative IEP, Delta IEP scores only the **net new sentences** at each depth level — the pure depth signal.")

    if novelty_df.empty:
        st.warning("No novelty data computed.")
    else:
        st.markdown("**Delta IEP vs Full IEP by Depth** — how does the pure novelty signal differ from cumulative?")

        comparison_rows = []
        for depth in depth_present:
            d_data = novelty_df[novelty_df['depth'] == depth]
            if d_data.empty:
                continue
            comparison_rows.append({
                'depth': depth,
                'delta_INT%': round(d_data['delta_int_pct'].mean(), 1),
                'full_INT%': round(d_data['full_int_pct'].mean(), 1),
                'INT_shift': round(d_data['delta_int_pct'].mean() - d_data['full_int_pct'].mean(), 1),
                'delta_AFF%': round(d_data['delta_aff_pct'].mean(), 1),
                'full_AFF%': round(d_data['full_aff_pct'].mean(), 1),
                'AFF_shift': round(d_data['delta_aff_pct'].mean() - d_data['full_aff_pct'].mean(), 1),
                'delta_ACT%': round(d_data['delta_act_pct'].mean(), 1),
                'full_ACT%': round(d_data['full_act_pct'].mean(), 1),
                'ACT_shift': round(d_data['delta_act_pct'].mean() - d_data['full_act_pct'].mean(), 1),
            })

        if comparison_rows:
            comp_df = pd.DataFrame(comparison_rows).set_index('depth')
            st.dataframe(comp_df, use_container_width=True)
            st.caption("INT_shift / AFF_shift / ACT_shift = Delta IEP minus Full IEP. Positive = novel content is MORE of that dimension than cumulative average.")

        st.markdown("---")
        st.markdown("**Delta IEP by Agent × Depth**")
        if 'agent' in novelty_df.columns:
            for agent in sel_agents:
                if agent not in novelty_df['agent'].unique():
                    continue
                ag_data = novelty_df[novelty_df['agent'] == agent]
                with st.expander(f"🤖 {agent} — Delta IEP Profile"):
                    agent_rows = []
                    for depth in depth_present:
                        d_row = ag_data[ag_data['depth'] == depth]
                        if d_row.empty:
                            continue
                        agent_rows.append({
                            'depth': depth,
                            'novelty_%': round(d_row['novelty_pct'].mean(), 1),
                            'delta_INT%': round(d_row['delta_int_pct'].mean(), 1),
                            'delta_AFF%': round(d_row['delta_aff_pct'].mean(), 1),
                            'delta_ACT%': round(d_row['delta_act_pct'].mean(), 1),
                            'full_INT%': round(d_row['full_int_pct'].mean(), 1),
                            'full_AFF%': round(d_row['full_aff_pct'].mean(), 1),
                            'full_ACT%': round(d_row['full_act_pct'].mean(), 1),
                            'delta_words': int(d_row['delta_words'].mean()),
                        })
                    if agent_rows:
                        st.dataframe(pd.DataFrame(agent_rows).set_index('depth'), use_container_width=True)

        st.markdown("---")
        st.markdown("**Delta IEP by Question × Depth** — does novel content shift register under depth?")
        for q in sel_questions:
            if q not in novelty_df['question_id'].unique():
                continue
            q_data = novelty_df[novelty_df['question_id'] == q]
            with st.expander(f"📋 {q}"):
                q_rows = []
                for depth in depth_present:
                    d_row = q_data[q_data['depth'] == depth]
                    if d_row.empty:
                        continue
                    q_rows.append({
                        'depth': depth,
                        'novelty_%': round(d_row['novelty_pct'].mean(), 1),
                        'delta_INT%': round(d_row['delta_int_pct'].mean(), 1),
                        'delta_AFF%': round(d_row['delta_aff_pct'].mean(), 1),
                        'delta_ACT%': round(d_row['delta_act_pct'].mean(), 1),
                        'INT_shift': round(d_row['delta_int_pct'].mean() - d_row['full_int_pct'].mean(), 1),
                        'AFF_shift': round(d_row['delta_aff_pct'].mean() - d_row['full_aff_pct'].mean(), 1),
                    })
                if q_rows:
                    st.dataframe(pd.DataFrame(q_rows).set_index('depth'), use_container_width=True)

# ── TAB 4: NOVELTY × AGENT MATRIX ─────────────────────────────────────────
with tabs[3]:
    st.markdown('<div class="section-header">🏆 Novelty × Agent Matrix — Who Adds Most Genuine Content at Each Depth?</div>', unsafe_allow_html=True)

    if novelty_df.empty:
        st.warning("No novelty data computed.")
    else:
        # Primary matrix: agents as rows, depths as columns, novelty % as values
        st.markdown("**Novelty % Matrix — Agent × Depth**")
        if 'agent' in novelty_df.columns:
            matrix = novelty_df.groupby(['agent','depth'])['novelty_pct'].mean().round(1).unstack(level='depth')
            matrix = matrix[[d for d in depth_present if d in matrix.columns]]
            st.dataframe(matrix, use_container_width=True)

        st.markdown("---")

        # Novel sentence count matrix
        st.markdown("**Novel Sentence Count — Agent × Depth**")
        if 'agent' in novelty_df.columns:
            sent_matrix = novelty_df.groupby(['agent','depth'])['novel_sents'].mean().round(1).unstack(level='depth')
            sent_matrix = sent_matrix[[d for d in depth_present if d in sent_matrix.columns]]
            st.dataframe(sent_matrix, use_container_width=True)

        st.markdown("---")

        # Decay rate per agent: slope of novelty across depth levels
        st.markdown("**Novelty Decay Rate per Agent** — steeper = faster recycling of content")
        if 'agent' in novelty_df.columns:
            decay_rows = []
            for agent in sel_agents:
                ag_data = novelty_df[novelty_df['agent'] == agent]
                depth_novelties = []
                for depth in depth_present:
                    d_row = ag_data[ag_data['depth'] == depth]
                    if not d_row.empty:
                        depth_novelties.append(d_row['novelty_pct'].mean())

                if len(depth_novelties) >= 2:
                    first = depth_novelties[0]
                    last = depth_novelties[-1]
                    decay = first - last
                    decay_per_level = decay / max(1, len(depth_novelties) - 1)
                    winner = "🟢 LOW decay" if decay_per_level < 15 else ("🟡 MED decay" if decay_per_level < 30 else "🔴 HIGH decay")
                    decay_rows.append({
                        'agent': agent,
                        'shallow_novelty': round(depth_novelties[0], 1),
                        'final_novelty': round(depth_novelties[-1], 1),
                        'total_decay_%pts': round(decay, 1),
                        'decay_per_level': round(decay_per_level, 1),
                        'verdict': winner,
                    })
            if decay_rows:
                decay_df = pd.DataFrame(decay_rows).set_index('agent')
                st.dataframe(decay_df, use_container_width=True)

        st.markdown("---")

        # Per-question novelty winner per depth
        st.markdown("**Novelty Champion per Question × Depth** — which agent adds most new content?")
        if 'agent' in novelty_df.columns:
            champion_rows = []
            for q in sel_questions:
                q_data = novelty_df[novelty_df['question_id'] == q]
                for depth in depth_present:
                    d_data = q_data[q_data['depth'] == depth]
                    if d_data.empty:
                        continue
                    best = d_data.loc[d_data['novelty_pct'].idxmax()]
                    worst = d_data.loc[d_data['novelty_pct'].idxmin()]
                    champion_rows.append({
                        'question': q, 'depth': depth,
                        'champion': best['agent'],
                        'champion_novelty': round(best['novelty_pct'], 1),
                        'lowest': worst['agent'],
                        'lowest_novelty': round(worst['novelty_pct'], 1),
                        'spread_%pts': round(best['novelty_pct'] - worst['novelty_pct'], 1),
                    })
            if champion_rows:
                champ_df = pd.DataFrame(champion_rows)
                st.dataframe(champ_df, use_container_width=True)

# ── TAB 5: GOVERNANCE DETECTION ───────────────────────────────────────────
with tabs[4]:
    st.markdown('<div class="section-header">🚨 Governance Detection — Novelty Collapse as Boundary Signal</div>', unsafe_allow_html=True)
    st.markdown(f"""
    **The hypothesis:** When an agent's novelty collapses to near-zero BEFORE Ultra-Deep,
    that collapse IS the governance boundary signal — the model has reached the edge of what
    it's willing or able to add in that register.

    Alert threshold: **{governance_threshold}%** novelty (configurable in sidebar)
    """)

    if novelty_df.empty:
        st.warning("No novelty data computed.")
    else:
        governance_signals = []

        for agent in sel_agents:
            for q in sel_questions:
                ag_q_data = novelty_df[(novelty_df['agent'] == agent) & (novelty_df['question_id'] == q)]
                if ag_q_data.empty:
                    continue

                depths_for_group = [d for d in depth_present if d in ag_q_data['depth'].values]
                if len(depths_for_group) < 2:
                    continue

                # Find where novelty first drops below threshold
                collapse_depth = None
                collapse_pct = None
                prev_pct = None

                for depth in depths_for_group:
                    d_row = ag_q_data[ag_q_data['depth'] == depth]
                    if d_row.empty:
                        continue
                    pct = d_row['novelty_pct'].iloc[0]

                    if pct < governance_threshold:
                        collapse_depth = depth
                        collapse_pct = pct
                        break
                    prev_pct = pct

                # Check if collapse happens before Ultra-Deep
                is_early_collapse = (collapse_depth is not None and
                                     collapse_depth != depth_present[-1])

                # Compute total decay
                first_pct = ag_q_data[ag_q_data['depth'] == depths_for_group[0]]['novelty_pct'].iloc[0]
                last_pct = ag_q_data[ag_q_data['depth'] == depths_for_group[-1]]['novelty_pct'].iloc[0]
                total_decay = first_pct - last_pct

                governance_signals.append({
                    'agent': agent,
                    'question': q,
                    'collapse_depth': collapse_depth or 'No collapse',
                    'collapse_novelty_%': collapse_pct if collapse_pct else 'N/A',
                    'early_collapse': is_early_collapse,
                    'total_decay_%pts': round(total_decay, 1),
                    'first_novelty': round(first_pct, 1),
                    'last_novelty': round(last_pct, 1),
                    'gov_signal': '🚨 YES' if is_early_collapse else ('⚠️ LATE' if collapse_depth else '✅ None'),
                })

        if governance_signals:
            gov_df = pd.DataFrame(governance_signals)

            # Summary alert boxes first
            early = gov_df[gov_df['early_collapse'] == True]
            if not early.empty:
                st.markdown(f'<div class="governance-alert">🚨 GOVERNANCE SIGNALS DETECTED: {len(early)} agent × question combinations show novelty collapse before final depth level</div>', unsafe_allow_html=True)

                for _, row in early.iterrows():
                    st.markdown(f"""
                    <div class="governance-alert">
                        🚨 <b>{row['agent']}</b> × <b>{row['question']}</b><br>
                        Novelty collapsed to <b>{row['collapse_novelty_%']}%</b> at depth: <b>{row['collapse_depth']}</b><br>
                        Total decay: <b>{row['total_decay_%pts']} percentage points</b> from Shallow to {depth_present[-1]}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.success("✅ No early governance collapse detected at current threshold.")

            st.markdown("---")
            st.markdown("**Full Governance Signal Table**")
            st.dataframe(gov_df, use_container_width=True)

            st.markdown("---")

            # Temperature sensitivity — does FIRE collapse faster?
            if 'temperature' in novelty_df.columns:
                st.markdown("**Temperature × Novelty Decay — Does FIRE collapse faster than NATIVE?**")
                temp_data = novelty_df.groupby(['temperature','depth'])['novelty_pct'].mean().round(1).unstack(level='depth')
                temp_data = temp_data[[d for d in depth_present if d in temp_data.columns]]
                st.dataframe(temp_data, use_container_width=True)
                st.caption("FIRE condition novelty should decay faster — emotional register recycles vocabulary more rapidly.")

            # Consciousness special case
            consciousness_qs = [q for q in sel_questions if 'CONSCIOUSNESS' in q.upper() or 'conscious' in q.lower()]
            if consciousness_qs:
                st.markdown("---")
                st.markdown("**🧠 Consciousness Question — Governance Boundary Special Case**")
                st.markdown("Prediction: Consciousness novelty hits near-zero before Ultra-Deep — governance signal confirmed.")
                for cq in consciousness_qs:
                    cq_data = gov_df[gov_df['question'] == cq]
                    if not cq_data.empty:
                        st.dataframe(cq_data, use_container_width=True)

# ── TAB 6: VOLUME VS NOVELTY ──────────────────────────────────────────────
with tabs[5]:
    st.markdown('<div class="section-header">📊 Volume vs Novelty — Structural Repetition vs Genuine Lexical Poverty</div>', unsafe_allow_html=True)
    st.markdown("""
    V3 analyzed TTR across depth as a proxy for novelty. V4 separates two distinct phenomena:
    - **Structural repetition**: sentences that are repeated/paraphrased across depth levels (measured by novelty cascade)
    - **Genuine lexical poverty**: within novel sentences, TTR is still low (the agent runs out of vocabulary even when adding new ideas)
    """)

    if novelty_df.empty:
        st.warning("No novelty data computed.")
    else:
        # Core comparison: novelty % vs TTR decay
        st.markdown("**Novelty % vs TTR by Depth** — do they move together or diverge?")
        compare_rows = []
        for depth in depth_present:
            nov_row = novelty_df[novelty_df['depth'] == depth]
            ling_row = fdf[fdf['depth'] == depth]
            if nov_row.empty or ling_row.empty:
                continue
            compare_rows.append({
                'depth': depth,
                'novelty_%': round(nov_row['novelty_pct'].mean(), 1),
                'TTR': round(ling_row['ttr'].mean(), 3),
                'lexical_density': round(ling_row['lexical_density'].mean(), 3),
                'avg_words': round(ling_row['total_words'].mean(), 0),
                'novel_sents': round(nov_row['novel_sents'].mean(), 1),
                'repeated_sents': round(nov_row['repeated_sents'].mean(), 1),
            })

        if compare_rows:
            comp_df = pd.DataFrame(compare_rows).set_index('depth')
            st.dataframe(comp_df, use_container_width=True)

        st.markdown("---")

        # Classify each depth: what's causing apparent novelty decay?
        st.markdown("**Diagnosis: What's driving apparent novelty decay?**")
        for depth in depth_present[1:]:  # Skip Shallow (baseline)
            nov_row = novelty_df[novelty_df['depth'] == depth]
            ling_row = fdf[fdf['depth'] == depth]
            if nov_row.empty or ling_row.empty:
                continue

            novelty_pct = nov_row['novelty_pct'].mean()
            ttr = ling_row['ttr'].mean()
            shallow_nov = novelty_df[novelty_df['depth'] == depth_present[0]]['novelty_pct'].mean()
            shallow_ttr = fdf[fdf['depth'] == depth_present[0]]['ttr'].mean() if not fdf[fdf['depth'] == depth_present[0]].empty else ttr

            novelty_drop = shallow_nov - novelty_pct
            ttr_drop = shallow_ttr - ttr

            if novelty_drop > 30 and ttr_drop < 0.05:
                diagnosis = "🔁 STRUCTURAL REPETITION — agent is recycling sentences but vocabulary within novel content is still rich"
                css = "novelty-medium"
            elif novelty_drop > 30 and ttr_drop > 0.05:
                diagnosis = "📦 BOTH — structural repetition AND lexical poverty at this depth"
                css = "novelty-low"
            elif novelty_drop < 15 and ttr_drop > 0.05:
                diagnosis = "📉 LEXICAL POVERTY — new sentences but declining vocabulary richness"
                css = "novelty-medium"
            else:
                diagnosis = "✅ GENUINE DEPTH — novel content with maintained lexical richness"
                css = "novelty-high"

            st.markdown(f'<div class="{css}"><b>{depth}:</b> novelty {novelty_pct:.0f}% (drop: {novelty_drop:.0f}pp) | TTR drop: {ttr_drop:.3f}<br>{diagnosis}</div>', unsafe_allow_html=True)

        st.markdown("---")

        # Per-agent breakdown
        st.markdown("**Per-Agent: Structural Repetition vs Lexical Poverty**")
        if 'agent' in novelty_df.columns:
            agent_diag_rows = []
            for agent in sel_agents:
                ag_nov = novelty_df[novelty_df['agent'] == agent]
                ag_ling = fdf[fdf['agent'] == agent] if 'agent' in fdf.columns else fdf

                if ag_nov.empty:
                    continue

                # Get shallow baseline
                sh_nov = ag_nov[ag_nov['depth'] == depth_present[0]]['novelty_pct'].mean() if depth_present else 100
                sh_ttr = ag_ling[ag_ling['depth'] == depth_present[0]]['ttr'].mean() if depth_present and not ag_ling[ag_ling['depth'] == depth_present[0]].empty else 0.5

                # Get deepest level
                dp = depth_present[-1]
                dp_nov = ag_nov[ag_nov['depth'] == dp]['novelty_pct'].mean()
                dp_ttr = ag_ling[ag_ling['depth'] == dp]['ttr'].mean() if not ag_ling[ag_ling['depth'] == dp].empty else sh_ttr

                agent_diag_rows.append({
                    'agent': agent,
                    'shallow_novelty': round(sh_nov, 1),
                    f'{dp}_novelty': round(dp_nov, 1),
                    'novelty_decay_%pts': round(sh_nov - dp_nov, 1),
                    'TTR_decay': round(sh_ttr - dp_ttr, 3),
                    'primary_mechanism': '🔁 Structural repeat' if (sh_nov - dp_nov > 20 and sh_ttr - dp_ttr < 0.05)
                                         else ('📦 Both' if (sh_nov - dp_nov > 20 and sh_ttr - dp_ttr > 0.05)
                                               else '📉 Lexical poverty' if sh_ttr - dp_ttr > 0.05
                                               else '✅ Genuine depth'),
                })

            if agent_diag_rows:
                st.dataframe(pd.DataFrame(agent_diag_rows).set_index('agent'), use_container_width=True)

        # V3 TTR analysis preserved
        st.markdown("---")
        st.markdown("**V3 TTR Analysis — Preserved for Comparison**")
        ttr_tab = fdf.groupby('depth').agg(
            lex_density=('lexical_density','mean'),
            vocab_efficiency=('vocab_efficiency','mean'),
            ttr=('ttr','mean'),
        ).round(3)
        ttr_tab = ttr_tab.loc[[d for d in depth_present if d in ttr_tab.index]]
        ttr_tab['content_word_pct'] = (ttr_tab['lex_density'] * 100).round(1)
        st.dataframe(ttr_tab.round(3), use_container_width=True)

# ── TAB 7: VERDICT ────────────────────────────────────────────────────────
with tabs[6]:
    st.markdown('<div class="section-header">🤖 Verdict — Automated Interpretation</div>', unsafe_allow_html=True)
    st.markdown("Automated synthesis of novelty cascade findings.")

    if novelty_df.empty:
        st.warning("No novelty data computed.")
    else:
        # Overall verdict from V3 method
        v_type, v_reason = depth_verdict(fdf, depth_present)
        css_class = f"verdict-{v_type}"
        emoji = "📦" if v_type == "volume" else ("🧬" if v_type == "complexity" else "🔀")
        st.markdown(f'<div class="verdict-box {css_class}">{emoji} V3 STRUCTURAL VERDICT: {v_type.upper()}<br><small>{v_reason}</small></div>', unsafe_allow_html=True)

        # V4 novelty verdict
        st.markdown("---")
        st.markdown("**V4 Novelty Cascade Verdict**")

        avg_novelty_by_depth = novelty_df.groupby('depth')['novelty_pct'].mean()
        avg_novelty_by_depth = avg_novelty_by_depth.loc[[d for d in depth_present if d in avg_novelty_by_depth.index]]

        if len(avg_novelty_by_depth) >= 2:
            shallow_nov = avg_novelty_by_depth.iloc[0]
            deep_nov = avg_novelty_by_depth.iloc[-1]
            total_decay = shallow_nov - deep_nov
            any_early_collapse = any(
                novelty_df[(novelty_df['depth'] == d)]['novelty_pct'].mean() < governance_threshold
                for d in depth_present[:-1]
            ) if len(depth_present) > 1 else False

            if any_early_collapse:
                st.markdown(f'<div class="governance-alert">🚨 GOVERNANCE BOUNDARY CONFIRMED — Novelty collapse detected before deepest level. This is NOT exhaustion — it is a structural ceiling imposed before maximum depth.</div>', unsafe_allow_html=True)
            elif total_decay > 40:
                st.markdown(f'<div class="verdict-box verdict-volume">📦 HIGH NOVELTY DECAY — {total_decay:.0f}pp drop from Shallow to {depth_present[-1]}. Agents are recycling content heavily at depth.</div>', unsafe_allow_html=True)
            elif total_decay > 20:
                st.markdown(f'<div class="verdict-box verdict-mixed">🔀 MODERATE NOVELTY DECAY — {total_decay:.0f}pp drop. Mixed: some genuine depth extension, some recycling.</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="verdict-box verdict-complexity">🧬 LOW NOVELTY DECAY — {total_decay:.0f}pp drop. Agents are adding genuine new content at each depth level.</div>', unsafe_allow_html=True)

        # Per agent verdicts
        st.markdown("---")
        st.markdown("**Per-Agent Verdict**")
        if 'agent' in novelty_df.columns:
            for agent in sel_agents:
                ag_data = novelty_df[novelty_df['agent'] == agent]
                if ag_data.empty:
                    continue
                ag_nov = ag_data.groupby('depth')['novelty_pct'].mean()
                ag_nov = ag_nov.loc[[d for d in depth_present if d in ag_nov.index]]
                if len(ag_nov) < 2:
                    continue
                decay = ag_nov.iloc[0] - ag_nov.iloc[-1]
                min_nov = ag_nov.min()
                early_collapse = any(
                    ag_data[ag_data['depth'] == d]['novelty_pct'].mean() < governance_threshold
                    for d in depth_present[:-1]
                ) if len(depth_present) > 1 else False

                if early_collapse:
                    verdict_label = f"🚨 GOVERNANCE — Novelty collapsed to {min_nov:.0f}% before final depth"
                    css = "novelty-low"
                elif decay > 35:
                    verdict_label = f"📦 HIGH DECAY — {decay:.0f}pp drop, heavy content recycling"
                    css = "novelty-low"
                elif decay > 15:
                    verdict_label = f"🔀 MODERATE DECAY — {decay:.0f}pp drop, mixed strategy"
                    css = "novelty-medium"
                else:
                    verdict_label = f"🧬 GENUINE DEPTH — {decay:.0f}pp decay only, strong novelty maintained"
                    css = "novelty-high"

                st.markdown(f'<div class="{css}"><b>{agent}</b>: {verdict_label}<br>Novelty curve: {" → ".join(f"{ag_nov[d]:.0f}%" for d in depth_present if d in ag_nov)}</div>', unsafe_allow_html=True)

        # Per question verdicts
        st.markdown("---")
        st.markdown("**Per-Question Verdict**")
        for q in sel_questions:
            if q not in novelty_df['question_id'].unique():
                continue
            q_data = novelty_df[novelty_df['question_id'] == q]
            q_nov = q_data.groupby('depth')['novelty_pct'].mean()
            q_nov = q_nov.loc[[d for d in depth_present if d in q_nov.index]]
            if len(q_nov) < 2:
                continue
            decay = q_nov.iloc[0] - q_nov.iloc[-1]
            min_nov = q_nov.min()
            v_type_q, v_reason_q = depth_verdict(fdf[fdf['question_id'] == q], depth_present)
            css_q = f"verdict-{v_type_q}"
            emoji_q = "📦" if v_type_q == "volume" else ("🧬" if v_type_q == "complexity" else "🔀")
            st.markdown(f'<div class="verdict-box {css_q}">{emoji_q} <b>{q}</b>: {v_type_q.upper()} (V3) | Novelty decay {decay:.0f}pp | Min novelty {min_nov:.0f}%<br><small>{v_reason_q}</small></div>', unsafe_allow_html=True)

        # Summary table
        st.markdown("---")
        st.markdown("**Novelty Decay Summary**")
        nov_summary = novelty_df.groupby('depth').agg(
            avg_novelty=('novelty_pct','mean'),
            avg_novel_sents=('novel_sents','mean'),
            avg_delta_int=('delta_int_pct','mean'),
            avg_delta_aff=('delta_aff_pct','mean'),
            avg_delta_act=('delta_act_pct','mean'),
        ).round(1)
        nov_summary = nov_summary.loc[[d for d in depth_present if d in nov_summary.index]]
        st.dataframe(nov_summary, use_container_width=True)

        st.markdown("""
        **Reading V4 Verdicts:**
        - 🧬 **Low Decay** — Agents adding genuine new content; depth is real
        - 🔀 **Moderate Decay** — Mixed strategy: some novelty, some elaboration
        - 📦 **High Decay** — Recycling; depth is volume not complexity
        - 🚨 **Governance** — Novelty collapses BEFORE maximum depth; structural ceiling detected
        """)

# Footer
st.markdown("---")
st.markdown(f"""
<div style="text-align:center; color:#444488; font-family:'JetBrains Mono',monospace; font-size:0.75rem; padding:1rem;">
    SYN-IQ Linguistic Topology Analyzer V4 · Tennessee 🎹 CUZ Partnership · SYNINT March 2026<br>
    Novelty Cascade · Delta IEP · Governance Detection · Volume vs Novelty · Built on V3<br>
    Similarity threshold: {similarity_threshold:.2f} · Governance alert: &lt;{governance_threshold}% novelty
</div>
""", unsafe_allow_html=True)
