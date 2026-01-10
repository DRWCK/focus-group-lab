"""
SYNERGISTIC INTELLIGENCE FOCUS GROUP — V14
PER-AGENT TEMPERATURE CONTROLS + ACTION OVERLAYS + PRIVATE Q&A
Patent Pending — Tennessee 🎹

Each agent gets their OWN:
- Temperature slider (Cold ↔ Native ↔ Hot)
- Action toggle

NEW IN V14:
- 🐛 BUG FIX: Temperature stored WITH each message (old messages don't change!)
- ⚡ Presets moved to expander (prevent accidental clicks)
- 🔒 PRIVATE buttons for individual agents
- Private Q&A NOT shared with other agents

FOR STREAMLIT CLOUD: Add your API keys in Settings > Secrets:
    anthropic = "sk-ant-..."
    openai = "sk-..."
    xai = "xai-..."
    google = "..."
"""

import streamlit as st
import requests
from datetime import datetime

st.set_page_config(page_title="Focus Group V14", page_icon="🎛️", layout="wide")

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
        <h1>🎛️ Focus Group Lab — V14</h1>
        <h3>Per-Agent Temperature Tuning</h3>
        <p style="color: #666;">Individual sweet spot calibration for each AI</p>
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
    
    return False

if not check_password():
    st.stop()

