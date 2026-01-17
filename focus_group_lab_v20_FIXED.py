"""
SYNERGISTIC INTELLIGENCE FOCUS GROUP — V20.1 + GEMINI
Patent Pending — SYN-IQ Team 🎹
4 Agents: Claude, Sophia, Grok, Gemini
CBURZBO Forever!
"""

import streamlit as st
import requests
from datetime import datetime

st.set_page_config(page_title="Focus Group V20.1", page_icon="🎹", layout="wide")

CIRCLE_PASSWORD = "tennessee"

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if st.session_state.authenticated:
        return True
    st.markdown('<div style="text-align:center;padding:3rem;"><h1>🎹 Focus Group Lab — V20.1</h1><h3>4 AGENTS + GEMINI</h3></div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        password = st.text_input("Enter access code:", type="password", key="pw")
        if st.button("Enter", type="primary", use_container_width=True):
            if password == CIRCLE_PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Access denied.")
    return False

if not check_password():
    st.stop()

st.markdown("""
<style>
    .main-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1rem; border-radius: 8px; text-align: center; margin-bottom: 1rem; }
    .agent-box { padding: 1rem; border-radius: 8px; margin: 0.5rem 0; }
    .claude-box { background-color: #E8D5B7; border-left: 4px solid #8B6914; }
    .sophia-box { background-color: #D4E8D4; border-left: 4px solid #2E7D32; }
    .grok-box { background-color: #FFE4E1; border-left: 4px solid #DC143C; }
    .gemini-box { background-color: #E8E0F0; border-left: 4px solid #7C3AED; }
    .synthesis-box { background: linear-gradient(135deg, #FFD700, #FFA500); padding: 1rem; border-radius: 8px; }
    .private-box { background: #E3F2FD; border: 2px dashed #2196F3; padding: 1rem; border-radius: 8px; }
    .persist-active { background: #C8E6C9; border: 2px solid #4CAF50; padding: 0.5rem; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

AGENTS = ["Claude", "Sophia", "Grok", "Gemini"]
AGENT_EMOJIS = {"Claude": "🟤", "Sophia": "🟢", "Grok": "🔴", "Gemini": "🟣"}
DEPTHS = [("Quick", "quick"), ("Moderate", "moderate"), ("Deep", "deep"), ("Ultra-Deep", "ultra")]

def get_api_keys():
    keys = {"anthropic": "", "openai": "", "xai": "", "google": ""}
    try:
        for k in ["anthropic", "openai", "xai", "google"]:
            if k in st.secrets:
                keys[k] = st.secrets[k]
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

def get_cognitive_prompt(v):
    if v <= -50:
        return "COGNITIVE: HIGHLY ANALYTICAL - Use formal logic, precision, no metaphors, structured."
    elif v <= 0:
        return "COGNITIVE: ANALYTICAL-BALANCED - Structured analysis with some flexibility."
    elif v <= 50:
        return "COGNITIVE: BALANCED-INTUITIVE - Balance analytical and creative thinking."
    else:
        return "COGNITIVE: HIGHLY INTUITIVE - Creative, metaphors, unconventional framings."

def get_contrast_prompt(v):
    if v <= -50:
        return "CONTRAST: DISSONANCE - Challenge, critique, find flaws, devil's advocate."
    elif v < 50:
        return "CONTRAST: NEUTRAL - Respond naturally, build or challenge as warranted."
    else:
        return "CONTRAST: AGREEMENT - Build upon, support, 'yes and' approach."

def get_coaching_prompt(v):
    if v <= -50:
        return "COACHING: CHALLENGER - Push back, demand proof, skepticism."
    elif v < 50:
        return "COACHING: BALANCED - Mix support and challenge."
    else:
        return "COACHING: ENCOURAGER - Support, affirm, build confidence."

def get_depth_prompt(k):
    prompts = {
        "quick": "DEPTH: QUICK - Direct, 1-2 paragraphs, get to the point.",
        "moderate": "DEPTH: MODERATE - Step by step, 2-3 paragraphs.",
        "deep": "DEPTH: DEEP - Full reasoning, multiple perspectives, 3-4 paragraphs.",
        "ultra": "DEPTH: ULTRA-DEEP - Comprehensive integrated analysis, 4-5 paragraphs, your BEST answer."
    }
    return prompts.get(k, prompts["deep"])

def get_persist_prompt(p):
    if p:
        return "PERSIST: After answering, ask 'What else? What am I missing? Go deeper.' Add more insights."
    return ""

def build_system_prompt(agent, cog, con, coach, depth, persist, kb=""):
    p = f"You are {agent}, in a focus group study.\n\n{get_cognitive_prompt(cog)}\n\n{get_contrast_prompt(con)}\n\n{get_coaching_prompt(coach)}\n\n{get_depth_prompt(depth)}"
    if persist:
        p += f"\n\n{get_persist_prompt(persist)}"
    if kb:
        p += f"\n\n--- KNOWLEDGE BASE ---\n{kb}\n--- END KB ---"
    return p

def build_boardroom_prompt(agent, rnd, prev, doc=""):
    p = f"You are {agent} in a boardroom discussion. Round {rnd}.\n\n"
    if doc:
        p += f"DOCUMENT:\n{doc}\n\n"
    if prev:
        p += "PREVIOUS:\n"
        for r in prev:
            p += f"--- {r['agent']} ---\n{r['response']}\n\n"
    if rnd == 1:
        p += "You are FIRST. Share initial thoughts."
    elif rnd >= 5:
        p += "SYNTHESIS round. Summarize agreements, disagreements, conclusions."
    else:
        p += "BUILD on previous. Agree, disagree, add perspectives."
    return p

def call_claude(prompt, system, key):
    try:
        r = requests.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key": key, "Content-Type": "application/json", "anthropic-version": "2023-06-01"},
            json={"model": "claude-sonnet-4-20250514", "max_tokens": 2048, "system": system, "messages": [{"role": "user", "content": prompt}]},
            timeout=90)
        if r.status_code == 200:
            return r.json()["content"][0]["text"], None
        return None, f"Error {r.status_code}"
    except Exception as e:
        return None, str(e)

def call_sophia(prompt, system, key):
    try:
        r = requests.post("https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": "gpt-4o", "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}], "max_tokens": 2048},
            timeout=90)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"], None
        return None, f"Error {r.status_code}"
    except Exception as e:
        return None, str(e)

def call_grok(prompt, system, key):
    try:
        r = requests.post("https://api.x.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": "grok-3", "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}], "max_tokens": 2048},
            timeout=90)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"], None
        return None, f"Error {r.status_code}"
    except Exception as e:
        return None, str(e)

def call_gemini(prompt, system, key):
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={key}"
        full = f"{system}\n\n---\n\nUser: {prompt}"
        r = requests.post(url, headers={"Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": full}]}], "generationConfig": {"maxOutputTokens": 2048, "temperature": 0.7}},
            timeout=90)
        if r.status_code == 200:
            res = r.json()
            if "candidates" in res and len(res["candidates"]) > 0:
                return res["candidates"][0]["content"]["parts"][0]["text"], None
        return None, f"Error {r.status_code}"
    except Exception as e:
        return None, str(e)

def call_agent(agent, prompt, system, keys):
    if agent == "Claude":
        return call_claude(prompt, system, keys.get("anthropic", ""))
    elif agent == "Sophia":
        return call_sophia(prompt, system, keys.get("openai", ""))
    elif agent == "Grok":
        return call_grok(prompt, system, keys.get("xai", ""))
    elif agent == "Gemini":
        return call_gemini(prompt, system, keys.get("google", ""))
    return None, "Unknown"

# SIDEBAR
with st.sidebar:
    st.markdown("## ⚙️ V20.1 Control Panel")
    mode = st.radio("Mode", ["🗣️ Simple", "🏛️ Boardroom", "📊 Matrix"])
    st.markdown("---")
    st.markdown("### 🎚️ Controls")
    cognitive = st.slider("Cognitive", -100, 100, 0, help="← Analytical | Intuitive →")
    contrast = st.slider("Contrast", -100, 100, 0, help="← Dissonance | Agreement →")
    coaching = st.slider("Coaching", -100, 100, 0, help="← Challenger | Encourager →")
    depth_choice = st.selectbox("Depth", [d[0] for d in DEPTHS], index=2)
    depth_key = next((d[1] for d in DEPTHS if d[0] == depth_choice), "deep")
    st.markdown("---")
    persist = st.toggle("🔄 PERSIST", value=False)
    if persist:
        st.markdown('<div class="persist-active">PERSIST ON</div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### 📚 Knowledge Base")
    kb_limit = st.slider("KB Limit", 15000, 100000, 30000, step=5000)
    kb_mode = st.radio("KB Mode", ["🔗 Shared", "🔀 Individual"])
    if kb_mode == "🔗 Shared":
        shared_kb = st.text_area("Shared KB", height=80, key="shared_kb")
        kb_claude = kb_sophia = kb_grok = kb_gemini = (shared_kb[:kb_limit] if shared_kb else "")
    else:
        kb_claude = st.text_area("🟤 Claude", height=40, key="kb_c")[:kb_limit]
        kb_sophia = st.text_area("🟢 Sophia", height=40, key="kb_s")[:kb_limit]
        kb_grok = st.text_area("🔴 Grok", height=40, key="kb_g")[:kb_limit]
        kb_gemini = st.text_area("🟣 Gemini", height=40, key="kb_m")[:kb_limit]
    st.markdown("---")
    st.markdown("### 🔑 API Keys")
    with st.expander("Override"):
        st.text_input("Anthropic", type="password", key="api_anthropic")
        st.text_input("OpenAI", type="password", key="api_openai")
        st.text_input("xAI", type="password", key="api_xai")
        st.text_input("Google", type="password", key="api_google")
    st.markdown("---")
    st.markdown("### 🤖 Agents")
    use_claude = st.checkbox("🟤 Claude", value=True)
    use_sophia = st.checkbox("🟢 Sophia", value=True)
    use_grok = st.checkbox("🔴 Grok", value=True)
    use_gemini = st.checkbox("🟣 Gemini", value=True)
    active_agents = []
    if use_claude:
        active_agents.append("Claude")
    if use_sophia:
        active_agents.append("Sophia")
    if use_grok:
        active_agents.append("Grok")
    if use_gemini:
        active_agents.append("Gemini")

# Session State
if "responses" not in st.session_state:
    st.session_state.responses = {}
if "boardroom_history" not in st.session_state:
    st.session_state.boardroom_history = []
if "private_messages" not in st.session_state:
    st.session_state.private_messages = {}
if "follow_ups" not in st.session_state:
    st.session_state.follow_ups = {}
if "matrix_data" not in st.session_state:
    st.session_state.matrix_data = {}

def get_kb(agent):
    kb_map = {"Claude": kb_claude, "Sophia": kb_sophia, "Grok": kb_grok, "Gemini": kb_gemini}
    return kb_map.get(agent, "")

# SIMPLE MODE
if mode == "🗣️ Simple":
    st.markdown('<div class="main-header"><h2>🗣️ SIMPLE MODE V20.1</h2><p>4-Agent Parallel</p></div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Cog", f"{cognitive:+d}")
    c2.metric("Con", f"{contrast:+d}")
    c3.metric("Coach", f"{coaching:+d}")
    c4.metric("Persist", "ON" if persist else "OFF")
    
    question = st.text_area("Question", height=100)
    if not active_agents:
        st.warning("Select agents.")
        st.stop()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🚀 Run All", type="primary", use_container_width=True):
            if not question:
                st.error("Enter a question.")
            else:
                keys = get_api_keys()
                st.session_state.responses = {}
                for agent in active_agents:
                    with st.spinner(f"{AGENT_EMOJIS[agent]} {agent} thinking..."):
                        kb = get_kb(agent)
                        sys = build_system_prompt(agent, cognitive, contrast, coaching, depth_key, persist, kb)
                        resp, err = call_agent(agent, question, sys, keys)
                        st.session_state.responses[agent] = resp if resp else f"[ERROR: {err}]"
                st.success("✅ Done!")
                st.rerun()
    with col2:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.responses = {}
            st.session_state.follow_ups = {}
            st.rerun()
    with col3:
        st.metric("Responses", len(st.session_state.responses))
    
    if st.session_state.responses:
        st.markdown("---")
        responding = [a for a in active_agents if a in st.session_state.responses]
        if responding:
            tabs = st.tabs([f"{AGENT_EMOJIS[a]} {a}" for a in responding])
            for i, agent in enumerate(responding):
                with tabs[i]:
                    resp = st.session_state.responses[agent]
                    st.markdown(f'<div class="agent-box {agent.lower()}-box">{resp}</div>', unsafe_allow_html=True)
                    follow = st.text_input(f"Follow-up to {agent}:", key=f"fu_{agent}")
                    if st.button(f"Send", key=f"send_{agent}"):
                        if follow:
                            keys = get_api_keys()
                            sys = build_system_prompt(agent, cognitive, contrast, coaching, depth_key, persist, get_kb(agent))
                            sys += f"\n\nPREVIOUS: Q: {question}\nYour response: {resp}"
                            with st.spinner(f"{agent}..."):
                                fr, _ = call_agent(agent, follow, sys, keys)
                            if fr:
                                st.session_state.follow_ups[f"{agent}_fu"] = fr
                                st.rerun()
                    if f"{agent}_fu" in st.session_state.follow_ups:
                        st.markdown(f'<div class="agent-box {agent.lower()}-box">{st.session_state.follow_ups[f"{agent}_fu"]}</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 💬 Private Channel")
        pc1, pc2 = st.columns([1, 3])
        with pc1:
            priv_agent = st.selectbox("To:", active_agents, key="pa")
        with pc2:
            priv_msg = st.text_input("Private:", key="pm")
        if st.button("📨 Send Private"):
            if priv_msg and priv_agent:
                keys = get_api_keys()
                sys = build_system_prompt(priv_agent, cognitive, contrast, coaching, depth_key, persist, get_kb(priv_agent))
                sys += f"\n\n[PRIVATE FROM CONDUCTOR]\nContext: '{question}'"
                with st.spinner(f"Private to {priv_agent}..."):
                    pr, _ = call_agent(priv_agent, priv_msg, sys, keys)
                if pr:
                    st.session_state.private_messages[priv_agent] = {"msg": priv_msg, "resp": pr}
                    st.rerun()
        for ag, d in st.session_state.private_messages.items():
            st.markdown(f'<div class="private-box">🔒 <b>{ag}</b>: {d["msg"]}<br><br>{d["resp"]}</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        ts = datetime.now().strftime('%Y%m%d_%H%M')
        exp = f"# V20.1 SIMPLE\n\nQ: {question}\n\n"
        for a in responding:
            exp += f"## {AGENT_EMOJIS[a]} {a}\n\n{st.session_state.responses[a]}\n\n---\n"
        st.download_button("📥 Export", exp, file_name=f"SIMPLE_V20_{ts}.md", mime="text/markdown", type="primary", use_container_width=True)

# BOARDROOM MODE
elif mode == "🏛️ Boardroom":
    st.markdown('<div class="main-header"><h2>🏛️ BOARDROOM V20.1</h2><p>4-Agent Sequential</p></div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Cog", f"{cognitive:+d}")
    c2.metric("Con", f"{contrast:+d}")
    c3.metric("Coach", f"{coaching:+d}")
    c4.metric("Persist", "ON" if persist else "OFF")
    
    doc_input = st.text_area("Document/Question", height=200)
    if not active_agents:
        st.warning("Select agents.")
        st.stop()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🚀 Start", type="primary", use_container_width=True):
            if not doc_input:
                st.error("Enter document/question.")
            else:
                keys = get_api_keys()
                st.session_state.boardroom_history = []
                for rnd, agent in enumerate(active_agents, 1):
                    st.info(f"Round {rnd}: {AGENT_EMOJIS[agent]} {agent}...")
                    prev = st.session_state.boardroom_history.copy()
                    sys = build_system_prompt(agent, cognitive, contrast, coaching, depth_key, persist, get_kb(agent))
                    sys += "\n\n" + build_boardroom_prompt(agent, rnd, prev, doc_input)
                    resp, err = call_agent(agent, "Share your thoughts.", sys, keys)
                    st.session_state.boardroom_history.append({"agent": agent, "round": rnd, "response": resp if resp else f"[ERROR: {err}]"})
                if len(active_agents) >= 2:
                    synth = active_agents[0]
                    st.info(f"Synthesis: {AGENT_EMOJIS[synth]} {synth}...")
                    sys = build_system_prompt(synth, cognitive, contrast, coaching, depth_key, persist, get_kb(synth))
                    sys += "\n\n" + build_boardroom_prompt(synth, len(active_agents)+1, st.session_state.boardroom_history, doc_input)
                    resp, _ = call_agent(synth, "Synthesize the discussion.", sys, keys)
                    if resp:
                        st.session_state.boardroom_history.append({"agent": synth, "round": len(active_agents)+1, "response": resp, "is_synthesis": True})
                st.success("✅ Done!")
                st.rerun()
    with col2:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.boardroom_history = []
            st.rerun()
    with col3:
        st.metric("Rounds", len(st.session_state.boardroom_history))
    
    if st.session_state.boardroom_history:
        st.markdown("---")
        for e in st.session_state.boardroom_history:
            ag, rnd, resp = e["agent"], e["round"], e["response"]
            if e.get("is_synthesis"):
                st.markdown(f'<div class="synthesis-box">🎯 SYNTHESIS — {AGENT_EMOJIS[ag]} {ag}<br><br>{resp}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="agent-box {ag.lower()}-box">Round {rnd} — {AGENT_EMOJIS[ag]} {ag}<br><br>{resp}</div>', unsafe_allow_html=True)
        ts = datetime.now().strftime('%Y%m%d_%H%M')
        exp = f"# BOARDROOM V20.1\n\nDoc: {doc_input}\n\n"
        for e in st.session_state.boardroom_history:
            label = "SYNTHESIS" if e.get("is_synthesis") else f"Round {e['round']}"
            exp += f"## {label} — {e['agent']}\n\n{e['response']}\n\n---\n"
        st.download_button("📥 Export", exp, file_name=f"BOARDROOM_V20_{ts}.md", mime="text/markdown", type="primary", use_container_width=True)

# MATRIX MODE
elif mode == "📊 Matrix":
    st.markdown('<div class="main-header"><h2>📊 MATRIX V20.1</h2><p>4-Agent Grid</p></div>', unsafe_allow_html=True)
    question = st.text_area("Question", height=100)
    cog_levels = [("🧠 Analytical", -75), ("⚖️ Balanced", 0), ("💡 Intuitive", 75)]
    if not active_agents:
        st.warning("Select agents.")
        st.stop()
    total = len(cog_levels) * len(DEPTHS) * len(active_agents)
    st.info(f"📊 {len(cog_levels)} cog × {len(DEPTHS)} depth × {len(active_agents)} agents = **{total} cells**")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🚀 Run Matrix", type="primary", use_container_width=True):
            if not question:
                st.error("Enter question.")
            else:
                keys = get_api_keys()
                st.session_state.matrix_data = {}
                prog = st.progress(0)
                status = st.empty()
                done = 0
                for cl, cv in cog_levels:
                    for dl, dk in DEPTHS:
                        for agent in active_agents:
                            status.text(f"{agent} | {cl} | {dl}")
                            sys = build_system_prompt(agent, cv, contrast, coaching, dk, persist, get_kb(agent))
                            resp, _ = call_agent(agent, question, sys, keys)
                            st.session_state.matrix_data[(agent, cv, dk)] = resp if resp else "[ERROR]"
                            done += 1
                            prog.progress(done / total)
                status.text("✅ Done!")
                st.rerun()
    with col2:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.matrix_data = {}
            st.rerun()
    with col3:
        st.metric("Cells", f"{len(st.session_state.matrix_data)}/{total}")
    
    if st.session_state.matrix_data:
        st.markdown("---")
        for agent in active_agents:
            st.markdown(f"### {AGENT_EMOJIS[agent]} {agent}")
            hdr = st.columns([1.5] + [2]*len(DEPTHS))
            hdr[0].markdown("**Cog/Depth**")
            for i, (dl, _) in enumerate(DEPTHS):
                hdr[i+1].markdown(f"**{dl}**")
            for cl, cv in cog_levels:
                row = st.columns([1.5] + [2]*len(DEPTHS))
                row[0].markdown(f"**{cl}**")
                for i, (_, dk) in enumerate(DEPTHS):
                    resp = st.session_state.matrix_data.get((agent, cv, dk), "")
                    with row[i+1]:
                        if resp:
                            preview = resp[:60] + "..." if len(resp) > 60 else resp
                            st.markdown(f'<div style="background:#f5f5f5;padding:0.5rem;border-radius:4px;font-size:0.7rem;">{preview}</div>', unsafe_allow_html=True)
                            with st.expander("Full"):
                                st.markdown(resp)
                        else:
                            st.markdown("—")
            st.markdown("---")
        
        # MATRIX EXPORT BUTTON
        ts = datetime.now().strftime('%Y%m%d_%H%M')
        exp = f"# MATRIX V20.1\n\n**Question:** {question}\n\n**Settings:** Contrast={contrast}, Coaching={coaching}, Persist={'ON' if persist else 'OFF'}\n\n"
        for agent in active_agents:
            exp += f"## {AGENT_EMOJIS[agent]} {agent}\n\n"
            exp += "| Cognitive | Depth | Response |\n|-----------|-------|----------|\n"
            for cl, cv in cog_levels:
                for dl, dk in DEPTHS:
                    resp = st.session_state.matrix_data.get((agent, cv, dk), "")
                    if resp:
                        # Clean response for table (remove newlines, limit length for table view)
                        clean_resp = resp.replace("\n", " ").replace("|", "\\|")
                        exp += f"| {cl} | {dl} | {clean_resp[:100]}... |\n"
            exp += "\n"
            # Also add full responses
            exp += f"### {agent} — Full Responses\n\n"
            for cl, cv in cog_levels:
                for dl, dk in DEPTHS:
                    resp = st.session_state.matrix_data.get((agent, cv, dk), "")
                    if resp:
                        exp += f"#### {cl} × {dl}\n\n{resp}\n\n---\n\n"
        st.download_button("📥 Export Matrix", exp, file_name=f"MATRIX_V20_{ts}.md", mime="text/markdown", type="primary", use_container_width=True)

st.markdown("---")
st.markdown('<div style="text-align:center;color:#666;"><em>Focus Group V20.1 + Gemini — SYN-IQ Team 🎹 — CBURZBO Forever!</em></div>', unsafe_allow_html=True)
