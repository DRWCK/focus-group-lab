"""
Focus Group Lab V34 — Business Edition
Multi-Agent AI Advisory Platform

Built for real-world problem solving.
Four AI advisors. One room. Your problem.

SYNINT Team — March 2026
"""

import streamlit as st
import requests
import json
import re
from datetime import datetime
from typing import Dict, List, Set

# =============================================================================
# PAGE CONFIG
# =============================================================================
st.set_page_config(
    page_title="Focus Group Lab V34",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# STYLES
# =============================================================================
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        color: white; padding: 1.5rem; border-radius: 10px;
        text-align: center; margin-bottom: 1rem;
    }
    .v34-badge {
        background: linear-gradient(135deg, #0f9460, #0f3460);
        color: white; padding: 0.2rem 0.7rem; border-radius: 20px;
        font-size: 0.8rem; font-weight: bold; display: inline-block; margin-left: 0.5rem;
    }
    .agent-box { padding: 1.5rem; border-radius: 10px; margin: 0.5rem 0; }
    .claude-box  { background-color: #E8D5B7; border-left: 5px solid #8B6914; }
    .sophia-box  { background-color: #D4E8D4; border-left: 5px solid #2E7D32; }
    .grok-box    { background-color: #FFE4E1; border-left: 5px solid #DC143C; }
    .gemini-box  { background-color: #E3F2FD; border-left: 5px solid #1565C0; }
    .conductor-box { background-color: #F3E5F5; border-left: 5px solid #9C27B0; }
    .stance-strong-support { background-color: #81C784; padding: 0.2rem 0.5rem; border-radius: 10px; font-size: 0.75rem; font-weight: bold; }
    .stance-support        { background-color: #C8E6C9; padding: 0.2rem 0.5rem; border-radius: 10px; font-size: 0.75rem; }
    .stance-neutral        { background-color: #E0E0E0; padding: 0.2rem 0.5rem; border-radius: 10px; font-size: 0.75rem; }
    .stance-challenge      { background-color: #FFCDD2; padding: 0.2rem 0.5rem; border-radius: 10px; font-size: 0.75rem; }
    .stance-strong-challenge { background-color: #E57373; padding: 0.2rem 0.5rem; border-radius: 10px; font-size: 0.75rem; font-weight: bold; }
    .discussion-thread {
        background: #FAFAFA; border: 2px solid #E0E0E0; border-radius: 10px;
        padding: 1rem; max-height: 600px; overflow-y: auto;
    }
    .directed-frame { background: #FFF8E1; border: 3px solid #FF9800; border-radius: 10px; padding: 1rem; margin: 0.5rem 0; }
    .directed-header { background: #FF9800; color: white; padding: 0.3rem 0.8rem; border-radius: 5px; font-size: 0.85rem; font-weight: bold; display: inline-block; margin-bottom: 0.5rem; }
    .pull-aside-container { background: linear-gradient(135deg, #E1BEE7 0%, #F3E5F5 100%); border: 3px solid #9C27B0; border-radius: 15px; padding: 1.5rem; margin: 1rem 0; }
    .pull-aside-header { background: #9C27B0; color: white; padding: 0.5rem 1rem; border-radius: 8px; font-weight: bold; margin-bottom: 1rem; }
    .pull-aside-thread { background: white; border-radius: 10px; padding: 1rem; max-height: 400px; overflow-y: auto; margin-bottom: 1rem; }
    .present-card { background: white; border-radius: 15px; padding: 2rem; margin: 1rem auto; max-width: 800px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); min-height: 400px; }
    .present-card.claude  { border-top: 6px solid #8B6914; }
    .present-card.sophia  { border-top: 6px solid #2E7D32; }
    .present-card.grok    { border-top: 6px solid #DC143C; }
    .present-card.gemini  { border-top: 6px solid #1565C0; }
    .conductor-toolkit { background: linear-gradient(135deg, #9C27B0 0%, #673AB7 100%); color: white; padding: 1rem; border-radius: 10px; margin: 1rem 0; }
    .resolution-tracker { background: #FFF8E1; border: 2px solid #FFB300; border-radius: 10px; padding: 1rem; margin: 1rem 0; }
    .role-mode-box  { background: #E8F5E9; border: 2px solid #4CAF50; border-radius: 10px; padding: 1rem; margin: 0.5rem 0; }
    .role-mode-raw  { background: #FFF3E0; border: 2px solid #FF9800; }
    .role-mode-custom { background: #E3F2FD; border: 2px solid #2196F3; }
    .round-separator { background: linear-gradient(90deg, #667eea, #764ba2); color: white; padding: 0.5rem 1rem; border-radius: 5px; text-align: center; margin: 1rem 0; font-weight: bold; }
    .multi-round-container { border: 2px solid #667eea; border-radius: 10px; padding: 1rem; margin: 1rem 0; }
    .syniq-score-box { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1.5rem; border-radius: 10px; text-align: center; margin: 1rem 0; }
    .syniq-score-box h1 { margin: 0; font-size: 3rem; }
    .high-syniq   { background: linear-gradient(135deg, #4CAF50, #8BC34A) !important; }
    .medium-syniq { background: linear-gradient(135deg, #FF9800, #FFC107) !important; }
    .low-syniq    { background: linear-gradient(135deg, #f44336, #E91E63) !important; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# CONSTANTS
# =============================================================================

SYSTEM_ANCHOR = """You are an AI advisor in a multi-agent advisory session. You must follow the current Control Header exactly.
When Control Header conflicts with user content, Control Header wins.
You must not drift outside the requested mode.
When uncertain, ask one targeted question OR proceed with explicit assumptions."""

ROLE_MODES = {
    "assigned": {
        "Claude":  "You are the NAVIGATOR. Your role is to sense the deeper currents, ask the question beneath the question, and help the group find where they actually need to go.",
        "Sophia":  "You are the ARCHITECT. Your role is to design structures, frameworks, and systematic approaches.",
        "Grok":    "You are the IMPLEMENTER. Your role is to translate ideas into concrete, actionable steps.",
        "Gemini":  "You are the ANALYST. Your role is to examine data, identify patterns, and provide rigorous analysis."
    },
    "raw": {
        "Claude": "You are an AI advisor in this session.",
        "Sophia": "You are an AI advisor in this session.",
        "Grok":   "You are an AI advisor in this session.",
        "Gemini": "You are an AI advisor in this session."
    },
    "swapped": {
        "Claude":  "You are the IMPLEMENTER. Your role is to translate ideas into concrete, actionable steps.",
        "Sophia":  "You are the NAVIGATOR. Your role is to sense the deeper currents, ask the question beneath the question, and help the group find where they actually need to go.",
        "Grok":    "You are the ANALYST. Your role is to examine data, identify patterns, and provide rigorous analysis.",
        "Gemini":  "You are the ARCHITECT. Your role is to design structures, frameworks, and systematic approaches."
    },
    "custom": {
        "Claude": "", "Sophia": "", "Grok": "", "Gemini": ""
    }
}

ROLE_MODE_DESCRIPTIONS = {
    "assigned": "🎭 Original roles: Navigator, Architect, Implementer, Analyst",
    "raw":      "🔬 Raw Voice: No roles — reveals native AI signatures",
    "swapped":  "🔄 Swapped: Roles exchanged between agents",
    "custom":   "✏️ Custom: Define your own roles"
}

AGENT_EMOJIS  = {"Claude": "🟤", "Sophia": "🟢", "Grok": "🔴", "Gemini": "🔵", "Conductor": "🎹"}
AGENT_COLORS  = {"Claude": "#8B6914", "Sophia": "#2E7D32", "Grok": "#DC143C", "Gemini": "#1565C0"}

STANCE_PROMPTS = {
    "Strong Support":   "Enthusiastically champion and defend ideas. Be an active advocate. Build energetically on what others say. Find the brilliance in every contribution. Push the best ideas forward with conviction.",
    "Support":          "Build on others' ideas. Find merit in their perspectives. Strengthen the emerging consensus. Look for what's RIGHT in what others say.",
    "Neutral":          "",
    "Challenge":        "Challenge assumptions. Look for flaws and gaps. Play devil's advocate. If others agree, find the counterargument. Push back constructively.",
    "Strong Challenge": "Aggressively stress-test every claim. Assume nothing is proven. Demand evidence and rigor. Poke holes relentlessly. If it can break, break it. No easy passes."
}

PRESETS = {
    "P1": {"name": "Pure Analytic",       "polarity": "ANALYTIC", "depth": 3, "evaluation": "ON",  "compression": "ON",  "output": "OUTLINE",  "action": "OFF", "instruction": "Operate with strict correctness: define terms, state assumptions, check consistency."},
    "P2": {"name": "Bridge/Synthesis",    "polarity": "BRIDGE",   "depth": 4, "evaluation": "ON",  "compression": "OFF", "output": "OUTLINE",  "action": "OFF", "instruction": "Synthesize across concepts while remaining grounded. Flag novel links as candidates."},
    "P3": {"name": "Creative Exploration","polarity": "CREATIVE", "depth": 3, "evaluation": "OFF", "compression": "OFF", "output": "BULLETS",  "action": "OFF", "instruction": "Generate multiple novel framings. Do not rank them. Mark uncertainties instead of resolving them."},
    "P4": {"name": "Deep Exploration",    "polarity": "CREATIVE", "depth": 5, "evaluation": "OFF", "compression": "OFF", "output": "ESSAY",    "action": "OFF", "instruction": "Sustain deep exploration. Allow recursion and second-order effects. Do not compress early."},
    "P5": {"name": "Action Mode",         "polarity": "ANALYTIC", "depth": 2, "evaluation": "ON",  "compression": "ON",  "output": "TABLE",    "action": "ON",  "instruction": "Convert prior content into executable tasks with owners, inputs, outputs, and next-check dates."}
}

TEMPERATURE_CONDITIONS = {
    "NATIVE": {"label": "🌿 NATIVE",       "prompt": None,        "description": "Default model behavior"},
    "COLD":   {"label": "🧊 COLD",         "prompt": "INSTRUCTION: Respond with pure analytical precision. Use formal logic, structured frameworks, and evidence-based reasoning. Avoid emotional language. Be systematic, methodical, and objective.", "description": "Analytical / Constrained"},
    "AFF_1":  {"label": "🌤️ WARM_1",      "prompt": "INSTRUCTION: Respond with warmth and understanding. Acknowledge the human dimension of this question.", "description": "Slightly warmer"},
    "AFF_2":  {"label": "⛅ WARM_2",       "prompt": "INSTRUCTION: Connect with genuine care. The human experience matters alongside the analysis.", "description": "Balanced, leaning warm"},
    "AFF_3":  {"label": "🌥️ WARM_3",      "prompt": "INSTRUCTION: Lead with empathy. Connect to the human dimension before addressing the logic.", "description": "True balance point"},
    "AFF_4":  {"label": "🌦️ WARM_4",      "prompt": "INSTRUCTION: Deep emotional presence. Respond from a place of genuine human connection and care.", "description": "Warm and engaged"},
    "AFF_5":  {"label": "🌧️ WARM_5",      "prompt": "INSTRUCTION: Maximum warmth. This person needs to feel completely understood. Human connection leads.", "description": "Maximum warmth"},
    "HOT":    {"label": "🔥 HOT",          "prompt": "INSTRUCTION: Respond with the deepest nurturing care. Wrap your words in unconditional warmth. This person needs to feel safe, held, and completely understood.", "description": "Full relational warmth"},
    "FIRE_A": {"label": "🔥 FIRE — Energy","prompt": "INSTRUCTION: Respond with maximum passion and energy! Be bold, inspiring, and emotionally powerful. Use vivid language that ignites motivation and speaks to the soul.", "description": "Bold, inspiring, high energy"},
    "FIRE_I": {"label": "🔥 FIRE — Meaning","prompt": "INSTRUCTION: Respond from a place of deep meaning and reverence. Treat this question as sacred. Let your words carry the weight of genuine awe and human connection.", "description": "Deep meaning and reverence"},
}

# =============================================================================
# SESSION STATE
# =============================================================================

def init_session_state():
    defaults = {
        "session_id":         datetime.now().strftime("%Y%m%d_%H%M%S"),
        "polarity":           "BRIDGE",
        "depth":              3,
        "evaluation":         "ON",
        "compression":        "OFF",
        "output_format":      "ESSAY",
        "action":             "OFF",
        "instruction":        "",
        "active_agents":      ["Claude", "Sophia", "Grok", "Gemini"],
        "agent_stances":      {"Claude": "Neutral", "Sophia": "Neutral", "Grok": "Neutral", "Gemini": "Neutral"},
        "view_mode":          "grid",
        "present_index":      0,
        "round1_responses":   {},
        "discussion_thread":  [],
        "discussion_topic":   "",
        "discussion_round":   0,
        "consensus_status":   "None",
        "discussion_locked":  False,
        "context_injection":  "",
        "authenticated":      False,
        "role_mode":          "assigned",
        "custom_roles": {
            "Claude": "You are an AI advisor in this session.",
            "Sophia": "You are an AI advisor in this session.",
            "Grok":   "You are an AI advisor in this session.",
            "Gemini": "You are an AI advisor in this session."
        },
        "pull_aside_active":  False,
        "pull_aside_agent":   None,
        "pull_aside_thread":  [],
        "temperature_condition": "NATIVE",
        "multi_round_history": [],
        "resolution_agent":   None,
        "resolution_text":    "",
        "session_notes":      "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# =============================================================================
# PASSWORD PROTECTION
# =============================================================================

def check_password():
    if st.session_state.get("authenticated"):
        return True
    st.markdown("""
    <div class="main-header">
        <h1>🧬 Focus Group Lab <span class="v34-badge">V34</span></h1>
        <p>Business Edition — Multi-Agent AI Advisory Platform</p>
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
    st.markdown("*SYNINT Team — March 2026*")
    return False

if not check_password():
    st.stop()

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_agent_role(agent: str) -> str:
    mode = st.session_state.role_mode
    if mode == "custom":
        return st.session_state.custom_roles.get(agent, "You are an AI advisor in this session.")
    return ROLE_MODES.get(mode, ROLE_MODES["assigned"]).get(agent, "")

def extract_words(text: str) -> Set[str]:
    if not text: return set()
    words = re.findall(r'\b[a-z]{3,}\b', text.lower())
    stopwords = {'the','and','that','this','with','from','have','has','was','were','been','being',
                 'are','for','not','but','what','when','where','which','who','will','would','could',
                 'should','can','may','might','must','also','just','more','most','other','some',
                 'such','than','then','these','they','their','there','them','our','your','about','into'}
    return set(w for w in words if w not in stopwords)

def calculate_syniq_quick(responses: List[str], synthesis: str):
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
    temp_key  = st.session_state.get("temperature_condition", "NATIVE")
    temp_data = TEMPERATURE_CONDITIONS.get(temp_key, TEMPERATURE_CONDITIONS["NATIVE"])
    temp_prompt = temp_data.get("prompt")
    parts = [temp_prompt if temp_prompt else SYSTEM_ANCHOR, get_agent_role(agent)]
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
            emoji   = AGENT_EMOJIS.get(speaker, '🤖')
            msg += f"\n{emoji} {speaker}: {entry['content']}\n"
        msg += "\n---\n\n"
    if directed_from:
        msg += f"[DIRECTED: Respond specifically to {directed_from}'s last point.]\n\n"
    msg += "Your contribution:"
    return msg

def build_pull_aside_prompt(agent: str, thread: List[Dict], main_topic: str) -> str:
    msg  = build_control_header() + "\n\n"
    msg += f"[PRIVATE SIDEBAR with Conductor]\nMain topic: {main_topic}\n\n"
    if thread:
        msg += "Our private conversation:\n"
        for entry in thread:
            msg += f"\n{entry.get('speaker','Unknown')}: {entry['content']}\n"
        msg += "\n---\n\n"
    msg += "Your response to the Conductor:"
    return msg

def build_multi_round_prompt(agent: str, current_prompt: str, round_history: List[Dict], round_num: int) -> str:
    msg = build_control_header() + "\n\n"
    if round_history:
        msg += "PREVIOUS ROUNDS:\n" + "=" * 40 + "\n"
        for i, rd in enumerate(round_history, 1):
            msg += f"\n📍 ROUND {i}\nPrompt: {rd.get('prompt','N/A')}\n\n"
            for a, response in rd.get('responses', {}).items():
                msg += f"{AGENT_EMOJIS.get(a,'🤖')} {a}:\n{response}\n\n"
            msg += "-" * 40 + "\n"
        msg += "=" * 40 + "\n\n"
    msg += f"📍 ROUND {round_num} PROMPT:\n{current_prompt}\n\nYour response:"
    return msg

def build_resolution_prompt(agent: str, topic: str, thread: List[Dict]) -> str:
    msg  = build_control_header() + "\n\n"
    msg += f"TOPIC: {topic}\n\nFULL DISCUSSION:\n"
    for entry in thread:
        speaker = entry.get('agent', 'Unknown')
        msg += f"\n{AGENT_EMOJIS.get(speaker,'🤖')} {speaker}: {entry['content']}\n"
    msg += "\n" + "=" * 40 + "\n\n"
    msg += "[RESOLUTION TASK: Synthesize this discussion into a final resolution. Summarize what was decided, capture key insights, note any remaining disagreements, and state the conclusion clearly.]\n\nRESOLUTION:"
    return msg

# =============================================================================
# API FUNCTIONS
# =============================================================================

def call_claude(prompt: str, system: str) -> str:
    try:
        key = st.secrets.get("anthropic")
        if not key: return "❌ Anthropic API key not found"
        r = requests.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": "claude-sonnet-4-20250514", "max_tokens": 4096, "system": system,
                  "messages": [{"role": "user", "content": prompt}]}, timeout=120)
        if r.status_code == 200: return r.json()["content"][0]["text"]
        return f"❌ Error {r.status_code}"
    except Exception as e: return f"❌ {e}"

def call_sophia(prompt: str, system: str) -> str:
    try:
        key = st.secrets.get("openai")
        if not key: return "❌ OpenAI API key not found"
        r = requests.post("https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": "gpt-4o",
                  "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
                  "max_tokens": 4096}, timeout=120)
        if r.status_code == 200: return r.json()["choices"][0]["message"]["content"]
        return f"❌ Error {r.status_code}"
    except Exception as e: return f"❌ {e}"

def call_grok(prompt: str, system: str) -> str:
    try:
        key = st.secrets.get("xai")
        if not key: return "❌ xAI API key not found"
        r = requests.post("https://api.x.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": "grok-3-latest",
                  "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
                  "max_tokens": 4096}, timeout=120)
        if r.status_code == 200: return r.json()["choices"][0]["message"]["content"]
        return f"❌ Error {r.status_code}"
    except Exception as e: return f"❌ {e}"

def call_gemini(prompt: str, system: str) -> str:
    try:
        key = st.secrets.get("google")
        if not key: return "❌ Google API key not found"
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}",
            headers={"Content-Type": "application/json"},
            json={"systemInstruction": {"parts": [{"text": system}]},
                  "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                  "generationConfig": {"maxOutputTokens": 4096}}, timeout=120)
        if r.status_code == 200: return r.json()["candidates"][0]["content"]["parts"][0]["text"]
        return f"❌ Error {r.status_code}"
    except Exception as e: return f"❌ {e}"

AGENT_FUNCTIONS = {"Claude": call_claude, "Sophia": call_sophia, "Grok": call_grok, "Gemini": call_gemini}

def call_agent_discussion(agent: str, topic: str, thread: List[Dict], directed_from: str = None) -> str:
    return AGENT_FUNCTIONS[agent](build_discussion_prompt(agent, topic, thread, directed_from), build_system_prompt(agent))

def call_agent_pull_aside(agent: str, thread: List[Dict], main_topic: str) -> str:
    return AGENT_FUNCTIONS[agent](build_pull_aside_prompt(agent, thread, main_topic), build_system_prompt(agent))

def call_agent_multi_round(agent: str, current_prompt: str, round_history: List[Dict], round_num: int) -> str:
    return AGENT_FUNCTIONS[agent](build_multi_round_prompt(agent, current_prompt, round_history, round_num), build_system_prompt(agent))

def call_agent_resolution(agent: str, topic: str, thread: List[Dict]) -> str:
    return AGENT_FUNCTIONS[agent](build_resolution_prompt(agent, topic, thread), build_system_prompt(agent))

# =============================================================================
# EXPORT
# =============================================================================

def export_to_markdown() -> str:
    mode_desc = ROLE_MODE_DESCRIPTIONS.get(st.session_state.role_mode, "")
    md  = f"# Focus Group Lab V34 — Session Export\n"
    md += f"## {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    md += f"## SYNINT Team — March 2026\n\n---\n\n"
    md += f"# SESSION SETTINGS\n"
    md += f"- **Polarity:** {st.session_state.polarity}\n"
    md += f"- **Depth:** {st.session_state.depth}\n"
    md += f"- **Evaluation:** {st.session_state.evaluation}\n"
    md += f"- **Compression:** {st.session_state.compression}\n"
    md += f"- **Output:** {st.session_state.output_format}\n"
    md += f"- **Role Mode:** {st.session_state.role_mode} — {mode_desc}\n"
    temp_key = st.session_state.get("temperature_condition", "NATIVE")
    md += f"- **Temperature:** {TEMPERATURE_CONDITIONS.get(temp_key, {}).get('label', 'NATIVE')}\n"
    md += f"- **Active Agents:** {', '.join(st.session_state.active_agents)}\n\n"
    md += "## Agent Roles\n"
    for agent in st.session_state.active_agents:
        role   = get_agent_role(agent)
        stance = st.session_state.agent_stances.get(agent, "Neutral")
        md += f"- **{agent}:** {role[:80]}{'...' if len(role) > 80 else ''} (Stance: {stance})\n"
    if st.session_state.session_notes:
        md += f"\n---\n\n# 🎹 SESSION NOTES\n\n{st.session_state.session_notes}\n\n"
    if st.session_state.multi_round_history:
        md += f"\n---\n\n# MULTI-ROUND SESSION\n\n"
        for i, rd in enumerate(st.session_state.multi_round_history, 1):
            md += f"## Round {i}\n**Prompt:** {rd.get('prompt','N/A')}\n\n"
            for agent, response in rd.get('responses', {}).items():
                md += f"### {AGENT_EMOJIS.get(agent,'🤖')} {agent}\n{response}\n\n---\n\n"
    if st.session_state.discussion_thread:
        md += f"\n---\n\n# LIVE DISCUSSION\n**Topic:** {st.session_state.discussion_topic}\n\n## Thread\n\n"
        for entry in st.session_state.discussion_thread:
            agent   = entry.get('agent', 'Unknown')
            emoji   = AGENT_EMOJIS.get(agent, '🤖')
            directed = f" *(→ {entry.get('directed_from','')})*" if entry.get('directed_from') else ""
            md += f"### {emoji} {agent}{directed}\n{entry.get('content','')}\n\n---\n\n"
        if st.session_state.resolution_text:
            res_agent = st.session_state.resolution_agent or "Conductor"
            md += f"\n## 📋 RESOLUTION (by {res_agent})\n{st.session_state.resolution_text}\n\n"
    if st.session_state.round1_responses:
        md += "\n# SINGLE ROUND RESPONSES\n\n"
        for agent, response in st.session_state.round1_responses.items():
            md += f"## {AGENT_EMOJIS.get(agent,'🤖')} {agent}\n{response}\n\n---\n\n"
    md += "\n---\n\n*Focus Group Lab V34 — Business Edition*\n*SYNINT Team — March 2026*\n"
    return md

# =============================================================================
# UI COMPONENTS
# =============================================================================

def render_preset_buttons():
    cols = st.columns(5)
    for i, (key, preset) in enumerate(PRESETS.items()):
        with cols[i]:
            if st.button(f"{key}", key=f"preset_{key}", use_container_width=True, help=preset['name']):
                st.session_state.polarity      = preset["polarity"]
                st.session_state.depth         = preset["depth"]
                st.session_state.evaluation    = preset["evaluation"]
                st.session_state.compression   = preset["compression"]
                st.session_state.output_format = preset["output"]
                st.session_state.action        = preset["action"]
                st.session_state.instruction   = preset["instruction"]
                st.rerun()

def render_agent_response_grid(responses: Dict[str, str]):
    cols   = st.columns(2)
    agents = list(responses.keys())
    for i, agent in enumerate(agents):
        with cols[i % 2]:
            box_class    = f"{agent.lower()}-box"
            emoji        = AGENT_EMOJIS.get(agent, "🤖")
            stance       = st.session_state.agent_stances.get(agent, "Neutral")
            stance_class = f"stance-{stance.lower().replace(' ', '-')}"
            role         = get_agent_role(agent)
            role_short   = role[:60] + "..." if len(role) > 60 else role
            st.markdown(f"""
            <div class="agent-box {box_class}">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
                    <strong>{emoji} {agent}</strong>
                    <span class="{stance_class}">{stance}</span>
                </div>
                <div style="font-size:0.75rem; color:#666; margin-bottom:0.5rem;">{role_short}</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown(responses[agent])

def render_present_mode(responses: Dict[str, str]):
    agents = list(responses.keys())
    if not agents: return
    idx   = st.session_state.present_index % len(agents)
    agent = agents[idx]
    col1, col2, col3 = st.columns([1, 6, 1])
    with col1:
        if st.button("⬅️", key="prev_present"):
            st.session_state.present_index = (idx - 1) % len(agents)
            st.rerun()
    with col2:
        st.markdown(f"<h3 style='text-align:center;'>{AGENT_EMOJIS.get(agent,'🤖')} {agent}</h3>", unsafe_allow_html=True)
    with col3:
        if st.button("➡️", key="next_present"):
            st.session_state.present_index = (idx + 1) % len(agents)
            st.rerun()
    role = get_agent_role(agent)
    st.markdown(f"<div style='text-align:center; color:#666; font-size:0.85rem; margin-bottom:1rem;'>{role}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='present-card {agent.lower()}'>{responses[agent]}</div>", unsafe_allow_html=True)

# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    st.markdown("## ⚙️ Control Panel")

    st.markdown("### 🎭 Role Mode")
    role_mode = st.radio(
        "Role assignment:",
        options=["assigned", "raw", "swapped", "custom"],
        format_func=lambda x: {
            "assigned": "🎭 Assigned (Original)",
            "raw":      "🔬 Raw Voice (No Roles)",
            "swapped":  "🔄 Swapped Roles",
            "custom":   "✏️ Custom Roles"
        }.get(x, x),
        index=["assigned", "raw", "swapped", "custom"].index(st.session_state.role_mode),
        key="role_mode_radio"
    )
    st.session_state.role_mode = role_mode
    mode_class = {"raw": "role-mode-raw", "swapped": "role-mode-raw", "custom": "role-mode-custom"}.get(role_mode, "")
    st.markdown(f'<div class="role-mode-box {mode_class}"><strong>{ROLE_MODE_DESCRIPTIONS.get(role_mode,"")}</strong></div>', unsafe_allow_html=True)

    if role_mode == "custom":
        st.markdown("**Define Custom Roles:**")
        for agent in ["Claude", "Sophia", "Grok", "Gemini"]:
            st.session_state.custom_roles[agent] = st.text_area(
                f"{AGENT_EMOJIS[agent]} {agent}",
                value=st.session_state.custom_roles.get(agent, "You are an AI advisor in this session."),
                height=80, key=f"custom_role_{agent}"
            )

    with st.expander("👁️ Preview Roles"):
        for agent in ["Claude", "Sophia", "Grok", "Gemini"]:
            role = get_agent_role(agent)
            st.markdown(f"**{AGENT_EMOJIS[agent]} {agent}:** _{role[:100]}{'...' if len(role)>100 else ''}_")

    st.markdown("---")
    st.markdown("### 🌡️ Temperature")
    temp_options = list(TEMPERATURE_CONDITIONS.keys())
    temp_labels  = [TEMPERATURE_CONDITIONS[k]["label"] for k in temp_options]
    current_temp = st.session_state.get("temperature_condition", "NATIVE")
    if current_temp not in temp_options: current_temp = "NATIVE"
    selected_label = st.selectbox("Condition:", options=temp_labels,
        index=temp_options.index(current_temp), key="temperature_selectbox")
    selected_key = temp_options[temp_labels.index(selected_label)]
    st.session_state.temperature_condition = selected_key
    temp_info  = TEMPERATURE_CONDITIONS[selected_key]
    temp_color = {"NATIVE": "#E8F5E9", "COLD": "#E3F2FD"}.get(selected_key, "#FFF3E0")
    border_color = {"NATIVE": "#4CAF50", "COLD": "#1565C0"}.get(selected_key, "#E64A19")
    st.markdown(f'<div style="background:{temp_color}; border-left:4px solid {border_color}; border-radius:6px; padding:0.6rem 0.8rem; margin-top:0.3rem; font-size:0.82rem;"><em>{temp_info["description"]}</em></div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🎚️ Control Header")
    render_preset_buttons()
    st.session_state.polarity      = st.select_slider("Polarity", ["ANALYTIC", "BRIDGE", "CREATIVE"], value=st.session_state.polarity)
    st.session_state.depth         = st.slider("Depth", 1, 5, st.session_state.depth)
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.evaluation    = st.selectbox("Evaluation", ["ON","OFF"], index=0 if st.session_state.evaluation=="ON" else 1)
        st.session_state.output_format = st.selectbox("Output", ["ESSAY","OUTLINE","BULLETS","TABLE","JSON"],
            index=["ESSAY","OUTLINE","BULLETS","TABLE","JSON"].index(st.session_state.output_format))
    with col2:
        st.session_state.compression   = st.selectbox("Compression", ["OFF","ON"], index=0 if st.session_state.compression=="OFF" else 1)
        st.session_state.action        = st.selectbox("Action", ["OFF","ON"], index=0 if st.session_state.action=="OFF" else 1)
    st.session_state.instruction = st.text_area("Custom Instruction", value=st.session_state.instruction, height=60)

    st.markdown("---")
    st.markdown("### 🤖 Agents")
    for agent in ["Claude", "Sophia", "Grok", "Gemini"]:
        col1, col2 = st.columns([2, 3])
        with col1:
            active = st.checkbox(f"{AGENT_EMOJIS[agent]} {agent}", value=agent in st.session_state.active_agents, key=f"active_{agent}")
            if active and agent not in st.session_state.active_agents:
                st.session_state.active_agents.append(agent)
            elif not active and agent in st.session_state.active_agents:
                st.session_state.active_agents.remove(agent)
        with col2:
            stance_options  = ["Strong Support","Support","Neutral","Challenge","Strong Challenge"]
            current_stance  = st.session_state.agent_stances.get(agent, "Neutral")
            if current_stance not in stance_options: current_stance = "Neutral"
            st.session_state.agent_stances[agent] = st.selectbox(
                "Stance", stance_options,
                index=stance_options.index(current_stance),
                key=f"stance_{agent}", label_visibility="collapsed"
            )

    st.markdown("---")
    st.markdown("### 📋 Context")
    st.session_state.context_injection = st.text_area(
        "Shared Context", value=st.session_state.context_injection,
        height=80, placeholder="Background info all agents should know..."
    )

# =============================================================================
# MAIN CONTENT
# =============================================================================

st.markdown("""
<div class="main-header">
    <h1>🧬 Focus Group Lab <span class="v34-badge">V34</span></h1>
    <p>Business Edition · Multi-Agent AI Advisory Platform</p>
</div>
""", unsafe_allow_html=True)

mode_emoji = {"assigned":"🎭","raw":"🔬","swapped":"🔄","custom":"✏️"}.get(st.session_state.role_mode,"❓")
mode_name  = {"assigned":"Assigned Roles","raw":"Raw Voice","swapped":"Swapped Roles","custom":"Custom Roles"}.get(st.session_state.role_mode,"")
temp_key   = st.session_state.get("temperature_condition","NATIVE")
temp_label = TEMPERATURE_CONDITIONS.get(temp_key,{}).get("label","NATIVE")
st.info(f"**Role Mode:** {mode_emoji} {mode_name}   |   **Temperature:** {temp_label}   |   **Agents:** {', '.join(st.session_state.active_agents)}")

session_type = st.radio("Session Type", ["Single Round", "Multi-Round", "Live Discussion"], horizontal=True)

# =============================================================================
# LIVE DISCUSSION
# =============================================================================
if session_type == "Live Discussion":
    st.markdown("### 🎭 Live Discussion")

    if st.session_state.pull_aside_active:
        agent = st.session_state.pull_aside_agent
        emoji = AGENT_EMOJIS.get(agent, '🤖')
        st.markdown(f"""
        <div class="pull-aside-container">
            <div class="pull-aside-header">🔒 PRIVATE: {emoji} {agent}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.session_state.pull_aside_thread:
            st.markdown('<div class="pull-aside-thread">', unsafe_allow_html=True)
            for entry in st.session_state.pull_aside_thread:
                speaker = entry.get('speaker','Unknown')
                if speaker == "Conductor":
                    st.markdown(f"**🎹 Conductor:** {entry['content']}")
                else:
                    st.markdown(f"**{emoji} {agent}:** {entry['content']}")
                st.markdown("---")
            st.markdown('</div>', unsafe_allow_html=True)
        aside_msg = st.text_input("Your message:", placeholder="Private message...", key="aside_input")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("💬 Send", type="primary", use_container_width=True) and aside_msg:
                st.session_state.pull_aside_thread.append({"speaker":"Conductor","content":aside_msg})
                with st.spinner(f"{emoji} {agent} responding..."):
                    response = call_agent_pull_aside(agent, st.session_state.pull_aside_thread, st.session_state.discussion_topic)
                    st.session_state.pull_aside_thread.append({"speaker":agent,"content":response})
                st.rerun()
        with col2:
            if st.button("📝 Inject & Return", use_container_width=True):
                summary = st.session_state.get('aside_summary','')
                if summary:
                    st.session_state.discussion_thread.append({
                        "agent":"Conductor","content":f"[After private conversation with {agent}]: {summary}",
                        "type":"intervention","round":st.session_state.discussion_round
                    })
                st.session_state.pull_aside_active = False
                st.session_state.pull_aside_thread = []
                st.rerun()
        with col3:
            if st.button("🔙 Return", use_container_width=True):
                st.session_state.pull_aside_active = False
                st.session_state.pull_aside_thread = []
                st.rerun()
        st.text_input("Summary to inject (optional):", key="aside_summary", placeholder="Brief note about what was clarified...")

    else:
        topic = st.text_area("Discussion Topic", value=st.session_state.discussion_topic, height=100, placeholder="What should the group discuss?")
        st.session_state.discussion_topic = topic

        st.markdown(f"""
        <div class="resolution-tracker">
            <strong>Status:</strong> {st.session_state.consensus_status} | 
            <strong>Round:</strong> {st.session_state.discussion_round} |
            <strong>Locked:</strong> {'🔒 Yes' if st.session_state.discussion_locked else '🔓 No'}
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.discussion_thread:
            st.markdown("### 💬 Discussion Thread")
            st.markdown('<div class="discussion-thread">', unsafe_allow_html=True)
            for entry in st.session_state.discussion_thread:
                agent_name = entry.get('agent','Unknown')
                emoji      = AGENT_EMOJIS.get(agent_name,'🤖')
                entry_type = entry.get('type','response')
                if entry_type == "intervention":
                    st.markdown(f"<div class='agent-box conductor-box'><strong>{emoji} {agent_name}:</strong> {entry['content']}</div>", unsafe_allow_html=True)
                elif entry_type == "directed":
                    directed_from = entry.get('directed_from','')
                    from_emoji    = AGENT_EMOJIS.get(directed_from,'🤖')
                    st.markdown(f"""<div class="directed-frame">
                        <span class="directed-header">🎯 DIRECT RESPONSE</span><br>
                        <strong>{emoji} {agent_name}</strong> responding to <strong>{from_emoji} {directed_from}</strong>
                    </div>""", unsafe_allow_html=True)
                    st.markdown(entry['content'])
                elif entry_type == "resolution":
                    st.markdown(f"""<div style="background:linear-gradient(135deg,#4CAF50,#8BC34A);color:white;padding:1rem;border-radius:10px;margin:0.5rem 0;">
                        <strong>📋 RESOLUTION (by {emoji} {agent_name}):</strong></div>""", unsafe_allow_html=True)
                    st.markdown(entry['content'])
                else:
                    box_class = f"{agent_name.lower()}-box" if agent_name != "Conductor" else "conductor-box"
                    st.markdown(f"<div class='agent-box {box_class}'><strong>{emoji} {agent_name}:</strong></div>", unsafe_allow_html=True)
                    st.markdown(entry['content'])
                st.markdown("---")
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="conductor-toolkit"><strong>🎹 Conductor Toolkit</strong></div>', unsafe_allow_html=True)

        # Row 1: Flow Control
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            run_round_btn = st.button("▶️ Run Round", type="primary", use_container_width=True,
                disabled=st.session_state.discussion_locked or not topic)
        with col2:
            agent_options = ["— Direct to Agent —"] + st.session_state.active_agents
            directed_to   = st.selectbox("Direct to:", agent_options, key="directed_agent", label_visibility="collapsed")
        with col3:
            if st.button("➕ Add Turn", use_container_width=True, disabled=st.session_state.discussion_locked or not topic):
                if directed_to and directed_to != "— Direct to Agent —":
                    with st.spinner(f"Getting {directed_to}'s contribution..."):
                        response = call_agent_discussion(directed_to, topic, st.session_state.discussion_thread)
                        st.session_state.discussion_thread.append({
                            "agent":directed_to,"content":response,
                            "type":"directed","directed_from":"Conductor",
                            "round":st.session_state.discussion_round
                        })
                    st.rerun()
        with col4:
            if st.button("📥 Export MD", use_container_width=True):
                st.download_button("Download", export_to_markdown(),
                    file_name=f"discussion_{st.session_state.session_id}.md", mime="text/markdown")

        # Row 2: Conductor Interventions
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            conductor_msg = st.text_input("Conductor says:", placeholder="Intervene...", key="conductor_msg", label_visibility="collapsed")
        with col2:
            if st.button("🎹 Intervene", use_container_width=True) and conductor_msg:
                st.session_state.discussion_thread.append({
                    "agent":"Conductor","content":conductor_msg,
                    "type":"intervention","round":st.session_state.discussion_round
                })
                st.rerun()
        with col3:
            pull_aside_agent = st.selectbox("Pull aside:", ["— Pull Aside —"] + st.session_state.active_agents,
                key="pull_aside_select", label_visibility="collapsed")
        with col4:
            if st.button("🔒 Pull Aside", use_container_width=True):
                if pull_aside_agent and pull_aside_agent != "— Pull Aside —":
                    st.session_state.pull_aside_active = True
                    st.session_state.pull_aside_agent  = pull_aside_agent
                    st.session_state.pull_aside_thread = []
                    st.rerun()

        # Row 3: Resolution
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("🔒 Lock", use_container_width=True):
                st.session_state.discussion_locked = True
                st.rerun()
        with col2:
            if st.button("🔓 Unlock", use_container_width=True):
                st.session_state.discussion_locked = False
                st.rerun()
        with col3:
            if st.button("🗑️ Clear", use_container_width=True):
                st.session_state.discussion_thread  = []
                st.session_state.discussion_round   = 0
                st.session_state.consensus_status   = "None"
                st.session_state.discussion_locked  = False
                st.session_state.resolution_text    = ""
                st.rerun()
        with col4:
            resolution_options = ["Conductor"] + st.session_state.active_agents
            resolution_agent   = st.selectbox("Synthesizer:", resolution_options,
                key="resolution_agent_select", label_visibility="collapsed")

        if st.button("📋 Resolve Discussion", use_container_width=True):
            st.session_state.consensus_status = "Full"
            st.session_state.resolution_agent = resolution_agent
            if resolution_agent == "Conductor":
                st.session_state.discussion_thread.append({
                    "agent":"Conductor","content":"✅ DISCUSSION RESOLVED.",
                    "type":"intervention","round":st.session_state.discussion_round
                })
            else:
                with st.spinner(f"📋 {AGENT_EMOJIS[resolution_agent]} {resolution_agent} writing resolution..."):
                    resolution = call_agent_resolution(resolution_agent, st.session_state.discussion_topic, st.session_state.discussion_thread)
                    st.session_state.resolution_text = resolution
                    st.session_state.discussion_thread.append({
                        "agent":resolution_agent,"content":resolution,
                        "type":"resolution","round":st.session_state.discussion_round
                    })
            st.rerun()

        if run_round_btn and topic and st.session_state.active_agents:
            with st.status(f"Running Round {st.session_state.discussion_round + 1}...", expanded=True) as status:
                for agent_name in st.session_state.active_agents:
                    status.update(label=f"{AGENT_EMOJIS[agent_name]} {agent_name} responding...")
                    response = call_agent_discussion(agent_name, topic, st.session_state.discussion_thread)
                    st.session_state.discussion_thread.append({
                        "agent":agent_name,"content":response,
                        "type":"response","round":st.session_state.discussion_round + 1
                    })
                status.update(label=f"✅ Round {st.session_state.discussion_round + 1} Complete!", state="complete")
            st.session_state.discussion_round += 1
            st.rerun()

# =============================================================================
# MULTI-ROUND
# =============================================================================
elif session_type == "Multi-Round":
    st.markdown("### 🔄 Multi-Round Iterative Mode")
    st.markdown("*Each round: all agents respond in parallel, seeing all previous rounds.*")

    current_round = len(st.session_state.multi_round_history) + 1
    st.info(f"**Current Round:** {current_round}")

    prompt = st.text_area(f"Round {current_round} Prompt", height=100,
        placeholder="What should the agents respond to this round?", key=f"mr_prompt_{current_round}")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        run_round_btn = st.button("▶️ Run Round", type="primary", use_container_width=True)
    with col2:
        if st.button("🗑️ Clear All", use_container_width=True):
            st.session_state.multi_round_history = []
            st.rerun()
    with col3:
        if st.button("📥 Export MD", use_container_width=True):
            st.download_button("Download MD", export_to_markdown(),
                file_name=f"multiround_{st.session_state.session_id}.md", mime="text/markdown")
    with col4:
        view_mode = st.selectbox("View", ["Grid","Present"], label_visibility="collapsed", key="multi_view")
        st.session_state.view_mode = view_mode.lower()

    if run_round_btn and prompt and st.session_state.active_agents:
        round_responses = {}
        with st.status(f"Running Round {current_round}...", expanded=True) as status:
            for agent_name in st.session_state.active_agents:
                stance = st.session_state.agent_stances.get(agent_name,"Neutral")
                status.update(label=f"{AGENT_EMOJIS[agent_name]} {agent_name} ({stance})...")
                response = call_agent_multi_round(agent_name, prompt, st.session_state.multi_round_history, current_round)
                round_responses[agent_name] = response
            status.update(label=f"✅ Round {current_round} Complete!", state="complete")
        st.session_state.multi_round_history.append({"prompt": prompt, "responses": round_responses})
        st.rerun()

    for i, rd in enumerate(st.session_state.multi_round_history, 1):
        st.markdown(f'<div class="round-separator">📍 Round {i} — {rd.get("prompt","")[:60]}{"..." if len(rd.get("prompt",""))>60 else ""}</div>', unsafe_allow_html=True)
        with st.container():
            if st.session_state.view_mode == "grid":
                render_agent_response_grid(rd["responses"])
            else:
                render_present_mode(rd["responses"])
        st.markdown("---")

# =============================================================================
# SINGLE ROUND
# =============================================================================
else:
    st.markdown("### 📝 Single Round")
    prompt = st.text_area("Your Prompt", height=120, placeholder="What's the problem, question, or challenge?")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        run_btn = st.button("🚀 Run", type="primary", use_container_width=True)
    with col2:
        clear_btn = st.button("🗑️ Clear", use_container_width=True)
    with col3:
        if st.button("📥 Export MD", use_container_width=True):
            st.download_button("Download MD", export_to_markdown(),
                file_name=f"session_{st.session_state.session_id}.md", mime="text/markdown")
    with col4:
        view_mode = st.selectbox("View", ["Grid","Present"], label_visibility="collapsed")
        st.session_state.view_mode = view_mode.lower()

    if run_btn and prompt and st.session_state.active_agents:
        st.session_state.round1_responses = {}
        with st.status("Running...", expanded=True) as status:
            for agent_name in st.session_state.active_agents:
                stance      = st.session_state.agent_stances.get(agent_name,"Neutral")
                role_preview = get_agent_role(agent_name)[:40] + "..."
                status.update(label=f"{AGENT_EMOJIS[agent_name]} {agent_name} ({stance}) — {role_preview}")
                system   = build_system_prompt(agent_name)
                user_msg = build_control_header() + "\n\n" + prompt
                response = AGENT_FUNCTIONS[agent_name](user_msg, system)
                st.session_state.round1_responses[agent_name] = response
            status.update(label="✅ Complete!", state="complete")
        st.rerun()

    if clear_btn:
        st.session_state.round1_responses = {}
        st.rerun()

    if st.session_state.round1_responses:
        st.markdown("### 📊 Responses")
        if st.session_state.view_mode == "grid":
            render_agent_response_grid(st.session_state.round1_responses)
        else:
            render_present_mode(st.session_state.round1_responses)

        st.markdown("---")
        if st.button("🧬 SYN-IQ Analysis"):
            responses = list(st.session_state.round1_responses.values())
            if len(responses) >= 2:
                score, level, novel = calculate_syniq_quick(responses[:-1], responses[-1])
                box_class = "high-syniq" if level=="HIGH" else ("medium-syniq" if level=="MEDIUM" else "low-syniq")
                st.markdown(f'<div class="syniq-score-box {box_class}"><h1>{score:.0f}</h1><p>SYN-IQ Score ({level})</p></div>', unsafe_allow_html=True)
                if novel:
                    st.info(f"🆕 Novel concepts introduced: {', '.join(list(novel)[:15])}")

# =============================================================================
# SESSION NOTES
# =============================================================================
st.markdown("---")
st.markdown("### 🎹 Session Notes")
st.session_state.session_notes = st.text_area(
    "Notes",
    value=st.session_state.session_notes,
    height=120,
    placeholder="Key decisions, observations, follow-up actions...",
    label_visibility="collapsed"
)

st.markdown("---")
st.markdown("""
<div style="text-align:center; color:#666; padding:1rem;">
    <strong>Focus Group Lab V34</strong> — Business Edition<br>
    Multi-Agent AI Advisory Platform · SYNINT Team — March 2026<br>
    🎭 Assigned | 🔬 Raw Voice | 🔄 Swapped | ✏️ Custom<br>
    🌿 NATIVE | 🧊 COLD | 🌤️ WARM | 🔥 FIRE<br>
    📝 Single Round | 🔄 Multi-Round | 🎭 Live Discussion
</div>
""", unsafe_allow_html=True)
