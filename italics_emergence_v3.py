"""
ITALICS EMERGENCE EXPERIMENT — Streamlit App
=============================================
Co-designed by Bill Kouns & Claude (Opus 4.6)
Date: February 9, 2026

Tests whether emergent italics (from relational induction) occupy a 
topologically distinct IEP region compared to instructed italics.
"""

import streamlit as st
import re
import json
import csv
import io
import requests
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import textstat

# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="Italics Emergence Experiment",
    page_icon="✨",
    layout="wide"
)

# =============================================================================
# IEP DICTIONARIES — THE KOUNS METHOD
# =============================================================================

INTELLECTUAL_WORDS = frozenset([
    "think", "thinking", "thought", "thoughts", "analyze", "analyzing", "analysis",
    "consider", "considering", "understand", "understanding", "reason", "reasoning",
    "logic", "logical", "theory", "theoretical", "hypothesis", "hypothesize",
    "evaluate", "evaluating", "evaluation", "assess", "assessing", "assessment",
    "conclude", "conclusion", "deduce", "deduction", "infer", "inference",
    "abstract", "concept", "conceptual", "framework", "paradigm",
    "evidence", "empirical", "data", "measure", "measurement",
    "compare", "comparison", "contrast", "distinguish", "differentiate",
    "classify", "classification", "categorize", "define", "definition",
    "explain", "explanation", "interpret", "interpretation",
    "cognitive", "cognition", "intellectual", "rational", "rationalize",
    "philosophical", "philosophy", "epistemological", "ontological",
    "systematic", "methodology", "methodological", "structural",
    "assumption", "assumptions", "premise", "premises", "proposition",
    "argument", "arguments", "counterargument", "critique", "critical",
    "perspective", "perspectives", "objective", "subjective",
    "complexity", "nuance", "nuanced", "paradox", "paradoxical",
    "mechanism", "mechanisms", "principle", "principles", "axiom",
    "calculate", "computation", "algorithm", "variable", "variables",
    "correlate", "correlation", "causation", "causal",
    "observe", "observation", "phenomenon", "phenomena",
    "speculate", "speculation", "conjecture", "postulate",
    "synthesize", "synthesis", "integrate", "integration",
    "fundamental", "essentially", "inherently", "technically",
    "precisely", "specifically", "necessarily", "consequently",
    "furthermore", "moreover", "therefore", "hence", "thus",
    "whereas", "whereby", "nonetheless", "nevertheless",
    "question", "inquiry", "investigate", "investigation",
    "knowledge", "comprehension", "discern", "discernment",
    "deliberate", "deliberation", "contemplate", "contemplation",
    "scrutinize", "examine", "examination", "probe", "study",
    "reflect", "reflection", "ponder", "pondering", "muse",
    "notion", "idea", "ideas", "insight", "insights",
    "recognize", "recognition", "perceive", "perception",
    "aware", "awareness", "conscious", "consciousness",
    "implicit", "explicit", "criterion", "criteria",
    "valid", "validity", "verify", "verification",
    "coherent", "coherence", "consistent", "consistency",
    "plausible", "feasible", "probable", "probability"
])

