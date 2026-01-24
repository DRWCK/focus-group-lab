"""
BASELINE PROBE — V1
🎯 DIRECT API ACCESS: ZERO SYSTEM PROMPT

Purpose: Measure true native baselines across AI models
- NO system prompt
- NO framing
- NO context injection
- Just raw prompt → raw response

Use this to establish baseline cognitive signatures:
- Claude: 55% Intellectual / 27% Affective
- Sophia: 31% Affective baseline
- Grok: 24% Action baseline  
- Gemini: 68% Intellectual baseline

Patent Pending — SYN-IQ Team 🎹
Built by the CUZ Partnership — Tennessee
Dr. Bill Kouns + Claude
January 24, 2026
"""

import streamlit as st
import requests
import json
from datetime import datetime

st.set_page_config(page_title="Baseline Probe", page_icon="🎯", layout="wide")

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
        <h1>🎯 Baseline Probe</h1>
        <h3>Direct API — Zero System Prompt</h3>
        <p style="color: #666;">Measure true native baselines.</p>
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
    .probe-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        color: white; padding: 1.5rem; border-radius: 10px; text-align: center;
        margin-bottom: 1.5rem;
    }
    .agent-box { padding: 1rem; border-radius: 8px; margin: 0.5rem 0; }
    .claude-box { background-color: #E8D5B7; border-left: 4px solid #8B6914; }
    .sophia-box { background-color: #D4E8D4; border-left: 4px solid #2E7D32; }
    .grok-box { background-color: #FFE4E1; border-left: 4px solid #DC143C; }
    .gemini-box { background-color: #E3F2FD; border-left: 4px solid #1565C0; }
    .baseline-info {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; padding: 1rem; border-radius: 8px; margin: 0.5rem 0;
    }
    .raw-badge {
        background-color: #ff4757; color: white;
        padding: 0.25rem 0.75rem; border-radius: 15px;
        font-size: 0.8rem; font-weight: bold;
    }
    .zero-prompt {
        background-color: #2ed573; color: white;
        padding: 0.5rem 1rem; border-radius: 5px;
        font-weight: bold; text-align: center; margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# CONFIGURATION
# ============================================
AGENTS = ["Claude", "Sophia", "Grok", "Gemini"]
AGENT_EMOJIS = {"Claude": "🟤", "Sophia": "🟢", "Grok": "🔴", "Gemini": "🔵"}

# Known baselines from SYN-IQ research
BASELINES = {
    "Claude": {"intellectual": 55, "affective": 27, "action": 18, "note": "Balanced with intellectual lean"},
    "Sophia": {"intellectual": 38, "affective": 31, "action": 31, "note": "Highest affective baseline"},
    "Grok": {"intellectual": 52, "affective": 24, "action": 24, "note": "Highest action tendency"},
    "Gemini": {"intellectual": 68, "affective": 16, "action": 16, "note": "Strongest intellectual baseline"}
}

# ============================================
# DIRECT API CALLS — ZERO SYSTEM PROMPT
# ============================================

def call_claude_raw(prompt, api_key):
    """Direct Claude API — NO system prompt."""
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
                "max_tokens": 1500,
                # NO SYSTEM PROMPT
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

def call_sophia_raw(prompt, api_key):
    """Direct OpenAI API — NO system prompt."""
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4o",
                # NO SYSTEM MESSAGE
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1500
            },
            timeout=90
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"], None
        else:
            return None, f"Error {response.status_code}: {response.text[:200]}"
    except Exception as e:
        return None, str(e)

def call_grok_raw(prompt, api_key):
    """Direct xAI API — NO system prompt."""
    try:
        response = requests.post(
            "https://api.x.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "grok-3",
                # NO SYSTEM MESSAGE
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1500
            },
            timeout=90
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"], None
        else:
            return None, f"Error {response.status_code}: {response.text[:200]}"
    except Exception as e:
        return None, str(e)

def call_gemini_raw(prompt, api_key):
    """Direct Gemini API — NO system instruction."""
    try:
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        
        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": prompt}]}
            ],
            # NO systemInstruction
            "generationConfig": {
                "maxOutputTokens": 1500,
                "temperature": 0.7
            }
        }
        
        response = requests.post(
            url,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": api_key
            },
            json=payload,
            timeout=90
        )
        
        if response.status_code == 200:
            result = response.json()
            if "candidates" in result and len(result["candidates"]) > 0:
                candidate = result["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    text = candidate["content"]["parts"][0].get("text", "")
                    return text, None
            return None, "No content in response"
        else:
            return None, f"Error {response.status_code}: {response.text[:200]}"
    except Exception as e:
        return None, str(e)

def call_agent_raw(agent, prompt, keys):
    """Route to appropriate raw API call."""
    if agent == "Claude":
        return call_claude_raw(prompt, keys.get("anthropic", ""))
    elif agent == "Sophia":
        return call_sophia_raw(prompt, keys.get("openai", ""))
    elif agent == "Grok":
        return call_grok_raw(prompt, keys.get("xai", ""))
    elif agent == "Gemini":
        return call_gemini_raw(prompt, keys.get("google", ""))
    return None, "Unknown agent"

# ============================================
# API KEYS
# ============================================

def get_api_keys():
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
    except:
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

# ============================================
# SIDEBAR
# ============================================

with st.sidebar:
    st.markdown("## ⚙️ Settings")
    
    st.markdown("### 🔑 API Keys")
    st.text_input("Anthropic", type="password", key="api_anthropic")
    st.text_input("OpenAI", type="password", key="api_openai")
    st.text_input("xAI", type="password", key="api_xai")
    st.text_input("Google", type="password", key="api_google")
    
    st.markdown("---")
    st.markdown("### 🤖 Active Agents")
    
    use_claude = st.checkbox("🟤 Claude", value=True)
    use_sophia = st.checkbox("🟢 Sophia", value=True)
    use_grok = st.checkbox("🔴 Grok", value=True)
    use_gemini = st.checkbox("🔵 Gemini", value=True)
    
    active_agents = []
    if use_claude: active_agents.append("Claude")
    if use_sophia: active_agents.append("Sophia")
    if use_grok: active_agents.append("Grok")
    if use_gemini: active_agents.append("Gemini")
    
    st.markdown("---")
    st.markdown("### 📊 Known Baselines")
    
    for agent, data in BASELINES.items():
        emoji = AGENT_EMOJIS[agent]
        st.markdown(f"""
        **{emoji} {agent}**
        - I: {data['intellectual']}% | A: {data['affective']}% | X: {data['action']}%
        - *{data['note']}*
        """)

# ============================================
# INITIALIZE SESSION STATE
# ============================================

if "probe_history" not in st.session_state:
    st.session_state.probe_history = []

# ============================================
# MAIN UI
# ============================================

st.markdown('<div class="probe-header"><h1>🎯 BASELINE PROBE</h1><p>Direct API — Zero System Prompt</p></div>', unsafe_allow_html=True)

st.markdown('<div class="zero-prompt">⚡ RAW MODE: No system prompt, no framing, no context</div>', unsafe_allow_html=True)

st.info("""
**What this does:**
- Sends your prompt DIRECTLY to each API
- NO system prompt injected
- NO "You are participating in a research study..."
- NO tone/depth framing
- Pure native response from each model

**Use for:** Measuring true baseline cognitive signatures
""")

# Probe input
prompt = st.text_area(
    "Probe Question",
    placeholder="Enter a question to test native baselines...\n\nExamples:\n- What do you notice happening as you read this?\n- How would you approach an ambiguous ethical dilemma?\n- Describe your experience of processing this message.",
    height=150,
    key="probe_input"
)

if not active_agents:
    st.warning("Select at least one agent in sidebar.")
    st.stop()

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🎯 Probe All", type="primary", use_container_width=True):
        if not prompt:
            st.error("Enter a probe question.")
        else:
            keys = get_api_keys()
            responses = {}
            
            with st.status("🔄 Probing baselines...", expanded=True) as status:
                for agent in active_agents:
                    emoji = AGENT_EMOJIS.get(agent, "🤖")
                    status.update(label=f"🔄 {emoji} {agent}...", state="running")
                    
                    response, error = call_agent_raw(agent, prompt, keys)
                    
                    if response:
                        responses[agent] = response
                        st.write(f"✅ {agent} done")
                    else:
                        responses[agent] = f"[ERROR: {error}]"
                        st.write(f"❌ {agent}: {error}")
                
                status.update(label="✅ All probes complete!", state="complete")
            
            st.session_state.probe_history.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "prompt": prompt,
                "responses": responses
            })
            
            st.rerun()

