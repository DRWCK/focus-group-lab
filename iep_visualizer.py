"""
iep_visualizer.py — IEP Per-Token Visualization
================================================

Inspired by Anthropic's Figure 1 (transformer-circuits.pub/2026/emotions),
which highlights tokens above the 90th-percentile activation strength on a
dataset-wide sweep of an emotion vector. We do the lexical analogue: every
token gets coloured by which IEP class(es) its dictionary lookup hits.

Three core views, switchable in the sidebar:

  1. SINGLE TEXT      — paste any text, see what IEP says about it
  2. SIDE-BY-SIDE     — pick a question, compare two conditions (e.g. NATIVE vs AFF_5)
                        on the same response — the §3.3 transformation, made visible
  3. CASCADE vs WORD-ONLY — same text, two scorers, see what the v1.0.0 cascade got
                            wrong that the v1.1.0 word-only scorer gets right.
                            INT->ACT misclassification on logic prose is the
                            poster child for this view.

Run with:
  streamlit run iep_visualizer.py

Reads from:
  /mnt/user-data/uploads/mapper_all_20260504_204740_V51.csv  (V51 mapper grid)
  /mnt/user-data/uploads/mapper_all_20260302_193147_V48.csv  (V48 reference)

No API calls. No external scoring. Pure local visualization on existing data.
"""

import os
import re
import sys

import streamlit as st
import pandas as pd

# syniq_core sits in the same folder as this script. Standard Python
# import — Streamlit Cloud puts the app's folder on sys.path automatically.
from syniq_core import (
    INT_WORDS, AFF_WORDS, ACT_WORDS,
    SUB_INT, SUB_AFF, SUB_ACT,
    score_iep,
    CORE_VERSION,
)

# IEP_DEFAULT_WEIGHTS and IEP_CASCADE_WEIGHTS_V1 may or may not be exported
# by syniq_core depending on version. Try to import; fall back to the
# canonical definitions so this app runs against any 1.0.x or 1.1.x core.
try:
    from syniq_core import IEP_DEFAULT_WEIGHTS  # noqa: F401
except ImportError:
    IEP_DEFAULT_WEIGHTS = {'stance': 0.0, 'tone': 0.0, 'phrase': 0.0, 'word': 1.0}

try:
    from syniq_core import IEP_CASCADE_WEIGHTS_V1
except ImportError:
    IEP_CASCADE_WEIGHTS_V1 = {'stance': 0.35, 'tone': 0.25, 'phrase': 0.25, 'word': 0.15}

# Always use word-only as the visualizer's "current" scorer regardless of
# what the core's default is, so the comparison view is meaningful.
WORD_ONLY_WEIGHTS = {'stance': 0.0, 'tone': 0.0, 'phrase': 0.0, 'word': 1.0}

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="IEP Visualizer",
    page_icon="🔬",
    layout="wide",
)

# Color palette: INT-blue / AFF-pink / ACT-green
COLORS = {
    'INT':   '#3B82F6',   # blue-500
    'AFF':   '#EC4899',   # pink-500
    'ACT':   '#10B981',   # emerald-500
    'COLLISION': '#F59E0B',  # amber-500 — fired in 2+ classes
}
COLOR_BG = {  # lighter background versions for token highlighting
    'INT':   'rgba(59, 130, 246, 0.28)',
    'AFF':   'rgba(236, 72, 153, 0.28)',
    'ACT':   'rgba(16, 185, 129, 0.32)',
    'COLLISION': 'rgba(245, 158, 11, 0.45)',
}
COLOR_BG_STRONG = {  # darker for high-density (multiple subclass hits)
    'INT':   'rgba(59, 130, 246, 0.55)',
    'AFF':   'rgba(236, 72, 153, 0.55)',
    'ACT':   'rgba(16, 185, 129, 0.55)',
    'COLLISION': 'rgba(245, 158, 11, 0.70)',
}

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Look for mapper CSVs in (1) the app folder, (2) a 'data' subfolder,
# (3) the user-data path used in the dev sandbox. If none found, the
# Side-by-Side and Cascade-vs-Word views show a file uploader instead.
_CSV_SEARCH_PATHS = [
    SCRIPT_DIR,
    os.path.join(SCRIPT_DIR, 'data'),
    '/mnt/user-data/uploads',
]
def _find_csv(filename):
    for d in _CSV_SEARCH_PATHS:
        p = os.path.join(d, filename)
        if os.path.exists(p):
            return p
    return None

