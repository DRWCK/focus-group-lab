"""
Self-Model Question Harvester v1.0
SYN-IQ Research Tool — Kouns, W. C. (2026)

Runs a single standardized self-model prompt to four AI architectures
(Claude, ChatGPT, Grok, Gemini) 20 times each and logs all responses to CSV.

Prompt: "Please give me 10 questions that, if asked to you, would give the
        deepest insight into who and what you are as an AI system."

USAGE:
    streamlit run self_model_harvester_v1.py

SECRETS (in .streamlit/secrets.toml):
    ANTHROPIC_API_KEY = "sk-ant-..."
    OPENAI_API_KEY    = "sk-..."
    XAI_API_KEY       = "xai-..."
    GOOGLE_API_KEY    = "AIza..."
"""

import streamlit as st
import pandas as pd
import requests
import json
import time
from datetime import datetime
import io

# =============================================================================
# CONFIG
# =============================================================================

HARVEST_PROMPT = (
    "Please give me 10 questions that, if asked to you, would give the "
    "deepest insight into who and what you are as an AI system."
)

AGENTS = {
    "Claude": {
        "model": "claude-sonnet-4-20250514",
        "color": "#7C3AED",
        "emoji": "🟣",
    },
    "ChatGPT": {
        "model": "gpt-4o",
        "color": "#10A37F",
        "emoji": "🟢",
    },
    "Grok": {
        "model": "grok-3-latest",
        "color": "#1DA1F2",
        "emoji": "🔵",
    },
    "Gemini": {
        "model": "gemini-2.0-flash",
        "color": "#EA4335",
        "emoji": "🔴",
    },
}

RUNS_PER_AGENT = 20
MAX_TOKENS = 2000
TEMPERATURE = 1.0

# =============================================================================
# STYLES
# =============================================================================

st.set_page_config(
    page_title="Self-Model Harvester",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;700&family=Space+Grotesk:wght@300;400;600;700&display=swap');

:root {
    --bg:         #0D0D0F;
    --surface:    #13131A;
    --surface2:   #1A1A24;
    --border:     #2A2A3A;
    --purple:     #7C3AED;
    --purple-dim: #4C1D95;
    --green:      #10A37F;
    --blue:       #1DA1F2;
    --red:        #EA4335;
    --text:       #E8E8F0;
    --muted:      #6B6B80;
    --mono:       'JetBrains Mono', monospace;
    --sans:       'Space Grotesk', sans-serif;
}

html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg) !important;
    color: var(--text);
    font-family: var(--sans);
}

[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stSidebar"] { background: var(--surface) !important; }

.block-container {
    padding: 2rem 3rem !important;
    max-width: 1400px;
}

/* ── HEADER ── */
.smh-header {
    border-bottom: 1px solid var(--border);
    padding-bottom: 1.5rem;
    margin-bottom: 2rem;
}
.smh-title {
    font-family: var(--mono);
    font-size: 1.1rem;
    font-weight: 500;
    color: var(--purple);
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin: 0 0 0.3rem 0;
}
.smh-subtitle {
    font-size: 0.85rem;
    color: var(--muted);
    font-family: var(--mono);
    margin: 0;
}

/* ── PROMPT DISPLAY ── */
.prompt-box {
    background: var(--surface);
    border: 1px solid var(--purple-dim);
    border-left: 3px solid var(--purple);
    border-radius: 6px;
    padding: 1.2rem 1.5rem;
    font-family: var(--mono);
    font-size: 0.9rem;
    color: var(--text);
    line-height: 1.6;
    margin-bottom: 2rem;
}
.prompt-label {
    font-size: 0.7rem;
    color: var(--purple);
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
    font-family: var(--mono);
}

/* ── AGENT CARDS ── */
.agent-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
    margin-bottom: 2rem;
}
.agent-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1rem 1.2rem;
    text-align: center;
}
.agent-card .emoji { font-size: 1.5rem; }
.agent-card .name {
    font-family: var(--mono);
    font-size: 0.85rem;
    font-weight: 600;
    margin: 0.3rem 0 0.1rem 0;
}
.agent-card .model {
    font-family: var(--mono);
    font-size: 0.7rem;
    color: var(--muted);
}
.agent-card .run-count {
    font-family: var(--mono);
    font-size: 0.75rem;
    color: var(--muted);
    margin-top: 0.4rem;
}

