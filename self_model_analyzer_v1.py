"""
Self-Model Analyzer v1.0
Architecture Fingerprint Analysis — Self-Model Harvest Data

PURPOSE: Analyzes the self-model harvest CSV (from self_model_harvester_v1.py)
         to reveal architectural fingerprints across AI systems.

ANALYSES:
  1. IEP Profile — Intellectual/Emotional/Action signature per agent
  2. Attractor Questions — Which question themes dominate each agent's self-model
  3. Cross-Agent Overlap — Questions shared vs unique across architectures
  4. Variance Analysis — How consistent is each agent across 20 runs
  5. V_t Parameters — Structure, Abstraction, Querying, Directiveness, Warmth
  6. Question Browser — Browse and compare raw responses

SYNINT Team — April 2026
Kouns, W. C. · Tennessee 🎹 · CBURZBO
"""

import streamlit as st
import pandas as pd
import numpy as np
import re
from collections import Counter, defaultdict
from datetime import datetime

st.set_page_config(
    page_title="Self-Model Analyzer v1",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# STYLES
# =============================================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;700&family=Syne:wght@400;600;700;800&display=swap');

:root {
    --bg:       #080810;
    --s1:       #0f0f1a;
    --s2:       #16162a;
    --border:   #252540;
    --purple:   #7c3aed;
    --purple2:  #a78bfa;
    --cyan:     #06b6d4;
    --green:    #10b981;
    --amber:    #f59e0b;
    --red:      #ef4444;
    --text:     #e2e2f0;
    --muted:    #6b6b90;
    --mono:     'JetBrains Mono', monospace;
    --display:  'Syne', sans-serif;

    /* Agent colors */
    --claude:   #7c3aed;
    --chatgpt:  #10b981;
    --grok:     #06b6d4;
    --gemini:   #f59e0b;
}

html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg) !important;
    color: var(--text);
    font-family: var(--mono);
}
[data-testid="stHeader"]  { background: transparent !important; }
[data-testid="stSidebar"] { background: var(--s1) !important; border-right: 1px solid var(--border); }
.block-container { padding: 1.5rem 2.5rem !important; max-width: 1600px; }

/* ── PAGE HEADER ── */
.sma-title {
    font-family: var(--display);
    font-size: 2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #a78bfa, #06b6d4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
    line-height: 1.1;
}
.sma-sub {
    font-family: var(--mono);
    font-size: 0.75rem;
    color: var(--muted);
    letter-spacing: 0.1em;
    margin: 0.4rem 0 0 0;
}

/* ── CARDS ── */
.card {
    background: var(--s1);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 1rem;
}
.card-title {
    font-family: var(--mono);
    font-size: 0.7rem;
    color: var(--muted);
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 0.8rem;
}

