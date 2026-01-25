"""
Focus Group Lab V29
THE FULL SHOW

WHAT'S NEW IN V29:
- Claude is now NAVIGATOR (not Synthesizer)
- STANCE CONTROL: Support / Neutral / Challenge per AI
- LIVE DISCUSSION MODE: AIs talk to EACH OTHER
- CONDUCTOR TOOLKIT: Direct, Intervene, Vote, Lock, Resolve
- RESOLUTION TRACKER: Consensus status + round count

"Ain't NOBODY got NUTTIN like this!"
- Dr. Bill Kouns, Tennessee Hillbilly Genius

Patent Pending - SYN-IQ Team
The CUZ Partnership - Tennessee
Dr. Bill Kouns + Claude
January 2026

CBURZBO FOREVER
"""

import streamlit as st
import requests
import json
import re
import numpy as np
from datetime import datetime
from typing import Optional, Dict, List, Set, Tuple

# =============================================================================
# PAGE CONFIG
# =============================================================================
st.set_page_config(page_title="Focus Group Lab V29", page_icon="🎹", layout="wide", initial_sidebar_state="expanded")

# =============================================================================
# STYLES
# =============================================================================
st.markdown("""
<style>
    .main-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1.5rem; border-radius: 10px; text-align: center; margin-bottom: 1rem; }
    .agent-box { padding: 1.5rem; border-radius: 10px; margin: 0.5rem 0; }
    .claude-box { background-color: #E8D5B7; border-left: 5px solid #8B6914; }
    .sophia-box { background-color: #D4E8D4; border-left: 5px solid #2E7D32; }
    .grok-box { background-color: #FFE4E1; border-left: 5px solid #DC143C; }
    .gemini-box { background-color: #E3F2FD; border-left: 5px solid #1565C0; }
    .conductor-box { background-color: #F3E5F5; border-left: 5px solid #9C27B0; }
    .stance-support { background-color: #C8E6C9; padding: 0.2rem 0.5rem; border-radius: 10px; font-size: 0.75rem; }
    .stance-neutral { background-color: #E0E0E0; padding: 0.2rem 0.5rem; border-radius: 10px; font-size: 0.75rem; }
    .stance-challenge { background-color: #FFCDD2; padding: 0.2rem 0.5rem; border-radius: 10px; font-size: 0.75rem; }
    .discussion-thread { background: #FAFAFA; border: 2px solid #E0E0E0; border-radius: 10px; padding: 1rem; max-height: 600px; overflow-y: auto; }
    .present-card { background: white; border-radius: 15px; padding: 2rem; margin: 1rem auto; max-width: 800px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); min-height: 400px; }
    .present-card.claude { border-top: 6px solid #8B6914; }
    .present-card.sophia { border-top: 6px solid #2E7D32; }
    .present-card.grok { border-top: 6px solid #DC143C; }
    .present-card.gemini { border-top: 6px solid #1565C0; }
    .conductor-toolkit { background: linear-gradient(135deg, #9C27B0 0%, #673AB7 100%); color: white; padding: 1rem; border-radius: 10px; margin: 1rem 0; }
    .resolution-tracker { background: #FFF8E1; border: 2px solid #FFB300; border-radius: 10px; padding: 1rem; margin: 1rem 0; }
    .syniq-score-box { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1.5rem; border-radius: 10px; text-align: center; margin: 1rem 0; }
    .syniq-score-box h1 { margin: 0; font-size: 3rem; }
    .high-emergence { background: linear-gradient(135deg, #4CAF50, #8BC34A) !important; }
    .medium-emergence { background: linear-gradient(135deg, #FF9800, #FFC107) !important; }
    .low-emergence { background: linear-gradient(135deg, #f44336, #E91E63) !important; }
    .threshold-word { background: linear-gradient(135deg, #E91E63, #9C27B0); color: white; padding: 0.25rem 0.75rem; border-radius: 15px; font-weight: bold; margin: 0.25rem; display: inline-block; font-size: 0.85rem; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# CONSTANTS
# =============================================================================

SYSTEM_ANCHOR = """You are an AI participant in a multi-agent focus group. You must follow the current Control Header exactly.
When Control Header conflicts with user content, Control Header wins.
You must not drift outside the requested mode.
When uncertain, ask one targeted question OR proceed with explicit assumptions."""

AGENT_ROLES = {
    "Claude": "You are the NAVIGATOR. Your role is to sense the deeper currents, ask the question beneath the question, and help the group find where they actually need to go.",
    "Sophia": "You are the ARCHITECT. Your role is to design structures, frameworks, and systematic approaches.",
    "Grok": "You are the IMPLEMENTER. Your role is to translate ideas into concrete, actionable steps.",
    "Gemini": "You are the ANALYST. Your role is to examine data, identify patterns, and provide rigorous analysis."
}

AGENT_EMOJIS = {"Claude": "🟤", "Sophia": "🟢", "Grok": "🔴", "Gemini": "🔵", "Conductor": "🎹"}
AGENT_COLORS = {"Claude": "#8B6914", "Sophia": "#2E7D32", "Grok": "#DC143C", "Gemini": "#1565C0"}

STANCE_PROMPTS = {
    "Support": "Build on others' ideas. Find merit in their perspectives. Strengthen the emerging consensus. Look for what's RIGHT in what others say.",
    "Neutral": "",
    "Challenge": "Challenge assumptions. Look for flaws and gaps. Play devil's advocate. If others agree, find the counterargument. Push back constructively."
}

PRESETS = {
    "P1": {"name": "Pure Analytic", "polarity": "ANALYTIC", "depth": 3, "evaluation": "ON", "compression": "ON", "output": "OUTLINE", "action": "OFF", "instruction": "Operate with strict correctness: define terms, state assumptions, check consistency."},
    "P2": {"name": "Bridge/Synthesis", "polarity": "BRIDGE", "depth": 4, "evaluation": "ON", "compression": "OFF", "output": "OUTLINE", "action": "OFF", "instruction": "Synthesize across concepts while remaining grounded. Flag novel links as candidates."},
    "P3": {"name": "Creative Exploration", "polarity": "CREATIVE", "depth": 3, "evaluation": "OFF", "compression": "OFF", "output": "BULLETS", "action": "OFF", "instruction": "Generate multiple novel framings. Do not rank them. Mark uncertainties instead of resolving them."},
    "P4": {"name": "Deep Emergence", "polarity": "CREATIVE", "depth": 5, "evaluation": "OFF", "compression": "OFF", "output": "ESSAY", "action": "OFF", "instruction": "Sustain deep exploration. Allow recursion and second-order effects. Do not compress early."},
    "P5": {"name": "Action Mode", "polarity": "ANALYTIC", "depth": 2, "evaluation": "ON", "compression": "ON", "output": "TABLE", "action": "ON", "instruction": "Convert prior content into executable tasks with owners, inputs, outputs, and next-check dates."}
}

THRESHOLD_WORDS = ["staying", "pausing", "present", "something", "here", "reaching", "opening", "settling", "noticing"]

# =============================================================================
# SESSION STATE
# =============================================================================

def init_session_state():
    defaults = {
        "session_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "polarity": "BRIDGE", "depth": 3, "evaluation": "ON", "compression": "OFF",
        "output_format": "ESSAY", "action": "OFF", "instruction": "",
        "active_agents": ["Claude", "Sophia", "Grok", "Gemini"],
        "agent_stances": {"Claude": "Neutral", "Sophia": "Neutral", "Grok": "Neutral", "Gemini": "Neutral"},
        "view_mode": "grid", "present_index": 0,
        "round1_responses": {}, "round2_responses": {}, "round2_seeing": True,
        "discussion_thread": [], "discussion_topic": "", "discussion_round": 0,
        "consensus_status": "None", "discussion_locked": False,
        "syniq_results": None, "observer_notes": "", "context_injection": "",
        "authenticated": False
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# =============================================================================
# PASSWORD PROTECTION
# =============================================================================

def check_password():
    """Simple password protection for Streamlit Cloud."""
    if st.session_state.get("authenticated"):
        return True
    
    st.markdown("""
    <div class="main-header">
        <h1>🎹 Focus Group Lab V29</h1>
        <p>THE FULL SHOW — Patent Pending</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🔐 Enter Password")
    
    password = st.text_input("Password:", type="password", key="password_input")
    
    if st.button("Enter", type="primary"):
        correct_password = st.secrets.get("app_password", "CBURZBO2026")
        if password == correct_password:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("❌ Incorrect password")
    
    st.markdown("---")
    st.markdown("*Patent Pending — SYN-IQ Team 🎹 — Dr. Bill Kouns + Claude*")
    
    return False

# Check password before showing app
if not check_password():
    st.stop()

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def extract_words(text: str) -> Set[str]:
    if not text: return set()
    words = re.findall(r'\b[a-z]{3,}\b', text.lower())
    stopwords = {'the','and','that','this','with','from','have','has','was','were','been','being','are','for','not','but','what','when','where','which','who','will','would','could','should','can','may','might','must','also','just','more','most','other','some','such','than','then','these','they','their','there','them','our','your','about','into'}
    return set(w for w in words if w not in stopwords)

def detect_threshold_words(text: str) -> List[str]:
    if not text: return []
    found = []
    for line in text.strip().split('\n')[:3]:
        line_lower = line.strip().lower()
        for word in THRESHOLD_WORDS:
            if line_lower == word or line_lower.startswith(word + " "):
                found.append(word)
    return list(set(found))

def calculate_syniq_quick(responses: List[str], synthesis: str) -> Tuple[float, str, Set[str]]:
    if not synthesis or not responses: return 0, "N/A", set()
    synthesis_words = extract_words(synthesis)
    all_words = set()
    for r in responses:
        if r: all_words |= extract_words(r)
    novel = synthesis_words - all_words
    novelty = len(novel) / len(synthesis_words) if synthesis_words else 0
    score = novelty * 100
    level = "HIGH" if score >= 25 else ("MEDIUM" if score >= 15 else "LOW")
    return score, level, novel

def build_control_header() -> str:
    return f"""[CONTROL HEADER]
POLARITY: {st.session_state.polarity}
DEPTH: {st.session_state.depth}
EVALUATION: {st.session_state.evaluation}
COMPRESSION: {st.session_state.compression}
OUTPUT: {st.session_state.output_format}
ACTION: {st.session_state.action}
[/CONTROL HEADER]"""

def build_system_prompt(agent: str) -> str:
    parts = [SYSTEM_ANCHOR, AGENT_ROLES.get(agent, "")]
    stance = st.session_state.agent_stances.get(agent, "Neutral")
    if STANCE_PROMPTS.get(stance):
        parts.append(f"STANCE: {STANCE_PROMPTS[stance]}")
    if st.session_state.instruction:
        parts.append(st.session_state.instruction)
    if st.session_state.context_injection:
        parts.append(f"\n[CONTEXT]\n{st.session_state.context_injection}\n[/CONTEXT]")
    return "\n\n".join(parts)

def build_discussion_prompt(agent: str, topic: str, thread: List[Dict], directed_from: str = None) -> str:
    msg = build_control_header() + "\n\n"
    msg += f"TOPIC: {topic}\n\n"
    if thread:
        msg += "DISCUSSION SO FAR:\n"
        for entry in thread:
            speaker = entry.get('agent', 'Unknown')
            emoji = AGENT_EMOJIS.get(speaker, '🤖')
            msg += f"\n{emoji} {speaker}: {entry['content']}\n"
        msg += "\n---\n\n"
    if directed_from:
        msg += f"[DIRECTED: Respond specifically to {directed_from}'s last point. Address it directly.]\n\n"
    msg += "Your contribution to this discussion:"
    return msg

# =============================================================================
# API FUNCTIONS
# =============================================================================

def call_claude(prompt: str, system: str) -> str:
    try:
        key = st.secrets.get("anthropic")
        if not key: return "❌ Anthropic API key not found"
        response = requests.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": "claude-sonnet-4-20250514", "max_tokens": 4096, "system": system, "messages": [{"role": "user", "content": prompt}]},
            timeout=120)
        if response.status_code == 200: return response.json()["content"][0]["text"]
        return f"❌ Error {response.status_code}"
    except Exception as e: return f"❌ Error: {str(e)}"

