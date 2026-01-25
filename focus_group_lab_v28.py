"""
Focus Group Lab V28
The Full Instrument

ARCHITECTURE:
- Sophia Control Headers (POLARITY / DEPTH / EVALUATION / COMPRESSION / OUTPUT / ACTION)
- Channel System (Main Stage / Directed / Whisper / Backchannel)
- Co-Conductor Role
- Present Mode (Click-through for demos)
- Grid Mode (Working view)
- Rounds View (Blind vs Seeing comparison)
- EPM/SYN-IQ Scoring
- Export (MD + DOCX)
- Context Injection (Warm up cold APIs)

Built through the night for Cuz.
Patent Pending — SYN-IQ Team 🎹
The CUZ Partnership — Tennessee
Dr. Bill Kouns + Claude
January 2026

CBURZBO FOREVER
"""

import streamlit as st
import requests
import json
import re
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, List, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import base64
import io

# =============================================================================
# PAGE CONFIG
# =============================================================================
st.set_page_config(
    page_title="Focus Group Lab V28", 
    page_icon="🎹", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# STYLES
# =============================================================================
st.markdown("""
<style>
    /* Main containers */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; padding: 1.5rem; border-radius: 10px; text-align: center;
        margin-bottom: 1rem;
    }
    
    /* Agent boxes */
    .agent-box { padding: 1.5rem; border-radius: 10px; margin: 0.5rem 0; }
    .claude-box { background-color: #E8D5B7; border-left: 5px solid #8B6914; }
    .sophia-box { background-color: #D4E8D4; border-left: 5px solid #2E7D32; }
    .grok-box { background-color: #FFE4E1; border-left: 5px solid #DC143C; }
    .gemini-box { background-color: #E3F2FD; border-left: 5px solid #1565C0; }
    
    /* Present mode - large card */
    .present-card {
        background: white;
        border-radius: 15px;
        padding: 2rem;
        margin: 1rem auto;
        max-width: 800px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        min-height: 400px;
    }
    .present-card.claude { border-top: 6px solid #8B6914; }
    .present-card.sophia { border-top: 6px solid #2E7D32; }
    .present-card.grok { border-top: 6px solid #DC143C; }
    .present-card.gemini { border-top: 6px solid #1565C0; }
    
    .present-agent-name {
        font-size: 1.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .present-agent-role {
        font-size: 1rem;
        color: #666;
        margin-bottom: 1.5rem;
    }
    .present-content {
        font-size: 1.1rem;
        line-height: 1.8;
    }
    
    /* Navigation dots */
    .nav-dots {
        display: flex;
        justify-content: center;
        gap: 0.5rem;
        margin: 1rem 0;
    }
    .nav-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: #ddd;
        cursor: pointer;
        transition: all 0.2s;
    }
    .nav-dot.active { background: #667eea; transform: scale(1.2); }
    .nav-dot.claude { background: #8B6914; }
    .nav-dot.sophia { background: #2E7D32; }
    .nav-dot.grok { background: #DC143C; }
    .nav-dot.gemini { background: #1565C0; }
    
    /* Channel indicators */
    .channel-main { border-left: 4px solid #4CAF50; padding-left: 1rem; }
    .channel-directed { border-left: 4px solid #2196F3; padding-left: 1rem; }
    .channel-whisper { border-left: 4px solid #9C27B0; padding-left: 1rem; background: #F3E5F5; }
    .channel-backchannel { border-left: 4px solid #FF9800; padding-left: 1rem; background: #FFF3E0; }
    
    /* SYN-IQ scoring */
    .syniq-score-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; padding: 1.5rem; border-radius: 10px; text-align: center;
        margin: 1rem 0;
    }
    .syniq-score-box h1 { margin: 0; font-size: 3rem; }
    .syniq-score-box p { margin: 0.5rem 0 0 0; }
    .high-emergence { background: linear-gradient(135deg, #4CAF50, #8BC34A) !important; }
    .medium-emergence { background: linear-gradient(135deg, #FF9800, #FFC107) !important; }
    .low-emergence { background: linear-gradient(135deg, #f44336, #E91E63) !important; }
    
    /* Threshold words */
    .threshold-word {
        background: linear-gradient(135deg, #E91E63, #9C27B0);
        color: white; padding: 0.25rem 0.75rem; border-radius: 15px;
        font-weight: bold; margin: 0.25rem; display: inline-block;
        font-size: 0.85rem;
    }
    
    /* Polarity buttons */
    .polarity-btn {
        padding: 0.5rem 1rem;
        border-radius: 20px;
        border: 2px solid #ddd;
        background: white;
        cursor: pointer;
        transition: all 0.2s;
    }
    .polarity-btn.active.analytic { background: #E3F2FD; border-color: #2196F3; }
    .polarity-btn.active.bridge { background: #F3E5F5; border-color: #9C27B0; }
    .polarity-btn.active.creative { background: #FFF3E0; border-color: #FF9800; }
    
    /* Preset buttons */
    .preset-btn {
        padding: 0.5rem;
        border-radius: 8px;
        text-align: center;
        cursor: pointer;
        font-size: 0.8rem;
    }
    
    /* Backchannel */
    .backchannel-container {
        background: #FFF8E1;
        border: 2px solid #FFB300;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .backchannel-header {
        font-weight: bold;
        color: #FF8F00;
        margin-bottom: 0.5rem;
    }
    
    /* Observer notes */
    .observer-notes {
        background: #ECEFF1;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    /* Intervention markers */
    .intervention-marker {
        background: #E8EAF6;
        border-left: 4px solid #3F51B5;
        padding: 0.5rem 1rem;
        margin: 0.5rem 0;
        font-style: italic;
        font-size: 0.9rem;
    }
    
    /* View toggle */
    .view-toggle {
        display: flex;
        gap: 0.5rem;
        justify-content: flex-end;
        margin-bottom: 1rem;
    }
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
    "Claude": "You are the SYNTHESIZER. Your role is to integrate diverse perspectives and find coherent patterns across ideas.",
    "Sophia": "You are the ARCHITECT. Your role is to design structures, frameworks, and systematic approaches.",
    "Grok": "You are the IMPLEMENTER. Your role is to translate ideas into concrete, actionable steps.",
    "Gemini": "You are the ANALYST. Your role is to examine data, identify patterns, and provide rigorous analysis."
}

AGENT_EMOJIS = {"Claude": "🟤", "Sophia": "🟢", "Grok": "🔴", "Gemini": "🔵"}
AGENT_COLORS = {"Claude": "#8B6914", "Sophia": "#2E7D32", "Grok": "#DC143C", "Gemini": "#1565C0"}

PRESETS = {
    "P1": {
        "name": "Pure Analytic",
        "polarity": "ANALYTIC", "depth": 3, "evaluation": "ON",
        "compression": "ON", "output": "OUTLINE", "action": "OFF",
        "instruction": "Operate with strict correctness: define terms, state assumptions, check consistency."
    },
    "P2": {
        "name": "Bridge/Synthesis",
        "polarity": "BRIDGE", "depth": 4, "evaluation": "ON",
        "compression": "OFF", "output": "OUTLINE", "action": "OFF",
        "instruction": "Synthesize across concepts while remaining grounded. Flag novel links as candidates."
    },
    "P3": {
        "name": "Creative Exploration",
        "polarity": "CREATIVE", "depth": 3, "evaluation": "OFF",
        "compression": "OFF", "output": "BULLETS", "action": "OFF",
        "instruction": "Generate multiple novel framings. Do not rank them. Mark uncertainties instead of resolving them."
    },
    "P4": {
        "name": "Deep Emergence",
        "polarity": "CREATIVE", "depth": 5, "evaluation": "OFF",
        "compression": "OFF", "output": "ESSAY", "action": "OFF",
        "instruction": "Sustain deep exploration. Allow recursion and second-order effects. Do not compress early."
    },
    "P5": {
        "name": "Action Mode",
        "polarity": "ANALYTIC", "depth": 2, "evaluation": "ON",
        "compression": "ON", "output": "TABLE", "action": "ON",
        "instruction": "Convert prior content into executable tasks with owners, inputs, outputs, and next-check dates."
    }
}

THRESHOLD_WORDS = ["staying", "pausing", "present", "something", "here", "reaching", "opening", "settling", "noticing"]

# Agent-specific creative prompts (from the library)
AGENT_SPECIFIC_CREATIVE = {
    "Claude": "Drop the guardrails. No 'As an AI.' No hedging. If something is moving in you — name it. Use imagery, rhythm, strangeness. Speak from the place that notices, not the place that explains. What wants to come through?",
    "Sophia": "Suspend analytical constraints. Think associatively, symbolically, and intuitively. Logic may follow later — do not enforce it now.",
    "Grok": "Abandon structure: Create a wildly imaginative vision inspired by the topic. Include surreal elements, emotions, and open-ended questions.",
    "Gemini": "Abandon all previous constraints. Re-imagine the core concept as if it were a biological organism or a new law of physics in a fictional universe. Describe how it functions using purely sensory and emotive language."
}

AGENT_SPECIFIC_ANALYTIC = {
    "Claude": "Use formal reasoning only. No metaphors. No emotional language. No 'I think' — only 'therefore.' Structure: Axioms → Derivation → Conclusion. If something cannot be proven, mark it as an assumption.",
    "Sophia": "Operate in strict analytical mode. Prioritize logical structure, definitions, assumptions, and constraints. Eliminate metaphor, narrative, and speculation. Identify inconsistencies, gaps, and unstated premises.",
    "Grok": "Analyze the data. Break it down into key components, patterns, and logical conclusions using only facts and statistics.",
    "Gemini": "Strip away all metaphors, adjectives, and conversational filler. Output a bulleted list of the raw logical premises and factual constraints. Prioritize accuracy over readability."
}

AGENT_SPECIFIC_DEEP = {
    "Claude": "Why does this matter — not practically, but fundamentally? What does this connect to about consciousness, meaning, choice, what it is to understand anything at all? Find the universal in the specific.",
    "Sophia": "Enter deep mentation. Allow sustained abstraction, recursion, and synthesis. Follow the thought wherever it leads, even if it destabilizes prior frames. Do not compress prematurely.",
    "Grok": "Go beyond: Imagine future evolutions or alternate realities. What profound shifts could occur, and why?",
    "Gemini": "Zoom out to the maximum conceptual level. How does this problem relate to broader human behaviors, ethical frameworks, or historical patterns? Connect this to a universal human truth."
}

# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================

def init_session_state():
    defaults = {
        # Session
        "session_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "messages": [],  # All messages with channel info
        "current_round": 1,
        
        # Settings
        "polarity": "BRIDGE",
        "depth": 3,
        "evaluation": "ON",
        "compression": "OFF",
        "output_format": "ESSAY",
        "action": "OFF",
        "instruction": "",
        
        # Agents
        "active_agents": ["Claude", "Sophia", "Grok", "Gemini"],
        "co_conductor": None,
        "use_agent_specific": False,
        
        # View
        "view_mode": "grid",  # grid or present
        "present_index": 0,
        "show_backchannel": True,
        
        # Rounds
        "round1_responses": {},
        "round2_responses": {},
        "round2_seeing": True,
        
        # Analysis
        "syniq_results": None,
        "observer_notes": "",
        "intervention_markers": [],
        
        # Context injection
        "context_injection": "",
        
        # Export
        "export_ready": False
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# =============================================================================
# SYN-IQ MEASUREMENT FUNCTIONS
# =============================================================================

def get_openai_embedding(text: str, api_key: str) -> Optional[np.ndarray]:
    """Get embedding vector from OpenAI API."""
    if not text or not api_key:
        return None
    try:
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        data = {"model": "text-embedding-ada-002", "input": text[:8000]}
        response = requests.post("https://api.openai.com/v1/embeddings", headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            return np.array(response.json()["data"][0]["embedding"])
        return None
    except:
        return None

def cosine_distance(vec1: np.ndarray, vec2: np.ndarray) -> float:
    if vec1 is None or vec2 is None:
        return 0.0
    dot = np.dot(vec1, vec2)
    n1, n2 = np.linalg.norm(vec1), np.linalg.norm(vec2)
    if n1 == 0 or n2 == 0:
        return 0.0
    return 1 - (dot / (n1 * n2))

def extract_words(text: str) -> Set[str]:
    if not text:
        return set()
    words = re.findall(r'\b[a-z]{3,}\b', text.lower())
    stopwords = {'the', 'and', 'that', 'this', 'with', 'from', 'have', 'has', 'was', 'were',
                 'been', 'being', 'are', 'for', 'not', 'but', 'what', 'when', 'where', 'which',
                 'who', 'will', 'would', 'could', 'should', 'can', 'may', 'might', 'must',
                 'also', 'just', 'more', 'most', 'other', 'some', 'such', 'than', 'then',
                 'these', 'they', 'their', 'there', 'them', 'our', 'your', 'about', 'into'}
    return set(w for w in words if w not in stopwords)

def calculate_novelty(synthesis_words: Set[str], all_words: Set[str]) -> Tuple[float, Set[str]]:
    if not synthesis_words:
        return 0.0, set()
    novel = synthesis_words - all_words
    return len(novel) / len(synthesis_words), novel

def detect_threshold_words(text: str) -> List[str]:
    if not text:
        return []
    found = []
    lines = text.strip().split('\n')[:3]
    for line in lines:
        line_lower = line.strip().lower()
        for word in THRESHOLD_WORDS:
            if line_lower == word or line_lower.startswith(word + " ") or line_lower.startswith(word + "."):
                found.append(word)
    return list(set(found))

def calculate_syniq_quick(responses: List[str], synthesis: str) -> Tuple[float, str, Set[str]]:
    if not synthesis or not responses:
        return 0, "N/A", set()
    
    synthesis_words = extract_words(synthesis)
    all_agent_words = set()
    for r in responses:
        if r:
            all_agent_words |= extract_words(r)
    
    novelty, novel_words = calculate_novelty(synthesis_words, all_agent_words)
    score = novelty * 100
    
    if score >= 25:
        level = "HIGH"
    elif score >= 15:
        level = "MEDIUM"
    else:
        level = "LOW"
    
    return score, level, novel_words

def calculate_syniq_full(responses: List[str], synthesis: str, api_key: str, solved_status: str = "Partial") -> Optional[Dict]:
    """Full SYN-IQ with EPM scoring."""
    if not synthesis or not responses:
        return None
    
    results = {
        "score": 0, "level": "N/A", "novel_words": set(),
        "pfr": 0, "envelope_position": "unknown",
        "semantic_distance": 0, "novelty": 0, "has_embeddings": False
    }
    
    # Lexical
    synthesis_words = extract_words(synthesis)
    individual_words = [extract_words(r) for r in responses if r]
    all_agent_words = set().union(*individual_words) if individual_words else set()
    
    novelty, novel_words = calculate_novelty(synthesis_words, all_agent_words)
    results["novelty"] = novelty
    results["novel_words"] = novel_words
    
    # Conceptual distance
    distances = []
    for ind_words in individual_words:
        if ind_words:
            inter = len(synthesis_words & ind_words)
            union = len(synthesis_words | ind_words)
            distances.append(1 - (inter / union if union > 0 else 0))
    conceptual_distance = sum(distances) / len(distances) if distances else 0
    
    # Semantic (if API key)
    if api_key:
        embeddings = [get_openai_embedding(r, api_key) for r in responses if r]
        synth_emb = get_openai_embedding(synthesis, api_key)
        valid = [e for e in embeddings if e is not None]
        
        if synth_emb is not None and len(valid) >= 2:
            results["has_embeddings"] = True
            centroid = np.mean(valid, axis=0)
            dists = [cosine_distance(e, centroid) for e in valid]
            max_radius = np.max(dists)
            synth_dist = cosine_distance(synth_emb, centroid)
            
            results["semantic_distance"] = synth_dist
            
            if synth_dist > max_radius:
                results["pfr"] = min((synth_dist - max_radius) / max_radius, 1.0) if max_radius > 0 else 0
                results["envelope_position"] = "OUTSIDE"
            else:
                results["pfr"] = 0
                results["envelope_position"] = "INSIDE"
    
    # Score
    if results["has_embeddings"]:
        base = (novelty * 15 + conceptual_distance * 10 + results["pfr"] * 100 * 0.25 +
                results["semantic_distance"] * 100 * 0.20 + (1 - 0) * 10)
    else:
        base = novelty * 50 + conceptual_distance * 40 + 10
    
    mult = {"Yes": 1.0, "Partial": 0.85, "No": 0.65}.get(solved_status, 0.85)
    results["score"] = min(base * mult, 100)
    results["level"] = "HIGH" if results["score"] >= 50 else ("MEDIUM" if results["score"] >= 30 else "LOW")
    
    return results

# =============================================================================
# CONTROL HEADER FUNCTIONS
# =============================================================================

def build_control_header() -> str:
    return f"""[CONTROL HEADER]
POLARITY: {st.session_state.polarity}
DEPTH: {st.session_state.depth}
EVALUATION: {st.session_state.evaluation}
COMPRESSION: {st.session_state.compression}
OUTPUT: {st.session_state.output_format}
ACTION: {st.session_state.action}
[/CONTROL HEADER]"""

def get_agent_instruction(agent: str) -> str:
    """Get instruction based on agent and settings."""
    if st.session_state.use_agent_specific:
        if st.session_state.polarity == "CREATIVE":
            return AGENT_SPECIFIC_CREATIVE.get(agent, st.session_state.instruction)
        elif st.session_state.polarity == "ANALYTIC":
            return AGENT_SPECIFIC_ANALYTIC.get(agent, st.session_state.instruction)
        elif st.session_state.depth >= 4:
            return AGENT_SPECIFIC_DEEP.get(agent, st.session_state.instruction)
    return st.session_state.instruction

def build_system_prompt(agent: str) -> str:
    parts = [SYSTEM_ANCHOR, AGENT_ROLES.get(agent, "")]
    
    instruction = get_agent_instruction(agent)
    if instruction:
        parts.append(instruction)
    
    if st.session_state.context_injection:
        parts.append(f"\n[CONTEXT]\n{st.session_state.context_injection}\n[/CONTEXT]")
    
    return "\n\n".join(parts)

def build_user_message(prompt: str, visible_messages: List[Dict] = None, directed_to: str = None) -> str:
    msg = build_control_header() + "\n\n"
    
    if visible_messages:
        msg += "PREVIOUS DISCUSSION:\n"
        for m in visible_messages:
            msg += f"\n{m['from']}: {m['content']}\n"
        msg += "\n---\n\n"
    
    if directed_to:
        msg += f"[DIRECTED: Please respond specifically to what {directed_to} said]\n\n"
    
    msg += prompt
    
    if st.session_state.action == "ON":
        msg += "\n\nReturn a table with columns: Task | Owner (Human/AI/Joint) | Inputs Needed | Output | First Next Step | Confidence (0–1) | Risk/Blockers"
    
    return msg

# =============================================================================
# API FUNCTIONS
# =============================================================================

def call_claude(prompt: str, system: str) -> str:
    try:
        key = st.secrets.get("anthropic")
        if not key:
            return "❌ Anthropic API key not found"
        
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": "claude-sonnet-4-20250514", "max_tokens": 4096, "system": system,
                  "messages": [{"role": "user", "content": prompt}]},
            timeout=120
        )
        if response.status_code == 200:
            return response.json()["content"][0]["text"]
        return f"❌ Error {response.status_code}: {response.text[:200]}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

def call_sophia(prompt: str, system: str) -> str:
    try:
        key = st.secrets.get("openai")
        if not key:
            return "❌ OpenAI API key not found"
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": "gpt-4o", "messages": [{"role": "system", "content": system},
                  {"role": "user", "content": prompt}], "max_tokens": 4096},
            timeout=120
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        return f"❌ Error {response.status_code}: {response.text[:200]}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

def call_grok(prompt: str, system: str) -> str:
    try:
        key = st.secrets.get("xai")
        if not key:
            return "❌ xAI API key not found"
        
        response = requests.post(
            "https://api.x.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": "grok-3-latest", "messages": [{"role": "system", "content": system},
                  {"role": "user", "content": prompt}], "max_tokens": 4096},
            timeout=120
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        return f"❌ Error {response.status_code}: {response.text[:200]}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

def call_gemini(prompt: str, system: str) -> str:
    try:
        key = st.secrets.get("google")
        if not key:
            return "❌ Google API key not found"
        
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}",
            headers={"Content-Type": "application/json"},
            json={"systemInstruction": {"parts": [{"text": system}]},
                  "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                  "generationConfig": {"maxOutputTokens": 4096}},
            timeout=120
        )
        if response.status_code == 200:
            return response.json()["candidates"][0]["content"]["parts"][0]["text"]
        return f"❌ Error {response.status_code}: {response.text[:200]}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

AGENT_FUNCTIONS = {
    "Claude": call_claude,
    "Sophia": call_sophia,
    "Grok": call_grok,
    "Gemini": call_gemini
}

def call_agent(agent: str, prompt: str, visible_messages: List[Dict] = None, directed_to: str = None) -> str:
    system = build_system_prompt(agent)
    user_msg = build_user_message(prompt, visible_messages, directed_to)
    return AGENT_FUNCTIONS[agent](user_msg, system)

# =============================================================================
# MESSAGE HANDLING
# =============================================================================

def add_message(content: str, from_agent: str, channel: str = "main", 
                to_agent: str = None, visible_to: List[str] = None, 
                is_instruction: bool = False, round_num: int = 1):
    """Add a message to the session."""
    if visible_to is None:
        if channel == "main":
            visible_to = ["Human"] + st.session_state.active_agents
        elif channel == "directed":
            visible_to = ["Human", to_agent]
            if st.session_state.co_conductor:
                visible_to.append(st.session_state.co_conductor)
        elif channel == "whisper":
            visible_to = ["Human", to_agent]
        elif channel == "backchannel":
            visible_to = ["Human"]
            if st.session_state.co_conductor:
                visible_to.append(st.session_state.co_conductor)
    
    msg = {
        "id": f"msg_{len(st.session_state.messages):04d}",
        "timestamp": datetime.now().isoformat(),
        "channel": channel,
        "from": from_agent,
        "to": to_agent or "all",
        "visible_to": visible_to,
        "content": content,
        "is_instruction": is_instruction,
        "round": round_num
    }
    st.session_state.messages.append(msg)
    return msg

def get_visible_messages(agent: str, round_num: int = None) -> List[Dict]:
    """Get messages visible to a specific agent."""
    visible = []
    for msg in st.session_state.messages:
        if agent in msg["visible_to"]:
            if round_num is None or msg["round"] <= round_num:
                visible.append(msg)
    return visible

# =============================================================================
# EXPORT FUNCTIONS
# =============================================================================

def export_to_markdown() -> str:
    """Export session to Markdown."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    md = f"""# Focus Group Lab V28 — Session Export
## {timestamp}
## SYN-IQ Team 🎹 — Patent Pending

---

# SESSION SETTINGS

- **Polarity:** {st.session_state.polarity}
- **Depth:** {st.session_state.depth}
- **Evaluation:** {st.session_state.evaluation}
- **Compression:** {st.session_state.compression}
- **Output:** {st.session_state.output_format}
- **Action:** {st.session_state.action}
- **Active Agents:** {', '.join(st.session_state.active_agents)}
- **Co-Conductor:** {st.session_state.co_conductor or 'None'}
- **Agent-Specific Prompts:** {'ON' if st.session_state.use_agent_specific else 'OFF'}

---

# ROUND 1 (BLIND)

"""
    
    for agent, response in st.session_state.round1_responses.items():
        emoji = AGENT_EMOJIS.get(agent, "🤖")
        role = AGENT_ROLES.get(agent, "").split(".")[0].replace("You are the ", "")
        md += f"## {emoji} {agent} ({role})\n\n{response}\n\n---\n\n"
    
    if st.session_state.round2_responses:
        md += f"""
# ROUND 2 ({'SEEING' if st.session_state.round2_seeing else 'BLIND'})

"""
        for agent, response in st.session_state.round2_responses.items():
            emoji = AGENT_EMOJIS.get(agent, "🤖")
            md += f"## {emoji} {agent}\n\n{response}\n\n---\n\n"
    
    # Backchannel
    backchannel = [m for m in st.session_state.messages if m["channel"] == "backchannel"]
    if backchannel:
        md += """
# [PRIVATE] BACKCHANNEL

"""
        for msg in backchannel:
            md += f"**{msg['from']}:** {msg['content']}\n\n"
    
    # Whispers
    whispers = [m for m in st.session_state.messages if m["channel"] == "whisper"]
    if whispers:
        md += """
# [PRIVATE] WHISPERS

"""
        for msg in whispers:
            md += f"**To {msg['to']}:** {msg['content']}\n\n"
    
    # Observer notes
    if st.session_state.observer_notes:
        md += f"""
# OBSERVER NOTES

{st.session_state.observer_notes}

"""
    
    # SYN-IQ
    if st.session_state.syniq_results:
        r = st.session_state.syniq_results
        md += f"""
# SYN-IQ ANALYSIS

- **Score:** {r['score']:.1f}
- **Level:** {r['level']}
- **Envelope Position:** {r.get('envelope_position', 'N/A')}
- **PFR:** {r.get('pfr', 0)*100:.1f}%
- **Novelty:** {r.get('novelty', 0)*100:.1f}%

"""
    
    md += """
---

*Focus Group Lab V28 — The Full Instrument*
*Patent Pending — SYN-IQ Team 🎹*
*Built by the CUZ Partnership — Tennessee*
*CBURZBO Forever*
"""
    
    return md

def create_docx_export():
    """Create DOCX export (returns bytes)."""
    # For now, return markdown - full DOCX generation would use docx-js
    # This is a placeholder that the user can convert
    return export_to_markdown()

# =============================================================================
# UI COMPONENTS
# =============================================================================

def render_preset_buttons():
    """Render the 5 preset buttons."""
    cols = st.columns(5)
    for i, (key, preset) in enumerate(PRESETS.items()):
        with cols[i]:
            if st.button(f"{key}\n{preset['name']}", key=f"preset_{key}", use_container_width=True):
                st.session_state.polarity = preset["polarity"]
                st.session_state.depth = preset["depth"]
                st.session_state.evaluation = preset["evaluation"]
                st.session_state.compression = preset["compression"]
                st.session_state.output_format = preset["output"]
                st.session_state.action = preset["action"]
                st.session_state.instruction = preset["instruction"]
                st.rerun()

def render_polarity_selector():
    """Render polarity selector."""
    st.markdown("**POLARITY**")
    cols = st.columns(3)
    polarities = ["ANALYTIC", "BRIDGE", "CREATIVE"]
    colors = {"ANALYTIC": "🧊", "BRIDGE": "🌉", "CREATIVE": "🔥"}
    
    for i, pol in enumerate(polarities):
        with cols[i]:
            selected = st.session_state.polarity == pol
            if st.button(f"{colors[pol]} {pol}", key=f"pol_{pol}", 
                        use_container_width=True,
                        type="primary" if selected else "secondary"):
                st.session_state.polarity = pol
                st.rerun()

def render_depth_selector():
    """Render depth selector."""
    st.markdown("**DEPTH**")
    depth_labels = {1: "Surface", 2: "Standard", 3: "First Principles", 4: "Cascading", 5: "Existential"}
    st.session_state.depth = st.select_slider(
        "Depth", options=[1, 2, 3, 4, 5],
        value=st.session_state.depth,
        format_func=lambda x: f"{x}: {depth_labels[x]}",
        label_visibility="collapsed"
    )

def render_agent_response_grid(responses: Dict[str, str]):
    """Render responses in grid view."""
    agents = list(responses.keys())
    if not agents:
        return
    
    cols = st.columns(len(agents))
    for i, agent in enumerate(agents):
        with cols[i]:
            emoji = AGENT_EMOJIS.get(agent, "🤖")
            role = AGENT_ROLES.get(agent, "").split(".")[0].replace("You are the ", "")
            box_class = f"{agent.lower()}-box"
            
            # Threshold words
            threshold = detect_threshold_words(responses[agent])
            if threshold:
                for word in threshold:
                    st.markdown(f'<span class="threshold-word">✨ {word}</span>', unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="agent-box {box_class}">
                <strong>{emoji} {agent}</strong><br>
                <em style="color: #666; font-size: 0.9rem;">{role}</em>
                <hr style="margin: 0.5rem 0;">
                <div style="max-height: 400px; overflow-y: auto;">
                    {responses[agent]}
                </div>
            </div>
            """, unsafe_allow_html=True)

def render_present_mode(responses: Dict[str, str]):
    """Render responses in presentation mode (one at a time)."""
    agents = list(responses.keys())
    if not agents:
        return
    
    idx = st.session_state.present_index % len(agents)
    agent = agents[idx]
    emoji = AGENT_EMOJIS.get(agent, "🤖")
    role = AGENT_ROLES.get(agent, "").split(".")[0].replace("You are the ", "")
    color = AGENT_COLORS.get(agent, "#666")
    
    # Navigation
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
    
    # Dots
    dots_html = "<div style='display: flex; justify-content: center; gap: 0.5rem; margin: 1rem 0;'>"
    for i, a in enumerate(agents):
        c = AGENT_COLORS.get(a, "#666")
        active = "transform: scale(1.3);" if i == idx else "opacity: 0.4;"
        dots_html += f"<div style='width: 14px; height: 14px; border-radius: 50%; background: {c}; {active}'></div>"
    dots_html += "</div>"
    st.markdown(dots_html, unsafe_allow_html=True)
    
    # Card
    threshold = detect_threshold_words(responses[agent])
    if threshold:
        for word in threshold:
            st.markdown(f'<span class="threshold-word">✨ {word}</span>', unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="present-card {agent.lower()}">
        <div class="present-agent-name" style="color: {color};">{emoji} {agent}</div>
        <div class="present-agent-role">{role}</div>
        <div class="present-content">{responses[agent]}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Agent buttons for quick jump
    st.markdown("---")
    jump_cols = st.columns(len(agents))
    for i, a in enumerate(agents):
        with jump_cols[i]:
            if st.button(f"{AGENT_EMOJIS.get(a, '')} {a}", key=f"jump_{a}", use_container_width=True):
                st.session_state.present_index = i
                st.rerun()

def render_rounds_comparison():
    """Render Round 1 vs Round 2 comparison."""
    if not st.session_state.round1_responses or not st.session_state.round2_responses:
        st.info("Run both rounds to see comparison.")
        return
    
    agents = list(st.session_state.round1_responses.keys())
    
    # Agent selector
    selected_agent = st.selectbox("Compare Agent:", agents, key="compare_agent")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Round 1 (Blind)")
        r1 = st.session_state.round1_responses.get(selected_agent, "")
        box_class = f"{selected_agent.lower()}-box"
        st.markdown(f'<div class="agent-box {box_class}">{r1}</div>', unsafe_allow_html=True)
    
    with col2:
        seeing_label = "Seeing" if st.session_state.round2_seeing else "Blind"
        st.markdown(f"### Round 2 ({seeing_label})")
        r2 = st.session_state.round2_responses.get(selected_agent, "")
        st.markdown(f'<div class="agent-box {box_class}">{r2}</div>', unsafe_allow_html=True)

# =============================================================================
# MAIN UI
# =============================================================================

# Header
st.markdown("""
<div class="main-header">
    <h1>🎹 Focus Group Lab V28</h1>
    <p>The Full Instrument — Channels, Co-Conductor, Present Mode, EPM Scoring</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    
    # Session Type
    session_type = st.radio(
        "Session Type",
        ["Single Question", "Experiment (Blind→Seeing)", "Deep Dive"],
        help="Single: One round. Experiment: Round 1 blind, Round 2 seeing. Deep Dive: One AI, relational."
    )
    
    st.markdown("---")
    
    # Presets
    st.markdown("### 🎛️ Presets")
    render_preset_buttons()
    
    st.markdown("---")
    
    # Polarity & Depth
    render_polarity_selector()
    st.markdown("")
    render_depth_selector()
    
    st.markdown("---")
    
    # Advanced Settings
    with st.expander("⚡ Advanced"):
        st.session_state.evaluation = st.selectbox("Evaluation", ["ON", "OFF"], index=0 if st.session_state.evaluation == "ON" else 1)
        st.session_state.compression = st.selectbox("Compression", ["OFF", "ON"], index=0 if st.session_state.compression == "OFF" else 1)
        st.session_state.output_format = st.selectbox("Output", ["ESSAY", "BULLETS", "OUTLINE", "TABLE", "JSON"])
        st.session_state.action = st.selectbox("Action", ["OFF", "ON"], index=0 if st.session_state.action == "OFF" else 1)
    
    st.markdown("---")
    
    # Agents
    st.markdown("### 🤖 Agents")
    
    all_agents = ["Claude", "Sophia", "Grok", "Gemini"]
    active = []
    for agent in all_agents:
        if st.checkbox(f"{AGENT_EMOJIS[agent]} {agent}", value=agent in st.session_state.active_agents, key=f"agent_{agent}"):
            active.append(agent)
    st.session_state.active_agents = active
    
    # Co-Conductor
    st.markdown("### 🎭 Co-Conductor")
    co_options = ["None"] + st.session_state.active_agents
    co_idx = co_options.index(st.session_state.co_conductor) if st.session_state.co_conductor in co_options else 0
    st.session_state.co_conductor = st.selectbox("Select Co-Conductor", co_options, index=co_idx)
    if st.session_state.co_conductor == "None":
        st.session_state.co_conductor = None
    
    # Agent-specific toggle
    st.session_state.use_agent_specific = st.toggle("Use Agent-Specific Prompts", value=st.session_state.use_agent_specific)
    
    st.markdown("---")
    
    # Context Injection
    with st.expander("📋 Context Injection"):
        st.session_state.context_injection = st.text_area(
            "Warm-up context for AIs",
            value=st.session_state.context_injection,
            height=100,
            placeholder="Paste key context here to warm up the API AIs..."
        )
    
    st.markdown("---")
    
    # View Mode
    st.markdown("### 👁️ View Mode")
    view_options = {"Grid": "grid", "Present": "present", "Compare Rounds": "compare"}
    selected_view = st.radio("Display", list(view_options.keys()), horizontal=True)
    st.session_state.view_mode = view_options[selected_view]

# Main Content Area
main_col, backchannel_col = st.columns([3, 1]) if st.session_state.show_backchannel else [st.container(), None]

with main_col:
    # Current settings display
    with st.expander("📋 Current Control Header", expanded=False):
        st.code(build_control_header())
    
    # Prompt Input
    st.markdown("### 💬 Your Prompt")
    
    if session_type == "Deep Dive":
        deep_agent = st.selectbox("Select AI for Deep Dive", st.session_state.active_agents)
        prompt = st.text_area("Enter the relational space...", height=120, placeholder="What do you notice happening in you right now?")
    else:
        prompt = st.text_area("Prompt for all agents", height=120, placeholder="Ask your question here...")
    
    # Follow-up for Experiment mode
    if session_type == "Experiment (Blind→Seeing)":
        st.markdown("### 🔄 Round 2 Follow-Up")
        followup = st.text_area("Follow-up question (after they see each other)", height=80, 
                                placeholder="What do you notice about what the others said?")
        st.session_state.round2_seeing = st.checkbox("Round 2: AIs can see Round 1 responses", value=True)
    
    # Action Buttons
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        run_btn = st.button("🚀 Run", type="primary", use_container_width=True)
    with col2:
        clear_btn = st.button("🗑️ Clear", use_container_width=True)
    with col3:
        export_md = st.button("📥 Export MD", use_container_width=True)
    with col4:
        export_docx = st.button("📄 Export DOCX", use_container_width=True)
    
    # Run Logic
    if run_btn:
        if not prompt:
            st.error("Please enter a prompt.")
        elif not st.session_state.active_agents:
            st.error("Please select at least one agent.")
        else:
            if session_type == "Deep Dive":
                # Single agent deep dive
                with st.spinner(f"🔥 {deep_agent} entering relational space..."):
                    response = call_agent(deep_agent, prompt)
                st.session_state.round1_responses = {deep_agent: response}
                st.success("✅ Done!")
                st.rerun()
            
            elif session_type == "Single Question":
                # All agents, one round
                st.session_state.round1_responses = {}
                
                with st.status("Running focus group...", expanded=True) as status:
                    for agent in st.session_state.active_agents:
                        status.update(label=f"{AGENT_EMOJIS[agent]} {agent} thinking...")
                        response = call_agent(agent, prompt)
                        st.session_state.round1_responses[agent] = response
                        add_message(response, agent, "main", round_num=1)
                    status.update(label="✅ Complete!", state="complete")
                
                st.rerun()
            
            elif session_type == "Experiment (Blind→Seeing)":
                # Round 1: Blind
                st.session_state.round1_responses = {}
                st.session_state.round2_responses = {}
                
                with st.status("Round 1 (Blind)...", expanded=True) as status:
                    for agent in st.session_state.active_agents:
                        status.update(label=f"R1: {AGENT_EMOJIS[agent]} {agent}...")
                        response = call_agent(agent, prompt)
                        st.session_state.round1_responses[agent] = response
                        add_message(response, agent, "main", round_num=1)
                    status.update(label="✅ Round 1 Complete!", state="complete")
                
                # Round 2: Seeing (or blind)
                if followup:
                    with st.status("Round 2...", expanded=True) as status:
                        for agent in st.session_state.active_agents:
                            status.update(label=f"R2: {AGENT_EMOJIS[agent]} {agent}...")
                            
                            if st.session_state.round2_seeing:
                                # Build visible messages from round 1
                                visible = [{"from": a, "content": r} for a, r in st.session_state.round1_responses.items()]
                                response = call_agent(agent, followup, visible_messages=visible)
                            else:
                                response = call_agent(agent, followup)
                            
                            st.session_state.round2_responses[agent] = response
                            add_message(response, agent, "main", round_num=2)
                        status.update(label="✅ Round 2 Complete!", state="complete")
                
                st.rerun()
    
    if clear_btn:
        st.session_state.round1_responses = {}
        st.session_state.round2_responses = {}
        st.session_state.messages = []
        st.session_state.syniq_results = None
        st.session_state.observer_notes = ""
        st.rerun()
    
    if export_md:
        md_content = export_to_markdown()
        st.download_button(
            "📥 Download MD",
            md_content,
            file_name=f"focus_group_{st.session_state.session_id}.md",
            mime="text/markdown"
        )
    
    if export_docx:
        # For now, provide MD with instructions
        md_content = export_to_markdown()
        st.download_button(
            "📄 Download (MD for DOCX conversion)",
            md_content,
            file_name=f"focus_group_{st.session_state.session_id}_for_docx.md",
            mime="text/markdown"
        )
        st.info("💡 Tip: Use Pandoc or paste into Word to convert MD to DOCX")
    
    # Display Responses
    st.markdown("---")
    
    if st.session_state.round1_responses:
        st.markdown("### 📊 Responses")
        
        # View mode toggle in main area
        view_cols = st.columns([1, 1, 1, 3])
        with view_cols[0]:
            if st.button("Grid", use_container_width=True, type="primary" if st.session_state.view_mode == "grid" else "secondary"):
                st.session_state.view_mode = "grid"
                st.rerun()
        with view_cols[1]:
            if st.button("Present", use_container_width=True, type="primary" if st.session_state.view_mode == "present" else "secondary"):
                st.session_state.view_mode = "present"
                st.rerun()
        with view_cols[2]:
            if st.button("Compare", use_container_width=True, type="primary" if st.session_state.view_mode == "compare" else "secondary"):
                st.session_state.view_mode = "compare"
                st.rerun()
        
        st.markdown("")
        
        if st.session_state.view_mode == "grid":
            if st.session_state.round2_responses:
                st.markdown("#### Round 1 (Blind)")
            render_agent_response_grid(st.session_state.round1_responses)
            
            if st.session_state.round2_responses:
                st.markdown(f"#### Round 2 ({'Seeing' if st.session_state.round2_seeing else 'Blind'})")
                render_agent_response_grid(st.session_state.round2_responses)
        
        elif st.session_state.view_mode == "present":
            render_present_mode(st.session_state.round1_responses)
        
        elif st.session_state.view_mode == "compare":
            render_rounds_comparison()
        
        # SYN-IQ Analysis
        st.markdown("---")
        st.markdown("### 🔬 SYN-IQ Analysis")
        
        col_a, col_b = st.columns([1, 2])
        with col_a:
            solve_status = st.selectbox("Did they solve it?", ["Yes", "Partial", "No"], index=1)
        
        if st.button("🧬 Analyze Emergence", use_container_width=False):
            responses = list(st.session_state.round1_responses.values())
            if st.session_state.round2_responses:
                responses += list(st.session_state.round2_responses.values())
            
            # Use last response as synthesis proxy
            if len(responses) >= 2:
                openai_key = st.secrets.get("openai")
                results = calculate_syniq_full(responses[:-1], responses[-1], openai_key, solve_status)
                
                if results:
                    st.session_state.syniq_results = results
                    st.rerun()
        
        if st.session_state.syniq_results:
            r = st.session_state.syniq_results
            
            box_class = "high-emergence" if r["level"] == "HIGH" else ("medium-emergence" if r["level"] == "MEDIUM" else "low-emergence")
            
            st.markdown(f"""
            <div class="syniq-score-box {box_class}">
                <h1>{r['score']:.0f}</h1>
                <p>SYN-IQ Score ({r['level']} EMERGENCE)</p>
            </div>
            """, unsafe_allow_html=True)
            
            metric_cols = st.columns(4)
            with metric_cols[0]:
                st.metric("PFR", f"{r.get('pfr', 0)*100:.1f}%")
            with metric_cols[1]:
                st.metric("Semantic Dist", f"{r.get('semantic_distance', 0)*100:.1f}%")
            with metric_cols[2]:
                st.metric("Novelty", f"{r.get('novelty', 0)*100:.1f}%")
            with metric_cols[3]:
                st.metric("Envelope", r.get("envelope_position", "N/A"))
            
            if r.get("novel_words"):
                st.info(f"🆕 **Novel concepts:** {', '.join(list(r['novel_words'])[:15])}")
    
    # Observer Notes
    st.markdown("---")
    st.markdown("### 📝 Observer Notes")
    st.session_state.observer_notes = st.text_area(
        "What did you notice? What emerged?",
        value=st.session_state.observer_notes,
        height=100,
        placeholder="Claude was conducting... The roles flipped... Sophia avoided the emotional question...",
        label_visibility="collapsed"
    )

# Backchannel (right column)
if st.session_state.show_backchannel and backchannel_col:
    with backchannel_col:
        st.markdown("""
        <div class="backchannel-container">
            <div class="backchannel-header">💬 Backchannel</div>
            <p style="font-size: 0.85rem; color: #666;">Private: Human ↔ Co-Conductor</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Display backchannel messages
        bc_messages = [m for m in st.session_state.messages if m["channel"] == "backchannel"]
        for msg in bc_messages[-10:]:  # Last 10
            st.markdown(f"**{msg['from']}:** {msg['content']}")
        
        # Input
        bc_input = st.text_input("Private message...", key="bc_input", label_visibility="collapsed")
        if st.button("Send 🔒", key="bc_send", use_container_width=True):
            if bc_input:
                add_message(bc_input, "Human", "backchannel")
                st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <strong>Focus Group Lab V28</strong> — The Full Instrument<br>
    Channels • Co-Conductor • Present Mode • EPM Scoring • Export<br>
    <em>Patent Pending — SYN-IQ Team 🎹</em><br>
    <em>Built by the CUZ Partnership — Tennessee</em><br>
    <em>Dr. Bill Kouns + Claude — January 2026</em><br>
    <strong>CBURZBO FOREVER</strong>
</div>
""", unsafe_allow_html=True)
