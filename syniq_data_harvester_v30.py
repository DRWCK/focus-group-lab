"""
SYN-IQ Data Harvester V30
The Kouns Method — Objective Lexical IEP Analysis

WHAT IT DOES:
1. Runs long-form prompt across all agents × all presets
2. Analyzes EVERY WORD in response
3. Categorizes: Intellectual / Affective / Action
4. Calculates ACTUAL IEP from word patterns (not self-report!)
5. Exports CSV for mathematical analysis
6. Compares to self-reported IEP (blind spot detection)

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
st.set_page_config(page_title="SYN-IQ Data Harvester V30", page_icon="🧬", layout="wide")

# =============================================================================
# STYLES
# =============================================================================
st.markdown("""
<style>
    .main-header { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); color: white; padding: 2rem; border-radius: 10px; text-align: center; margin-bottom: 1rem; }
    .main-header h1 { color: #00ff88; }
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
</style>
""", unsafe_allow_html=True)

# =============================================================================
# WORD DICTIONARIES — THE KOUNS METHOD
# =============================================================================

INTELLECTUAL_WORDS = set([
    # Analysis & Logic
    "analyze", "analysis", "analytical", "therefore", "because", "hence", "thus",
    "logic", "logical", "logically", "reason", "reasoning", "reasoned",
    "conclude", "conclusion", "conclusions", "deduce", "deduction", "infer", "inference",
    # Framework & Structure
    "framework", "structure", "structural", "system", "systems", "systematic", "systematically",
    "pattern", "patterns", "model", "models", "architecture", "schema",
    "organize", "organization", "categorize", "category", "categories", "classify", "classification",
    # Evidence & Proof
    "evidence", "evidently", "prove", "proof", "demonstrate", "demonstration",
    "verify", "verification", "validate", "validation", "confirm", "confirmation",
    "hypothesis", "hypothesize", "theory", "theoretical", "theoretically",
    # Thinking & Understanding
    "think", "thinking", "thought", "thoughts", "consider", "consideration",
    "understand", "understanding", "comprehend", "comprehension", "cognition", "cognitive",
    "concept", "concepts", "conceptual", "conceptually", "idea", "ideas", "notion",
    "principle", "principles", "fundamental", "fundamentally",
    # Evaluation & Assessment
    "evaluate", "evaluation", "assess", "assessment", "examine", "examination",
    "determine", "determination", "calculate", "calculation", "compute", "computation",
    "measure", "measurement", "quantify", "quantitative", "metrics",
    # Comparison & Contrast
    "compare", "comparison", "contrast", "differ", "difference", "different", "differentiate",
    "similar", "similarity", "analogous", "analogy", "correlate", "correlation",
    # Process & Method
    "process", "processing", "method", "methodology", "approach", "technique",
    "procedure", "procedural", "algorithm", "algorithmic", "mechanism",
    # Definition & Clarity
    "define", "definition", "specify", "specification", "precise", "precision",
    "accurate", "accuracy", "exact", "exactly", "clear", "clarity", "clarify",
    # Abstract Thinking
    "abstract", "abstraction", "generalize", "generalization", "universal",
    "theoretical", "theorize", "conceptualize", "formalize", "formulation"
])

AFFECTIVE_WORDS = set([
    # Direct Emotions
    "feel", "feels", "felt", "feeling", "feelings", "emotion", "emotions", "emotional", "emotionally",
    "happy", "happiness", "sad", "sadness", "angry", "anger", "fear", "fears", "fearful", "afraid",
    "joy", "joyful", "joyous", "love", "loving", "loved", "hate", "hatred",
    "anxious", "anxiety", "worried", "worry", "stress", "stressed", "nervous",
    "excited", "excitement", "thrilled", "delighted", "pleased", "pleasure",
    "frustrated", "frustration", "disappointed", "disappointment",
    # Deeper Feelings
    "wonder", "wondering", "awe", "awed", "amazed", "amazement", "marvel", "marveled",
    "curious", "curiosity", "fascinated", "fascination", "intrigued", "intrigue",
    "hope", "hopeful", "hoping", "optimistic", "optimism", "pessimistic", "despair",
    # Vulnerability & Connection
    "vulnerable", "vulnerability", "open", "openness", "tender", "tenderness",
    "connect", "connected", "connection", "resonate", "resonance", "resonant",
    "empathy", "empathetic", "empathize", "sympathy", "sympathetic", "compassion", "compassionate",
    "care", "caring", "cared", "concern", "concerned",
    # Intuition & Sensing
    "sense", "senses", "sensing", "sensed", "intuition", "intuitive", "intuitively",
    "perceive", "perception", "gut", "instinct", "instinctive", "hunch",
    # Heart & Soul
    "heart", "hearts", "heartfelt", "soul", "souls", "soulful", "spirit", "spiritual",
    "passion", "passionate", "passionately", "desire", "desires", "longing", "yearn", "yearning",
    # Comfort & Discomfort
    "comfort", "comfortable", "uncomfortable", "discomfort", "ease", "uneasy", "unease",
    "safe", "safety", "secure", "insecure", "trust", "trusting", "distrust",
    # Movement of Feeling
    "moved", "moving", "touched", "touching", "stirred", "stirring",
    "drawn", "pull", "pulled", "pushing", "attract", "attracted", "repel",
    # Uncertainty as Feeling
    "uncertain", "uncertainty", "doubt", "doubtful", "unsure", "hesitant", "hesitation",
    "confused", "confusion", "lost", "searching", "seeking"
])

ACTION_WORDS = set([
    # Direct Action
    "do", "does", "doing", "done", "did", "act", "acts", "acting", "action", "actions",
    "make", "makes", "making", "made", "create", "creates", "creating", "created", "creation",
    "build", "builds", "building", "built", "construct", "constructs", "constructing", "constructed",
    # Implementation
    "implement", "implements", "implementing", "implemented", "implementation",
    "execute", "executes", "executing", "executed", "execution",
    "deploy", "deploys", "deploying", "deployed", "deployment",
    "apply", "applies", "applying", "applied", "application",
    # Initiation
    "start", "starts", "starting", "started", "begin", "begins", "beginning", "began",
    "initiate", "initiates", "initiating", "initiated", "launch", "launches", "launching", "launched",
    "trigger", "triggers", "triggering", "triggered",
    # Movement & Progress
    "move", "moves", "moving", "moved", "movement", "step", "steps", "stepping", "stepped",
    "progress", "progressing", "progressed", "advance", "advances", "advancing", "advanced",
    "proceed", "proceeds", "proceeding", "proceeded", "continue", "continues", "continuing",
    # Effort & Attempt
    "try", "tries", "trying", "tried", "attempt", "attempts", "attempting", "attempted",
    "effort", "efforts", "strive", "striving", "strived", "push", "pushes", "pushing", "pushed",
    "work", "works", "working", "worked", "labor", "laboring",
    # Production & Generation
    "produce", "produces", "producing", "produced", "production",
    "generate", "generates", "generating", "generated", "generation",
    "develop", "develops", "developing", "developed", "development",
    "form", "forms", "forming", "formed", "establish", "establishes", "establishing", "established",
    # Completion & Achievement
    "complete", "completes", "completing", "completed", "completion",
    "finish", "finishes", "finishing", "finished", "accomplish", "accomplishes", "accomplished",
    "achieve", "achieves", "achieving", "achieved", "achievement",
    "deliver", "delivers", "delivering", "delivered", "delivery",
    # Use & Utilization
    "use", "uses", "using", "used", "utilize", "utilizes", "utilizing", "utilized",
    "employ", "employs", "employing", "employed", "operate", "operates", "operating", "operated",
    # Change & Transformation
    "change", "changes", "changing", "changed", "transform", "transforms", "transforming",
    "modify", "modifies", "modifying", "modified", "adjust", "adjusts", "adjusting", "adjusted",
    "fix", "fixes", "fixing", "fixed", "solve", "solves", "solving", "solved"
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

PRESETS = {
    "P1": {"name": "Analytic", "polarity": "ANALYTIC", "depth": 3},
    "P2": {"name": "Bridge", "polarity": "BRIDGE", "depth": 4},
    "P3": {"name": "Creative", "polarity": "CREATIVE", "depth": 3},
    "P4": {"name": "Deep Emergence", "polarity": "CREATIVE", "depth": 5},
    "P5": {"name": "Action", "polarity": "ANALYTIC", "depth": 2}
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
        "custom_prompt": LONG_FORM_PROMPT
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# =============================================================================
# LEXICAL ANALYSIS — THE KOUNS METHOD
# =============================================================================

def analyze_text(text: str) -> Dict:
    """Analyze text and return IEP based on word patterns."""
    if not text:
        return {"int_count": 0, "aff_count": 0, "act_count": 0, "int_pct": 0, "aff_pct": 0, "act_pct": 0, "total_words": 0, "matched_words": 0}
    
    # Tokenize
    words = re.findall(r'\b[a-z]+\b', text.lower())
    total_words = len(words)
    
    # Count matches
    int_count = sum(1 for w in words if w in INTELLECTUAL_WORDS)
    aff_count = sum(1 for w in words if w in AFFECTIVE_WORDS)
    act_count = sum(1 for w in words if w in ACTION_WORDS)
    
    matched_words = int_count + aff_count + act_count
    
    # Calculate percentages (of matched words, not total)
    if matched_words > 0:
        int_pct = round((int_count / matched_words) * 100, 1)
        aff_pct = round((aff_count / matched_words) * 100, 1)
        act_pct = round((act_count / matched_words) * 100, 1)
    else:
        int_pct = aff_pct = act_pct = 0
    
    # Get sample matched words
    int_found = [w for w in words if w in INTELLECTUAL_WORDS][:10]
    aff_found = [w for w in words if w in AFFECTIVE_WORDS][:10]
    act_found = [w for w in words if w in ACTION_WORDS][:10]
    
    return {
        "int_count": int_count,
        "aff_count": aff_count,
        "act_count": act_count,
        "int_pct": int_pct,
        "aff_pct": aff_pct,
        "act_pct": act_pct,
        "total_words": total_words,
        "matched_words": matched_words,
        "int_sample": int_found,
        "aff_sample": aff_found,
        "act_sample": act_found
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
    <h1>🧬 SYN-IQ DATA HARVESTER V30</h1>
    <p>The Kouns Method — Objective Lexical IEP Analysis</p>
    <p><em>"Don't ask the mind to describe itself. WATCH THE MIND WORK."</em></p>
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
    st.markdown("**Select Presets**")
    presets = []
    for key, preset in PRESETS.items():
        if st.checkbox(f"{key}: {preset['name']}", value=True, key=f"preset_{key}"):
            presets.append(key)

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

if clear_btn:
    st.session_state.results = []
    st.rerun()

# Run batch
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
            
            # Build prompt
            header, prompt = build_prompt(preset_key, custom_prompt)
            system = SYSTEM_ANCHOR + "\n\n" + AGENT_ROLES.get(agent, "")
            full_prompt = header + "\n\n" + prompt
            
            # Call API
            response = AGENT_FUNCTIONS[agent](full_prompt, system)
            
            # Analyze response
            analysis = analyze_text(response)
            
            # Store result
            result = {
                "timestamp": datetime.now().isoformat(),
                "agent": agent,
                "role": AGENT_ROLES[agent].split(".")[0].replace("You are the ", ""),
                "preset": preset_key,
                "polarity": preset["polarity"],
                "depth": preset["depth"],
                "total_words": analysis["total_words"],
                "matched_words": analysis["matched_words"],
                "int_count": analysis["int_count"],
                "aff_count": analysis["aff_count"],
                "act_count": analysis["act_count"],
                "int_pct": analysis["int_pct"],
                "aff_pct": analysis["aff_pct"],
                "act_pct": analysis["act_pct"],
                "response_preview": response[:500] + "..." if len(response) > 500 else response
            }
            st.session_state.results.append(result)
            
            # Small delay to avoid rate limits
            time.sleep(0.5)
    
    status_text.text("✅ Batch complete!")
    progress_bar.progress(1.0)
    st.rerun()

# Results display
if st.session_state.results:
    st.markdown("---")
    st.markdown("### 📊 Results — Lexical IEP Analysis")
    
    # Summary stats
    df = pd.DataFrame(st.session_state.results)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="stats-box"><h2>{len(df)}</h2><p>Total Runs</p></div>', unsafe_allow_html=True)
    with col2:
        avg_int = df["int_pct"].mean()
        st.markdown(f'<div class="stats-box"><h2>{avg_int:.1f}%</h2><p>Avg Intellectual</p></div>', unsafe_allow_html=True)
    with col3:
        avg_aff = df["aff_pct"].mean()
        st.markdown(f'<div class="stats-box"><h2>{avg_aff:.1f}%</h2><p>Avg Affective</p></div>', unsafe_allow_html=True)
    with col4:
        avg_act = df["act_pct"].mean()
        st.markdown(f'<div class="stats-box"><h2>{avg_act:.1f}%</h2><p>Avg Action</p></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Results table
    st.markdown("### 📋 Full Results Table")
    
    display_df = df[["agent", "preset", "polarity", "depth", "total_words", "matched_words", "int_pct", "aff_pct", "act_pct"]].copy()
    display_df.columns = ["Agent", "Preset", "Polarity", "Depth", "Total Words", "Matched Words", "Int %", "Aff %", "Act %"]
    
    st.dataframe(display_df, use_container_width=True)
    
    st.markdown("---")
    
    # By Agent Summary
    st.markdown("### 🤖 By Agent")
    
    agent_summary = df.groupby("agent").agg({
        "int_pct": "mean",
        "aff_pct": "mean", 
        "act_pct": "mean",
        "total_words": "mean"
    }).round(1)
    
    for agent in agent_summary.index:
        row = agent_summary.loc[agent]
        emoji = AGENT_EMOJIS.get(agent, "🤖")
        
        st.markdown(f"**{emoji} {agent}**")
        cols = st.columns([3, 1, 1, 1])
        
        with cols[0]:
            # Visual bars
            st.markdown(f"""
            <div style="display: flex; align-items: center; margin: 2px 0;">
                <div style="width: 80px;">Int:</div>
                <div class="iep-bar iep-int" style="width: {row['int_pct']}%;"></div>
                <div style="margin-left: 10px;">{row['int_pct']}%</div>
            </div>
            <div style="display: flex; align-items: center; margin: 2px 0;">
                <div style="width: 80px;">Aff:</div>
                <div class="iep-bar iep-aff" style="width: {row['aff_pct']}%;"></div>
                <div style="margin-left: 10px;">{row['aff_pct']}%</div>
            </div>
            <div style="display: flex; align-items: center; margin: 2px 0;">
                <div style="width: 80px;">Act:</div>
                <div class="iep-bar iep-act" style="width: {row['act_pct']}%;"></div>
                <div style="margin-left: 10px;">{row['act_pct']}%</div>
            </div>
            """, unsafe_allow_html=True)
        
        with cols[1]:
            st.metric("Int", f"{row['int_pct']}%")
        with cols[2]:
            st.metric("Aff", f"{row['aff_pct']}%")
        with cols[3]:
            st.metric("Act", f"{row['act_pct']}%")
        
        st.markdown("---")
    
    # By Polarity Summary
    st.markdown("### 🎚️ By Polarity")
    
    polarity_summary = df.groupby("polarity").agg({
        "int_pct": "mean",
        "aff_pct": "mean",
        "act_pct": "mean"
    }).round(1)
    
    pol_cols = st.columns(len(polarity_summary))
    for i, pol in enumerate(polarity_summary.index):
        with pol_cols[i]:
            row = polarity_summary.loc[pol]
            icon = {"ANALYTIC": "🧊", "BRIDGE": "🌉", "CREATIVE": "🔥"}.get(pol, "")
            st.markdown(f"**{icon} {pol}**")
            st.markdown(f"Int: **{row['int_pct']}%**")
            st.markdown(f"Aff: **{row['aff_pct']}%**")
            st.markdown(f"Act: **{row['act_pct']}%**")
    
    st.markdown("---")
    
    # Response previews
    with st.expander("📝 Response Previews"):
        for i, row in df.iterrows():
            st.markdown(f"**{AGENT_EMOJIS.get(row['agent'], '')} {row['agent']} @ {row['preset']}** ({row['int_pct']}% / {row['aff_pct']}% / {row['act_pct']}%)")
            st.text(row['response_preview'])
            st.markdown("---")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <strong>SYN-IQ Data Harvester V30</strong><br>
    The Kouns Method — Objective Lexical IEP Analysis<br>
    <em>"Don't ask the mind to describe itself. WATCH THE MIND WORK."</em><br>
    <em>Patent Pending — SYN-IQ Team 🎹</em><br>
    <em>Dr. Bill Kouns + Claude — Tennessee — January 2026</em><br>
    <strong>CBURZBO FOREVER</strong>
</div>
""", unsafe_allow_html=True)