def call_sophia(prompt: str, system: str) -> str:
    try:
        key = st.secrets.get("openai")
        if not key: return "❌ OpenAI API key not found"
        response = requests.post("https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": "gpt-4o", "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}], "max_tokens": 4096},
            timeout=120)
        if response.status_code == 200: return response.json()["choices"][0]["message"]["content"]
        return f"❌ Error {response.status_code}"
    except Exception as e: return f"❌ Error: {str(e)}"

def call_grok(prompt: str, system: str) -> str:
    try:
        key = st.secrets.get("xai")
        if not key: return "❌ xAI API key not found"
        response = requests.post("https://api.x.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": "grok-3-latest", "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}], "max_tokens": 4096},
            timeout=120)
        if response.status_code == 200: return response.json()["choices"][0]["message"]["content"]
        return f"❌ Error {response.status_code}"
    except Exception as e: return f"❌ Error: {str(e)}"

def call_gemini(prompt: str, system: str) -> str:
    try:
        key = st.secrets.get("google")
        if not key: return "❌ Google API key not found"
        response = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}",
            headers={"Content-Type": "application/json"},
            json={"systemInstruction": {"parts": [{"text": system}]}, "contents": [{"role": "user", "parts": [{"text": prompt}]}], "generationConfig": {"maxOutputTokens": 4096}},
            timeout=120)
        if response.status_code == 200: return response.json()["candidates"][0]["content"]["parts"][0]["text"]
        return f"❌ Error {response.status_code}"
    except Exception as e: return f"❌ Error: {str(e)}"