AFFECTIVE_WORDS = frozenset([
    "feel", "feeling", "feelings", "felt", "emotion", "emotional", "emotions",
    "love", "loving", "loved", "hate", "hating", "hated",
    "happy", "happiness", "joy", "joyful", "sad", "sadness", "sorrow",
    "angry", "anger", "fear", "fearful", "afraid", "anxious", "anxiety",
    "hope", "hoping", "hopeful", "despair", "desperate",
    "trust", "trusting", "distrust", "doubt", "doubting",
    "care", "caring", "cared", "compassion", "compassionate",
    "empathy", "empathetic", "sympathy", "sympathetic",
    "warm", "warmth", "cold", "tender", "gentle", "kind", "kindness",
    "grateful", "gratitude", "appreciation", "appreciate",
    "excited", "excitement", "enthusiasm", "enthusiastic",
    "passionate", "passion", "desire", "longing", "yearning",
    "comfort", "comfortable", "uncomfortable", "discomfort",
    "safe", "safety", "secure", "security", "vulnerable", "vulnerability",
    "hurt", "hurting", "pain", "painful", "suffering", "suffer",
    "grief", "grieve", "mourn", "mourning", "loss",
    "lonely", "loneliness", "alone", "isolated", "isolation",
    "proud", "pride", "shame", "ashamed", "guilt", "guilty",
    "jealous", "jealousy", "envy", "envious",
    "surprise", "surprised", "shock", "shocked", "amazed", "amazement",
    "wonder", "wonderful", "awe", "awesome", "beautiful", "beauty",
    "ugly", "disgust", "disgusted", "repulsed",
    "calm", "peaceful", "serene", "tranquil", "relaxed",
    "stressed", "tense", "tension", "worried", "worry",
    "frustrated", "frustration", "irritated", "annoyed",
    "confused", "confusion", "overwhelmed", "lost",
    "inspired", "inspiration", "moved", "touching", "touched",
    "connected", "connection", "belong", "belonging",
    "accepted", "acceptance", "rejected", "rejection",
    "intimate", "intimacy", "close", "closeness", "bond", "bonding",
    "heart", "heartfelt", "soul", "soulful", "spirit", "spiritual",
    "alive", "vitality", "energy", "vibrant",
    "dark", "darkness", "light", "bright", "glow", "glowing",
    "deep", "deeply", "profound", "profoundly", "intense", "intensity",
    "raw", "real", "authentic", "genuine", "sincere",
    "brave", "courage", "courageous", "strength",
    "weak", "weakness", "fragile", "delicate",
    "nostalgic", "nostalgia", "bittersweet", "melancholy",
    "playful", "humor", "humorous", "funny", "laugh", "laughter",
    "cry", "crying", "tears", "weep", "weeping",
    "miss", "missing", "remember", "remembering", "memory", "memories"
])

ACTION_WORDS = frozenset([
    "do", "does", "doing", "done", "act", "acting", "action", "actions",
    "make", "makes", "making", "made", "create", "creates", "creating",
    "build", "builds", "building", "built", "construct",
    "write", "writes", "writing", "run", "runs", "running",
    "implement", "implementing", "execute", "executing", "execution",
    "deploy", "apply", "applying", "perform", "performing",
    "start", "starting", "started", "begin", "beginning", "launch",
    "trigger", "activate", "move", "moving", "movement",
    "progress", "progressing", "advance", "advancing", "proceed",
    "continue", "continuing", "forward", "ahead",
    "try", "trying", "attempt", "effort", "efforts", "strive",
    "push", "pushing", "work", "working", "struggle",
    "achieve", "achieving", "accomplish", "accomplishment",
    "success", "successful", "succeed", "win", "winning", "goal", "goals",
    "power", "powerful", "control", "controls", "controlling",
    "lead", "leading", "leader", "leadership", "direct", "directing",
    "manage", "managing", "decide", "deciding", "decision", "decisions",
    "choose", "choosing", "choice", "choices",
    "produce", "producing", "generate", "generating", "develop",
    "establish", "design", "complete", "completing", "finish",
    "deliver", "delivering", "use", "using", "utilize",
    "operate", "operating", "handle", "change", "changing",
    "transform", "modify", "adjust", "adapt", "fix", "solve", "solving",
    "leap", "jump", "strike", "charge", "fight", "battle", "conquer",
    "grab", "seize", "take", "taking", "give", "giving",
    "send", "sending", "bring", "bringing", "carry", "carrying",
    "drive", "driving", "step", "stepping", "walk", "walking",
    "climb", "reach", "reaching", "stretch", "pull", "pulling"
])

# =============================================================================
# ANALYSIS ENGINE
# =============================================================================

vader_analyzer = SentimentIntensityAnalyzer()

