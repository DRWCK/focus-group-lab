"""
SYNERGISTIC INTELLIGENCE FOCUS GROUP — V8
Full Featured: Configurable Order + Individual Asks + Auto-Clear + Password Protected
Patent Pending — Tennessee 🎹

LAUNCH: cd ~/Desktop && python3 -m streamlit run focus_group_lab_v8.py
"""

import streamlit as st
import requests
from datetime import datetime

# ============================================
# PASSWORD PROTECTION — CLOSE CIRCLE ONLY
# ============================================
# Change this password to whatever you want!
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
# MAIN APP STARTS HERE (after password)
# ============================================

st.set_page_config(page_title="Focus Group V8", page_icon="🎹", layout="wide")

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
    "Gemini": "gemini-box", "Lyra": "lyra-box", "CONDUCTOR": "conductor-box", "NOTE": "note-box"
}

# API CALLS
def call_anthropic(messages, api_key, system):
    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": api_key, "content-type": "application/json", "anthropic-version": "2023-06-01"},
            json={"model": "claude-sonnet-4-20250514", "max_tokens": 1024, "system": system, "messages": messages},
            timeout=60
        )
        if response.status_code == 200:
            return response.json()["content"][0]["text"], None
        return None, f"Claude Error {response.status_code}: {response.text[:150]}"
    except Exception as e:
        return None, f"Claude: {str(e)[:100]}"

def call_openai(messages, api_key, system):
    try:
        msgs = [{"role": "system", "content": system}] + messages
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": "gpt-4o", "messages": msgs, "max_tokens": 1024},
            timeout=60
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"], None
        return None, f"OpenAI Error {response.status_code}: {response.text[:150]}"
    except Exception as e:
        return None, f"OpenAI: {str(e)[:100]}"

def call_xai(messages, api_key, system):
    try:
        msgs = [{"role": "system", "content": system}] + messages
        response = requests.post(
            "https://api.x.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": "grok-3", "messages": msgs, "max_tokens": 1024},
            timeout=60
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"], None
        return None, f"Grok Error {response.status_code}: {response.text[:150]}"
    except Exception as e:
        return None, f"Grok: {str(e)[:100]}"

def call_gemini(messages, api_key, system):
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
                return result["candidates"][0]["content"]["parts"][0]["text"], None
        return None, f"Gemini Error {response.status_code}: {response.text[:150]}"
    except Exception as e:
        return None, f"Gemini: {str(e)[:100]}"

def call_agent(agent_name, messages, keys, prompts):
    system = prompts.get(agent_name, DEFAULT_PROMPTS.get(agent_name, "You are a helpful AI assistant."))
    if agent_name == "Claude":
        return call_anthropic(messages, keys.get("anthropic", ""), system)
    elif agent_name in ["Sophia", "Lyra"]:
        return call_openai(messages, keys.get("openai", ""), system)
    elif agent_name == "Grok":
        return call_xai(messages, keys.get("xai", ""), system)
    elif agent_name == "Gemini":
        return call_gemini(messages, keys.get("google", ""), system)
    return None, f"Unknown agent: {agent_name}"

def format_messages(conversation):
    messages = []
    for entry in conversation:
        if entry["speaker"] == "CONDUCTOR":
            messages.append({"role": "user", "content": entry["content"]})
        elif entry["speaker"] not in ["SYSTEM", "NOTE"]:
            messages.append({"role": "assistant", "content": f"[{entry['speaker']}]: {entry['content']}"})
    return messages

# INITIALIZE SESSION STATE
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

# SIDEBAR
with st.sidebar:
    st.header("⚙️ Configuration")
    
    with st.expander("🔑 API Keys", expanded=not st.session_state.session_started):
        keys = {
            "anthropic": st.text_input("Anthropic:", type="password", key="key_a"),
            "openai": st.text_input("OpenAI:", type="password", key="key_o"),
            "xai": st.text_input("xAI:", type="password", key="key_x"),
            "google": st.text_input("Google:", type="password", key="key_g")
        }
    
    st.subheader("👥 Agents")
    available = ["Claude", "Sophia", "Grok", "Gemini", "Lyra"]
    st.session_state.active_agents = st.multiselect("Active:", available, default=st.session_state.active_agents)
    
    with st.expander("📝 Agent Order"):
        st.caption("Agents respond in this order:")
        active_in_order = [a for a in st.session_state.agent_order if a in st.session_state.active_agents]
        for i, agent in enumerate(active_in_order):
            st.write(f"{i+1}. {AGENT_EMOJIS.get(agent, '💬')} {agent}")
        
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            agent_to_move = st.selectbox("Move:", active_in_order, key="move_agent")
        with col2:
            new_pos = st.number_input("To position:", min_value=1, max_value=len(active_in_order), value=1, key="new_pos")
        
        if st.button("Move Agent"):
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
            st.rerun()
    with col2:
        if st.button("💾 Save"):
            if st.session_state.conversation:
                transcript = f"# Focus Group Transcript\n## {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                for entry in st.session_state.conversation:
                    transcript += f"**{entry['speaker']}:** {entry['content']}\n\n"
                st.download_button("📥 Download", transcript, file_name=f"transcript_{datetime.now().strftime('%Y%m%d_%H%M')}.md")