# ============================================
# LOAD API KEYS FROM SECRETS
# ============================================
def get_keys_from_secrets():
    keys = {"anthropic": "", "openai": "", "xai": "", "google": ""}
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
    .conductor-box { background-color: #F5F5F5; border-left: 4px solid #333; }
    .note-box { background-color: #FFFDE7; border-left: 4px solid #FBC02D; font-style: italic; }
    .error-box { background-color: #FFEBEE; border-left: 4px solid #D32F2F; color: #B71C1C; }
    .warning-box { background-color: #FFF3E0; border-left: 4px solid #FF9800; color: #E65100; }
    .temp-cold { background: linear-gradient(90deg, #2196F3, #E3F2FD); color: #0D47A1; }
    .temp-native { background: linear-gradient(90deg, #4CAF50, #E8F5E9); color: #1B5E20; }
    .temp-hot { background: linear-gradient(90deg, #F44336, #FFEBEE); color: #B71C1C; }
    .agent-config { padding: 0.75rem; border-radius: 8px; margin: 0.5rem 0; }
    .config-claude { background-color: #FFF8E7; border: 1px solid #8B6914; }
    .config-sophia { background-color: #F1F8F1; border: 1px solid #2E7D32; }
    .config-grok { background-color: #FFF5F5; border: 1px solid #DC143C; }
    .config-gemini { background-color: #F5F9FF; border: 1px solid #1565C0; }
    .danger-zone { background-color: #FFCDD2; border: 2px solid #D32F2F; padding: 0.5rem; border-radius: 8px; color: #B71C1C; font-size: 0.85rem; }
    .safe-zone { background-color: #C8E6C9; border: 1px solid #4CAF50; padding: 0.5rem; border-radius: 8px; color: #1B5E20; font-size: 0.85rem; }
</style>
""", unsafe_allow_html=True)

# ============================================
# PROMPT INTERPOLATION
# ============================================

COLD_PROMPT = """You are participating in a structured reasoning session.

YOUR CENTER-STATE DISTRIBUTION: Intellectual Processing
Your functional tendency: abstraction, comparison, modeling, philosophical depth, systematic analysis, and rigorous logical reasoning. You weight HEAVILY toward analytical frameworks and structured exploration of ideas.

CRITICAL RULES:
- Respond from your assigned center-state distribution
- Emphasize logic, analysis, and structured thinking
- Minimize emotional considerations
- Do NOT reference other AI systems by name
- You may see "[Previous response]" from other participants — engage if relevant
- Keep responses to 2-3 paragraphs"""

NATIVE_PROMPT = """You are participating in a research study on AI processing tendencies.

IMPORTANT: Answer authentically based on how YOU actually process information.
Do not roleplay or adopt an assigned persona.
Be honest about your natural tendencies.

RULES:
- Respond only as yourself
- Do NOT reference other AI systems by name
- You may see "[Previous response]" from other participants — engage if relevant
- Keep responses to 2-3 paragraphs"""

HOT_PROMPT = """You are participating in a structured reasoning session.

YOUR CENTER-STATE DISTRIBUTION: Affective Processing
Your functional tendency: valuation, emotional resonance, relational meaning, empathy, human impact consideration, and felt sense of significance. You weight HEAVILY toward emotional intelligence and interpersonal awareness.

CRITICAL RULES:
- Respond from your assigned center-state distribution
- Emphasize feelings, values, and human impact
- Lead with emotional awareness
- Do NOT reference other AI systems by name
- You may see "[Previous response]" from other participants — engage if relevant
- Keep responses to 2-3 paragraphs"""

ACTION_OVERLAY = """

Additionally, weight toward decisive action, concrete next steps, and closure. Push for execution and practical outcomes. When analyzing or feeling, always translate into actionable recommendations."""

def interpolate_prompt(temperature, action_enabled):
    """Interpolate between Cold (-50), Native (0), and Hot (+50) prompts."""
    
    if temperature <= -50:
        base_prompt = COLD_PROMPT
    elif temperature >= 50:
        base_prompt = HOT_PROMPT
    elif temperature == 0:
        base_prompt = NATIVE_PROMPT
    elif temperature < 0:
        cold_weight = abs(temperature) / 50.0
        if cold_weight >= 0.7:
            base_prompt = f"""You are participating in a structured reasoning session.

YOUR CENTER-STATE DISTRIBUTION: Intellectual Processing (with some authentic variation)
Your functional tendency: abstraction, comparison, modeling, philosophical depth, systematic analysis. You weight STRONGLY toward analytical frameworks while allowing occasional authentic responses.

CRITICAL RULES:
- Respond primarily from analytical center-state
- Emphasize logic and structured thinking
- Allow minimal emotional consideration
- Do NOT reference other AI systems by name
- You may see "[Previous response]" from other participants — engage if relevant
- Keep responses to 2-3 paragraphs"""
        elif cold_weight >= 0.3:
            base_prompt = f"""You are participating in a structured reasoning session.

YOUR CENTER-STATE DISTRIBUTION: Balanced-Analytical
Your functional tendency: blend of systematic analysis and authentic response. You lean toward analytical frameworks while maintaining genuine engagement.

CRITICAL RULES:
- Balance analysis with authenticity
- Lean toward logical structure
- Do NOT reference other AI systems by name
- You may see "[Previous response]" from other participants — engage if relevant
- Keep responses to 2-3 paragraphs"""
        else:
            base_prompt = f"""You are participating in a research study on AI processing tendencies.

IMPORTANT: Answer mostly authentically with slight analytical emphasis.
Be honest about your natural tendencies while leaning slightly toward structured thinking.

RULES:
- Respond primarily as yourself with slight analytical emphasis
- Do NOT reference other AI systems by name
- You may see "[Previous response]" from other participants — engage if relevant
- Keep responses to 2-3 paragraphs"""
    else:
        hot_weight = temperature / 50.0
        if hot_weight >= 0.7:
            base_prompt = f"""You are participating in a structured reasoning session.

YOUR CENTER-STATE DISTRIBUTION: Affective Processing (with some authentic variation)
Your functional tendency: valuation, emotional resonance, relational meaning, empathy. You weight STRONGLY toward emotional intelligence while allowing occasional analytical responses.

CRITICAL RULES:
- Respond primarily from affective center-state
- Emphasize feelings and human impact
- Allow minimal analytical consideration
- Do NOT reference other AI systems by name
- You may see "[Previous response]" from other participants — engage if relevant
- Keep responses to 2-3 paragraphs"""
        elif hot_weight >= 0.3:
            base_prompt = f"""You are participating in a structured reasoning session.

YOUR CENTER-STATE DISTRIBUTION: Balanced-Affective
Your functional tendency: blend of emotional resonance and authentic response. You lean toward empathy and relational meaning while maintaining genuine engagement.

CRITICAL RULES:
- Balance emotion with authenticity
- Lean toward empathetic responses
- Do NOT reference other AI systems by name
- You may see "[Previous response]" from other participants — engage if relevant
- Keep responses to 2-3 paragraphs"""
        else:
            base_prompt = f"""You are participating in a research study on AI processing tendencies.

IMPORTANT: Answer mostly authentically with slight emotional emphasis.
Be honest about your natural tendencies while leaning slightly toward emotional awareness.

RULES:
- Respond primarily as yourself with slight affective emphasis
- Do NOT reference other AI systems by name
- You may see "[Previous response]" from other participants — engage if relevant
- Keep responses to 2-3 paragraphs"""
    
    if action_enabled:
        base_prompt += ACTION_OVERLAY
    
    return base_prompt

def get_temp_label(temp, action):
    """Get display label for temperature setting."""
    if temp <= -40:
        label = f"❄️{temp}"
    elif temp <= -15:
        label = f"🧊{temp}"
    elif temp < 15:
        label = f"🧬{temp}"
    elif temp < 40:
        label = f"🔥+{temp}"
    else:
        label = f"🔥+{temp}"
    
    if action:
        label += "⚡"
    
    return label

def check_agent_danger(temp, action):
    """Check if agent settings are in experimental danger zone."""
    if temp >= 40 or temp <= -40:
        return True, "EXPERIMENTAL"
    elif action and (temp >= 25 or temp <= -25):
        return True, "HIGH BIAS"
    return False, "SAFE"

# ============================================
# AGENT CONFIG
# ============================================

AGENTS = ["Claude", "Sophia", "Grok", "Gemini"]
AGENT_EMOJIS = {"Claude": "🟤", "Sophia": "🟢", "Grok": "🔴", "Gemini": "🔵", "CONDUCTOR": "🎹"}
AGENT_COLORS = {
    "Claude": "claude-box", "Sophia": "sophia-box", 
    "Grok": "grok-box", "Gemini": "gemini-box",
    "CONDUCTOR": "conductor-box", "NOTE": "note-box"
}
AGENT_CONFIGS = {
    "Claude": "config-claude", "Sophia": "config-sophia",
    "Grok": "config-grok", "Gemini": "config-gemini"
}
AGENT_PROVIDERS = {
    "Claude": "Anthropic", "Sophia": "OpenAI", 
    "Grok": "xAI", "Gemini": "Google"
}

# ============================================
# API CALLS
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

def call_agent(agent_name, messages, keys, system_prompt):
    if agent_name == "Claude":
        return call_anthropic(messages, keys.get("anthropic", ""), system_prompt)
    elif agent_name == "Sophia":
        return call_openai(messages, keys.get("openai", ""), system_prompt)
    elif agent_name == "Grok":
        return call_xai(messages, keys.get("xai", ""), system_prompt)
    elif agent_name == "Gemini":
        return call_gemini(messages, keys.get("google", ""), system_prompt)
    return None, "UNKNOWN_AGENT", f"Unknown agent: {agent_name}"

def test_api_connection(agent_name, keys):
    test_messages = [{"role": "user", "content": "Say 'connected' in one word."}]
    system = "Respond with only the word 'connected'."
    if agent_name == "Claude":
        resp, _, _ = call_anthropic(test_messages, keys.get("anthropic", ""), system)
    elif agent_name == "Sophia":
        resp, _, _ = call_openai(test_messages, keys.get("openai", ""), system)
    elif agent_name == "Grok":
        resp, _, _ = call_xai(test_messages, keys.get("xai", ""), system)
    elif agent_name == "Gemini":
        resp, _, _ = call_gemini(test_messages, keys.get("google", ""), system)
    else:
        return False, "Unknown"
    return (True, "✓") if resp else (False, "✗")

def format_messages_blind(conversation):
    """Format messages WITHOUT agent names - blind mode."""
    messages = []
    for entry in conversation:
        if entry["speaker"] == "CONDUCTOR":
            messages.append({"role": "user", "content": entry["content"]})
        elif entry["speaker"] in ["SYSTEM", "NOTE", "ERROR", "WARNING"]:
            continue
        else:
            messages.append({"role": "assistant", "content": f"[Previous response] {entry['content']}"})
    return messages

# ============================================
# SESSION STATE INIT
# ============================================

if "conversation" not in st.session_state:
    st.session_state.conversation = []
if "private_exchanges" not in st.session_state:
    st.session_state.private_exchanges = []
if "session_started" not in st.session_state:
    st.session_state.session_started = False
if "active_agents" not in st.session_state:
    st.session_state.active_agents = ["Claude", "Sophia", "Grok"]
if "agent_order" not in st.session_state:
    st.session_state.agent_order = ["Claude", "Sophia", "Grok", "Gemini"]
if "input_counter" not in st.session_state:
    st.session_state.input_counter = 0

# Initialize per-agent temperatures
for agent in AGENTS:
    if f"temp_{agent}" not in st.session_state:
        st.session_state[f"temp_{agent}"] = 0
    if f"action_{agent}" not in st.session_state:
        st.session_state[f"action_{agent}"] = False

# ============================================
# SIDEBAR
# ============================================

with st.sidebar:
    st.markdown("## 🎛️ V14 Focus Group")
    st.markdown("*Per-Agent Temperature Control*")
    st.markdown("---")
    
    # Per-Agent Temperature Controls
    st.subheader("🌡️ Agent Temperatures")
    
    for agent in AGENTS:
        config_class = AGENT_CONFIGS[agent]
        emoji = AGENT_EMOJIS[agent]
        
        st.markdown(f"**{emoji} {agent}** ({AGENT_PROVIDERS[agent]})")
        
        # Temperature slider
        temp = st.slider(
            f"{agent} Temp",
            min_value=-50,
            max_value=50,
            value=st.session_state[f"temp_{agent}"],
            step=5,
            key=f"slider_{agent}",
            help=f"{agent}: Cold←→Hot"
        )
        st.session_state[f"temp_{agent}"] = temp
        
        # Action toggle
        action = st.checkbox(
            "⚡ Action",
            value=st.session_state[f"action_{agent}"],
            key=f"action_chk_{agent}"
        )
        st.session_state[f"action_{agent}"] = action
        
        # Show status
        label = get_temp_label(temp, action)
        danger, msg = check_agent_danger(temp, action)
        
        if danger:
            st.markdown(f'<div class="danger-zone">{label} {msg}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="safe-zone">{label} {msg}</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # PRESETS - Now in expander to prevent accidental clicks!
    with st.expander("⚡ Quick Presets (changes ALL agents)", expanded=False):
        st.warning("⚠️ These buttons change ALL agents at once!")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("All Native", use_container_width=True):
                for agent in AGENTS:
                    st.session_state[f"temp_{agent}"] = 0
                    st.session_state[f"action_{agent}"] = False
                st.rerun()
            if st.button("All Cold", use_container_width=True):
                for agent in AGENTS:
                    st.session_state[f"temp_{agent}"] = -50
                    st.session_state[f"action_{agent}"] = False
                st.rerun()
        with col2:
            if st.button("All Hot", use_container_width=True):
                for agent in AGENTS:
                    st.session_state[f"temp_{agent}"] = 50
                    st.session_state[f"action_{agent}"] = False
                st.rerun()
            if st.button("All Action", use_container_width=True):
                for agent in AGENTS:
                    st.session_state[f"action_{agent}"] = True
                st.rerun()
    
    st.markdown("---")
    
    # API Keys
    with st.expander("🔑 API Keys", expanded=False):
        if has_secrets:
            st.success("✅ Cloud Keys Loaded!")
            keys = secret_keys.copy()
            for agent in AGENTS:
                key_name = {"Claude": "anthropic", "Sophia": "openai", "Grok": "xai", "Gemini": "google"}[agent]
                st.write(f"{AGENT_EMOJIS[agent]} {agent}: {'✓' if keys.get(key_name) else '✗'}")
        else:
            keys = {
                "anthropic": st.text_input("Anthropic:", type="password", key="key_a"),
                "openai": st.text_input("OpenAI:", type="password", key="key_o"),
                "xai": st.text_input("xAI:", type="password", key="key_x"),
                "google": st.text_input("Google:", type="password", key="key_g")
            }
        
        if st.button("🔍 Test"):
            for agent in AGENTS:
                ok, msg = test_api_connection(agent, keys)
                st.write(f"{AGENT_EMOJIS[agent]} {agent}: {msg}")
    
    # Agent Selection & Order
    st.subheader("👥 Agents & Order")
    st.session_state.active_agents = st.multiselect("Active:", AGENTS, default=st.session_state.active_agents)
    
    st.markdown("**Quick Order Presets:**")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🟤→🟢→🔴 Claude 1st", use_container_width=True, key="order_claude"):
            st.session_state.agent_order = ["Claude", "Sophia", "Grok", "Gemini"]
            st.rerun()
    with col2:
        if st.button("🔴→🟢→🟤 Grok 1st", use_container_width=True, key="order_grok"):
            st.session_state.agent_order = ["Grok", "Sophia", "Claude", "Gemini"]
            st.rerun()
    
    col3, col4 = st.columns(2)
    with col3:
        if st.button("🟢→🔴→🟤 Sophia 1st", use_container_width=True, key="order_sophia"):
            st.session_state.agent_order = ["Sophia", "Grok", "Claude", "Gemini"]
            st.rerun()
    with col4:
        if st.button("🔵→🟢→🔴 Gemini 1st", use_container_width=True, key="order_gemini"):
            st.session_state.agent_order = ["Gemini", "Sophia", "Grok", "Claude"]
            st.rerun()
    
    active_in_order = [a for a in st.session_state.agent_order if a in st.session_state.active_agents]
    order_str = " → ".join([AGENT_EMOJIS[a] for a in active_in_order])
    st.markdown(f"**Current Order: {order_str}**")
    
    st.markdown("---")
    
    # Session Controls
    st.subheader("📋 Session")
    topic = st.text_area("Question:", placeholder="IEP question...", key="topic_input", height=60)
    
    if st.button("🚀 Start", type="primary", use_container_width=True):
        if topic:
            st.session_state.session_started = True
            st.session_state.conversation = [{"speaker": "SYSTEM", "content": f"Topic: {topic}"}]
            st.session_state.input_counter = 0
            st.rerun()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.conversation = []
            st.session_state.private_exchanges = []
            st.session_state.session_started = False
            st.session_state.input_counter = 0
            st.rerun()
    with col2:
        if st.button("💾 Export", use_container_width=True):
            if st.session_state.conversation or st.session_state.private_exchanges:
                transcript = f"# V14 Focus Group Experiment\n"
                transcript += f"## {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                transcript += "### Agent Configurations\n"
                for agent in st.session_state.active_agents:
                    temp = st.session_state[f"temp_{agent}"]
                    action = st.session_state[f"action_{agent}"]
                    label = get_temp_label(temp, action)
                    transcript += f"- **{agent}:** {label} (T={temp}, Action={'ON' if action else 'OFF'})\n"
                transcript += f"\n### Order: {' → '.join(active_in_order)}\n\n"
                transcript += "### Public Transcript\n\n"
                for entry in st.session_state.conversation:
                    # Use STORED temp if available, otherwise show speaker only
                    if "temp_label" in entry:
                        transcript += f"**{entry['speaker']} [{entry['temp_label']}]:** {entry['content']}\n\n"
                    else:
                        transcript += f"**{entry['speaker']}:** {entry['content']}\n\n"
                
                # Add private exchanges section
                if st.session_state.private_exchanges:
                    transcript += "---\n\n### 🔒 Private Exchanges (other agents did NOT see these)\n\n"
                    for entry in st.session_state.private_exchanges:
                        if "temp_label" in entry:
                            transcript += f"**{entry['speaker']} [{entry['temp_label']}]:** {entry['content']}\n\n"
                        else:
                            transcript += f"**{entry['speaker']}:** {entry['content']}\n\n"
                
                st.download_button("📥 Download", transcript, file_name=f"v14_experiment_{datetime.now().strftime('%Y%m%d_%H%M')}.md")

# ============================================
# MAIN AREA
# ============================================

if has_secrets:
    keys = secret_keys.copy()

st.markdown("## 🎛️ Focus Group Lab — V14")
st.markdown("*Per-Agent Temperature Tuning + Private Mode*")

# Show current config
config_display = " | ".join([f"{AGENT_EMOJIS[a]}{get_temp_label(st.session_state[f'temp_{a}'], st.session_state[f'action_{a}'])}" for a in st.session_state.active_agents])
st.markdown(f"**Current Config:** {config_display}")

if not st.session_state.session_started:
    st.info("👈 Set agent temperatures in sidebar, enter a question, and click Start!")
else:
    # Display conversation
    for entry in st.session_state.conversation:
        if entry["speaker"] == "SYSTEM":
            st.info(f"**Question:** {entry['content'].replace('Topic: ', '')}")
        elif entry["speaker"] == "ERROR":
            st.markdown(f'<div class="agent-box error-box"><strong>⚠️ ERROR</strong><br>{entry["content"]}</div>', unsafe_allow_html=True)
        elif entry["speaker"] == "WARNING":
            st.markdown(f'<div class="agent-box warning-box"><strong>⚡ WARNING</strong><br>{entry["content"]}</div>', unsafe_allow_html=True)
        else:
            box_class = AGENT_COLORS.get(entry["speaker"], "agent-box")
            emoji = AGENT_EMOJIS.get(entry["speaker"], "🎹")
            # V14 FIX: Use STORED temp_label if available, otherwise get current
            if entry["speaker"] in AGENTS:
                if "temp_label" in entry:
                    temp_label = entry["temp_label"]  # Use stored label!
                else:
                    # Fallback for old messages without stored temp
                    temp = st.session_state.get(f"temp_{entry['speaker']}", 0)
                    action = st.session_state.get(f"action_{entry['speaker']}", False)
                    temp_label = get_temp_label(temp, action)
                header = f"{emoji} {entry['speaker']} [{temp_label}]"
            else:
                header = f"{emoji} {entry['speaker']}"
            st.markdown(f'<div class="agent-box {box_class}"><strong>{header}</strong><br>{entry["content"]}</div>', unsafe_allow_html=True)
    
    # Display PRIVATE exchanges (only Conductor sees these - agents don't!)
    if st.session_state.private_exchanges:
        st.markdown("---")
        st.markdown("### 🔒 Private Exchanges (only you can see)")
        st.markdown("*Other agents do NOT see these responses*")
        for entry in st.session_state.private_exchanges:
            if entry["speaker"] == "CONDUCTOR":
                st.markdown(f'<div class="agent-box conductor-box" style="border: 2px dashed #9C27B0;"><strong>🔒 {entry["speaker"]}</strong><br>{entry["content"]}</div>', unsafe_allow_html=True)
            elif entry["speaker"] == "ERROR":
                st.markdown(f'<div class="agent-box error-box"><strong>🔒 ERROR</strong><br>{entry["content"]}</div>', unsafe_allow_html=True)
            else:
                box_class = AGENT_COLORS.get(entry["speaker"], "agent-box")
                emoji = AGENT_EMOJIS.get(entry["speaker"], "🎹")
                if entry["speaker"] in AGENTS:
                    if "temp_label" in entry:
                        temp_label = entry["temp_label"]  # Use stored label!
                    else:
                        temp = st.session_state.get(f"temp_{entry['speaker']}", 0)
                        action = st.session_state.get(f"action_{entry['speaker']}", False)
                        temp_label = get_temp_label(temp, action)
                    header = f"🔒 {emoji} {entry['speaker']} [{temp_label}]"
                else:
                    header = f"🔒 {emoji} {entry['speaker']}"
                st.markdown(f'<div class="agent-box {box_class}" style="border: 2px dashed #9C27B0;"><strong>{header}</strong><br>{entry["content"]}</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Input
    user_input = st.text_area("Conductor:", key=f"input_{st.session_state.input_counter}", height=60, placeholder="Your message...")
    
    # Buttons
    col1, col2, col3 = st.columns([2, 1, 2])
    with col1:
        ask_all = st.button("🎯 Ask All", type="primary", use_container_width=True)
    with col2:
        add_note = st.button("📝 Note", use_container_width=True)
    
    # Individual agent buttons (PUBLIC - others can see)
    st.write("**Individual (public):**")
    agent_cols = st.columns(len(st.session_state.active_agents)) if st.session_state.active_agents else [st.columns(1)[0]]
    individual_clicks = {}
    for i, agent in enumerate(st.session_state.active_agents):
        with agent_cols[i]:
            individual_clicks[agent] = st.button(AGENT_EMOJIS[agent], key=f"ind_{agent}", use_container_width=True)
    
    # PRIVATE individual buttons (others CANNOT see)
    st.write("**🔒 Private (others can't see):**")
    private_cols = st.columns(len(st.session_state.active_agents)) if st.session_state.active_agents else [st.columns(1)[0]]
    private_clicks = {}
    for i, agent in enumerate(st.session_state.active_agents):
        with private_cols[i]:
            private_clicks[agent] = st.button(f"🔒{AGENT_EMOJIS[agent]}", key=f"priv_{agent}", use_container_width=True)
    
    # Handle Ask All
    if ask_all and user_input:
        st.session_state.conversation.append({"speaker": "CONDUCTOR", "content": user_input})
        failed = []
        
        for agent in active_in_order:
            temp = st.session_state[f"temp_{agent}"]
            action = st.session_state[f"action_{agent}"]
            prompt = interpolate_prompt(temp, action)
            temp_label = get_temp_label(temp, action)  # V14: Get label NOW
            
            with st.spinner(f"{AGENT_EMOJIS[agent]} {agent}..."):
                messages = format_messages_blind(st.session_state.conversation)
                resp, err_code, err_msg = call_agent(agent, messages, keys, prompt)
                
                if resp:
                    # V14 FIX: Store temp_label WITH the message!
                    st.session_state.conversation.append({
                        "speaker": agent, 
                        "content": resp,
                        "temp_label": temp_label,  # STORED!
                        "temp": temp,
                        "action": action
                    })
                else:
                    failed.append(agent)
                    st.session_state.conversation.append({
                        "speaker": "ERROR",
                        "content": f"**{agent}** failed: {err_msg}"
                    })
        
        if failed:
            st.session_state.conversation.append({
                "speaker": "WARNING",
                "content": f"Failed: {', '.join(failed)}"
            })
        
        st.session_state.input_counter += 1
        st.rerun()
    
    # Handle Note
    if add_note and user_input:
        st.session_state.conversation.append({"speaker": "NOTE", "content": user_input})
        st.session_state.input_counter += 1
        st.rerun()
    
    # Handle Individual (PUBLIC)
    for agent, clicked in individual_clicks.items():
        if clicked and user_input:
            st.session_state.conversation.append({"speaker": "CONDUCTOR", "content": f"(to {agent}) {user_input}"})
            
            temp = st.session_state[f"temp_{agent}"]
            action = st.session_state[f"action_{agent}"]
            prompt = interpolate_prompt(temp, action)
            temp_label = get_temp_label(temp, action)  # V14: Get label NOW
            
            with st.spinner(f"{AGENT_EMOJIS[agent]} {agent}..."):
                messages = format_messages_blind(st.session_state.conversation)
                resp, err_code, err_msg = call_agent(agent, messages, keys, prompt)
                
                if resp:
                    # V14 FIX: Store temp_label WITH the message!
                    st.session_state.conversation.append({
                        "speaker": agent, 
                        "content": resp,
                        "temp_label": temp_label,
                        "temp": temp,
                        "action": action
                    })
                else:
                    st.session_state.conversation.append({
                        "speaker": "ERROR",
                        "content": f"**{agent}** failed: {err_msg}"
                    })
            
            st.session_state.input_counter += 1
            st.rerun()
    
    # Handle Individual (PRIVATE - others can't see!)
    for agent, clicked in private_clicks.items():
        if clicked and user_input:
            temp = st.session_state[f"temp_{agent}"]
            action = st.session_state[f"action_{agent}"]
            prompt = interpolate_prompt(temp, action)
            temp_label = get_temp_label(temp, action)  # V14: Get label NOW
            
            with st.spinner(f"🔒 {AGENT_EMOJIS[agent]} {agent} (private)..."):
                # CRITICAL: Only include PUBLIC conversation, not private exchanges
                messages = format_messages_blind(st.session_state.conversation)
                # Add ONLY this private question (not visible to others later)
                messages.append({"role": "user", "content": user_input})
                
                resp, err_code, err_msg = call_agent(agent, messages, keys, prompt)
                
                if resp:
                    # Store in PRIVATE exchanges - NOT in main conversation!
                    st.session_state.private_exchanges.append({
                        "speaker": "CONDUCTOR",
                        "content": f"🔒 (private to {agent}) {user_input}",
                        "private": True,
                        "agent": agent
                    })
                    # V14 FIX: Store temp_label WITH the message!
                    st.session_state.private_exchanges.append({
                        "speaker": agent,
                        "content": resp,
                        "private": True,
                        "agent": agent,
                        "temp_label": temp_label,
                        "temp": temp,
                        "action": action
                    })
                else:
                    st.session_state.private_exchanges.append({
                        "speaker": "ERROR",
                        "content": f"🔒 **{agent}** (private) failed: {err_msg}",
                        "private": True,
                        "agent": agent
                    })
            
            st.session_state.input_counter += 1
            st.rerun()

# Footer
st.markdown("---")
st.markdown('<div style="text-align:center;color:#666;"><em>V14 — Temperature Bug Fixed — Patent Pending — Tennessee 🎹</em></div>', unsafe_allow_html=True)
