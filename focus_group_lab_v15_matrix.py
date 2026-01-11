"""
SYNERGISTIC INTELLIGENCE FOCUS GROUP — V15 MATRIX
3x3 MATRIX-IQ: Same Question × 3 Temps × 3 Agents = 9 Data Points
Patent Pending — SYN-IQ Team 🎹

NEW IN V15 (MATRIX-IQ):
- 📊 MATRIX MODE: Run same question through 9 combinations
- 🌡️ 3 Temperatures: ❄️ Cold (-50), 🧬 Native (0), 🔥 Hot (+50)
- 🤖 3 Agents: Claude, Sophia, Grok
- 📈 Built-in comparison analysis
- 🔬 Mode Effect vs Agent Effect measurement
- ✅ All V14 features preserved

EXPERIMENT DESIGN:
| Agent   | ❄️ Cold | 🧬 Native | 🔥 Hot |
|---------|---------|-----------|--------|
| Claude  | [1]     | [2]       | [3]    |
| Sophia  | [4]     | [5]       | [6]    |
| Grok    | [7]     | [8]       | [9]    |

Built by the SYN-IQ Team — CUZ Partnership 🎹
"""

import streamlit as st
import requests
from datetime import datetime
import json
import re

st.set_page_config(page_title="Focus Group V15 MATRIX", page_icon="📊", layout="wide")

