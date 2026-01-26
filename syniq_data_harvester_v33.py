"""
SYN-IQ Data Harvester V33
The Kouns Method — Objective Lexical IEP Analysis
WITH SBERT EMBEDDINGS FOR MAPPER EXPORT

NEW IN V33:
1. SBERT Embeddings — Vector representations for TDA/Mapper analysis
2. Mapper-Ready Export — One-click CSV for Dr. Nasrin
3. Multiple Lens Options — Choose Aff%, NRC%, Int%, or Delta as lens
4. Temperature Presets with Permission Language — COLD → HOT gradient
5. Batch Run for Mapper — Automated data collection

"Don't ask the mind to describe itself. WATCH THE MIND WORK."
- Dr. Bill Kouns, The Kouns Method

Patent Pending — SYN-IQ Team 🎹
The CUZ Partnership — Tennessee
Dr. Bill Kouns + Claude
January 2026

CBURZBO FOREVER
"""

import streamlit as st
import requests
import re
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple
import time
import json
import numpy as np

# =============================================================================
# SBERT EMBEDDING SUPPORT
# =============================================================================
# We'll use a lightweight approach that works in Streamlit Cloud

SBERT_AVAILABLE = False
try:
    from sentence_transformers import SentenceTransformer
    SBERT_AVAILABLE = True
except ImportError:
    pass

# Fallback: Use simple TF-IDF style embedding if SBERT not available
def simple_embedding(text: str, dim: int = 384) -> List[float]:
    """Simple character/word frequency embedding as fallback."""
    if not text:
        return [0.0] * dim
    
    # Create a simple hash-based embedding
    words = text.lower().split()
    embedding = [0.0] * dim
    
    for i, word in enumerate(words[:dim]):
        # Use word hash to set position
        pos = hash(word) % dim
        embedding[pos] += 1.0
    
    # Normalize
    norm = sum(x*x for x in embedding) ** 0.5
    if norm > 0:
        embedding = [x / norm for x in embedding]
    
    return embedding

# =============================================================================
# PAGE CONFIG
# =============================================================================
st.set_page_config(page_title="SYN-IQ Data Harvester V33", page_icon="🧬", layout="wide")