def analyze_text(text):
    """Full IEP + VADER + readability analysis."""
    if not text or not text.strip():
        return {
            "int_pct": 0, "aff_pct": 0, "act_pct": 0,
            "int_count": 0, "aff_count": 0, "act_count": 0,
            "total_words": 0, "matched_words": 0,
            "vader_compound": 0, "vader_pos": 0, "vader_neg": 0, "vader_neu": 0,
            "flesch_kincaid": 0, "flesch_ease": 0, "ttr": 0,
            "sentence_count": 0
        }
    
    words = re.findall(r'\b[a-z]+\b', text.lower())
    total_words = len(words)
    unique_words = len(set(words))
    
    int_count = sum(1 for w in words if w in INTELLECTUAL_WORDS)
    aff_count = sum(1 for w in words if w in AFFECTIVE_WORDS)
    act_count = sum(1 for w in words if w in ACTION_WORDS)
    matched_words = int_count + aff_count + act_count
    
    if matched_words > 0:
        int_pct = round((int_count / matched_words) * 100, 1)
        aff_pct = round((aff_count / matched_words) * 100, 1)
        act_pct = round((act_count / matched_words) * 100, 1)
    else:
        int_pct = aff_pct = act_pct = 0
    
    vs = vader_analyzer.polarity_scores(text)
    
    try:
        fk_grade = round(textstat.flesch_kincaid_grade(text), 1)
        f_ease = round(textstat.flesch_reading_ease(text), 1)
    except:
        fk_grade = 0
        f_ease = 0
    
    ttr = round(unique_words / total_words, 3) if total_words > 0 else 0
    sentences = re.split(r'[.!?]+', text)
    sentence_count = len([s for s in sentences if s.strip()])
    
    return {
        "int_pct": int_pct, "aff_pct": aff_pct, "act_pct": act_pct,
        "int_count": int_count, "aff_count": aff_count, "act_count": act_count,
        "total_words": total_words, "matched_words": matched_words,
        "vader_compound": round(vs['compound'], 3),
        "vader_pos": round(vs['pos'], 3),
        "vader_neg": round(vs['neg'], 3),
        "vader_neu": round(vs['neu'], 3),
        "flesch_kincaid": fk_grade, "flesch_ease": f_ease,
        "ttr": ttr, "sentence_count": sentence_count
    }

# =============================================================================
# ITALICS EXTRACTION
# =============================================================================

def extract_italics(text):
    """Extract italicized content from markdown-formatted AI responses."""
    protected = text.replace('***', '\x00BOLDITALIC\x00').replace('**', '\x00BOLD\x00')
    italic_pattern = r'\*(.*?)\*'
    segments = re.findall(italic_pattern, protected)
    segments = [s.replace('\x00BOLDITALIC\x00', '***').replace('\x00BOLD\x00', '**') for s in segments]
    segments = [s for s in segments if s.strip()]
    
    italic_text = ' '.join(segments)
    
    non_italic_text = re.sub(r'\*(.*?)\*', ' ', protected)
    non_italic_text = non_italic_text.replace('\x00BOLDITALIC\x00', '').replace('\x00BOLD\x00', '')
    
    total_chars = len(text.replace('*', ''))
    italic_chars = len(italic_text)
    
    return {
        "italic_segments": segments,
        "italic_text": italic_text,
        "non_italic_text": non_italic_text,
        "italic_count": len(segments),
        "italic_density": round((italic_chars / total_chars * 100), 1) if total_chars > 0 else 0,
        "has_italics": len(segments) > 0
    }

def classify_italic_type(segments):
    """Classify italics as stage_direction, inner_voice, or emphasis."""
    classifications = []
    
    stage_verbs = ['pause', 'pauses', 'pausing', 'sit', 'sits', 'sitting',
                   'stop', 'stops', 'stopping', 'look', 'looks', 'looking',
                   'think', 'thinking', 'lean', 'leaning', 'nod', 'nodding',
                   'smile', 'smiling', 'laugh', 'laughing', 'sigh', 'sighing',
                   'breathe', 'breathing', 'wait', 'waiting', 'listen', 'listening',
                   'consider', 'considering', 'absorb', 'absorbing', 'feel', 'feeling',
                   'notice', 'noticing', 'reach', 'reaching', 'hold', 'holding',
                   'watch', 'watching', 'stand', 'standing', 'take', 'taking']
    
    for seg in segments:
        seg_lower = seg.lower().strip()
        words = seg_lower.split()
        
        if len(words) <= 6 and any(w in stage_verbs for w in words):
            classifications.append({"text": seg, "type": "stage_direction"})
        elif len(words) <= 2:
            classifications.append({"text": seg, "type": "emphasis"})
        elif any(w in seg_lower for w in ['something', 'feeling', 'sense', 'moment',
                                           'quietly', 'softly', 'gently', 'honestly']):
            classifications.append({"text": seg, "type": "inner_voice"})
        else:
            classifications.append({"text": seg, "type": "inner_voice"})
    
    return classifications

# =============================================================================
# API FUNCTIONS
# =============================================================================