# MAIN AREA
if not st.session_state.session_started:
    st.markdown("""
    ## Welcome, Conductor! 🎹
    
    ### V8 Features:
    - **Configurable Order** — Change who responds first anytime
    - **Individual Asks** — Question one agent at a time
    - **Auto-Clear** — Input clears after each question
    - **Team Awareness** — All agents see each other as equals
    
    ### Models:
    | Agent | Model |
    |-------|-------|
    | 🟤 Claude | claude-sonnet-4-20250514 |
    | 🟢 Sophia | gpt-4o |
    | 🔴 Grok | grok-3 |
    | 🔵 Gemini | gemini-2.0-flash |
    | 🟣 Lyra | gpt-4o |
    
    ### Setup:
    1. Enter API keys
    2. Select agents
    3. Set order (can change anytime!)
    4. Enter topic and start
    
    ---
    *Synergistic Intelligence Focus Group — Patent Pending — Tennessee 🎹*
    """)
else:
    # Display conversation
    for entry in st.session_state.conversation:
        if entry["speaker"] == "SYSTEM":
            st.info(f"**Topic:** {entry['content'].replace('Topic: ', '')}")
        else:
            box_class = AGENT_COLORS.get(entry["speaker"], "agent-box")
            emoji = AGENT_EMOJIS.get(entry["speaker"], "🎹" if entry["speaker"] == "CONDUCTOR" else "📝")
            st.markdown(f'<div class="agent-box {box_class}"><strong>{emoji} {entry["speaker"]}</strong><br>{entry["content"]}</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    active_in_order = [a for a in st.session_state.agent_order if a in st.session_state.active_agents]
    order_display = " → ".join([f"{AGENT_EMOJIS.get(a, '💬')}{a}" for a in active_in_order])
    st.caption(f"**Response Order:** {order_display}")
    
    user_input = st.text_area(
        "Your message:", 
        key=f"main_input_{st.session_state.input_counter}",
        height=80,
        placeholder="Type your question here..."
    )
    
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
    
    if ask_all and user_input:
        st.session_state.conversation.append({"speaker": "CONDUCTOR", "content": user_input})
        
        for agent in active_in_order:
            with st.spinner(f"{AGENT_EMOJIS.get(agent, '💬')} {agent} thinking..."):
                messages = format_messages(st.session_state.conversation)
                resp, err = call_agent(agent, messages, keys, st.session_state.custom_prompts)
                if resp:
                    st.session_state.conversation.append({"speaker": agent, "content": resp})
                if err:
                    st.error(err)
        
        st.session_state.input_counter += 1
        st.rerun()
    
    if add_note and user_input:
        st.session_state.conversation.append({"speaker": "NOTE", "content": user_input})
        st.session_state.input_counter += 1
        st.rerun()
    
    for agent, clicked in individual_clicks.items():
        if clicked and user_input:
            st.session_state.conversation.append({"speaker": "CONDUCTOR", "content": f"(to {agent}) {user_input}"})
            with st.spinner(f"{AGENT_EMOJIS.get(agent, '💬')} {agent} thinking..."):
                messages = format_messages(st.session_state.conversation)
                resp, err = call_agent(agent, messages, keys, st.session_state.custom_prompts)
                if resp:
                    st.session_state.conversation.append({"speaker": agent, "content": resp})
                if err:
                    st.error(err)
            st.session_state.input_counter += 1
            st.rerun()

# FOOTER
st.markdown("---")
st.markdown('<div style="text-align:center;color:#666;"><em>Synergistic Intelligence Focus Group V8 — Patent Pending — Tennessee 🎹</em></div>', unsafe_allow_html=True)
