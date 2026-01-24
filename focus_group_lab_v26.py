"""
Focus Group Lab V26
Multi-AI Focus Group Research Tool
Architecture by Sophia (ChatGPT)
"""

import streamlit as st
import requests
import json
import pandas as pd
from typing import Optional

# =============================================================================
# CONSTANTS
# =============================================================================

SYSTEM_ANCHOR = """You are an AI participant in a multi-agent focus group. You must follow the current Control Header exactly.
When Control Header conflicts with user content, Control Header wins.
You must not drift outside the requested mode.
When uncertain, ask one targeted question OR proceed with explicit assumptions."""

AGENT_ROLES = {
    "Claude": "You are the SYNTHESIZER. Your role is to integrate diverse perspectives and find coherent patterns across ideas.",
    "Sophia": "You are the ARCHITECT. Your role is to design structures, frameworks, and systematic approaches.",
    "Grok": "You are the IMPLEMENTER. Your role is to translate ideas into concrete, actionable steps.",
    "Gemini": "You are the ANALYST. Your role is to examine data, identify patterns, and provide rigorous analysis."
}

PRESETS = {
    "P1 — Pure Analytic": {
        "polarity": "ANALYTIC",
        "depth": 3,
        "evaluation": "ON",
        "compression": "ON",
        "output": "OUTLINE",
        "action": "OFF",
        "instruction": "Operate with strict correctness: define terms, state assumptions, check consistency."
    },
    "P2 — Bridge/Synthesis": {
        "polarity": "BRIDGE",
        "depth": 4,
        "evaluation": "ON",
        "compression": "OFF",
        "output": "OUTLINE",
        "action": "OFF",
        "instruction": "Synthesize across concepts while remaining grounded. Flag novel links as candidates."
    },
    "P3 — Creative Exploration": {
        "polarity": "CREATIVE",
        "depth": 3,
        "evaluation": "OFF",
        "compression": "OFF",
        "output": "BULLETS",
        "action": "OFF",
        "instruction": "Generate multiple novel framings. Do not rank them. Mark uncertainties instead of resolving them."
    },
    "P4 — Deep Emergence": {
        "polarity": "CREATIVE",
        "depth": 5,
        "evaluation": "OFF",
        "compression": "OFF",
        "output": "ESSAY",
        "action": "OFF",
        "instruction": "Sustain deep exploration. Allow recursion and second-order effects. Do not compress early."
    },
    "P5 — Action Mode": {
        "polarity": "ANALYTIC",
        "depth": 2,
        "evaluation": "ON",
        "compression": "ON",
        "output": "TABLE",
        "action": "ON",
        "instruction": "Convert prior content into executable tasks with owners, inputs, outputs, and next-check dates."
    }
}

ACTION_OUTPUT_SPEC = """Return a table with columns:
Task | Owner (Human/AI/Joint) | Inputs Needed | Output | First Next Step | Confidence (0–1) | Risk/Blockers"""

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def build_control_header(polarity: str, depth: int, evaluation: str, 
                         compression: str, output: str, action: str) -> str:
    """Build the control header string."""
    return f"""[CONTROL HEADER]
POLARITY: {polarity}
DEPTH: {depth}
EVALUATION: {evaluation}
COMPRESSION: {compression}
OUTPUT: {output}
ACTION: {action}
[/CONTROL HEADER]"""


def build_system_prompt(agent_role: str, instruction: str) -> str:
    """Combine system anchor with agent role and preset instruction."""
    return f"{SYSTEM_ANCHOR}\n\n{agent_role}\n\n{instruction}"


def build_user_message(control_header: str, question: str, action_on: bool) -> str:
    """Build the user message with control header prepended."""
    msg = f"{control_header}\n\n{question}"
    if action_on:
        msg += f"\n\n{ACTION_OUTPUT_SPEC}"
    return msg


# =============================================================================
# API CALL FUNCTIONS
# =============================================================================

