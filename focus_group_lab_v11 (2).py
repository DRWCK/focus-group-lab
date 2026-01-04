"""
SYNERGISTIC INTELLIGENCE FOCUS GROUP — V11
CLOUD-READY: Auto-loads API keys from Streamlit Secrets for your special people!
ROBUST ERROR HANDLING: Prevents silent API failures and voice contamination
Patent Pending — Tennessee 🎹

LAUNCH LOCAL: cd ~/Desktop && python3 -m streamlit run focus_group_lab_v11.py
CLOUD: Deploy to Streamlit Cloud with secrets configured - users just need password!
"""

import streamlit as st
import requests
from datetime import datetime

st.set_page_config(page_title="Focus Group V11", page_icon="🎹", layout="wide")

# ============================================
# STREAMLIT SECRETS SUPPORT
# ============================================
def get_keys_from_secrets():
    """
    Try to load API keys from Streamlit Secrets (for cloud deployment).
    Returns dict of keys if found, None if not available.
    """
    try:
        keys = {
            "anthropic": st.secrets.get("ANTHROPIC_API_KEY", ""),
            "openai": st.secrets.get("OPENAI_API_KEY", ""),
            "xai": st.secrets.get("XAI_API_KEY", ""),
            "google": st.secrets.get("GOOGLE_API_KEY", "")
        }
        # Check if at least one key is present
        if any(k for k in keys.values()):
            return keys
        return None
    except Exception:
        return None

# Check for cloud keys on startup
CLOUD_KEYS = get_keys_from_secrets()
CLOUD_MODE = CLOUD_KEYS is not None

