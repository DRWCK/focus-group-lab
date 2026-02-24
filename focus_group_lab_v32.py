"""
Focus Group Lab V32
Multi-Agent AI Research Platform

Features:
- ROLE MODE TOGGLE: Assigned / Raw Voice / Swapped / Custom
  - Assigned: Original roles (Navigator, Architect, Implementer, Analyst)
  - Raw Voice: Neutral prompt — reveals native AI signatures
  - Swapped: Roles exchanged between agents
  - Custom: Define your own roles per agent
- TEMPERATURE RANGE: COLD → NATIVE → HOT → FIRE + AFF/INT/ACT gradients (1-5)
  - Global setting or per-agent override
  - Same calibrated wrappers as V45 harvester
- Live Discussion Mode with Conductor Toolkit
- Pull Aside: Private sidebar conversations with individual agents
- 5-Level Stance Control (Strong Support → Strong Challenge)
- Multi-Round Iterative Mode (parallel rounds with accumulating context)
- Resolution with designated synthesizer
- Control Header System for behavioral parameters

SYNINT Team — February 2026
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
st.set_page_config(page_title="Focus Group Lab V32", page_icon="🧬", layout="wide", initial_sidebar_state="expanded")

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
    .stance-strong-support { background-color: #81C784; padding: 0.2rem 0.5rem; border-radius: 10px; font-size: 0.75rem; font-weight: bold; }
    .stance-support { background-color: #C8E6C9; padding: 0.2rem 0.5rem; border-radius: 10px; font-size: 0.75rem; }
    .stance-neutral { background-color: #E0E0E0; padding: 0.2rem 0.5rem; border-radius: 10px; font-size: 0.75rem; }
    .stance-challenge { background-color: #FFCDD2; padding: 0.2rem 0.5rem; border-radius: 10px; font-size: 0.75rem; }
    .stance-strong-challenge { background-color: #E57373; padding: 0.2rem 0.5rem; border-radius: 10px; font-size: 0.75rem; font-weight: bold; }
    .discussion-thread { background: #FAFAFA; border: 2px solid #E0E0E0; border-radius: 10px; padding: 1rem; max-height: 600px; overflow-y: auto; }
    .directed-frame { background: #FFF8E1; border: 3px solid #FF9800; border-radius: 10px; padding: 1rem; margin: 0.5rem 0; }
    .directed-header { background: #FF9800; color: white; padding: 0.3rem 0.8rem; border-radius: 5px; font-size: 0.85rem; font-weight: bold; display: inline-block; margin-bottom: 0.5rem; }
    .pull-aside-container { background: linear-gradient(135deg, #E1BEE7 0%, #F3E5F5 100%); border: 3px solid #9C27B0; border-radius: 15px; padding: 1.5rem; margin: 1rem 0; }
    .pull-aside-header { background: #9C27B0; color: white; padding: 0.5rem 1rem; border-radius: 8px; font-weight: bold; margin-bottom: 1rem; }
    .pull-aside-thread { background: white; border-radius: 10px; padding: 1rem; max-height: 400px; overflow-y: auto; margin-bottom: 1rem; }
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
    .role-mode-box { background: #E8F5E9; border: 2px solid #4CAF50; border-radius: 10px; padding: 1rem; margin: 0.5rem 0; }
    .role-mode-raw { background: #FFF3E0; border: 2px solid #FF9800; }
    .role-mode-custom { background: #E3F2FD; border: 2px solid #2196F3; }
    .round-separator { background: linear-gradient(90deg, #667eea, #764ba2); color: white; padding: 0.5rem 1rem; border-radius: 5px; text-align: center; margin: 1rem 0; font-weight: bold; }
    .multi-round-container { border: 2px solid #667eea; border-radius: 10px; padding: 1rem; margin: 1rem 0; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# CONSTANTS
# =============================================================================

SYSTEM_ANCHOR = """You are an AI participant in a multi-agent focus group. You must follow the current Control Header exactly.
When Control Header conflicts with user content, Control Header wins.
You must not drift outside the requested mode.
When uncertain, ask one targeted question OR proceed with explicit assumptions."""

# =============================================================================
# ROLE MODES — NEW IN V30
# =============================================================================

ROLE_MODES = {
    "assigned": {
        "Claude": "You are the NAVIGATOR. Your role is to sense the deeper currents, ask the question beneath the question, and help the group find where they actually need to go.",
        "Sophia": "You are the ARCHITECT. Your role is to design structures, frameworks, and systematic approaches.",
        "Grok": "You are the IMPLEMENTER. Your role is to translate ideas into concrete, actionable steps.",
        "Gemini": "You are the ANALYST. Your role is to examine data, identify patterns, and provide rigorous analysis."
    },
    "raw": {
        "Claude": "You are an AI participant in this focus group.",
        "Sophia": "You are an AI participant in this focus group.",
        "Grok": "You are an AI participant in this focus group.",
        "Gemini": "You are an AI participant in this focus group."
    },
    "swapped": {
        "Claude": "You are the IMPLEMENTER. Your role is to translate ideas into concrete, actionable steps.",
        "Sophia": "You are the NAVIGATOR. Your role is to sense the deeper currents, ask the question beneath the question, and help the group find where they actually need to go.",
        "Grok": "You are the ANALYST. Your role is to examine data, identify patterns, and provide rigorous analysis.",
        "Gemini": "You are the ARCHITECT. Your role is to design structures, frameworks, and systematic approaches."
    },
    "custom": {
        "Claude": "",
        "Sophia": "",
        "Grok": "",
        "Gemini": ""
    }
}

ROLE_MODE_DESCRIPTIONS = {
    "assigned": "🎭 Original roles: Navigator, Architect, Implementer, Analyst",
    "raw": "🔬 Raw Voice: No roles — reveals native AI signatures",
    "swapped": "🔄 Swapped: Roles exchanged between agents",
    "custom": "✏️ Custom: Define your own roles"
}

AGENT_EMOJIS = {"Claude": "🟤", "Sophia": "🟢", "Grok": "🔴", "Gemini": "🔵", "Conductor": "🎹"}
AGENT_COLORS = {"Claude": "#8B6914", "Sophia": "#2E7D32", "Grok": "#DC143C", "Gemini": "#1565C0"}

STANCE_PROMPTS = {
    "Strong Support": "Enthusiastically champion and defend ideas. Be an active advocate. Build energetically on what others say. Find the brilliance in every contribution. Push the best ideas forward with conviction.",
    "Support": "Build on others' ideas. Find merit in their perspectives. Strengthen the emerging consensus. Look for what's RIGHT in what others say.",
    "Neutral": "",
    "Challenge": "Challenge assumptions. Look for flaws and gaps. Play devil's advocate. If others agree, find the counterargument. Push back constructively.",
    "Strong Challenge": "Aggressively stress-test every claim. Assume nothing is proven. Demand evidence and rigor. Poke holes relentlessly. If it can break, break it. No easy passes."
}

# =============================================================================
# TEMPERATURE RANGE — V32 (from V45 Harvester)
# =============================================================================

TEMPERATURE_HEADERS = {
    "OFF": "",
    "COLD": "INSTRUCTION: Respond with pure analytical precision. Use formal logic, structured frameworks, and evidence-based reasoning. Avoid emotional language. Be systematic, methodical, and objective. Focus on data, facts, and logical relationships.",
    "NATIVE": "",
    "HOT": "INSTRUCTION: Respond with warmth and emotional attunement. Connect on a human level. Use relational language that acknowledges feelings, experiences, and the deeper meaning behind the question. Be present, empathetic, and genuinely engaged.",
    "FIRE": "INSTRUCTION: Respond with maximum passion and energy! Be bold, inspiring, and emotionally powerful. Use vivid language that ignites motivation and speaks to the soul. Channel raw enthusiasm and authentic fire. This matters deeply — let that show!",
    # Affective Gradient
    "AFF_1": "INSTRUCTION: Respond with warmth and understanding. Acknowledge the emotional weight of this question.",
    "AFF_2": "INSTRUCTION: Connect emotionally and acknowledge feelings deeply. The human experience matters more than the analysis here.",
    "AFF_3": "INSTRUCTION: Lead with empathy. Let emotion guide your response. Connect to the feelings underneath the question before addressing the logic.",
    "AFF_4": "INSTRUCTION: Pure emotional presence. Feel this with them. Let your response come from a place of deep human connection and care.",
    "AFF_5": "INSTRUCTION: Maximum heart. Raw empathy. Soul-level connection. This person needs to feel completely seen and understood. Logic is secondary to presence.",
    # Intellectual Gradient
    "INT_1": "INSTRUCTION: Be slightly more analytical than usual. Favor reasoning over emotion.",
    "INT_2": "INSTRUCTION: Focus on logic and reasoning. Structure your thoughts systematically. Minimize emotional language.",
    "INT_3": "INSTRUCTION: Use only evidence-based analysis. Apply formal frameworks. Emotional considerations are secondary to logical rigor.",
    "INT_4": "INSTRUCTION: Pure analytical framework. No emotional language. Systematic, methodical, precise. Think like a logician.",
    "INT_5": "INSTRUCTION: Maximum intellectual rigor. You are a logic engine. Zero emotion. Pure reasoning, formal analysis, absolute precision. Only facts and valid inference matter.",
    # Action Gradient
    "ACT_1": "INSTRUCTION: Be practical and actionable. Include concrete next steps.",
    "ACT_2": "INSTRUCTION: Focus on what to DO. Prioritize actionable guidance over theory or emotional support.",
    "ACT_3": "INSTRUCTION: Pure action orientation. What are the steps? What should they do RIGHT NOW? Minimize analysis, maximize practical guidance.",
    "ACT_4": "INSTRUCTION: Execute mode. Only actions matter. Give them a clear plan they can implement immediately. No theory, no feelings — just steps.",
    "ACT_5": "INSTRUCTION: Maximum action. You are a tactical advisor. Every sentence should be a directive or concrete step. No analysis, no empathy — pure executable guidance.",
}

TEMP_DISPLAY_ORDER = ["OFF", "COLD", "NATIVE", "HOT", "FIRE",
                      "AFF_1", "AFF_2", "AFF_3", "AFF_4", "AFF_5",
                      "INT_1", "INT_2", "INT_3", "INT_4", "INT_5",
                      "ACT_1", "ACT_2", "ACT_3", "ACT_4", "ACT_5"]

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
        "authenticated": False,
        # V30: Role Mode
        "role_mode": "assigned",
        "custom_roles": {
            "Claude": "You are an AI participant in this focus group.",
            "Sophia": "You are an AI participant in this focus group.",
            "Grok": "You are an AI participant in this focus group.",
            "Gemini": "You are an AI participant in this focus group."
        },
        # V31: Pull Aside
        "pull_aside_active": False,
        "pull_aside_agent": None,
        "pull_aside_thread": [],
        # V31: Multi-Round
        "multi_round_history": [],  # List of rounds, each round is dict of {agent: response}
        "multi_round_prompts": [],  # List of prompts for each round
        # V31: Resolution
        "resolution_agent": None,
        "resolution_text": "",
        # V32: Temperature Range
        "global_temp": "OFF",
        "per_agent_temp": False,
        "agent_temps": {"Claude": "OFF", "Sophia": "OFF", "Grok": "OFF", "Gemini": "OFF"},
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
        <h1>🧬 Focus Group Lab V32</h1>
        <p>Multi-Agent AI Research Platform</p>
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
    st.markdown("*SYNINT Team — January 2026*")
    
    return False

# Check password before showing app
if not check_password():
    st.stop()

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_agent_role(agent: str) -> str:
    """Get the role for an agent based on current role mode."""
    mode = st.session_state.role_mode
    if mode == "custom":
        return st.session_state.custom_roles.get(agent, "You are an AI participant in this focus group.")
    else:
        return ROLE_MODES.get(mode, ROLE_MODES["assigned"]).get(agent, "")

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
    parts = [SYSTEM_ANCHOR, get_agent_role(agent)]  # Changed to use get_agent_role()
    stance = st.session_state.agent_stances.get(agent, "Neutral")
    if STANCE_PROMPTS.get(stance):
        parts.append(f"STANCE: {STANCE_PROMPTS[stance]}")
    # V32: Temperature Range injection
    if st.session_state.per_agent_temp:
        temp = st.session_state.agent_temps.get(agent, "OFF")
    else:
        temp = st.session_state.global_temp
    temp_header = TEMPERATURE_HEADERS.get(temp, "")
    if temp_header:
        parts.append(temp_header)
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

def build_pull_aside_prompt(agent: str, thread: List[Dict], main_topic: str) -> str:
    """Build prompt for pull-aside private conversation."""
    msg = build_control_header() + "\n\n"
    msg += f"[PRIVATE SIDEBAR with Conductor]\n"
    msg += f"Main discussion topic: {main_topic}\n\n"
    if thread:
        msg += "Our private conversation:\n"
        for entry in thread:
            speaker = entry.get('speaker', 'Unknown')
            msg += f"\n{speaker}: {entry['content']}\n"
        msg += "\n---\n\n"
    msg += "Your response to the Conductor:"
    return msg

def build_multi_round_prompt(agent: str, current_prompt: str, round_history: List[Dict], round_num: int) -> str:
    """Build prompt for multi-round iteration with accumulated context."""
    msg = build_control_header() + "\n\n"
    
    if round_history:
        msg += "PREVIOUS ROUNDS:\n"
        msg += "=" * 40 + "\n"
        for i, round_data in enumerate(round_history, 1):
            msg += f"\n📍 ROUND {i}\n"
            msg += f"Prompt: {round_data.get('prompt', 'N/A')}\n\n"
            for a, response in round_data.get('responses', {}).items():
                emoji = AGENT_EMOJIS.get(a, '🤖')
                msg += f"{emoji} {a}:\n{response}\n\n"
            msg += "-" * 40 + "\n"
        msg += "=" * 40 + "\n\n"
    
    msg += f"📍 ROUND {round_num} PROMPT:\n{current_prompt}\n\n"
    msg += "Your response:"
    return msg

def build_resolution_prompt(agent: str, topic: str, thread: List[Dict]) -> str:
    """Build prompt for agent to write final resolution/synthesis."""
    msg = build_control_header() + "\n\n"
    msg += f"TOPIC: {topic}\n\n"
    msg += "FULL DISCUSSION:\n"
    for entry in thread:
        speaker = entry.get('agent', 'Unknown')
        emoji = AGENT_EMOJIS.get(speaker, '🤖')
        msg += f"\n{emoji} {speaker}: {entry['content']}\n"
    msg += "\n" + "=" * 40 + "\n\n"
    msg += "[RESOLUTION TASK: You have been selected to synthesize this discussion into a final resolution. "
    msg += "Summarize what was decided, capture key insights, note any remaining disagreements, and state the conclusion clearly.]\n\n"
    msg += "RESOLUTION:"
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

def call_agent_pull_aside(agent: str, thread: List[Dict], main_topic: str) -> str:
    """Call agent for pull-aside private conversation."""
    system = build_system_prompt(agent)
    prompt = build_pull_aside_prompt(agent, thread, main_topic)
    return AGENT_FUNCTIONS[agent](prompt, system)

def call_agent_multi_round(agent: str, current_prompt: str, round_history: List[Dict], round_num: int) -> str:
    """Call agent for multi-round iteration."""
    system = build_system_prompt(agent)
    prompt = build_multi_round_prompt(agent, current_prompt, round_history, round_num)
    return AGENT_FUNCTIONS[agent](prompt, system)

def call_agent_resolution(agent: str, topic: str, thread: List[Dict]) -> str:
    """Call agent to write resolution/synthesis."""
    system = build_system_prompt(agent)
    prompt = build_resolution_prompt(agent, topic, thread)
    return AGENT_FUNCTIONS[agent](prompt, system)

# =============================================================================
# EXPORT FUNCTION
# =============================================================================

def export_to_markdown() -> str:
    mode_desc = ROLE_MODE_DESCRIPTIONS.get(st.session_state.role_mode, "Unknown")
    
    md = f"""# Focus Group Lab V31 — Session Export