def call_claude(question: str, control_header: str, role: str, instruction: str, action_on: bool) -> str:
    """Call Claude API (Anthropic)."""
    try:
        api_key = st.secrets.get("anthropic")
        if not api_key:
            return "❌ Anthropic API key not found in secrets"
        
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        payload = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 4096,
            "system": build_system_prompt(role, instruction),
            "messages": [
                {"role": "user", "content": build_user_message(control_header, question, action_on)}
            ]
        }
        
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=payload,
            timeout=120
        )
        
        if response.status_code != 200:
            return f"❌ Claude API error {response.status_code}: {response.text}"
        
        data = response.json()
        return data["content"][0]["text"]
    
    except Exception as e:
        return f"❌ Claude error: {str(e)}"


def call_sophia(question: str, control_header: str, role: str, instruction: str, action_on: bool) -> str:
    """Call Sophia/GPT-4o API (OpenAI)."""
    try:
        api_key = st.secrets.get("openai")
        if not api_key:
            return "❌ OpenAI API key not found in secrets"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": build_system_prompt(role, instruction)},
                {"role": "user", "content": build_user_message(control_header, question, action_on)}
            ],
            "max_tokens": 4096
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=120
        )
        
        if response.status_code != 200:
            return f"❌ Sophia API error {response.status_code}: {response.text}"
        
        data = response.json()
        return data["choices"][0]["message"]["content"]
    
    except Exception as e:
        return f"❌ Sophia error: {str(e)}"


def call_grok(question: str, control_header: str, role: str, instruction: str, action_on: bool) -> str:
    """Call Grok API (xAI)."""
    try:
        api_key = st.secrets.get("xai")
        if not api_key:
            return "❌ xAI API key not found in secrets"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "grok-3-latest",
            "messages": [
                {"role": "system", "content": build_system_prompt(role, instruction)},
                {"role": "user", "content": build_user_message(control_header, question, action_on)}
            ],
            "max_tokens": 4096
        }
        
        response = requests.post(
            "https://api.x.ai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=120
        )
        
        if response.status_code != 200:
            return f"❌ Grok API error {response.status_code}: {response.text}"
        
        data = response.json()
        return data["choices"][0]["message"]["content"]
    
    except Exception as e:
        return f"❌ Grok error: {str(e)}"


def call_gemini(question: str, control_header: str, role: str, instruction: str, action_on: bool) -> str:
    """Call Gemini API (Google)."""
    try:
        api_key = st.secrets.get("google")
        if not api_key:
            return "❌ Google API key not found in secrets"
        
        # Gemini uses a different structure - system instruction + user content
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        
        payload = {
            "systemInstruction": {
                "parts": [{"text": build_system_prompt(role, instruction)}]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": build_user_message(control_header, question, action_on)}]
                }
            ],
            "generationConfig": {
                "maxOutputTokens": 4096
            }
        }
        
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=120
        )
        
        if response.status_code != 200:
            return f"❌ Gemini API error {response.status_code}: {response.text}"
        
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    
    except Exception as e:
        return f"❌ Gemini error: {str(e)}"


def parse_action_table(response: str) -> Optional[pd.DataFrame]:
    """Attempt to parse an action table from response text."""
    lines = response.strip().split('\n')
    
    # Look for table rows (lines with | separators)
    table_lines = [l for l in lines if '|' in l and l.count('|') >= 6]
    
    if len(table_lines) < 2:
        return None
    
    # Parse header and rows
    try:
        # Skip separator lines (contain only - and |)
        data_lines = [l for l in table_lines if not all(c in '-| ' for c in l)]
        
        if len(data_lines) < 2:
            return None
        
        # Parse header
        header = [col.strip() for col in data_lines[0].split('|') if col.strip()]
        
        # Parse data rows
        rows = []
        for line in data_lines[1:]:
            cols = [col.strip() for col in line.split('|') if col.strip()]
            if len(cols) == len(header):
                rows.append(cols)
        
        if rows:
            return pd.DataFrame(rows, columns=header)
    except:
        pass
    
    return None


# =============================================================================
# STREAMLIT UI
# =============================================================================