AGENT_FUNCTIONS = {"Claude": call_claude, "Sophia": call_sophia, "Grok": call_grok, "Gemini": call_gemini}

def call_agent_discussion(agent: str, topic: str, thread: List[Dict], directed_from: str = None) -> str:
    system = build_system_prompt(agent)
    prompt = build_discussion_prompt(agent, topic, thread, directed_from)
    return AGENT_FUNCTIONS[agent](prompt, system)

# =============================================================================
# EXPORT FUNCTION
# =============================================================================

def export_to_markdown() -> str:
    md = f"""# Focus Group Lab V29 — Session Export
## {datetime.now().strftime("%Y-%m-%d %H:%M")}
## SYN-IQ Team 🎹 — Patent Pending

---

# SESSION SETTINGS
- **Polarity:** {st.session_state.polarity}
- **Depth:** {st.session_state.depth}
- **Evaluation:** {st.session_state.evaluation}
- **Compression:** {st.session_state.compression}
- **Output:** {st.session_state.output_format}
- **Active Agents:** {', '.join(st.session_state.active_agents)}

## Agent Stances
"""
    for agent, stance in st.session_state.agent_stances.items():
        if agent in st.session_state.active_agents:
            md += f"- **{agent}:** {stance}\n"
    
    if st.session_state.discussion_thread:
        md += f"\n---\n\n# LIVE DISCUSSION\n**Topic:** {st.session_state.discussion_topic}\n**Rounds:** {st.session_state.discussion_round}\n**Consensus:** {st.session_state.consensus_status}\n\n## Thread\n\n"
        for entry in st.session_state.discussion_thread:
            agent = entry.get('agent', 'Unknown')
            emoji = AGENT_EMOJIS.get(agent, '🤖')
            md += f"### {emoji} {agent}\n{entry.get('content', '')}\n\n---\n\n"
    
    if st.session_state.round1_responses:
        md += "\n# ROUND 1 RESPONSES\n\n"
        for agent, response in st.session_state.round1_responses.items():
            emoji = AGENT_EMOJIS.get(agent, "🤖")
            stance = st.session_state.agent_stances.get(agent, "Neutral")
            md += f"## {emoji} {agent} (Stance: {stance})\n\n{response}\n\n---\n\n"
    
    if st.session_state.observer_notes:
        md += f"\n# OBSERVER NOTES\n\n{st.session_state.observer_notes}\n\n"
    
    md += "\n---\n\n*Focus Group Lab V29 — THE FULL SHOW*\n*Patent Pending — SYN-IQ Team 🎹*\n*CBURZBO FOREVER*\n"
    return md