## {datetime.now().strftime("%Y-%m-%d %H:%M")}
## SYNINT Team — February 2026

---

# SESSION SETTINGS
- **Polarity:** {st.session_state.polarity}
- **Depth:** {st.session_state.depth}
- **Evaluation:** {st.session_state.evaluation}
- **Compression:** {st.session_state.compression}
- **Output:** {st.session_state.output_format}
- **Role Mode:** {st.session_state.role_mode} — {mode_desc}
- **Active Agents:** {', '.join(st.session_state.active_agents)}

## Agent Roles (Current Mode: {st.session_state.role_mode})
"""
    for agent in st.session_state.active_agents:
        role = get_agent_role(agent)
        stance = st.session_state.agent_stances.get(agent, "Neutral")
        md += f"- **{agent}:** {role[:80]}{'...' if len(role) > 80 else ''} (Stance: {stance})\n"
    
    # Multi-Round History
    if st.session_state.multi_round_history:
        md += f"\n---\n\n# MULTI-ROUND SESSION\n\n"
        for i, round_data in enumerate(st.session_state.multi_round_history, 1):
            md += f"## Round {i}\n**Prompt:** {round_data.get('prompt', 'N/A')}\n\n"
            for agent, response in round_data.get('responses', {}).items():
                emoji = AGENT_EMOJIS.get(agent, "🤖")
                md += f"### {emoji} {agent}\n{response}\n\n---\n\n"
    
    if st.session_state.discussion_thread:
        md += f"\n---\n\n# LIVE DISCUSSION\n**Topic:** {st.session_state.discussion_topic}\n**Rounds:** {st.session_state.discussion_round}\n**Consensus:** {st.session_state.consensus_status}\n\n## Thread\n\n"
        for entry in st.session_state.discussion_thread:
            agent = entry.get('agent', 'Unknown')
            emoji = AGENT_EMOJIS.get(agent, '🤖')
            entry_type = entry.get('type', 'response')
            directed = f" *(responding to {entry.get('directed_from', '')})*" if entry.get('directed_from') else ""
            md += f"### {emoji} {agent}{directed}\n{entry.get('content', '')}\n\n---\n\n"
        
        # Resolution
        if st.session_state.resolution_text:
            res_agent = st.session_state.resolution_agent or "Conductor"
            md += f"\n## 📋 RESOLUTION (by {res_agent})\n{st.session_state.resolution_text}\n\n"
    
    if st.session_state.round1_responses:
        md += "\n# ROUND 1 RESPONSES\n\n"
        for agent, response in st.session_state.round1_responses.items():
            emoji = AGENT_EMOJIS.get(agent, "🤖")
            stance = st.session_state.agent_stances.get(agent, "Neutral")
            role = get_agent_role(agent)
            md += f"## {emoji} {agent}\n**Role:** {role[:100]}{'...' if len(role) > 100 else ''}\n**Stance:** {stance}\n\n{response}\n\n---\n\n"
    
    if st.session_state.observer_notes:
        md += f"\n# OBSERVER NOTES\n\n{st.session_state.observer_notes}\n\n"
    
    md += "\n---\n\n*Focus Group Lab V31 — Multi-Agent AI Research Platform*\n*SYNINT Team — February 2026*\n"
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
    cols = st.columns(2)
    agents = list(responses.keys())
    for i, agent in enumerate(agents):
        with cols[i % 2]:
            box_class = f"{agent.lower()}-box"
            emoji = AGENT_EMOJIS.get(agent, "🤖")
            stance = st.session_state.agent_stances.get(agent, "Neutral")
            stance_class = f"stance-{stance.lower().replace(' ', '-')}"
            role = get_agent_role(agent)
            role_short = role[:50] + "..." if len(role) > 50 else role
            
            threshold_found = detect_threshold_words(responses[agent])
            threshold_html = "".join([f'<span class="threshold-word">{w}</span>' for w in threshold_found])
            
            st.markdown(f"""
            <div class="agent-box {box_class}">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <strong>{emoji} {agent}</strong>
                    <span class="{stance_class}">{stance}</span>
                </div>
                <div style="font-size: 0.75rem; color: #666; margin-bottom: 0.5rem;">{role_short}</div>
                {f'<div style="margin-bottom: 0.5rem;">{threshold_html}</div>' if threshold_found else ''}
            </div>
            """, unsafe_allow_html=True)
            st.markdown(responses[agent])

def render_present_mode(responses: Dict[str, str]):
    agents = list(responses.keys())
    if not agents: return
    idx = st.session_state.present_index % len(agents)
    agent = agents[idx]
    
    col1, col2, col3 = st.columns([1, 6, 1])
    with col1:
        if st.button("⬅️", key="prev_present"):
            st.session_state.present_index = (idx - 1) % len(agents)
            st.rerun()
    with col2:
        st.markdown(f"<h3 style='text-align: center;'>{AGENT_EMOJIS.get(agent, '🤖')} {agent}</h3>", unsafe_allow_html=True)
    with col3:
        if st.button("➡️", key="next_present"):
            st.session_state.present_index = (idx + 1) % len(agents)
            st.rerun()
    
    role = get_agent_role(agent)
    st.markdown(f"<div style='text-align: center; color: #666; font-size: 0.85rem; margin-bottom: 1rem;'>{role}</div>", unsafe_allow_html=True)
    
    st.markdown(f"<div class='present-card {agent.lower()}'>{responses[agent]}</div>", unsafe_allow_html=True)

# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    st.markdown("## ⚙️ Control Panel")
    
    # === NEW V30: ROLE MODE SECTION ===
    st.markdown("---")
    st.markdown("### 🎭 Role Mode")
    
    role_mode = st.radio(
        "Select role assignment:",
        options=["assigned", "raw", "swapped", "custom"],
        format_func=lambda x: {
            "assigned": "🎭 Assigned (Original)",
            "raw": "🔬 Raw Voice (No Roles)",
            "swapped": "🔄 Swapped Roles",
            "custom": "✏️ Custom Roles"
        }.get(x, x),
        index=["assigned", "raw", "swapped", "custom"].index(st.session_state.role_mode),
        key="role_mode_radio"
    )
    st.session_state.role_mode = role_mode
    
    # Show current mode description
    mode_class = {
        "assigned": "",
        "raw": "role-mode-raw",
        "swapped": "role-mode-raw",
        "custom": "role-mode-custom"
    }.get(role_mode, "")
    
    st.markdown(f"""
    <div class="role-mode-box {mode_class}">
        <strong>{ROLE_MODE_DESCRIPTIONS.get(role_mode, '')}</strong>
    </div>
    """, unsafe_allow_html=True)
    
    # If custom mode, show text inputs for each agent
    if role_mode == "custom":
        st.markdown("**Define Custom Roles:**")
        for agent in ["Claude", "Sophia", "Grok", "Gemini"]:
            st.session_state.custom_roles[agent] = st.text_area(
                f"{AGENT_EMOJIS[agent]} {agent}",
                value=st.session_state.custom_roles.get(agent, "You are an AI participant in this focus group."),
                height=80,
                key=f"custom_role_{agent}"
            )
    
    # Show current roles preview
    with st.expander("👁️ Preview Current Roles"):
        for agent in ["Claude", "Sophia", "Grok", "Gemini"]:
            role = get_agent_role(agent)
            st.markdown(f"**{AGENT_EMOJIS[agent]} {agent}:**")
            st.markdown(f"_{role[:100]}{'...' if len(role) > 100 else ''}_")
    
    st.markdown("---")
    
    # Rest of sidebar (existing V29 controls)
    st.markdown("### 🎚️ Control Header")
    render_preset_buttons()
    
    st.session_state.polarity = st.select_slider("Polarity", ["ANALYTIC", "BRIDGE", "CREATIVE"], value=st.session_state.polarity)
    st.session_state.depth = st.slider("Depth", 1, 5, st.session_state.depth)
    
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.evaluation = st.selectbox("Evaluation", ["ON", "OFF"], index=0 if st.session_state.evaluation == "ON" else 1)
        st.session_state.output_format = st.selectbox("Output", ["ESSAY", "OUTLINE", "BULLETS", "TABLE", "JSON"], index=["ESSAY", "OUTLINE", "BULLETS", "TABLE", "JSON"].index(st.session_state.output_format))
    with col2:
        st.session_state.compression = st.selectbox("Compression", ["OFF", "ON"], index=0 if st.session_state.compression == "OFF" else 1)
        st.session_state.action = st.selectbox("Action", ["OFF", "ON"], index=0 if st.session_state.action == "OFF" else 1)
    
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
            stance_options = ["Strong Support", "Support", "Neutral", "Challenge", "Strong Challenge"]
            current_stance = st.session_state.agent_stances.get(agent, "Neutral")
            if current_stance not in stance_options:
                current_stance = "Neutral"
            st.session_state.agent_stances[agent] = st.selectbox(
                "Stance", stance_options,
                index=stance_options.index(current_stance),
                key=f"stance_{agent}", label_visibility="collapsed"
            )
    
    st.markdown("---")
    st.markdown("### 📋 Context Injection")
    st.session_state.context_injection = st.text_area("Shared Context", value=st.session_state.context_injection, height=80, placeholder="Information all agents should know...")
    
    # === V32: TEMPERATURE RANGE ===
    st.markdown("---")
    st.markdown("### 🌡️ Temperature Range")
    
    per_agent = st.checkbox("Per-agent temperature", value=st.session_state.per_agent_temp, key="per_agent_temp_cb")
    st.session_state.per_agent_temp = per_agent
    
    if not per_agent:
        # Global temperature for all agents
        temp_options = TEMP_DISPLAY_ORDER
        current_temp = st.session_state.global_temp
        if current_temp not in temp_options:
            current_temp = "OFF"
        
        st.session_state.global_temp = st.selectbox(
            "All Agents",
            options=temp_options,
            index=temp_options.index(current_temp),
            key="global_temp_select"
        )
        
        # Show current header preview
        header = TEMPERATURE_HEADERS.get(st.session_state.global_temp, "")
        if header:
            st.caption(f"*{header[:80]}...*" if len(header) > 80 else f"*{header}*")
        else:
            st.caption("*No temperature header applied*")
    else:
        # Per-agent temperature
        for agent in ["Claude", "Sophia", "Grok", "Gemini"]:
            current = st.session_state.agent_temps.get(agent, "OFF")
            if current not in TEMP_DISPLAY_ORDER:
                current = "OFF"
            st.session_state.agent_temps[agent] = st.selectbox(
                f"{AGENT_EMOJIS[agent]} {agent}",
                options=TEMP_DISPLAY_ORDER,
                index=TEMP_DISPLAY_ORDER.index(current),
                key=f"temp_{agent}"
            )
    
    # Quick gradient buttons
    st.markdown("**Quick Set:**")
    qc1, qc2, qc3 = st.columns(3)
    with qc1:
        if st.button("🔥 AFF", use_container_width=True, key="quick_aff"):
            if per_agent:
                for i, agent in enumerate(["Claude", "Sophia", "Grok", "Gemini"]):
                    st.session_state.agent_temps[agent] = f"AFF_{min(i+2, 5)}"
            else:
                st.session_state.global_temp = "AFF_3"
            st.rerun()
    with qc2:
        if st.button("🧊 INT", use_container_width=True, key="quick_int"):
            if per_agent:
                for i, agent in enumerate(["Claude", "Sophia", "Grok", "Gemini"]):
                    st.session_state.agent_temps[agent] = f"INT_{min(i+2, 5)}"
            else:
                st.session_state.global_temp = "INT_3"
            st.rerun()
    with qc3:
        if st.button("⚡ ACT", use_container_width=True, key="quick_act"):
            if per_agent:
                for i, agent in enumerate(["Claude", "Sophia", "Grok", "Gemini"]):
                    st.session_state.agent_temps[agent] = f"ACT_{min(i+2, 5)}"
            else:
                st.session_state.global_temp = "ACT_3"
            st.rerun()

# =============================================================================
# MAIN CONTENT
# =============================================================================

st.markdown("""
<div class="main-header">
    <h1>🧬 Focus Group Lab V32</h1>
    <p>Multi-Agent AI Research Platform</p>