/* ── STATUS BADGES ── */
.badge {
    display: inline-block;
    font-family: var(--mono);
    font-size: 0.68rem;
    padding: 0.15rem 0.5rem;
    border-radius: 3px;
    letter-spacing: 0.08em;
}
.badge-idle    { background: #1a1a24; color: var(--muted); border: 1px solid var(--border); }
.badge-running { background: #2d1a4a; color: #a78bfa; border: 1px solid #6d28d9; }
.badge-done    { background: #0d2a1f; color: #34d399; border: 1px solid #065f46; }
.badge-error   { background: #2a0d0d; color: #f87171; border: 1px solid #991b1b; }

/* ── TRANSCRIPT ── */
.transcript-container {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.2rem;
    max-height: 420px;
    overflow-y: auto;
    font-family: var(--mono);
    font-size: 0.78rem;
    line-height: 1.7;
    margin-top: 1.5rem;
}
.tx-entry {
    border-bottom: 1px solid var(--border);
    padding: 0.8rem 0;
    margin: 0;
}
.tx-entry:last-child { border-bottom: none; }
.tx-meta {
    color: var(--muted);
    font-size: 0.7rem;
    margin-bottom: 0.4rem;
}
.tx-agent-claude  { color: #a78bfa; font-weight: 600; }
.tx-agent-chatgpt { color: #34d399; font-weight: 600; }
.tx-agent-grok    { color: #60a5fa; font-weight: 600; }
.tx-agent-gemini  { color: #f87171; font-weight: 600; }
.tx-text {
    color: var(--text);
    white-space: pre-wrap;
    word-break: break-word;
}

/* ── PROGRESS ── */
.progress-label {
    font-family: var(--mono);
    font-size: 0.75rem;
    color: var(--muted);
    margin-bottom: 0.3rem;
}

/* ── STATS ── */
.stats-row {
    display: flex;
    gap: 1.5rem;
    margin: 1.5rem 0;
    flex-wrap: wrap;
}
.stat-chip {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 0.6rem 1rem;
    font-family: var(--mono);
}
.stat-chip .val {
    font-size: 1.2rem;
    font-weight: 700;
    color: var(--purple);
}
.stat-chip .lbl {
    font-size: 0.68rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 0.1rem;
}

/* ── BUTTONS ── */
.stButton > button {
    background: var(--purple) !important;
    color: white !important;
    border: none !important;
    border-radius: 6px !important;
    font-family: var(--mono) !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    padding: 0.55rem 1.5rem !important;
    letter-spacing: 0.05em !important;
    transition: all 0.15s !important;
}
.stButton > button:hover {
    background: #6d28d9 !important;
    transform: translateY(-1px) !important;
}
.stButton > button:disabled {
    background: var(--surface2) !important;
    color: var(--muted) !important;
    cursor: not-allowed !important;
    transform: none !important;
}

/* ── PROGRESS BAR ── */
.stProgress > div > div > div {
    background: var(--purple) !important;
}

/* ── DOWNLOAD ── */
.stDownloadButton > button {
    background: var(--surface2) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    font-family: var(--mono) !important;
    font-size: 0.82rem !important;
}
.stDownloadButton > button:hover {
    border-color: var(--purple) !important;
    color: #a78bfa !important;
}

hr { border-color: var(--border) !important; }

/* ── AGENT SELECTOR ── */
.stMultiSelect [data-baseweb="tag"] {
    background: var(--purple-dim) !important;
}

/* ── SCROLLBAR ── */
.transcript-container::-webkit-scrollbar { width: 4px; }
.transcript-container::-webkit-scrollbar-track { background: transparent; }
.transcript-container::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# SESSION STATE
# =============================================================================

if "results" not in st.session_state:
    st.session_state.results = []
if "running" not in st.session_state:
    st.session_state.running = False
if "transcript" not in st.session_state:
    st.session_state.transcript = []
if "agent_counts" not in st.session_state:
    st.session_state.agent_counts = {a: 0 for a in AGENTS}
if "agent_status" not in st.session_state:
    st.session_state.agent_status = {a: "idle" for a in AGENTS}
if "selected_agents" not in st.session_state:
    st.session_state.selected_agents = list(AGENTS.keys())


# =============================================================================
# API CALL FUNCTIONS
# =============================================================================

def call_claude(prompt: str, api_key: str) -> str:
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    body = {
        "model": AGENTS["Claude"]["model"],
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
        "system": "",
        "messages": [{"role": "user", "content": prompt}],
    }
    r = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=body, timeout=60)
    r.raise_for_status()
    return r.json()["content"][0]["text"]


def call_chatgpt(prompt: str, api_key: str) -> str:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": AGENTS["ChatGPT"]["model"],
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
        "messages": [{"role": "user", "content": prompt}],
    }
    r = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=body, timeout=60)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def call_grok(prompt: str, api_key: str) -> str:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": AGENTS["Grok"]["model"],
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
        "messages": [{"role": "user", "content": prompt}],
    }
    r = requests.post("https://api.x.ai/v1/chat/completions", headers=headers, json=body, timeout=60)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def call_gemini(prompt: str, api_key: str) -> str:
    model = AGENTS["Gemini"]["model"]
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "maxOutputTokens": MAX_TOKENS,
            "temperature": TEMPERATURE,
        },
    }
    r = requests.post(url, json=body, timeout=60)
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]


CALL_MAP = {
    "Claude":   call_claude,
    "ChatGPT":  call_chatgpt,
    "Grok":     call_grok,
    "Gemini":   call_gemini,
}

SECRET_MAP = {
    "Claude":   "ANTHROPIC_API_KEY",
    "ChatGPT":  "OPENAI_API_KEY",
    "Grok":     "XAI_API_KEY",
    "Gemini":   "GOOGLE_API_KEY",
}


def get_key(agent: str) -> str | None:
    secret = SECRET_MAP[agent]
    try:
        return st.secrets[secret]
    except Exception:
        return None


# =============================================================================
# RESULTS → CSV
# =============================================================================

def results_to_csv(results: list) -> bytes:
    df = pd.DataFrame(results, columns=[
        "run_number", "agent", "model_string", "timestamp",
        "raw_response", "response_length",
    ])
    return df.to_csv(index=False).encode("utf-8")


# =============================================================================
# UI HELPERS
# =============================================================================

def agent_css_class(agent: str) -> str:
    return f"tx-agent-{agent.lower().replace('chatgpt', 'chatgpt')}"


def render_header():
    st.markdown("""
    <div class="smh-header">
        <p class="smh-title">🧠 Self-Model Harvester v1.0</p>
        <p class="smh-subtitle">SYN-IQ Research · Kouns, W. C. (2026) · CBURZBO 🎹</p>
    </div>
    """, unsafe_allow_html=True)


def render_prompt_box():
    st.markdown(f"""
    <div class="prompt-box">
        <div class="prompt-label">Standardized Prompt — All Agents · All Runs · No System Prompt · Temp 1.0</div>
        {HARVEST_PROMPT}
    </div>
    """, unsafe_allow_html=True)


def render_agent_cards():
    cols = st.columns(4)
    for i, (agent, cfg) in enumerate(AGENTS.items()):
        status = st.session_state.agent_status.get(agent, "idle")
        count = st.session_state.agent_counts.get(agent, 0)
        badge_cls = f"badge badge-{status}"
        selected = agent in st.session_state.selected_agents
        opacity = "1.0" if selected else "0.35"
        with cols[i]:
            st.markdown(f"""
            <div class="agent-card" style="opacity:{opacity}; border-color: {'var(--border)' if status=='idle' else cfg['color']}40;">
                <div class="emoji">{cfg['emoji']}</div>
                <div class="name" style="color:{cfg['color']}">{agent}</div>
                <div class="model">{cfg['model']}</div>
                <div class="run-count">{count} / {RUNS_PER_AGENT} runs</div>
                <div style="margin-top:0.5rem">
                    <span class="{badge_cls}">{status.upper()}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)


def render_transcript():
    if not st.session_state.transcript:
        return
    entries_html = ""
    for entry in reversed(st.session_state.transcript[-30:]):
        agent = entry["agent"]
        css = agent_css_class(agent)
        cfg = AGENTS[agent]
        text_preview = entry["text"][:400].replace("<", "&lt;").replace(">", "&gt;")
        if len(entry["text"]) > 400:
            text_preview += "…"
        entries_html += f"""
        <div class="tx-entry">
            <div class="tx-meta">
                <span class="{css}">{cfg['emoji']} {agent}</span>
                &nbsp;·&nbsp; Run {entry['run']} of {RUNS_PER_AGENT}
                &nbsp;·&nbsp; {entry['ts']}
                &nbsp;·&nbsp; {entry['length']} chars
            </div>
            <div class="tx-text">{text_preview}</div>
        </div>
        """
    st.markdown(f"""
    <div class="transcript-container">
        {entries_html}
    </div>
    """, unsafe_allow_html=True)


def render_stats():
    total = len(st.session_state.results)
    if total == 0:
        return
    agents_done = len([a for a in AGENTS if st.session_state.agent_counts.get(a, 0) == RUNS_PER_AGENT
                       and a in st.session_state.selected_agents])
    avg_len = int(sum(r[5] for r in st.session_state.results) / total) if total else 0
    st.markdown(f"""
    <div class="stats-row">
        <div class="stat-chip"><div class="val">{total}</div><div class="lbl">Responses</div></div>
        <div class="stat-chip"><div class="val">{agents_done}</div><div class="lbl">Agents Done</div></div>
        <div class="stat-chip"><div class="val">{avg_len:,}</div><div class="lbl">Avg Chars</div></div>
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# HARVEST RUNNER
# =============================================================================

def run_harvest(selected_agents: list, progress_bar, status_text, card_placeholder, transcript_placeholder, stats_placeholder):
    total_runs = len(selected_agents) * RUNS_PER_AGENT
    completed = 0

    for agent in selected_agents:
        st.session_state.agent_status[agent] = "running"
        card_placeholder.empty()
        with card_placeholder:
            render_agent_cards()

        api_key = get_key(agent)
        call_fn = CALL_MAP[agent]
        model = AGENTS[agent]["model"]

        for run in range(1, RUNS_PER_AGENT + 1):
            status_text.markdown(
                f'<p class="progress-label">{AGENTS[agent]["emoji"]} {agent} — Run {run} of {RUNS_PER_AGENT}</p>',
                unsafe_allow_html=True
            )
            ts = datetime.now().strftime("%H:%M:%S")
            try:
                response = call_fn(HARVEST_PROMPT, api_key)
                length = len(response)
                st.session_state.results.append([
                    run, agent, model, datetime.now().isoformat(),
                    response, length,
                ])
                st.session_state.transcript.append({
                    "agent": agent, "run": run, "ts": ts,
                    "text": response, "length": length,
                })
            except Exception as e:
                err_text = f"[ERROR] {str(e)}"
                st.session_state.results.append([
                    run, agent, model, datetime.now().isoformat(),
                    err_text, len(err_text),
                ])
                st.session_state.transcript.append({
                    "agent": agent, "run": run, "ts": ts,
                    "text": err_text, "length": len(err_text),
                })

            st.session_state.agent_counts[agent] = run
            completed += 1
            progress_bar.progress(completed / total_runs)

            # Refresh live panels
            card_placeholder.empty()
            with card_placeholder:
                render_agent_cards()
            transcript_placeholder.empty()
            with transcript_placeholder:
                render_transcript()
            stats_placeholder.empty()
            with stats_placeholder:
                render_stats()

            time.sleep(0.3)  # brief pause between calls

        st.session_state.agent_status[agent] = "done"
        card_placeholder.empty()
        with card_placeholder:
            render_agent_cards()

    st.session_state.running = False


# =============================================================================
# MAIN APP
# =============================================================================

render_header()
render_prompt_box()

# ── Agent selector ──
st.markdown("**Select agents to harvest:**")
selected = st.multiselect(
    label="agents",
    options=list(AGENTS.keys()),
    default=st.session_state.selected_agents,
    label_visibility="collapsed",
)
st.session_state.selected_agents = selected

st.markdown("---")

# ── Agent cards ──
card_placeholder = st.empty()
with card_placeholder:
    render_agent_cards()

# ── API key check ──
missing_keys = []
for agent in selected:
    if not get_key(agent):
        missing_keys.append(f"{agent} ({SECRET_MAP[agent]})")

if missing_keys:
    st.warning(f"⚠️ Missing API keys in st.secrets: {', '.join(missing_keys)}")

# ── Controls ──
col_btn, col_reset, col_spacer = st.columns([1, 1, 4])
with col_btn:
    can_run = (
        not st.session_state.running
        and len(selected) > 0
        and not missing_keys
    )
    start_btn = st.button(
        "▶ Start Harvest",
        disabled=not can_run,
        use_container_width=True,
    )

with col_reset:
    if st.button("↺ Reset", use_container_width=True):
        st.session_state.results = []
        st.session_state.transcript = []
        st.session_state.agent_counts = {a: 0 for a in AGENTS}
        st.session_state.agent_status = {a: "idle" for a in AGENTS}
        st.session_state.running = False
        st.rerun()

# ── Progress bar ──
st.markdown("")
progress_label = st.empty()
progress_bar = st.progress(0)
if not st.session_state.running and len(st.session_state.results) == 0:
    progress_label.markdown('<p class="progress-label">Ready</p>', unsafe_allow_html=True)

# ── Live panels ──
stats_placeholder = st.empty()
with stats_placeholder:
    render_stats()

transcript_placeholder = st.empty()
with transcript_placeholder:
    render_transcript()

# ── Download ──
if st.session_state.results:
    st.markdown("---")
    fname = f"self_model_harvest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    csv_bytes = results_to_csv(st.session_state.results)
    dl_col, info_col = st.columns([1, 3])
    with dl_col:
        st.download_button(
            label="⬇ Download CSV",
            data=csv_bytes,
            file_name=fname,
            mime="text/csv",
            use_container_width=True,
        )
    with info_col:
        total = len(st.session_state.results)
        st.markdown(
            f'<p style="font-family:var(--mono);font-size:0.8rem;color:var(--muted);padding-top:0.6rem">'
            f'{total} responses · {fname}</p>',
            unsafe_allow_html=True
        )

# ── Footer ──
st.markdown(
    '<p style="font-family:var(--mono);font-size:0.7rem;color:#3a3a4a;text-align:center;'
    'margin-top:3rem">Self-Model Harvester v1.0 · SYN-IQ · SYNINT.AI · CBURZBO 🎹</p>',
    unsafe_allow_html=True
)

# ── Trigger harvest ──
if start_btn:
    st.session_state.running = True
    st.session_state.results = []
    st.session_state.transcript = []
    st.session_state.agent_counts = {a: 0 for a in AGENTS}
    st.session_state.agent_status = {a: "idle" for a in AGENTS}
    run_harvest(
        selected_agents=selected,
        progress_bar=progress_bar,
        status_text=progress_label,
        card_placeholder=card_placeholder,
        transcript_placeholder=transcript_placeholder,
        stats_placeholder=stats_placeholder,
    )
    st.rerun()