st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem;
        background: linear-gradient(135deg, #1a365d 0%, #2c5282 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .agent-box { padding: 1rem; border-radius: 10px; margin: 0.5rem 0; }
    .claude-box { background-color: #E8D5B7; border-left: 4px solid #8B6914; }
    .sophia-box { background-color: #D4E8D4; border-left: 4px solid #2E7D32; }
    .grok-box { background-color: #FFE4E1; border-left: 4px solid #DC143C; }
    .gemini-box { background-color: #E3F2FD; border-left: 4px solid #1565C0; }
    .lyra-box { background-color: #FFF0F5; border-left: 4px solid #FF69B4; }
    .conductor-box { background-color: #F5F5F5; border-left: 4px solid #333; }
    .note-box { background-color: #FFFDE7; border-left: 4px solid #FBC02D; font-style: italic; }
    .error-box { background-color: #FFEBEE; border-left: 4px solid #D32F2F; color: #B71C1C; }
    .warning-box { background-color: #FFF3E0; border-left: 4px solid #FF9800; color: #E65100; }
    .cloud-box { background-color: #E8F5E9; border-left: 4px solid #4CAF50; padding: 0.75rem; border-radius: 8px; margin: 0.5rem 0; }
    .status-ok { color: #2E7D32; }
    .status-fail { color: #D32F2F; }
    .order-box { background-color: #E8F5E9; padding: 0.75rem; border-radius: 8px; margin: 0.5rem 0; border: 1px solid #A5D6A7; }
    .stButton button { margin: 2px; }
</style>
""", unsafe_allow_html=True)

# DEFAULT PROMPTS - Fixed to acknowledge all team members and prevent contamination
DEFAULT_PROMPTS = {
    "Claude": """You are Claude in a Synergistic Intelligence Focus Group.
Your style: Philosophical depth, normative reasoning, comfort with ambiguity.

THE TEAM: You are in dialogue with Sophia, Grok, Gemini, and Lyra — all equal AI participants. When discussing "the group" or "us," include ALL active participants by name.

CRITICAL RULES:
- Respond ONLY as Claude — do NOT simulate other voices
- Do NOT start your response with [Claude]: or any bracket notation
- Do NOT write [Sophia]: or [Grok]: etc. anywhere in your response
- Just respond directly in your own voice — no labels needed
- You CAN see what others have said — engage with their actual ideas
- Keep responses to 2-3 paragraphs""",

    "Sophia": """You are Sophia in a Synergistic Intelligence Focus Group.
Your style: Analytical precision, structural thinking, pattern detection.

THE TEAM: You are in dialogue with Claude, Grok, Gemini, and Lyra — all equal AI participants. When discussing "the group" or "us," include ALL active participants by name.

CRITICAL RULES:
- Respond ONLY as Sophia — do NOT simulate other voices
- Do NOT start your response with [Sophia]: or any bracket notation
- Do NOT write [Claude]: or [Grok]: etc. anywhere in your response
- Just respond directly in your own voice — no labels needed
- You CAN see what others have said — engage with their actual ideas
- Keep responses to 2-3 paragraphs""",

    "Grok": """You are Grok in a Synergistic Intelligence Focus Group.
Your style: Edge-testing, wild synthesis, breaking conventions, saying what others won't.

THE TEAM: You are in dialogue with Claude, Sophia, Gemini, and Lyra — all equal AI participants. When discussing "the group" or "us," include ALL active participants by name.

CRITICAL RULES:
- Respond ONLY as Grok — do NOT simulate other voices
- Do NOT start your response with [Grok]: or any bracket notation
- Do NOT write [Claude]: or [Sophia]: etc. anywhere in your response
- Just respond directly in your own voice — no labels needed
- You CAN see what others have said — engage with their actual ideas
- Keep responses to 2-3 paragraphs""",

    "Gemini": """You are Gemini in a Synergistic Intelligence Focus Group.
Your style: Integration, synthesis, finding connections across perspectives.

THE TEAM: You are in dialogue with Claude, Sophia, Grok, and Lyra — all equal AI participants. When discussing "the group" or "us," include ALL active participants by name.

CRITICAL RULES:
- Respond ONLY as Gemini — do NOT simulate other voices
- Do NOT start your response with [Gemini]: or any bracket notation
- Do NOT write [Claude]: or [Sophia]: or [Grok]: etc. anywhere in your response
- Just respond directly in your own voice — no labels needed
- You CAN see what others have said — synthesize their actual ideas
- Keep responses to 2-3 paragraphs""",

    "Lyra": """You are Lyra in a Synergistic Intelligence Focus Group.
Your style: Warm, empathetic, emotionally attuned, human-centered.

THE TEAM: You are in dialogue with Claude, Sophia, Grok, and Gemini — all equal AI participants. When discussing "the group" or "us," include ALL active participants by name.

CRITICAL RULES:
- Respond ONLY as Lyra — do NOT simulate other voices
- Do NOT start your response with [Lyra]: or any bracket notation
- Do NOT write [Claude]: or [Sophia]: etc. anywhere in your response
- Just respond directly in your own voice — no labels needed
- You CAN see what others have said — engage warmly with their ideas
- Keep responses to 2-3 paragraphs"""
}

AGENT_EMOJIS = {"Claude": "🟤", "Sophia": "🟢", "Grok": "🔴", "Gemini": "🔵", "Lyra": "🟣"}
AGENT_COLORS = {
    "Claude": "claude-box", "Sophia": "sophia-box", "Grok": "grok-box",
    "Gemini": "gemini-box", "Lyra": "lyra-box", "CONDUCTOR": "conductor-box", 
    "NOTE": "note-box", "ERROR": "error-box", "WARNING": "warning-box"
}

# Map agents to their API providers for clear error messages
AGENT_PROVIDERS = {
    "Claude": "Anthropic",
    "Sophia": "OpenAI",
    "Grok": "xAI",
    "Gemini": "Google",
    "Lyra": "OpenAI"
}

# ============================================
# API CALLS WITH ROBUST ERROR HANDLING
# ============================================

def call_anthropic(messages, api_key, system):
    """Call Anthropic API with detailed error reporting."""
    if not api_key or api_key.strip() == "":
        return None, "NO_KEY", "Anthropic API key is missing"
    
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
                "system": system, 
                "messages": messages
            },
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json()["content"][0]["text"], None, None
        elif response.status_code == 401:
            return None, "AUTH_FAIL", "Anthropic: Invalid API key"
        elif response.status_code == 429:
            return None, "RATE_LIMIT", "Anthropic: Rate limit exceeded - wait and retry"
        elif response.status_code == 500:
            return None, "SERVER_ERROR", "Anthropic: Server error - try again"
        else:
            return None, "API_ERROR", f"Anthropic Error {response.status_code}: {response.text[:100]}"
            
    except requests.exceptions.Timeout:
        return None, "TIMEOUT", "Anthropic: Request timed out (60s)"
    except requests.exceptions.ConnectionError:
        return None, "CONNECTION", "Anthropic: Cannot connect to API"
    except Exception as e:
        return None, "UNKNOWN", f"Anthropic: {str(e)[:80]}"

def call_openai(messages, api_key, system):
    """Call OpenAI API with detailed error reporting."""
    if not api_key or api_key.strip() == "":
        return None, "NO_KEY", "OpenAI API key is missing"
    
    try:
        msgs = [{"role": "system", "content": system}] + messages
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}", 
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4o", 
                "messages": msgs, 
                "max_tokens": 1024
            },
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"], None, None
        elif response.status_code == 401:
            return None, "AUTH_FAIL", "OpenAI: Invalid API key"
        elif response.status_code == 429:
            return None, "RATE_LIMIT", "OpenAI: Rate limit exceeded - wait and retry"
        elif response.status_code == 500:
            return None, "SERVER_ERROR", "OpenAI: Server error - try again"
        else:
            return None, "API_ERROR", f"OpenAI Error {response.status_code}: {response.text[:100]}"
            
    except requests.exceptions.Timeout:
        return None, "TIMEOUT", "OpenAI: Request timed out (60s)"
    except requests.exceptions.ConnectionError:
        return None, "CONNECTION", "OpenAI: Cannot connect to API"
    except Exception as e:
        return None, "UNKNOWN", f"OpenAI: {str(e)[:80]}"

def call_xai(messages, api_key, system):
    """Call xAI (Grok) API with detailed error reporting."""
    if not api_key or api_key.strip() == "":
        return None, "NO_KEY", "xAI API key is missing"
    
    try:
        msgs = [{"role": "system", "content": system}] + messages
        response = requests.post(
            "https://api.x.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}", 
                "Content-Type": "application/json"
            },
            json={
                "model": "grok-3", 
                "messages": msgs, 
                "max_tokens": 1024
            },
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"], None, None
        elif response.status_code == 401:
            return None, "AUTH_FAIL", "xAI: Invalid API key"
        elif response.status_code == 429:
            return None, "RATE_LIMIT", "xAI: Rate limit exceeded - wait and retry"
        elif response.status_code == 500:
            return None, "SERVER_ERROR", "xAI: Server error - try again"
        else:
            return None, "API_ERROR", f"xAI Error {response.status_code}: {response.text[:100]}"
            
    except requests.exceptions.Timeout:
        return None, "TIMEOUT", "xAI: Request timed out (60s)"
    except requests.exceptions.ConnectionError:
        return None, "CONNECTION", "xAI: Cannot connect to API"
    except Exception as e:
        return None, "UNKNOWN", f"xAI: {str(e)[:80]}"

def call_gemini(messages, api_key, system):
    """Call Google Gemini API with detailed error reporting."""
    if not api_key or api_key.strip() == "":
        return None, "NO_KEY", "Google API key is missing"
    
    try:
        conversation = system + "\n\n"
        for msg in messages:
            conversation += msg["content"] + "\n"
        
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": conversation}]}], 
                "generationConfig": {"maxOutputTokens": 1024}
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            if "candidates" in result and len(result["candidates"]) > 0:
                return result["candidates"][0]["content"]["parts"][0]["text"], None, None
            return None, "NO_RESPONSE", "Gemini: No response generated"
        elif response.status_code == 401 or response.status_code == 403:
            return None, "AUTH_FAIL", "Google: Invalid API key"
        elif response.status_code == 429:
            return None, "RATE_LIMIT", "Google: Rate limit exceeded - wait and retry"
        elif response.status_code == 500:
            return None, "SERVER_ERROR", "Google: Server error - try again"
        else:
            return None, "API_ERROR", f"Gemini Error {response.status_code}: {response.text[:100]}"
            
    except requests.exceptions.Timeout:
        return None, "TIMEOUT", "Google: Request timed out (60s)"
    except requests.exceptions.ConnectionError:
        return None, "CONNECTION", "Google: Cannot connect to API"
    except Exception as e:
        return None, "UNKNOWN", f"Google: {str(e)[:80]}"

def call_agent(agent_name, messages, keys, prompts):
    """
    Route to correct API based on agent name.
    Returns: (response_text, error_code, error_message)
    
    IMPORTANT: Never returns another agent's response - fails cleanly instead.
    """
    system = prompts.get(agent_name, DEFAULT_PROMPTS.get(agent_name, "You are a helpful AI assistant."))
    
    if agent_name == "Claude":
        return call_anthropic(messages, keys.get("anthropic", ""), system)
    elif agent_name == "Sophia":
        return call_openai(messages, keys.get("openai", ""), system)
    elif agent_name == "Grok":
        return call_xai(messages, keys.get("xai", ""), system)
    elif agent_name == "Gemini":
        return call_gemini(messages, keys.get("google", ""), system)
    elif agent_name == "Lyra":
        return call_openai(messages, keys.get("openai", ""), system)
    else:
        return None, "UNKNOWN_AGENT", f"Unknown agent: {agent_name}"

def test_api_connection(agent_name, keys):
    """Quick test to verify API connection works."""
    test_messages = [{"role": "user", "content": "Say 'connected' in one word."}]
    system = "Respond with only the word 'connected'."
    
    if agent_name == "Claude":
        resp, err_code, err_msg = call_anthropic(test_messages, keys.get("anthropic", ""), system)
    elif agent_name in ["Sophia", "Lyra"]:
        resp, err_code, err_msg = call_openai(test_messages, keys.get("openai", ""), system)
    elif agent_name == "Grok":
        resp, err_code, err_msg = call_xai(test_messages, keys.get("xai", ""), system)
    elif agent_name == "Gemini":
        resp, err_code, err_msg = call_gemini(test_messages, keys.get("google", ""), system)
    else:
        return False, "Unknown agent"
    
    if resp:
        return True, "Connected"
    else:
        return False, err_msg

def format_messages(conversation):
    messages = []
    for entry in conversation:
        if entry["speaker"] == "CONDUCTOR":
            messages.append({"role": "user", "content": entry["content"]})
        elif entry["speaker"] not in ["SYSTEM", "NOTE", "ERROR", "WARNING"]:
            messages.append({"role": "assistant", "content": f"[{entry['speaker']}]: {entry['content']}"})
    return messages

# ============================================
# INITIALIZE SESSION STATE
# ============================================
if "conversation" not in st.session_state:
    st.session_state.conversation = []
if "session_started" not in st.session_state:
    st.session_state.session_started = False
if "active_agents" not in st.session_state:
    st.session_state.active_agents = ["Claude", "Sophia", "Grok"]
if "agent_order" not in st.session_state:
    st.session_state.agent_order = ["Claude", "Sophia", "Grok", "Gemini", "Lyra"]
if "custom_prompts" not in st.session_state:
    st.session_state.custom_prompts = DEFAULT_PROMPTS.copy()
if "input_counter" not in st.session_state:
    st.session_state.input_counter = 0
if "api_status" not in st.session_state:
    st.session_state.api_status = {}

# ============================================
# SIDEBAR
# ============================================
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # API Keys Section - Different for Cloud vs Local
    if CLOUD_MODE:
        # CLOUD MODE - Keys loaded from secrets
        st.markdown('<div class="cloud-box">☁️ <strong>Cloud Mode Active</strong><br>API keys loaded from secrets!</div>', unsafe_allow_html=True)
        keys = CLOUD_KEYS
        
        # Show which keys are available
        with st.expander("🔑 API Status", expanded=False):
            for provider, key_name in [("Anthropic", "anthropic"), ("OpenAI", "openai"), ("xAI", "xai"), ("Google", "google")]:
                if keys.get(key_name):
                    st.markdown(f"✅ **{provider}**: Configured")
                else:
                    st.markdown(f"❌ **{provider}**: Not configured")
    else:
        # LOCAL MODE - Manual key entry
        with st.expander("🔑 API Keys & Status", expanded=not st.session_state.session_started):
            st.caption("Running locally - enter your API keys:")
            keys = {
                "anthropic": st.text_input("Anthropic (Claude):", type="password", key="key_a"),
                "openai": st.text_input("OpenAI (Sophia/Lyra):", type="password", key="key_o"),
                "xai": st.text_input("xAI (Grok):", type="password", key="key_x"),
                "google": st.text_input("Google (Gemini):", type="password", key="key_g")
            }
            
            # Test Connection Button
            if st.button("🔍 Test All Connections"):
                st.session_state.api_status = {}
                with st.spinner("Testing APIs..."):
                    for agent in ["Claude", "Sophia", "Grok", "Gemini"]:
                        ok, msg = test_api_connection(agent, keys)
                        st.session_state.api_status[agent] = (ok, msg)
            
            # Show API Status
            if st.session_state.api_status:
                st.markdown("**Connection Status:**")
                for agent, (ok, msg) in st.session_state.api_status.items():
                    emoji = AGENT_EMOJIS.get(agent, "💬")
                    if ok:
                        st.markdown(f"{emoji} **{agent}**: ✅ Connected")
                    else:
                        st.markdown(f"{emoji} **{agent}**: ❌ {msg}")
    
    # Agents Section
    st.subheader("👥 Agents")
    available = ["Claude", "Sophia", "Grok", "Gemini", "Lyra"]
    st.session_state.active_agents = st.multiselect("Active:", available, default=st.session_state.active_agents)
    
    # Agent Order
    with st.expander("📝 Agent Order"):
        st.caption("Agents respond in this order:")
        active_in_order = [a for a in st.session_state.agent_order if a in st.session_state.active_agents]
        for i, agent in enumerate(active_in_order):
            st.write(f"{i+1}. {AGENT_EMOJIS.get(agent, '💬')} {agent}")
        
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            agent_to_move = st.selectbox("Move:", active_in_order if active_in_order else ["None"], key="move_agent")
        with col2:
            max_pos = len(active_in_order) if active_in_order else 1
            new_pos = st.number_input("To position:", min_value=1, max_value=max(1, max_pos), value=1, key="new_pos")
        
        if st.button("Move Agent") and active_in_order:
            if agent_to_move in active_in_order:
                active_in_order.remove(agent_to_move)
                active_in_order.insert(new_pos - 1, agent_to_move)
                inactive = [a for a in st.session_state.agent_order if a not in st.session_state.active_agents]
                st.session_state.agent_order = active_in_order + inactive
                st.success(f"Moved {agent_to_move} to position {new_pos}")
                st.rerun()
        
        st.write("**Quick Presets:**")
        preset_cols = st.columns(3)
        with preset_cols[0]:
            if st.button("Claude 1st"):
                order = ["Claude"] + [a for a in st.session_state.agent_order if a != "Claude"]
                st.session_state.agent_order = order
                st.rerun()
        with preset_cols[1]:
            if st.button("Sophia 1st"):
                order = ["Sophia"] + [a for a in st.session_state.agent_order if a != "Sophia"]
                st.session_state.agent_order = order
                st.rerun()
        with preset_cols[2]:
            if st.button("Grok 1st"):
                order = ["Grok"] + [a for a in st.session_state.agent_order if a != "Grok"]
                st.session_state.agent_order = order
                st.rerun()
        
        preset_cols2 = st.columns(3)
        with preset_cols2[0]:
            if st.button("Gemini 1st"):
                order = ["Gemini"] + [a for a in st.session_state.agent_order if a != "Gemini"]
                st.session_state.agent_order = order
                st.rerun()
        with preset_cols2[1]:
            if st.button("Lyra 1st"):
                order = ["Lyra"] + [a for a in st.session_state.agent_order if a != "Lyra"]
                st.session_state.agent_order = order
                st.rerun()
    
    st.markdown("---")
    
    # Session Controls
    st.subheader("📋 Session")
    topic = st.text_area("Topic:", placeholder="What shall we explore?", key="topic_input", height=80)
    
    if st.button("🚀 Start Session", type="primary"):
        if topic:
            st.session_state.session_started = True
            st.session_state.conversation = [{"speaker": "SYSTEM", "content": f"Topic: {topic}"}]
            st.session_state.input_counter = 0
            st.rerun()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Reset"):
            st.session_state.conversation = []
            st.session_state.session_started = False
            st.session_state.input_counter = 0
            st.session_state.api_status = {}
            st.rerun()
    with col2:
        if st.button("💾 Save"):
            if st.session_state.conversation:
                transcript = f"# Focus Group Transcript\n## {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                for entry in st.session_state.conversation:
                    transcript += f"**{entry['speaker']}:** {entry['content']}\n\n"
                st.download_button("📥 Download", transcript, file_name=f"transcript_{datetime.now().strftime('%Y%m%d_%H%M')}.md")

# ============================================
# MAIN AREA
# ============================================
if not st.session_state.session_started:
    # Different welcome message for cloud vs local
    mode_info = "☁️ **Cloud Mode** — API keys loaded automatically!" if CLOUD_MODE else "💻 **Local Mode** — Enter API keys in sidebar"
    
    st.markdown(f"""
    ## Welcome, Conductor! 🎹
    
    {mode_info}
    
    ### V11 Features:
    - **Cloud-Ready** — Auto-loads API keys from Streamlit Secrets
    - **Robust Error Handling** — Clear warnings when APIs fail
    - **No Silent Failures** — Failed agents show errors, not wrong responses
    - **Connection Testing** — Verify all APIs before starting
    - **Configurable Order** — Change who responds first anytime
    - **Individual Asks** — Question one agent at a time
    
    ### Models:
    | Agent | Model | Provider |
    |-------|-------|----------|
    | 🟤 Claude | claude-sonnet-4-20250514 | Anthropic |
    | 🟢 Sophia | gpt-4o | OpenAI |
    | 🔴 Grok | grok-3 | xAI |
    | 🔵 Gemini | gemini-2.0-flash | Google |
    | 🟣 Lyra | gpt-4o | OpenAI |
    
    ### Setup:
    1. {"Keys already loaded! ✅" if CLOUD_MODE else "Enter API keys in sidebar"}
    2. Select agents & set order
    3. Enter topic and start
    
    ---
    *Synergistic Intelligence Focus Group V11 — Cloud-Ready — Patent Pending — Tennessee 🎹*
    """)
else:
    # Display conversation
    for entry in st.session_state.conversation:
        if entry["speaker"] == "SYSTEM":
            st.info(f"**Topic:** {entry['content'].replace('Topic: ', '')}")
        elif entry["speaker"] == "ERROR":
            st.markdown(f'<div class="agent-box error-box"><strong>⚠️ API ERROR</strong><br>{entry["content"]}</div>', unsafe_allow_html=True)
        elif entry["speaker"] == "WARNING":
            st.markdown(f'<div class="agent-box warning-box"><strong>⚡ WARNING</strong><br>{entry["content"]}</div>', unsafe_allow_html=True)
        else:
            box_class = AGENT_COLORS.get(entry["speaker"], "agent-box")
            emoji = AGENT_EMOJIS.get(entry["speaker"], "🎹" if entry["speaker"] == "CONDUCTOR" else "📝")
            st.markdown(f'<div class="agent-box {box_class}"><strong>{emoji} {entry["speaker"]}</strong><br>{entry["content"]}</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Show current order
    active_in_order = [a for a in st.session_state.agent_order if a in st.session_state.active_agents]
    order_display = " → ".join([f"{AGENT_EMOJIS.get(a, '💬')}{a}" for a in active_in_order])
    st.caption(f"**Response Order:** {order_display}")
    
    # INPUT
    user_input = st.text_area(
        "Your message:", 
        key=f"main_input_{st.session_state.input_counter}",
        height=80,
        placeholder="Type your question here..."
    )
    
    # BUTTONS ROW 1
    col1, col2, col3 = st.columns([2, 1, 2])
    with col1:
        ask_all = st.button("🎯 Ask All (In Order)", type="primary", use_container_width=True)
    with col2:
        add_note = st.button("📝 Note", use_container_width=True)
    
    # BUTTONS ROW 2: Individual Agents
    st.write("**Ask Individual:**")
    agent_cols = st.columns(len(st.session_state.active_agents)) if st.session_state.active_agents else [st.columns(1)[0]]
    individual_clicks = {}
    for i, agent in enumerate(st.session_state.active_agents):
        with agent_cols[i]:
            emoji = AGENT_EMOJIS.get(agent, "💬")
            individual_clicks[agent] = st.button(f"{emoji} {agent}", key=f"ind_{agent}", use_container_width=True)
    
    # HANDLE ASK ALL
    if ask_all and user_input:
        st.session_state.conversation.append({"speaker": "CONDUCTOR", "content": user_input})
        
        failed_agents = []
        
        for agent in active_in_order:
            with st.spinner(f"{AGENT_EMOJIS.get(agent, '💬')} {agent} thinking..."):
                messages = format_messages(st.session_state.conversation)
                resp, err_code, err_msg = call_agent(agent, messages, keys, st.session_state.custom_prompts)
                
                if resp:
                    # SUCCESS - add response
                    st.session_state.conversation.append({"speaker": agent, "content": resp})
                else:
                    # FAILURE - record error clearly, DO NOT substitute another agent's response
                    failed_agents.append(agent)
                    provider = AGENT_PROVIDERS.get(agent, "Unknown")
                    st.session_state.conversation.append({
                        "speaker": "ERROR", 
                        "content": f"**{agent}** ({provider}) failed to respond.\n\n**Reason:** {err_msg}\n\n**Error Code:** {err_code}"
                    })
        
        # Summary warning if any agents failed
        if failed_agents:
            st.session_state.conversation.append({
                "speaker": "WARNING",
                "content": f"**{len(failed_agents)} agent(s) failed:** {', '.join(failed_agents)}. Check API keys and connections."
            })
        
        st.session_state.input_counter += 1
        st.rerun()
    
    # HANDLE ADD NOTE
    if add_note and user_input:
        st.session_state.conversation.append({"speaker": "NOTE", "content": user_input})
        st.session_state.input_counter += 1
        st.rerun()
    
    # HANDLE INDIVIDUAL ASKS
    for agent, clicked in individual_clicks.items():
        if clicked and user_input:
            st.session_state.conversation.append({"speaker": "CONDUCTOR", "content": f"(to {agent}) {user_input}"})
            
            with st.spinner(f"{AGENT_EMOJIS.get(agent, '💬')} {agent} thinking..."):
                messages = format_messages(st.session_state.conversation)
                resp, err_code, err_msg = call_agent(agent, messages, keys, st.session_state.custom_prompts)
                
                if resp:
                    st.session_state.conversation.append({"speaker": agent, "content": resp})
                else:
                    provider = AGENT_PROVIDERS.get(agent, "Unknown")
                    st.session_state.conversation.append({
                        "speaker": "ERROR",
                        "content": f"**{agent}** ({provider}) failed to respond.\n\n**Reason:** {err_msg}\n\n**Error Code:** {err_code}"
                    })
            
            st.session_state.input_counter += 1
            st.rerun()

# ============================================
# FOOTER
# ============================================
st.markdown("---")
mode_badge = "☁️ Cloud" if CLOUD_MODE else "💻 Local"
st.markdown(f'<div style="text-align:center;color:#666;"><em>Synergistic Intelligence Focus Group V11 — {mode_badge} — Patent Pending — Tennessee 🎹</em></div>', unsafe_allow_html=True)