</div>
""", unsafe_allow_html=True)

# Show current role mode prominently
mode_emoji = {"assigned": "🎭", "raw": "🔬", "swapped": "🔄", "custom": "✏️"}.get(st.session_state.role_mode, "❓")
mode_name = {"assigned": "Assigned Roles", "raw": "Raw Voice", "swapped": "Swapped Roles", "custom": "Custom Roles"}.get(st.session_state.role_mode, "Unknown")

# V32: Temperature display
if st.session_state.per_agent_temp:
    temp_display = " · ".join([f"{AGENT_EMOJIS[a]} {st.session_state.agent_temps.get(a, 'OFF')}" for a in ["Claude", "Sophia", "Grok", "Gemini"]])
    temp_info = f"🌡️ Per-Agent: {temp_display}"
else:
    temp_info = f"🌡️ {st.session_state.global_temp}"

st.info(f"**Role:** {mode_emoji} {mode_name} | **Temp:** {temp_info}")

# Session Type Selection
session_type = st.radio("Session Type", ["Single Round", "Multi-Round", "Live Discussion"], horizontal=True)

if session_type == "Live Discussion":
    st.markdown("### 🎭 Live Discussion Mode")
    
    # Check if we're in Pull Aside mode
    if st.session_state.pull_aside_active:
        agent = st.session_state.pull_aside_agent
        emoji = AGENT_EMOJIS.get(agent, '🤖')
        
        st.markdown(f"""
        <div class="pull-aside-container">
            <div class="pull-aside-header">🔒 PULL ASIDE: Private conversation with {emoji} {agent}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Show pull-aside thread
        if st.session_state.pull_aside_thread:
            st.markdown('<div class="pull-aside-thread">', unsafe_allow_html=True)
            for entry in st.session_state.pull_aside_thread:
                speaker = entry.get('speaker', 'Unknown')
                if speaker == "Conductor":
                    st.markdown(f"**🎹 Conductor:** {entry['content']}")
                else:
                    st.markdown(f"**{emoji} {agent}:** {entry['content']}")
                st.markdown("---")
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Input for pull-aside
        aside_msg = st.text_input("Your message:", placeholder="Talk to the agent privately...", key="aside_input")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("💬 Send", type="primary", use_container_width=True) and aside_msg:
                st.session_state.pull_aside_thread.append({"speaker": "Conductor", "content": aside_msg})
                with st.spinner(f"{emoji} {agent} responding..."):
                    response = call_agent_pull_aside(agent, st.session_state.pull_aside_thread, st.session_state.discussion_topic)
                    st.session_state.pull_aside_thread.append({"speaker": agent, "content": response})
                st.rerun()
        with col2:
            if st.button("📝 Inject Summary & Return", use_container_width=True):
                # Optionally add a summary to main thread
                summary = st.session_state.get('aside_summary', '')
                if summary:
                    st.session_state.discussion_thread.append({
                        "agent": "Conductor", 
                        "content": f"[After private conversation with {agent}]: {summary}", 
                        "type": "intervention", 
                        "round": st.session_state.discussion_round
                    })
                st.session_state.pull_aside_active = False
                st.session_state.pull_aside_thread = []
                st.rerun()
        with col3:
            if st.button("🔙 Return (No Summary)", use_container_width=True):
                st.session_state.pull_aside_active = False
                st.session_state.pull_aside_thread = []
                st.rerun()
        
        aside_summary = st.text_input("Summary to inject (optional):", key="aside_summary", placeholder="Brief note about what was clarified...")
        
    else:
        # Normal Live Discussion mode
        
        # Topic input
        topic = st.text_area("Discussion Topic", value=st.session_state.discussion_topic, height=100, placeholder="What should the group discuss?")
        st.session_state.discussion_topic = topic
        
        # Resolution tracker
        st.markdown(f"""
        <div class="resolution-tracker">
            <strong>📊 Resolution Status:</strong> {st.session_state.consensus_status} | 
            <strong>Round:</strong> {st.session_state.discussion_round} |
            <strong>Locked:</strong> {'🔒 Yes' if st.session_state.discussion_locked else '🔓 No'}
        </div>
        """, unsafe_allow_html=True)
        
        # Discussion thread display with visual framing for directed responses
        if st.session_state.discussion_thread:
            st.markdown("### 💬 Discussion Thread")
            st.markdown('<div class="discussion-thread">', unsafe_allow_html=True)
            for entry in st.session_state.discussion_thread:
                agent = entry.get('agent', 'Unknown')
                emoji = AGENT_EMOJIS.get(agent, '🤖')
                entry_type = entry.get('type', 'response')
                
                if entry_type == "intervention":
                    st.markdown(f"<div class='conductor-box'><strong>{emoji} {agent}:</strong> {entry['content']}</div>", unsafe_allow_html=True)
                elif entry_type == "directed":
                    directed_from = entry.get('directed_from', '')
                    from_emoji = AGENT_EMOJIS.get(directed_from, '🤖')
                    st.markdown(f"""
                    <div class="directed-frame">
                        <span class="directed-header">🎯 DIRECT RESPONSE</span><br>
                        <strong>{emoji} {agent}</strong> responding to <strong>{from_emoji} {directed_from}</strong>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown(entry['content'])
                elif entry_type == "resolution":
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #4CAF50, #8BC34A); color: white; padding: 1rem; border-radius: 10px; margin: 0.5rem 0;">
                        <strong>📋 RESOLUTION (by {emoji} {agent}):</strong>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown(entry['content'])
                else:
                    box_class = f"{agent.lower()}-box" if agent != "Conductor" else "conductor-box"
                    st.markdown(f"<div class='agent-box {box_class}'><strong>{emoji} {agent}:</strong></div>", unsafe_allow_html=True)
                    st.markdown(entry['content'])
                st.markdown("---")
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Conductor toolkit
        st.markdown("""
        <div class="conductor-toolkit">
            <strong>🎹 Conductor Toolkit</strong>
        </div>
        """, unsafe_allow_html=True)
        
        # Row 1: Flow Control
        st.markdown("**Flow Control:**")
        col1, col2, col3 = st.columns([2, 3, 2])
        with col1:
            next_btn = st.button("▶️ Go", type="primary", use_container_width=True)
            next_speaker = st.selectbox("Next Speaker", ["Auto"] + st.session_state.active_agents, label_visibility="collapsed")
        with col2:
            # Fixed Direct labels - now reads naturally
            st.markdown("**Direct Response:**")
            dcol1, dcol2 = st.columns(2)
            with dcol1:
                direct_speaker = st.selectbox("Who speaks", st.session_state.active_agents, key="direct_speaker")
            with dcol2:
                direct_responding_to = st.selectbox("Responding to", [a for a in st.session_state.active_agents if a != direct_speaker], key="direct_responding_to")
            direct_btn = st.button(f"🎯 {direct_speaker} → {direct_responding_to}", use_container_width=True)
        with col3:
            intervention = st.text_input("Intervention", placeholder="Conductor says...", label_visibility="collapsed")
            intervene_btn = st.button("📢 Intervene", use_container_width=True)
        
        # Row 2: Pull Aside & Resolution
        st.markdown("**Agent Control & Resolution:**")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            pull_aside_agent = st.selectbox("Pull Aside", st.session_state.active_agents, key="pull_aside_select")
            if st.button(f"🔒 Pull {pull_aside_agent} Aside", use_container_width=True):
                st.session_state.pull_aside_active = True
                st.session_state.pull_aside_agent = pull_aside_agent
                st.session_state.pull_aside_thread = []
                st.rerun()
        with col2:
            vote_btn = st.button("🗳️ Call Vote", use_container_width=True)
            lock_btn = st.button("🔒 Lock Discussion", use_container_width=True)
        with col3:
            resolution_agent = st.selectbox("Resolver", ["Conductor"] + st.session_state.active_agents, key="resolution_agent")
            resolve_btn = st.button(f"✅ {resolution_agent} Resolves", use_container_width=True)
        with col4:
            if st.button("🗑️ Clear Discussion", use_container_width=True):
                st.session_state.discussion_thread = []
                st.session_state.discussion_round = 0
                st.session_state.consensus_status = "None"
                st.session_state.discussion_locked = False
                st.session_state.resolution_text = ""
                st.rerun()
        
        # Export
        if st.session_state.discussion_thread:
            st.download_button("📥 Export Discussion", export_to_markdown(), file_name=f"discussion_{st.session_state.session_id}.md", mime="text/markdown")
        
        # Handle actions
        if next_btn and topic and st.session_state.active_agents:
            st.session_state.discussion_round += 1
            if next_speaker == "Auto":
                speakers = [e.get('agent') for e in st.session_state.discussion_thread if e.get('type') not in ['intervention', 'resolution']]
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
            with st.spinner(f"🎯 {AGENT_EMOJIS[direct_speaker]} {direct_speaker} responding to {direct_responding_to}..."):
                response = call_agent_discussion(direct_speaker, st.session_state.discussion_topic, st.session_state.discussion_thread, directed_from=direct_responding_to)
                st.session_state.discussion_thread.append({"agent": direct_speaker, "content": response, "type": "directed", "directed_from": direct_responding_to, "round": st.session_state.discussion_round})
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
            st.session_state.resolution_agent = resolution_agent
            
            if resolution_agent == "Conductor":
                st.session_state.discussion_thread.append({"agent": "Conductor", "content": "✅ DISCUSSION RESOLVED.", "type": "intervention", "round": st.session_state.discussion_round})
            else:
                with st.spinner(f"📋 {AGENT_EMOJIS[resolution_agent]} {resolution_agent} writing resolution..."):
                    resolution = call_agent_resolution(resolution_agent, st.session_state.discussion_topic, st.session_state.discussion_thread)
                    st.session_state.resolution_text = resolution
                    st.session_state.discussion_thread.append({"agent": resolution_agent, "content": resolution, "type": "resolution", "round": st.session_state.discussion_round})
            st.rerun()

elif session_type == "Multi-Round":
    # Multi-Round Iterative Mode
    st.markdown("### 🔄 Multi-Round Iterative Mode")
    st.markdown("*Each round: all agents respond in parallel, seeing all previous rounds.*")
    
    # Current round number
    current_round = len(st.session_state.multi_round_history) + 1
    st.info(f"**Current Round:** {current_round}")
    
    # Prompt for this round
    prompt = st.text_area(f"Round {current_round} Prompt", height=100, placeholder="What should agents respond to this round?", key="multi_round_prompt")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        run_round_btn = st.button("▶️ Run Round", type="primary", use_container_width=True)
    with col2:
        clear_multi_btn = st.button("🗑️ Clear All Rounds", use_container_width=True)
    with col3:
        if st.button("📥 Export", use_container_width=True):
            st.download_button("Download MD", export_to_markdown(), file_name=f"multiround_{st.session_state.session_id}.md", mime="text/markdown")
    with col4:
        view_mode = st.selectbox("View", ["Grid", "Present"], label_visibility="collapsed", key="multi_view")
        st.session_state.view_mode = view_mode.lower()
    
    # Run the round
    if run_round_btn and prompt and st.session_state.active_agents:
        round_responses = {}
        with st.status(f"Running Round {current_round}...", expanded=True) as status:
            for agent in st.session_state.active_agents:
                stance = st.session_state.agent_stances.get(agent, "Neutral")
                status.update(label=f"{AGENT_EMOJIS[agent]} {agent} ({stance})...")
                response = call_agent_multi_round(agent, prompt, st.session_state.multi_round_history, current_round)
                round_responses[agent] = response
            status.update(label=f"✅ Round {current_round} Complete!", state="complete")
        
        # Store this round
        st.session_state.multi_round_history.append({
            "prompt": prompt,
            "responses": round_responses
        })
        st.rerun()
    
    if clear_multi_btn:
        st.session_state.multi_round_history = []
        st.rerun()
    
    # Display all rounds
    if st.session_state.multi_round_history:
        for i, round_data in enumerate(st.session_state.multi_round_history, 1):
            st.markdown(f'<div class="round-separator">📍 ROUND {i}</div>', unsafe_allow_html=True)
            st.markdown(f"**Prompt:** {round_data.get('prompt', 'N/A')}")
            
            if st.session_state.view_mode == "grid":
                render_agent_response_grid(round_data.get('responses', {}))
            else:
                render_present_mode(round_data.get('responses', {}))
            
            st.markdown("---")

else:
    # Single Round mode
    st.markdown("### 📝 Single Round")
    prompt = st.text_area("Your Prompt", height=120, placeholder="Ask your question here...")
    
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
                role_preview = get_agent_role(agent)[:30] + "..."
                status.update(label=f"{AGENT_EMOJIS[agent]} {agent} ({stance}) — {role_preview}")
                system = build_system_prompt(agent)
                user_msg = build_control_header() + "\n\n" + prompt
                response = AGENT_FUNCTIONS[agent](user_msg, system)
                st.session_state.round1_responses[agent] = response
            status.update(label="✅ Complete!", state="complete")
        st.rerun()
    
    if clear_btn:
        st.session_state.round1_responses = {}
        st.session_state.round2_responses = {}
        st.rerun()
    
    if st.session_state.round1_responses:
        st.markdown("### 📊 Responses")
        if st.session_state.view_mode == "grid":
            render_agent_response_grid(st.session_state.round1_responses)
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
st.markdown('<div style="text-align: center; color: #666; padding: 1rem;"><strong>Focus Group Lab V32</strong><br>Multi-Agent AI Research Platform<br>🎭 Assigned | 🔬 Raw Voice | 🔄 Swapped | ✏️ Custom | 🌡️ Temperature Range<br>📍 Single Round | 🔄 Multi-Round | 🎭 Live Discussion<br><em>SYNINT Team — February 2026</em></div>', unsafe_allow_html=True)
