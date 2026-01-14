"""
SYNERGISTIC INTELLIGENCE FOCUS GROUP — V20 FULL BEAST
Patent Pending — SYN-IQ Team 🎹

NEW IN V20:
- ⚡ CONTRAST SLIDER: Agreement ↔ Dissonance (-100 to +100)
- 💪 COACHING SLIDER: Challenger ↔ Encourager (-100 to +100)  
- 🔄 PERSIST TOGGLE: "Keep digging deeper" mode
- 📚 KB LIMIT SLIDER: 15K → 100K characters
- 🔀 SHARED/INDIVIDUAL KB: Same docs or unique per agent
- 📁 3 UPLOAD ZONES: One per agent
- 📑 AGENT TABS: Access agents individually
- 💬 PRIVATE CHANNEL: Send to one agent only
- 📏 INCREASED MAX_TOKENS: 2048 (was 1024)
- 🔄 DEPTH 4 FIX: Integrated analysis (not draft-critique-revise)

MODES:
- 🗣️ Simple Mode: Parallel responses
- 📊 Matrix Mode: Tone × Depth grid
- 🏛️ Boardroom Mode: Sequential with synthesis

Built by the SYN-IQ Team — CUZ Partnership 🎹
CBURZBO Forever!
"""

import streamlit as st
import requests
from datetime import datetime
import json