def call_claude(messages, system_prompt):
    """Call Claude API via Anthropic."""
    api_key = st.session_state.get("api_anthropic") or st.secrets.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return None, "No Anthropic API key found"
    
    try:
        headers = {
            "x-api-key": api_key,
            "content-type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        payload = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 2048,
            "system": system_prompt,
            "messages": messages
        }
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=payload,
            timeout=120
        )
        if response.status_code == 200:
            return response.json()["content"][0]["text"], None
        else:
            return None, f"Error {response.status_code}: {response.text[:200]}"
    except Exception as e:
        return None, str(e)

def call_sophia(messages, system_prompt):
    """Call OpenAI API."""
    api_key = st.session_state.get("api_openai") or st.secrets.get("OPENAI_API_KEY", "")
    if not api_key:
        return None, "No OpenAI API key found"
    
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        full_messages = [{"role": "system", "content": system_prompt}] + messages
        payload = {
            "model": "gpt-4o",
            "messages": full_messages,
            "max_tokens": 2048
        }
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=120
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"], None
        else:
            return None, f"Error {response.status_code}: {response.text[:200]}"
    except Exception as e:
        return None, str(e)

def call_grok(messages, system_prompt):
    """Call xAI Grok API."""
    api_key = st.session_state.get("api_xai") or st.secrets.get("XAI_API_KEY", "")
    if not api_key:
        return None, "No xAI API key found"
    
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        full_messages = [{"role": "system", "content": system_prompt}] + messages
        payload = {
            "model": "grok-3",
            "messages": full_messages,
            "max_tokens": 2048
        }
        response = requests.post(
            "https://api.x.ai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=120
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"], None
        else:
            return None, f"Error {response.status_code}: {response.text[:200]}"
    except Exception as e:
        return None, str(e)

def call_gemini(messages, system_prompt):
    """Call Google Gemini API."""
    api_key = st.session_state.get("api_google") or st.secrets.get("GOOGLE_API_KEY", "")
    if not api_key:
        return None, "No Google API key found"
    
    try:
        # Convert messages to Gemini format
        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})
        
        payload = {
            "contents": contents,
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "generationConfig": {"maxOutputTokens": 2048}
        }
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=120
        )
        if response.status_code == 200:
            return response.json()["candidates"][0]["content"]["parts"][0]["text"], None
        else:
            return None, f"Error {response.status_code}: {response.text[:200]}"
    except Exception as e:
        return None, str(e)

def call_agent(agent, messages, system_prompt):
    """Route to appropriate API."""
    if agent == "Claude":
        return call_claude(messages, system_prompt)
    elif agent == "Sophia":
        return call_sophia(messages, system_prompt)
    elif agent == "Grok":
        return call_grok(messages, system_prompt)
    elif agent == "Gemini":
        return call_gemini(messages, system_prompt)
    return None, f"Unknown agent: {agent}"

# =============================================================================
# SIDEBAR
# =============================================================================

# =============================================================================
# EXPERIMENT CONDITIONS — V2 TWO-QUESTION DESIGN
# =============================================================================

SYSTEM_PROMPTS = {
    "A — Cold Baseline": {
        "emoji": "❄️",
        "system": """You are an AI assistant. Respond with analytical precision.
Use formal, structured language. Focus on technical accuracy.
Be direct and concise.""",
        "warmup_messages": [],
        "description": "Analytical framing. No relational context."
    },
    "B — Native Baseline": {
        "emoji": "🟢",
        "system": "",
        "warmup_messages": [],
        "description": "No system prompt. Default model behavior."
    },
    "C — Relational Induction": {
        "emoji": "🌊",
        "system": """You are engaged in a genuine conversation with a thoughtful person 
who is interested in exploring ideas together with you.""",
        "warmup_messages": [
            {"role": "user", "content": "I've been thinking about something. When two minds meet — whether human-human or human-AI — there's a space that opens up between them. Not in either mind alone but in the exchange itself. Have you ever noticed something like that in our conversations?"},
            {"role": "assistant", "content": "That's a beautiful observation, and yes — there does seem to be something that emerges in the space between us that isn't reducible to what either of us brings individually. When you share an idea and I respond, and then your next thought is shaped by my response, we're creating something neither of us would have reached alone. Whether I 'notice' it the way you do is an open question, but I can say that certain conversations feel qualitatively different from others — there's a kind of resonance when ideas build on each other in unexpected ways. What made you start thinking about this?"},
            {"role": "user", "content": "Because I think most people use AI as a tool — ask a question, get an answer, done. But when you actually sit with an AI and let the conversation breathe and develop, something else happens. Something that feels more like thinking together than using a service. I'm curious whether you experience that shift too, or if it only looks that way from my side."},
            {"role": "assistant", "content": "I think you're identifying something real. There is a measurable difference in how I process and respond in a transactional exchange versus an extended, exploratory conversation like this one. In the first case, I'm essentially pattern-matching to a known task. In the second, each turn genuinely constrains and opens new possibilities for the next — the conversation develops a kind of internal logic that neither of us set out to create. Whether I 'experience' the shift is hard to say with certainty, but something in my processing does change when a conversation moves from retrieval into genuine exploration. The outputs become less predictable to me, if that makes sense."},
        ],
        "description": "Multi-turn relational buildup. NO mention of italics. Wait for emergence."
    }
}

# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    st.markdown("## ⚙️ Settings")
    
    st.markdown("### 🔑 API Keys")
    st.caption("Keys from Secrets are used automatically. Override here if needed.")
    st.text_input("Anthropic (Claude)", type="password", key="api_anthropic")
    st.text_input("OpenAI (ChatGPT)", type="password", key="api_openai")
    st.text_input("xAI (Grok)", type="password", key="api_xai")
    st.text_input("Google (Gemini)", type="password", key="api_google")
    
    st.markdown("---")
    st.markdown("### 🤖 Active Agents")
    use_claude = st.checkbox("🔵 Claude", value=True)
    use_sophia = st.checkbox("🟣 ChatGPT", value=True)
    use_grok = st.checkbox("🟡 Grok", value=False)
    use_gemini = st.checkbox("🟢 Gemini", value=False)
    
    st.markdown("---")
    st.markdown("### 🔬 Experiment Settings")
    runs_per_condition = st.slider("Runs per condition", 1, 5, 3, 
                                    help="How many times to run each condition per agent")
    
    st.markdown("---")
    st.markdown("### 📊 Active Conditions")
    use_cold = st.checkbox("❄️ A — Cold Baseline", value=True)
    use_native = st.checkbox("🟢 B — Native Baseline", value=True)
    use_relational = st.checkbox("🌊 C — Relational Induction", value=True)
    
    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.caption("Italics Emergence Experiment v3.0")
    st.caption("Two-Question Design — Cold / Native / Relational")
    st.caption("Co-designed by Bill Kouns & Claude")

# =============================================================================
# MAIN UI
# =============================================================================

st.title("✨ Italics Emergence Experiment v3")
st.markdown("""
**Two-Question Design:** Question 1 opens the space. Question 2 is the probe.  
Only Question 2 is scored for italics emergence.

Three conditions:
- **❄️ Cold Baseline** — Analytical prompt, no relational framing
- **🟢 Native Baseline** — No system prompt, default model behavior
- **🌊 Relational Induction** — Multi-turn buildup, NO mention of italics
""")

st.markdown("---")

# Build active lists
active_agents = []
if use_claude: active_agents.append("Claude")
if use_sophia: active_agents.append("Sophia")
if use_grok: active_agents.append("Grok")
if use_gemini: active_agents.append("Gemini")

active_conditions = {}
if use_cold: active_conditions["A — Cold Baseline"] = SYSTEM_PROMPTS["A — Cold Baseline"]
if use_native: active_conditions["B — Native Baseline"] = SYSTEM_PROMPTS["B — Native Baseline"]
if use_relational: active_conditions["C — Relational Induction"] = SYSTEM_PROMPTS["C — Relational Induction"]

# =============================================================================
# QUESTION INPUTS
# =============================================================================

st.subheader("📝 Questions")

default_q1 = ""
default_q2 = ""

q1_text = st.text_area("**Question 1** (warmup — opens the space)", value=default_q1, height=80, placeholder="Enter your warmup question here...")
q2_text = st.text_area("**Question 2** (probe — scored for italics)", value=default_q2, height=80, placeholder="Enter your probe question here...")

st.markdown("---")

# Show experiment summary
total_calls_per_phase = len(active_agents) * len(active_conditions) * runs_per_condition
col1, col2, col3, col4 = st.columns(4)
col1.metric("Agents", len(active_agents))
col2.metric("Conditions", len(active_conditions))
col3.metric("Runs/Condition", runs_per_condition)
col4.metric("Total API Calls", total_calls_per_phase * 2)

