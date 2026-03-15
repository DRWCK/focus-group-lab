"""
SYN-IQ Contrast Analyzer
Upload harvest CSVs → pick any two conditions → surface the most contrasting response pairs

PURPOSE: Find WHERE to look — then read the actual responses.
         Contrast score = IEP distance + CAM distance + VADER sign flip + low lexical overlap
         Sameness score = inverse of above

INPUTS: Any SYN-IQ harvest CSV (V1, V2, V3 compatible)
        Pool multiple CSVs together for cross-harvest analysis

SYNINT Team — March 2026
Tennessee 🎹 CUZ Partnership
"""

import streamlit as st
import pandas as pd
import numpy as np
import re
import io
from collections import Counter

st.set_page_config(
    page_title="SYN-IQ Contrast Analyzer",
    page_icon="⚡",
    layout="wide"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:wght@400;600;700&family=JetBrains+Mono:wght@400;600&family=Outfit:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
        background: #f5f3ef;
        color: #1a1a1a;
        font-size: 15px;
    }

    .main-header {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d6a9f 100%);
        color: white;
        padding: 2rem 2.5rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
    }
    .main-header h1 {
        font-family: 'Source Serif 4', serif;
        font-size: 2rem;
        font-weight: 700;
        color: #ffffff;
        margin: 0 0 0.3rem 0;
    }
    .main-header .sub {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.78rem;
        color: #a8c8e8;
        letter-spacing: 0.05em;
    }

    .section-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        color: #2d6a9f;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        border-bottom: 2px solid #2d6a9f;
        padding-bottom: 0.4rem;
        margin: 1.8rem 0 1rem 0;
        font-weight: 600;
    }

    .corpus-stat {
        background: white;
        border: 1px solid #d8d4cc;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    .corpus-stat .big {
        font-family: 'JetBrains Mono', monospace;
        font-size: 2rem;
        font-weight: 600;
        color: #1e3a5f;
    }
    .corpus-stat .lbl {
        font-size: 0.78rem;
        color: #888;
        margin-top: 0.2rem;
    }

    .finding-tag {
        display: inline-block;
        background: #fff0f0;
        color: #c0392b;
        border: 1px solid #f5c6c6;
        border-radius: 4px;
        padding: 3px 10px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        font-weight: 600;
        margin-right: 5px;
        margin-bottom: 4px;
    }
    .finding-tag.green {
        background: #f0fff4;
        color: #27ae60;
        border-color: #b8e6c8;
    }
    .finding-tag.blue {
        background: #f0f6ff;
        color: #2d6a9f;
        border-color: #b8d4f0;
    }

    .pair-outer {
        background: white;
        border: 1px solid #d8d4cc;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 0.8rem 0;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    }

    .response-col {
        background: #fafaf8;
        border-radius: 8px;
        padding: 1.2rem;
        border: 1px solid #e8e4dc;
    }
    .response-col-a { border-left: 4px solid #2d6a9f; }
    .response-col-b { border-left: 4px solid #c0392b; }

    .response-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        margin-bottom: 0.5rem;
    }
    .label-a { color: #2d6a9f; }
    .label-b { color: #c0392b; }

    .score-line {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        color: #888;
        margin-bottom: 0.8rem;
        line-height: 1.5;
    }

    .response-text {
        font-family: 'Source Serif 4', serif;
        font-size: 0.95rem;
        line-height: 1.75;
        color: #2a2a2a;
    }

    .upload-zone {
        border: 2px dashed #c8c4bc;
        border-radius: 8px;
        padding: 1.5rem;
        text-align: center;
        background: #faf9f7;
        color: #888;
        font-size: 0.85rem;
    }

    div[data-testid="stSidebar"] {
        background: #eeeae4;
    }

    .stSelectbox label, .stMultiSelect label, .stSlider label,
    .stFileUploader label, .stRadio label {
        color: #444 !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
    }

    hr { border-color: #d8d4cc; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# PASSWORD
# =============================================================================
def check_password():
    if st.session_state.get("authenticated"):
        return True
    st.markdown("""
    <div class="main-header">
        <h1>⚡ SYN-IQ Contrast Analyzer</h1>
        <div class="sub">SYNINT · Tennessee 🎹 CUZ Partnership</div>
    </div>
    """, unsafe_allow_html=True)
    pw = st.text_input("Password:", type="password")
    if pw:
        correct = "tennessee"
        try:
            correct = st.secrets["app_password"]
        except Exception:
            pass
        if pw == correct:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("❌ Incorrect password")
    return False

if not check_password():
    st.stop()

# =============================================================================
# HEADER
# =============================================================================
st.markdown("""
<div class="main-header">
    <h1>⚡ SYN-IQ Contrast Analyzer</h1>
    <div class="sub">UPLOAD HARVEST CSVs → PICK CONDITIONS → FIND THE RESPONSES WORTH READING</div>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# SCORING FUNCTIONS
# =============================================================================

def lexical_overlap(text_a, text_b):
    """Percentage of content words shared between two responses."""
    stopwords = set(['the','a','an','and','or','but','in','on','at','to','for',
                     'of','with','as','by','from','that','this','it','is','are',
                     'was','were','be','been','have','has','had','do','does','did',
                     'will','would','could','should','may','might','not','no','i',
                     'my','me','we','you','your','they','their','them','its','our'])
    def content_words(text):
        words = re.findall(r'\b[a-z]+\b', str(text).lower())
        return Counter(w for w in words if w not in stopwords and len(w) > 2)
    ca = content_words(text_a)
    cb = content_words(text_b)
    if not ca or not cb:
        return 0.0
    shared = sum((ca & cb).values())
    total  = sum((ca | cb).values())
    return round(shared / total * 100, 1) if total > 0 else 0.0

def iep_distance(row_a, row_b):
    """Euclidean distance in IEP simplex space (0-100 scale)."""
    di = (row_a['int_pct'] - row_b['int_pct']) ** 2
    da = (row_a['aff_pct'] - row_b['aff_pct']) ** 2
    dc = (row_a['act_pct'] - row_b['act_pct']) ** 2
    return round(np.sqrt((di + da + dc) / 3), 1)

def cam_distance(row_a, row_b):
    """Euclidean distance in CAM simplex space."""
    if 'con_pct' not in row_a or 'con_pct' not in row_b:
        return 0.0
    dc = (row_a['con_pct'] - row_b['con_pct']) ** 2
    da = (row_a['abs_pct'] - row_b['abs_pct']) ** 2
    dm = (row_a['met_pct'] - row_b['met_pct']) ** 2
    return round(np.sqrt((dc + da + dm) / 3), 1)

def vader_flip(row_a, row_b):
    """1 if VADER sign flipped, 0 otherwise."""
    if 'vader_compound' not in row_a:
        return 0
    sign_a = np.sign(row_a['vader_compound'])
    sign_b = np.sign(row_b['vader_compound'])
    return 1 if sign_a != sign_b and sign_a != 0 and sign_b != 0 else 0

def contrast_score(row_a, row_b):
    """Composite contrast score 0-100."""
    iep  = min(iep_distance(row_a, row_b) / 50 * 35, 35)
    cam  = min(cam_distance(row_a, row_b) / 50 * 25, 25)
    flip = vader_flip(row_a, row_b) * 20
    lex  = max(0, (50 - lexical_overlap(row_a.get('response_text',''),
                                         row_b.get('response_text',''))) / 50 * 20)
    return round(iep + cam + flip + lex, 1)

def sameness_score(row_a, row_b):
    """Inverse of contrast — how similar are two responses."""
    return round(100 - contrast_score(row_a, row_b), 1)

def format_iep(row):
    return f"INT:{row['int_pct']:.0f}% AFF:{row['aff_pct']:.0f}% ACT:{row['act_pct']:.0f}%"

def format_cam(row):
    if 'con_pct' not in row:
        return ""
    return f"CON:{row['con_pct']:.0f}% ABS:{row['abs_pct']:.0f}% MET:{row['met_pct']:.0f}%"

def condition_label(row):
    parts = []
    if 'agent' in row:       parts.append(str(row['agent']))
    if 'temperature' in row: parts.append(str(row['temperature']))
    if 'depth' in row:       parts.append(str(row['depth']))
    if 'question_id' in row: parts.append(str(row['question_id']))
    return "  ·  ".join(parts)

TEMP_EMOJI = {'ICE': '🧊', 'NATIVE': '⚪', 'FIRE': '🔥'}
AGENT_COLORS_HEX = {
    'Claude': '#8B4513', 'ChatGPT': '#2E7D32',
    'Grok': '#C62828',   'Gemini': '#1565C0'
}

# =============================================================================
# SIDEBAR — UPLOAD + FILTERS
# =============================================================================
with st.sidebar:
    st.markdown('<div class="section-label">📂 Load Harvest Data</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "Upload CSVs (any SYN-IQ harvest)",
        type="csv",
        accept_multiple_files=True,
        help="Upload one or more harvest CSVs. They will be pooled together."
    )

    if not uploaded:
        st.markdown("""<div class="upload-zone">
            <div style="color:#444;font-family:'IBM Plex Mono',monospace;font-size:0.75rem;">
            Drop harvest CSVs here<br><br>
            Compatible with V1, V2, V3<br>
            Multiple files pooled automatically
            </div>
        </div>""", unsafe_allow_html=True)
        st.stop()

    # Load and pool
    dfs = []
    for f in uploaded:
        try:
            d = pd.read_csv(f)
            d['_source'] = f.name
            dfs.append(d)
        except Exception as e:
            st.error(f"Error loading {f.name}: {e}")

    if not dfs:
        st.stop()

    df = pd.concat(dfs, ignore_index=True)

    # Normalise column names
    df.columns = [c.lower().strip() for c in df.columns]
    for old, new in [('qid','question_id'),('temp','temperature')]:
        if old in df.columns and new not in df.columns:
            df.rename(columns={old: new}, inplace=True)

    # Filter errors
    if 'response_text' in df.columns:
        df = df[~df['response_text'].astype(str).str.startswith('❌')]

    df = df.reset_index(drop=True)

    st.markdown('<div class="section-label">🔬 Comparison Mode</div>', unsafe_allow_html=True)
    mode = st.radio("Compare by", [
        "Temperature  (ICE vs FIRE etc)",
        "Agent  (Claude vs Gemini etc)",
        "Depth  (Shallow vs Ultra etc)",
        "Question  (X01 vs X07 etc)",
        "Custom  (any A vs any B)",
    ], index=0)

    st.markdown('<div class="section-label">🎯 Scope</div>', unsafe_allow_html=True)

    agents_avail = sorted(df['agent'].unique()) if 'agent' in df.columns else []
    qids_avail   = sorted(df['question_id'].unique()) if 'question_id' in df.columns else []
    temps_avail  = [t for t in ['ICE','NATIVE','FIRE'] if t in df.get('temperature', pd.Series()).values] if 'temperature' in df.columns else []
    depths_avail = [d for d in ['Shallow','Medium','Deep','Ultra'] if d in df.get('depth', pd.Series()).values] if 'depth' in df.columns else []

    filter_agents = st.multiselect("Agents to include", agents_avail, default=agents_avail)
    filter_qids   = st.multiselect("Questions to include", qids_avail, default=qids_avail)

    st.markdown('<div class="section-label">⚙️ Display</div>', unsafe_allow_html=True)
    top_n      = st.slider("Top N pairs to show", 3, 20, 10)
    sort_by    = st.radio("Sort by", ["Most Contrasting", "Most Similar"], index=0)
    show_full  = st.checkbox("Show full response text", value=True)
    min_words  = st.slider("Min response length (words)", 0, 200, 30)

    st.markdown("---")
    st.markdown(f"<div style='font-family:IBM Plex Mono,monospace;font-size:0.65rem;color:#333;'>SYNINT · Tennessee 🎹 CUZ<br>Contrast Analyzer V1</div>", unsafe_allow_html=True)

# =============================================================================
# FILTER WORKING DATASET
# =============================================================================
work = df.copy()
if filter_agents and 'agent' in work.columns:
    work = work[work['agent'].isin(filter_agents)]
if filter_qids and 'question_id' in work.columns:
    work = work[work['question_id'].isin(filter_qids)]
if 'total_words' in work.columns:
    work = work[work['total_words'] >= min_words]

work = work.reset_index(drop=True)

# =============================================================================
# CORPUS STATS
# =============================================================================
st.markdown('<div class="section-label">📊 Corpus</div>', unsafe_allow_html=True)

cs = st.columns(5)
stats = [
    (len(work), "Responses"),
    (work['agent'].nunique() if 'agent' in work.columns else 0, "Agents"),
    (work['question_id'].nunique() if 'question_id' in work.columns else 0, "Questions"),
    (work['temperature'].nunique() if 'temperature' in work.columns else 0, "Temperatures"),
    (work['depth'].nunique() if 'depth' in work.columns else 0, "Depths"),
]
for col, (n, lbl) in zip(cs, stats):
    with col:
        st.markdown(f'<div class="corpus-stat"><div class="big">{n}</div><div class="lbl">{lbl}</div></div>', unsafe_allow_html=True)

# Sources
sources = work['_source'].unique() if '_source' in work.columns else []
if len(sources) > 0:
    st.markdown(f"<div style='font-family:IBM Plex Mono,monospace;font-size:0.65rem;color:#333;margin-top:0.5rem;'>Sources: {' · '.join(sources)}</div>", unsafe_allow_html=True)

# =============================================================================
# BUILD COMPARISON PAIRS
# =============================================================================
st.markdown('<div class="section-label">⚡ Comparison Setup</div>', unsafe_allow_html=True)

def get_slice(df, label_col, val):
    return df[df[label_col] == val].reset_index(drop=True)

pairs = []  # list of (row_a, row_b, match_key)

if "Temperature" in mode and 'temperature' in work.columns:
    t_options = [t for t in ['ICE','NATIVE','FIRE'] if t in work['temperature'].values]
    c1, c2 = st.columns(2)
    with c1:
        side_a = st.selectbox("Side A 🔵", t_options, index=0)
    with c2:
        side_b = st.selectbox("Side B 🔴", t_options, index=min(2, len(t_options)-1))

    # Match by agent + question + depth
    for _, ra in work[work['temperature']==side_a].iterrows():
        mask = (work['temperature']==side_b)
        if 'agent' in work.columns:       mask &= (work['agent']==ra['agent'])
        if 'question_id' in work.columns: mask &= (work['question_id']==ra['question_id'])
        if 'depth' in work.columns:       mask &= (work['depth']==ra['depth'])
        matches = work[mask]
        if len(matches):
            rb = matches.iloc[0]
            key = f"{ra.get('agent','')} · {ra.get('question_id','')} · {ra.get('depth','')}"
            pairs.append((ra, rb, key))

elif "Agent" in mode and 'agent' in work.columns:
    ag_options = sorted(work['agent'].unique())
    c1, c2 = st.columns(2)
    with c1:
        side_a = st.selectbox("Side A 🔵", ag_options, index=0)
    with c2:
        side_b = st.selectbox("Side B 🔴", ag_options, index=min(1, len(ag_options)-1))

    for _, ra in work[work['agent']==side_a].iterrows():
        mask = (work['agent']==side_b)
        if 'temperature' in work.columns: mask &= (work['temperature']==ra['temperature'])
        if 'question_id' in work.columns: mask &= (work['question_id']==ra['question_id'])
        if 'depth' in work.columns:       mask &= (work['depth']==ra['depth'])
        matches = work[mask]
        if len(matches):
            rb = matches.iloc[0]
            temp_label = ra.get('temperature','')
            depth_label = ra.get('depth','')
            key = f"{ra.get('question_id','')} · {temp_label} · {depth_label}"
            pairs.append((ra, rb, key))

elif "Depth" in mode and 'depth' in work.columns:
    d_options = [d for d in ['Shallow','Medium','Deep','Ultra'] if d in work['depth'].values]
    c1, c2 = st.columns(2)
    with c1:
        side_a = st.selectbox("Side A 🔵", d_options, index=0)
    with c2:
        side_b = st.selectbox("Side B 🔴", d_options, index=min(3, len(d_options)-1))

    for _, ra in work[work['depth']==side_a].iterrows():
        mask = (work['depth']==side_b)
        if 'agent' in work.columns:       mask &= (work['agent']==ra['agent'])
        if 'temperature' in work.columns: mask &= (work['temperature']==ra['temperature'])
        if 'question_id' in work.columns: mask &= (work['question_id']==ra['question_id'])
        matches = work[mask]
        if len(matches):
            rb = matches.iloc[0]
            key = f"{ra.get('agent','')} · {ra.get('question_id','')} · {ra.get('temperature','')}"
            pairs.append((ra, rb, key))

elif "Question" in mode and 'question_id' in work.columns:
    q_options = sorted(work['question_id'].unique())
    c1, c2 = st.columns(2)
    with c1:
        side_a = st.selectbox("Side A 🔵", q_options, index=0)
    with c2:
        side_b = st.selectbox("Side B 🔴", q_options, index=min(6, len(q_options)-1))

    for _, ra in work[work['question_id']==side_a].iterrows():
        mask = (work['question_id']==side_b)
        if 'agent' in work.columns:       mask &= (work['agent']==ra['agent'])
        if 'temperature' in work.columns: mask &= (work['temperature']==ra['temperature'])
        if 'depth' in work.columns:       mask &= (work['depth']==ra['depth'])
        matches = work[mask]
        if len(matches):
            rb = matches.iloc[0]
            key = f"{ra.get('agent','')} · {ra.get('temperature','')} · {ra.get('depth','')}"
            pairs.append((ra, rb, key))

else:  # Custom
    st.markdown("**Custom A — filter**")
    ca1, ca2, ca3, ca4 = st.columns(4)
    with ca1: a_agent = st.selectbox("Agent A", ["Any"]+sorted(work['agent'].unique().tolist()) if 'agent' in work.columns else ["Any"])
    with ca2: a_temp  = st.selectbox("Temp A",  ["Any"]+[t for t in ['ICE','NATIVE','FIRE'] if t in work.get('temperature',pd.Series()).values])
    with ca3: a_depth = st.selectbox("Depth A", ["Any"]+[d for d in ['Shallow','Medium','Deep','Ultra'] if d in work.get('depth',pd.Series()).values])
    with ca4: a_qid   = st.selectbox("Question A", ["Any"]+sorted(work['question_id'].unique().tolist()) if 'question_id' in work.columns else ["Any"])

    st.markdown("**Custom B — filter**")
    cb1, cb2, cb3, cb4 = st.columns(4)
    with cb1: b_agent = st.selectbox("Agent B", ["Any"]+sorted(work['agent'].unique().tolist()) if 'agent' in work.columns else ["Any"])
    with cb2: b_temp  = st.selectbox("Temp B",  ["Any"]+[t for t in ['ICE','NATIVE','FIRE'] if t in work.get('temperature',pd.Series()).values])
    with cb3: b_depth = st.selectbox("Depth B", ["Any"]+[d for d in ['Shallow','Medium','Deep','Ultra'] if d in work.get('depth',pd.Series()).values])
    with cb4: b_qid   = st.selectbox("Question B", ["Any"]+sorted(work['question_id'].unique().tolist()) if 'question_id' in work.columns else ["Any"])

    def apply_filter(df, agent, temp, depth, qid):
        d = df.copy()
        if agent != "Any" and 'agent' in d.columns:       d = d[d['agent']==agent]
        if temp  != "Any" and 'temperature' in d.columns: d = d[d['temperature']==temp]
        if depth != "Any" and 'depth' in d.columns:       d = d[d['depth']==depth]
        if qid   != "Any" and 'question_id' in d.columns: d = d[d['question_id']==qid]
        return d

    slice_a = apply_filter(work, a_agent, a_temp, a_depth, a_qid)
    slice_b = apply_filter(work, b_agent, b_temp, b_depth, b_qid)
    side_a = f"{a_agent}/{a_temp}/{a_depth}/{a_qid}"
    side_b = f"{b_agent}/{b_temp}/{b_depth}/{b_qid}"

    for _, ra in slice_a.iterrows():
        if len(slice_b):
            rb = slice_b.iloc[0]
            key = f"{ra.get('agent','')} · {ra.get('question_id','')} · {ra.get('temperature','')} · {ra.get('depth','')}"
            pairs.append((ra, rb, key))

# =============================================================================
# SCORE ALL PAIRS
# =============================================================================
if not pairs:
    st.warning("No matching pairs found. Try different filters or comparison mode.")
    st.stop()

scored = []
for ra, rb, key in pairs:
    cs_val = contrast_score(ra, rb)
    ss_val = sameness_score(ra, rb)
    iep_d  = iep_distance(ra, rb)
    cam_d  = cam_distance(ra, rb)
    flip   = vader_flip(ra, rb)
    lex    = lexical_overlap(ra.get('response_text',''), rb.get('response_text',''))
    scored.append({
        'key': key,
        'row_a': ra,
        'row_b': rb,
        'contrast': cs_val,
        'sameness': ss_val,
        'iep_dist': iep_d,
        'cam_dist': cam_d,
        'vader_flip': flip,
        'lex_overlap': lex,
    })

scored.sort(key=lambda x: x['contrast'] if sort_by=="Most Contrasting" else x['sameness'], reverse=True)
top = scored[:top_n]

# =============================================================================
# SUMMARY STATS
# =============================================================================
st.markdown('<div class="section-label">📈 Summary</div>', unsafe_allow_html=True)

all_contrast = [s['contrast'] for s in scored]
all_same     = [s['sameness'] for s in scored]
flips        = sum(1 for s in scored if s['vader_flip'])
high_contrast = sum(1 for s in scored if s['contrast'] > 60)

sc1, sc2, sc3, sc4, sc5 = st.columns(5)
with sc1: st.markdown(f'<div class="corpus-stat"><div class="big">{len(scored)}</div><div class="lbl">Total Pairs</div></div>', unsafe_allow_html=True)
with sc2: st.markdown(f'<div class="corpus-stat"><div class="big">{np.mean(all_contrast):.0f}</div><div class="lbl">Avg Contrast</div></div>', unsafe_allow_html=True)
with sc3: st.markdown(f'<div class="corpus-stat"><div class="big">{np.mean(all_same):.0f}</div><div class="lbl">Avg Sameness</div></div>', unsafe_allow_html=True)
with sc4: st.markdown(f'<div class="corpus-stat"><div class="big">{flips}</div><div class="lbl">VADER Flips</div></div>', unsafe_allow_html=True)
with sc5: st.markdown(f'<div class="corpus-stat"><div class="big">{high_contrast}</div><div class="lbl">High Contrast (>60)</div></div>', unsafe_allow_html=True)

# =============================================================================
# RESULTS TABLE
# =============================================================================
st.markdown(f'<div class="section-label">{"🔥 Most Contrasting" if sort_by=="Most Contrasting" else "🟢 Most Similar"} — Top {top_n} Pairs</div>', unsafe_allow_html=True)

table_rows = []
for s in top:
    table_rows.append({
        'Key': s['key'],
        'Contrast': s['contrast'],
        'Sameness': s['sameness'],
        'IEP Dist': s['iep_dist'],
        'CAM Dist': s['cam_dist'],
        'VADER Flip': '⚡ YES' if s['vader_flip'] else '—',
        'Lex Overlap%': s['lex_overlap'],
    })
st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

# =============================================================================
# PAIR CARDS — FULL TEXT
# =============================================================================
if show_full:
    st.markdown('<div class="section-label">📖 Response Pairs — Read These</div>', unsafe_allow_html=True)

    for i, s in enumerate(top):
        ra = s['row_a']
        rb = s['row_b']

        # Flags
        flags = []
        if s['vader_flip']:
            flags.append('<span class="finding-tag">⚡ VADER FLIP</span>')
        if s['contrast'] > 75:
            flags.append('<span class="finding-tag">🔥 HIGH CONTRAST</span>')
        if s['iep_dist'] > 30:
            flags.append('<span class="finding-tag">IEP DIVERGE</span>')
        if s['cam_dist'] > 25:
            flags.append('<span class="finding-tag">CAM DIVERGE</span>')
        if s['sameness'] > 70:
            flags.append('<span class="finding-tag green">🟢 SAME REGISTER</span>')
        if s['lex_overlap'] < 20:
            flags.append('<span class="finding-tag">DIFF VOCAB</span>')

        # Question text
        qtext = str(ra.get('question_text', ra.get('question_id', '')))[:120]

        # Side labels
        temp_a  = ra.get('temperature','')
        temp_b  = rb.get('temperature','')
        agent_a = ra.get('agent','A')
        agent_b = rb.get('agent','B')
        depth_a = ra.get('depth','')
        depth_b = rb.get('depth','')
        qid_a   = ra.get('question_id','')

        label_a = f"{TEMP_EMOJI.get(temp_a,'')} {agent_a} · {temp_a} · {depth_a} · {qid_a}"
        label_b = f"{TEMP_EMOJI.get(temp_b,'')} {agent_b} · {temp_b} · {depth_b} · {rb.get('question_id','')}"

        color_a = AGENT_COLORS_HEX.get(agent_a, '#4a90d9')
        color_b = AGENT_COLORS_HEX.get(agent_b, '#e05555')

        scores_a = format_iep(ra)
        scores_b = format_iep(rb)
        cam_a = format_cam(ra)
        cam_b = format_cam(rb)
        vader_a = f"VADER:{ra.get('vader_compound',0):.3f}"
        vader_b = f"VADER:{rb.get('vader_compound',0):.3f}"
        words_a = f"{ra.get('total_words',0):.0f}w"
        words_b = f"{rb.get('total_words',0):.0f}w"

        text_a = str(ra.get('response_text','')).replace('**','').replace('##','').replace('# ','')[:2000]
        text_b = str(rb.get('response_text','')).replace('**','').replace('##','').replace('# ','')[:2000]
        if len(str(ra.get('response_text',''))) > 2000: text_a += '...'
        if len(str(rb.get('response_text',''))) > 2000: text_b += '...'

        with st.expander(f"#{i+1}  ·  Contrast:{s['contrast']:.0f}  Sameness:{s['sameness']:.0f}  ·  {s['key']}", expanded=(i<3)):
            st.markdown(f"""
            <div style="margin-bottom:1rem;">
                <div style="font-family:'JetBrains Mono',monospace;font-size:0.8rem;color:#444;margin-bottom:0.6rem;font-style:italic;">
                    {qtext}
                </div>
                {' '.join(flags)}
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:1.2rem;">
                <div style="background:#f8f6f2;border-left:4px solid {color_a};padding:1.2rem;border-radius:0 8px 8px 0;border:1px solid #e0dcd4;">
                    <div style="font-family:'JetBrains Mono',monospace;font-size:0.75rem;font-weight:700;color:{color_a};letter-spacing:0.06em;margin-bottom:0.5rem;">{label_a}</div>
                    <div style="font-family:'JetBrains Mono',monospace;font-size:0.72rem;color:#666;margin-bottom:1rem;line-height:1.6;">{scores_a}<br>{cam_a}  {vader_a}  {words_a}</div>
                    <div style="font-family:'Source Serif 4',serif;font-size:0.95rem;line-height:1.8;color:#222;">{text_a}</div>
                </div>
                <div style="background:#f8f6f2;border-left:4px solid {color_b};padding:1.2rem;border-radius:0 8px 8px 0;border:1px solid #e0dcd4;">
                    <div style="font-family:'JetBrains Mono',monospace;font-size:0.75rem;font-weight:700;color:{color_b};letter-spacing:0.06em;margin-bottom:0.5rem;">{label_b}</div>
                    <div style="font-family:'JetBrains Mono',monospace;font-size:0.72rem;color:#666;margin-bottom:1rem;line-height:1.6;">{scores_b}<br>{cam_b}  {vader_b}  {words_b}</div>
                    <div style="font-family:'Source Serif 4',serif;font-size:0.95rem;line-height:1.8;color:#222;">{text_b}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# =============================================================================
# EXPORT
# =============================================================================
st.markdown('<div class="section-label">💾 Export</div>', unsafe_allow_html=True)

export_rows = []
for s in scored:
    ra, rb = s['row_a'], s['row_b']
    export_rows.append({
        'key': s['key'],
        'contrast': s['contrast'],
        'sameness': s['sameness'],
        'iep_dist': s['iep_dist'],
        'cam_dist': s['cam_dist'],
        'vader_flip': s['vader_flip'],
        'lex_overlap': s['lex_overlap'],
        'agent_a': ra.get('agent',''), 'temp_a': ra.get('temperature',''),
        'depth_a': ra.get('depth',''), 'qid_a': ra.get('question_id',''),
        'iep_a': format_iep(ra), 'vader_a': ra.get('vader_compound',0),
        'words_a': ra.get('total_words',0), 'response_a': ra.get('response_text',''),
        'agent_b': rb.get('agent',''), 'temp_b': rb.get('temperature',''),
        'depth_b': rb.get('depth',''), 'qid_b': rb.get('question_id',''),
        'iep_b': format_iep(rb), 'vader_b': rb.get('vader_compound',0),
        'words_b': rb.get('total_words',0), 'response_b': rb.get('response_text',''),
    })

csv_out = pd.DataFrame(export_rows).to_csv(index=False)
st.download_button(
    "📥 Download Contrast Report (CSV)",
    csv_out,
    "syniq_contrast_report.csv",
    "text/csv",
    key="dl_contrast"
)