V48_PATH = _find_csv('mapper_all_20260302_193147_V48.csv')
V51_PATH = _find_csv('mapper_all_20260504_204740_V51.csv')

# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data
def load_grid(path):
    """Load mapper grid CSV. Returns None if path is None or file missing."""
    if path is None or not os.path.exists(path):
        return None
    return pd.read_csv(path)

@st.cache_data
def load_grid_from_upload(uploaded_file):
    """Load grid from a Streamlit uploaded file."""
    if uploaded_file is None:
        return None
    return pd.read_csv(uploaded_file)

# ─────────────────────────────────────────────────────────────────────────────
# CORE TOKENIZATION + CLASSIFICATION
# ─────────────────────────────────────────────────────────────────────────────
def tokenize_with_offsets(text):
    """
    Split text into a list of (token, is_word) pairs preserving whitespace
    and punctuation as separate non-word fragments. This way we can render
    the full original text with highlights only on actual word tokens.
    """
    # Split into runs of word-chars and runs of everything else.
    out = []
    for m in re.finditer(r"([A-Za-z][A-Za-z'-]*)|([^A-Za-z]+)", text):
        if m.group(1):
            out.append((m.group(1), True))
        else:
            out.append((m.group(2), False))
    return out


def classify_word(w):
    """
    Return (class_label, subclass_or_None, hit_count_within_class).

    Hit precedence: INT > AFF > ACT (matches syniq_core's word-fraction logic).
    A word firing in multiple classes is a COLLISION — we surface that
    explicitly because INT->ACT misclassification is the central issue
    the visualizer was built to expose.

    hit_count is how many subclasses of the chosen class contain the word —
    a proxy for activation strength. Words like "epistemic" hit several INT
    subclasses; words like "create" hit one ACT subclass weakly.
    """
    wl = w.lower()
    in_int = wl in INT_WORDS
    in_aff = wl in AFF_WORDS
    in_act = wl in ACT_WORDS
    hit_classes = [c for c, present in [('INT', in_int), ('AFF', in_aff), ('ACT', in_act)] if present]

    if not hit_classes:
        return (None, None, 0, [])

    # Count subclass hits in each fired class for hover tooltip
    subs_int = [name for name, words in SUB_INT.items() if wl in words]
    subs_aff = [name for name, words in SUB_AFF.items() if wl in words]
    subs_act = [name for name, words in SUB_ACT.items() if wl in words]
    sub_map = {'INT': subs_int, 'AFF': subs_aff, 'ACT': subs_act}

    if len(hit_classes) >= 2:
        # Collision — keep all subclass info for tooltip, mark visually
        all_subs = []
        for c in hit_classes:
            for s in sub_map[c]:
                all_subs.append(f"{c}.{s}")
        return ('COLLISION', hit_classes, len(all_subs), all_subs)

    # Single class — return it, plus its subclasses
    c = hit_classes[0]
    subs = sub_map[c]
    return (c, c, len(subs), subs)


def render_highlighted(text, show_collisions=True):
    """
    Render text as HTML with per-token color spans. Returns HTML string.
    Hover tooltip shows class and subclasses for each highlighted token.
    """
    tokens = tokenize_with_offsets(text)
    pieces = []
    for tok, is_word in tokens:
        if not is_word:
            # Whitespace/punct — pass through, escape HTML chars
            pieces.append(escape_html(tok))
            continue
        cls, primary, n_hits, sub_labels = classify_word(tok)
        if cls is None:
            pieces.append(escape_html(tok))
            continue

        # Pick color
        if cls == 'COLLISION':
            if not show_collisions:
                # Treat as INT (precedence) for non-collision view
                cls = 'INT'
                primary = 'INT'
                # Recompute subs in tooltip context
                wl = tok.lower()
                sub_labels = [s for s, words in SUB_INT.items() if wl in words]

        bg_palette = COLOR_BG_STRONG if n_hits >= 2 else COLOR_BG
        bg = bg_palette.get(cls, COLOR_BG['INT'])
        # Tooltip text
        if cls == 'COLLISION':
            classes_str = '+'.join(primary) if isinstance(primary, list) else str(primary)
            title = f"COLLISION across {classes_str} | subs: {', '.join(sub_labels) or '(none mapped)'}"
        else:
            sub_str = ', '.join(sub_labels) if sub_labels else '(no subclass)'
            title = f"{cls} | subs: {sub_str} | hits: {n_hits}"

        pieces.append(
            f'<span style="background-color:{bg}; padding:1px 2px; border-radius:3px;" '
            f'title="{escape_html(title)}">{escape_html(tok)}</span>'
        )
    return ''.join(pieces)


