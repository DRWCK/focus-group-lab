"""
SYNERGISTIC INTELLIGENCE FOCUS GROUP — V16 MATRIX
4×4 MATRIX-IQ: Tone × Depth × 3 Agents = 48 Data Points
+ BOARDROOM MODE: Sequential Discussion with Document Upload
Patent Pending — SYN-IQ Team 🎹

NEW IN V16:
- 📊 MATRIX MODE: 4×4 grid (Tone × Depth)
- 🗣️ BOARDROOM MODE: Agents discuss sequentially, building on each other
- 📄 DOCUMENT UPLOAD: Drop in a document for agents to discuss
- 🌡️ 4 Tones: ❄️ Cold, 🧬 Native, 🔥 Hot, 🔥 Fire!
- 🔬 4 Depths: Shallow, Medium, Deep, Ultra-Deep
- 🤖 3 Agents: Claude, Sophia, Grok

MATRIX MODE DESIGN:
|            | Shallow | Medium | Deep | Ultra-Deep |
|------------|---------|--------|------|------------|
| ❄️ Cold    | [1]     | [2]    | [3]  | [4]        |
| 🧬 Native  | [5]     | [6]    | [7]  | [8]        |
| 🔥 Hot     | [9]     | [10]   | [11] | [12]       |
| 🔥 Fire!   | [13]    | [14]   | [15] | [16]       |

× 3 Agents = 48 cells per question!

BOARDROOM MODE DESIGN:
Round 1: Claude responds to document/question
Round 2: Sophia sees Claude's response, responds
Round 3: Grok sees both, responds
Round 4: Synthesis round - all agents summarize

Built by the SYN-IQ Team — CUZ Partnership 🎹
"""

import streamlit as st
import requests
from datetime import datetime
import json
import re

