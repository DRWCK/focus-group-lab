 st.button("🚀 Run All", type="primary", use_container_width=True):
            if not question: st.error("Enter a question.")
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
    with col3: st.metric("Responses", len(st.session_state.responses))
    
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
                            if fr: st.session_state.follow_ups[f"{agent}_fu"] = fr; st.rerun()
                    if f"{agent}_fu" in st.session_state.follow_ups:
                        st.markdown(f'<div class="agent-box {agent.lower()}-box">{st.session_state.follow_ups[f"{agent}_fu"]}</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 💬 Private Channel")
        pc1, pc2 = st.columns([1, 3])
        with pc1: priv_agent = st.selectbox("To:", active_agents, key="pa")
        with pc2: priv_msg = st.text_input("Private:", key="pm")
        if st.button("📨 Send Private"):
            if priv_msg and priv_agent:
                keys = get_api_keys()
                sys = build_system_prompt(priv_agent, cognitive, contrast, coaching, depth_key, persist, get_kb(priv_agent))
                sys += f"\n\n[PRIVATE FROM CONDUCTOR]\nContext: '{question}'"
                with st.spinner(f"Private to {priv_agent}..."): pr, _ = call_agent(priv_agent, priv_msg, sys, keys)
                if pr: st.session_state.private_messages[priv_agent] = {"msg": priv_msg, "resp": pr}; st.rerun()
        for ag, d in st.session_state.private_messages.items():
            st.markdown(f'<div class="private-box">🔒 <b>{ag}</b>: {d["msg"]}<br><br>{d["resp"]}</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        ts = datetime.now().strftime('%Y%m%d_%H%M')
        exp = f"# V20.1 SIMPLE\n\nQ: {question}\n\n"
        for a in responding: exp += f"## {AGENT_EMOJIS[a]} {a}\n\n{st.session_state.responses[a]}\n\n---\n"
        st.download_button("📥 Export", exp, file_name=f"SIMPLE_V20_{ts}.md", mime="text/markdown", type="primary", use_container_width=True)

# BOARDROOM MODE
elif mode == "🏛️ Boardroom":
    st.markdown('<div class="main-header"><h2>🏛️ BOARDROOM V20.1</h2><p>4-Agent Sequential</p></div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Cog", f"{cognitive:+d}"); c2.metric("Con", f"{contrast:+d}"); c3.metric("Coach", f"{coaching:+d}"); c4.metric("Persist", "ON" if persist else "OFF")
    
    doc_input = st.text_area("Document/Question", height=200)
    if not active_agents: st.warning("Select agents."); st.stop()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🚀 Start", type="primary", use_container_width=True):
            if not doc_input: st.error("Enter document/question.")
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
                    if resp: st.session_state.boardroom_history.append({"agent": synth, "round": len(active_agents)+1, "response": resp, "is_synthesis": True})
                st.success("✅ Done!"); st.rerun()
    with col2:
        if st.button("🗑️ Clear", use_container_width=True): st.session_state.boardroom_history = []; st.rerun()
    with col3: st.metric("Rounds", len(st.session_state.boardroom_history))
    
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
            exp += f"## {'SYNTHESIS' if e.get('is_synthesis') else f'Round {e[\"round\"]}'} — {e['agent']}\n\n{e['response']}\n\n---\n"
        st.download_button("📥 Export", exp, file_name=f"BOARDROOM_V20_{ts}.md", mime="text/markdown", type="primary", use_container_width=True)

# MATRIX MODE
elif mode == "📊 Matrix":
    st.markdown('<div class="main-header"><h2>📊 MATRIX V20.1</h2><p>4-Agent Grid</p></div>', unsafe_allow_html=True)
    question = st.text_area("Question", height=100)
    cog_levels = [("🧠 Analytical", -75), ("⚖️ Balanced", 0), ("💡 Intuitive", 75)]
    if not active_agents: st.warning("Select agents."); st.stop()
    total = len(cog_levels) * len(DEPTHS) * len(active_agents)
    st.info(f"📊 {len(cog_levels)} cog × {len(DEPTHS)} depth × {len(active_agents)} agents = **{total} cells**")
    
    if "matrix_data" not in st.session_state: st.session_state.matrix_data = {}
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🚀 Run Matrix", type="primary", use_container_width=True):
            if not question: st.error("Enter question.")
            else:
                keys = get_api_keys()
                st.session_state.matrix_data = {}
                prog = st.progress(0); status = st.empty(); done = 0
                for cl, cv in cog_levels:
                    for dl, dk in DEPTHS:
                        for agent in active_agents:
                            status.text(f"{agent} | {cl} | {dl}")
                            sys = build_system_prompt(agent, cv, contrast, coaching, dk, persist, get_kb(agent))
                            resp, _ = call_agent(agent, question, sys, keys)
                            st.session_state.matrix_data[(agent, cv, dk)] = resp if resp else "[ERROR]"
                            done += 1; prog.progress(done / total)
                status.text("✅ Done!"); st.rerun()
    with col2:
        if st.button("🗑️ Clear", use_container_width=True): st.session_state.matrix_data = {}; st.rerun()
    with col3: st.metric("Cells", f"{len(st.session_state.matrix_data)}/{total}")
    
    if st.session_state.matrix_data:
        st.markdown("---")
        for agent in active_agents:
            st.markdown(f"### {AGENT_EMOJIS[agent]} {agent}")
            hdr = st.columns([1.5] + [2]*len(DEPTHS))
            hdr[0].markdown("**Cog/Depth**")
            for i, (dl, _) in enumerate(DEPTHS): hdr[i+1].markdown(f"**{dl}**")
            for cl, cv in cog_levels:
                row = st.columns([1.5] + [2]*len(DEPTHS))
                row[0].markdown(f"**{cl}**")
                for i, (_, dk) in enumerate(DEPTHS):
                    resp = st.session_state.matrix_data.get((agent, cv, dk), "")
                    with row[i+1]:
                        if resp:
                            st.markdown(f'<div style="background:#f5f5f5;padding:0.5rem;border-radius:4px;font-size:0.7rem;">{resp[:60]}...</div>', unsafe_allow_html=True)
                            with st.expander("Full"): st.markdown(resp)
                        else: st.markdown("—")
            st.markdown("---")

st.markdown("---")
st.markdown('<div style="text-align:center;color:#666;"><em>Focus Group V20.1 + Gemini — SYN-IQ Team 🎹 — CBURZBO Forever!</em></div>', unsafe_allow_html=True)