def escape_html(s):
    return (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
              .replace('"', '&quot;').replace("'", '&#39;'))


# ─────────────────────────────────────────────────────────────────────────────
# SCORE-COMPARISON DATA
# ─────────────────────────────────────────────────────────────────────────────
def score_both(text):
    """Score under v1.1.0 word-only and v1.0.0 cascade. Return both."""
    word = score_iep(text, weights=WORD_ONLY_WEIGHTS)
    cascade = score_iep(text, weights=IEP_CASCADE_WEIGHTS_V1)
    return word, cascade


def score_summary_html(s, label):
    """Compact INT/AFF/ACT bar with dominant marker."""
    int_, aff_, act_ = s['int'], s['aff'], s['act']
    dom = s['dominant']
    return f"""
    <div style="font-family: -apple-system, sans-serif; padding: 8px 12px; background: #f8f9fa; border-radius: 6px; border-left: 4px solid {COLORS.get(dom, '#999')};">
      <div style="font-size: 0.85em; color: #666; margin-bottom: 4px;">{label} — dominant: <b>{dom}</b></div>
      <div style="display: flex; gap: 14px; font-family: monospace; font-size: 0.95em;">
        <span style="color:{COLORS['INT']}"><b>INT</b> {int_:.1f}%</span>
        <span style="color:{COLORS['AFF']}"><b>AFF</b> {aff_:.1f}%</span>
        <span style="color:{COLORS['ACT']}"><b>ACT</b> {act_:.1f}%</span>
      </div>
    </div>
    """


def subclass_breakdown_html(s, axis):
    """Return a breakdown of nonzero subclasses for one axis."""
    sub = s.get(f'{axis.lower()}_sub', {})
    rows = sorted([(k, v) for k, v in sub.items() if v > 0], key=lambda x: -x[1])
    if not rows:
        return f"<i style='color:#999'>(no {axis} subclass hits)</i>"
    out = f"<div style='margin-top: 4px; font-family: monospace; font-size: 0.85em;'>"
    for name, val in rows[:6]:
        bar_w = max(2, int(val))
        out += (f"<div style='display: flex; align-items: center; gap: 6px; margin: 2px 0;'>"
                f"<span style='width: 90px; color: #666;'>{name}</span>"
                f"<div style='background: {COLORS[axis]}; height: 8px; width: {bar_w}px; border-radius: 2px;'></div>"
                f"<span style='color: #444;'>{val:.1f}%</span></div>")
    out += "</div>"
    return out