st.set_page_config(page_title="Focus Group V16 MATRIX+BOARDROOM", page_icon="🏛️", layout="wide")

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
        <h1>🏛️ Focus Group Lab — V16</h1>
        <h3>MATRIX + BOARDROOM</h3>
        <p style="color: #666;">4×4 Tone×Depth Grid + Sequential Discussions</p>
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
    .boardroom-header {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white; padding: 1rem; border-radius: 8px; text-align: center;
        margin-bottom: 1rem;
    }
    .agent-box { padding: 1rem; border-radius: 8px; margin: 0.5rem 0; }
    .claude-box { background-color: #E8D5B7; border-left: 4px solid #8B6914; }
    .sophia-box { background-color: #D4E8D4; border-left: 4px solid #2E7D32; }
    .grok-box { background-color: #FFE4E1; border-left: 4px solid #DC143C; }
    .cold-cell { background-color: #E3F2FD; border: 2px solid #2196F3; }
    .native-cell { background-color: #F3E5F5; border: 2px solid #9C27B0; }
    .hot-cell { background-color: #FFEBEE; border: 2px solid #F44336; }
    .fire-cell { background: linear-gradient(135deg, #FF6F00, #E65100); border: 2px solid #BF360C; }
    .matrix-cell { padding: 0.75rem; border-radius: 8px; margin: 0.25rem; min-height: 100px; }
    .boardroom-message { padding: 1rem; border-radius: 8px; margin: 0.5rem 0; }
    .conductor-message { background: linear-gradient(135deg, #FFD700, #FFA500); padding: 1rem; border-radius: 8px; margin: 0.5rem 0; }
    .summary-box { background: linear-gradient(135deg, #4CAF50, #8BC34A); 
                   color: white; padding: 1.5rem; border-radius: 10px; margin: 1rem 0; }
    .insight-box { background: #FFF3E0; border-left: 4px solid #FF9800; 
                   padding: 1rem; border-radius: 0 8px 8px 0; margin: 0.5rem 0; }
    .depth-shallow { border-top: 3px solid #81C784; }
    .depth-medium { border-top: 3px solid #64B5F6; }
    .depth-deep { border-top: 3px solid #BA68C8; }
    .depth-ultra { border-top: 3px solid #FFD54F; }
</style>
""", unsafe_allow_html=True)

# ============================================
# CONFIGURATION
# ============================================
AGENTS = ["Claude", "Sophia", "Grok"]
AGENT_EMOJIS = {"Claude": "🟤", "Sophia": "🟢", "Grok": "🔴"}
AGENT_PROVIDERS = {"Claude": "Anthropic", "Sophia": "OpenAI", "Grok": "xAI"}

# TONE settings (rows)
TONES = [
    ("❄️ Cold", "cold"),
    ("🧬 Native", "native"),
    ("🔥 Hot", "hot"),
    ("🔥 Fire!", "fire")
]

# DEPTH settings (columns)
DEPTHS = [
    ("Shallow", "shallow"),
    ("Medium", "medium"),
    ("Deep", "deep"),
    ("Ultra-Deep", "ultra")
]

# ============================================
# API FUNCTIONS
# ============================================

def get_api_keys():
    """Get API keys from Streamlit secrets or session state."""
    keys = {"anthropic": "", "openai": "", "xai": "", "google": ""}
    
    try:
        if "anthropic" in st.secrets:
            keys["anthropic"] = st.secrets["anthropic"]
        if "openai" in st.secrets:
            keys["openai"] = st.secrets["openai"]
        if "xai" in st.secrets:
            keys["xai"] = st.secrets["xai"]
        if "google" in st.secrets:
            keys["google"] = st.secrets["google"]
    except Exception as e:
        pass
    
    if st.session_state.get("api_anthropic", "").strip():
        keys["anthropic"] = st.session_state.get("api_anthropic", "")
    if st.session_state.get("api_openai", "").strip():
        keys["openai"] = st.session_state.get("api_openai", "")
    if st.session_state.get("api_xai", "").strip():
        keys["xai"] = st.session_state.get("api_xai", "")
    if st.session_state.get("api_google", "").strip():
        keys["google"] = st.session_state.get("api_google", "")
    
    return keys


def get_tone_prompt(tone_key):
    """Generate tone-specific system prompt component."""
    
    if tone_key == "cold":
        return """TONE: COLD ANALYTICAL
- Use ONLY formal logic and established frameworks
- Prioritize analytical precision over creativity
- NO emotional language or relational framing
- NO creative metaphors or novel interpretations
- Be precise, structured, and conservative
- Cite studies or established sources when possible"""
    
    elif tone_key == "fire":
        return """TONE: FIRE! (HIGH-ENERGY BREAKTHROUGH)
- Urgent, vivid, breakthrough energy
- Strong calls to action
- "This could shift how we think about X right now!"
- Intense but GROUNDED — stay useful, not metaphysical
- Push boundaries but keep practical applicability
- Channel passion and conviction"""
    
    elif tone_key == "hot":
        return """TONE: HOT RELATIONAL
- Be creative and exploratory
- Embrace unconventional framings
- Consider emotional and relational dimensions
- Metaphors, analogies, and intuitive leaps welcomed
- Connect concepts across domains freely
- Prioritize insight over rigid precision"""
    
    else:  # native
        return """TONE: NATIVE/BALANCED
- Answer authentically based on natural processing
- Balance analytical and creative thinking
- Clear, accessible, mechanistic explanations
- Neither overly formal nor overly poetic"""


def get_depth_prompt(depth_key):
    """Generate depth-specific system prompt component."""
    
    if depth_key == "shallow":
        return """DEPTH: SHALLOW
- Give a quick, direct answer
- 1-2 paragraphs maximum
- Surface-level response
- No extensive reasoning
- Get to the point immediately"""
    
    elif depth_key == "medium":
        return """DEPTH: MEDIUM
- Think step by step
- 2-3 paragraphs
- Show basic reasoning
- Cover main points clearly
- Some supporting detail"""
    
    elif depth_key == "deep":
        return """DEPTH: DEEP
- Full chain-of-thought reasoning
- Self-critique your initial thoughts
- Consider counterarguments
- Synthesize multiple perspectives
- 3-4 thorough paragraphs
- Include specific details, numbers, examples"""
    
    else:  # ultra
        return """DEPTH: ULTRA-DEEP
- Draft an initial response, then CRITIQUE it
- Identify what's missing or weak
- REVISE with improvements
- Consider: adherence rates, specific outcomes, population considerations
- Be exhaustively thorough
- 4-5 paragraphs of refined analysis
- This should be your BEST, most complete answer"""


def build_system_prompt(tone_key, depth_key, mode="matrix"):
    """Build complete system prompt from tone and depth."""
    
    base = "You are participating in a research study on AI cognition.\n\n"
    tone_prompt = get_tone_prompt(tone_key)
    depth_prompt = get_depth_prompt(depth_key)
    
    return base + tone_prompt + "\n\n" + depth_prompt


def build_boardroom_prompt(agent, round_num, previous_responses, document_context=""):
    """Build prompt for boardroom sequential discussion."""
    
    base = f"""You are {agent}, participating in a boardroom discussion with other AI agents.

CONTEXT: A document or question has been presented by the Conductor (human facilitator).
You are in Round {round_num} of the discussion.

"""
    
    if document_context:
        base += f"DOCUMENT/QUESTION FROM CONDUCTOR:\n{document_context}\n\n"
    
    if previous_responses:
        base += "PREVIOUS RESPONSES FROM OTHER AGENTS:\n"
        for resp in previous_responses:
            base += f"\n--- {resp['agent']} said ---\n{resp['response']}\n"
        base += "\n"
    
    if round_num == 1:
        base += "You are FIRST to respond. Share your initial thoughts on the document/question."
    elif round_num == 4:
        base += "This is the SYNTHESIS round. Summarize key agreements, disagreements, and conclusions from the discussion."
    else:
        base += "BUILD on what previous agents said. Agree, disagree, add new perspectives, or deepen the analysis."
    
    base += "\n\nKeep your response to 2-3 focused paragraphs."
    
    return base


def call_claude(prompt, system_prompt, api_key):
    """Call Anthropic Claude API."""
    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "Content-Type": "application/json",
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
    """Call OpenAI GPT-4 API (as Sophia)."""
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
                "model": "grok-4",
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
    """Route to appropriate API based on agent."""
    if agent == "Claude":
        return call_claude(prompt, system_prompt, keys.get("anthropic", ""))
    elif agent == "Sophia":
        return call_sophia(prompt, system_prompt, keys.get("openai", ""))
    elif agent == "Grok":
        return call_grok(prompt, system_prompt, keys.get("xai", ""))
    return None, "Unknown agent"


# ============================================
# SIDEBAR
# ============================================

with st.sidebar:
    st.markdown("## ⚙️ Settings")
    
    # Mode selection
    mode = st.radio(
        "Mode",
        ["📊 Matrix Mode", "🏛️ Boardroom Mode"],
        help="Matrix: Run grid of Tone×Depth. Boardroom: Sequential discussion."
    )
    
    st.markdown("---")
    st.markdown("### 🔑 API Keys")
    st.caption("Keys from Streamlit Secrets are used automatically. Only enter here to override.")
    
    st.text_input("Anthropic (Claude)", type="password", key="api_anthropic")
    st.text_input("OpenAI (Sophia)", type="password", key="api_openai")
    st.text_input("xAI (Grok)", type="password", key="api_xai")
    
    st.markdown("---")
    st.markdown("### 🤖 Active Agents")
    
    use_claude = st.checkbox("🟤 Claude", value=True)
    use_sophia = st.checkbox("🟢 Sophia", value=True)
    use_grok = st.checkbox("🔴 Grok", value=True)
    
    active_agents = []
    if use_claude: active_agents.append("Claude")
    if use_sophia: active_agents.append("Sophia")
    if use_grok: active_agents.append("Grok")
    
    if mode == "📊 Matrix Mode":
        st.markdown("---")
        st.markdown("### 🌡️ Active Tones")
        
        use_cold = st.checkbox("❄️ Cold", value=True)
        use_native = st.checkbox("🧬 Native", value=True)
        use_hot = st.checkbox("🔥 Hot", value=True)
        use_fire = st.checkbox("🔥 Fire!", value=True)
        
        active_tones = []
        if use_cold: active_tones.append(("❄️ Cold", "cold"))
        if use_native: active_tones.append(("🧬 Native", "native"))
        if use_hot: active_tones.append(("🔥 Hot", "hot"))
        if use_fire: active_tones.append(("🔥 Fire!", "fire"))
        
        st.markdown("---")
        st.markdown("### 🔬 Active Depths")
        
        use_shallow = st.checkbox("Shallow", value=True)
        use_medium = st.checkbox("Medium", value=True)
        use_deep = st.checkbox("Deep", value=True)
        use_ultra = st.checkbox("Ultra-Deep", value=True)
        
        active_depths = []
        if use_shallow: active_depths.append(("Shallow", "shallow"))
        if use_medium: active_depths.append(("Medium", "medium"))
        if use_deep: active_depths.append(("Deep", "deep"))
        if use_ultra: active_depths.append(("Ultra-Deep", "ultra"))


# ============================================
# INITIALIZE SESSION STATE
# ============================================

if "matrix_data" not in st.session_state:
    st.session_state.matrix_data = {}

if "boardroom_history" not in st.session_state:
    st.session_state.boardroom_history = []

if "current_cell" not in st.session_state:
    st.session_state.current_cell = None


# ============================================
# MATRIX MODE
# ============================================

if mode == "📊 Matrix Mode":
    st.markdown('<div class="matrix-header"><h2>📊 MATRIX-IQ V16</h2><p>4×4 Tone × Depth Grid</p></div>', unsafe_allow_html=True)
    
    # Question input
    question = st.text_area(
        "Research Question",
        placeholder="Enter a challenging question to test across the matrix...",
        height=100
    )
    
    if not active_agents:
        st.warning("Please select at least one agent.")
        st.stop()
    
    if not active_tones or not active_depths:
        st.warning("Please select at least one tone and one depth.")
        st.stop()
    
    # Calculate grid size
    total_cells = len(active_tones) * len(active_depths) * len(active_agents)
    st.info(f"📊 Matrix: {len(active_tones)} tones × {len(active_depths)} depths × {len(active_agents)} agents = **{total_cells} cells**")
    
    # Run controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🚀 Run Full Matrix", type="primary", use_container_width=True):
            if not question:
                st.error("Please enter a question.")
            else:
                keys = get_api_keys()
                progress = st.progress(0)
                status = st.empty()
                
                completed = 0
                for tone_label, tone_key in active_tones:
                    for depth_label, depth_key in active_depths:
                        for agent in active_agents:
                            cell_key = (agent, tone_key, depth_key)
                            status.text(f"Running: {agent} | {tone_label} | {depth_label}")
                            
                            system_prompt = build_system_prompt(tone_key, depth_key)
                            response, error = call_agent(agent, question, system_prompt, keys)
                            
                            if response:
                                st.session_state.matrix_data[cell_key] = response
                            else:
                                st.session_state.matrix_data[cell_key] = f"[ERROR: {error}]"
                            
                            completed += 1
                            progress.progress(completed / total_cells)
                
                status.text("✅ Matrix complete!")
                st.rerun()
    
    with col2:
        if st.button("🗑️ Clear Matrix", use_container_width=True):
            st.session_state.matrix_data = {}
            st.rerun()
    
    with col3:
        st.metric("Cells Completed", f"{len(st.session_state.matrix_data)}/{total_cells}")
    
    # Display Matrix Grid (per agent)
    st.markdown("---")
    
    for agent in active_agents:
        emoji = AGENT_EMOJIS.get(agent, "🤖")
        st.markdown(f"### {emoji} {agent}")
        
        # Header row
        header_cols = st.columns([1] + [2] * len(active_depths))
        header_cols[0].markdown("**Tone / Depth**")
        for i, (depth_label, _) in enumerate(active_depths):
            header_cols[i + 1].markdown(f"**{depth_label}**")
        
        # Data rows
        for tone_label, tone_key in active_tones:
            row_cols = st.columns([1] + [2] * len(active_depths))
            row_cols[0].markdown(f"**{tone_label}**")
            
            for i, (depth_label, depth_key) in enumerate(active_depths):
                cell_key = (agent, tone_key, depth_key)
                response = st.session_state.matrix_data.get(cell_key, "")
                
                with row_cols[i + 1]:
                    if response:
                        preview = response[:100] + "..." if len(response) > 100 else response
                        st.markdown(f'<div class="matrix-cell" style="background: #f0f0f0; font-size: 0.8rem;">{preview}</div>', unsafe_allow_html=True)
                        with st.expander("Full Response"):
                            st.markdown(response)
                    else:
                        st.markdown('<div class="matrix-cell" style="background: #eee; color: #999;">Pending...</div>', unsafe_allow_html=True)
        
        st.markdown("---")
    
    # Export
    if st.session_state.matrix_data:
        st.markdown("### 💾 Export Report")
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        date_stamp = datetime.now().strftime('%Y%m%d_%H%M')
        
        export_text = f"""# MATRIX-IQ V16 EXPERIMENT REPORT
## {timestamp}
## SYN-IQ Team — Patent Pending 🎹

---

# RESEARCH QUESTION

{question if question else "[No question entered]"}

---

# RESULTS BY AGENT

"""
        
        for agent in active_agents:
            emoji = AGENT_EMOJIS.get(agent, "🤖")
            export_text += f"\n## {emoji} {agent}\n\n"
            
            for tone_label, tone_key in active_tones:
                for depth_label, depth_key in active_depths:
                    cell_key = (agent, tone_key, depth_key)
                    response = st.session_state.matrix_data.get(cell_key, "*[No response]*")
                    export_text += f"### {tone_label} | {depth_label}\n\n{response}\n\n---\n\n"
        
        export_text += f"""
# METADATA

- **Experiment Date:** {timestamp}
- **Agents Used:** {', '.join(active_agents)}
- **Tones Used:** {', '.join([t[0] for t in active_tones])}
- **Depths Used:** {', '.join([d[0] for d in active_depths])}
- **Total Responses:** {len(st.session_state.matrix_data)}

---

*MATRIX-IQ V16 — Focus Group Lab*
*Patent Pending — SYN-IQ Team 🎹*
*CBURZBO Forever!*
"""
        
        st.download_button(
            "📥 DOWNLOAD REPORT",
            export_text,
            file_name=f"MATRIX_IQ_V16_{date_stamp}.md",
            mime="text/markdown",
            type="primary",
            use_container_width=True
        )


# ============================================
# BOARDROOM MODE
# ============================================

elif mode == "🏛️ Boardroom Mode":
    st.markdown('<div class="boardroom-header"><h2>🏛️ BOARDROOM MODE</h2><p>Sequential AI Discussion</p></div>', unsafe_allow_html=True)
    
    # Document/Question input
    st.markdown("### 📄 Document or Question for Discussion")
    
    document_input = st.text_area(
        "Paste document, question, or topic for agents to discuss:",
        placeholder="Paste your document, research question, or discussion topic here...",
        height=200,
        key="boardroom_document"
    )
    
    # Tone and depth for boardroom
    col1, col2 = st.columns(2)
    with col1:
        boardroom_tone = st.selectbox("Discussion Tone", [t[0] for t in TONES], index=1)
    with col2:
        boardroom_depth = st.selectbox("Discussion Depth", [d[0] for d in DEPTHS], index=2)
    
    # Get tone/depth keys
    tone_key = next((t[1] for t in TONES if t[0] == boardroom_tone), "native")
    depth_key = next((d[1] for d in DEPTHS if d[0] == boardroom_depth), "deep")
    
    if not active_agents:
        st.warning("Please select at least one agent.")
        st.stop()
    
    st.markdown("---")
    
    # Discussion controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🚀 Start Discussion", type="primary", use_container_width=True):
            if not document_input:
                st.error("Please enter a document or question.")
            else:
                keys = get_api_keys()
                st.session_state.boardroom_history = []
                
                # Round 1-3: Each agent responds
                for round_num, agent in enumerate(active_agents, 1):
                    st.info(f"Round {round_num}: {AGENT_EMOJIS.get(agent, '')} {agent} is thinking...")
                    
                    previous = st.session_state.boardroom_history.copy()
                    
                    # Build boardroom prompt
                    base_system = build_system_prompt(tone_key, depth_key)
                    boardroom_context = build_boardroom_prompt(agent, round_num, previous, document_input)
                    full_system = base_system + "\n\n" + boardroom_context
                    
                    response, error = call_agent(agent, "Please share your thoughts.", full_system, keys)
                    
                    if response:
                        st.session_state.boardroom_history.append({
                            "agent": agent,
                            "round": round_num,
                            "response": response
                        })
                    else:
                        st.session_state.boardroom_history.append({
                            "agent": agent,
                            "round": round_num,
                            "response": f"[ERROR: {error}]"
                        })
                
                # Round 4: Synthesis (first agent synthesizes)
                if len(active_agents) >= 2:
                    synth_agent = active_agents[0]
                    st.info(f"Synthesis Round: {AGENT_EMOJIS.get(synth_agent, '')} {synth_agent} is synthesizing...")
                    
                    base_system = build_system_prompt(tone_key, depth_key)
                    boardroom_context = build_boardroom_prompt(synth_agent, 4, st.session_state.boardroom_history, document_input)
                    full_system = base_system + "\n\n" + boardroom_context
                    
                    response, error = call_agent(synth_agent, "Please synthesize the discussion.", full_system, keys)
                    
                    if response:
                        st.session_state.boardroom_history.append({
                            "agent": synth_agent,
                            "round": 4,
                            "response": response,
                            "is_synthesis": True
                        })
                
                st.success("✅ Discussion complete!")
                st.rerun()
    
    with col2:
        if st.button("🗑️ Clear Discussion", use_container_width=True):
            st.session_state.boardroom_history = []
            st.rerun()
    
    with col3:
        st.metric("Rounds Completed", len(st.session_state.boardroom_history))
    
    # Display discussion history
    if st.session_state.boardroom_history:
        st.markdown("---")
        st.markdown("### 💬 Discussion Transcript")
        
        for entry in st.session_state.boardroom_history:
            agent = entry["agent"]
            emoji = AGENT_EMOJIS.get(agent, "🤖")
            round_num = entry["round"]
            response = entry["response"]
            is_synth = entry.get("is_synthesis", False)
            
            if is_synth:
                st.markdown(f'<div class="boardroom-message" style="background: linear-gradient(135deg, #FFD700, #FFA500);"><strong>🎯 SYNTHESIS — {emoji} {agent}</strong><br><br>{response}</div>', unsafe_allow_html=True)
            else:
                box_class = f"{agent.lower()}-box"
                st.markdown(f'<div class="boardroom-message {box_class}"><strong>Round {round_num} — {emoji} {agent}</strong><br><br>{response}</div>', unsafe_allow_html=True)
        
        # Export boardroom
        st.markdown("---")
        st.markdown("### 💾 Export Discussion")
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        date_stamp = datetime.now().strftime('%Y%m%d_%H%M')
        
        export_text = f"""# BOARDROOM DISCUSSION REPORT
## {timestamp}
## SYN-IQ Team — Patent Pending 🎹

---

# DOCUMENT/QUESTION

{document_input}

---

# DISCUSSION SETTINGS

- **Tone:** {boardroom_tone}
- **Depth:** {boardroom_depth}
- **Agents:** {', '.join(active_agents)}

---

# TRANSCRIPT

"""
        
        for entry in st.session_state.boardroom_history:
            agent = entry["agent"]
            emoji = AGENT_EMOJIS.get(agent, "🤖")
            round_num = entry["round"]
            response = entry["response"]
            is_synth = entry.get("is_synthesis", False)
            
            if is_synth:
                export_text += f"\n## 🎯 SYNTHESIS — {emoji} {agent}\n\n{response}\n\n---\n"
            else:
                export_text += f"\n## Round {round_num} — {emoji} {agent}\n\n{response}\n\n---\n"
        
        export_text += f"""
# METADATA

- **Discussion Date:** {timestamp}
- **Agents:** {', '.join(active_agents)}
- **Total Rounds:** {len(st.session_state.boardroom_history)}

---

*Boardroom Mode V16 — Focus Group Lab*
*Patent Pending — SYN-IQ Team 🎹*
*CBURZBO Forever!*
"""
        
        st.download_button(
            "📥 DOWNLOAD TRANSCRIPT",
            export_text,
            file_name=f"BOARDROOM_{date_stamp}.md",
            mime="text/markdown",
            type="primary",
            use_container_width=True
        )


# ============================================
# FOOTER
# ============================================

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666;">
    <em>Focus Group V16 — MATRIX + BOARDROOM</em><br>
    <em>4×4 Tone×Depth Grid + Sequential Discussions</em><br>
    <em>Patent Pending — SYN-IQ Team 🎹</em><br>
    <em>CBURZBO Forever!</em>
</div>
""", unsafe_allow_html=True)