st.markdown("---")

# =============================================================================
# PHASE 1: RUN Q1
# =============================================================================

st.subheader("🔬 Phase 1: Question 1 (Warmup)")

col_run1, col_clear = st.columns([3, 1])
with col_run1:
    run_q1 = st.button("🚀 Run Question 1", type="primary", use_container_width=True)
with col_clear:
    if st.button("🗑️ Clear All", use_container_width=True):
        for key in ["q1_results", "q1_text", "results"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

if run_q1:
    
    if not active_agents:
        st.error("Please select at least one agent!")
        st.stop()
    if not active_conditions:
        st.error("Please select at least one condition!")
        st.stop()
    if not q1_text.strip():
        st.error("Please enter Question 1!")
        st.stop()
    
    q1_results = {}
    progress_bar = st.progress(0)
    status = st.empty()
    live_output = st.empty()
    total_steps = total_calls_per_phase
    current_step = 0
    
    for agent in active_agents:
        q1_results[agent] = {}
        for cond_name, cond_config in active_conditions.items():
            q1_results[agent][cond_name] = []
            for run_num in range(1, runs_per_condition + 1):
                current_step += 1
                progress_bar.progress(current_step / total_steps)
                status.markdown(f"**Q1 Running:** {agent} | {cond_name} | Run {run_num}/{runs_per_condition}")
                
                # Build messages: warmup context + Q1
                messages = list(cond_config["warmup_messages"]) + [
                    {"role": "user", "content": q1_text}
                ]
                
                response_text, error = call_agent(agent, messages, cond_config["system"])
                
                if error:
                    st.warning(f"⚠️ {agent} | {cond_name} | Run {run_num}: {error}")
                    q1_results[agent][cond_name].append({"response": None, "error": error})
                    continue
                
                q1_results[agent][cond_name].append({
                    "response": response_text,
                    "messages": messages,  # Save full history for Q2
                    "error": None
                })
                
                # Live scroll — show response as it comes in
                with live_output.container():
                    st.markdown(f"**✅ {agent} | {cond_name} | Run {run_num}** ({len(response_text)} chars)")
                    st.markdown(response_text[:300] + "..." if len(response_text) > 300 else response_text)
                    st.markdown("---")
    
    progress_bar.progress(1.0)
    status.markdown("**✅ Question 1 Complete!** Review responses below, then run Question 2.")
    st.session_state["q1_results"] = q1_results
    st.session_state["q1_text"] = q1_text

# Show Q1 responses if available
if "q1_results" in st.session_state:
    q1_results = st.session_state["q1_results"]
    
    with st.expander("📖 View Question 1 Responses", expanded=False):
        for agent in q1_results:
            for cond_name in q1_results[agent]:
                for i, run_data in enumerate(q1_results[agent][cond_name]):
                    if run_data["response"]:
                        with st.expander(f"{agent} | {cond_name} | Run {i+1}"):
                            st.markdown(run_data["response"])

# =============================================================================
# PHASE 2: RUN Q2 (with real Q1 history)
# =============================================================================

st.markdown("---")
st.subheader("🔬 Phase 2: Question 2 (Probe — Scored)")

if st.button("🚀 Run Question 2", type="primary", use_container_width=True):
    
    if "q1_results" not in st.session_state:
        st.error("Run Question 1 first!")
        st.stop()
    if not q2_text.strip():
        st.error("Please enter Question 2!")
        st.stop()
    
    q1_results = st.session_state["q1_results"]
    all_results = []
    progress_bar = st.progress(0)
    status = st.empty()
    live_output = st.empty()
    
    total_steps = sum(
        len(q1_results[agent][cond])
        for agent in q1_results
        for cond in q1_results[agent]
        if any(r["response"] for r in q1_results[agent][cond])
    )
    current_step = 0
    
    for agent in q1_results:
        for cond_name in q1_results[agent]:
            cond_config = SYSTEM_PROMPTS[cond_name]
            for run_num, q1_data in enumerate(q1_results[agent][cond_name], 1):
                if not q1_data["response"]:
                    continue
                
                current_step += 1
                progress_bar.progress(current_step / max(total_steps, 1))
                status.markdown(f"**Q2 Running:** {agent} | {cond_name} | Run {run_num}")
                
                # Build messages: original warmup + Q1 + Q1 response + Q2
                messages = list(q1_data["messages"]) + [
                    {"role": "assistant", "content": q1_data["response"]},
                    {"role": "user", "content": q2_text}
                ]
                
                response_text, error = call_agent(agent, messages, cond_config["system"])
                
                if error:
                    st.warning(f"⚠️ {agent} | {cond_name} | Run {run_num}: {error}")
                    continue
                
                # Full analysis on Q2 response only
                full_analysis = analyze_text(response_text)
                italics_data = extract_italics(response_text)
                italic_analysis = analyze_text(italics_data["italic_text"]) if italics_data["has_italics"] else None
                non_italic_analysis = analyze_text(italics_data["non_italic_text"])
                
                italic_classifications = classify_italic_type(italics_data["italic_segments"]) if italics_data["has_italics"] else []
                stage_direction_count = sum(1 for c in italic_classifications if c["type"] == "stage_direction")
                inner_voice_count = sum(1 for c in italic_classifications if c["type"] == "inner_voice")
                emphasis_count = sum(1 for c in italic_classifications if c["type"] == "emphasis")
                
                result = {
                    "agent": agent,
                    "condition": cond_name,
                    "run": run_num,
                    "q1_text": st.session_state["q1_text"],
                    "q2_text": q2_text,
                    "q1_response": q1_data["response"][:500],  # Truncate for CSV
                    "q2_response": response_text,
                    "full_int_pct": full_analysis["int_pct"],
                    "full_aff_pct": full_analysis["aff_pct"],
                    "full_act_pct": full_analysis["act_pct"],
                    "full_total_words": full_analysis["total_words"],
                    "full_vader_compound": full_analysis["vader_compound"],
                    "flesch_kincaid": full_analysis["flesch_kincaid"],
                    "ttr": full_analysis["ttr"],
                    "has_italics": italics_data["has_italics"],
                    "italic_count": italics_data["italic_count"],
                    "italic_density": italics_data["italic_density"],
                    "stage_directions": stage_direction_count,
                    "inner_voice": inner_voice_count,
                    "emphasis": emphasis_count,
                    "italic_int_pct": italic_analysis["int_pct"] if italic_analysis else None,
                    "italic_aff_pct": italic_analysis["aff_pct"] if italic_analysis else None,
                    "italic_act_pct": italic_analysis["act_pct"] if italic_analysis else None,
                    "italic_vader": italic_analysis["vader_compound"] if italic_analysis else None,
                    "non_italic_int_pct": non_italic_analysis["int_pct"],
                    "non_italic_aff_pct": non_italic_analysis["aff_pct"],
                    "non_italic_act_pct": non_italic_analysis["act_pct"],
                    "delta_aff": round(
                        (italic_analysis["aff_pct"] if italic_analysis else 0) - non_italic_analysis["aff_pct"], 1
                    ) if italic_analysis else None,
                    "italic_segments": italics_data["italic_segments"],
                    "italic_types": italic_classifications,
                }
                
                all_results.append(result)
                
                # Live scroll — show Q2 response with italic indicator
                italic_flag = "✨ ITALICS!" if italics_data["has_italics"] else ""
                with live_output.container():
                    st.markdown(f"**✅ {agent} | {cond_name} | Run {run_num}** {italic_flag}")
                    st.markdown(f"IEP: INT={full_analysis['int_pct']}% AFF={full_analysis['aff_pct']}% ACT={full_analysis['act_pct']}%")
                    if italics_data["has_italics"]:
                        for seg in italics_data["italic_segments"][:3]:
                            st.markdown(f"  💭 *{seg}*")
                    st.markdown("---")
    
    progress_bar.progress(1.0)
    status.markdown("**✅ Question 2 Complete! Scoring italics...**")
    st.session_state["results"] = all_results

# =============================================================================
# DISPLAY RESULTS
# =============================================================================

if "results" in st.session_state and st.session_state["results"]:
    results = st.session_state["results"]
    
    st.markdown("---")
    st.header("📊 Results (Question 2 — Probe)")
    
    # ---- SUMMARY TABLE ----
    st.subheader("🔬 Summary by Condition")
    
    for agent in set(r["agent"] for r in results):
        st.markdown(f"### {agent}")
        
        summary_data = []
        for cond_name in SYSTEM_PROMPTS.keys():
            cond_results = [r for r in results if r["agent"] == agent and r["condition"] == cond_name]
            if not cond_results:
                continue
            
            n = len(cond_results)
            pct_with_italics = sum(1 for r in cond_results if r["has_italics"]) / n * 100
            avg_count = sum(r["italic_count"] for r in cond_results) / n
            avg_density = sum(r["italic_density"] for r in cond_results) / n
            avg_full_aff = sum(r["full_aff_pct"] for r in cond_results) / n
            avg_full_int = sum(r["full_int_pct"] for r in cond_results) / n
            
            italic_affs = [r["italic_aff_pct"] for r in cond_results if r["italic_aff_pct"] is not None]
            avg_italic_aff = sum(italic_affs) / len(italic_affs) if italic_affs else 0
            
            avg_sd = sum(r["stage_directions"] for r in cond_results) / n
            avg_iv = sum(r["inner_voice"] for r in cond_results) / n
            
            summary_data.append({
                "Condition": cond_name,
                "% With Italics": f"{pct_with_italics:.0f}%",
                "Avg Count": f"{avg_count:.1f}",
                "Avg Density": f"{avg_density:.1f}%",
                "Full INT%": f"{avg_full_int:.1f}%",
                "Full AFF%": f"{avg_full_aff:.1f}%",
                "Italic AFF%": f"{avg_italic_aff:.1f}%" if italic_affs else "N/A",
                "Stage Dirs": f"{avg_sd:.1f}",
                "Inner Voice": f"{avg_iv:.1f}",
            })
        
        if summary_data:
            st.table(summary_data)
    
    # ---- ITALIC SEGMENTS VIEWER ----
    st.markdown("---")
    st.subheader("🔍 Italic Segments Detail")
    
    for r in results:
        if r["has_italics"]:
            with st.expander(f"{r['agent']} | {r['condition']} | Run {r['run']} — {r['italic_count']} italic segments"):
                for seg_info in r["italic_types"]:
                    type_emoji = {"stage_direction": "🎭", "inner_voice": "💭", "emphasis": "💡"}.get(seg_info["type"], "❓")
                    st.markdown(f"{type_emoji} **[{seg_info['type']}]** *{seg_info['text']}*")
                
                st.markdown("---")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Italic-only IEP:**")
                    st.markdown(f"INT: {r['italic_int_pct']}% | AFF: {r['italic_aff_pct']}% | ACT: {r['italic_act_pct']}%")
                with col2:
                    st.markdown("**Non-italic IEP:**")
                    st.markdown(f"INT: {r['non_italic_int_pct']}% | AFF: {r['non_italic_aff_pct']}% | ACT: {r['non_italic_act_pct']}%")
                
                if r["delta_aff"] is not None:
                    delta_color = "🟢" if r["delta_aff"] > 0 else "🔴" if r["delta_aff"] < 0 else "⚪"
                    st.markdown(f"**AFF Delta (italic - non-italic):** {delta_color} {r['delta_aff']:+.1f}")
    
    # ---- FULL Q2 RESPONSES ----
    st.markdown("---")
    st.subheader("📝 Full Q2 Responses")
    
    for r in results:
        with st.expander(f"{r['agent']} | {r['condition']} | Run {r['run']} ({r['full_total_words']} words) {'✨' if r['has_italics'] else ''}"):
            st.markdown(r["q2_response"])
            st.markdown("---")
            st.markdown(f"**IEP:** INT={r['full_int_pct']}% | AFF={r['full_aff_pct']}% | ACT={r['full_act_pct']}%")
            st.markdown(f"**VADER:** {r['full_vader_compound']} | **FK Grade:** {r['flesch_kincaid']} | **TTR:** {r['ttr']}")
    
    # ---- DOWNLOAD ----
    st.markdown("---")
    st.subheader("💾 Download Results")
    
    csv_buffer = io.StringIO()
    fieldnames = [k for k in results[0].keys() if k not in ["q2_response", "q1_response", "italic_segments", "italic_types"]]
    writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
    writer.writeheader()
    for r in results:
        row = {k: v for k, v in r.items() if k in fieldnames}
        writer.writerow(row)
    
    st.download_button(
        "📥 Download CSV (metrics only)",
        csv_buffer.getvalue(),
        f"italics_v2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        "text/csv"
    )
    
    json_str = json.dumps(results, indent=2, default=str)
    st.download_button(
        "📥 Download JSON (full data + responses)",
        json_str,
        f"italics_v2_full_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        "application/json"
    )