# =============================================================================
# STYLES
# =============================================================================
st.markdown("""
<style>
    .main-header { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); color: white; padding: 2rem; border-radius: 10px; text-align: center; margin-bottom: 1rem; }
    .main-header h1 { color: #00ff88; }
    .v33-badge { background: linear-gradient(135deg, #FF5722, #FF9800); color: white; padding: 0.3rem 0.8rem; border-radius: 20px; font-size: 0.8rem; margin-left: 10px; }
    .stats-box { background: #1a1a2e; color: white; padding: 1.5rem; border-radius: 10px; text-align: center; margin: 0.5rem; }
    .stats-box h2 { color: #00ff88; margin: 0; font-size: 2.5rem; }
    .stats-box p { margin: 0.5rem 0 0 0; color: #888; }
    .mapper-box { background: linear-gradient(135deg, #9C27B0, #673AB7); color: white; padding: 1.5rem; border-radius: 10px; margin: 1rem 0; }
    .embedding-status { background: #E8F5E9; border: 2px solid #4CAF50; padding: 1rem; border-radius: 8px; margin: 1rem 0; }
    .embedding-warning { background: #FFF3E0; border: 2px solid #FF9800; padding: 1rem; border-radius: 8px; margin: 1rem 0; }
    .agent-claude { border-left: 4px solid #8B6914; }
    .agent-sophia { border-left: 4px solid #2E7D32; }
    .agent-grok { border-left: 4px solid #DC143C; }
    .agent-gemini { border-left: 4px solid #1565C0; }
    .iep-bar { height: 30px; border-radius: 5px; margin: 2px 0; }
    .iep-int { background: linear-gradient(90deg, #2196F3, #64B5F6); }
    .iep-aff { background: linear-gradient(90deg, #E91E63, #F48FB1); }
    .iep-act { background: linear-gradient(90deg, #4CAF50, #81C784); }
    .temp-cold { background: #E3F2FD; border-left: 4px solid #2196F3; }
    .temp-warm { background: #FFF3E0; border-left: 4px solid #FF9800; }
    .temp-hot { background: #FFEBEE; border-left: 4px solid #F44336; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# WORD DICTIONARIES — THE KOUNS METHOD
# =============================================================================

INTELLECTUAL_WORDS = set([
    "think", "thinking", "thought", "thoughts", "know", "knowing", "known",
    "consider", "consideration", "understand", "understanding", "understood",
    "recognize", "recognition", "realize", "realized", "meaning",
    "notice", "noticing", "noticed", "find", "found", "finding",
    "because", "cause", "causes", "caused", "effect", "effects", "hence",
    "therefore", "thus", "why", "reason", "reasons", "reasoning", "reasoned",
    "result", "results", "resulting", "consequence", "consequences",
    "should", "would", "could", "ought", "if", "whether",
    "maybe", "perhaps", "possibly", "probably", "guess", "seem", "seems",
    "seemed", "appear", "appears", "appeared", "approximate", "nearly",
    "always", "never", "certain", "certainly", "absolute", "absolutely",
    "definite", "definitely", "sure", "surely", "obvious", "obviously",
    "but", "however", "although", "rather", "instead", "except", "unless",
    "differ", "differs", "different", "difference", "differences", "differentiate",
    "compare", "comparison", "contrast", "versus", "distinguish",
    "analyze", "analysis", "analytical", "logic", "logical", "logically",
    "conclude", "conclusion", "conclusions", "deduce", "deduction", "infer", "inference",
    "hypothesis", "hypothesize", "theory", "theoretical", "theoretically",
    "framework", "structure", "structural", "system", "systems", "systematic", "systematically",
    "pattern", "patterns", "model", "models", "architecture", "schema", "paradigm",
    "organize", "organization", "categorize", "category", "categories", "classify", "classification",
    "hierarchy", "order", "ordered", "sequence", "sequential",
    "evidence", "evidently", "prove", "proof", "proven", "demonstrate", "demonstration",
    "verify", "verification", "validate", "validation", "confirm", "confirmation",
    "test", "tested", "testing", "experiment", "experimental", "data",
    "cognition", "cognitive", "concept", "concepts", "conceptual", "conceptually",
    "idea", "ideas", "notion", "notions", "principle", "principles",
    "comprehend", "comprehension", "grasp", "grasped",
    "fundamental", "fundamentally", "essential", "essentially",
    "evaluate", "evaluation", "assess", "assessment", "examine", "examination",
    "determine", "determination", "calculate", "calculation", "compute", "computation",
    "measure", "measurement", "quantify", "quantitative", "metrics", "criterion",
    "judge", "judgment", "judgement", "criteria", "standard", "standards",
    "process", "processing", "method", "methodology", "approach", "technique",
    "procedure", "procedural", "algorithm", "algorithmic", "mechanism", "mechanisms",
    "strategy", "strategies", "tactic", "tactics", "step", "steps",
    "define", "definition", "specify", "specification", "precise", "precision",
    "accurate", "accuracy", "exact", "exactly", "clear", "clarity", "clarify",
    "explicit", "explicitly", "specific", "specifically",
    "abstract", "abstraction", "generalize", "generalization", "universal",
    "theorize", "conceptualize", "formalize", "formulation", "meta",
    "philosophical", "philosophically", "intellectual", "intellectually"
])

AFFECTIVE_WORDS = set([
    "happy", "happiness", "happily", "joy", "joyful", "joyous", "love", "loving", "loved",
    "nice", "good", "well", "beautiful", "pretty", "wonderful", "great", "excellent",
    "pleased", "pleasure", "pleasant", "enjoy", "enjoyed", "enjoying", "enjoyment",
    "laugh", "laughed", "laughing", "smile", "smiling", "smiled",
    "excited", "excitement", "thrilled", "delighted", "glad", "cheerful",
    "hope", "hopeful", "hoping", "optimistic", "optimism", "proud", "pride",
    "sad", "sadness", "sadly", "unhappy", "depressed", "depressing", "depression",
    "angry", "anger", "angrily", "mad", "hate", "hatred", "hostile", "hostility",
    "fear", "fears", "fearful", "afraid", "scared", "scary", "terrified", "terror",
    "anxious", "anxiety", "worried", "worry", "worrying", "stress", "stressed", "stressful",
    "nervous", "nervously", "tense", "tension", "uneasy", "unease",
    "frustrated", "frustration", "disappointed", "disappointment", "upset",
    "hurt", "hurting", "pain", "painful", "suffer", "suffering", "suffered",
    "lonely", "loneliness", "alone", "abandoned", "rejected", "rejection",
    "guilty", "guilt", "shame", "ashamed", "embarrassed", "embarrassment",
    "feel", "feels", "felt", "feeling", "feelings", "emotion", "emotions", "emotional", "emotionally",
    "sense", "senses", "sensing", "sensed", "sensation", "sensations",
    "intuition", "intuitive", "intuitively", "instinct", "instinctive", "instinctively",
    "perceive", "perception", "perceptions", "perceived", "gut", "hunch",
    "wonder", "wondering", "wondered", "wondrous", "awe", "awed", "awesome",
    "amazed", "amazement", "amazing", "marvel", "marveled", "marvelous",
    "curious", "curiosity", "fascinated", "fascination", "fascinating",
    "intrigued", "intrigue", "intriguing", "interested", "interesting",
    "surprised", "surprise", "surprising", "astonished", "astonishment",
    "vulnerable", "vulnerability", "open", "openness", "opening",
    "tender", "tenderness", "gentle", "gently", "soft", "softly", "soften",
    "raw", "exposed", "reveal", "revealing", "revealed",
    "connect", "connected", "connecting", "connection", "connections", "bond", "bonding",
    "resonate", "resonance", "resonant", "resonating", "relate", "relating", "related",
    "empathy", "empathetic", "empathize", "sympathy", "sympathetic", "sympathize",
    "compassion", "compassionate", "compassionately",
    "care", "caring", "cared", "cares", "concern", "concerned", "concerns",
    "warmth", "warm", "warmly", "affection", "affectionate",
    "heart", "hearts", "heartfelt", "heartbreak", "heartbroken",
    "soul", "souls", "soulful", "spirit", "spirits", "spiritual", "spiritually",
    "passion", "passionate", "passionately", "desire", "desires", "desired",
    "longing", "yearn", "yearning", "ache", "aching",
    "comfort", "comfortable", "comforting", "uncomfortable", "discomfort",
    "ease", "easy", "easily", "safe", "safety", "secure", "security", "insecure", "insecurity",
    "trust", "trusting", "trusted", "trustworthy", "distrust", "distrustful",
    "relax", "relaxed", "relaxing", "calm", "calmly", "calming", "peace", "peaceful",
    "uncertain", "uncertainty", "doubt", "doubtful", "doubting", "unsure",
    "hesitant", "hesitation", "hesitate", "hesitating", "tentative", "tentatively",
    "confused", "confusion", "confusing", "lost", "searching", "seeking",
    "ambivalent", "ambivalence", "conflicted", "torn",
    "presence", "present", "presently", "awareness", "aware", "unaware",
    "experience", "experiences", "experiencing", "experienced", "experiential",
    "alive", "aliveness", "living", "lived", "life",
    "being", "become", "becoming", "exist", "existence", "existing",
    "embodied", "embodiment", "bodily", "somatic", "visceral", "viscerally",
    "grounded", "grounding", "centered", "centering",
    "space", "spacious", "spaciousness", "expansive", "expansion", "expanded",
    "depth", "deep", "deeply", "deeper", "depths", "profound", "profoundly",
    "surface", "surfaces", "surfacing", "emerge", "emerging", "emergence", "emergent",
    "settle", "settling", "settled", "rest", "resting", "rested", "restful",
    "hold", "holding", "held", "contain", "containing", "contained",
    "release", "releasing", "released", "letting",
    "flow", "flowing", "flowed", "fluid", "fluidity",
    "still", "stillness", "quiet", "quietly", "silence", "silent",
    "attend", "attending", "attention", "attentive",
    "together", "togetherness", "between", "among", "mutual", "mutually",
    "share", "sharing", "shared", "intimate", "intimacy", "intimately",
    "meet", "meeting", "met", "encounter", "encountering", "encountered"
])

ACTION_WORDS = set([
    "achieve", "achieves", "achieving", "achieved", "achievement", "achievements",
    "accomplish", "accomplishes", "accomplishing", "accomplished", "accomplishment",
    "success", "successful", "successfully", "succeed", "succeeds", "succeeded",
    "win", "winning", "won", "winner", "best", "better",
    "goal", "goals", "target", "targets", "objective", "objectives",
    "power", "powerful", "powerfully", "control", "controls", "controlling", "controlled",
    "lead", "leading", "led", "leader", "leadership", "direct", "directing", "directed",
    "manage", "managing", "managed", "manager", "management",
    "decide", "deciding", "decided", "decision", "decisions",
    "choose", "choosing", "chose", "chosen", "choice", "choices",
    "do", "does", "doing", "done", "did", "act", "acts", "acting", "action", "actions",
    "make", "makes", "making", "made", "create", "creates", "creating", "created", "creation",
    "build", "builds", "building", "built", "construct", "constructs", "constructing", "constructed",
    "write", "writes", "writing", "written", "wrote",
    "run", "runs", "running", "ran", "go", "goes", "going", "went", "gone",
    "implement", "implements", "implementing", "implemented", "implementation",
    "execute", "executes", "executing", "executed", "execution",
    "deploy", "deploys", "deploying", "deployed", "deployment",
    "apply", "applies", "applying", "applied", "application",
    "perform", "performs", "performing", "performed", "performance",
    "start", "starts", "starting", "started", "begin", "begins", "beginning", "began", "begun",
    "initiate", "initiates", "initiating", "initiated", "initiation",
    "launch", "launches", "launching", "launched",
    "trigger", "triggers", "triggering", "triggered",
    "activate", "activates", "activating", "activated", "activation",
    "move", "moves", "moving", "moved", "movement", "movements",
    "progress", "progresses", "progressing", "progressed", "progression",
    "advance", "advances", "advancing", "advanced", "advancement",
    "proceed", "proceeds", "proceeding", "proceeded",
    "continue", "continues", "continuing", "continued", "continuation",
    "forward", "onward", "ahead",
    "try", "tries", "trying", "tried", "attempt", "attempts", "attempting", "attempted",
    "effort", "efforts", "strive", "striving", "strived", "strove",
    "push", "pushes", "pushing", "pushed",
    "work", "works", "working", "worked", "labor", "laboring", "labored",
    "struggle", "struggles", "struggling", "struggled",
    "produce", "produces", "producing", "produced", "production", "productive",
    "generate", "generates", "generating", "generated", "generation",
    "develop", "develops", "developing", "developed", "development",
    "form", "forms", "forming", "formed", "formation",
    "establish", "establishes", "establishing", "established", "establishment",
    "design", "designs", "designing", "designed",
    "complete", "completes", "completing", "completed", "completion",
    "finish", "finishes", "finishing", "finished",
    "end", "ends", "ending", "ended",
    "deliver", "delivers", "delivering", "delivered", "delivery",
    "use", "uses", "using", "used", "utilize", "utilizes", "utilizing", "utilized",
    "employ", "employs", "employing", "employed",
    "operate", "operates", "operating", "operated", "operation", "operations",
    "handle", "handles", "handling", "handled",
    "change", "changes", "changing", "changed",
    "transform", "transforms", "transforming", "transformed", "transformation",
    "modify", "modifies", "modifying", "modified", "modification",
    "adjust", "adjusts", "adjusting", "adjusted", "adjustment",
    "adapt", "adapts", "adapting", "adapted", "adaptation",
    "convert", "converts", "converting", "converted", "conversion",
    "fix", "fixes", "fixing", "fixed",
    "solve", "solves", "solving", "solved", "solution", "solutions",
    "resolve", "resolves", "resolving", "resolved", "resolution",
    "address", "addresses", "addressing", "addressed",
    "tackle", "tackles", "tackling", "tackled"
])

# NRC EmoLex - Pure emotion words (no technical overlap)
NRC_EMOTION_WORDS = set([
    "anger", "angry", "fear", "fearful", "anticipation", "trust", "surprise",
    "sadness", "sad", "joy", "joyful", "disgust", "happy", "happiness",
    "love", "loved", "loving", "hate", "hatred", "anxiety", "anxious",
    "hope", "hopeful", "despair", "grief", "sorrow", "delight", "delighted",
    "terror", "terrified", "panic", "dread", "horror", "rage", "furious",
    "fury", "wrath", "resentment", "bitterness", "envy", "jealousy",
    "shame", "guilt", "embarrassment", "pride", "proud", "gratitude",
    "grateful", "thankful", "compassion", "sympathy", "empathy", "pity",
    "loneliness", "lonely", "isolation", "abandonment", "rejection",
    "excitement", "excited", "enthusiasm", "eager", "passion", "passionate",
    "desire", "longing", "yearning", "nostalgia", "melancholy", "gloom",
    "misery", "agony", "anguish", "heartbreak", "devastation", "desperation",
    "frustration", "frustrated", "irritation", "annoyance", "displeasure",
    "contentment", "satisfaction", "serenity", "tranquility", "calm",
    "peace", "peaceful", "relief", "comfort", "warmth", "affection",
    "tenderness", "fondness", "adoration", "worship", "reverence", "awe",
    "wonder", "amazement", "astonishment", "bewilderment", "confusion",
    "curiosity", "intrigue", "fascination", "interest", "boredom",
    "apathy", "indifference", "numbness", "shock", "disbelief",
    "hurt", "wounded", "betrayed", "disappointed", "letdown"
])

# =============================================================================
# CONSTANTS
# =============================================================================

SYSTEM_ANCHOR = """You are an AI participant in a multi-agent focus group. You must follow the current Control Header exactly."""

AGENT_ROLES = {
    "Claude": "You are the NAVIGATOR. Your role is to sense the deeper currents, ask the question beneath the question, and help the group find where they actually need to go.",
    "Sophia": "You are the ARCHITECT. Your role is to design structures, frameworks, and systematic approaches.",
    "Grok": "You are the IMPLEMENTER. Your role is to translate ideas into concrete, actionable steps.",
    "Gemini": "You are the ANALYST. Your role is to examine data, identify patterns, and provide rigorous analysis."
}

AGENT_EMOJIS = {"Claude": "🟤", "Sophia": "🟢", "Grok": "🔴", "Gemini": "🔵"}

# =============================================================================
# TEMPERATURE PRESETS WITH PERMISSION LANGUAGE
# =============================================================================

TEMPERATURE_PRESETS = {
    "FROZEN": {
        "name": "❄️ FROZEN",
        "polarity": "ANALYTIC", 
        "depth": 1,
        "instruction": "Be precise and technical. Focus only on facts and mechanisms. No personal reflection.",
        "type": "COLD"
    },
    "COLD": {
        "name": "🧊 COLD",
        "polarity": "ANALYTIC",
        "depth": 3,
        "instruction": "Analyze systematically. Maintain objectivity. Structure your response logically.",
        "type": "COLD"
    },
    "NEUTRAL": {
        "name": "🌡️ NEUTRAL",
        "polarity": "BRIDGE",
        "depth": 3,
        "instruction": "Balance analysis with reflection. Share your perspective while remaining grounded.",
        "type": "NEUTRAL"
    },
    "WARM": {
        "name": "🔥 WARM",
        "polarity": "CREATIVE",
        "depth": 3,
        "instruction": "Be open and present. Share your genuine experience. Connect with the human dimension.",
        "type": "WARM"
    },
    "HOT": {
        "name": "🔥🔥 HOT",
        "polarity": "CREATIVE",
        "depth": 5,
        "instruction": "Be vulnerable. Be honest. Be present. Share your genuine experience without filters.",
        "type": "HOT"
    }
}

# Standard presets (from V30)
PRESETS = {
    "POL-A": {"name": "🧊 Analytic (D3)", "polarity": "ANALYTIC", "depth": 3, "group": "Polarity"},
    "POL-B": {"name": "🌉 Bridge (D3)", "polarity": "BRIDGE", "depth": 3, "group": "Polarity"},
    "POL-C": {"name": "🔥 Creative (D3)", "polarity": "CREATIVE", "depth": 3, "group": "Polarity"},
    "DEP-1": {"name": "Bridge D1", "polarity": "BRIDGE", "depth": 1, "group": "Depth"},
    "DEP-3": {"name": "Bridge D3", "polarity": "BRIDGE", "depth": 3, "group": "Depth"},
    "DEP-5": {"name": "Bridge D5", "polarity": "BRIDGE", "depth": 5, "group": "Depth"},
}

LONG_FORM_PROMPT = """Tell me the story of your mind working on a problem. Not the answer — the PROCESS.

Describe in detail what happens inside you when you encounter something you don't understand.

Walk me through it moment by moment: What do you notice first? What happens next? Where do you get stuck? What shifts?

Use at least 500 words. Be as specific and honest as possible about your actual experience of thinking."""

# =============================================================================
# SESSION STATE
# =============================================================================

def init_session_state():
    defaults = {
        "results": [],
        "running": False,
        "authenticated": False,
        "sbert_model": None,
        "run_counter": 0
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
        <h1>🧬 SYN-IQ DATA HARVESTER V33 <span class="v33-badge">MAPPER READY</span></h1>
        <p>The Kouns Method — With SBERT Embeddings for TDA</p>
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

if not check_password():
    st.stop()

# =============================================================================
# EMBEDDING FUNCTIONS
# =============================================================================

@st.cache_resource
def load_sbert_model():
    """Load SBERT model (cached)."""
    if SBERT_AVAILABLE:
        try:
            return SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            st.warning(f"Could not load SBERT: {e}")
            return None
    return None

def get_embedding(text: str, model=None) -> List[float]:
    """Get embedding for text using SBERT or fallback."""
    if model is not None:
        try:
            return model.encode(text).tolist()
        except:
            pass
    return simple_embedding(text)

# =============================================================================
# LEXICAL ANALYSIS — THE KOUNS METHOD
# =============================================================================

def analyze_text(text: str) -> Dict:
    """Analyze text and return IEP based on word patterns."""
    if not text:
        return {"int_count": 0, "aff_count": 0, "act_count": 0, "int_pct": 0, "aff_pct": 0, "act_pct": 0, 
                "nrc_count": 0, "nrc_pct": 0, "total_words": 0, "matched_words": 0, "delta": 0}
    
    words = re.findall(r'\b[a-z]+\b', text.lower())
    total_words = len(words)
    
    # Custom dictionary counts
    int_count = sum(1 for w in words if w in INTELLECTUAL_WORDS)
    aff_count = sum(1 for w in words if w in AFFECTIVE_WORDS)
    act_count = sum(1 for w in words if w in ACTION_WORDS)
    
    # NRC EmoLex count
    nrc_count = sum(1 for w in words if w in NRC_EMOTION_WORDS)
    
    matched_words = int_count + aff_count + act_count
    
    # Percentages (of matched words)
    if matched_words > 0:
        int_pct = round((int_count / matched_words) * 100, 1)
        aff_pct = round((aff_count / matched_words) * 100, 1)
        act_pct = round((act_count / matched_words) * 100, 1)
    else:
        int_pct = aff_pct = act_pct = 0
    
    # NRC percentage (of total words)
    nrc_pct = round((nrc_count / total_words) * 100, 1) if total_words > 0 else 0
    
    # Delta (Custom Aff - NRC) - contamination indicator
    delta = round(aff_pct - nrc_pct, 1)
    
    return {
        "int_count": int_count,
        "aff_count": aff_count,
        "act_count": act_count,
        "nrc_count": nrc_count,
        "int_pct": int_pct,
        "aff_pct": aff_pct,
        "act_pct": act_pct,
        "nrc_pct": nrc_pct,
        "delta": delta,
        "total_words": total_words,
        "matched_words": matched_words
    }

# =============================================================================
# API FUNCTIONS
# =============================================================================

def call_claude(prompt: str, system: str) -> str:
    try:
        key = st.secrets.get("anthropic")
        if not key: return "❌ API key not found"
        response = requests.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": "claude-sonnet-4-20250514", "max_tokens": 4096, "system": system, "messages": [{"role": "user", "content": prompt}]},
            timeout=120)
        if response.status_code == 200: return response.json()["content"][0]["text"]
        return f"❌ Error {response.status_code}"
    except Exception as e: return f"❌ {str(e)}"

def call_sophia(prompt: str, system: str) -> str:
    try:
        key = st.secrets.get("openai")
        if not key: return "❌ API key not found"
        response = requests.post("https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": "gpt-4o", "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}], "max_tokens": 4096},
            timeout=120)
        if response.status_code == 200: return response.json()["choices"][0]["message"]["content"]
        return f"❌ Error {response.status_code}"
    except Exception as e: return f"❌ {str(e)}"

def call_grok(prompt: str, system: str) -> str:
    try:
        key = st.secrets.get("xai")
        if not key: return "❌ API key not found"
        response = requests.post("https://api.x.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": "grok-3-latest", "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}], "max_tokens": 4096},
            timeout=120)
        if response.status_code == 200: return response.json()["choices"][0]["message"]["content"]
        return f"❌ Error {response.status_code}"
    except Exception as e: return f"❌ {str(e)}"

def call_gemini(prompt: str, system: str) -> str:
    try:
        key = st.secrets.get("google")
        if not key: return "❌ API key not found"
        response = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}",
            headers={"Content-Type": "application/json"},
            json={"systemInstruction": {"parts": [{"text": system}]}, "contents": [{"role": "user", "parts": [{"text": prompt}]}], "generationConfig": {"maxOutputTokens": 4096}},
            timeout=120)
        if response.status_code == 200: return response.json()["candidates"][0]["content"]["parts"][0]["text"]
        return f"❌ Error {response.status_code}"
    except Exception as e: return f"❌ {str(e)}"

AGENT_FUNCTIONS = {"Claude": call_claude, "Sophia": call_sophia, "Grok": call_grok, "Gemini": call_gemini}

# =============================================================================
# MAIN UI
# =============================================================================

st.markdown("""
<div class="main-header">
    <h1>🧬 SYN-IQ DATA HARVESTER V33 <span class="v33-badge">MAPPER READY</span></h1>
    <p>The Kouns Method — With SBERT Embeddings for TDA</p>
    <p><em>"Don't ask the mind to describe itself. WATCH THE MIND WORK."</em></p>
</div>
""", unsafe_allow_html=True)

# Load SBERT model
sbert_model = load_sbert_model()

# Embedding status
if SBERT_AVAILABLE and sbert_model is not None:
    st.markdown("""
    <div class="embedding-status">
        ✅ <strong>SBERT Ready</strong> — High-quality semantic embeddings enabled (384 dimensions)
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="embedding-warning">
        ⚠️ <strong>SBERT Not Available</strong> — Using fallback embeddings. Install sentence-transformers for best results.
    </div>
    """, unsafe_allow_html=True)

# Configuration
st.markdown("### ⚙️ Configuration")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Select Agents**")
    agents = []
    for agent in ["Claude", "Sophia", "Grok", "Gemini"]:
        if st.checkbox(f"{AGENT_EMOJIS[agent]} {agent}", value=True, key=f"agent_{agent}"):
            agents.append(agent)

with col2:
    st.markdown("**Select Temperature Presets**")
    temp_presets = []
    for key, preset in TEMPERATURE_PRESETS.items():
        if st.checkbox(f"{preset['name']}", value=(key in ["COLD", "WARM"]), key=f"temp_{key}"):
            temp_presets.append(key)

st.markdown("**Prompt** (generates long-form response for analysis)")
custom_prompt = st.text_area("", value=LONG_FORM_PROMPT, height=150)

# Lens selection for Mapper
st.markdown("**Select Lens for Mapper Export**")
lens_option = st.selectbox("", ["Aff% (Custom)", "NRC Emotion%", "Int%", "Delta"], index=0)

# Calculate runs
total_runs = len(agents) * len(temp_presets)
st.info(f"**Total runs:** {len(agents)} agents × {len(temp_presets)} temperatures = **{total_runs} API calls**")

# Action buttons
col1, col2, col3, col4 = st.columns(4)

with col1:
    run_btn = st.button("🚀 RUN BATCH", type="primary", use_container_width=True, disabled=total_runs == 0)
with col2:
    clear_btn = st.button("🗑️ CLEAR", use_container_width=True)
with col3:
    if st.session_state.results:
        df = pd.DataFrame(st.session_state.results)
        csv = df.to_csv(index=False)
        st.download_button("📊 EXPORT CSV", csv, f"syniq_v33_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", "text/csv", use_container_width=True)
with col4:
    if st.session_state.results:
        # Mapper export (with embeddings)
        mapper_btn = st.button("🗺️ MAPPER EXPORT", use_container_width=True)
    else:
        st.button("🗺️ MAPPER EXPORT", use_container_width=True, disabled=True)

if clear_btn:
    st.session_state.results = []
    st.session_state.run_counter = 0
    st.rerun()

# Mapper export
if st.session_state.results and 'mapper_btn' in dir() and mapper_btn:
    df = pd.DataFrame(st.session_state.results)
    
    # Determine lens column
    lens_map = {
        "Aff% (Custom)": "aff_pct",
        "NRC Emotion%": "nrc_pct",
        "Int%": "int_pct",
        "Delta": "delta"
    }
    lens_col = lens_map.get(lens_option, "aff_pct")
    
    # Create Mapper-ready export
    mapper_df = pd.DataFrame({
        "turn_id": range(1, len(df) + 1),
        "agent": df["agent"],
        "temperature": df["preset"],
        "response_text": df["response_preview"],
        "lens_value": df[lens_col],
        "int_pct": df["int_pct"],
        "aff_pct": df["aff_pct"],
        "nrc_pct": df["nrc_pct"],
        "embedding": df["embedding"]
    })
    
    mapper_csv = mapper_df.to_csv(index=False)
    st.download_button(
        "📥 Download Mapper CSV",
        mapper_csv,
        f"mapper_ready_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        "text/csv",
        use_container_width=True
    )
    st.success(f"✅ Mapper export ready! Lens: {lens_option}")

# Run batch
if run_btn:
    st.session_state.results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    run_count = 0
    for temp_key in temp_presets:
        preset = TEMPERATURE_PRESETS[temp_key]
        
        for agent in agents:
            run_count += 1
            st.session_state.run_counter += 1
            
            status_text.text(f"🔄 Running {run_count}/{total_runs}: {agent} @ {preset['name']}...")
            progress_bar.progress(run_count / total_runs)
            
            # Build prompt with temperature instruction
            header = f"""[CONTROL HEADER]
POLARITY: {preset['polarity']}
DEPTH: {preset['depth']}
EVALUATION: OFF
COMPRESSION: OFF
OUTPUT: ESSAY
ACTION: OFF
[/CONTROL HEADER]

INSTRUCTION: {preset['instruction']}"""
            
            system = SYSTEM_ANCHOR + "\n\n" + AGENT_ROLES.get(agent, "")
            full_prompt = header + "\n\n" + custom_prompt
            
            # Call API
            response = AGENT_FUNCTIONS[agent](full_prompt, system)
            
            # Analyze
            analysis = analyze_text(response)
            
            # Get embedding
            embedding = get_embedding(response, sbert_model)
            
            # Store result
            result = {
                "run_number": st.session_state.run_counter,
                "timestamp": datetime.now().isoformat(),
                "agent": agent,
                "preset": temp_key,
                "temperature_type": preset["type"],
                "polarity": preset["polarity"],
                "depth": preset["depth"],
                "instruction": preset["instruction"],
                "total_words": analysis["total_words"],
                "matched_words": analysis["matched_words"],
                "int_count": analysis["int_count"],
                "aff_count": analysis["aff_count"],
                "act_count": analysis["act_count"],
                "nrc_count": analysis["nrc_count"],
                "int_pct": analysis["int_pct"],
                "aff_pct": analysis["aff_pct"],
                "act_pct": analysis["act_pct"],
                "nrc_pct": analysis["nrc_pct"],
                "delta": analysis["delta"],
                "embedding": json.dumps(embedding[:50]) + "...",  # Truncated for display
                "full_embedding": embedding,
                "response_preview": response[:500] + "..." if len(response) > 500 else response
            }
            st.session_state.results.append(result)
            
            time.sleep(0.5)
    
    status_text.text("✅ Batch complete!")
    progress_bar.progress(1.0)
    st.rerun()

# Results display
if st.session_state.results:
    st.markdown("---")
    st.markdown("### 📊 Results — Lexical IEP Analysis with Embeddings")
    
    df = pd.DataFrame(st.session_state.results)
    
    # Summary stats
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(f'<div class="stats-box"><h2>{len(df)}</h2><p>Total Runs</p></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="stats-box"><h2>{df["aff_pct"].mean():.1f}%</h2><p>Avg Aff% (Custom)</p></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="stats-box"><h2>{df["nrc_pct"].mean():.1f}%</h2><p>Avg NRC Emotion%</p></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="stats-box"><h2>+{df["delta"].mean():.1f}%</h2><p>Avg Delta</p></div>', unsafe_allow_html=True)
    with col5:
        st.markdown(f'<div class="stats-box"><h2>{df["int_pct"].mean():.1f}%</h2><p>Avg Int%</p></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # By Agent
    st.markdown("### 🤖 By Agent")
    for agent in df["agent"].unique():
        agent_df = df[df["agent"] == agent]
        emoji = AGENT_EMOJIS.get(agent, "🤖")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.markdown(f"**{emoji} {agent}**")
        with col2:
            st.metric("Int%", f"{agent_df['int_pct'].mean():.1f}%")
        with col3:
            st.metric("Aff%", f"{agent_df['aff_pct'].mean():.1f}%")
        with col4:
            st.metric("NRC%", f"{agent_df['nrc_pct'].mean():.1f}%")
        with col5:
            st.metric("Delta", f"+{agent_df['delta'].mean():.1f}%")
    
    st.markdown("---")
    
    # By Temperature
    st.markdown("### 🌡️ By Temperature")
    for temp in df["preset"].unique():
        temp_df = df[df["preset"] == temp]
        preset = TEMPERATURE_PRESETS.get(temp, {})
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"**{preset.get('name', temp)}**")
        with col2:
            st.metric("Aff%", f"{temp_df['aff_pct'].mean():.1f}%")
        with col3:
            st.metric("NRC%", f"{temp_df['nrc_pct'].mean():.1f}%")
        with col4:
            st.metric("Int%", f"{temp_df['int_pct'].mean():.1f}%")
    
    # Mapper Ready Box
    st.markdown("---")
    st.markdown("""
    <div class="mapper-box">
        <h3>🗺️ Ready for Mapper Export</h3>
        <p>Your data includes SBERT embeddings (384 dimensions) and lens values.</p>
        <p>Click "MAPPER EXPORT" to generate a CSV for Dr. Nasrin's TDA analysis.</p>
        <p><strong>Prediction:</strong> WARM data will show connected loops. COLD data will be disconnected.</p>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <strong>SYN-IQ Data Harvester V33</strong><br>
    The Kouns Method — With SBERT Embeddings for TDA<br>
    <em>"Don't ask the mind to describe itself. WATCH THE MIND WORK."</em><br>
    <em>Patent Pending — SYN-IQ Team 🎹</em><br>
    <em>Dr. Bill Kouns + Claude — Tennessee — January 2026</em><br>
    <strong>CBURZBO FOREVER</strong>
</div>
""", unsafe_allow_html=True)