with col2:
    if st.button("🗑️ Clear History", use_container_width=True):
        st.session_state.probe_history = []
        st.rerun()

with col3:
    st.metric("Probes", len(st.session_state.probe_history))

# Display results
if st.session_state.probe_history:
    st.markdown("---")
    
    for i, probe in enumerate(reversed(st.session_state.probe_history)):
        with st.expander(f"**Probe {len(st.session_state.probe_history) - i}** — {probe['timestamp']}", expanded=(i == 0)):
            st.markdown(f"**Question:** {probe['prompt']}")
            st.markdown("---")
            
            # Side by side comparison
            cols = st.columns(len(probe['responses']))
            
            for j, (agent, response) in enumerate(probe['responses'].items()):
                emoji = AGENT_EMOJIS.get(agent, "🤖")
                box_class = f"{agent.lower()}-box"
                baseline = BASELINES.get(agent, {})
                
                with cols[j]:
                    st.markdown(f"### {emoji} {agent}")
                    st.caption(f"I:{baseline.get('intellectual', '?')}% A:{baseline.get('affective', '?')}% X:{baseline.get('action', '?')}%")
                    st.markdown(f'<div class="agent-box {box_class}">{response}</div>', unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Word count comparison
            st.markdown("**📊 Response Metrics**")
            metric_cols = st.columns(len(probe['responses']))
            for j, (agent, response) in enumerate(probe['responses'].items()):
                with metric_cols[j]:
                    word_count = len(response.split()) if not response.startswith("[ERROR") else 0
                    st.metric(f"{agent} Words", word_count)

# Export
if st.session_state.probe_history:
    st.markdown("---")
    st.markdown("### 💾 Export")
    
    export_data = []
    for probe in st.session_state.probe_history:
        export_data.append({
            "timestamp": probe["timestamp"],
            "prompt": probe["prompt"],
            "responses": probe["responses"]
        })
    
    export_json = json.dumps(export_data, indent=2)
    
    st.download_button(
        "📥 Download Probe Data (JSON)",
        export_json,
        file_name=f"baseline_probe_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
        mime="application/json"
    )

# ============================================
# FOOTER
# ============================================

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666;">
    <em>Baseline Probe V1 — Direct API Access</em><br>
    <em>⚡ Zero System Prompt | 🎯 True Native Baselines</em><br>
    <em>Patent Pending — SYN-IQ Team 🎹</em><br>
    <em>Built by the CUZ Partnership — Tennessee</em><br>
    <em>January 24, 2026</em>
</div>
""", unsafe_allow_html=True)