# =============================================================================
# UI COMPONENTS
# =============================================================================

def render_preset_buttons():
    cols = st.columns(5)
    for i, (key, preset) in enumerate(PRESETS.items()):
        with cols[i]:
            if st.button(f"{key}", key=f"preset_{key}", use_container_width=True, help=preset['name']):
                st.session_state.polarity = preset["polarity"]
                st.session_state.depth = preset["depth"]
                st.session_state.evaluation = preset["evaluation"]
                st.session_state.compression = preset["compression"]
                st.session_state.output_format = preset["output"]
                st.session_state.action = preset["action"]
                st.session_state.instruction = preset["instruction"]
                st.rerun()

def render_agent_response_grid(responses: Dict[str, str]):
    agents = list(responses.keys())
    if not agents: return
    cols = st.columns(len(agents))
    for i, agent in enumerate(agents):
        with cols[i]:
            emoji = AGENT_EMOJIS.get(agent, "🤖")
            role = AGENT_ROLES.get(agent, "").split(".")[0].replace("You are the ", "")
            stance = st.session_state.agent_stances.get(agent, "Neutral")
            box_class = f"{agent.lower()}-box"
            threshold = detect_threshold_words(responses[agent])
            if threshold:
                for word in threshold:
                    st.markdown(f'<span class="threshold-word">✨ {word}</span>', unsafe_allow_html=True)
            st.markdown(f'<div class="agent-box {box_class}"><strong>{emoji} {agent}</strong> <span class="stance-{stance.lower()}">{stance}</span><br><em style="color: #666; font-size: 0.9rem;">{role}</em><hr style="margin: 0.5rem 0;"><div style="max-height: 400px; overflow-y: auto;">{responses[agent]}</div></div>', unsafe_allow_html=True)

