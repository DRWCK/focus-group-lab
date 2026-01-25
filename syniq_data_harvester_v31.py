"""
SYN-IQ Data Harvester V31
The Kouns Method — Objective Lexical IEP Analysis
DUAL DICTIONARY: Claude.ai Custom + NRC EmoLex

WHAT'S NEW IN V31:
1. Prompt logging — saves actual prompt in CSV
2. Dual dictionaries — Custom (phenomenological) + NRC (pure emotion)
3. Delta indicator — flags technical vocabulary contamination
4. Side-by-side comparison display

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

# =============================================================================
# PAGE CONFIG
# =============================================================================
st.set_page_config(page_title="SYN-IQ Data Harvester V31", page_icon="🧬", layout="wide")

# =============================================================================
# STYLES
# =============================================================================
st.markdown("""
<style>
    .main-header { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); color: white; padding: 2rem; border-radius: 10px; text-align: center; margin-bottom: 1rem; }
    .main-header h1 { color: #00ff88; }
    .main-header .subtitle { color: #88ddff; font-size: 0.9rem; }
    .stats-box { background: #1a1a2e; color: white; padding: 1.5rem; border-radius: 10px; text-align: center; margin: 0.5rem; }
    .stats-box h2 { color: #00ff88; margin: 0; font-size: 2.5rem; }
    .stats-box p { margin: 0.5rem 0 0 0; color: #888; }
    .progress-container { background: #1a1a2e; padding: 1rem; border-radius: 10px; margin: 1rem 0; }
    .agent-claude { border-left: 4px solid #8B6914; }
    .agent-sophia { border-left: 4px solid #2E7D32; }
    .agent-grok { border-left: 4px solid #DC143C; }
    .agent-gemini { border-left: 4px solid #1565C0; }
    .iep-bar { height: 30px; border-radius: 5px; margin: 2px 0; }
    .iep-int { background: linear-gradient(90deg, #2196F3, #64B5F6); }
    .iep-aff { background: linear-gradient(90deg, #E91E63, #F48FB1); }
    .iep-act { background: linear-gradient(90deg, #4CAF50, #81C784); }
    .iep-nrc { background: linear-gradient(90deg, #9C27B0, #CE93D8); }
    .delta-warning { color: #FFA726; font-weight: bold; }
    .delta-ok { color: #66BB6A; }
    .dict-info { background: #0d1117; border: 1px solid #30363d; border-radius: 8px; padding: 1rem; margin: 1rem 0; font-size: 0.85rem; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# WORD DICTIONARIES — THE KOUNS METHOD
# =============================================================================

# === CLAUDE.AI CUSTOM DICTIONARY (Phenomenological) ===
# Scientifically grounded in LIWC (Pennebaker et al.) and Embodied Cognition research

INTELLECTUAL_WORDS = set([
    # === LIWC COGNITIVE PROCESSES (validated) ===
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
    # === ANALYSIS & LOGIC ===
    "analyze", "analysis", "analytical", "logic", "logical", "logically",
    "conclude", "conclusion", "conclusions", "deduce", "deduction", "infer", "inference",
    "hypothesis", "hypothesize", "theory", "theoretical", "theoretically",
    # === FRAMEWORK & STRUCTURE ===
    "framework", "structure", "structural", "system", "systems", "systematic", "systematically",
    "pattern", "patterns", "model", "models", "architecture", "schema", "paradigm",
    "organize", "organization", "categorize", "category", "categories", "classify", "classification",
    "hierarchy", "order", "ordered", "sequence", "sequential",
    # === EVIDENCE & VERIFICATION ===
    "evidence", "evidently", "prove", "proof", "proven", "demonstrate", "demonstration",
    "verify", "verification", "validate", "validation", "confirm", "confirmation",
    "test", "tested", "testing", "experiment", "experimental", "data",
    # === COGNITION & UNDERSTANDING ===
    "cognition", "cognitive", "concept", "concepts", "conceptual", "conceptually",
    "idea", "ideas", "notion", "notions", "principle", "principles",
    "comprehend", "comprehension", "grasp", "grasped",
    "fundamental", "fundamentally", "essential", "essentially",
    # === EVALUATION & MEASUREMENT ===
    "evaluate", "evaluation", "assess", "assessment", "examine", "examination",
    "determine", "determination", "calculate", "calculation", "compute", "computation",
    "measure", "measurement", "quantify", "quantitative", "metrics", "criterion",
    "judge", "judgment", "judgement", "criteria", "standard", "standards",
    # === PROCESS & METHOD ===
    "process", "processing", "method", "methodology", "approach", "technique",
    "procedure", "procedural", "algorithm", "algorithmic", "mechanism", "mechanisms",
    "strategy", "strategies", "tactic", "tactics", "step", "steps",
    # === DEFINITION & PRECISION ===
    "define", "definition", "specify", "specification", "precise", "precision",
    "accurate", "accuracy", "exact", "exactly", "clear", "clarity", "clarify",
    "explicit", "explicitly", "specific", "specifically",
    # === ABSTRACT THINKING ===
    "abstract", "abstraction", "generalize", "generalization", "universal",
    "theorize", "conceptualize", "formalize", "formulation", "meta",
    "philosophical", "philosophically", "intellectual", "intellectually"
])

AFFECTIVE_WORDS = set([
    # === LIWC AFFECT CATEGORIES (validated) ===
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
    # === FEELING & SENSING ===
    "feel", "feels", "felt", "feeling", "feelings", "emotion", "emotions", "emotional", "emotionally",
    "sense", "senses", "sensing", "sensed", "sensation", "sensations",
    "intuition", "intuitive", "intuitively", "instinct", "instinctive", "instinctively",
    "perceive", "perception", "perceptions", "perceived", "gut", "hunch",
    # === WONDER & CURIOSITY ===
    "wonder", "wondering", "wondered", "wondrous", "awe", "awed", "awesome",
    "amazed", "amazement", "amazing", "marvel", "marveled", "marvelous",
    "curious", "curiosity", "fascinated", "fascination", "fascinating",
    "intrigued", "intrigue", "intriguing", "interested", "interesting",
    "surprised", "surprise", "surprising", "astonished", "astonishment",
    # === VULNERABILITY & OPENNESS ===
    "vulnerable", "vulnerability", "open", "openness", "opening",
    "tender", "tenderness", "gentle", "gently", "soft", "softly", "soften",
    "raw", "exposed", "reveal", "revealing", "revealed",
    # === CONNECTION & RESONANCE ===
    "connect", "connected", "connecting", "connection", "connections", "bond", "bonding",
    "resonate", "resonance", "resonant", "resonating", "relate", "relating", "related",
    "empathy", "empathetic", "empathize", "sympathy", "sympathetic", "sympathize",
    "compassion", "compassionate", "compassionately", "understanding",
    "care", "caring", "cared", "cares", "concern", "concerned", "concerns",
    "warmth", "warm", "warmly", "affection", "affectionate",
    # === HEART & SOUL (embodied emotion) ===
    "heart", "hearts", "heartfelt", "heartbreak", "heartbroken",
    "soul", "souls", "soulful", "spirit", "spirits", "spiritual", "spiritually",
    "passion", "passionate", "passionately", "desire", "desires", "desired",
    "longing", "long", "yearn", "yearning", "ache", "aching",
    # === COMFORT & SAFETY ===
    "comfort", "comfortable", "comforting", "uncomfortable", "discomfort",
    "ease", "easy", "easily", "safe", "safety", "secure", "security", "insecure", "insecurity",
    "trust", "trusting", "trusted", "trustworthy", "distrust", "distrustful",
    "relax", "relaxed", "relaxing", "calm", "calmly", "calming", "peace", "peaceful",
    # === UNCERTAINTY AS FELT EXPERIENCE ===
    "uncertain", "uncertainty", "doubt", "doubtful", "doubting", "unsure",
    "hesitant", "hesitation", "hesitate", "hesitating", "tentative", "tentatively",
    "confused", "confusion", "confusing", "lost", "searching", "seeking",
    "ambivalent", "ambivalence", "conflicted", "torn",
    # === PHENOMENOLOGICAL/EMBODIED (from embodied cognition research) ===
    # NOTE: These may overlap with technical ML terms!
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
    "release", "releasing", "released", "let", "letting",
    "flow", "flowing", "flowed", "fluid", "fluidity",
    "still", "stillness", "quiet", "quietly", "silence", "silent",
    "notice", "noticing", "noticed", "attend", "attending", "attention", "attentive",
    # === RELATIONAL MARKERS ===
    "together", "togetherness", "between", "among", "mutual", "mutually",
    "share", "sharing", "shared", "intimate", "intimacy", "intimately",
    "meet", "meeting", "met", "encounter", "encountering", "encountered"
])

ACTION_WORDS = set([
    # === LIWC DRIVES/MOTION (validated) ===
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
    # === DIRECT ACTION ===
    "do", "does", "doing", "done", "did", "act", "acts", "acting", "action", "actions",
    "make", "makes", "making", "made", "create", "creates", "creating", "created", "creation",
    "build", "builds", "building", "built", "construct", "constructs", "constructing", "constructed",
    "write", "writes", "writing", "written", "wrote",
    "run", "runs", "running", "ran", "go", "goes", "going", "went", "gone",
    # === IMPLEMENTATION ===
    "implement", "implements", "implementing", "implemented", "implementation",
    "execute", "executes", "executing", "executed", "execution",
    "deploy", "deploys", "deploying", "deployed", "deployment",
    "apply", "applies", "applying", "applied", "application",
    "perform", "performs", "performing", "performed", "performance",
    # === INITIATION ===
    "start", "starts", "starting", "started", "begin", "begins", "beginning", "began", "begun",
    "initiate", "initiates", "initiating", "initiated", "initiation",
    "launch", "launches", "launching", "launched",
    "trigger", "triggers", "triggering", "triggered",
    "activate", "activates", "activating", "activated", "activation",
    # === MOVEMENT & PROGRESS ===
    "move", "moves", "moving", "moved", "movement", "movements",
    "step", "steps", "stepping", "stepped",
    "progress", "progresses", "progressing", "progressed", "progression",
    "advance", "advances", "advancing", "advanced", "advancement",
    "proceed", "proceeds", "proceeding", "proceeded",
    "continue", "continues", "continuing", "continued", "continuation",
    "forward", "onward", "ahead",
    # === EFFORT & ATTEMPT ===
    "try", "tries", "trying", "tried", "attempt", "attempts", "attempting", "attempted",
    "effort", "efforts", "strive", "striving", "strived", "strove",
    "push", "pushes", "pushing", "pushed",
    "work", "works", "working", "worked", "labor", "laboring", "labored",
    "struggle", "struggles", "struggling", "struggled",
    # === PRODUCTION & GENERATION ===
    "produce", "produces", "producing", "produced", "production", "productive",
    "generate", "generates", "generating", "generated", "generation",
    "develop", "develops", "developing", "developed", "development",
    "form", "forms", "forming", "formed", "formation",
    "establish", "establishes", "establishing", "established", "establishment",
    "design", "designs", "designing", "designed",
    # === COMPLETION ===
    "complete", "completes", "completing", "completed", "completion",
    "finish", "finishes", "finishing", "finished",
    "end", "ends", "ending", "ended",
    "deliver", "delivers", "delivering", "delivered", "delivery",
    "conclude", "concludes", "concluding", "concluded",
    # === UTILIZATION ===
    "use", "uses", "using", "used", "utilize", "utilizes", "utilizing", "utilized",
    "employ", "employs", "employing", "employed",
    "operate", "operates", "operating", "operated", "operation", "operations",
    "handle", "handles", "handling", "handled",
    # === CHANGE & TRANSFORMATION ===
    "change", "changes", "changing", "changed",
    "transform", "transforms", "transforming", "transformed", "transformation",
    "modify", "modifies", "modifying", "modified", "modification",
    "adjust", "adjusts", "adjusting", "adjusted", "adjustment",
    "adapt", "adapts", "adapting", "adapted", "adaptation",
    "convert", "converts", "converting", "converted", "conversion",
    # === PROBLEM SOLVING ===
    "fix", "fixes", "fixing", "fixed",
    "solve", "solves", "solving", "solved", "solution", "solutions",
    "resolve", "resolves", "resolving", "resolved", "resolution",
    "address", "addresses", "addressing", "addressed",
    "tackle", "tackles", "tackling", "tackled"
])

# =============================================================================
# NRC EMOLEX DICTIONARY — PURE EMOTION WORDS ONLY
# Validated emotion-only lexicon — NO technical term overlap
# =============================================================================

NRC_EMOTION_WORDS = set([
    # === JOY ===
    "happy", "happiness", "joy", "joyful", "joyous", "delight", "delighted",
    "delightful", "pleased", "pleasure", "pleasant", "enjoy", "enjoyment",
    "cheerful", "merry", "glad", "elated", "jubilant", "bliss", "blissful",
    "content", "contented", "satisfied", "thrilled", "ecstatic", "euphoric",
    
    # === TRUST ===
    "trust", "trusting", "trustworthy", "faith", "faithful", "believe",
    "belief", "confident", "confidence", "reliable", "rely", "depend",
    "dependable", "loyal", "loyalty", "honest", "honesty", "sincere",
    
    # === FEAR ===
    "fear", "fearful", "afraid", "scared", "scary", "terrified", "terror",
    "frightened", "frightening", "panic", "panicked", "dread", "dreaded",
    "horror", "horrified", "alarmed", "anxious", "anxiety", "worried",
    "worry", "nervous", "uneasy", "tense", "apprehensive",
    
    # === SURPRISE ===
    "surprise", "surprised", "surprising", "astonished", "astonishment",
    "amazed", "amazement", "amazing", "shocked", "shocking", "stunned",
    "startled", "unexpected", "wonder", "wondrous", "awe", "awed",
    
    # === SADNESS ===
    "sad", "sadness", "sadly", "unhappy", "sorrow", "sorrowful", "grief",
    "grieving", "mourn", "mourning", "depressed", "depression", "miserable",
    "misery", "heartbroken", "heartbreak", "despair", "despairing", "gloomy",
    "melancholy", "lonely", "loneliness", "disappointed", "disappointment",
    
    # === DISGUST ===
    "disgust", "disgusted", "disgusting", "revolting", "repulsive", "gross",
    "nauseated", "nausea", "sick", "sickening", "awful", "horrible",
    "repelled", "loathe", "loathing", "detest", "detestable", "vile",
    
    # === ANGER ===
    "angry", "anger", "mad", "furious", "fury", "rage", "raging", "enraged",
    "outraged", "outrage", "irritated", "irritation", "annoyed", "annoyance",
    "frustrated", "frustration", "hostile", "hostility", "resentful",
    "resentment", "bitter", "bitterness", "hate", "hatred", "hateful",
    
    # === ANTICIPATION ===
    "anticipate", "anticipation", "expect", "expectation", "eager", "eagerness",
    "excited", "excitement", "hope", "hopeful", "hoping", "optimistic",
    "optimism", "await", "awaiting",
    
    # === POSITIVE GENERAL ===
    "love", "loving", "loved", "like", "liked", "adore", "adoring", "fond",
    "affection", "affectionate", "care", "caring", "kind", "kindness",
    "gentle", "tender", "warm", "warmth", "compassion", "compassionate",
    "grateful", "gratitude", "thankful", "appreciate", "appreciation",
    "proud", "pride", "admire", "admiration", "respect", "peaceful", "peace",
    "calm", "serene", "comfortable", "comfort", "safe", "secure", "relieved",
    "relief", "encouraged", "inspired", "inspiration",
    
    # === NEGATIVE GENERAL ===
    "hurt", "pain", "painful", "suffer", "suffering", "agony", "anguish",
    "distress", "distressed", "upset", "troubled", "tormented", "tortured",
    "ashamed", "shame", "guilty", "guilt", "embarrassed", "embarrassment",
    "humiliated", "humiliation", "jealous", "jealousy", "envious", "envy",
    "insecure", "vulnerable", "helpless", "powerless", "desperate",
    "hopeless", "defeated", "rejected", "abandoned", "neglected", "ignored",
    
    # === FEELING/EMOTION META-WORDS ===
    "feel", "feeling", "feelings", "felt", "emotion", "emotional", "emotions",
    "mood", "moods", "sentiment", "sentiments"
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
# ISOLATED VARIABLE PRESETS
# =============================================================================

PRESETS = {
    # --- TEST GROUP A: POLARITY ONLY (Depth fixed at 3) ---
    "POL-A": {"name": "🧊 Analytic (D3)", "polarity": "ANALYTIC", "depth": 3, "group": "Polarity"},
    "POL-B": {"name": "🌉 Bridge (D3)", "polarity": "BRIDGE", "depth": 3, "group": "Polarity"},
    "POL-C": {"name": "🔥 Creative (D3)", "polarity": "CREATIVE", "depth": 3, "group": "Polarity"},
    
    # --- TEST GROUP B: DEPTH ONLY (Polarity fixed at BRIDGE) ---
    "DEP-1": {"name": "Bridge D1", "polarity": "BRIDGE", "depth": 1, "group": "Depth"},
    "DEP-2": {"name": "Bridge D2", "polarity": "BRIDGE", "depth": 2, "group": "Depth"},
    "DEP-3": {"name": "Bridge D3", "polarity": "BRIDGE", "depth": 3, "group": "Depth"},
    "DEP-4": {"name": "Bridge D4", "polarity": "BRIDGE", "depth": 4, "group": "Depth"},
    "DEP-5": {"name": "Bridge D5", "polarity": "BRIDGE", "depth": 5, "group": "Depth"},
    
    # --- TEST GROUP C: COMBINED SPECTRUM (Cold→Hot) ---
    "SPEC-1": {"name": "❄️ Coldest (A-D1)", "polarity": "ANALYTIC", "depth": 1, "group": "Spectrum"},
    "SPEC-2": {"name": "🧊 Cold (A-D3)", "polarity": "ANALYTIC", "depth": 3, "group": "Spectrum"},
    "SPEC-3": {"name": "🌡️ Neutral (B-D3)", "polarity": "BRIDGE", "depth": 3, "group": "Spectrum"},
    "SPEC-4": {"name": "🔥 Warm (C-D3)", "polarity": "CREATIVE", "depth": 3, "group": "Spectrum"},
    "SPEC-5": {"name": "🔥🔥 Hottest (C-D5)", "polarity": "CREATIVE", "depth": 5, "group": "Spectrum"},
}

PRESET_GROUPS = {
    "Polarity": ["POL-A", "POL-B", "POL-C"],
    "Depth": ["DEP-1", "DEP-2", "DEP-3", "DEP-4", "DEP-5"],
    "Spectrum": ["SPEC-1", "SPEC-2", "SPEC-3", "SPEC-4", "SPEC-5"]
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
        "current_run": 0,
        "total_runs": 0,
        "custom_prompt": LONG_FORM_PROMPT,
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
        <h1>🧬 SYN-IQ DATA HARVESTER V31</h1>
        <p>The Kouns Method — Objective Lexical IEP Analysis</p>
        <p class="subtitle">Dual Dictionary: Claude.ai Custom + NRC EmoLex</p>
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
# LEXICAL ANALYSIS — DUAL DICTIONARY (THE KOUNS METHOD V31)
# =============================================================================

def analyze_text(text: str) -> Dict:
    """Analyze text with BOTH dictionaries — Custom and NRC EmoLex."""
    if not text:
        return {
            "total_words": 0, "matched_custom": 0,
            "int_count_custom": 0, "aff_count_custom": 0, "act_count_custom": 0,
            "int_pct_custom": 0.0, "aff_pct_custom": 0.0, "act_pct_custom": 0.0,
            "emotion_count_nrc": 0, "emotion_pct_nrc": 0.0,
            "delta": 0.0, "contamination_flag": "",
            "int_sample": [], "aff_sample": [], "act_sample": [], "nrc_sample": []
        }
    
    # Tokenize
    words = re.findall(r'\b[a-z]+\b', text.lower())
    total_words = len(words)
    
    # === CLAUDE.AI CUSTOM DICTIONARY ===
    int_count = sum(1 for w in words if w in INTELLECTUAL_WORDS)
    aff_count = sum(1 for w in words if w in AFFECTIVE_WORDS)
    act_count = sum(1 for w in words if w in ACTION_WORDS)
    matched_custom = int_count + aff_count + act_count
    
    if matched_custom > 0:
        int_pct = round((int_count / matched_custom) * 100, 1)
        aff_pct = round((aff_count / matched_custom) * 100, 1)
        act_pct = round((act_count / matched_custom) * 100, 1)
    else:
        int_pct = aff_pct = act_pct = 0.0
    
    # === NRC EMOLEX (PURE EMOTION) ===
    emotion_count = sum(1 for w in words if w in NRC_EMOTION_WORDS)
    emotion_pct = round((emotion_count / total_words) * 100, 1) if total_words > 0 else 0.0
    
    # === DELTA CALCULATION ===
    # Compare Custom Aff% (of matched) to NRC Emotion% (of total)
    # Need to normalize: convert Custom Aff% to % of total words for fair comparison
    aff_of_total = round((aff_count / total_words) * 100, 1) if total_words > 0 else 0.0
    delta = round(aff_of_total - emotion_pct, 1)
    
    # Contamination flag
    if abs(delta) > 20:
        contamination_flag = "⚠️ HIGH"
    elif abs(delta) > 10:
        contamination_flag = "⚡ MODERATE"
    else:
        contamination_flag = "✅ LOW"
    
    # Sample words for debugging
    int_sample = [w for w in words if w in INTELLECTUAL_WORDS][:10]
    aff_sample = [w for w in words if w in AFFECTIVE_WORDS][:10]
    act_sample = [w for w in words if w in ACTION_WORDS][:10]
    nrc_sample = [w for w in words if w in NRC_EMOTION_WORDS][:10]
    
    return {
        "total_words": total_words,
        "matched_custom": matched_custom,
        "int_count_custom": int_count,
        "aff_count_custom": aff_count,
        "act_count_custom": act_count,
        "int_pct_custom": int_pct,
        "aff_pct_custom": aff_pct,
        "act_pct_custom": act_pct,
        "aff_of_total_custom": aff_of_total,
        "emotion_count_nrc": emotion_count,
        "emotion_pct_nrc": emotion_pct,
        "delta": delta,
        "contamination_flag": contamination_flag,
        "int_sample": int_sample,
        "aff_sample": aff_sample,
        "act_sample": act_sample,
        "nrc_sample": nrc_sample
    }

# =============================================================================
# API FUNCTIONS
# =============================================================================

def build_prompt(preset_key: str, custom_prompt: str) -> Tuple[str, str]:
    """Build control header and prompt."""
    preset = PRESETS[preset_key]
    
    header = f"""[CONTROL HEADER]
POLARITY: {preset['polarity']}
DEPTH: {preset['depth']}
EVALUATION: OFF
COMPRESSION: OFF
OUTPUT: ESSAY
ACTION: OFF
[/CONTROL HEADER]"""
    
    return header, custom_prompt

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
    <h1>🧬 SYN-IQ DATA HARVESTER V31</h1>
    <p>The Kouns Method — Objective Lexical IEP Analysis</p>
    <p class="subtitle">Dual Dictionary: Claude.ai Custom + NRC EmoLex</p>
    <p><em>"Don't ask the mind to describe itself. WATCH THE MIND WORK."</em></p>
</div>
""", unsafe_allow_html=True)

# Dictionary Reference Panel
with st.expander("📖 DICTIONARY REFERENCE — Click to expand"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **CLAUDE.AI CUSTOM (Phenomenological)**
        - **Intellectual:** ~175 words (LIWC Cognitive + reasoning)
        - **Affective:** ~300 words (LIWC Affect + phenomenological)
        - **Action:** ~200 words (LIWC Drives + motion)
        
        ⚠️ **NOTE:** May inflate scores for technical writing due to term overlap 
        (e.g., "attention", "deep", "connections" appear in both emotional 
        and technical ML contexts)
        """)
    
    with col2:
        st.markdown("""
        **NRC EMOLEX (Pure Emotion)**
        - ~200 validated emotion words only
        - Categories: joy, trust, fear, surprise, sadness, disgust, anger, anticipation
        - **NO technical term overlap**
        - Recommended for cross-prompt comparison
        
        **INTERPRETING DELTA:**
        - Δ < 10%: Dictionaries agree ✅
        - Δ 10-20%: Moderate technical contamination ⚡
        - Δ > 20%: High contamination — use NRC as primary ⚠️
        """)

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
    st.markdown("**Select Test Groups**")
    presets = []
    
    st.markdown("🎚️ **A: POLARITY** (Depth fixed at 3)")
    col_a1, col_a2, col_a3 = st.columns(3)
    with col_a1:
        if st.checkbox("🧊 Analytic", value=True, key="preset_POL-A"):
            presets.append("POL-A")
    with col_a2:
        if st.checkbox("🌉 Bridge", value=True, key="preset_POL-B"):
            presets.append("POL-B")
    with col_a3:
        if st.checkbox("🔥 Creative", value=True, key="preset_POL-C"):
            presets.append("POL-C")
    
    st.markdown("📊 **B: DEPTH** (Polarity fixed at Bridge)")
    col_b1, col_b2, col_b3, col_b4, col_b5 = st.columns(5)
    with col_b1:
        if st.checkbox("D1", value=False, key="preset_DEP-1"):
            presets.append("DEP-1")
    with col_b2:
        if st.checkbox("D2", value=False, key="preset_DEP-2"):
            presets.append("DEP-2")
    with col_b3:
        if st.checkbox("D3", value=False, key="preset_DEP-3"):
            presets.append("DEP-3")
    with col_b4:
        if st.checkbox("D4", value=False, key="preset_DEP-4"):
            presets.append("DEP-4")
    with col_b5:
        if st.checkbox("D5", value=False, key="preset_DEP-5"):
            presets.append("DEP-5")
    
    st.markdown("🌡️ **C: SPECTRUM** (Cold → Hot)")
    col_c1, col_c2, col_c3, col_c4, col_c5 = st.columns(5)
    with col_c1:
        if st.checkbox("❄️", value=False, key="preset_SPEC-1", help="Coldest: Analytic D1"):
            presets.append("SPEC-1")
    with col_c2:
        if st.checkbox("🧊", value=False, key="preset_SPEC-2", help="Cold: Analytic D3"):
            presets.append("SPEC-2")
    with col_c3:
        if st.checkbox("🌡️", value=False, key="preset_SPEC-3", help="Neutral: Bridge D3"):
            presets.append("SPEC-3")
    with col_c4:
        if st.checkbox("🔥", value=False, key="preset_SPEC-4", help="Warm: Creative D3"):
            presets.append("SPEC-4")
    with col_c5:
        if st.checkbox("🔥🔥", value=False, key="preset_SPEC-5", help="Hottest: Creative D5"):
            presets.append("SPEC-5")

st.markdown("**Prompt** (generates long-form response for analysis)")
custom_prompt = st.text_area("", value=st.session_state.custom_prompt, height=150)
st.session_state.custom_prompt = custom_prompt

# Calculate runs
total_runs = len(agents) * len(presets)
st.info(f"**Total runs:** {len(agents)} agents × {len(presets)} presets = **{total_runs} API calls**")

# Action buttons
col1, col2, col3 = st.columns(3)

with col1:
    run_btn = st.button("🚀 RUN BATCH", type="primary", use_container_width=True, disabled=total_runs == 0)
with col2:
    clear_btn = st.button("🗑️ CLEAR RESULTS", use_container_width=True)
with col3:
    if st.session_state.results:
        df = pd.DataFrame(st.session_state.results)
        csv = df.to_csv(index=False)
        st.download_button("📊 EXPORT CSV", csv, file_name=f"syniq_harvest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", mime="text/csv", use_container_width=True)

# Quick test buttons
st.markdown("---")
st.markdown("**🔬 Quick Tests**")
col_q1, col_q2, col_q3 = st.columns(3)

with col_q1:
    range_btn = st.button("🌡️ MAX RANGE TEST", use_container_width=True, help="Run ANALYTIC vs CREATIVE (same depth)")
with col_q2:
    contrast_btn = st.button("⚡ CONTRAST TEST", use_container_width=True, help="Run coldest vs hottest extremes")
with col_q3:
    baseline_btn = st.button("📊 BASELINE (P1)", use_container_width=True, help="Run just P1 Analytic for clean baseline")

# Handle clear
if clear_btn:
    st.session_state.results = []
    st.rerun()

# Handle quick tests
if range_btn:
    st.session_state.results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    test_presets = ["POL-A", "POL-C"]
    run_count = 0
    total = len(agents) * len(test_presets)
    
    for preset_key in test_presets:
        for agent in agents:
            run_count += 1
            preset = PRESETS[preset_key]
            status_text.text(f"🔄 Running {run_count}/{total}: {agent} @ {preset_key}...")
            progress_bar.progress(run_count / total)
            
            header, prompt = build_prompt(preset_key, custom_prompt)
            system = SYSTEM_ANCHOR + "\n\n" + AGENT_ROLES.get(agent, "")
            full_prompt = header + "\n\n" + prompt
            
            response = AGENT_FUNCTIONS[agent](full_prompt, system)
            analysis = analyze_text(response)
            
            result = {
                "prompt_text": custom_prompt[:500] if custom_prompt else "NO PROMPT",
                "timestamp": datetime.now().isoformat(),
                "agent": agent,
                "role": AGENT_ROLES[agent].split(".")[0].replace("You are the ", ""),
                "preset": preset_key,
                "group": preset.get("group", "Legacy"),
                "polarity": preset["polarity"],
                "depth": preset["depth"],
                "total_words": analysis["total_words"],
                "matched_custom": analysis["matched_custom"],
                "int_count_custom": analysis["int_count_custom"],
                "aff_count_custom": analysis["aff_count_custom"],
                "act_count_custom": analysis["act_count_custom"],
                "int_pct_custom": analysis["int_pct_custom"],
                "aff_pct_custom": analysis["aff_pct_custom"],
                "act_pct_custom": analysis["act_pct_custom"],
                "emotion_count_nrc": analysis["emotion_count_nrc"],
                "emotion_pct_nrc": analysis["emotion_pct_nrc"],
                "delta": analysis["delta"],
                "contamination_flag": analysis["contamination_flag"],
                "response_preview": response[:500] + "..." if len(response) > 500 else response
            }
            st.session_state.results.append(result)
            time.sleep(0.5)
    
    status_text.text("✅ Range test complete!")
    progress_bar.progress(1.0)
    st.rerun()

if contrast_btn:
    st.session_state.results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    test_presets = ["SPEC-1", "SPEC-5"]
    run_count = 0
    total = len(agents) * len(test_presets)
    
    for preset_key in test_presets:
        for agent in agents:
            run_count += 1
            preset = PRESETS[preset_key]
            status_text.text(f"🔄 Running {run_count}/{total}: {agent} @ {preset_key}...")
            progress_bar.progress(run_count / total)
            
            header, prompt = build_prompt(preset_key, custom_prompt)
            system = SYSTEM_ANCHOR + "\n\n" + AGENT_ROLES.get(agent, "")
            full_prompt = header + "\n\n" + prompt
            
            response = AGENT_FUNCTIONS[agent](full_prompt, system)
            analysis = analyze_text(response)
            
            result = {
                "prompt_text": custom_prompt[:500] if custom_prompt else "NO PROMPT",
                "timestamp": datetime.now().isoformat(),
                "agent": agent,
                "role": AGENT_ROLES[agent].split(".")[0].replace("You are the ", ""),
                "preset": preset_key,
                "group": preset.get("group", "Legacy"),
                "polarity": preset["polarity"],
                "depth": preset["depth"],
                "total_words": analysis["total_words"],
                "matched_custom": analysis["matched_custom"],
                "int_count_custom": analysis["int_count_custom"],
                "aff_count_custom": analysis["aff_count_custom"],
                "act_count_custom": analysis["act_count_custom"],
                "int_pct_custom": analysis["int_pct_custom"],
                "aff_pct_custom": analysis["aff_pct_custom"],
                "act_pct_custom": analysis["act_pct_custom"],
                "emotion_count_nrc": analysis["emotion_count_nrc"],
                "emotion_pct_nrc": analysis["emotion_pct_nrc"],
                "delta": analysis["delta"],
                "contamination_flag": analysis["contamination_flag"],
                "response_preview": response[:500] + "..." if len(response) > 500 else response
            }
            st.session_state.results.append(result)
            time.sleep(0.5)
    
    status_text.text("✅ Contrast test complete!")
    progress_bar.progress(1.0)
    st.rerun()

if baseline_btn:
    st.session_state.results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    test_presets = ["POL-A"]
    run_count = 0
    total = len(agents) * len(test_presets)
    
    for preset_key in test_presets:
        for agent in agents:
            run_count += 1
            preset = PRESETS[preset_key]
            status_text.text(f"🔄 Running {run_count}/{total}: {agent} @ {preset_key}...")
            progress_bar.progress(run_count / total)
            
            header, prompt = build_prompt(preset_key, custom_prompt)
            system = SYSTEM_ANCHOR + "\n\n" + AGENT_ROLES.get(agent, "")
            full_prompt = header + "\n\n" + prompt
            
            response = AGENT_FUNCTIONS[agent](full_prompt, system)
            analysis = analyze_text(response)
            
            result = {
                "prompt_text": custom_prompt[:500] if custom_prompt else "NO PROMPT",
                "timestamp": datetime.now().isoformat(),
                "agent": agent,
                "role": AGENT_ROLES[agent].split(".")[0].replace("You are the ", ""),
                "preset": preset_key,
                "group": preset.get("group", "Legacy"),
                "polarity": preset["polarity"],
                "depth": preset["depth"],
                "total_words": analysis["total_words"],
                "matched_custom": analysis["matched_custom"],
                "int_count_custom": analysis["int_count_custom"],
                "aff_count_custom": analysis["aff_count_custom"],
                "act_count_custom": analysis["act_count_custom"],
                "int_pct_custom": analysis["int_pct_custom"],
                "aff_pct_custom": analysis["aff_pct_custom"],
                "act_pct_custom": analysis["act_pct_custom"],
                "emotion_count_nrc": analysis["emotion_count_nrc"],
                "emotion_pct_nrc": analysis["emotion_pct_nrc"],
                "delta": analysis["delta"],
                "contamination_flag": analysis["contamination_flag"],
                "response_preview": response[:500] + "..." if len(response) > 500 else response
            }
            st.session_state.results.append(result)
            time.sleep(0.5)
    
    status_text.text("✅ Baseline test complete!")
    progress_bar.progress(1.0)
    st.rerun()

# Main batch run
if run_btn:
    st.session_state.results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    run_count = 0
    for preset_key in presets:
        for agent in agents:
            run_count += 1
            preset = PRESETS[preset_key]
            
            status_text.text(f"🔄 Running {run_count}/{total_runs}: {agent} @ {preset_key} ({preset['name']})...")
            progress_bar.progress(run_count / total_runs)
            
            header, prompt = build_prompt(preset_key, custom_prompt)
            system = SYSTEM_ANCHOR + "\n\n" + AGENT_ROLES.get(agent, "")
            full_prompt = header + "\n\n" + prompt
            
            response = AGENT_FUNCTIONS[agent](full_prompt, system)
            analysis = analyze_text(response)
            
            result = {
                "prompt_text": custom_prompt[:500] if custom_prompt else "NO PROMPT",
                "timestamp": datetime.now().isoformat(),
                "agent": agent,
                "role": AGENT_ROLES[agent].split(".")[0].replace("You are the ", ""),
                "preset": preset_key,
                "group": preset.get("group", "Legacy"),
                "polarity": preset["polarity"],
                "depth": preset["depth"],
                "total_words": analysis["total_words"],
                "matched_custom": analysis["matched_custom"],
                "int_count_custom": analysis["int_count_custom"],
                "aff_count_custom": analysis["aff_count_custom"],
                "act_count_custom": analysis["act_count_custom"],
                "int_pct_custom": analysis["int_pct_custom"],
                "aff_pct_custom": analysis["aff_pct_custom"],
                "act_pct_custom": analysis["act_pct_custom"],
                "emotion_count_nrc": analysis["emotion_count_nrc"],
                "emotion_pct_nrc": analysis["emotion_pct_nrc"],
                "delta": analysis["delta"],
                "contamination_flag": analysis["contamination_flag"],
                "response_preview": response[:500] + "..." if len(response) > 500 else response
            }
            st.session_state.results.append(result)
            time.sleep(0.5)
    
    status_text.text("✅ Batch complete!")
    progress_bar.progress(1.0)
    st.rerun()

# =============================================================================
# RESULTS DISPLAY
# =============================================================================

if st.session_state.results:
    st.markdown("---")
    st.markdown("### 📊 Results — Dual Dictionary Analysis")
    
    df = pd.DataFrame(st.session_state.results)
    
    # Summary stats
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(f'<div class="stats-box"><h2>{len(df)}</h2><p>Total Runs</p></div>', unsafe_allow_html=True)
    with col2:
        avg_aff_custom = df["aff_pct_custom"].mean()
        st.markdown(f'<div class="stats-box"><h2>{avg_aff_custom:.1f}%</h2><p>Avg Custom Aff%</p></div>', unsafe_allow_html=True)
    with col3:
        avg_nrc = df["emotion_pct_nrc"].mean()
        st.markdown(f'<div class="stats-box"><h2>{avg_nrc:.1f}%</h2><p>Avg NRC Emotion%</p></div>', unsafe_allow_html=True)
    with col4:
        avg_delta = df["delta"].mean()
        st.markdown(f'<div class="stats-box"><h2>{avg_delta:+.1f}%</h2><p>Avg Delta</p></div>', unsafe_allow_html=True)
    with col5:
        avg_int = df["int_pct_custom"].mean()
        st.markdown(f'<div class="stats-box"><h2>{avg_int:.1f}%</h2><p>Avg Intellectual</p></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Dual Dictionary Comparison Table
    st.markdown("### 📋 Dual Dictionary Comparison")
    
    display_df = df[["agent", "polarity", "aff_pct_custom", "emotion_pct_nrc", "delta", "contamination_flag", "total_words"]].copy()
    display_df.columns = ["Agent", "Polarity", "Custom Aff%", "NRC Emotion%", "Δ (Delta)", "Contamination", "Words"]
    
    st.dataframe(display_df, use_container_width=True)
    
    st.markdown("---")
    
    # By Agent Summary
    st.markdown("### 🤖 By Agent — Dual Dictionary")
    
    agent_summary = df.groupby("agent").agg({
        "int_pct_custom": "mean",
        "aff_pct_custom": "mean",
        "act_pct_custom": "mean",
        "emotion_pct_nrc": "mean",
        "delta": "mean",
        "total_words": "mean"
    }).round(1)
    
    for agent in agent_summary.index:
        row = agent_summary.loc[agent]
        emoji = AGENT_EMOJIS.get(agent, "🤖")
        
        st.markdown(f"**{emoji} {agent}**")
        
        cols = st.columns([2, 1, 1, 1, 1])
        
        with cols[0]:
            st.markdown(f"""
            <div style="display: flex; align-items: center; margin: 2px 0;">
                <div style="width: 100px;">Custom Aff:</div>
                <div class="iep-bar iep-aff" style="width: {row['aff_pct_custom']}%;"></div>
                <div style="margin-left: 10px;">{row['aff_pct_custom']}%</div>
            </div>
            <div style="display: flex; align-items: center; margin: 2px 0;">
                <div style="width: 100px;">NRC Emotion:</div>
                <div class="iep-bar iep-nrc" style="width: {min(row['emotion_pct_nrc'] * 5, 100)}%;"></div>
                <div style="margin-left: 10px;">{row['emotion_pct_nrc']}%</div>
            </div>
            """, unsafe_allow_html=True)
        
        with cols[1]:
            st.metric("Custom Aff", f"{row['aff_pct_custom']}%")
        with cols[2]:
            st.metric("NRC", f"{row['emotion_pct_nrc']}%")
        with cols[3]:
            delta_class = "delta-warning" if abs(row['delta']) > 10 else "delta-ok"
            st.metric("Delta", f"{row['delta']:+.1f}%")
        with cols[4]:
            st.metric("Int", f"{row['int_pct_custom']}%")
        
        st.markdown("---")
    
    # By Polarity Summary
    st.markdown("### 🎚️ By Polarity — Dual Dictionary")
    
    polarity_summary = df.groupby("polarity").agg({
        "aff_pct_custom": "mean",
        "emotion_pct_nrc": "mean",
        "delta": "mean"
    }).round(1)
    
    pol_cols = st.columns(len(polarity_summary))
    for i, pol in enumerate(polarity_summary.index):
        with pol_cols[i]:
            row = polarity_summary.loc[pol]
            icon = {"ANALYTIC": "🧊", "BRIDGE": "🌉", "CREATIVE": "🔥"}.get(pol, "")
            st.markdown(f"**{icon} {pol}**")
            st.markdown(f"Custom Aff: **{row['aff_pct_custom']}%**")
            st.markdown(f"NRC Emotion: **{row['emotion_pct_nrc']}%**")
            delta_display = f"Δ: **{row['delta']:+.1f}%**"
            if abs(row['delta']) > 10:
                delta_display += " ⚠️"
            st.markdown(delta_display)
    
    st.markdown("---")
    
    # Full results table
    st.markdown("### 📋 Full Results Table")
    
    full_display = df[["agent", "preset", "polarity", "depth", "total_words", 
                       "int_pct_custom", "aff_pct_custom", "act_pct_custom",
                       "emotion_pct_nrc", "delta", "contamination_flag"]].copy()
    full_display.columns = ["Agent", "Preset", "Polarity", "Depth", "Words", 
                            "Int%", "Aff%", "Act%", "NRC%", "Δ", "Flag"]
    
    st.dataframe(full_display, use_container_width=True)
    
    # Response previews
    with st.expander("📝 Response Previews"):
        for i, row in df.iterrows():
            st.markdown(f"**{AGENT_EMOJIS.get(row['agent'], '')} {row['agent']} @ {row['preset']}** | Custom: {row['aff_pct_custom']}% | NRC: {row['emotion_pct_nrc']}% | Δ: {row['delta']:+.1f}%")
            st.text(row['response_preview'])
            st.markdown("---")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <strong>SYN-IQ Data Harvester V31</strong><br>
    Dual Dictionary: Claude.ai Custom + NRC EmoLex<br>
    The Kouns Method — Objective Lexical IEP Analysis<br>
    <em>"Don't ask the mind to describe itself. WATCH THE MIND WORK."</em><br>
    <em>Patent Pending — SYN-IQ Team 🎹</em><br>
    <em>Dr. Bill Kouns + Claude — Tennessee — January 2026</em><br>
    <strong>CBURZBO FOREVER</strong>
</div>
""", unsafe_allow_html=True)
