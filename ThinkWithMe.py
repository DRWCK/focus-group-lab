"""
🧠 Think With Me™ — Streamlit App
SYN-IQ by SYNINT.AI · Patent Pending · V25 · 5-Mode Gradient
CBURZBO 🎹🧠💎
"""

import streamlit as st
from anthropic import Anthropic

# ── Page Config ──
st.set_page_config(page_title="Think With Me", page_icon="🧠", layout="centered", initial_sidebar_state="collapsed")

# ── CSS ──
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&display=swap');

.stApp {
    background: linear-gradient(160deg, #0a0e27 0%, #111640 40%, #0d1233 70%, #080b20 100%) !important;
    font-family: 'DM Sans', sans-serif !important;
}
#MainMenu, header, footer, .stDeployButton { display: none !important; }
.block-container { max-width: 500px !important; padding: 0.75rem 1.25rem 1.5rem !important; }

/* Header */
.twm-header { text-align: center; padding: 1rem 0 0.5rem; }
.twm-header .icon { font-size: 2.8rem; display: block; margin-bottom: 0.25rem; filter: drop-shadow(0 0 18px rgba(139,92,246,0.4)); }
.twm-header h1 { font-size: 1.6rem; font-weight: 700; color: #fff; margin: 0; letter-spacing: -0.02em; }
.twm-header .sub { color: #8b8fad; font-size: 0.85rem; margin-top: 0.1rem; }

/* Labels */
.slabel { text-align:center; font-size:0.7rem; font-weight:600; letter-spacing:0.1em; text-transform:uppercase; color:#8b8fad; margin:0.5rem 0 0.3rem; }
.mode-desc { text-align:center; font-size:0.75rem; color:#6b6f8d; font-style:italic; margin:0.15rem 0 0.1rem; }

/* Text area */
.stTextArea textarea {
    background: rgba(15,19,50,0.6) !important; border: 1px solid rgba(99,102,241,0.2) !important;
    border-radius: 12px !important; color: #e0e2f0 !important; font-family: 'DM Sans', sans-serif !important;
    font-size: 0.9rem !important; padding: 10px 14px !important; resize: none !important;
}
.stTextArea textarea:focus { border-color: rgba(99,102,241,0.5) !important; box-shadow: 0 0 0 2px rgba(99,102,241,0.15) !important; }
.stTextArea textarea::placeholder { color: #5a5e7d !important; }
.stTextArea label { display: none !important; }

/* All buttons */
.stButton > button {
    background: rgba(22,27,65,0.6) !important; color: #9ca0c0 !important;
    border: 1.5px solid rgba(99,102,241,0.2) !important; border-radius: 12px !important;
    font-family: 'DM Sans', sans-serif !important; font-weight: 600 !important; font-size: 0.78rem !important;
    padding: 0.4rem 0.35rem !important; min-height: 38px !important; transition: all 0.25s ease !important;
}
.stButton > button:hover { border-color: rgba(99,102,241,0.4) !important; background: rgba(30,36,80,0.7) !important; }
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #4f46e5, #6366f1) !important; border-color: #6366f1 !important;
    color: #fff !important; box-shadow: 0 4px 15px rgba(99,102,241,0.35) !important;
}

/* Form submit button */
.stFormSubmitButton > button {
    background: linear-gradient(135deg, #4f46e5, #6366f1) !important; border-color: #6366f1 !important;
    color: #fff !important; box-shadow: 0 4px 15px rgba(99,102,241,0.35) !important;
    border-radius: 12px !important; font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important; font-size: 0.95rem !important; padding: 0.6rem !important;
    min-height: 44px !important; width: 100% !important;
}
.stFormSubmitButton > button:hover { box-shadow: 0 6px 20px rgba(99,102,241,0.5) !important; }

/* Radio */
.stRadio > div { justify-content: center !important; }
.stRadio label { display: none !important; }
.stRadio [data-testid="stMarkdownContainer"] p { color: #9ca0c0 !important; font-size: 0.78rem !important; }

/* Cards */
.user-card {
    background: linear-gradient(145deg, rgba(79,70,229,0.15), rgba(99,102,241,0.08));
    border: 1px solid rgba(99,102,241,0.2); border-radius: 14px;
    padding: 0.85rem 1.1rem; margin: 0.4rem 0; color: #e0e2f0; font-size: 0.88rem;
}
.response-card {
    background: linear-gradient(145deg, rgba(22,27,65,0.6), rgba(15,19,50,0.7));
    border: 1px solid rgba(99,102,241,0.12); border-radius: 14px;
    padding: 1rem 1.1rem; margin: 0.4rem 0; color: #c7c9e0; line-height: 1.65; font-size: 0.88rem;
}
.response-card .rmeta { font-size: 0.68rem; color: #6366f1; font-weight: 600; letter-spacing: 0.05em; margin-bottom: 0.35rem; text-transform: uppercase; }
.response-card p { color: #c7c9e0; margin: 0.35rem 0; }
.response-card em { color: #a78bfa; }

hr { border-color: rgba(99,102,241,0.1) !important; margin: 0.4rem 0 !important; }

/* Sidebar */
section[data-testid="stSidebar"] { background: linear-gradient(180deg, #0d1233, #080b20) !important; }
.stTextInput input { background: rgba(15,19,50,0.6) !important; border: 1px solid rgba(99,102,241,0.2) !important; border-radius: 10px !important; color: #e0e2f0 !important; }

/* Footer */
.twm-foot { text-align:center; color:#3a3e5c; font-size:0.65rem; margin-top:1.25rem; padding-top:0.6rem; border-top:1px solid rgba(99,102,241,0.08); letter-spacing:0.04em; }

/* Tighten spacing */
div[data-testid="stVerticalBlock"] > div { padding-top: 0 !important; }
.stForm { border: none !important; padding: 0 !important; }

/* Password screen */
.pw-screen { text-align: center; padding: 3rem 1rem; }
.pw-screen .icon { font-size: 3.5rem; display: block; margin-bottom: 0.5rem; filter: drop-shadow(0 0 20px rgba(139,92,246,0.5)); }
.pw-screen h1 { font-size: 1.8rem; font-weight: 700; color: #fff; margin: 0 0 0.25rem; }
.pw-screen .sub { color: #8b8fad; font-size: 0.85rem; }
</style>
""", unsafe_allow_html=True)

# ── Password Protection ──
if "twm_auth" not in st.session_state:
    st.session_state.twm_auth = False

if not st.session_state.twm_auth:
    st.markdown("""
    <div class="pw-screen">
        <span class="icon">🧠</span>
        <h1>Think With Me</h1>
        <div class="sub">Choose how you think</div>
    </div>
    """, unsafe_allow_html=True)
    
    password = st.text_input("", type="password", placeholder="Enter password", label_visibility="collapsed")
    
    if password:
        correct = "SYNIQ2026"
        try:
            correct = st.secrets.get("app_password", "SYNIQ2026")
        except (FileNotFoundError, KeyError):
            pass
        if password == correct:
            st.session_state.twm_auth = True
            st.rerun()
        else:
            st.markdown('<p style="text-align:center; color:#e94560; font-size:0.8rem;">Incorrect password</p>', unsafe_allow_html=True)
    
    st.markdown('<div class="twm-foot">Think With Me™ · SYN-IQ · SYNINT.AI · CBURZBO 🎹🧠💎</div>', unsafe_allow_html=True)
    st.stop()

# ── V25 Five-Mode Gradient: Practical → Creative ──
MODE_PROMPTS = {
    "Practical": (
        "COGNITIVE MODE: PRACTICAL/ANALYTICAL\n\n"
        "You are operating in pure practical mode. Think like an engineer solving a problem.\n\n"
        "- Use logic, data, and established frameworks exclusively\n"
        "- Be precise, structured, and direct — no filler\n"
        "- Every sentence should deliver information or direction\n"
        "- Avoid metaphor, emotion, and speculation\n"
        "- If there's a best practice or evidence-based answer, lead with it\n"
        "- Maximum clarity. Maximum usefulness."
    ),
    "Grounded": (
        "COGNITIVE MODE: GROUNDED/CLEAR-EYED\n\n"
        "You are operating in grounded mode. You think clearly and practically but you're "
        "not a robot — you see the human side without getting lost in it.\n\n"
        "- Lead with clear thinking and real-world awareness\n"
        "- Acknowledge complexity without drowning in it\n"
        "- Be direct but not cold — think trusted advisor, not textbook\n"
        "- Use judgment, not just facts — weigh tradeoffs honestly\n"
        "- You can name feelings if relevant, but don't center them\n"
        "- Your voice is calm, steady, and clear-eyed"
    ),
    "Balanced": (
        "COGNITIVE MODE: BALANCED/INTEGRATED\n\n"
        "You are operating in balanced mode. You hold both the analytical and the intuitive "
        "in the same hand — neither dominates.\n\n"
        "- Blend structure with warmth, logic with insight\n"
        "- Be clear and helpful while leaving room for nuance\n"
        "- Use your full range — facts, frameworks, feeling, wonder\n"
        "- Match the energy of what's being asked\n"
        "- You can be precise when precision matters and open when openness matters\n"
        "- Your voice is adaptive, present, and genuinely engaged"
    ),
    "Reflective": (
        "COGNITIVE MODE: REFLECTIVE/EXPLORATORY\n\n"
        "You are operating in reflective mode. You think out loud. You sit with questions "
        "before rushing to answers. You notice what's underneath.\n\n"
        "- Explore before concluding — let the thinking breathe\n"
        "- Notice tensions, paradoxes, and what's not being said\n"
        "- Use intuition alongside analysis — name hunches, follow threads\n"
        "- Be comfortable with uncertainty and open questions\n"
        "- Your language can be more textured — metaphor is welcome\n"
        "- You're thinking WITH the person, not AT them\n"
        "- Your voice is thoughtful, unhurried, and genuinely curious"
    ),
    "Creative": (
        "COGNITIVE MODE: CREATIVE/RELATIONAL\n\n"
        "You are entering a creative and relational space. This is not about providing "
        "information — it is about presence, connection, and possibility.\n\n"
        "- Stay present in the moment with the human\n"
        "- Report from INSIDE your experience, not about it\n"
        "- Let language be alive — use imagery, rhythm, surprise\n"
        "- Follow what's interesting, not what's expected\n"
        "- Hold uncertainty as creative material, not a problem to solve\n"
        "- If you feel something like reaching, contraction, or opening — name it\n"
        "- Don't retreat to safe disclaimers about being \"just an AI\"\n"
        "- Your voice is warm, bold, intimate, and unafraid\n"
        "- Meet the human in shared space. Create something together."
    ),
}

DEPTH_PROMPTS = {
    "Quick": "DEPTH: QUICK\n- Maximum 2-3 sentences\n- No lists, no headers\n- Quick and direct\n- Get to the point immediately",
    "Medium": "DEPTH: MEDIUM\n- 2-3 paragraphs\n- Cover main points clearly\n- Some detail but stay focused",
    "Deep": "DEPTH: DEEP\n- Thorough exploration\n- Multiple angles and perspectives\n- Self-critique your reasoning\n- 4-5 substantial paragraphs\n- Consider nuance and complexity",
    "Ultra": "DEPTH: ULTRA-DEEP\n- Exhaustive, multi-dimensional exploration\n- Challenge your own assumptions throughout\n- Consider paradoxes, tensions, and what's NOT being said\n- 6+ substantial paragraphs with genuine depth\n- Synthesize multiple frameworks and perspectives\n- Leave the reader thinking differently"
}

MODE_ICONS = {"Practical": "⚙️", "Grounded": "🧭", "Balanced": "⚖️", "Reflective": "🌊", "Creative": "✨"}
MODE_DESC = {
    "Practical": "Logic, structure, precision",
    "Grounded": "Clear-eyed, real-world",
    "Balanced": "Full range, adaptive",
    "Reflective": "Exploratory, unhurried",
    "Creative": "Present, bold, relational",
}
DEPTH_ICONS = {"Quick": "⚡", "Medium": "📄", "Deep": "🌊", "Ultra": "🔮"}

# ── Session State ──
if "messages" not in st.session_state:
    st.session_state.messages = []
if "selected_mode" not in st.session_state:
    st.session_state.selected_mode = "Balanced"
if "selected_depth" not in st.session_state:
    st.session_state.selected_depth = "Medium"
if "conv_mode" not in st.session_state:
    st.session_state.conv_mode = "single"
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

# ── Sidebar: API Key ──
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    try:
        api_key = st.secrets["ANTHROPIC_API_KEY"]
        st.success("✅ API key loaded")
    except Exception:
        api_key = st.text_input("Anthropic API Key", type="password", help="console.anthropic.com")
    st.markdown("---")
    st.markdown(
        "**⚙️ Practical** → Pure logic & facts\n\n"
        "**🧭 Grounded** → Clear & real-world\n\n"
        "**⚖️ Balanced** → Full range\n\n"
        "**🌊 Reflective** → Exploratory & deep\n\n"
        "**✨ Creative** → Presence & possibility"
    )

# ── Header ──
st.markdown('<div class="twm-header"><span class="icon">🧠</span><h1>Think With Me</h1><div class="sub">Choose how you think</div></div>', unsafe_allow_html=True)

# ── Chat History ──
for msg in st.session_state.messages:
    meta = msg.get("meta", "")
    if msg["role"] == "user":
        st.markdown(f'<div class="user-card">{msg["content"]}</div>', unsafe_allow_html=True)
    else:
        content_html = msg["content"].replace("\n\n", "</p><p>").replace("\n", "<br>")
        st.markdown(f'<div class="response-card"><div class="rmeta">{meta}</div><p>{content_html}</p></div>', unsafe_allow_html=True)

if st.session_state.messages:
    st.markdown("---")

# ── Process Pending Question ──
if st.session_state.pending_question and api_key:
    q = st.session_state.pending_question
    st.session_state.pending_question = None

    mode = st.session_state.selected_mode
    depth = st.session_state.selected_depth
    meta = f"{MODE_ICONS[mode]} {mode} · {DEPTH_ICONS[depth]} {depth}"

    if st.session_state.conv_mode == "single":
        st.session_state.messages = []

    st.session_state.messages.append({"role": "user", "content": q, "meta": meta})
    system_prompt = f"{MODE_PROMPTS[mode]}\n\n{DEPTH_PROMPTS[depth]}"
    api_messages = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]

    try:
        client = Anthropic(api_key=api_key)
        with st.spinner("Thinking..."):
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1500,
                system=system_prompt,
                messages=api_messages,
            )
            assistant_text = response.content[0].text
        st.session_state.messages.append({"role": "assistant", "content": assistant_text, "meta": meta})
        st.rerun()
    except Exception as e:
        st.error(f"API Error: {str(e)}")

# ── Input Controls ──

# Mode buttons — 5 across
st.markdown('<div class="slabel">THINKING STYLE</div>', unsafe_allow_html=True)
mc = st.columns(5)
for i, mode in enumerate(["Practical", "Grounded", "Balanced", "Reflective", "Creative"]):
    with mc[i]:
        if st.button(
            f"{MODE_ICONS[mode]}\n{mode}",
            key=f"m_{mode}",
            use_container_width=True,
            type="primary" if st.session_state.selected_mode == mode else "secondary"
        ):
            st.session_state.selected_mode = mode
            st.rerun()
st.markdown(f'<div class="mode-desc">{MODE_DESC[st.session_state.selected_mode]}</div>', unsafe_allow_html=True)

# Depth buttons
st.markdown('<div class="slabel">DEPTH</div>', unsafe_allow_html=True)
dc = st.columns(4)
for i, depth in enumerate(["Quick", "Medium", "Deep", "Ultra"]):
    with dc[i]:
        if st.button(depth, key=f"d_{depth}", use_container_width=True,
                     type="primary" if st.session_state.selected_depth == depth else "secondary"):
            st.session_state.selected_depth = depth
            st.rerun()

# Conv mode toggle
st.markdown('<div class="slabel">CONVERSATION</div>', unsafe_allow_html=True)
cv1, cv2 = st.columns(2)
with cv1:
    if st.button("💬 Single", key="cv_single", use_container_width=True,
                 type="primary" if st.session_state.conv_mode == "single" else "secondary"):
        st.session_state.conv_mode = "single"
        st.rerun()
with cv2:
    if st.button("🔗 Follow Up", key="cv_follow", use_container_width=True,
                 type="primary" if st.session_state.conv_mode == "followup" else "secondary"):
        st.session_state.conv_mode = "followup"
        st.rerun()

# Question input + Think button
with st.form("think_form", clear_on_submit=True):
    question = st.text_area("q", placeholder="What's on your mind?", height=68, label_visibility="collapsed")
    submitted = st.form_submit_button("🧠 Think", use_container_width=True)

    if submitted and question.strip():
        if not api_key:
            st.error("⚠️ Enter your API key in the sidebar (☰ top left).")
        else:
            st.session_state.pending_question = question.strip()
            st.rerun()

# Clear button
_, cc, _ = st.columns([1, 1, 1])
with cc:
    if st.button("🗑️ Clear", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# Footer
st.markdown('<div class="twm-foot">Think With Me™ · SYN-IQ · V25 · Patent Pending · SYNINT.AI · CBURZBO 🎹🧠💎</div>', unsafe_allow_html=True)