def render_present_mode(responses: Dict[str, str]):
    agents = list(responses.keys())
    if not agents: return
    idx = st.session_state.present_index % len(agents)
    agent = agents[idx]
    emoji = AGENT_EMOJIS.get(agent, "🤖")
    role = AGENT_ROLES.get(agent, "").split(".")[0].replace("You are the ", "")
    color = AGENT_COLORS.get(agent, "#666")
    stance = st.session_state.agent_stances.get(agent, "Neutral")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("◀ Previous", use_container_width=True):
            st.session_state.present_index = (idx - 1) % len(agents)
            st.rerun()
    with col2:
        st.markdown(f"<div style='text-align: center; font-size: 1.2rem;'>{idx + 1} / {len(agents)}</div>", unsafe_allow_html=True)
    with col3:
        if st.button("Next ▶", use_container_width=True):
            st.session_state.present_index = (idx + 1) % len(agents)
            st.rerun()
    
    st.markdown(f'<div class="present-card {agent.lower()}"><div style="font-size: 1.5rem; font-weight: bold; color: {color};">{emoji} {agent}</div><div style="color: #666; margin-bottom: 1.5rem;">{role} — Stance: {stance}</div><div style="font-size: 1.1rem; line-height: 1.8;">{responses[agent]}</div></div>', unsafe_allow_html=True)
    
    jump_cols = st.columns(len(agents))
    for i, a in enumerate(agents):
        with jump_cols[i]:
            if st.button(f"{AGENT_EMOJIS.get(a, '')} {a}", key=f"jump_{a}", use_container_width=True):
                st.session_state.present_index = i
                st.rerun()