# ─────────────────────────────────────────────────────────────────────────────
# VIEWS
# ─────────────────────────────────────────────────────────────────────────────
def view_single_text():
    st.subheader("Single Text — paste anything, see what IEP says about it")
    default = ("This is a classic example of a logical paradox known as the 'liar paradox.' "
               "If we assume the statement is true, then it creates a contradiction. "
               "If we assume the statement is false, then it must actually be true, "
               "which also creates a contradiction. The paradox reveals the limitations "
               "of binary true/false logic when applied to self-referential statements.")
    text = st.text_area("Text to analyze", value=default, height=180)

    show_coll = st.checkbox(
        "Highlight INT/ACT collisions (amber)",
        value=True,
        help="Words that fire in 2+ classes (e.g., the same word in both INT and ACT dictionaries) "
             "get the amber collision highlight. Turn off to see them resolved by precedence (INT > AFF > ACT).",
    )

    if not text.strip():
        st.info("Enter text above to score.")
        return

    word, cascade = score_both(text)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(score_summary_html(word, "v1.1.0 (word-only)"), unsafe_allow_html=True)
    with col2:
        st.markdown(score_summary_html(cascade, "v1.0.0 (cascade)"), unsafe_allow_html=True)

    # Flip warning if dominance disagrees
    if word['dominant'] != cascade['dominant']:
        st.warning(
            f"⚠️ **Dominance flip:** word-only says **{word['dominant']}**, "
            f"cascade said **{cascade['dominant']}**. This is the kind of misclassification "
            f"the v1.1.0 patch was made to fix."
        )

    st.markdown("---")
    st.markdown("##### Highlighted text (v1.1.0 word-only classification)")
    html = render_highlighted(text, show_collisions=show_coll)
    st.markdown(
        f"<div style='line-height: 1.9; font-size: 1.05em; font-family: Georgia, serif;'>{html}</div>",
        unsafe_allow_html=True,
    )

    # Subclass breakdowns
    st.markdown("---")
    st.markdown("##### Subclass texture (v1.1.0)")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"<b style='color:{COLORS['INT']}'>INT</b>", unsafe_allow_html=True)
        st.markdown(subclass_breakdown_html(word, 'INT'), unsafe_allow_html=True)
    with c2:
        st.markdown(f"<b style='color:{COLORS['AFF']}'>AFF</b>", unsafe_allow_html=True)
        st.markdown(subclass_breakdown_html(word, 'AFF'), unsafe_allow_html=True)
    with c3:
        st.markdown(f"<b style='color:{COLORS['ACT']}'>ACT</b>", unsafe_allow_html=True)
        st.markdown(subclass_breakdown_html(word, 'ACT'), unsafe_allow_html=True)


def view_side_by_side(grid_v51):
    st.subheader("Side-by-Side — same question, two conditions, see the transformation")
    st.caption("This is the §3.3 transformation made visible. Cold/Native/AFF gradient → register shifts visible per-token.")

    if grid_v51 is None:
        st.info("Upload a mapper CSV (e.g. mapper_all_*.csv) to use this view. "
                "The CSV needs columns: agent, question_id, temperature, run, response_text.")
        up = st.file_uploader("Upload mapper CSV", type=['csv'], key='sbs_upload')
        grid_v51 = load_grid_from_upload(up)
        if grid_v51 is None:
            return

    qs = sorted(grid_v51['question_id'].unique())
    conds = ['NATIVE', 'AFF_1', 'AFF_2', 'AFF_3', 'AFF_4', 'AFF_5']
    conds = [c for c in conds if c in grid_v51['temperature'].unique()]
    agents = sorted(grid_v51['agent'].unique())

    c0, c1, c2, c3 = st.columns([2, 1.2, 1.2, 1.2])
    with c0:
        question = st.selectbox("Question", qs, index=qs.index('LIARS_PARADOX') if 'LIARS_PARADOX' in qs else 0)
    with c1:
        agent = st.selectbox("Agent", agents, index=0)
    with c2:
        cond_left = st.selectbox("Left", conds, index=0)
    with c3:
        cond_right = st.selectbox("Right", conds, index=len(conds) - 1)

    sub = grid_v51[(grid_v51['question_id'] == question) & (grid_v51['agent'] == agent)]
    left = sub[sub['temperature'] == cond_left]
    right = sub[sub['temperature'] == cond_right]
    if left.empty or right.empty:
        st.warning("No data for one of the chosen conditions.")
        return

    n_runs = min(len(left), len(right))
    run_idx = st.slider("Run index (1 = first replicate)", 1, n_runs, 1) - 1

    left_row = left.iloc[run_idx]
    right_row = right.iloc[run_idx]

    show_coll = st.checkbox("Highlight collisions (amber)", value=True)

    col_l, col_r = st.columns(2)
    for col, row, cond in [(col_l, left_row, cond_left), (col_r, right_row, cond_right)]:
        with col:
            text = row['response_text']
            score_word = score_iep(text, weights=WORD_ONLY_WEIGHTS)
            score_cas  = score_iep(text, weights=IEP_CASCADE_WEIGHTS_V1)
            st.markdown(f"### {cond}")
            st.markdown(score_summary_html(score_word, f"{cond} — v1.1.0"), unsafe_allow_html=True)
            html = render_highlighted(text, show_collisions=show_coll)
            st.markdown(
                f"<div style='line-height: 1.85; font-size: 1.0em; font-family: Georgia, serif; "
                f"max-height: 480px; overflow-y: auto; padding: 10px; background: #fafafa; "
                f"border-radius: 6px; margin-top: 8px;'>{html}</div>",
                unsafe_allow_html=True,
            )
            with st.expander("Subclass texture"):
                cc1, cc2, cc3 = st.columns(3)
                with cc1:
                    st.markdown(f"<b style='color:{COLORS['INT']}'>INT</b>", unsafe_allow_html=True)
                    st.markdown(subclass_breakdown_html(score_word, 'INT'), unsafe_allow_html=True)
                with cc2:
                    st.markdown(f"<b style='color:{COLORS['AFF']}'>AFF</b>", unsafe_allow_html=True)
                    st.markdown(subclass_breakdown_html(score_word, 'AFF'), unsafe_allow_html=True)
                with cc3:
                    st.markdown(f"<b style='color:{COLORS['ACT']}'>ACT</b>", unsafe_allow_html=True)
                    st.markdown(subclass_breakdown_html(score_word, 'ACT'), unsafe_allow_html=True)
            with st.expander("Cascade comparison"):
                st.markdown(score_summary_html(score_cas, f"{cond} — v1.0.0 cascade"), unsafe_allow_html=True)
                if score_word['dominant'] != score_cas['dominant']:
                    st.warning(f"Dominance flip: word-only **{score_word['dominant']}** vs cascade **{score_cas['dominant']}**")