st.set_page_config(page_title="Focus Group V20", page_icon="🎹", layout="wide")

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
        <h1>🎹 Focus Group Lab — V20</h1>
        <h3>THE FULL BEAST</h3>
        <p style="color: #666;">Contrast • Coaching • Persist • Individual KB</p>
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
    .main-header { 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
        color: white; padding: 1rem; border-radius: 8px; text-align: center; 
        margin-bottom: 1rem;
    }
    .agent-box { padding: 1rem; border-radius: 8px; margin: 0.5rem 0; }
    .claude-box { background-color: #E8D5B7; border-left: 4px solid #8B6914; }
    .sophia-box { background-color: #D4E8D4; border-left: 4px solid #2E7D32; }
    .grok-box { background-color: #FFE4E1; border-left: 4px solid #DC143C; }
    .synthesis-box { background: linear-gradient(135deg, #FFD700, #FFA500); padding: 1rem; border-radius: 8px; }
    .private-box { background: #E3F2FD; border: 2px dashed #2196F3; padding: 1rem; border-radius: 8px; }
    .slider-label { font-size: 0.9rem; color: #666; margin-bottom: 0.25rem; }
    .persist-active { background: #C8E6C9; border: 2px solid #4CAF50; padding: 0.5rem; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# ============================================
# CONFIGURATION
# ============================================
AGENTS = ["Claude", "Sophia", "Grok"]
AGENT_EMOJIS = {"Claude": "🟤", "Sophia": "🟢", "Grok": "🔴"}
AGENT_PROVIDERS = {"Claude": "Anthropic", "Sophia": "OpenAI", "Grok": "xAI"}

TONES = [
    ("❄️ Cold", "cold"),
    ("🧬 Native", "native"),
    ("🔥 Hot", "hot"),
    ("🔥 Fire!", "fire")
]

DEPTHS = [
    ("Quick", "quick"),
    ("Moderate", "moderate"),
    ("Deep", "deep"),
    ("Ultra-Deep", "ultra")
]

# ============================================
# API FUNCTIONS
# ============================================

def get_api_keys():
    """Get API keys from Streamlit secrets or session state."""
    keys = {"anthropic": "", "openai": "", "xai": ""}
    
    try:
        if "anthropic" in st.secrets:
            keys["anthropic"] = st.secrets["anthropic"]
        if "openai" in st.secrets:
            keys["openai"] = st.secrets["openai"]
        if "xai" in st.secrets:
            keys["xai"] = st.secrets["xai"]
    except:
        pass
    
    if st.session_state.get("api_anthropic", "").strip():
        keys["anthropic"] = st.session_state.get("api_anthropic", "")
    if st.session_state.get("api_openai", "").strip():
        keys["openai"] = st.session_state.get("api_openai", "")
    if st.session_state.get("api_xai", "").strip():
        keys["xai"] = st.session_state.get("api_xai", "")
    
    return keys


def get_cognitive_prompt(cognitive_value):
    """Generate cognitive mode prompt from slider value (-100 to +100)."""
    
    if cognitive_value <= -50:
        return """COGNITIVE MODE: HIGHLY ANALYTICAL
- Use ONLY formal logic and established frameworks
- Prioritize precision over creativity
- NO emotional language or metaphors
- Be structured, systematic, conservative
- Cite established sources when possible"""
    
    elif cognitive_value <= 0:
        return """COGNITIVE MODE: ANALYTICAL-BALANCED
- Lean toward structured analysis
- Some flexibility for context
- Clear, methodical reasoning
- Moderate creativity within bounds"""
    
    elif cognitive_value <= 50:
        return """COGNITIVE MODE: BALANCED-INTUITIVE
- Balance analytical and creative thinking
- Allow metaphors and analogies
- Consider emotional dimensions
- Flexible but grounded"""
    
    else:
        return """COGNITIVE MODE: HIGHLY INTUITIVE
- Be creative and exploratory
- Embrace unconventional framings
- Metaphors, analogies, intuitive leaps welcomed
- Prioritize insight over rigid precision
- Connect concepts across domains freely"""


def get_contrast_prompt(contrast_value):
    """Generate contrast/dissonance prompt from slider value (-100 to +100)."""
    
    if contrast_value <= -50:
        return """CONTRAST MODE: DISSONANCE
- Challenge and critique prior contributions
- Find flaws, gaps, and weaknesses
- Play devil's advocate
- Push back on assumptions
- Force deeper examination through disagreement"""
    
    elif contrast_value < 50:
        return """CONTRAST MODE: NEUTRAL
- Respond naturally without forced agreement or disagreement
- Build on ideas where appropriate
- Challenge where warranted
- Balanced engagement"""
    
    else:
        return """CONTRAST MODE: AGREEMENT
- Build upon and support prior contributions
- Find common ground
- Extend and strengthen ideas
- Collaborative, constructive tone
- "Yes, and..." approach"""


def get_coaching_prompt(coaching_value):
    """Generate coaching style prompt from slider value (-100 to +100)."""
    
    if coaching_value <= -50:
        return """COACHING STYLE: CHALLENGER
- Push back and demand proof
- Express healthy skepticism
- Ask tough questions
- "Prove it" mentality
- Force rigorous justification"""
    
    elif coaching_value < 50:
        return """COACHING STYLE: BALANCED
- Mix of support and challenge
- Constructive criticism
- Acknowledge strengths while noting improvements
- Professional, balanced engagement"""
    
    else:
        return """COACHING STYLE: ENCOURAGER
- Support and affirm contributions
- Build confidence
- "You've got this" mentality
- Highlight strengths and potential
- Constructive, positive framing"""


def get_depth_prompt(depth_key):
    """Generate depth-specific prompt."""
    
    if depth_key == "quick":
        return """DEPTH: QUICK
- Give a direct, concise answer
- 1-2 paragraphs maximum
- Get to the point immediately
- No extensive reasoning needed"""
    
    elif depth_key == "moderate":
        return """DEPTH: MODERATE
- Think step by step
- 2-3 paragraphs
- Show basic reasoning
- Cover main points clearly"""
    
    elif depth_key == "deep":
        return """DEPTH: DEEP
- Full chain-of-thought reasoning
- Consider multiple perspectives
- 3-4 thorough paragraphs
- Include specific details and examples
- Address counterarguments"""
    
    else:  # ultra - FIXED: integrated analysis, not draft-critique-revise
        return """DEPTH: ULTRA-DEEP (INTEGRATED ANALYSIS)
- Provide comprehensive multi-dimensional analysis
- Integrate critical evaluation THROUGHOUT (not as separate draft/critique)
- Consider: multiple stakeholders, risks, opportunities, edge cases
- Be exhaustively thorough but coherent
- 4-5 paragraphs of refined, integrated analysis
- This should be your BEST, most complete answer"""


def get_persist_prompt(persist_enabled):
    """Generate persistence prompt if enabled."""
    
    if persist_enabled:
        return """PERSISTENCE MODE: ACTIVE
- Do NOT stop at your first answer
- After your initial response, ask yourself:
  * "What else? What am I missing?"
  * "What are the gaps in my analysis?"
  * "Go deeper - what haven't I considered?"
- Challenge your own response
- Add additional insights you may have missed
- Push beyond the obvious"""
    
    return ""


def build_system_prompt(agent, cognitive, contrast, coaching, depth_key, persist, knowledge_base=""):
    """Build complete system prompt from all parameters."""
    
    base = f"You are {agent}, participating in a focus group research study on AI cognition.\n\n"
    
    cognitive_prompt = get_cognitive_prompt(cognitive)
    contrast_prompt = get_contrast_prompt(contrast)
    coaching_prompt = get_coaching_prompt(coaching)
    depth_prompt = get_depth_prompt(depth_key)
    persist_prompt = get_persist_prompt(persist)
    
    full_prompt = base + cognitive_prompt + "\n\n" + contrast_prompt + "\n\n" + coaching_prompt + "\n\n" + depth_prompt
    
    if persist_prompt:
        full_prompt += "\n\n" + persist_prompt
    
    if knowledge_base:
        full_prompt += f"\n\n--- KNOWLEDGE BASE (Reference this in your response) ---\n{knowledge_base}\n--- END KNOWLEDGE BASE ---"
    
    return full_prompt


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
        base += "You are FIRST to respond. Share your initial thoughts."
    elif round_num >= 4:
        base += "This is the SYNTHESIS round. Summarize key agreements, disagreements, and conclusions."
    else:
        base += "BUILD on what previous agents said. Agree, disagree, add new perspectives, or deepen the analysis."
    
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
                "max_tokens": 2048,  # INCREASED from 1024
                "system": system_prompt,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=90
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
                "max_tokens": 2048  # INCREASED from 1024
            },
            timeout=90
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
                "model": "grok-3",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 2048  # INCREASED from 1024
            },
            timeout=90
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
    st.markdown("## ⚙️ V20 Control Panel")
    
    # Mode selection
    mode = st.radio(
        "Mode",
        ["🗣️ Simple Mode", "📊 Matrix Mode", "🏛️ Boardroom Mode"],
        help="Simple: Parallel. Matrix: Grid. Boardroom: Sequential."
    )
    
    st.markdown("---")
    
    # === NEW V20 SLIDERS ===
    st.markdown("### 🎚️ Cognitive Controls")
    
    cognitive = st.slider(
        "Cognitive Mode",
        -100, 100, 0,
        help="← Analytical | Intuitive →"
    )
    st.caption(f"{'🧠 Analytical' if cognitive < 0 else '💡 Intuitive' if cognitive > 0 else '⚖️ Balanced'}")
    
    contrast = st.slider(
        "Contrast Mode",
        -100, 100, 0,
        help="← Dissonance | Agreement →"
    )
    st.caption(f"{'⚡ Dissonance' if contrast < -25 else '🤝 Agreement' if contrast > 25 else '⚖️ Neutral'}")
    
    coaching = st.slider(
        "Coaching Mode", 
        -100, 100, 0,
        help="← Challenger | Encourager →"
    )
    st.caption(f"{'💪 Challenger' if coaching < -25 else '🌟 Encourager' if coaching > 25 else '⚖️ Balanced'}")
    
    depth_choice = st.selectbox("Depth", [d[0] for d in DEPTHS], index=2)
    depth_key = next((d[1] for d in DEPTHS if d[0] == depth_choice), "deep")
    
    st.markdown("---")
    
    # PERSIST Toggle
    persist = st.toggle("🔄 PERSIST Mode", value=False, help="Keep digging deeper")
    if persist:
        st.markdown('<div class="persist-active">PERSIST: Active — Agents will dig deeper</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # === KNOWLEDGE BASE ===
    st.markdown("### 📚 Knowledge Base")
    
    kb_limit = st.slider(
        "KB Limit (chars)",
        15000, 100000, 30000, step=5000,
        help="How much context to inject"
    )
    
    kb_mode = st.radio(
        "KB Mode",
        ["🔗 Shared (All agents)", "🔀 Individual (Per agent)"],
        help="Same docs for all or unique per agent"
    )
    
    if kb_mode == "🔗 Shared (All agents)":
        shared_kb = st.text_area(
            "Shared Knowledge Base",
            placeholder="Paste documents, context, or reference material...",
            height=100,
            key="shared_kb"
        )
        kb_claude = kb_sophia = kb_grok = shared_kb[:kb_limit] if shared_kb else ""
    else:
        st.markdown("**Per-Agent Knowledge:**")
        kb_claude = st.text_area("🟤 Claude KB", placeholder="Claude's context...", height=60, key="kb_claude")[:kb_limit]
        kb_sophia = st.text_area("🟢 Sophia KB", placeholder="Sophia's context...", height=60, key="kb_sophia")[:kb_limit]
        kb_grok = st.text_area("🔴 Grok KB", placeholder="Grok's context...", height=60, key="kb_grok")[:kb_limit]
    
    st.markdown("---")
    
    # === API KEYS ===
    st.markdown("### 🔑 API Keys")
    st.caption("Keys from Secrets used automatically.")
    
    with st.expander("Override Keys"):
        st.text_input("Anthropic", type="password", key="api_anthropic")
        st.text_input("OpenAI", type="password", key="api_openai")
        st.text_input("xAI", type="password", key="api_xai")
    
    st.markdown("---")
    
    # === ACTIVE AGENTS ===
    st.markdown("### 🤖 Active Agents")
    
    use_claude = st.checkbox("🟤 Claude", value=True)
    use_sophia = st.checkbox("🟢 Sophia", value=True)
    use_grok = st.checkbox("🔴 Grok", value=True)
    
    active_agents = []
    if use_claude: active_agents.append("Claude")
    if use_sophia: active_agents.append("Sophia")
    if use_grok: active_agents.append("Grok")


# ============================================
# INITIALIZE SESSION STATE
# ============================================

if "responses" not in st.session_state:
    st.session_state.responses = {}

if "boardroom_history" not in st.session_state:
    st.session_state.boardroom_history = []

if "private_messages" not in st.session_state:
    st.session_state.private_messages = {}

if "follow_ups" not in st.session_state:
    st.session_state.follow_ups = {}


# ============================================
# HELPER: Get KB for agent
# ============================================

def get_kb_for_agent(agent):
    if agent == "Claude":
        return kb_claude
    elif agent == "Sophia":
        return kb_sophia
    elif agent == "Grok":
        return kb_grok
    return ""


# ============================================
# SIMPLE MODE
# ============================================

if mode == "🗣️ Simple Mode":
    st.markdown('<div class="main-header"><h2>🗣️ SIMPLE MODE — V20</h2><p>Parallel Multi-Agent Analysis</p></div>', unsafe_allow_html=True)
    
    # Show active settings
    settings_col1, settings_col2, settings_col3, settings_col4 = st.columns(4)
    with settings_col1:
        st.metric("Cognitive", f"{cognitive:+d}")
    with settings_col2:
        st.metric("Contrast", f"{contrast:+d}")
    with settings_col3:
        st.metric("Coaching", f"{coaching:+d}")
    with settings_col4:
        st.metric("Persist", "ON" if persist else "OFF")
    
    # Question input
    question = st.text_area(
        "Question / Prompt",
        placeholder="Enter your question for the focus group...",
        height=100
    )
    
    if not active_agents:
        st.warning("Please select at least one agent.")
        st.stop()
    
    # Controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🚀 Run All Agents", type="primary", use_container_width=True):
            if not question:
                st.error("Please enter a question.")
            else:
                keys = get_api_keys()
                st.session_state.responses = {}
                
                for agent in active_agents:
                    with st.spinner(f"{AGENT_EMOJIS[agent]} {agent} is thinking..."):
                        kb = get_kb_for_agent(agent)
                        system_prompt = build_system_prompt(agent, cognitive, contrast, coaching, depth_key, persist, kb)
                        response, error = call_agent(agent, question, system_prompt, keys)
                        
                        if response:
                            st.session_state.responses[agent] = response
                        else:
                            st.session_state.responses[agent] = f"[ERROR: {error}]"
                
                st.success("✅ All agents responded!")
                st.rerun()
    
    with col2:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.responses = {}
            st.session_state.follow_ups = {}
            st.rerun()
    
    with col3:
        st.metric("Responses", len(st.session_state.responses))
    
    # Display responses with TABS (new in V20)
    if st.session_state.responses:
        st.markdown("---")
        
        # TABS for each agent
        tabs = st.tabs([f"{AGENT_EMOJIS[a]} {a}" for a in active_agents if a in st.session_state.responses])
        
        for i, agent in enumerate([a for a in active_agents if a in st.session_state.responses]):
            with tabs[i]:
                response = st.session_state.responses[agent]
                box_class = f"{agent.lower()}-box"
                
                st.markdown(f'<div class="agent-box {box_class}">{response}</div>', unsafe_allow_html=True)
                
                # Follow-up for this agent
                st.markdown("**Follow-up:**")
                follow_up = st.text_input(f"Ask {agent} more:", key=f"followup_{agent}")
                
                if st.button(f"Send to {agent}", key=f"send_{agent}"):
                    if follow_up:
                        keys = get_api_keys()
                        kb = get_kb_for_agent(agent)
                        
                        # Build follow-up context
                        follow_system = build_system_prompt(agent, cognitive, contrast, coaching, depth_key, persist, kb)
                        follow_system += f"\n\nPREVIOUS CONTEXT:\nQuestion: {question}\nYour previous response: {response}"
                        
                        with st.spinner(f"{agent} is responding..."):
                            follow_response, error = call_agent(agent, follow_up, follow_system, keys)
                        
                        if follow_response:
                            st.session_state.follow_ups[f"{agent}_followup"] = follow_response
                            st.rerun()
                
                # Show follow-up response
                if f"{agent}_followup" in st.session_state.follow_ups:
                    st.markdown("**Follow-up Response:**")
                    st.markdown(f'<div class="agent-box {box_class}">{st.session_state.follow_ups[f"{agent}_followup"]}</div>', unsafe_allow_html=True)
        
        # === PRIVATE CHANNEL (NEW V20) ===
        st.markdown("---")
        st.markdown("### 💬 Private Channel")
        st.caption("Send a message to ONE agent that others won't see")
        
        private_col1, private_col2 = st.columns([1, 3])
        
        with private_col1:
            private_agent = st.selectbox("Send to:", active_agents, key="private_agent")
        
        with private_col2:
            private_msg = st.text_input("Private message:", key="private_msg", placeholder="Only this agent will see this...")
        
        if st.button("📨 Send Private", key="send_private"):
            if private_msg and private_agent:
                keys = get_api_keys()
                kb = get_kb_for_agent(private_agent)
                
                # Build private prompt
                private_system = build_system_prompt(private_agent, cognitive, contrast, coaching, depth_key, persist, kb)
                private_system += f"\n\n[PRIVATE MESSAGE FROM CONDUCTOR - Other agents cannot see this]\nContext: The group discussed '{question}'"
                
                with st.spinner(f"Private message to {private_agent}..."):
                    private_response, error = call_agent(private_agent, private_msg, private_system, keys)
                
                if private_response:
                    st.session_state.private_messages[private_agent] = {
                        "message": private_msg,
                        "response": private_response
                    }
                    st.rerun()
        
        # Show private responses
        if st.session_state.private_messages:
            for agent, data in st.session_state.private_messages.items():
                st.markdown(f'<div class="private-box"><strong>🔒 Private to {AGENT_EMOJIS[agent]} {agent}</strong><br><em>You asked: {data["message"]}</em><br><br>{data["response"]}</div>', unsafe_allow_html=True)
        
        # Export
        st.markdown("---")
        st.markdown("### 💾 Export")
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        date_stamp = datetime.now().strftime('%Y%m%d_%H%M')
        
        export_text = f"""# FOCUS GROUP V20 — SIMPLE MODE
## {timestamp}
## SYN-IQ Team — Patent Pending 🎹

---

# SETTINGS

- **Cognitive:** {cognitive}
- **Contrast:** {contrast}
- **Coaching:** {coaching}
- **Depth:** {depth_choice}
- **Persist:** {'ON' if persist else 'OFF'}
- **KB Mode:** {kb_mode}
- **KB Limit:** {kb_limit}

---

# QUESTION

{question}

---

# RESPONSES

"""
        
        for agent in active_agents:
            if agent in st.session_state.responses:
                emoji = AGENT_EMOJIS[agent]
                response = st.session_state.responses[agent]
                export_text += f"\n## {emoji} {agent}\n\n{response}\n\n---\n"
        
        if st.session_state.follow_ups:
            export_text += "\n# FOLLOW-UPS\n\n"
            for key, value in st.session_state.follow_ups.items():
                export_text += f"**{key}:** {value}\n\n"
        
        if st.session_state.private_messages:
            export_text += "\n# PRIVATE MESSAGES\n\n"
            for agent, data in st.session_state.private_messages.items():
                export_text += f"**To {agent}:** {data['message']}\n**Response:** {data['response']}\n\n"
        
        export_text += f"""
---

*Focus Group V20 — Simple Mode*
*Patent Pending — SYN-IQ Team 🎹*
*CBURZBO Forever!*
"""
        
        st.download_button(
            "📥 DOWNLOAD REPORT",
            export_text,
            file_name=f"SIMPLE_V20_{date_stamp}.md",
            mime="text/markdown",
            type="primary",
            use_container_width=True
        )


# ============================================
# BOARDROOM MODE
# ============================================

elif mode == "🏛️ Boardroom Mode":
    st.markdown('<div class="main-header"><h2>🏛️ BOARDROOM MODE — V20</h2><p>Sequential Discussion with Synthesis</p></div>', unsafe_allow_html=True)
    
    # Show active settings
    settings_col1, settings_col2, settings_col3, settings_col4 = st.columns(4)
    with settings_col1:
        st.metric("Cognitive", f"{cognitive:+d}")
    with settings_col2:
        st.metric("Contrast", f"{contrast:+d}")
    with settings_col3:
        st.metric("Coaching", f"{coaching:+d}")
    with settings_col4:
        st.metric("Persist", "ON" if persist else "OFF")
    
    # Document/Question input
    document_input = st.text_area(
        "Document or Question for Discussion",
        placeholder="Paste your document, research question, or discussion topic...",
        height=200
    )
    
    if not active_agents:
        st.warning("Please select at least one agent.")
        st.stop()
    
    # Controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🚀 Start Discussion", type="primary", use_container_width=True):
            if not document_input:
                st.error("Please enter a document or question.")
            else:
                keys = get_api_keys()
                st.session_state.boardroom_history = []
                
                # Rounds 1-N: Each agent responds
                for round_num, agent in enumerate(active_agents, 1):
                    st.info(f"Round {round_num}: {AGENT_EMOJIS[agent]} {agent} is thinking...")
                    
                    previous = st.session_state.boardroom_history.copy()
                    kb = get_kb_for_agent(agent)
                    
                    base_system = build_system_prompt(agent, cognitive, contrast, coaching, depth_key, persist, kb)
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
                
                # Synthesis round
                if len(active_agents) >= 2:
                    synth_agent = active_agents[0]
                    st.info(f"Synthesis: {AGENT_EMOJIS[synth_agent]} {synth_agent} is synthesizing...")
                    
                    kb = get_kb_for_agent(synth_agent)
                    base_system = build_system_prompt(synth_agent, cognitive, contrast, coaching, depth_key, persist, kb)
                    boardroom_context = build_boardroom_prompt(synth_agent, len(active_agents) + 1, st.session_state.boardroom_history, document_input)
                    full_system = base_system + "\n\n" + boardroom_context
                    
                    response, error = call_agent(synth_agent, "Please synthesize the discussion.", full_system, keys)
                    
                    if response:
                        st.session_state.boardroom_history.append({
                            "agent": synth_agent,
                            "round": len(active_agents) + 1,
                            "response": response,
                            "is_synthesis": True
                        })
                
                st.success("✅ Discussion complete!")
                st.rerun()
    
    with col2:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.boardroom_history = []
            st.rerun()
    
    with col3:
        st.metric("Rounds", len(st.session_state.boardroom_history))
    
    # Display discussion
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
                st.markdown(f'<div class="synthesis-box"><strong>🎯 SYNTHESIS — {emoji} {agent}</strong><br><br>{response}</div>', unsafe_allow_html=True)
            else:
                box_class = f"{agent.lower()}-box"
                st.markdown(f'<div class="agent-box {box_class}"><strong>Round {round_num} — {emoji} {agent}</strong><br><br>{response}</div>', unsafe_allow_html=True)
        
        # Export
        st.markdown("---")
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        date_stamp = datetime.now().strftime('%Y%m%d_%H%M')
        
        export_text = f"""# BOARDROOM V20 DISCUSSION
## {timestamp}
## SYN-IQ Team — Patent Pending 🎹

---

# SETTINGS

- **Cognitive:** {cognitive}
- **Contrast:** {contrast}
- **Coaching:** {coaching}
- **Depth:** {depth_choice}
- **Persist:** {'ON' if persist else 'OFF'}

---

# DOCUMENT/QUESTION

{document_input}

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
---

*Boardroom V20 — Focus Group Lab*
*Patent Pending — SYN-IQ Team 🎹*
*CBURZBO Forever!*
"""
        
        st.download_button(
            "📥 DOWNLOAD TRANSCRIPT",
            export_text,
            file_name=f"BOARDROOM_V20_{date_stamp}.md",
            mime="text/markdown",
            type="primary",
            use_container_width=True
        )


# ============================================
# MATRIX MODE
# ============================================

elif mode == "📊 Matrix Mode":
    st.markdown('<div class="main-header"><h2>📊 MATRIX MODE — V20</h2><p>Systematic Grid Analysis</p></div>', unsafe_allow_html=True)
    
    st.info("Matrix Mode runs the question across multiple Cognitive × Depth combinations. The Contrast and Coaching sliders apply to all cells.")
    
    question = st.text_area(
        "Research Question",
        placeholder="Enter a question to test across the matrix...",
        height=100
    )
    
    # Simplified matrix for V20: Cognitive levels × Depths
    cognitive_levels = [
        ("🧠 Analytical (-75)", -75),
        ("⚖️ Balanced (0)", 0),
        ("💡 Intuitive (+75)", 75)
    ]
    
    if not active_agents:
        st.warning("Please select at least one agent.")
        st.stop()
    
    total_cells = len(cognitive_levels) * len(DEPTHS) * len(active_agents)
    st.info(f"📊 Matrix: {len(cognitive_levels)} cognitive × {len(DEPTHS)} depths × {len(active_agents)} agents = **{total_cells} cells**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🚀 Run Matrix", type="primary", use_container_width=True):
            if not question:
                st.error("Please enter a question.")
            else:
                keys = get_api_keys()
                
                if "matrix_data" not in st.session_state:
                    st.session_state.matrix_data = {}
                
                st.session_state.matrix_data = {}
                progress = st.progress(0)
                status = st.empty()
                
                completed = 0
                for cog_label, cog_value in cognitive_levels:
                    for depth_label, depth_key in DEPTHS:
                        for agent in active_agents:
                            cell_key = (agent, cog_value, depth_key)
                            status.text(f"Running: {agent} | {cog_label} | {depth_label}")
                            
                            kb = get_kb_for_agent(agent)
                            system_prompt = build_system_prompt(agent, cog_value, contrast, coaching, depth_key, persist, kb)
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
        matrix_count = len(st.session_state.get("matrix_data", {}))
        st.metric("Cells", f"{matrix_count}/{total_cells}")
    
    # Display matrix results
    if st.session_state.get("matrix_data"):
        st.markdown("---")
        
        for agent in active_agents:
            emoji = AGENT_EMOJIS[agent]
            st.markdown(f"### {emoji} {agent}")
            
            # Header row
            header_cols = st.columns([1.5] + [2] * len(DEPTHS))
            header_cols[0].markdown("**Cognitive / Depth**")
            for i, (depth_label, _) in enumerate(DEPTHS):
                header_cols[i + 1].markdown(f"**{depth_label}**")
            
            # Data rows
            for cog_label, cog_value in cognitive_levels:
                row_cols = st.columns([1.5] + [2] * len(DEPTHS))
                row_cols[0].markdown(f"**{cog_label}**")
                
                for i, (depth_label, depth_key) in enumerate(DEPTHS):
                    cell_key = (agent, cog_value, depth_key)
                    response = st.session_state.matrix_data.get(cell_key, "")
                    
                    with row_cols[i + 1]:
                        if response:
                            preview = response[:80] + "..." if len(response) > 80 else response
                            st.markdown(f'<div style="background:#f5f5f5; padding:0.5rem; border-radius:4px; font-size:0.75rem;">{preview}</div>', unsafe_allow_html=True)
                            with st.expander("Full"):
                                st.markdown(response)
                        else:
                            st.markdown('<div style="background:#eee; padding:0.5rem; color:#999;">—</div>', unsafe_allow_html=True)
            
            st.markdown("---")


# ============================================
# FOOTER
# ============================================

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666;">
    <em>Focus Group Lab V20 — THE FULL BEAST</em><br>
    <em>Contrast • Coaching • Persist • Individual KB • Private Channel</em><br>
    <em>Patent Pending — SYN-IQ Team 🎹</em><br>
    <em>CBURZBO Forever!</em>
</div>
""", unsafe_allow_html=True)