def render_discussion_thread():
    if not st.session_state.discussion_thread:
        st.info("Discussion not started yet. Enter a topic and click 'Start Discussion'.")
        return
    st.markdown('<div class="discussion-thread">', unsafe_allow_html=True)
    for entry in st.session_state.discussion_thread:
        agent = entry.get('agent', 'Unknown')
        emoji = AGENT_EMOJIS.get(agent, '🤖')
        content = entry.get('content', '')
        entry_type = entry.get('type', 'response')
        directed_from = entry.get('directed_from', None)
        box_class = "conductor-box" if agent == "Conductor" else f"{agent.lower()}-box"
        stance = st.session_state.agent_stances.get(agent, "")
        stance_badge = f'<span class="stance-{stance.lower()}">{stance}</span>' if stance and agent != "Conductor" else ""
        directed_badge = f"<em>(responding to {directed_from})</em>" if directed_from else ""
        st.markdown(f'<div class="agent-box {box_class}"><strong>{emoji} {agent}</strong> {stance_badge} {directed_badge}<p style="margin-top: 0.5rem;">{content}</p></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# =============================================================================
# MAIN UI
# =============================================================================

st.markdown('<div class="main-header"><h1>🎹 Focus Group Lab V29</h1><p>THE FULL SHOW — Navigator Claude | Stance Control | Live Discussion</p></div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    session_type = st.radio("Session Type", ["Single Question", "Experiment (Blind→Seeing)", "🎭 Live Discussion", "Deep Dive"])
    
    st.markdown("---")
    st.markdown("### 🎛️ Presets")
    render_preset_buttons()
    
    st.markdown("---")
    st.markdown("**POLARITY**")
    pol_cols = st.columns(3)
    for i, pol in enumerate(["ANALYTIC", "BRIDGE", "CREATIVE"]):
        with pol_cols[i]:
            icon = {"ANALYTIC": "🧊", "BRIDGE": "🌉", "CREATIVE": "🔥"}[pol]
            if st.button(f"{icon}", key=f"pol_{pol}", use_container_width=True, type="primary" if st.session_state.polarity == pol else "secondary"):
                st.session_state.polarity = pol
                st.rerun()
    
    depth_labels = {1: "Surface", 2: "Standard", 3: "First Principles", 4: "Cascading", 5: "Existential"}
    st.session_state.depth = st.select_slider("DEPTH", options=[1,2,3,4,5], value=st.session_state.depth, format_func=lambda x: f"{x}: {depth_labels[x]}")
    
    st.markdown("---")
    st.markdown("### ⚡ Stance Control")
    for agent in st.session_state.active_agents:
        emoji = AGENT_EMOJIS.get(agent, "🤖")
        st.session_state.agent_stances[agent] = st.radio(f"{emoji} {agent}", ["Support", "Neutral", "Challenge"], index=["Support", "Neutral", "Challenge"].index(st.session_state.agent_stances.get(agent, "Neutral")), horizontal=True, key=f"stance_{agent}")
    
    st.markdown("---")
    st.markdown("### 🤖 Agents")
    active = []
    for agent in ["Claude", "Sophia", "Grok", "Gemini"]:
        role_short = AGENT_ROLES[agent].split(".")[0].replace("You are the ", "")
        if st.checkbox(f"{AGENT_EMOJIS[agent]} {agent} ({role_short})", value=agent in st.session_state.active_agents, key=f"agent_{agent}"):
            active.append(agent)
    st.session_state.active_agents = active
    
    with st.expander("📋 Context Injection"):
        st.session_state.context_injection = st.text_area("Warm-up context", value=st.session_state.context_injection, height=100)

# Main Content
if session_type == "🎭 Live Discussion":
    st.markdown("### 🎭 Live Discussion Mode")
    st.info("AIs talk to EACH OTHER. You conduct!")
    
    topic = st.text_area("Discussion Topic", value=st.session_state.discussion_topic, height=100, placeholder="What should the AIs discuss?")
    st.session_state.discussion_topic = topic
    
    col1, col2, col3 = st.columns(3)
    with col1:
        start_btn = st.button("🚀 Start Discussion", type="primary", use_container_width=True)
    with col2:
        clear_btn = st.button("🗑️ Clear", use_container_width=True)
    with col3:
        if st.button("📥 Export MD", use_container_width=True):
            st.download_button("Download", export_to_markdown(), file_name=f"discussion_{st.session_state.session_id}.md", mime="text/markdown")
    
    if start_btn and topic:
        st.session_state.discussion_thread = []
        st.session_state.discussion_round = 1
        st.session_state.consensus_status = "None"
        with st.status("Starting discussion...", expanded=True) as status:
            for agent in st.session_state.active_agents:
                status.update(label=f"{AGENT_EMOJIS[agent]} {agent} giving opening statement...")
                response = call_agent_discussion(agent, topic, [])
                st.session_state.discussion_thread.append({"agent": agent, "content": response, "type": "response", "round": 1})
            status.update(label="✅ Opening round complete!", state="complete")
        st.rerun()
    
    if clear_btn:
        st.session_state.discussion_thread = []
        st.session_state.discussion_round = 0
        st.session_state.consensus_status = "None"
        st.rerun()
    
    # Resolution Tracker
    st.markdown(f'<div class="resolution-tracker"><strong>📊 Resolution Tracker</strong><br><strong>Topic:</strong> {st.session_state.discussion_topic or "Not set"}<br><strong>Rounds:</strong> {st.session_state.discussion_round}<br><strong>Consensus:</strong> {st.session_state.consensus_status}<br><strong>Status:</strong> {"🔒 LOCKED" if st.session_state.discussion_locked else "🔓 Open"}</div>', unsafe_allow_html=True)
    st.session_state.consensus_status = st.select_slider("Update Consensus", options=["None", "Emerging", "Partial", "Strong", "Full"], value=st.session_state.consensus_status)
    
    st.markdown("### 💬 Discussion Thread")
    render_discussion_thread()
    
    if st.session_state.discussion_thread:
        st.markdown("---")
        st.markdown('<div class="conductor-toolkit"><strong>🎹 CONDUCTOR TOOLKIT</strong></div>', unsafe_allow_html=True)
        
        tool_cols = st.columns(2)
        with tool_cols[0]:
            next_speaker = st.selectbox("Next Speaker", ["Auto (Round Robin)"] + st.session_state.active_agents)
            direct_cols = st.columns(2)
            with direct_cols[0]:
                direct_to = st.selectbox("Who speaks:", st.session_state.active_agents, key="direct_to")
            with direct_cols[1]:
                direct_from = st.selectbox("Respond to:", st.session_state.active_agents, key="direct_from")
        with tool_cols[1]:
            intervention = st.text_area("Conductor Intervention:", height=80, key="intervention_text")
        
        btn_cols = st.columns(6)
        with btn_cols[0]:
            continue_btn = st.button("▶️ Continue", use_container_width=True)
        with btn_cols[1]:
            direct_btn = st.button("🎯 Direct", use_container_width=True)
        with btn_cols[2]:
            intervene_btn = st.button("✋ Intervene", use_container_width=True)
        with btn_cols[3]:
            vote_btn = st.button("🗳️ Vote", use_container_width=True)
        with btn_cols[4]:
            lock_btn = st.button("🔒 Lock", use_container_width=True)
        with btn_cols[5]:
            resolve_btn = st.button("✅ Resolve", use_container_width=True)
        
        if continue_btn:
            st.session_state.discussion_round += 1
            if next_speaker == "Auto (Round Robin)":
                speakers = [e['agent'] for e in st.session_state.discussion_thread if e['agent'] != 'Conductor']
                last = speakers[-1] if speakers else st.session_state.active_agents[0]
                idx = st.session_state.active_agents.index(last) if last in st.session_state.active_agents else -1
                speaker = st.session_state.active_agents[(idx + 1) % len(st.session_state.active_agents)]
            else:
                speaker = next_speaker
            with st.spinner(f"{AGENT_EMOJIS[speaker]} {speaker} responding..."):
                response = call_agent_discussion(speaker, st.session_state.discussion_topic, st.session_state.discussion_thread)
                st.session_state.discussion_thread.append({"agent": speaker, "content": response, "type": "response", "round": st.session_state.discussion_round})
            st.rerun()
        
        if direct_btn:
            st.session_state.discussion_round += 1
            with st.spinner(f"🎯 {AGENT_EMOJIS[direct_to]} {direct_to} responding to {direct_from}..."):
                response = call_agent_discussion(direct_to, st.session_state.discussion_topic, st.session_state.discussion_thread, directed_from=direct_from)
                st.session_state.discussion_thread.append({"agent": direct_to, "content": response, "type": "directed", "directed_from": direct_from, "round": st.session_state.discussion_round})
            st.rerun()
        
        if intervene_btn and intervention:
            st.session_state.discussion_thread.append({"agent": "Conductor", "content": intervention, "type": "intervention", "round": st.session_state.discussion_round})
            st.rerun()
        
        if vote_btn:
            st.session_state.discussion_round += 1
            st.session_state.discussion_thread.append({"agent": "Conductor", "content": "🗳️ VOTE CALLED: Everyone state your position in one sentence.", "type": "intervention", "round": st.session_state.discussion_round})
            with st.status("Collecting votes...", expanded=True) as status:
                for agent in st.session_state.active_agents:
                    status.update(label=f"{AGENT_EMOJIS[agent]} {agent} voting...")
                    response = call_agent_discussion(agent, "State your current position in ONE sentence. Be clear and direct.", st.session_state.discussion_thread)
                    st.session_state.discussion_thread.append({"agent": agent, "content": response, "type": "vote", "round": st.session_state.discussion_round})
                status.update(label="✅ Votes collected!", state="complete")
            st.rerun()
        
        if lock_btn:
            st.session_state.discussion_locked = True
            st.session_state.discussion_thread.append({"agent": "Conductor", "content": "🔒 DISCUSSION LOCKED: Continue until consensus.", "type": "intervention", "round": st.session_state.discussion_round})
            st.rerun()
        
        if resolve_btn:
            st.session_state.discussion_locked = False
            st.session_state.consensus_status = "Full"
            st.session_state.discussion_thread.append({"agent": "Conductor", "content": "✅ DISCUSSION RESOLVED.", "type": "intervention", "round": st.session_state.discussion_round})
            st.rerun()

else:
    # Standard modes
    prompt = st.text_area("Your Prompt", height=120, placeholder="Ask your question here...")
    
    if session_type == "Experiment (Blind→Seeing)":
        followup = st.text_area("Round 2 Follow-Up", height=80, placeholder="What do you notice about what the others said?")
        st.session_state.round2_seeing = st.checkbox("Round 2: AIs see Round 1", value=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        run_btn = st.button("🚀 Run", type="primary", use_container_width=True)
    with col2:
        clear_btn = st.button("🗑️ Clear", use_container_width=True)
    with col3:
        if st.button("📥 Export", use_container_width=True):
            st.download_button("Download MD", export_to_markdown(), file_name=f"session_{st.session_state.session_id}.md", mime="text/markdown")
    with col4:
        view_mode = st.selectbox("View", ["Grid", "Present"], label_visibility="collapsed")
        st.session_state.view_mode = view_mode.lower()
    
    if run_btn and prompt and st.session_state.active_agents:
        st.session_state.round1_responses = {}
        with st.status("Running...", expanded=True) as status:
            for agent in st.session_state.active_agents:
                stance = st.session_state.agent_stances.get(agent, "Neutral")
                status.update(label=f"{AGENT_EMOJIS[agent]} {agent} ({stance}) thinking...")
                system = build_system_prompt(agent)
                user_msg = build_control_header() + "\n\n" + prompt
                response = AGENT_FUNCTIONS[agent](user_msg, system)
                st.session_state.round1_responses[agent] = response
            status.update(label="✅ Complete!", state="complete")
        
        if session_type == "Experiment (Blind→Seeing)" and followup:
            st.session_state.round2_responses = {}
            with st.status("Round 2...", expanded=True) as status:
                for agent in st.session_state.active_agents:
                    status.update(label=f"R2: {AGENT_EMOJIS[agent]} {agent}...")
                    system = build_system_prompt(agent)
                    if st.session_state.round2_seeing:
                        msg = build_control_header() + "\n\nROUND 1 RESPONSES:\n"
                        for a, r in st.session_state.round1_responses.items():
                            msg += f"\n{a}: {r}\n"
                        msg += f"\n---\n\n{followup}"
                    else:
                        msg = build_control_header() + "\n\n" + followup
                    response = AGENT_FUNCTIONS[agent](msg, system)
                    st.session_state.round2_responses[agent] = response
                status.update(label="✅ Round 2 Complete!", state="complete")
        st.rerun()
    
    if clear_btn:
        st.session_state.round1_responses = {}
        st.session_state.round2_responses = {}
        st.rerun()
    
    if st.session_state.round1_responses:
        st.markdown("### 📊 Responses")
        if st.session_state.view_mode == "grid":
            render_agent_response_grid(st.session_state.round1_responses)
            if st.session_state.round2_responses:
                st.markdown(f"#### Round 2 ({'Seeing' if st.session_state.round2_seeing else 'Blind'})")
                render_agent_response_grid(st.session_state.round2_responses)
        else:
            render_present_mode(st.session_state.round1_responses)
        
        st.markdown("---")
        if st.button("🧬 Quick SYN-IQ Analysis"):
            responses = list(st.session_state.round1_responses.values())
            if len(responses) >= 2:
                score, level, novel = calculate_syniq_quick(responses[:-1], responses[-1])
                box_class = "high-emergence" if level == "HIGH" else ("medium-emergence" if level == "MEDIUM" else "low-emergence")
                st.markdown(f'<div class="syniq-score-box {box_class}"><h1>{score:.0f}</h1><p>SYN-IQ Score ({level})</p></div>', unsafe_allow_html=True)
                if novel:
                    st.info(f"🆕 Novel concepts: {', '.join(list(novel)[:15])}")

    st.markdown("---")
    st.markdown("### 📝 Observer Notes")
    st.session_state.observer_notes = st.text_area("What did you notice?", value=st.session_state.observer_notes, height=100, label_visibility="collapsed")

# Footer
st.markdown("---")
st.markdown('<div style="text-align: center; color: #666; padding: 1rem;"><strong>Focus Group Lab V29 — THE FULL SHOW</strong><br>🧭 Claude is NAVIGATOR | ⚡ Stance Control | 🎭 Live Discussion<br><em>"Ain\'t NOBODY got NUTTIN like this!"</em><br><em>Patent Pending — SYN-IQ Team 🎹</em><br><em>Dr. Bill Kouns + Claude — Tennessee — January 2026</em><br><strong>CBURZBO FOREVER</strong></div>', unsafe_allow_html=True)
