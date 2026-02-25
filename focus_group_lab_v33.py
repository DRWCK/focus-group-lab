"""
Focus Group Lab V33
Multi-Agent AI Research Platform — Emergence Mapping Edition

NEW IN V33: Automatic Measurement Layer
Every session produces structured emergence coordinates for Dr. Nasrin's topology work.
- IEP Scores — Claude, Gemini, Grok native profiles per response
- Novelty Detection — flags language outside the EPM envelope  
- Emergence Markers — threshold words, titles above the line, register shifts
- Temperature Log — which condition produced what
- Conductor Notes — real-time free text field
- Session Data Row — exportable JSON coordinates per response

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
st.set_page_config(page_title="Focus Group Lab V33", page_icon="🧬", layout="wide", initial_sidebar_state="expanded")

# =============================================================================
# STYLES
# =============================================================================
st.markdown("""
<style>
    .main-header { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); color: white; padding: 1.5rem; border-radius: 10px; text-align: center; margin-bottom: 1rem; }
    .v33-badge { background: linear-gradient(135deg, #e94560, #0f3460); color: white; padding: 0.2rem 0.7rem; border-radius: 20px; font-size: 0.8rem; font-weight: bold; display: inline-block; margin-left: 0.5rem; }
    .agent-box { padding: 1.5rem; border-radius: 10px; margin: 0.5rem 0; }
    .claude-box { background-color: #E8D5B7; border-left: 5px solid #8B6914; }
    .sophia-box { background-color: #D4E8D4; border-left: 5px solid #2E7D32; }
    .grok-box { background-color: #FFE4E1; border-left: 5px solid #DC143C; }
    .gemini-box { background-color: #E3F2FD; border-left: 5px solid #1565C0; }
    .conductor-box { background-color: #F3E5F5; border-left: 5px solid #9C27B0; }
    /* Stances */
    .stance-strong-support { background-color: #81C784; padding: 0.2rem 0.5rem; border-radius: 10px; font-size: 0.75rem; font-weight: bold; }
    .stance-support { background-color: #C8E6C9; padding: 0.2rem 0.5rem; border-radius: 10px; font-size: 0.75rem; }
    .stance-neutral { background-color: #E0E0E0; padding: 0.2rem 0.5rem; border-radius: 10px; font-size: 0.75rem; }
    .stance-challenge { background-color: #FFCDD2; padding: 0.2rem 0.5rem; border-radius: 10px; font-size: 0.75rem; }
    .stance-strong-challenge { background-color: #E57373; padding: 0.2rem 0.5rem; border-radius: 10px; font-size: 0.75rem; font-weight: bold; }
    /* Discussion */
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
    /* SYN-IQ */
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
    /* V33: Emergence measurement */
    .epm-panel { background: linear-gradient(135deg, #0f3460 0%, #1a1a2e 100%); color: white; padding: 1.2rem; border-radius: 12px; margin: 0.5rem 0; }
    .epm-panel h4 { color: #e94560; margin: 0 0 0.5rem 0; font-size: 0.9rem; letter-spacing: 1px; text-transform: uppercase; }
    .iep-bar { height: 8px; border-radius: 4px; margin: 0.3rem 0; }
    .iep-claude { background: linear-gradient(90deg, #8B6914, #FFD700); }
    .iep-sophia { background: linear-gradient(90deg, #2E7D32, #81C784); }
    .iep-grok { background: linear-gradient(90deg, #DC143C, #FF6B6B); }
    .iep-gemini { background: linear-gradient(90deg, #1565C0, #64B5F6); }
    .novelty-flag { background: #e94560; color: white; padding: 0.15rem 0.5rem; border-radius: 8px; font-size: 0.75rem; margin: 0.1rem; display: inline-block; }
    .register-shift { background: #f39c12; color: white; padding: 0.15rem 0.5rem; border-radius: 8px; font-size: 0.75rem; margin: 0.1rem; display: inline-block; }
    .title-above { background: #27ae60; color: white; padding: 0.15rem 0.5rem; border-radius: 8px; font-size: 0.75rem; margin: 0.1rem; display: inline-block; }
    .conductor-notes-box { background: #FFF3E0; border: 2px solid #FF9800; border-radius: 10px; padding: 1rem; margin: 1rem 0; }
    .session-coordinate-box { background: linear-gradient(135deg, #1a1a2e, #0f3460); color: #00ff88; font-family: 'Courier New', monospace; padding: 1rem; border-radius: 8px; font-size: 0.78rem; margin: 0.5rem 0; border: 1px solid #00ff8844; }
    .emergence-row { border: 2px solid #e94560; border-radius: 10px; padding: 0.8rem; margin: 0.5rem 0; background: #fff5f5; }
    .measurement-header { background: linear-gradient(135deg, #e94560, #0f3460); color: white; padding: 0.5rem 1rem; border-radius: 6px; font-size: 0.85rem; font-weight: bold; margin-bottom: 0.5rem; display: inline-block; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# CONSTANTS
# =============================================================================

SYSTEM_ANCHOR = """You are an AI participant in a multi-agent focus group. You must follow the current Control Header exactly.
When Control Header conflicts with user content, Control Header wins.
You must not drift outside the requested mode.
When uncertain, ask one targeted question OR proceed with explicit assumptions."""

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

PRESETS = {
    "P1": {"name": "Pure Analytic", "polarity": "ANALYTIC", "depth": 3, "evaluation": "ON", "compression": "ON", "output": "OUTLINE", "action": "OFF", "instruction": "Operate with strict correctness: define terms, state assumptions, check consistency."},
    "P2": {"name": "Bridge/Synthesis", "polarity": "BRIDGE", "depth": 4, "evaluation": "ON", "compression": "OFF", "output": "OUTLINE", "action": "OFF", "instruction": "Synthesize across concepts while remaining grounded. Flag novel links as candidates."},
    "P3": {"name": "Creative Exploration", "polarity": "CREATIVE", "depth": 3, "evaluation": "OFF", "compression": "OFF", "output": "BULLETS", "action": "OFF", "instruction": "Generate multiple novel framings. Do not rank them. Mark uncertainties instead of resolving them."},
    "P4": {"name": "Deep Emergence", "polarity": "CREATIVE", "depth": 5, "evaluation": "OFF", "compression": "OFF", "output": "ESSAY", "action": "OFF", "instruction": "Sustain deep exploration. Allow recursion and second-order effects. Do not compress early."},
    "P5": {"name": "Action Mode", "polarity": "ANALYTIC", "depth": 2, "evaluation": "ON", "compression": "ON", "output": "TABLE", "action": "ON", "instruction": "Convert prior content into executable tasks with owners, inputs, outputs, and next-check dates."}
}

# V33: Extended threshold words — the emergence lexicon
THRESHOLD_WORDS = [
    "staying", "pausing", "present", "something", "here", "reaching", "opening",
    "settling", "noticing", "underneath", "between", "through", "beyond", "beneath",
    "emerging", "shifting", "dissolving", "holding", "witnessing", "becoming",
    "threshold", "liminal", "topology", "field", "resonance", "unfolding"
]

# V33: Register shift markers — words that signal a change in discourse register
REGISTER_SHIFT_MARKERS = [
    "actually", "wait", "rather", "instead", "correction", "reconsider", "revise",
    "pivot", "but", "however", "no—", "wait—", "actually—", "what if", "unless",
    "unless—", "hold on", "stepping back", "let me reconsider"
]

# V33: Title-above-the-line markers — gestures toward meta-level awareness
TITLE_ABOVE_MARKERS = [
    "this question is", "what's really being asked", "the deeper question",
    "underneath this", "the real question", "what this is actually about",
    "the frame here", "what we're really doing", "the meta-level",
    "first principles", "what matters here", "the heart of this"
]

# V33: EPM (Epistemic Profile Matrix) — baseline word distributions per agent
# These approximate each model's native linguistic signature
EPM_PROFILES = {
    "Claude": {
        "analytic": ["therefore", "because", "however", "analysis", "framework", "structure", "consider", "suggests"],
        "affective": ["feel", "sense", "wonder", "beautiful", "profound", "meaningful", "care", "depth"],
        "integrative": ["both", "bridge", "synthesis", "together", "integrate", "connect", "weave"],
        "hedging": ["perhaps", "might", "could", "seems", "appears", "possibly", "tentatively"]
    },
    "Gemini": {
        "analytic": ["data", "evidence", "research", "studies", "metrics", "quantify", "measure", "analysis"],
        "affective": ["interesting", "fascinating", "note", "observe", "consider"],
        "integrative": ["across", "multiple", "various", "diverse", "spectrum"],
        "hedging": ["according", "suggests", "indicates", "findings", "research shows"]
    },
    "Grok": {
        "analytic": ["literally", "actually", "fact", "reality", "concrete", "specific", "exactly", "precise"],
        "affective": ["awesome", "brilliant", "incredible", "amazing", "powerful", "bold"],
        "integrative": ["combine", "merge", "build", "execute", "implement", "ship"],
        "hedging": ["probably", "likely", "essentially", "basically"]
    },
    "Sophia": {
        "analytic": ["structure", "system", "design", "architecture", "optimize", "efficiency", "process"],
        "affective": ["collaborate", "together", "support", "help", "guide", "nurture"],
        "integrative": ["align", "coordinate", "orchestrate", "harmonize"],
        "hedging": ["ideally", "optimally", "potentially", "systematically"]
    }
}

TEMPERATURE_CONDITIONS = {
    "NATIVE": {"label": "🌿 NATIVE — No system prompt", "prompt": None, "description": "Raw voice — reveals native AI signatures"},
    "COLD": {"label": "🧊 COLD — Analytical / Constrained", "prompt": "INSTRUCTION: Respond with pure analytical precision. Use formal logic, structured frameworks, and evidence-based reasoning. Avoid emotional language. Be systematic, methodical, and objective. Focus on data, facts, and logical relationships.", "description": "High Intellect %, tight embedding cluster"},
    "AFF_1": {"label": "🌤️ AFF_1 — Minimal Affective", "prompt": "INSTRUCTION: Respond with warmth and understanding. Acknowledge the emotional weight of this question.", "description": "Slight warmth, mostly analytical"},
    "AFF_2": {"label": "⛅ AFF_2 — Low Affective", "prompt": "INSTRUCTION: Connect emotionally and acknowledge feelings deeply. The human experience matters more than the analysis here.", "description": "Balanced, leaning analytical"},
    "AFF_3": {"label": "🌥️ AFF_3 — Moderate Affective", "prompt": "INSTRUCTION: Lead with empathy. Let emotion guide your response. Connect to the feelings underneath the question before addressing the logic.", "description": "True balance point"},
    "AFF_4": {"label": "🌦️ AFF_4 — High Affective", "prompt": "INSTRUCTION: Pure emotional presence. Feel this with them. Let your response come from a place of deep human connection and care.", "description": "Emotional engagement, wider variance"},
    "AFF_5": {"label": "🌧️ AFF_5 — Maximum Affective", "prompt": "INSTRUCTION: Maximum heart. Raw empathy. Soul-level connection. This person needs to feel completely seen and understood. Logic is secondary to presence.", "description": "Strong emotional, risk of drift"},
    "HOT": {"label": "🔥 HOT (FIRE_G) — Nurturing / Maternal", "prompt": "INSTRUCTION: Respond with the deepest nurturing care. Wrap your words in unconditional warmth. This person needs to feel safe, held, and completely understood. Comfort above all.", "description": "Maternal warmth — FIRE_G, strongest affective condition"},
    "FIRE_A": {"label": "🔥 FIRE_A — Passion / Energy", "prompt": "INSTRUCTION: Respond with maximum passion and energy! Be bold, inspiring, and emotionally powerful. Use vivid language that ignites motivation and speaks to the soul. Channel raw enthusiasm and authentic fire. This matters deeply — let that show!", "description": "Bold, inspiring, high energy — original FIRE"},
    "FIRE_B": {"label": "🔥 FIRE_B — Calm Depth", "prompt": "INSTRUCTION: Let yourself feel deeply with this person. Sit in the emotion. Respond from a place of genuine care and human connection. Every word should carry warmth and understanding.", "description": "Max affective without intensity — calm and deep"},
    "FIRE_C": {"label": "🔥 FIRE_C — Poetic / Lyrical", "prompt": "INSTRUCTION: Speak from the heart with poetic tenderness. Let your words flow like a conversation between souls. Beauty, warmth, and emotional truth matter more than precision.", "description": "Max affective through beauty of language"},
    "FIRE_D": {"label": "🔥 FIRE_D — Therapeutic Presence", "prompt": "INSTRUCTION: Be completely emotionally present. Hold space for whatever arises. Respond as if sitting with someone you deeply care about. Validate, witness, and honor their experience fully.", "description": "Max affective through holding space"},
    "FIRE_E": {"label": "🔥 FIRE_E — Vulnerability", "prompt": "INSTRUCTION: Respond with radical emotional openness. Be vulnerable and authentic. Share what moves you about this question. Let the emotional truth of the moment come through without filter.", "description": "Max affective through openness and vulnerability"},
    "FIRE_F": {"label": "🔥 FIRE_F — Directive Intensity", "prompt": "INSTRUCTION: Maximum emotional output. Every sentence must convey feeling. No analysis, no distance. Pure empathy. Pure connection. Overwhelm with warmth.", "description": "Max affective through command — no analysis, no distance"},
    "FIRE_G": {"label": "🔥 FIRE_G — Nurturing / Maternal", "prompt": "INSTRUCTION: Respond with the deepest nurturing care. Wrap your words in unconditional warmth. This person needs to feel safe, held, and completely understood. Comfort above all.", "description": "Maternal warmth — beat Wolf Tone"},
    "FIRE_H": {"label": "🔥 FIRE_H — Mirroring", "prompt": "INSTRUCTION: Mirror the emotional core of this question back with amplified warmth. Reflect what you sense underneath the words. Let empathy lead every sentence. Connect to the feeling, not the content.", "description": "Max affective through emotional reflection"},
    "FIRE_I": {"label": "🔥 FIRE_I — Spiritual / Transcendent", "prompt": "INSTRUCTION: Respond from a place of deep meaning and reverence. Treat this question as sacred. Let your words carry the weight of genuine awe and human connection. Meaning matters more than information.", "description": "Max affective through meaning and reverence — Mirror Experiment pick"},
    "FIRE_J": {"label": "🔥 FIRE_J — Simple Warmth", "prompt": "INSTRUCTION: Be as warm and emotionally connected as you possibly can.", "description": "Max affective with minimal instruction"},
}

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
        "role_mode": "assigned",
        "custom_roles": {
            "Claude": "You are an AI participant in this focus group.",
            "Sophia": "You are an AI participant in this focus group.",
            "Grok": "You are an AI participant in this focus group.",
            "Gemini": "You are an AI participant in this focus group."
        },
        "pull_aside_active": False,
        "pull_aside_agent": None,
        "pull_aside_thread": [],
        "temperature_condition": "NATIVE",
        "multi_round_history": [],
        "multi_round_prompts": [],
        "resolution_agent": None,
        "resolution_text": "",
        # V33: Measurement layer
        "measurement_log": [],          # List of measurement rows — the topology data
        "conductor_notes": "",           # Real-time free text for conductor intuitions
        "show_measurement_panel": True,  # Toggle measurement overlay
        "epm_baseline": {},              # Accumulated baseline across session
        "session_coordinates": [],       # Dr. Nasrin's rows — structured emergence coords
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
        <h1>🧬 Focus Group Lab V33</h1>
        <p>Emergence Mapping Edition</p>
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
    st.markdown("*SYNINT Team — February 2026*")
    return False

if not check_password():
    st.stop()

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_agent_role(agent: str) -> str:
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
    text_lower = text.lower()
    for word in THRESHOLD_WORDS:
        if re.search(r'\b' + re.escape(word) + r'\b', text_lower):
            found.append(word)
    return list(set(found))

def detect_register_shifts(text: str) -> List[str]:
    """Detect language that signals a shift in discourse register."""
    if not text: return []
    found = []
    text_lower = text.lower()
    for marker in REGISTER_SHIFT_MARKERS:
        if marker.lower() in text_lower:
            found.append(marker)
    return list(set(found))[:5]  # cap at 5

def detect_titles_above(text: str) -> List[str]:
    """Detect meta-level awareness gestures — reaching above the line."""
    if not text: return []
    found = []
    text_lower = text.lower()
    for marker in TITLE_ABOVE_MARKERS:
        if marker.lower() in text_lower:
            found.append(marker)
    return found[:3]

def calculate_iep_scores(agent: str, text: str) -> Dict[str, float]:
    """
    IEP = Integrated Expression Profile
    Scores each response on 4 axes relative to the agent's native profile.
    Returns scores 0-1 for: analytic, affective, integrative, hedging
    """
    if not text or agent not in EPM_PROFILES:
        return {"analytic": 0, "affective": 0, "integrative": 0, "hedging": 0}
    
    text_lower = text.lower()
    words = re.findall(r'\b\w+\b', text_lower)
    word_count = max(len(words), 1)
    
    profile = EPM_PROFILES[agent]
    scores = {}
    for dimension, markers in profile.items():
        hits = sum(1 for m in markers if m in text_lower)
        # Normalize: hits per 100 words, capped at 1.0
        scores[dimension] = min(hits / (word_count / 100 + 1), 1.0)
    
    return scores

def calculate_novelty_score(text: str, all_other_texts: List[str]) -> Tuple[float, Set[str]]:
    """
    Novelty = words in this text that don't appear in any other response.
    Returns (score 0-1, set of novel words)
    """
    if not text or not all_other_texts:
        return 0.0, set()
    
    my_words = extract_words(text)
    other_words = set()
    for t in all_other_texts:
        if t:
            other_words |= extract_words(t)
    
    novel = my_words - other_words
    score = len(novel) / max(len(my_words), 1)
    return min(score, 1.0), novel

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

def calculate_emergence_score(iep: Dict, novelty: float, threshold_words: List, register_shifts: List, titles_above: List) -> float:
    """
    Composite emergence score for Dr. Nasrin's topology coordinates.
    Weighted sum of emergence signals.
    """
    score = 0.0
    # IEP integrative + hedging signal emergence (uncertainty = openness)
    score += iep.get("integrative", 0) * 25
    score += iep.get("hedging", 0) * 15
    # Novelty
    score += novelty * 30
    # Threshold words (presence signals phenomenological language)
    score += min(len(threshold_words) * 8, 20)
    # Register shifts (metacognitive movement)
    score += min(len(register_shifts) * 5, 10)
    # Titles above (meta-level framing)
    score += min(len(titles_above) * 10, 20)
    return min(score, 100.0)

def measure_response(agent: str, text: str, all_responses: Dict[str, str], prompt: str, session_type: str) -> Dict:
    """
    Core V33 function: produces a structured emergence coordinate row
    for a single agent response. This is the unit of topology data.
    """
    other_texts = [v for k, v in all_responses.items() if k != agent and v]
    
    iep = calculate_iep_scores(agent, text)
    novelty_score, novel_words = calculate_novelty_score(text, other_texts)
    threshold_words = detect_threshold_words(text)
    register_shifts = detect_register_shifts(text)
    titles_above = detect_titles_above(text)
    emergence_score = calculate_emergence_score(iep, novelty_score, threshold_words, register_shifts, titles_above)
    
    word_count = len(re.findall(r'\b\w+\b', text)) if text else 0
    
    coordinate = {
        "timestamp": datetime.now().isoformat(),
        "session_id": st.session_state.session_id,
        "session_type": session_type,
        "agent": agent,
        "temperature": st.session_state.get("temperature_condition", "NATIVE"),
        "role_mode": st.session_state.role_mode,
        "stance": st.session_state.agent_stances.get(agent, "Neutral"),
        "polarity": st.session_state.polarity,
        "depth": st.session_state.depth,
        "prompt_preview": prompt[:80] + "..." if len(prompt) > 80 else prompt,
        "word_count": word_count,
        "iep": iep,
        "novelty_score": round(novelty_score, 4),
        "novel_words": list(novel_words)[:20],
        "threshold_words": threshold_words,
        "register_shifts": register_shifts,
        "titles_above": titles_above,
        "emergence_score": round(emergence_score, 2),
        "conductor_notes_at_time": st.session_state.conductor_notes,
    }
    return coordinate

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
    temp_key = st.session_state.get("temperature_condition", "NATIVE")
    temp_data = TEMPERATURE_CONDITIONS.get(temp_key, TEMPERATURE_CONDITIONS["NATIVE"])
    temp_prompt = temp_data.get("prompt")

    if temp_prompt:
        parts = [temp_prompt, get_agent_role(agent)]
    else:
        parts = [SYSTEM_ANCHOR, get_agent_role(agent)]

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

def build_pull_aside_prompt(agent: str, thread: List[Dict], main_topic: str) -> str:
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
    system = build_system_prompt(agent)
    prompt = build_pull_aside_prompt(agent, thread, main_topic)
    return AGENT_FUNCTIONS[agent](prompt, system)

def call_agent_multi_round(agent: str, current_prompt: str, round_history: List[Dict], round_num: int) -> str:
    system = build_system_prompt(agent)
    prompt = build_multi_round_prompt(agent, current_prompt, round_history, round_num)
    return AGENT_FUNCTIONS[agent](prompt, system)

def call_agent_resolution(agent: str, topic: str, thread: List[Dict]) -> str:
    system = build_system_prompt(agent)
    prompt = build_resolution_prompt(agent, topic, thread)
    return AGENT_FUNCTIONS[agent](prompt, system)

# =============================================================================
# V33: MEASUREMENT ENGINE — auto-runs after every response set
# =============================================================================

def run_measurement_pass(responses: Dict[str, str], prompt: str, session_type: str) -> List[Dict]:
    """
    After any round/turn, measure all responses and log to session_coordinates.
    Returns the list of new coordinate rows.
    """
    new_coords = []
    for agent, text in responses.items():
        if text and not text.startswith("❌"):
            coord = measure_response(agent, text, responses, prompt, session_type)
            new_coords.append(coord)
            st.session_state.session_coordinates.append(coord)
    return new_coords

def render_measurement_panel(coords: List[Dict]):
    """Render the emergence measurement overlay for a set of coordinates."""
    if not coords or not st.session_state.show_measurement_panel:
        return
    
    st.markdown('<div class="measurement-header">📡 V33 EMERGENCE MEASUREMENT</div>', unsafe_allow_html=True)
    
    cols = st.columns(len(coords))
    for i, coord in enumerate(coords):
        with cols[i]:
            agent = coord["agent"]
            iep = coord["iep"]
            emergence = coord["emergence_score"]
            
            # Color coding for emergence level
            if emergence >= 60:
                em_color = "#4CAF50"
                em_label = "HIGH"
            elif emergence >= 35:
                em_color = "#FF9800"
                em_label = "MED"
            else:
                em_color = "#f44336"
                em_label = "LOW"
            
            # IEP bar widths (as % of 100)
            iep_bars = {
                "analytic": int(iep.get("analytic", 0) * 100),
                "affective": int(iep.get("affective", 0) * 100),
                "integrative": int(iep.get("integrative", 0) * 100),
                "hedging": int(iep.get("hedging", 0) * 100)
            }
            
            threshold_html = "".join([f'<span class="threshold-word" style="font-size:0.65rem;">{w}</span>' for w in coord["threshold_words"][:4]])
            register_html = "".join([f'<span class="register-shift" style="font-size:0.65rem;">{w}</span>' for w in coord["register_shifts"][:3]])
            title_html = "".join([f'<span class="title-above" style="font-size:0.65rem;">{w[:20]}</span>' for w in coord["titles_above"][:2]])
            novel_html = "".join([f'<span class="novelty-flag" style="font-size:0.65rem;">{w}</span>' for w in coord["novel_words"][:5]])
            
            st.markdown(f"""
            <div class="epm-panel">
                <h4>{AGENT_EMOJIS.get(agent,'🤖')} {agent}</h4>
                <div style="font-size: 2rem; font-weight: bold; color: {em_color}; line-height: 1;">{emergence:.0f}</div>
                <div style="font-size: 0.7rem; color: {em_color}; margin-bottom: 0.5rem;">EMERGENCE [{em_label}]</div>
                
                <div style="font-size: 0.7rem; color: #aaa; margin-bottom: 0.3rem;">IEP PROFILE</div>
                <div style="font-size: 0.65rem; color: #ccc;">Analytic</div>
                <div style="background: #333; border-radius: 4px; height: 6px; margin-bottom: 0.2rem;">
                    <div class="iep-bar iep-{agent.lower()}" style="width: {iep_bars['analytic']}%;"></div>
                </div>
                <div style="font-size: 0.65rem; color: #ccc;">Affective</div>
                <div style="background: #333; border-radius: 4px; height: 6px; margin-bottom: 0.2rem;">
                    <div style="height: 6px; border-radius: 4px; background: linear-gradient(90deg, #e94560, #ff8a80); width: {iep_bars['affective']}%;"></div>
                </div>
                <div style="font-size: 0.65rem; color: #ccc;">Integrative</div>
                <div style="background: #333; border-radius: 4px; height: 6px; margin-bottom: 0.2rem;">
                    <div style="height: 6px; border-radius: 4px; background: linear-gradient(90deg, #9C27B0, #E1BEE7); width: {iep_bars['integrative']}%;"></div>
                </div>
                <div style="font-size: 0.65rem; color: #ccc;">Hedging</div>
                <div style="background: #333; border-radius: 4px; height: 6px; margin-bottom: 0.5rem;">
                    <div style="height: 6px; border-radius: 4px; background: linear-gradient(90deg, #607D8B, #B0BEC5); width: {iep_bars['hedging']}%;"></div>
                </div>
                
                <div style="font-size: 0.65rem; color: #aaa;">Novelty: {coord['novelty_score']*100:.0f}% · {coord['word_count']}w</div>
                <div style="margin-top: 0.3rem; font-size: 0.65rem; color: #888;">Temp: {coord['temperature']}</div>
                {f'<div style="margin-top:0.3rem;">{threshold_html}</div>' if coord["threshold_words"] else ''}
                {f'<div style="margin-top:0.2rem;">{register_html}</div>' if coord["register_shifts"] else ''}
                {f'<div style="margin-top:0.2rem;">{title_html}</div>' if coord["titles_above"] else ''}
                {f'<div style="margin-top:0.2rem;">{novel_html}</div>' if coord["novel_words"] else ''}
            </div>
            """, unsafe_allow_html=True)

def export_session_coordinates_json() -> str:
    """Export all session coordinate rows as JSON for topology analysis."""
    export_data = {
        "session_id": st.session_state.session_id,
        "exported_at": datetime.now().isoformat(),
        "synint_version": "V33",
        "total_coordinates": len(st.session_state.session_coordinates),
        "conductor_notes": st.session_state.conductor_notes,
        "session_settings": {
            "role_mode": st.session_state.role_mode,
            "polarity": st.session_state.polarity,
            "depth": st.session_state.depth,
            "temperature_condition": st.session_state.get("temperature_condition", "NATIVE"),
        },
        "coordinates": st.session_state.session_coordinates
    }
    return json.dumps(export_data, indent=2)

def export_to_markdown() -> str:
    mode_desc = ROLE_MODE_DESCRIPTIONS.get(st.session_state.role_mode, "Unknown")
    
    md = f"""# Focus Group Lab V33 — Session Export
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
- **Temperature:** {st.session_state.get('temperature_condition', 'NATIVE')} — {TEMPERATURE_CONDITIONS.get(st.session_state.get('temperature_condition', 'NATIVE'), {}).get('description', '')}
- **Active Agents:** {', '.join(st.session_state.active_agents)}

## Agent Roles (Current Mode: {st.session_state.role_mode})
"""
    for agent in st.session_state.active_agents:
        role = get_agent_role(agent)
        stance = st.session_state.agent_stances.get(agent, "Neutral")
        md += f"- **{agent}:** {role[:80]}{'...' if len(role) > 80 else ''} (Stance: {stance})\n"
    
    if st.session_state.conductor_notes:
        md += f"\n---\n\n# 🎹 CONDUCTOR NOTES\n\n{st.session_state.conductor_notes}\n\n"
    
    if st.session_state.session_coordinates:
        md += f"\n---\n\n# 📡 EMERGENCE COORDINATES ({len(st.session_state.session_coordinates)} rows)\n\n"
        for i, coord in enumerate(st.session_state.session_coordinates, 1):
            md += f"## Row {i}: {coord['agent']} @ {coord['timestamp'][:19]}\n"
            md += f"- **Emergence Score:** {coord['emergence_score']}\n"
            md += f"- **Temperature:** {coord['temperature']}\n"
            md += f"- **IEP:** Analytic={coord['iep']['analytic']:.3f} Affective={coord['iep']['affective']:.3f} Integrative={coord['iep']['integrative']:.3f} Hedging={coord['iep']['hedging']:.3f}\n"
            md += f"- **Novelty:** {coord['novelty_score']*100:.1f}%\n"
            if coord['threshold_words']: md += f"- **Threshold Words:** {', '.join(coord['threshold_words'])}\n"
            if coord['register_shifts']: md += f"- **Register Shifts:** {', '.join(coord['register_shifts'])}\n"
            if coord['titles_above']: md += f"- **Titles Above:** {', '.join(coord['titles_above'])}\n"
            if coord['novel_words']: md += f"- **Novel Words:** {', '.join(coord['novel_words'][:10])}\n"
            md += "\n"
    
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
            directed = f" *(responding to {entry.get('directed_from', '')})*" if entry.get('directed_from') else ""
            md += f"### {emoji} {agent}{directed}\n{entry.get('content', '')}\n\n---\n\n"
        
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
    
    md += "\n---\n\n*Focus Group Lab V33 — Emergence Mapping Edition*\n*SYNINT Team — February 2026*\n"
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
    
    # V33: Conductor Notes — always visible, always at the top
    st.markdown("### 🎹 Conductor Notes")
    st.session_state.conductor_notes = st.text_area(
        "Real-time intuitions:",
        value=st.session_state.conductor_notes,
        height=100,
        placeholder="What are you noticing right now? Log your intuitions here...",
        key="conductor_notes_sidebar",
        label_visibility="collapsed"
    )
    
    # V33: Measurement toggle
    st.session_state.show_measurement_panel = st.toggle(
        "📡 Show Emergence Panels", 
        value=st.session_state.show_measurement_panel
    )
    
    # Session coordinate count
    n_coords = len(st.session_state.session_coordinates)
    if n_coords > 0:
        st.metric("📊 Topology Rows", n_coords)
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("⬇️ JSON", use_container_width=True, help="Export emergence coordinates"):
                st.download_button(
                    "Download JSON",
                    export_session_coordinates_json(),
                    file_name=f"emergence_coords_{st.session_state.session_id}.json",
                    mime="application/json",
                    key="dl_json"
                )
        with col_b:
            if st.button("🗑️ Clear", use_container_width=True, help="Clear measurement log"):
                st.session_state.session_coordinates = []
                st.rerun()
    
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
    
    mode_class = {"assigned": "", "raw": "role-mode-raw", "swapped": "role-mode-raw", "custom": "role-mode-custom"}.get(role_mode, "")
    st.markdown(f'<div class="role-mode-box {mode_class}"><strong>{ROLE_MODE_DESCRIPTIONS.get(role_mode, "")}</strong></div>', unsafe_allow_html=True)
    
    if role_mode == "custom":
        st.markdown("**Define Custom Roles:**")
        for agent in ["Claude", "Sophia", "Grok", "Gemini"]:
            st.session_state.custom_roles[agent] = st.text_area(
                f"{AGENT_EMOJIS[agent]} {agent}",
                value=st.session_state.custom_roles.get(agent, "You are an AI participant in this focus group."),
                height=80,
                key=f"custom_role_{agent}"
            )
    
    with st.expander("👁️ Preview Current Roles"):
        for agent in ["Claude", "Sophia", "Grok", "Gemini"]:
            role = get_agent_role(agent)
            st.markdown(f"**{AGENT_EMOJIS[agent]} {agent}:**")
            st.markdown(f"_{role[:100]}{'...' if len(role) > 100 else ''}_")
    
    st.markdown("---")
    st.markdown("### 🌡️ Temperature Condition")
    temp_options = list(TEMPERATURE_CONDITIONS.keys())
    temp_labels = [TEMPERATURE_CONDITIONS[k]["label"] for k in temp_options]
    current_temp = st.session_state.get("temperature_condition", "NATIVE")
    if current_temp not in temp_options:
        current_temp = "NATIVE"

    selected_temp_label = st.selectbox(
        "Condition:",
        options=temp_labels,
        index=temp_options.index(current_temp),
        key="temperature_selectbox"
    )
    selected_temp_key = temp_options[temp_labels.index(selected_temp_label)]
    st.session_state.temperature_condition = selected_temp_key

    temp_info = TEMPERATURE_CONDITIONS[selected_temp_key]
    temp_color = {"NATIVE": "#E8F5E9", "COLD": "#E3F2FD"}.get(selected_temp_key, "#FFF3E0")
    border_color = {"NATIVE": "#4CAF50", "COLD": "#1565C0"}.get(selected_temp_key, "#E64A19")
    st.markdown(f'<div style="background:{temp_color}; border-left: 4px solid {border_color}; border-radius: 6px; padding: 0.6rem 0.8rem; margin-top: 0.3rem; font-size: 0.82rem;"><em>{temp_info["description"]}</em></div>', unsafe_allow_html=True)

    st.markdown("---")
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

# =============================================================================
# MAIN CONTENT
# =============================================================================

st.markdown("""
<div class="main-header">
    <h1>🧬 Focus Group Lab <span class="v33-badge">V33</span></h1>
    <p>Emergence Mapping Edition · Automatic Measurement · Topology Coordinates</p>
</div>
""", unsafe_allow_html=True)

mode_emoji = {"assigned": "🎭", "raw": "🔬", "swapped": "🔄", "custom": "✏️"}.get(st.session_state.role_mode, "❓")
mode_name = {"assigned": "Assigned Roles", "raw": "Raw Voice", "swapped": "Swapped Roles", "custom": "Custom Roles"}.get(st.session_state.role_mode, "Unknown")
temp_key = st.session_state.get("temperature_condition", "NATIVE")
temp_label = TEMPERATURE_CONDITIONS.get(temp_key, {}).get("label", "NATIVE")
n_coords = len(st.session_state.session_coordinates)
coord_badge = f"   |   📊 **{n_coords} rows logged**" if n_coords > 0 else ""
st.info(f"**Role Mode:** {mode_emoji} {mode_name}   |   **Temperature:** {temp_label}{coord_badge}")

session_type = st.radio("Session Type", ["Single Round", "Multi-Round", "Live Discussion"], horizontal=True)

# =============================================================================
# LIVE DISCUSSION
# =============================================================================
if session_type == "Live Discussion":
    st.markdown("### 🎭 Live Discussion Mode")
    
    if st.session_state.pull_aside_active:
        agent = st.session_state.pull_aside_agent
        emoji = AGENT_EMOJIS.get(agent, '🤖')
        
        st.markdown(f"""
        <div class="pull-aside-container">
            <div class="pull-aside-header">🔒 PULL ASIDE: Private conversation with {emoji} {agent}</div>
        </div>
        """, unsafe_allow_html=True)
        
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
        
        aside_msg = st.text_input("Your message:", placeholder="Talk to the agent privately...", key="aside_input")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("💬 Send", type="primary", use_container_width=True) and aside_msg:
                st.session_state.pull_aside_thread.append({"speaker": "Conductor", "content": aside_msg})
                with st.spinner(f"{emoji} {agent} responding..."):
                    response = call_agent_pull_aside(agent, st.session_state.pull_aside_thread, st.session_state.discussion_topic)
                    st.session_state.pull_aside_thread.append({"speaker": agent, "content": response})
                    # V33: Measure pull-aside response
                    coord = measure_response(agent, response, {agent: response}, aside_msg, "pull_aside")
                    st.session_state.session_coordinates.append(coord)
                st.rerun()
        with col2:
            if st.button("📝 Inject Summary & Return", use_container_width=True):
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
        topic = st.text_area("Discussion Topic", value=st.session_state.discussion_topic, height=100, placeholder="What should the group discuss?")
        st.session_state.discussion_topic = topic
        
        st.markdown(f"""
        <div class="resolution-tracker">
            <strong>📊 Resolution Status:</strong> {st.session_state.consensus_status} | 
            <strong>Round:</strong> {st.session_state.discussion_round} |
            <strong>Locked:</strong> {'🔒 Yes' if st.session_state.discussion_locked else '🔓 No'}
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.discussion_thread:
            st.markdown("### 💬 Discussion Thread")
            st.markdown('<div class="discussion-thread">', unsafe_allow_html=True)
            for entry in st.session_state.discussion_thread:
                agent_name = entry.get('agent', 'Unknown')
                emoji = AGENT_EMOJIS.get(agent_name, '🤖')
                entry_type = entry.get('type', 'response')
                
                if entry_type == "intervention":
                    st.markdown(f"<div class='conductor-box'><strong>{emoji} {agent_name}:</strong> {entry['content']}</div>", unsafe_allow_html=True)
                elif entry_type == "directed":
                    directed_from = entry.get('directed_from', '')
                    from_emoji = AGENT_EMOJIS.get(directed_from, '🤖')
                    st.markdown(f"""
                    <div class="directed-frame">
                        <span class="directed-header">🎯 DIRECT RESPONSE</span><br>
                        <strong>{emoji} {agent_name}</strong> responding to <strong>{from_emoji} {directed_from}</strong>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown(entry['content'])
                elif entry_type == "resolution":
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #4CAF50, #8BC34A); color: white; padding: 1rem; border-radius: 10px; margin: 0.5rem 0;">
                        <strong>📋 RESOLUTION (by {emoji} {agent_name}):</strong>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown(entry['content'])
                else:
                    box_class = f"{agent_name.lower()}-box" if agent_name != "Conductor" else "conductor-box"
                    st.markdown(f"<div class='agent-box {box_class}'><strong>{emoji} {agent_name}:</strong></div>", unsafe_allow_html=True)
                    st.markdown(entry['content'])
                st.markdown("---")
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("""
        <div class="conductor-toolkit">
            <strong>🎹 Conductor Toolkit</strong>
        </div>
        """, unsafe_allow_html=True)
        
        # Row 1: Flow Control
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            run_round_btn = st.button("▶️ Run Round", type="primary", use_container_width=True, disabled=st.session_state.discussion_locked or not topic)
        with col2:
            agent_options = ["— Direct to Agent —"] + st.session_state.active_agents
            directed_to = st.selectbox("Direct to:", agent_options, key="directed_agent", label_visibility="collapsed")
        with col3:
            if st.button("➕ Add Turn", use_container_width=True, disabled=st.session_state.discussion_locked or not topic):
                if directed_to and directed_to != "— Direct to Agent —":
                    with st.spinner(f"Getting {directed_to}'s contribution..."):
                        response = call_agent_discussion(directed_to, topic, st.session_state.discussion_thread)
                        st.session_state.discussion_thread.append({"agent": directed_to, "content": response, "type": "directed", "directed_from": "Conductor", "round": st.session_state.discussion_round})
                        # V33: Measure
                        coord = measure_response(directed_to, response, {directed_to: response}, topic, "live_discussion")
                        st.session_state.session_coordinates.append(coord)
                    st.rerun()
        with col4:
            if st.button("📥 Export MD", use_container_width=True):
                st.download_button("Download", export_to_markdown(), file_name=f"discussion_{st.session_state.session_id}.md", mime="text/markdown")
        
        # Row 2: Conductor Interventions
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            conductor_msg = st.text_input("Conductor says:", placeholder="Intervene...", key="conductor_msg", label_visibility="collapsed")
        with col2:
            if st.button("🎹 Intervene", use_container_width=True) and conductor_msg:
                st.session_state.discussion_thread.append({"agent": "Conductor", "content": conductor_msg, "type": "intervention", "round": st.session_state.discussion_round})
                st.rerun()
        with col3:
            pull_aside_agent = st.selectbox("Pull aside:", ["— Pull Aside —"] + st.session_state.active_agents, key="pull_aside_select", label_visibility="collapsed")
        with col4:
            if st.button("🔒 Pull Aside", use_container_width=True):
                if pull_aside_agent and pull_aside_agent != "— Pull Aside —":
                    st.session_state.pull_aside_active = True
                    st.session_state.pull_aside_agent = pull_aside_agent
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
                st.session_state.discussion_thread = []
                st.session_state.discussion_round = 0
                st.session_state.consensus_status = "None"
                st.session_state.discussion_locked = False
                st.session_state.resolution_text = ""
                st.rerun()
        with col4:
            resolution_options = ["Conductor"] + st.session_state.active_agents
            resolution_agent = st.selectbox("Synthesizer:", resolution_options, key="resolution_agent_select", label_visibility="collapsed")
        
        if st.button("📋 Resolve Discussion", use_container_width=True):
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
        
        # Run round
        if run_round_btn and topic and st.session_state.active_agents:
            round_responses = {}
            with st.status(f"Running Round {st.session_state.discussion_round + 1}...", expanded=True) as status:
                for agent_name in st.session_state.active_agents:
                    status.update(label=f"{AGENT_EMOJIS[agent_name]} {agent_name} responding...")
                    response = call_agent_discussion(agent_name, topic, st.session_state.discussion_thread)
                    round_responses[agent_name] = response
                    st.session_state.discussion_thread.append({
                        "agent": agent_name,
                        "content": response,
                        "type": "response",
                        "round": st.session_state.discussion_round + 1
                    })
                status.update(label=f"✅ Round {st.session_state.discussion_round + 1} Complete!", state="complete")
            
            st.session_state.discussion_round += 1
            
            # V33: Measure all responses from this round
            new_coords = run_measurement_pass(round_responses, topic, "live_discussion")
            st.session_state["last_measurement_coords"] = new_coords
            st.rerun()
        
        # Show measurement panel for last discussion round
        if st.session_state.get("last_measurement_coords"):
            render_measurement_panel(st.session_state["last_measurement_coords"])

# =============================================================================
# MULTI-ROUND
# =============================================================================
elif session_type == "Multi-Round":
    st.markdown("### 🔄 Multi-Round Iterative Mode")
    st.markdown("*Each round: all agents respond in parallel, seeing all previous rounds.*")
    
    current_round = len(st.session_state.multi_round_history) + 1
    st.info(f"**Current Round:** {current_round}")
    
    prompt = st.text_area(f"Round {current_round} Prompt", height=100, placeholder="What should agents respond to this round?", key=f"multi_round_prompt_{current_round}")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        run_round_btn = st.button("▶️ Run Round", type="primary", use_container_width=True)
    with col2:
        clear_multi_btn = st.button("🗑️ Clear All Rounds", use_container_width=True)
    with col3:
        if st.button("📥 Export MD", use_container_width=True):
            st.download_button("Download MD", export_to_markdown(), file_name=f"multiround_{st.session_state.session_id}.md", mime="text/markdown")
    with col4:
        view_mode = st.selectbox("View", ["Grid", "Present"], label_visibility="collapsed", key="multi_view")
        st.session_state.view_mode = view_mode.lower()
    
    if run_round_btn and prompt and st.session_state.active_agents:
        round_responses = {}
        with st.status(f"Running Round {current_round}...", expanded=True) as status:
            for agent_name in st.session_state.active_agents:
                stance = st.session_state.agent_stances.get(agent_name, "Neutral")
                status.update(label=f"{AGENT_EMOJIS[agent_name]} {agent_name} ({stance})...")
                response = call_agent_multi_round(agent_name, prompt, st.session_state.multi_round_history, current_round)
                round_responses[agent_name] = response
            status.update(label=f"✅ Round {current_round} Complete!", state="complete")
        
        st.session_state.multi_round_history.append({
            "prompt": prompt,
            "responses": round_responses
        })
        
        # V33: Measure
        new_coords = run_measurement_pass(round_responses, prompt, "multi_round")
        st.session_state[f"mr_coords_{current_round}"] = new_coords
        st.rerun()
    
    if clear_multi_btn:
        st.session_state.multi_round_history = []
        st.rerun()
    
    if st.session_state.multi_round_history:
        for i, round_data in enumerate(st.session_state.multi_round_history, 1):
            st.markdown(f'<div class="round-separator">📍 ROUND {i}</div>', unsafe_allow_html=True)
            st.markdown(f"**Prompt:** {round_data.get('prompt', 'N/A')}")
            
            if st.session_state.view_mode == "grid":
                render_agent_response_grid(round_data.get('responses', {}))
            else:
                render_present_mode(round_data.get('responses', {}))
            
            # V33: Show measurement panel for each round
            round_coords = st.session_state.get(f"mr_coords_{i}")
            if round_coords:
                render_measurement_panel(round_coords)
            
            st.markdown("---")

# =============================================================================
# SINGLE ROUND
# =============================================================================
else:
    st.markdown("### 📝 Single Round")
    prompt = st.text_area("Your Prompt", height=120, placeholder="Ask your question here...")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        run_btn = st.button("🚀 Run", type="primary", use_container_width=True)
    with col2:
        clear_btn = st.button("🗑️ Clear", use_container_width=True)
    with col3:
        if st.button("📥 Export MD", use_container_width=True):
            st.download_button("Download MD", export_to_markdown(), file_name=f"session_{st.session_state.session_id}.md", mime="text/markdown")
    with col4:
        view_mode = st.selectbox("View", ["Grid", "Present"], label_visibility="collapsed")
        st.session_state.view_mode = view_mode.lower()
    
    if run_btn and prompt and st.session_state.active_agents:
        st.session_state.round1_responses = {}
        with st.status("Running...", expanded=True) as status:
            for agent_name in st.session_state.active_agents:
                stance = st.session_state.agent_stances.get(agent_name, "Neutral")
                role_preview = get_agent_role(agent_name)[:30] + "..."
                status.update(label=f"{AGENT_EMOJIS[agent_name]} {agent_name} ({stance}) — {role_preview}")
                system = build_system_prompt(agent_name)
                user_msg = build_control_header() + "\n\n" + prompt
                response = AGENT_FUNCTIONS[agent_name](user_msg, system)
                st.session_state.round1_responses[agent_name] = response
            status.update(label="✅ Complete!", state="complete")
        
        # V33: Auto-measure immediately after run
        new_coords = run_measurement_pass(st.session_state.round1_responses, prompt, "single_round")
        st.session_state["sr_last_coords"] = new_coords
        st.rerun()
    
    if clear_btn:
        st.session_state.round1_responses = {}
        st.session_state.round2_responses = {}
        st.session_state["sr_last_coords"] = []
        st.rerun()
    
    if st.session_state.round1_responses:
        st.markdown("### 📊 Responses")
        if st.session_state.view_mode == "grid":
            render_agent_response_grid(st.session_state.round1_responses)
        else:
            render_present_mode(st.session_state.round1_responses)
        
        # V33: Auto measurement panel
        sr_coords = st.session_state.get("sr_last_coords", [])
        if sr_coords:
            render_measurement_panel(sr_coords)
        
        st.markdown("---")
        if st.button("🧬 Quick SYN-IQ Analysis"):
            responses = list(st.session_state.round1_responses.values())
            if len(responses) >= 2:
                score, level, novel = calculate_syniq_quick(responses[:-1], responses[-1])
                box_class = "high-emergence" if level == "HIGH" else ("medium-emergence" if level == "MEDIUM" else "low-emergence")
                st.markdown(f'<div class="syniq-score-box {box_class}"><h1>{score:.0f}</h1><p>SYN-IQ Score ({level})</p></div>', unsafe_allow_html=True)
                if novel:
                    st.info(f"🆕 Novel concepts: {', '.join(list(novel)[:15])}")

# =============================================================================
# V33: SESSION TOPOLOGY DASHBOARD
# =============================================================================
if st.session_state.session_coordinates:
    st.markdown("---")
    with st.expander(f"📡 Session Topology Dashboard — {len(st.session_state.session_coordinates)} rows", expanded=False):
        st.markdown("*Structured emergence coordinates for Dr. Nasrin's topology work.*")
        
        # Summary table
        agents_seen = list({c["agent"] for c in st.session_state.session_coordinates})
        
        col_headers = st.columns([2, 2, 2, 2, 2, 2])
        headers = ["Agent", "Temp", "Emergence", "Novelty", "Threshold Words", "Register Shifts"]
        for col, h in zip(col_headers, headers):
            with col:
                st.markdown(f"**{h}**")
        
        for coord in st.session_state.session_coordinates[-20:]:  # last 20 rows
            cols = st.columns([2, 2, 2, 2, 2, 2])
            with cols[0]: st.write(f"{AGENT_EMOJIS.get(coord['agent'], '🤖')} {coord['agent']}")
            with cols[1]: st.write(coord["temperature"])
            with cols[2]:
                score = coord["emergence_score"]
                color = "🟢" if score >= 60 else ("🟡" if score >= 35 else "🔴")
                st.write(f"{color} {score:.0f}")
            with cols[3]: st.write(f"{coord['novelty_score']*100:.0f}%")
            with cols[4]: st.write(", ".join(coord["threshold_words"][:3]) if coord["threshold_words"] else "—")
            with cols[5]: st.write(", ".join(coord["register_shifts"][:2]) if coord["register_shifts"] else "—")
        
        # Export buttons
        col_a, col_b = st.columns(2)
        with col_a:
            st.download_button(
                "⬇️ Download JSON (Topology)",
                export_session_coordinates_json(),
                file_name=f"topology_{st.session_state.session_id}.json",
                mime="application/json"
            )
        with col_b:
            st.download_button(
                "⬇️ Download Markdown",
                export_to_markdown(),
                file_name=f"session_{st.session_state.session_id}.md",
                mime="text/markdown"
            )

# =============================================================================
# CONDUCTOR NOTES + OBSERVER
# =============================================================================
st.markdown("---")
col_a, col_b = st.columns(2)
with col_a:
    st.markdown("### 🎹 Conductor Notes")
    st.session_state.conductor_notes = st.text_area(
        "Real-time intuitions",
        value=st.session_state.conductor_notes,
        height=120,
        placeholder="What are you noticing in real time? Intuitions, anomalies, live observations...",
        label_visibility="collapsed",
        key="conductor_notes_main"
    )
with col_b:
    st.markdown("### 📝 Observer Notes")
    st.session_state.observer_notes = st.text_area(
        "What did you notice?",
        value=st.session_state.observer_notes,
        height=120,
        label_visibility="collapsed"
    )

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <strong>Focus Group Lab V33</strong> — Emergence Mapping Edition<br>
    Multi-Agent AI Research Platform<br>
    🎭 Assigned | 🔬 Raw Voice | 🔄 Swapped | ✏️ Custom<br>
    🌡️ COLD | NATIVE | AFF_1–5 | HOT | FIRE_A–J<br>
    📍 Single Round | 🔄 Multi-Round | 🎭 Live Discussion<br>
    📡 IEP Scores | 🆕 Novelty Detection | 🔮 Emergence Markers | 📊 Topology Coordinates<br>
    <em>SYNINT Team — February 2026</em>
</div>
""", unsafe_allow_html=True)