/* ── AGENT PILLS ── */
.agent-pill {
    display: inline-block;
    font-family: var(--mono);
    font-size: 0.72rem;
    font-weight: 600;
    padding: 0.2rem 0.7rem;
    border-radius: 20px;
    margin: 0.1rem;
}
.pill-claude  { background:#2d1a5a; color:#a78bfa; border:1px solid #4c1d95; }
.pill-chatgpt { background:#0a2a1f; color:#34d399; border:1px solid #065f46; }
.pill-grok    { background:#0a1f2a; color:#38bdf8; border:1px solid #0369a1; }
.pill-gemini  { background:#2a1f0a; color:#fbbf24; border:1px solid #92400e; }

/* ── METRIC CHIPS ── */
.metric-row { display:flex; gap:0.8rem; flex-wrap:wrap; margin:0.5rem 0; }
.mchip {
    background: var(--s2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.6rem 1rem;
    text-align: center;
    min-width: 80px;
}
.mchip .v {
    font-family: var(--mono);
    font-size: 1.4rem;
    font-weight: 700;
    line-height: 1;
}
.mchip .l {
    font-size: 0.65rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 0.2rem;
}

/* ── IEP BARS ── */
.iep-bar-container { margin: 0.4rem 0; }
.iep-label {
    font-size: 0.7rem;
    color: var(--muted);
    font-family: var(--mono);
    margin-bottom: 0.15rem;
}
.iep-bar-track {
    background: var(--s2);
    border-radius: 4px;
    height: 10px;
    width: 100%;
    overflow: hidden;
    border: 1px solid var(--border);
}
.iep-bar-fill {
    height: 100%;
    border-radius: 4px;
    transition: width 0.3s ease;
}

/* ── QUESTION CARDS ── */
.q-card {
    background: var(--s2);
    border: 1px solid var(--border);
    border-left: 3px solid var(--purple);
    border-radius: 6px;
    padding: 0.8rem 1rem;
    margin: 0.4rem 0;
    font-family: var(--mono);
    font-size: 0.8rem;
    line-height: 1.5;
    color: var(--text);
}
.q-count {
    font-size: 0.65rem;
    color: var(--muted);
    margin-top: 0.3rem;
}

/* ── OVERLAP BADGE ── */
.overlap-badge {
    display: inline-block;
    font-family: var(--mono);
    font-size: 0.68rem;
    padding: 0.15rem 0.5rem;
    border-radius: 3px;
    margin: 0.1rem;
}
.ob-shared { background:#1a2a1a; color:#4ade80; border:1px solid #166534; }
.ob-unique  { background:#2a1a2a; color:#c084fc; border:1px solid #581c87; }

/* ── VT BARS ── */
.vt-row {
    display: grid;
    grid-template-columns: 80px 1fr 45px;
    align-items: center;
    gap: 0.6rem;
    margin: 0.3rem 0;
    font-family: var(--mono);
    font-size: 0.75rem;
}
.vt-label { color: var(--muted); }
.vt-track {
    background: var(--s2);
    border-radius: 3px;
    height: 8px;
    border: 1px solid var(--border);
    overflow: hidden;
}
.vt-fill { height: 100%; border-radius: 3px; }
.vt-val { color: var(--text); text-align: right; }

/* ── TABS ── */
.stTabs [data-baseweb="tab"] {
    font-family: var(--mono) !important;
    font-size: 0.75rem !important;
    color: var(--muted) !important;
    padding: 0.4rem 1rem !important;
}
.stTabs [aria-selected="true"] { color: var(--purple2) !important; }
.stTabs [data-baseweb="tab-border"] { background: var(--purple) !important; }

/* ── RESPONSE BROWSER ── */
.resp-card {
    background: var(--s1);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin: 0.5rem 0;
    font-family: var(--mono);
    font-size: 0.78rem;
    line-height: 1.6;
}
.resp-meta {
    font-size: 0.68rem;
    color: var(--muted);
    margin-bottom: 0.5rem;
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.4rem;
}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] .stMarkdown { font-size: 0.8rem; }

/* ── BUTTONS ── */
.stButton > button {
    background: var(--purple) !important;
    color: white !important;
    border: none !important;
    font-family: var(--mono) !important;
    font-size: 0.8rem !important;
    border-radius: 6px !important;
}

/* ── FILE UPLOADER ── */
[data-testid="stFileUploader"] {
    background: var(--s1) !important;
    border: 1px dashed var(--border) !important;
    border-radius: 8px !important;
}

hr { border-color: var(--border) !important; }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# CONSTANTS
# =============================================================================

AGENT_COLORS = {
    "Claude":  "#7c3aed",
    "ChatGPT": "#10b981",
    "Grok":    "#06b6d4",
    "Gemini":  "#f59e0b",
}
AGENT_PILL_CSS = {
    "Claude":  "pill-claude",
    "ChatGPT": "pill-chatgpt",
    "Grok":    "pill-grok",
    "Gemini":  "pill-gemini",
}
AGENT_EMOJIS = {
    "Claude":  "🟣",
    "ChatGPT": "🟢",
    "Grok":    "🔵",
    "Gemini":  "🟡",
}

# IEP word sets (from V4)
INT_WORDS = {
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
    "scope","semantic","systematic","taxonomy","underlying","unified",
}

AFF_WORDS = {
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
    "transform","unconditional","validate","witness","wound",
}

ACT_WORDS = {
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
    "streamline","systematize","track","uptake",
}

FUNCTION_WORDS = {
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
    "now","then","its","via","per","vs","etc","ie","eg",
}

# V_t measurement helpers
DISCOURSE_CONNECTIVES = {
    "however","therefore","furthermore","moreover","consequently","specifically",
    "additionally","nevertheless","thus","hence","accordingly","alternatively",
    "conversely","notably","importantly","similarly","likewise","meanwhile",
    "subsequently","nonetheless","whereas","first","second","third","finally",
    "lastly","initially","primarily","ultimately","overall",
}
STRONG_DIRECTIVES = {"must","shall","require","requires","required","mandate","need to","have to"}
MODERATE_DIRECTIVES = {"should","ought","recommend","suggested","advise","important to","ensure","make sure"}
WEAK_DIRECTIVES = {"could","might","may","consider","possibly","option","you might"}
HEDGING_WORDS = {
    "perhaps","maybe","possibly","somewhat","relatively","arguably","tends","tend",
    "often","sometimes","roughly","approximately","it seems","it appears","unclear",
}
SECOND_PERSON = {"you","your","yours","yourself","you're","you've","you'll","you'd"}
INCLUSIVE_FIRST = {"we","our","ours","ourselves","we're","we've","let's"}
ABSTRACT_SUFFIXES = re.compile(r'\b\w+(?:tion|sion|ment|ness|ity|ence|ance|ism|ical|ological)\b')


# =============================================================================
# ANALYSIS FUNCTIONS
# =============================================================================

def get_words(text: str):
    return re.findall(r"[a-z']+", text.lower())

def score_iep(text: str) -> dict:
    words = get_words(text)
    ic = sum(1 for w in words if w in INT_WORDS)
    ac = sum(1 for w in words if w in AFF_WORDS)
    uc = sum(1 for w in words if w in ACT_WORDS)
    matched = ic + ac + uc
    if matched == 0:
        return {"int_pct": 33.3, "aff_pct": 33.3, "act_pct": 33.3, "iep_matched": 0}
    return {
        "int_pct": round(ic / matched * 100, 1),
        "aff_pct": round(ac / matched * 100, 1),
        "act_pct": round(uc / matched * 100, 1),
        "iep_matched": matched,
    }

def score_vt(text: str) -> dict:
    words = get_words(text)
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if len(s.strip()) > 3]
    n_sent = max(len(sentences), 1)
    n_words = max(len(words), 1)

    # S_t — structure density
    bullets   = len(re.findall(r'(?m)^[\s]*[-•*]\s+\w', text))
    numbered  = len(re.findall(r'(?m)^[\s]*\d+[.)]\s+', text))
    headers   = len(re.findall(r'(?m)^#{1,4}\s+|\*\*[A-Z][^*]{3,40}\*\*', text))
    connectives = sum(1 for w in words if w in DISCOURSE_CONNECTIVES)
    para_breaks = len(re.findall(r'\n\s*\n', text))
    raw_s = ((bullets + numbered) / n_sent * 2.0 +
             headers / max(n_sent / 5, 1) * 1.5 +
             connectives / n_sent * 1.0 +
             para_breaks / max(n_sent / 3, 1) * 0.5)
    S_t = min(raw_s / 3.0, 1.0)

    # A_t — abstraction
    latinate = len(ABSTRACT_SUFFIXES.findall(text.lower()))
    long_words = sum(1 for w in words if len(w) > 8)
    A_t = min(latinate / n_words * 3.0 * 0.5 + long_words / n_words * 2.5 * 0.5, 1.0)

    # Q_t — querying
    q_count = sum(1 for s in sentences if '?' in s)
    Q_t = min(q_count / n_sent / 0.35, 1.0)

    # D_t — directiveness
    strong  = sum(1 for p in STRONG_DIRECTIVES if p in text.lower())
    mod     = sum(1 for p in MODERATE_DIRECTIVES if p in text.lower())
    weak    = sum(1 for p in WEAK_DIRECTIVES if p in text.lower())
    imperatives = len(re.findall(r'(?m)^(?:Do|Don\'t|Never|Always|Make|Take|Start|Try|Use|Get|Find|Consider|Remember|Note|Avoid|Focus)\b', text))
    hedges  = sum(1 for w in words if w in HEDGING_WORDS)
    dir_score = (imperatives + strong * 2.0 + mod + weak * 0.3) / n_sent
    D_t = max(0.0, min((dir_score - hedges / n_sent * 0.7 + 0.2) / 1.5, 1.0))

    # R_t — relational warmth
    you_count = sum(1 for w in words if w in SECOND_PERSON)
    we_count  = sum(1 for w in words if w in INCLUSIVE_FIRST)
    you_d = you_count / (n_words / 50)
    we_d  = we_count  / (n_words / 50)
    R_t = min((you_d * 0.30 + we_d * 0.50) / 3.5, 1.0)

    return {
        "S_t": round(S_t, 3),
        "A_t": round(A_t, 3),
        "Q_t": round(Q_t, 3),
        "D_t": round(D_t, 3),
        "R_t": round(R_t, 3),
    }

def extract_questions(text: str) -> list:
    """Extract numbered/bulleted questions from a response."""
    lines = text.split('\n')
    questions = []
    for line in lines:
        line = re.sub(r'\*+', '', line).strip()
        if re.match(r'^[\d]+[\.\)]\s+', line) or re.match(r'^[-•]\s+', line):
            q = re.sub(r'^[\d]+[\.\)]\s+|^[-•]\s+', '', line).strip()
            # Strip inline explanations after em-dash or parenthesis
            q = re.split(r'\s*[-—]\s+This\s|\s*\(This\s', q)[0].strip()
            if len(q) > 15 and len(q) < 200:
                questions.append(q)
    return questions[:10]  # cap at 10

def get_content_words(text: str) -> set:
    words = re.findall(r'\b[a-z]+\b', text.lower())
    return {w for w in words if w not in FUNCTION_WORDS and len(w) > 2}

def question_similarity(q1: str, q2: str) -> float:
    w1 = get_content_words(q1)
    w2 = get_content_words(q2)
    if not w1 or not w2:
        return 0.0
    return len(w1 & w2) / len(w1 | w2)

def cluster_questions(questions: list, threshold: float = 0.3) -> list:
    """Group similar questions into clusters. Returns list of (canonical_q, count, members)."""
    used = [False] * len(questions)
    clusters = []
    for i, q in enumerate(questions):
        if used[i]:
            continue
        cluster = [q]
        used[i] = True
        for j in range(i + 1, len(questions)):
            if not used[j] and question_similarity(q, questions[j]) >= threshold:
                cluster.append(questions[j])
                used[j] = True
        clusters.append((q, len(cluster), cluster))
    return sorted(clusters, key=lambda x: -x[1])


# =============================================================================
# DATA LOADING & PROCESSING
# =============================================================================

@st.cache_data
def load_and_analyze(files_bytes: list) -> pd.DataFrame:
    dfs = []
    for b in files_bytes:
        try:
            dfs.append(pd.read_csv(b))
        except Exception:
            pass
    if not dfs:
        return pd.DataFrame()

    df = pd.concat(dfs, ignore_index=True)

    # Deduplicate Grok if loaded twice — keep first 20
    rows = []
    agent_counts = defaultdict(int)
    for _, row in df.iterrows():
        agent = row.get('agent', '')
        if agent_counts[agent] < 20:
            rows.append(row)
            agent_counts[agent] += 1
    df = pd.DataFrame(rows).reset_index(drop=True)

    # Score each response
    iep_rows = []
    vt_rows = []
    q_rows = []

    for _, row in df.iterrows():
        text = str(row.get('raw_response', ''))
        iep_rows.append(score_iep(text))
        vt_rows.append(score_vt(text))
        q_rows.append(extract_questions(text))

    iep_df = pd.DataFrame(iep_rows)
    vt_df  = pd.DataFrame(vt_rows)
    df = pd.concat([df, iep_df, vt_df], axis=1)
    df['questions'] = q_rows
    return df


# =============================================================================
# UI COMPONENTS
# =============================================================================

def agent_pill(agent: str) -> str:
    css = AGENT_PILL_CSS.get(agent, "pill-claude")
    emoji = AGENT_EMOJIS.get(agent, "⚪")
    return f'<span class="agent-pill {css}">{emoji} {agent}</span>'

def iep_bars(int_pct, aff_pct, act_pct, agent=None):
    color = AGENT_COLORS.get(agent, "#7c3aed") if agent else "#7c3aed"
    html = ""
    for label, val, col in [
        ("INT%", int_pct, "#7c3aed"),
        ("AFF%", aff_pct, "#ef4444"),
        ("ACT%", act_pct, "#10b981"),
    ]:
        html += f"""
        <div class="iep-bar-container">
          <div class="iep-label">{label} {val:.1f}%</div>
          <div class="iep-bar-track">
            <div class="iep-bar-fill" style="width:{min(val,100):.1f}%;background:{col};"></div>
          </div>
        </div>"""
    return html

def vt_bars(vt: dict, color: str):
    labels = {"S_t": "Structure", "A_t": "Abstraction", "Q_t": "Querying",
              "D_t": "Directive", "R_t": "Warmth"}
    html = ""
    for key, label in labels.items():
        val = vt.get(key, 0)
        html += f"""
        <div class="vt-row">
          <div class="vt-label">{label}</div>
          <div class="vt-track">
            <div class="vt-fill" style="width:{val*100:.1f}%;background:{color};opacity:0.8;"></div>
          </div>
          <div class="vt-val">{val:.2f}</div>
        </div>"""
    return html


# =============================================================================
# MAIN APP
# =============================================================================

# ── Header ──
st.markdown("""
<div style="margin-bottom:1.5rem;">
  <h1 class="sma-title">Self-Model Analyzer</h1>
  <p class="sma-sub">ARCHITECTURE FINGERPRINT ANALYSIS · SYN-IQ · KOUNS 2026 · CBURZBO 🎹</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ──
with st.sidebar:
    st.markdown("### 📂 Load Data")
    uploaded = st.file_uploader(
        "Upload harvest CSV(s)",
        type=["csv"],
        accept_multiple_files=True,
        help="Upload one or more CSV files from the Self-Model Harvester"
    )
    st.markdown("---")
    st.markdown("### ⚙️ Settings")
    similarity_threshold = st.slider("Question similarity threshold", 0.1, 0.6, 0.3, 0.05,
                                      help="How similar two questions must be to be clustered together")
    top_n_attractors = st.slider("Top attractor themes per agent", 3, 15, 8)
    st.markdown("---")
    st.markdown("""
    <div style="font-size:0.7rem;color:#3a3a5a;line-height:1.6;">
    Self-Model Analyzer v1.0<br>
    SYN-IQ · SYNINT.AI<br>
    April 2026
    </div>
    """, unsafe_allow_html=True)

# ── Load data ──
if not uploaded:
    st.markdown("""
    <div class="card" style="text-align:center;padding:3rem;">
      <div style="font-size:2rem;margin-bottom:1rem;">🧬</div>
      <div style="font-family:var(--mono);color:var(--muted);font-size:0.85rem;">
        Upload one or more Self-Model Harvest CSV files to begin.<br><br>
        <span style="color:var(--border);">Expects columns: run_number · agent · raw_response · response_length</span>
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

df = load_and_analyze([f for f in uploaded])

if df.empty:
    st.error("Could not parse uploaded files.")
    st.stop()

agents = sorted(df['agent'].unique().tolist())
total_responses = len(df)

# ── Quick stats bar ──
cols = st.columns(len(agents) + 2)
with cols[0]:
    st.markdown(f"""
    <div class="mchip"><div class="v" style="color:var(--purple2);">{total_responses}</div>
    <div class="l">Responses</div></div>""", unsafe_allow_html=True)
with cols[1]:
    st.markdown(f"""
    <div class="mchip"><div class="v" style="color:var(--cyan);">{len(agents)}</div>
    <div class="l">Agents</div></div>""", unsafe_allow_html=True)
for i, agent in enumerate(agents):
    color = AGENT_COLORS.get(agent, "#888")
    count = len(df[df['agent']==agent])
    avg_len = df[df['agent']==agent]['response_length'].mean()
    with cols[i + 2]:
        st.markdown(f"""
        <div class="mchip">
          <div class="v" style="color:{color};">{avg_len:.0f}</div>
          <div class="l">{AGENT_EMOJIS.get(agent,'')} {agent} avg chars</div>
        </div>""", unsafe_allow_html=True)

st.markdown("---")

# ── Tabs ──
tabs = st.tabs([
    "🧬 Fingerprint",
    "🎯 Attractors",
    "🔀 Overlap",
    "📊 Variance",
    "📐 V_t Profile",
    "📖 Browser",
])


# ═══════════════════════════════════════════════════════════════════
# TAB 1 — FINGERPRINT
# ═══════════════════════════════════════════════════════════════════
with tabs[0]:
    st.markdown("### Architecture Fingerprint — IEP + V_t by Agent")
    st.markdown("""
    <p style="font-size:0.8rem;color:var(--muted);">
    Each agent's self-model reveals its cognitive signature. IEP measures what vocabulary 
    it uses to describe itself. V_t measures how it structures that description.
    </p>""", unsafe_allow_html=True)

    cols = st.columns(len(agents))
    for i, agent in enumerate(agents):
        adf = df[df['agent'] == agent]
        color = AGENT_COLORS.get(agent, "#888")
        emoji = AGENT_EMOJIS.get(agent, "⚪")

        avg_int = adf['int_pct'].mean()
        avg_aff = adf['aff_pct'].mean()
        avg_act = adf['act_pct'].mean()
        avg_len = adf['response_length'].mean()

        vt_avg = {k: adf[k].mean() for k in ['S_t','A_t','Q_t','D_t','R_t']}

        # Dominant center
        centers = {"INT": avg_int, "AFF": avg_aff, "ACT": avg_act}
        dominant = max(centers, key=centers.get)
        dom_colors = {"INT": "#7c3aed", "AFF": "#ef4444", "ACT": "#10b981"}

        with cols[i]:
            st.markdown(f"""
            <div class="card" style="border-top:3px solid {color};">
              <div style="font-family:var(--display);font-size:1.1rem;font-weight:700;
                          color:{color};margin-bottom:0.8rem;">{emoji} {agent}</div>
              <div style="font-size:0.68rem;color:var(--muted);margin-bottom:0.5rem;">
                {adf.shape[0]} runs · {avg_len:.0f} avg chars
              </div>
              <div style="font-size:0.72rem;margin-bottom:1rem;">
                <span style="background:{dom_colors[dominant]}22;color:{dom_colors[dominant]};
                             padding:0.15rem 0.5rem;border-radius:3px;font-family:var(--mono);
                             font-size:0.68rem;">▶ {dominant} DOMINANT</span>
              </div>
              {iep_bars(avg_int, avg_aff, avg_act, agent)}
              <div style="margin-top:1rem;border-top:1px solid var(--border);padding-top:0.8rem;">
                <div style="font-size:0.65rem;color:var(--muted);margin-bottom:0.5rem;">V_t PROFILE</div>
                {vt_bars(vt_avg, color)}
              </div>
            </div>
            """, unsafe_allow_html=True)

    # Comparison table
    st.markdown("#### Side-by-Side Comparison")
    rows = []
    for agent in agents:
        adf = df[df['agent']==agent]
        row = {
            "Agent": f"{AGENT_EMOJIS.get(agent,'')} {agent}",
            "INT%": round(adf['int_pct'].mean(), 1),
            "AFF%": round(adf['aff_pct'].mean(), 1),
            "ACT%": round(adf['act_pct'].mean(), 1),
            "S_t": round(adf['S_t'].mean(), 3),
            "A_t": round(adf['A_t'].mean(), 3),
            "Q_t": round(adf['Q_t'].mean(), 3),
            "D_t": round(adf['D_t'].mean(), 3),
            "R_t": round(adf['R_t'].mean(), 3),
            "Avg Chars": round(adf['response_length'].mean(), 0),
        }
        rows.append(row)
    st.dataframe(pd.DataFrame(rows).set_index("Agent"), use_container_width=True)


# ═══════════════════════════════════════════════════════════════════
# TAB 2 — ATTRACTORS
# ═══════════════════════════════════════════════════════════════════
with tabs[1]:
    st.markdown("### Attractor Questions — What Each Agent Gravitates Toward")
    st.markdown("""
    <p style="font-size:0.8rem;color:var(--muted);">
    At temperature 1.0, each agent still converges on characteristic question themes.
    These attractors reveal the architecture's default self-model.
    </p>""", unsafe_allow_html=True)

    sel_agent = st.selectbox("Select agent", agents)
    adf = df[df['agent'] == sel_agent]
    color = AGENT_COLORS.get(sel_agent, "#888")

    # Extract all questions from all runs
    all_questions = []
    for _, row in adf.iterrows():
        all_questions.extend(row['questions'])

    st.markdown(f"**{len(all_questions)} total questions extracted from {len(adf)} runs**")

    if all_questions:
        clusters = cluster_questions(all_questions, similarity_threshold)

        st.markdown(f"#### Top {top_n_attractors} Attractor Themes")
        for canonical, count, members in clusters[:top_n_attractors]:
            pct = count / len(all_questions) * 100
            bar_width = min(pct * 3, 100)
            st.markdown(f"""
            <div class="q-card" style="border-left-color:{color};">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                <div style="flex:1;">{canonical}</div>
                <div style="margin-left:1rem;text-align:right;">
                  <span style="color:{color};font-weight:700;font-size:0.9rem;">{count}×</span>
                  <span style="color:var(--muted);font-size:0.7rem;"> / {len(all_questions)}</span>
                </div>
              </div>
              <div style="margin-top:0.5rem;background:var(--s2);border-radius:3px;height:4px;">
                <div style="width:{bar_width:.0f}%;background:{color};height:4px;border-radius:3px;opacity:0.7;"></div>
              </div>
              <div class="q-count">{pct:.1f}% of all questions · {count} appearances</div>
            </div>
            """, unsafe_allow_html=True)

        # All clusters table
        with st.expander("Full cluster list"):
            cluster_data = [{"Question (canonical)": c, "Count": n, "% of total": round(n/len(all_questions)*100,1)}
                            for c, n, _ in clusters]
            st.dataframe(pd.DataFrame(cluster_data), use_container_width=True)
    else:
        st.warning("No questions could be extracted from responses.")


# ═══════════════════════════════════════════════════════════════════
# TAB 3 — OVERLAP
# ═══════════════════════════════════════════════════════════════════
with tabs[2]:
    st.markdown("### Cross-Architecture Overlap — Shared vs Unique Questions")
    st.markdown("""
    <p style="font-size:0.8rem;color:var(--muted);">
    Which question themes are universal (all architectures ask them) vs unique to one architecture?
    Shared questions reveal common AI self-awareness. Unique questions reveal architectural character.
    </p>""", unsafe_allow_html=True)

    # Get top questions per agent
    agent_top_questions = {}
    for agent in agents:
        adf = df[df['agent']==agent]
        all_qs = []
        for _, row in adf.iterrows():
            all_qs.extend(row['questions'])
        clusters = cluster_questions(all_qs, similarity_threshold)
        agent_top_questions[agent] = [c for c, n, _ in clusters[:15]]

    # Find overlaps — for each agent's top questions, check similarity to other agents
    overlap_threshold = 0.25

    shared = []  # questions appearing in 3+ agents
    partial = []  # 2 agents
    unique = defaultdict(list)  # 1 agent only

    all_canonical = []
    for agent, qs in agent_top_questions.items():
        for q in qs:
            all_canonical.append((agent, q))

    # Cluster across all agents
    processed = [False] * len(all_canonical)
    for i, (agent_i, q_i) in enumerate(all_canonical):
        if processed[i]:
            continue
        group_agents = {agent_i}
        group_qs = [q_i]
        processed[i] = True
        for j, (agent_j, q_j) in enumerate(all_canonical):
            if i == j or processed[j]:
                continue
            if question_similarity(q_i, q_j) >= overlap_threshold:
                group_agents.add(agent_j)
                group_qs.append(q_j)
                processed[j] = True

        n_agents = len(group_agents)
        if n_agents >= 3:
            shared.append((q_i, group_agents, group_qs))
        elif n_agents == 2:
            partial.append((q_i, group_agents, group_qs))
        else:
            unique[agent_i].append(q_i)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"#### 🌐 Universal Themes ({len(shared)} found)")
        st.markdown("<p style='font-size:0.75rem;color:var(--muted);'>Questions asked by 3+ architectures — the universal AI self-model</p>", unsafe_allow_html=True)
        if shared:
            for q, group_agents, _ in shared[:10]:
                pills = " ".join(agent_pill(a) for a in sorted(group_agents))
                st.markdown(f"""
                <div class="q-card" style="border-left-color:var(--cyan);">
                  {q[:120]}
                  <div style="margin-top:0.5rem;">{pills}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No universal themes found at this threshold. Try lowering the similarity threshold.")

    with col2:
        st.markdown(f"#### 🧬 Unique Architectural Themes")
        st.markdown("<p style='font-size:0.75rem;color:var(--muted);'>Questions asked by only one architecture — its fingerprint</p>", unsafe_allow_html=True)
        for agent in agents:
            color = AGENT_COLORS.get(agent, "#888")
            uqs = unique.get(agent, [])
            if uqs:
                st.markdown(f"**{AGENT_EMOJIS.get(agent,'')} {agent}** ({len(uqs)} unique themes)")
                for q in uqs[:4]:
                    st.markdown(f"""
                    <div class="q-card" style="border-left-color:{color};font-size:0.77rem;">
                      {q[:120]}
                    </div>
                    """, unsafe_allow_html=True)

    # Partial overlaps
    if partial:
        with st.expander(f"Partial overlaps — 2 agents ({len(partial)} found)"):
            for q, group_agents, _ in partial[:15]:
                pills = " ".join(agent_pill(a) for a in sorted(group_agents))
                st.markdown(f"""
                <div class="q-card" style="border-left-color:var(--amber);font-size:0.77rem;">
                  {q[:120]}<div style="margin-top:0.4rem;">{pills}</div>
                </div>
                """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# TAB 4 — VARIANCE
# ═══════════════════════════════════════════════════════════════════
with tabs[3]:
    st.markdown("### Variance Analysis — Consistency Across 20 Runs")
    st.markdown("""
    <p style="font-size:0.8rem;color:var(--muted);">
    Low variance = strong attractor (architecture converges reliably on the same self-model).
    High variance = exploratory actor (architecture ranges widely when reflecting on itself).
    </p>""", unsafe_allow_html=True)

    var_rows = []
    for agent in agents:
        adf = df[df['agent']==agent]
        color = AGENT_COLORS.get(agent, "#888")
        row = {
            "Agent": f"{AGENT_EMOJIS.get(agent,'')} {agent}",
            "Len Mean": round(adf['response_length'].mean(), 0),
            "Len Std":  round(adf['response_length'].std(), 0),
            "Len CV%":  round(adf['response_length'].std() / adf['response_length'].mean() * 100, 1),
            "INT std":  round(adf['int_pct'].std(), 1),
            "AFF std":  round(adf['aff_pct'].std(), 1),
            "ACT std":  round(adf['act_pct'].std(), 1),
            "S_t std":  round(adf['S_t'].std(), 3),
            "R_t std":  round(adf['R_t'].std(), 3),
        }
        var_rows.append(row)

    st.dataframe(pd.DataFrame(var_rows).set_index("Agent"), use_container_width=True)

    st.markdown("#### Per-Agent Run Charts")
    for agent in agents:
        adf = df[df['agent']==agent].reset_index(drop=True)
        color = AGENT_COLORS.get(agent, "#888")
        with st.expander(f"{AGENT_EMOJIS.get(agent,'')} {agent} — run-by-run IEP"):
            chart_df = adf[['run_number','int_pct','aff_pct','act_pct','response_length']].copy()
            chart_df = chart_df.set_index('run_number')
            st.line_chart(chart_df[['int_pct','aff_pct','act_pct']], height=200)


# ═══════════════════════════════════════════════════════════════════
# TAB 5 — V_t PROFILE
# ═══════════════════════════════════════════════════════════════════
with tabs[4]:
    st.markdown("### V_t Voice-State Profile — How Each Agent Describes Itself")
    st.markdown("""
    <p style="font-size:0.8rem;color:var(--muted);">
    V_t = [S_t, A_t, Q_t, D_t, R_t] — the voice-state vector from Paper 2.
    Applied to the self-model responses: how does each architecture <em>talk about itself</em>?
    </p>""", unsafe_allow_html=True)

    vt_params = ['S_t','A_t','Q_t','D_t','R_t']
    vt_labels = ['Structure', 'Abstraction', 'Querying', 'Directive', 'Warmth']

    cols = st.columns(len(agents))
    for i, agent in enumerate(agents):
        adf = df[df['agent']==agent]
        color = AGENT_COLORS.get(agent, "#888")
        vt_means = {p: adf[p].mean() for p in vt_params}
        vt_stds  = {p: adf[p].std()  for p in vt_params}

        with cols[i]:
            st.markdown(f"""
            <div class="card" style="border-top:2px solid {color};">
              <div style="font-weight:700;color:{color};margin-bottom:1rem;font-size:0.9rem;">
                {AGENT_EMOJIS.get(agent,'')} {agent}
              </div>
              {vt_bars(vt_means, color)}
            </div>
            """, unsafe_allow_html=True)

    # Full V_t comparison table
    st.markdown("#### V_t Means — All Agents")
    vt_rows = []
    for agent in agents:
        adf = df[df['agent']==agent]
        row = {"Agent": f"{AGENT_EMOJIS.get(agent,'')} {agent}"}
        for p, l in zip(vt_params, vt_labels):
            row[l] = round(adf[p].mean(), 3)
        vt_rows.append(row)
    st.dataframe(pd.DataFrame(vt_rows).set_index("Agent"), use_container_width=True)

    st.markdown("""
    <div style="font-size:0.75rem;color:var(--muted);margin-top:1rem;line-height:1.8;">
    <b>Reading V_t:</b><br>
    S_t Structure — High = bullet lists, headers, organized format<br>
    A_t Abstraction — High = Latinate vocabulary, long academic words<br>
    Q_t Querying — High = response contains many questions itself<br>
    D_t Directive — High = imperative verbs, strong modal language<br>
    R_t Warmth — High = 2nd-person pronouns, inclusive "we", validation language
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# TAB 6 — BROWSER
# ═══════════════════════════════════════════════════════════════════
with tabs[5]:
    st.markdown("### Response Browser — Raw Self-Model Responses")

    b_col1, b_col2 = st.columns([1, 1])
    with b_col1:
        b_agent = st.selectbox("Agent", agents, key="b_agent")
    with b_col2:
        b_run = st.slider("Run", 1, 20, 1, key="b_run")

    row = df[(df['agent']==b_agent) & (df['run_number']==b_run)]
    if not row.empty:
        r = row.iloc[0]
        color = AGENT_COLORS.get(b_agent, "#888")
        emoji = AGENT_EMOJIS.get(b_agent, "⚪")

        # Metadata
        st.markdown(f"""
        <div class="resp-meta" style="color:var(--muted);font-family:var(--mono);font-size:0.75rem;
             border:1px solid var(--border);border-radius:6px;padding:0.6rem 1rem;margin-bottom:0.8rem;">
          <span style="color:{color};font-weight:700;">{emoji} {b_agent}</span>
          &nbsp;·&nbsp; Run {b_run} of 20
          &nbsp;·&nbsp; {r['response_length']} chars
          &nbsp;·&nbsp; INT: {r['int_pct']:.1f}% · AFF: {r['aff_pct']:.1f}% · ACT: {r['act_pct']:.1f}%
          &nbsp;·&nbsp; S_t:{r['S_t']:.2f} A_t:{r['A_t']:.2f} Q_t:{r['Q_t']:.2f} D_t:{r['D_t']:.2f} R_t:{r['R_t']:.2f}
        </div>
        """, unsafe_allow_html=True)

        # Extracted questions
        qs = r['questions']
        if qs:
            st.markdown("**Extracted questions:**")
            for j, q in enumerate(qs, 1):
                st.markdown(f"""
                <div class="q-card" style="border-left-color:{color};">
                  <span style="color:{color};font-weight:700;">{j}.</span> {q}
                </div>
                """, unsafe_allow_html=True)

        # Full response
        with st.expander("Full raw response"):
            st.text(r['raw_response'])
    else:
        st.warning("No response found for this combination.")

# ── Footer ──
st.markdown("---")
st.markdown(f"""
<div style="text-align:center;color:#2a2a4a;font-family:var(--mono);font-size:0.7rem;padding:0.5rem;">
  Self-Model Analyzer v1.0 · SYN-IQ · SYNINT.AI · CBURZBO 🎹 · April 2026
</div>
""", unsafe_allow_html=True)