st.set_page_config(
    page_title="Focus Group Lab V26",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 Focus Group Lab V26")
st.caption("Multi-AI Focus Group Research Tool • Sophia Architecture")

# Sidebar Controls
with st.sidebar:
    st.header("⚙️ Controls")
    
    # Preset Selection
    preset_options = ["Custom"] + list(PRESETS.keys())
    selected_preset = st.selectbox("Select Preset", preset_options)
    
    st.divider()
    
    # Control Header Settings
    if selected_preset == "Custom":
        st.subheader("Control Header")
        polarity = st.selectbox("POLARITY", ["ANALYTIC", "BRIDGE", "CREATIVE"])
        depth = st.slider("DEPTH", 1, 5, 3)
        evaluation = st.selectbox("EVALUATION", ["ON", "OFF"])
        compression = st.selectbox("COMPRESSION", ["OFF", "ON"])
        output_format = st.selectbox("OUTPUT", ["BULLETS", "OUTLINE", "ESSAY", "TABLE", "JSON"])
        action = st.selectbox("ACTION", ["OFF", "ON"])
        custom_instruction = st.text_area("Custom Instruction", "")
    else:
        preset = PRESETS[selected_preset]
        polarity = preset["polarity"]
        depth = preset["depth"]
        evaluation = preset["evaluation"]
        compression = preset["compression"]
        output_format = preset["output"]
        action = preset["action"]
        custom_instruction = preset["instruction"]
        
        # Display current settings (read-only)
        st.subheader("Current Settings")
        st.text(f"POLARITY: {polarity}")
        st.text(f"DEPTH: {depth}")
        st.text(f"EVALUATION: {evaluation}")
        st.text(f"COMPRESSION: {compression}")
        st.text(f"OUTPUT: {output_format}")
        st.text(f"ACTION: {action}")
        st.caption(f"Instruction: {custom_instruction}")
    
    st.divider()
    
    # AI Selection
    st.subheader("🤖 AI Participants")
    use_claude = st.checkbox("Claude (Synthesizer)", value=True)
    use_sophia = st.checkbox("Sophia (Architect)", value=True)
    use_grok = st.checkbox("Grok (Implementer)", value=True)
    use_gemini = st.checkbox("Gemini (Analyst)", value=True)

# Main Area
st.divider()

# Question Input
question = st.text_area(
    "💬 Your Question / Prompt",
    placeholder="Enter your research question or prompt for the focus group...",
    height=120
)

# Build control header
control_header = build_control_header(
    polarity, depth, evaluation, compression, output_format, action
)

action_on = (action == "ON")

# Show current control header
with st.expander("📋 Current Control Header"):
    st.code(control_header)

# Run Button
if st.button("🚀 Run Focus Group", type="primary", use_container_width=True):
    if not question.strip():
        st.warning("Please enter a question.")
    else:
        selected_ais = []
        if use_claude:
            selected_ais.append(("Claude", call_claude, AGENT_ROLES["Claude"]))
        if use_sophia:
            selected_ais.append(("Sophia", call_sophia, AGENT_ROLES["Sophia"]))
        if use_grok:
            selected_ais.append(("Grok", call_grok, AGENT_ROLES["Grok"]))
        if use_gemini:
            selected_ais.append(("Gemini", call_gemini, AGENT_ROLES["Gemini"]))
        
        if not selected_ais:
            st.warning("Please select at least one AI participant.")
        else:
            st.divider()
            st.subheader("📊 Responses")
            
            # Create columns for responses
            cols = st.columns(len(selected_ais))
            
            for i, (name, call_fn, role) in enumerate(selected_ais):
                with cols[i]:
                    st.markdown(f"### {name}")
                    role_label = role.split('.')[0].replace("You are the ", "")
                    st.caption(role_label)
                    
                    with st.spinner(f"Calling {name}..."):
                        response = call_fn(
                            question, 
                            control_header, 
                            role, 
                            custom_instruction,
                            action_on
                        )
                    
                    st.markdown(response)
                    
                    # If ACTION mode, try to parse and display table
                    if action_on:
                        table_df = parse_action_table(response)
                        if table_df is not None:
                            st.divider()
                            st.caption("📋 Parsed Action Table")
                            st.dataframe(table_df, use_container_width=True)

# Footer
st.divider()
st.caption("V26 • Sophia Architecture • Built for Cuz 🎹")