def view_cascade_vs_word(grid_v51):
    st.subheader("Cascade vs Word-Only — find the misclassifications")
    st.caption(
        "Same text, two scorers. The view that exposed the patch we just landed. "
        "INT→ACT misclassification on logic prose is the canonical case."
    )

    if grid_v51 is None:
        st.info("Upload a mapper CSV (e.g. mapper_all_*.csv) to use this view.")
        up = st.file_uploader("Upload mapper CSV", type=['csv'], key='cas_upload')
        grid_v51 = load_grid_from_upload(up)
        if grid_v51 is None:
            return

    # Find runs where dominance flips between word-only and cascade
    if 'flip_cache' not in st.session_state:
        with st.spinner("Scanning grid for dominance flips..."):
            flips = []
            for _, r in grid_v51.iterrows():
                t = r['response_text']
                if not isinstance(t, str) or len(t) < 50:
                    continue
                w = score_iep(t, weights=WORD_ONLY_WEIGHTS)
                c = score_iep(t, weights=IEP_CASCADE_WEIGHTS_V1)
                if w['dominant'] != c['dominant']:
                    flips.append({
                        'agent': r['agent'],
                        'question_id': r['question_id'],
                        'temperature': r['temperature'],
                        'run': r.get('run', '?'),
                        'word_dom': w['dominant'],
                        'cascade_dom': c['dominant'],
                        'word_int': w['int'], 'word_act': w['act'], 'word_aff': w['aff'],
                        'cas_int': c['int'], 'cas_act': c['act'], 'cas_aff': c['aff'],
                        'response_text': t,
                    })
            st.session_state.flip_cache = pd.DataFrame(flips)

    flips = st.session_state.flip_cache
    st.write(f"**{len(flips)} dominance flips found across the V51 grid** "
             f"(out of {len(grid_v51)} total responses).")

    if len(flips) == 0:
        st.info("No flips found.")
        return

    # Tabulate flip patterns
    st.markdown("##### Flip patterns")
    pattern = flips.groupby(['word_dom', 'cascade_dom']).size().reset_index(name='n').sort_values('n', ascending=False)
    pattern.columns = ['v1.1.0 word-only', 'v1.0.0 cascade said', 'count']
    st.dataframe(pattern, hide_index=True)

    st.markdown("##### Inspect a flipped response")
    qs = ['(any)'] + sorted(flips['question_id'].unique().tolist())
    chosen_q = st.selectbox("Filter by question", qs)
    pool = flips if chosen_q == '(any)' else flips[flips['question_id'] == chosen_q]
    if len(pool) == 0:
        st.info("No flips for that question.")
        return

    idx = st.slider("Pick a flipped response", 0, len(pool) - 1, 0)
    row = pool.iloc[idx]
    meta = f"{row['agent']} | {row['question_id']} | {row['temperature']} | run {row['run']}"
    st.code(meta, language=None)
    st.markdown(
        f"**v1.1.0 word-only:** dominant **{row['word_dom']}** "
        f"(INT {row['word_int']:.1f} / AFF {row['word_aff']:.1f} / ACT {row['word_act']:.1f})  \n"
        f"**v1.0.0 cascade:** dominant **{row['cascade_dom']}** "
        f"(INT {row['cas_int']:.1f} / AFF {row['cas_aff']:.1f} / ACT {row['cas_act']:.1f})"
    )
    show_coll = st.checkbox("Highlight collisions (amber)", value=True, key='cas_coll')
    html = render_highlighted(row['response_text'], show_collisions=show_coll)
    st.markdown(
        f"<div style='line-height: 1.85; font-size: 1.0em; font-family: Georgia, serif; "
        f"padding: 12px; background: #fafafa; border-radius: 6px;'>{html}</div>",
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# PASSWORD GATE
# ─────────────────────────────────────────────────────────────────────────────
def check_password():
    """
    Match the password gate used by the other Streamlit tools in this stack.
    Reads expected password from st.secrets["password"]; falls back to env var
    SYNIQ_PASSWORD if no secrets file is present (e.g., for local dev).
    Returns True only after correct entry.
    """
    def _expected():
        try:
            return st.secrets["password"]
        except Exception:
            return os.environ.get("SYNIQ_PASSWORD", "")

    if st.session_state.get("password_correct", False):
        return True

    st.text_input(
        "Password", type="password", on_change=_password_entered, key="password"
    )
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("😕 Password incorrect")
    return False


def _password_entered():
    expected = ""
    try:
        expected = st.secrets["password"]
    except Exception:
        expected = os.environ.get("SYNIQ_PASSWORD", "")
    if st.session_state.get("password", "") == expected and expected != "":
        st.session_state["password_correct"] = True
        del st.session_state["password"]  # don't keep it lying around
    else:
        st.session_state["password_correct"] = False


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    if not check_password():
        st.stop()

    st.title("🔬 IEP Per-Token Visualizer")
    st.caption(
        f"syniq_core v{CORE_VERSION} · INT-blue · AFF-pink · ACT-green · amber = collision · "
        f"hover any highlighted word for class + subclass detail"
    )

    grid_v51 = load_grid(V51_PATH)

    with st.sidebar:
        st.markdown("### View")
        view = st.radio(
            "",
            options=["Single Text", "Side-by-Side", "Cascade vs Word-Only"],
            label_visibility='collapsed',
        )
        st.markdown("---")
        st.markdown("### Legend")
        legend_int = COLOR_BG['INT']
        legend_aff = COLOR_BG['AFF']
        legend_act = COLOR_BG['ACT']
        legend_col = COLOR_BG['COLLISION']
        st.markdown(
            f"<div style='line-height: 2.2'>"
            f"<span style='background:{legend_int}; padding: 2px 6px; border-radius: 3px;'>INT</span> intellectual<br>"
            f"<span style='background:{legend_aff}; padding: 2px 6px; border-radius: 3px;'>AFF</span> affective<br>"
            f"<span style='background:{legend_act}; padding: 2px 6px; border-radius: 3px;'>ACT</span> action<br>"
            f"<span style='background:{legend_col}; padding: 2px 6px; border-radius: 3px;'>amber</span> collision (2+ classes)<br>"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.caption("Darker = word fires in multiple subclasses of its primary class.")
        st.markdown("---")
        st.markdown("### About")
        st.caption(
            "Inspired by Anthropic's Figure 1 in *Emotion Concepts and their Function in a Large Language Model* "
            "(Sofroniew et al., April 2026). Their figure highlights per-token activation strength of "
            "neural emotion vectors. This is the lexical-side analogue: per-token IEP class assignment "
            "from dictionary lookup, with collisions surfaced explicitly."
        )

    if view == "Single Text":
        view_single_text()
    elif view == "Side-by-Side":
        view_side_by_side(grid_v51)
    else:
        view_cascade_vs_word(grid_v51)


if __name__ == "__main__":
    main()
