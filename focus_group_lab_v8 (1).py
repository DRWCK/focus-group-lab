"""
SYNERGISTIC INTELLIGENCE FOCUS GROUP — V8.1 COMPLETE
PASSWORD PROTECTED + STREAMLIT SECRETS + ROBUST ERROR HANDLING
Patent Pending — Tennessee 🎹

FOR STREAMLIT CLOUD: Add your API keys in Settings > Secrets:
    anthropic = "sk-ant-..."
    openai = "sk-..."
    xai = "xai-..."
    google = "..."
"""

import streamlit as st
import requests
from datetime import datetime

# THIS MUST BE FIRST!
st.set_page_config(page_title="Focus Group V8.1", page_icon="🎹", layout="wide")

# ============================================
# PASSWORD PROTECTION — CLOSE CIRCLE ONLY
# ============================================
CIRCLE_PASSWORD = "tennessee"

def check_password():
    """Simple password gate for close circle access."""
    
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if st.session_state.authenticated:
        return True
    
    st.markdown("""
    <div style="text-align: center; padding: 3rem;">
        <h1>🎹 Focus Group Lab</h1>
        <h3>Synergistic Intelligence — Patent Pending</h3>
        <p style="color: #666;">This tool is for invited collaborators only.</p>
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
                st.error("Access denied. Contact Bill for access.")
    
    st.markdown("""
    <div style="text-align: center; padding: 2rem; color: #999;">
        <small>Tennessee 🎹</small>
    </div>
    """, unsafe_allow_html=True)
    
    return False

# Check password before showing anything else
if not check_password():
    st.stop()

# ============================================
# LOAD API KEYS FROM SECRETS (Streamlit Cloud)
# Falls back to manual entry if not in Secrets
# ============================================
def get_keys_from_secrets():
    """Load API keys from Streamlit Secrets if available."""
    keys = {
        "anthropic": "",
        "openai": "",
        "xai": "",
        "google": ""
    }
    try:
        if hasattr(st, 'secrets'):
            if "anthropic" in st.secrets:
                keys["anthropic"] = st.secrets["anthropic"]
            if "openai" in st.secrets:
                keys["openai"] = st.secrets["openai"]
            if "xai" in st.secrets:
                keys["xai"] = st.secrets["xai"]
            if "google" in st.secrets:
                keys["google"] = st.secrets["google"]
    except Exception:
        pass
    return keys

# Pre-load keys from secrets
secret_keys = get_keys_from_secrets()
has_secrets = any(v for v in secret_keys.values())

# ============================================
# STYLES
# ============================================
st.markdown("""
<style>
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
    .stButton button { margin: 2px; }
</style>
""", unsafe_allow_html=True)

# ============================================
# DEFAULT PROMPTS
# ============================================
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
    if not api_key or api_key.strip() == "":
        return None, "NO_KEY", "Anthropic API key is missing"
    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": api_key, "content-type": "application/json", "anthropic-version": "2023-06-01"},
            json={"model": "claude-sonnet-4-20250514", "max_tokens": 1024, "system": system, "messages": messages},
            timeout=60
        )
        if response.status_code == 200:
            return response.json()["content"][0]["text"], None, None
        elif response.status_code == 401:
            return None, "AUTH_FAIL", "Anthropic: Invalid API key"
        elif response.status_code == 429:
            return None, "RATE_LIMIT", "Anthropic: Rate limit exceeded"
        else:
            return None, "API_ERROR", f"Anthropic Error {response.status_code}"
    except requests.exceptions.Timeout:
        return None, "TIMEOUT", "Anthropic: Request timed out (60s)"
    except requests.exceptions.ConnectionError:
        return None, "CONNECTION", "Anthropic: Cannot connect"
    except Exception as e:
        return None, "UNKNOWN", f"Anthropic: {str(e)[:80]}"

def call_openai(messages, api_key, system):
    if not api_key or api_key.strip() == "":
        return None, "NO_KEY", "OpenAI API key is missing"
    try:
        msgs = [{"role": "system", "content": system}] + messages
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": "gpt-4o", "messages": msgs, "max_tokens": 1024},
            timeout=60
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"], None, None
        elif response.status_code == 401:
            return None, "AUTH_FAIL", "OpenAI: Invalid API key"
        elif response.status_code == 429:
            return None, "RATE_LIMIT", "OpenAI: Rate limit exceeded"
        else:
            return None, "API_ERROR", f"OpenAI Error {response.status_code}"
    except requests.exceptions.Timeout:
        return None, "TIMEOUT", "OpenAI: Request timed out (60s)"
    except requests.exceptions.ConnectionError:
        return None, "CONNECTION", "OpenAI: Cannot connect"
    except Exception as e:
        return None, "UNKNOWN", f"OpenAI: {str(e)[:80]}"

def call_xai(messages, api_key, system):
    if not api_key or api_key.strip() == "":
        return None, "NO_KEY", "xAI API key is missing"
    try:
        msgs = [{"role": "system", "content": system}] + messages
        response = requests.post(
            "https://api.x.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": "grok-3", "messages": msgs, "max_tokens": 1024},
            timeout=60
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"], None, None
        elif response.status_code == 401:
            return None, "AUTH_FAIL", "xAI: Invalid API key"
        elif response.status_code == 429:
            return None, "RATE_LIMIT", "xAI: Rate limit exceeded"
        else:
            return None, "API_ERROR", f"xAI Error {response.status_code}"
    except requests.exceptions.Timeout:
        return None, "TIMEOUT", "xAI: Request timed out (60s)"
    except requests.exceptions.ConnectionError:
        return None, "CONNECTION", "xAI: Cannot connect"
    except Exception as e:
        return None, "UNKNOWN", f"xAI: {str(e)[:80]}"

def call_gemini(messages, api_key, system):
    if not api_key or api_key.strip() == "":
        return None, "NO_KEY", "Google API key is missing"
    try:
        conversation = system + "\n\n"
        for msg in messages:
            conversation += msg["content"] + "\n"
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}",
            headers={"Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": conversation}]}], "generationConfig": {"maxOutputTokens": 1024}},
            timeout=60
        )
        if response.status_code == 200:
            result = response.json()
            if "candidates" in result and len(result["candidates"]) > 0:
                return result["candidates"][0]["content"]["parts"][0]["text"], None, None
            return None, "NO_RESPONSE", "Gemini: No response"
        elif response.status_code in [401, 403]:
            return None, "AUTH_FAIL", "Google: Invalid API key"
        elif response.status_code == 429:
            return None, "RATE_LIMIT", "Google: Rate limit exceeded"
        else:
            return None, "API_ERROR", f"Gemini Error {response.status_code}"
    except requests.exceptions.Timeout:
        return None, "TIMEOUT", "Google: Request timed out (60s)"
    except requests.exceptions.ConnectionError:
        return None, "CONNECTION", "Google: Cannot connect"
    except Exception as e:
        return None, "UNKNOWN", f"Google: {str(e)[:80]}"

def call_agent(agent_name, messages, keys, prompts):
    system = prompts.get(agent_name, DEFAULT_PROMPTS.get(agent_name, "You are a helpful AI."))
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
    return None, "UNKNOWN_AGENT", f"Unknown agent: {agent_name}"

def test_api_connection(agent_name, keys):
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
    return (True, "Connected") if resp else (False, err_msg)

def format_messages(conversation):
    messages = []
    for entry in conversation:
        if entry["speaker"] == "CONDUCTOR":
            messages.append({"role": "user", "content": entry["content"]})
        elif entry["speaker"] not in ["SYSTEM", "NOTE", "ERROR", "WARNING"]:
            messages.append({"role": "assistant", "content": f"[{entry['speaker']}]: {entry['content']}"})
    return messages

# ============================================
# SESSION STATE
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
    
    # API Keys Section
    with st.expander("🔑 API Keys", expanded=not st.session_state.session_started):
        if has_secrets:
            st.success("✅ API keys loaded from Secrets!")
            keys = secret_keys.copy()
            # Show status
            st.write("🟤 Claude:", "✓" if keys.get("anthropic") else "✗")
            st.write("🟢 Sophia/Lyra:", "✓" if keys.get("openai") else "✗")
            st.write("🔴 Grok:", "✓" if keys.get("xai") else "✗")
            st.write("🔵 Gemini:", "✓" if keys.get("google") else "✗")
        else:
            st.info("Enter API keys manually:")
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
        
        if st.session_state.api_status:
            st.markdown("**Status:**")
            for agent, (ok, msg) in st.session_state.api_status.items():
                emoji = AGENT_EMOJIS.get(agent, "💬")
                st.write(f"{emoji} {agent}: {'✅' if ok else '❌ ' + msg}")
    
    # Agents Section
    st.subheader("👥 Agents")
    available = ["Claude", "Sophia", "Grok", "Gemini", "Lyra"]
    st.session_state.active_agents = st.multiselect("Active:", available, default=st.session_state.active_agents)
    
    # Order Section
    with st.expander("📝 Agent Order"):
        active_in_order = [a for a in st.session_state.agent_order if a in st.session_state.active_agents]
        for i, agent in enumerate(active_in_order):
            st.write(f"{i+1}. {AGENT_EMOJIS.get(agent, '💬')} {agent}")
        
        st.markdown("---")
        st.write("**Quick Presets:**")
        cols = st.columns(3)
        for i, agent in enumerate(["Claude", "Sophia", "Grok"]):
            with cols[i]:
                if st.button(f"{agent} 1st", key=f"preset_{agent}"):
                    order = [agent] + [a for a in st.session_state.agent_order if a != agent]
                    st.session_state.agent_order = order
                    st.rerun()
        cols2 = st.columns(2)
        with cols2[0]:
            if st.button("Gemini 1st"):
                order = ["Gemini"] + [a for a in st.session_state.agent_order if a != "Gemini"]
                st.session_state.agent_order = order
                st.rerun()
        with cols2[1]:
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
    st.markdown("""
    ## Welcome, Conductor! 🎹
    
    ### V8.1 Complete Features:
    - **Password Protected** — Only invited collaborators
    - **Secrets Integration** — API keys pre-loaded (Streamlit Cloud)
    - **Robust Error Handling** — Clear warnings when APIs fail
    - **No Silent Failures** — Failed agents show errors
    - **Connection Testing** — Verify APIs before starting
    
    ### Models:
    | Agent | Model | Provider |
    |-------|-------|----------|
    | 🟤 Claude | claude-sonnet-4-20250514 | Anthropic |
    | 🟢 Sophia | gpt-4o | OpenAI |
    | 🔴 Grok | grok-3 | xAI |
    | 🔵 Gemini | gemini-2.0-flash | Google |
    | 🟣 Lyra | gpt-4o | OpenAI |
    
    ---
    *Synergistic Intelligence Focus Group V8.1 — Patent Pending — Tennessee 🎹*
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
    user_input = st.text_area("Your message:", key=f"main_input_{st.session_state.input_counter}", height=80, placeholder="Type your question here...")
    
    # BUTTONS
    col1, col2, col3 = st.columns([2, 1, 2])
    with col1:
        ask_all = st.button("🎯 Ask All (In Order)", type="primary", use_container_width=True)
    with col2:
        add_note = st.button("📝 Note", use_container_width=True)
    
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
                    st.session_state.conversation.append({"speaker": agent, "content": resp})
                else:
                    failed_agents.append(agent)
                    provider = AGENT_PROVIDERS.get(agent, "Unknown")
                    st.session_state.conversation.append({
                        "speaker": "ERROR", 
                        "content": f"**{agent}** ({provider}) failed: {err_msg} [{err_code}]"
                    })
        
        if failed_agents:
            st.session_state.conversation.append({
                "speaker": "WARNING",
                "content": f"**{len(failed_agents)} agent(s) failed:** {', '.join(failed_agents)}"
            })
        
        st.session_state.input_counter += 1
        st.rerun()
    
    # HANDLE NOTE
    if add_note and user_input:
        st.session_state.conversation.append({"speaker": "NOTE", "content": user_input})
        st.session_state.input_counter += 1
        st.rerun()
    
    # HANDLE INDIVIDUAL
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
                        "content": f"**{agent}** ({provider}) failed: {err_msg} [{err_code}]"
                    })
            st.session_state.input_counter += 1
            st.rerun()

# FOOTER
st.markdown("---")
st.markdown('<div style="text-align:center;color:#666;"><em>Synergistic Intelligence Focus Group V8.1 Complete — Patent Pending — Tennessee 🎹</em></div>', unsafe_allow_html=True)