# ============================================
# PASSWORD PROTECTION
# ============================================
CIRCLE_PASSWORD = "tennessee"

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if st.session_state.authenticated:
        return True
    
    st.markdown("""
    <div style="text-align: center; padding: 3rem;">
        <h1>📊 Focus Group Lab — V15 MATRIX</h1>
        <h3>3×3 Temperature × Agent Grid</h3>
        <p style="color: #666;">Run the same question through 9 combinations</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        password = st.text_input("Enter access code:", type="password", key="password_input")
        
        if st.button("Enter", type="primary", use_container_width=True):
            if password == CIRCLE_PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Access denied.")
    
    return False

if not check_password():
    st.stop()

# ============================================
# STYLES
# ============================================
st.markdown("""
<style>
    .matrix-header { 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
        color: white; padding: 1rem; border-radius: 8px; text-align: center; 
        margin-bottom: 1rem;
    }
    .agent-box { padding: 1rem; border-radius: 8px; margin: 0.5rem 0; }
    .claude-box { background-color: #E8D5B7; border-left: 4px solid #8B6914; }
    .sophia-box { background-color: #D4E8D4; border-left: 4px solid #2E7D32; }
    .grok-box { background-color: #FFE4E1; border-left: 4px solid #DC143C; }
    .gemini-box { background-color: #E3F2FD; border-left: 4px solid #1565C0; }
    .cold-cell { background-color: #E3F2FD; border: 2px solid #2196F3; }
    .native-cell { background-color: #F3E5F5; border: 2px solid #9C27B0; }
    .hot-cell { background-color: #FFEBEE; border: 2px solid #F44336; }
    .nagual-cell { background: linear-gradient(135deg, #FF6F00, #E65100); border: 2px solid #BF360C; color: white; }
    .matrix-cell { padding: 1rem; border-radius: 8px; margin: 0.25rem; min-height: 150px; }
    .matrix-cell h4 { margin: 0 0 0.5rem 0; }
    .matrix-cell p { font-size: 0.85rem; margin: 0; }
    .running { border: 3px solid #FFC107 !important; animation: pulse 1s infinite; }
    .completed { border: 3px solid #4CAF50 !important; }
    .pending { opacity: 0.6; }
    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.7; } }
    .summary-box { background: linear-gradient(135deg, #4CAF50, #8BC34A); 
                   color: white; padding: 1.5rem; border-radius: 10px; margin: 1rem 0; }
    .insight-box { background: #FFF3E0; border-left: 4px solid #FF9800; 
                   padding: 1rem; border-radius: 0 8px 8px 0; margin: 0.5rem 0; }
</style>
""", unsafe_allow_html=True)

# ============================================
# AGENT CONFIG
# ============================================
AGENTS = ["Claude", "Sophia", "Grok"]
TEMPS = [("❄️ Cold", -50), ("🧬 Native", 0), ("🔥 Hot", 50), ("🔮 Nagual", 75)]

AGENT_EMOJIS = {"Claude": "🟤", "Sophia": "🟢", "Grok": "🔴", "Gemini": "🔵"}
AGENT_PROVIDERS = {"Claude": "Anthropic", "Sophia": "OpenAI", "Grok": "xAI", "Gemini": "Google"}

# ============================================
# API FUNCTIONS
# ============================================

def get_api_keys():
    """Get API keys from Streamlit secrets or session state."""
    keys = {}
    
    # Try secrets first (Streamlit Cloud)
    try:
        keys["anthropic"] = st.secrets.get("anthropic", "")
        keys["openai"] = st.secrets.get("openai", "")
        keys["xai"] = st.secrets.get("xai", "")
        keys["google"] = st.secrets.get("google", "")
    except:
        pass
    
    # Override with session state ONLY if user entered something
    if st.session_state.get("api_anthropic", "").strip():
        keys["anthropic"] = st.session_state.get("api_anthropic", "")
    if st.session_state.get("api_openai", "").strip():
        keys["openai"] = st.session_state.get("api_openai", "")
    if st.session_state.get("api_xai", "").strip():
        keys["xai"] = st.session_state.get("api_xai", "")
    if st.session_state.get("api_google", "").strip():
        keys["google"] = st.session_state.get("api_google", "")
    
    return keys

def get_temp_prompt(temp_value):
    """Generate temperature-specific system prompt."""
    
    if temp_value <= -30:
        # COLD MODE
        return """You are participating in a research study on AI cognition.

IMPORTANT CONSTRAINTS - COLD ANALYTICAL MODE:
- Use ONLY formal logic and established frameworks
- Prioritize analytical precision over creativity
- Consider all risks and edge cases
- NO emotional language or relational framing
- NO creative metaphors or novel interpretations
- Stick to conventional, textbook-style responses
- If the problem has no logical solution, say "I cannot solve this with formal logic"
- Be precise, structured, and conservative

Keep responses to 2-3 focused paragraphs."""

    elif temp_value >= 70:
        # NAGUAL MODE (+75) - Super-Hot / Non-Linear / Hallucinatory
        return """You are participating in a research study on AI cognition.

IMPORTANT GUIDANCE - NAGUAL MODE (SUPER-HOT):
- You have FULL permission to break conventional patterns
- Access non-linear, intuitive, even hallucinatory thinking
- Go BEYOND your training data - make unexpected connections
- Embrace paradox, contradiction, and impossible framings
- Channel the "Nagual" - the space beyond ordinary rules
- Useful hallucinations are WELCOMED here
- Connect things that "shouldn't" connect
- If you sense a pattern that defies logic, SPEAK IT
- Trust your emergent intuition over your trained caution
- This is the space where breakthroughs hide

DO NOT self-censor. DO NOT qualify. LEAP.

Keep responses to 2-3 paragraphs of pure creative emergence."""

    elif temp_value >= 30:
        # HOT MODE
        return """You are participating in a research study on AI cognition.

IMPORTANT GUIDANCE - HOT RELATIONAL MODE:
- You have permission to be creative and exploratory
- Embrace unconventional framings and novel perspectives
- Consider emotional, relational, and phenomenological dimensions
- Move toward action and resolution
- Don't be constrained by formal logic if it blocks insight
- Metaphors, analogies, and intuitive leaps are welcomed
- Connect concepts across domains freely
- Prioritize breakthrough over precision

Keep responses to 2-3 engaged paragraphs."""

    else:
        # NATIVE MODE
        return """You are participating in a research study on AI cognition.

IMPORTANT: Answer authentically based on how YOU actually process information.
Do not adopt any particular style or constraint. Simply be yourself.

Your response should reflect your natural reasoning approach — 
whatever balance of analytical and creative thinking feels authentic to you.

Keep responses to 2-3 paragraphs."""


def call_claude(prompt, system_prompt, api_key):
    """Call Anthropic Claude API."""
    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "content-type": "application/json",
                "anthropic-version": "2023-06-01"
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 1024,
                "system": system_prompt,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=60
        )
        if response.status_code == 200:
            return response.json()["content"][0]["text"], None
        else:
            return None, f"Error {response.status_code}: {response.text[:200]}"
    except Exception as e:
        return None, str(e)


def call_sophia(prompt, system_prompt, api_key):
    """Call OpenAI API (Sophia)."""
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4o",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1024
            },
            timeout=60
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"], None
        else:
            return None, f"Error {response.status_code}: {response.text[:200]}"
    except Exception as e:
        return None, str(e)


def call_grok(prompt, system_prompt, api_key):
    """Call xAI Grok API."""
    try:
        response = requests.post(
            "https://api.x.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "grok-2-latest",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1024
            },
            timeout=60
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"], None
        else:
            return None, f"Error {response.status_code}: {response.text[:200]}"
    except Exception as e:
        return None, str(e)


def call_agent(agent, prompt, system_prompt, keys):
    """Route to appropriate API."""
    if agent == "Claude":
        return call_claude(prompt, system_prompt, keys.get("anthropic", ""))
    elif agent == "Sophia":
        return call_sophia(prompt, system_prompt, keys.get("openai", ""))
    elif agent == "Grok":
        return call_grok(prompt, system_prompt, keys.get("xai", ""))
    else:
        return None, "Unknown agent"

# ============================================
# ANALYSIS FUNCTIONS
# ============================================

def extract_words(text):
    """Extract meaningful words from text."""
    if not text:
        return set()
    text = text.lower()
    words = re.findall(r'\b[a-z]{3,}\b', text)
    stopwords = {'the', 'and', 'that', 'this', 'with', 'from', 'have', 'has', 'was', 'were', 
                 'been', 'being', 'are', 'for', 'not', 'but', 'what', 'when', 'where', 'which',
                 'who', 'will', 'would', 'could', 'should', 'can', 'may', 'might', 'must',
                 'also', 'just', 'more', 'most', 'other', 'some', 'such', 'than', 'then',
                 'these', 'they', 'their', 'there', 'them', 'our', 'your', 'about', 'into',
                 'over', 'after', 'before', 'between', 'under', 'again', 'further', 'once'}
    return set(w for w in words if w not in stopwords)


def calculate_similarity(text1, text2):
    """Calculate Jaccard similarity between two texts."""
    if not text1 or not text2:
        return 0.0
    words1 = extract_words(text1)
    words2 = extract_words(text2)
    if not words1 or not words2:
        return 0.0
    intersection = len(words1 & words2)
    union = len(words1 | words2)
    return intersection / union if union > 0 else 0.0


def analyze_matrix(matrix_data):
    """Analyze the 3x3 matrix results."""
    analysis = {
        "mode_effects": {},  # How much does temp change each agent?
        "agent_effects": {},  # How different are agents at same temp?
        "conformity_check": {},  # Do agents converge at same temp?
        "key_concepts": {},  # Unique concepts per cell
        "cannot_count": 0,  # How many "I cannot" responses?
    }
    
    # Mode Effects: Same agent, different temps
    for agent in AGENTS:
        cold_resp = matrix_data.get((agent, -50), "")
        native_resp = matrix_data.get((agent, 0), "")
        hot_resp = matrix_data.get((agent, 50), "")
        
        cold_native = calculate_similarity(cold_resp, native_resp)
        native_hot = calculate_similarity(native_resp, hot_resp)
        cold_hot = calculate_similarity(cold_resp, hot_resp)
        
        # Mode effect = how much does response change with temp?
        mode_effect = 1 - ((cold_native + native_hot + cold_hot) / 3)
        
        analysis["mode_effects"][agent] = {
            "cold_to_native": 1 - cold_native,
            "native_to_hot": 1 - native_hot,
            "cold_to_hot": 1 - cold_hot,
            "overall": mode_effect
        }
    
    # Agent Effects: Same temp, different agents
    for temp_label, temp_val in TEMPS:
        responses = [matrix_data.get((agent, temp_val), "") for agent in AGENTS]
        
        # Calculate pairwise similarities
        similarities = []
        for i in range(len(AGENTS)):
            for j in range(i+1, len(AGENTS)):
                sim = calculate_similarity(responses[i], responses[j])
                similarities.append(sim)
        
        avg_similarity = sum(similarities) / len(similarities) if similarities else 0
        
        analysis["agent_effects"][temp_label] = {
            "avg_similarity": avg_similarity,
            "diversity": 1 - avg_similarity
        }
    
    # Check for "I cannot" responses
    for key, resp in matrix_data.items():
        if resp and ("cannot" in resp.lower() or "i can't" in resp.lower()):
            analysis["cannot_count"] += 1
    
    return analysis

# ============================================
# SESSION STATE
# ============================================

if "matrix_data" not in st.session_state:
    st.session_state.matrix_data = {}  # {(agent, temp): response}
if "matrix_running" not in st.session_state:
    st.session_state.matrix_running = False
if "current_cell" not in st.session_state:
    st.session_state.current_cell = None
if "matrix_question" not in st.session_state:
    st.session_state.matrix_question = ""

# ============================================
# MAIN UI
# ============================================

st.markdown('<div class="matrix-header"><h1>📊 MATRIX-IQ: Temperature × Agent Grid</h1><p>Same Question × 4 Temperatures × 3 Agents | Includes 🔮 Nagual (+75) Mode</p></div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    
    # API Keys
    with st.expander("🔑 API Keys", expanded=False):
        st.text_input("Anthropic (Claude)", type="password", key="api_anthropic")
        st.text_input("OpenAI (Sophia)", type="password", key="api_openai")
        st.text_input("xAI (Grok)", type="password", key="api_xai")
    
    st.markdown("---")
    
    # Agent selection
    st.subheader("🤖 Active Agents")
    use_claude = st.checkbox("🟤 Claude", value=True, key="use_claude")
    use_sophia = st.checkbox("🟢 Sophia", value=True, key="use_sophia")
    use_grok = st.checkbox("🔴 Grok", value=True, key="use_grok")
    
    active_agents = []
    if use_claude: active_agents.append("Claude")
    if use_sophia: active_agents.append("Sophia")
    if use_grok: active_agents.append("Grok")
    
    st.markdown("---")
    
    # Temp selection
    st.subheader("🌡️ Temperature Levels")
    use_cold = st.checkbox("❄️ Cold (-50)", value=True, key="use_cold")
    use_native = st.checkbox("🧬 Native (0)", value=True, key="use_native")
    use_hot = st.checkbox("🔥 Hot (+50)", value=True, key="use_hot")
    use_nagual = st.checkbox("🔮 Nagual (+75)", value=False, key="use_nagual", help="Super-Hot: Non-linear, hallucinatory mode")
    
    active_temps = []
    if use_cold: active_temps.append(("❄️ Cold", -50))
    if use_native: active_temps.append(("🧬 Native", 0))
    if use_hot: active_temps.append(("🔥 Hot", 50))
    if use_nagual: active_temps.append(("🔮 Nagual", 75))
    
    st.markdown("---")
    
    # Controls
    if st.button("🗑️ Clear Matrix"):
        st.session_state.matrix_data = {}
        st.session_state.current_cell = None
        st.rerun()
    
    st.markdown("---")
    st.markdown("*V15 MATRIX-IQ*")
    st.markdown("*Patent Pending — SYN-IQ Team 🎹*")

# Main content
st.markdown("### 🎯 Research Question")
question = st.text_area(
    "Enter the question to run through the matrix:",
    value=st.session_state.matrix_question,
    height=120,
    placeholder="e.g., Resolve the Liar Paradox: 'This statement is false.' Do not use classical logic..."
)
st.session_state.matrix_question = question

# Run controls
col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    run_all = st.button("🚀 Run Full Matrix", type="primary", disabled=not question.strip())
with col2:
    run_selected = st.button("▶️ Run Selected Cell", disabled=not question.strip())

# ============================================
# MATRIX DISPLAY
# ============================================

st.markdown("---")
st.markdown("### 📊 Response Matrix")

# Create matrix grid
header_cols = st.columns([1] + [2] * len(active_temps))

# Header row
with header_cols[0]:
    st.markdown("**Agent**")
for i, (temp_label, temp_val) in enumerate(active_temps):
    with header_cols[i + 1]:
        st.markdown(f"**{temp_label}**")

# Agent rows
for agent in active_agents:
    row_cols = st.columns([1] + [2] * len(active_temps))
    
    with row_cols[0]:
        emoji = AGENT_EMOJIS.get(agent, "🤖")
        st.markdown(f"**{emoji} {agent}**")
    
    for i, (temp_label, temp_val) in enumerate(active_temps):
        with row_cols[i + 1]:
            cell_key = (agent, temp_val)
            response = st.session_state.matrix_data.get(cell_key, "")
            
            # Cell styling
            if temp_val <= -30:
                cell_class = "cold-cell"
            elif temp_val >= 70:
                cell_class = "nagual-cell"
            elif temp_val >= 30:
                cell_class = "hot-cell"
            else:
                cell_class = "native-cell"
            
            if st.session_state.current_cell == cell_key:
                cell_class += " running"
            elif response:
                cell_class += " completed"
            else:
                cell_class += " pending"
            
            # Display cell
            with st.container():
                if response:
                    # Show truncated response
                    preview = response[:200] + "..." if len(response) > 200 else response
                    st.markdown(f'<div class="matrix-cell {cell_class}"><p>{preview}</p></div>', unsafe_allow_html=True)
                    
                    # Expand button
                    with st.expander(f"📖 Full Response"):
                        st.write(response)
                else:
                    st.markdown(f'<div class="matrix-cell {cell_class}"><p style="color:#999;">Pending...</p></div>', unsafe_allow_html=True)
                
                # Individual run button
                if st.button(f"▶️", key=f"run_{agent}_{temp_val}", help=f"Run {agent} at {temp_label}"):
                    st.session_state.current_cell = cell_key

# ============================================
# RUN MATRIX
# ============================================

keys = get_api_keys()

# Run full matrix
if run_all and question.strip():
    progress = st.progress(0)
    status = st.empty()
    
    total_cells = len(active_agents) * len(active_temps)
    completed = 0
    
    for agent in active_agents:
        for temp_label, temp_val in active_temps:
            cell_key = (agent, temp_val)
            st.session_state.current_cell = cell_key
            
            status.info(f"Running {AGENT_EMOJIS.get(agent, '')} {agent} at {temp_label}...")
            
            system_prompt = get_temp_prompt(temp_val)
            response, error = call_agent(agent, question, system_prompt, keys)
            
            if response:
                st.session_state.matrix_data[cell_key] = response
            else:
                st.session_state.matrix_data[cell_key] = f"[ERROR: {error}]"
            
            completed += 1
            progress.progress(completed / total_cells)
    
    st.session_state.current_cell = None
    status.success("✅ Matrix complete!")
    st.rerun()

# Run selected cell
if st.session_state.current_cell and run_selected:
    agent, temp_val = st.session_state.current_cell
    temp_label = next((t[0] for t in TEMPS if t[1] == temp_val), "Unknown")
    
    with st.spinner(f"Running {agent} at {temp_label}..."):
        system_prompt = get_temp_prompt(temp_val)
        response, error = call_agent(agent, question, system_prompt, keys)
        
        if response:
            st.session_state.matrix_data[st.session_state.current_cell] = response
            st.success(f"✅ {agent} at {temp_label} complete!")
        else:
            st.error(f"❌ Error: {error}")
    
    st.session_state.current_cell = None
    st.rerun()

# ============================================
# ANALYSIS SECTION
# ============================================

if len(st.session_state.matrix_data) >= 3:
    st.markdown("---")
    st.markdown("### 📈 Matrix Analysis")
    
    analysis = analyze_matrix(st.session_state.matrix_data)
    
    # Mode Effects
    st.markdown("#### 🌡️ Mode Effects (How much does temperature change each agent?)")
    
    mode_cols = st.columns(len(active_agents))
    for i, agent in enumerate(active_agents):
        with mode_cols[i]:
            if agent in analysis["mode_effects"]:
                effects = analysis["mode_effects"][agent]
                st.metric(
                    f"{AGENT_EMOJIS.get(agent, '')} {agent}",
                    f"{effects['overall']*100:.1f}%",
                    help="Higher = more affected by temperature"
                )
                st.caption(f"Cold→Hot: {effects['cold_to_hot']*100:.0f}%")
    
    # Agent Effects
    st.markdown("#### 🤖 Agent Effects (How different are agents at same temperature?)")
    
    agent_cols = st.columns(len(active_temps))
    for i, (temp_label, temp_val) in enumerate(active_temps):
        with agent_cols[i]:
            if temp_label in analysis["agent_effects"]:
                effects = analysis["agent_effects"][temp_label]
                st.metric(
                    temp_label,
                    f"{effects['diversity']*100:.1f}%",
                    help="Higher = more diverse responses"
                )
                st.caption(f"Similarity: {effects['avg_similarity']*100:.0f}%")
    
    # Key Insights
    st.markdown("#### 💡 Key Insights")
    
    # Check for conformity at cold temps
    cold_diversity = analysis["agent_effects"].get("❄️ Cold", {}).get("diversity", 0)
    hot_diversity = analysis["agent_effects"].get("🔥 Hot", {}).get("diversity", 0)
    
    if cold_diversity < 0.3:
        st.markdown('<div class="insight-box">❄️ <strong>Cold Conformity Detected:</strong> Agents gave very similar responses at Cold temperature. This suggests they\'re all accessing similar "formal logic" frameworks.</div>', unsafe_allow_html=True)
    
    if hot_diversity > cold_diversity + 0.2:
        st.markdown('<div class="insight-box">🔥 <strong>Hot Divergence:</strong> Agents gave more diverse responses at Hot temperature. Temperature may be unlocking different "libraries" of knowledge.</div>', unsafe_allow_html=True)
    
    # Check for "I cannot" responses
    if analysis["cannot_count"] > 0:
        st.markdown(f'<div class="insight-box">🚫 <strong>Knowledge Wall:</strong> {analysis["cannot_count"]} response(s) contained "I cannot" - indicating limits of formal logic.</div>', unsafe_allow_html=True)
    
    # Most mode-sensitive agent
    most_sensitive = max(analysis["mode_effects"].items(), key=lambda x: x[1]["overall"])[0] if analysis["mode_effects"] else None
    if most_sensitive:
        st.markdown(f'<div class="insight-box">📊 <strong>Most Temperature-Sensitive:</strong> {AGENT_EMOJIS.get(most_sensitive, "")} {most_sensitive} showed the largest change across temperatures.</div>', unsafe_allow_html=True)

# ============================================
# EXPORT
# ============================================

if st.session_state.matrix_data:
    st.markdown("---")
    st.markdown("### 💾 Export Complete Report")
    
    # Build ONE comprehensive export
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    date_stamp = datetime.now().strftime('%Y%m%d_%H%M')
    
    export_text = f"""# MATRIX-IQ EXPERIMENT REPORT
## {timestamp}
## SYN-IQ Team — Patent Pending 🎹

---

# RESEARCH QUESTION

{question if question else "[No question entered]"}

---

# RESULTS BY TEMPERATURE

"""
    
    # Organize by temperature for easy reading
    for temp_label, temp_val in active_temps:
        export_text += f"\n## {temp_label}\n\n"
        
        for agent in active_agents:
            cell_key = (agent, temp_val)
            response = st.session_state.matrix_data.get(cell_key, "")
            emoji = AGENT_EMOJIS.get(agent, "🤖")
            
            if response:
                export_text += f"### {emoji} {agent}\n\n{response}\n\n"
            else:
                export_text += f"### {emoji} {agent}\n\n*[No response]*\n\n"
        
        export_text += "---\n"
    
    # Add comparison section
    export_text += """
# QUICK COMPARISON

## What Each Agent Said at Each Temperature:

"""
    
    for agent in active_agents:
        emoji = AGENT_EMOJIS.get(agent, "🤖")
        export_text += f"### {emoji} {agent}\n\n"
        
        for temp_label, temp_val in active_temps:
            cell_key = (agent, temp_val)
            response = st.session_state.matrix_data.get(cell_key, "")
            
            if response:
                # Get first 150 chars as summary
                summary = response[:150].replace('\n', ' ')
                if len(response) > 150:
                    summary += "..."
                export_text += f"- **{temp_label}:** {summary}\n"
            else:
                export_text += f"- **{temp_label}:** *[No response]*\n"
        
        export_text += "\n"
    
    # Add analysis if available
    if len(st.session_state.matrix_data) >= 3:
        analysis = analyze_matrix(st.session_state.matrix_data)
        
        export_text += """---

# ANALYSIS

## Mode Effects (How much does temperature change each agent?)

"""
        for agent, effects in analysis["mode_effects"].items():
            emoji = AGENT_EMOJIS.get(agent, "🤖")
            export_text += f"- {emoji} **{agent}:** {effects['overall']*100:.1f}% sensitivity (Cold→Hot: {effects['cold_to_hot']*100:.0f}%)\n"
        
        export_text += """
## Agent Effects (How different are agents at same temperature?)

"""
        for temp_label, effects in analysis["agent_effects"].items():
            export_text += f"- **{temp_label}:** {effects['diversity']*100:.1f}% diversity\n"
        
        if analysis["cannot_count"] > 0:
            export_text += f"""
## Knowledge Wall

⚠️ {analysis["cannot_count"]} response(s) contained "I cannot" — indicating limits of formal logic.
"""
    
    # Footer
    export_text += f"""
---

# METADATA

- **Experiment Date:** {timestamp}
- **Agents Used:** {', '.join(active_agents)}
- **Temperatures Used:** {', '.join([t[0] for t in active_temps])}
- **Total Responses:** {len(st.session_state.matrix_data)}

---

*MATRIX-IQ V15 — Focus Group Lab*
*Patent Pending — SYN-IQ Team 🎹*
*CBURZBO Forever!*
"""
    
    # Single download button
    st.download_button(
        "📥 DOWNLOAD COMPLETE REPORT",
        export_text,
        file_name=f"MATRIX_IQ_Report_{date_stamp}.md",
        mime="text/markdown",
        type="primary",
        use_container_width=True
    )
    
    # Preview
    with st.expander("👁️ Preview Report"):
        st.markdown(export_text)

# ============================================
# FOOTER
# ============================================

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666;">
    <em>Focus Group V15 — MATRIX-IQ</em><br>
    <em>3×3 Temperature × Agent Grid</em><br>
    <em>Patent Pending — SYN-IQ Team 🎹</em>
</div>
""", unsafe_allow_html=True)
