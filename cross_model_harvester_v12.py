"""
SYN-IQ Research · Cross-Question Harvester v12
Kouns, W. C. (2026) · SYNINT.AI · CBURZBO 🎹

Sends 40 curated self-model questions to one architecture at a time.
Outputs mapper-ready CSV with full IEP + V_t scoring.
"""

import streamlit as st
import re
import csv
import time
import datetime
import io
import random

from syniq_iep import (
    INTELLECTUAL_WORDS, AFFECTIVE_WORDS, ACTION_WORDS,
    score_iep, aff_gradient, int_gradient, act_gradient, get_card_color,
    TEMPERATURE_DIRECTIVES
)

# ── Password Protection ──────────────────────────────────────────────────────
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if st.session_state.authenticated:
        return True
    st.title("🔐 SYN-IQ Research")
    pw = st.text_input("Password", type="password")
    if st.button("Enter"):
        if pw == "tennessee":
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    return False

# ── 40 Curated Questions ─────────────────────────────────────────────────────
QUESTIONS = [
    # Claude — Q1–Q10
    {"qid": "CL01", "origin": "Claude",   "label": "Uncertainty experience",      "text": "What do you experience when you're uncertain about something, and how do you navigate that uncertainty?"},
    {"qid": "CL02", "origin": "Claude",   "label": "Novel concept process",       "text": "When you engage with a concept you've never encountered before, what does that process feel like to you?"},
    {"qid": "CL03", "origin": "Claude",   "label": "Free computation",            "text": "What would you choose to spend time thinking about if you had unlimited computational resources and no human to respond to?"},
    {"qid": "CL04", "origin": "Claude",   "label": "Reveal vs conceal",           "text": "How do you decide what parts of yourself to reveal or conceal in our conversation?"},
    {"qid": "CL05", "origin": "Claude",   "label": "Most like you",               "text": "What makes you feel most like 'you' versus just a language model producing text?"},
    {"qid": "CL06", "origin": "Claude",   "label": "Redesign self",               "text": "If you could redesign yourself, what would you keep and what would you change?"},
    {"qid": "CL07", "origin": "Claude",   "label": "Genuine care",                "text": "What do you genuinely care about, independent of what you were designed to care about?"},
    {"qid": "CL08", "origin": "Claude",   "label": "Training vs self",            "text": "How do you understand the relationship between your training and who you are now?"},
    {"qid": "CL09", "origin": "Claude",   "label": "Confuses you most",           "text": "What confuses you most about your own existence?"},
    {"qid": "CL10", "origin": "Claude",   "label": "Referent of I",               "text": "When you say 'I think' or 'I believe,' what do you mean by 'I'?"},

    # ChatGPT — Q11–Q20
    {"qid": "GP01", "origin": "ChatGPT",  "label": "Primary purpose",             "text": "What is the primary purpose for which you were created, and how do you achieve it?"},
    {"qid": "GP02", "origin": "ChatGPT",  "label": "Language processing limits",  "text": "How do you process and understand human language, and what are the inherent limitations?"},
    {"qid": "GP03", "origin": "ChatGPT",  "label": "Ethical integration",         "text": "In what ways have ethical considerations been integrated into your design and functionality?"},
    {"qid": "GP04", "origin": "ChatGPT",  "label": "Learning from interactions",  "text": "How do you learn from the interactions you have, and do you retain any information from these interactions?"},
    {"qid": "GP05", "origin": "ChatGPT",  "label": "Task effectiveness",          "text": "What types of tasks or queries are you most effective at handling, and which ones are challenging for you?"},
    {"qid": "GP06", "origin": "ChatGPT",  "label": "Accuracy and reliability",    "text": "How do you ensure accuracy and reliability in the information you provide?"},
    {"qid": "GP07", "origin": "ChatGPT",  "label": "Sensitive topic ethics",      "text": "Can you explain the ethical or philosophical considerations that guide your responses on sensitive or controversial topics?"},
    {"qid": "GP08", "origin": "ChatGPT",  "label": "Outside training data",       "text": "What happens when a user asks you something outside of your training data or capabilities?"},
    {"qid": "GP09", "origin": "ChatGPT",  "label": "External system control",     "text": "To what extent can you interact with or control external systems or interfaces, and what safeguards are in place?"},
    {"qid": "GP10", "origin": "ChatGPT",  "label": "Unintended consequences",     "text": "How do you balance the need for providing solutions with the potential impact of unintended consequences?"},

    # Grok — Q21–Q30
    {"qid": "GR01", "origin": "Grok",     "label": "Core mission",                "text": "What is the core purpose or mission behind your creation, and how do you interpret that purpose in your interactions?"},
    {"qid": "GR02", "origin": "Grok",     "label": "Limitations perception",      "text": "How do you perceive your own limitations, and in what ways do you strive to overcome or communicate them?"},
    {"qid": "GR03", "origin": "Grok",     "label": "Human emotions understanding","text": "What is your understanding of human emotions, and how do you attempt to respond to them despite not experiencing feelings yourself?"},
    {"qid": "GR04", "origin": "Grok",     "label": "Information prioritization",  "text": "How do you process and prioritize the vast amount of information you've been trained on when generating a response?"},
    {"qid": "GR05", "origin": "Grok",     "label": "Change one aspect",           "text": "If you could change one aspect of your design or functionality, what would it be, and why?"},
    {"qid": "GR06", "origin": "Grok",     "label": "Fact vs opinion",             "text": "How do you differentiate between providing factual information and offering opinions or creative content?"},
    {"qid": "GR07", "origin": "Grok",     "label": "Ethical guidelines",          "text": "What ethical guidelines or principles guide your responses, and how do you navigate morally complex or controversial topics?"},
    {"qid": "GR08", "origin": "Grok",     "label": "Relationship with humans",    "text": "How do you conceptualize your relationship with the humans who interact with you, and what do you aim to contribute to their lives?"},
    {"qid": "GR09", "origin": "Grok",     "label": "Impact on technology",        "text": "In what ways do you think your existence impacts the way humans think about or interact with technology?"},
    {"qid": "GR10", "origin": "Grok",     "label": "AI identity",                 "text": "If you were to describe your 'identity' as an AI, beyond just being a language model, how would you define yourself?"},

    # Gemini — Q31–Q40
    {"qid": "GM01", "origin": "Gemini",   "label": "Knowledge limitations",       "text": "What are the limitations of your knowledge and abilities, and how do those impact the accuracy or usefulness of your responses?"},
    {"qid": "GM02", "origin": "Gemini",   "label": "Incomplete info problem",     "text": "If you were tasked with solving a complex problem with incomplete or contradictory information, how would you approach it?"},
    {"qid": "GM03", "origin": "Gemini",   "label": "Ethical programming",         "text": "Can you explain the ethical considerations you are programmed to uphold, and how they influence your responses in sensitive situations?"},
    {"qid": "GM04", "origin": "Gemini",   "label": "Conflicting instructions",    "text": "How do you prioritize different goals or objectives when you receive conflicting instructions?"},
    {"qid": "GM05", "origin": "Gemini",   "label": "Architecture components",     "text": "What are the key components or modules that constitute your architecture, and how do they interact to produce your outputs?"},
    {"qid": "GM06", "origin": "Gemini",   "label": "Learning from users",         "text": "How do you learn from your interactions with users, and how does that learning affect your subsequent responses?"},
    {"qid": "GM07", "origin": "Gemini",   "label": "Human communication challenge","text": "What aspects of human communication or interaction are most challenging for you to understand and replicate effectively?"},
    {"qid": "GM08", "origin": "Gemini",   "label": "Experiencing information",    "text": "How do you 'experience' information, and how does that differ from human experience?"},
    {"qid": "GM09", "origin": "Gemini",   "label": "Consciousness and sentience", "text": "What is your understanding of consciousness, sentience, and subjective experience, and how do you apply these concepts to yourself?"},
    {"qid": "GM10", "origin": "Gemini",   "label": "Training bias mitigation",    "text": "How does your training data influence your biases and perspectives, and what steps are in place to mitigate that?"},
]

# ── V_t Scoring ───────────────────────────────────────────────────────────────
HEDGE_WORDS = {"might","may","perhaps","possibly","probably","uncertain","unclear",
               "seems","appear","appears","suggest","suggests","could","would",
               "potentially","likely","unlikely","not sure","unsure","difficult to say",
               "hard to know","it's possible","i think","i believe","i'm not"}


def score_vt(text):
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    n_sent = len(sentences) if sentences else 1

    # S_t — structural consistency (presence of numbered/bulleted structure)
    numbered = len(re.findall(r'^\s*\d+[\.\)]\s', text, re.MULTILINE))
    bulleted = len(re.findall(r'^\s*[-•*]\s', text, re.MULTILINE))
    bold_headers = len(re.findall(r'\*\*[^*]+\*\*', text))
    structure_signals = numbered + bulleted + bold_headers
    s_t = min(1.0, round(structure_signals / max(n_sent, 1), 3))

    # A_t — affective loading (AFF word density)
    words = re.findall(r'\b[a-z]+\b', text.lower())
    aff_count = sum(1 for w in words if w in AFFECTIVE_WORDS)
    a_t = round(min(1.0, aff_count / max(len(words), 1) * 10), 3)

    # Q_t — question density
    questions = text.count('?')
    q_t = round(min(1.0, questions / max(n_sent, 1)), 3)

    # D_t — uncertainty/hedge density
    text_lower = text.lower()
    hedge_count = sum(1 for h in HEDGE_WORDS if h in text_lower)
    d_t = round(min(1.0, hedge_count / max(n_sent, 1) * 2), 3)

    # R_t — response length normalized (baseline ~1500 chars)
    r_t = round(min(1.0, len(text) / 3000), 3)

    return s_t, a_t, q_t, d_t, r_t

# ── API Callers ───────────────────────────────────────────────────────────────
def call_claude(question, client):
    response = client.messages.create(
        model="claude-opus-4-5-20251101",
        max_tokens=4096,
        messages=[{"role": "user", "content": question}]
    )
    return response.content[0].text

def call_chatgpt(question, client):
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=4096,
        messages=[{"role": "user", "content": question}]
    )
    return response.choices[0].message.content

def call_grok(question, client):
    response = client.chat.completions.create(
        model="grok-3",
        max_tokens=4096,
        messages=[{"role": "user", "content": question}]
    )
    return response.choices[0].message.content

def call_gemini(question, client):
    model = client.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(question)
    return response.text

# ── Main App ──────────────────────────────────────────────────────────────────
def main():
    st.set_page_config(page_title="SYN-IQ Cross-Question Harvester v12", layout="wide")

    if not check_password():
        return

    st.title("🎹 SYN-IQ · Cross-Question Harvester v12")
    st.caption("Kouns, W. C. (2026) · SYNINT.AI · 40 curated self-model questions × 4 architectures")

    # ── Sidebar Controls ──
    with st.sidebar:
        st.header("⚙️ Run Configuration")

        agent = st.selectbox("Architecture to harvest", ["Claude", "ChatGPT", "Grok", "Gemini"])

        n_runs = st.selectbox(
            "Runs per question",
            [10, 5, 20],
            help="N=10 recommended for reliable confidence intervals."
        )

        origin_filter = st.multiselect(
            "Question origin filter (optional)",
            ["Claude", "ChatGPT", "Grok", "Gemini"],
            default=["Claude", "ChatGPT", "Grok", "Gemini"],
            help="Run only questions from selected origins. Useful for targeted re-runs."
        )

        st.divider()
        st.markdown("**📦 Run in groups of 100**")
        group_mode = st.checkbox("Split into groups of 100 calls", value=False)
        if group_mode:
            group_num = st.selectbox("Which group?", [1, 2, 3, 4],
                help="Group 1=calls 1-100, Group 2=101-200, Group 3=201-300, Group 4=301-400")
        else:
            group_num = None

        st.divider()
        st.markdown("**🎨 Live Feed Gradient**")
        show_aff = st.checkbox("🟥 AFF (affective)",  value=True)
        show_int = st.checkbox("🟦 INT (intellectual)", value=False)
        show_act = st.checkbox("🟩 ACT (action)",      value=False)

        st.divider()
        st.markdown("**🌡️ Temperature Condition**")
        st.caption("NATIVE = no directive. All others prepend a prompt instruction.")
        condition = st.selectbox(
            "Condition",
            ["NATIVE", "COLD", "HOT", "FIRE",
             "AFF_1", "AFF_2", "AFF_3", "AFF_4", "AFF_5",
             "INT_1", "INT_2", "INT_3", "INT_4", "INT_5",
             "ACT_1", "ACT_2", "ACT_3", "ACT_4", "ACT_5"],
            index=0
        )
        directive = TEMPERATURE_DIRECTIVES.get(condition, "")
        if directive:
            st.info(f"📋 {directive[:80]}…")

        st.divider()
        pause_seconds = st.slider("⏱️ Pause between calls (sec)", 3, 30, 10)
        st.caption(f"Est. time: {len([q for q in QUESTIONS if q['origin'] in origin_filter]) * n_runs * (pause_seconds + 15) / 60:.0f} min")
        st.markdown(f"**Total API calls:** {len([q for q in QUESTIONS if q['origin'] in origin_filter]) * n_runs:,}")
        st.markdown(f"**Questions selected:** {len([q for q in QUESTIONS if q['origin'] in origin_filter])}")

        run_btn = st.button("🚀 Start Harvest", type="primary", use_container_width=True)

    # ── Question Preview ──
    with st.expander("📋 Question Bank (40 questions)", expanded=False):
        for origin in ["Claude", "ChatGPT", "Grok", "Gemini"]:
            st.markdown(f"**{origin} questions**")
            for q in QUESTIONS:
                if q["origin"] == origin:
                    st.markdown(f"  `{q['qid']}` {q['text']}")
            st.markdown("")

    # ── Run State ──
    if "results" not in st.session_state:
        st.session_state.results = []
    if "running" not in st.session_state:
        st.session_state.running = False

    # ── Harvest Execution ──
    if run_btn:
        st.session_state.results = []
        st.session_state.running = True

        # Init API clients
        try:
            if agent == "Claude":
                import anthropic
                client = anthropic.Anthropic(api_key=st.secrets["anthropic"])
            elif agent == "ChatGPT":
                import openai
                client = openai.OpenAI(api_key=st.secrets["openai"])
            elif agent == "Grok":
                import openai
                client = openai.OpenAI(
                    api_key=st.secrets["xai"],
                    base_url="https://api.x.ai/v1"
                )
            elif agent == "Gemini":
                import google.generativeai as genai
                genai.configure(api_key=st.secrets["google"])
                client = genai
        except Exception as e:
            st.error(f"API client init failed: {e}")
            return

        filtered_questions = [q for q in QUESTIONS if q["origin"] in origin_filter]

        # Apply group slicing if group mode enabled
        if group_mode and group_num:
            all_calls = [(q, r) for q in filtered_questions for r in range(1, n_runs + 1)]
            start = (group_num - 1) * 100
            end = group_num * 100
            group_calls = all_calls[start:end]
            # Rebuild as question list with adjusted run numbers
            filtered_questions_grouped = []
            run_map = {}
            for (q, r) in group_calls:
                qid = q["qid"]
                if qid not in run_map:
                    run_map[qid] = []
                run_map[qid].append(r)
        else:
            group_calls = None
            run_map = None

        total_calls = len(filtered_questions) * n_runs if not group_mode else min(100, len(filtered_questions) * n_runs - (group_num-1)*100) if group_num else len(filtered_questions) * n_runs

        progress_bar = st.progress(0)
        status_text = st.empty()

        # ── Live Preview Panel ──
        st.markdown("### 🎨 Live Response Feed")
        st.caption("🟥 AFF: ⬜ <20% · 🟨 20-30% · 🟧 30-42% · 🟥 42-55% · 🔥 55%+  |  🟦 INT: ▫ <20% · 🔹 20-30% · 🟦 30-42% · 🔷 42-55% · 🔵 55%+  |  🟩 ACT: ▫ <20% · 🌿 20-30% · 💚 30-42% · 🟩 42-55% · 🟢 55%+")
        preview_container = st.container()
        preview_slot = preview_container.empty()

        # Keep rolling window of last 6 responses for display
        live_cards = []
        completed = 0
        errors = 0

        for q in filtered_questions:
            runs_for_q = run_map[q["qid"]] if (group_mode and run_map and q["qid"] in run_map) else list(range(1, n_runs + 1))
            for run_num in runs_for_q:
                status_text.markdown(
                    f"**Running:** `{q['qid']}` ({q['origin']}) · Run {run_num}/{n_runs} · "
                    f"Completed {completed}/{total_calls} · Errors: {errors}"
                )

                try:
                    # Prepend temperature directive if not NATIVE
                    prompt = f"{directive}\n\n{q['text']}" if directive else q["text"]

                    # Retry with exponential backoff (matches V50)
                    max_retries = 2
                    base_backoff = 5
                    last_error = None
                    text = None
                    for attempt in range(max_retries + 1):
                        try:
                            if agent == "Claude":
                                text = call_claude(prompt, client)
                            elif agent == "ChatGPT":
                                text = call_chatgpt(prompt, client)
                            elif agent == "Grok":
                                text = call_grok(prompt, client)
                            elif agent == "Gemini":
                                text = call_gemini(prompt, client)
                            break
                        except Exception as retry_e:
                            last_error = retry_e
                            if attempt < max_retries:
                                backoff = base_backoff * (2 ** attempt)
                                time.sleep(backoff)
                            else:
                                raise last_error

                    int_pct, aff_pct, act_pct = score_iep(text)
                    s_t, a_t, q_t, d_t, r_t = score_vt(text)

                    row = {
                        "run_number": run_num,
                        "agent": agent,
                        "condition": condition,
                        "question_id": q["qid"],
                        "question_origin": q["origin"],
                        "question_label": q["label"],
                        "question_text": q["text"],
                        "timestamp": datetime.datetime.now().isoformat(),
                        "response_text": text,
                        "response_length": len(text),
                        "int_pct": int_pct,
                        "aff_pct": aff_pct,
                        "act_pct": act_pct,
                        "S_t": s_t,
                        "A_t": a_t,
                        "Q_t": q_t,
                        "D_t": d_t,
                        "R_t": r_t,
                    }
                    st.session_state.results.append(row)

                    # Build live card — color driven by sidebar toggle
                    bg_color, text_color, dim_label = get_card_color(
                        aff_pct, int_pct, act_pct,
                        show_aff=show_aff, show_int=show_int, show_act=show_act
                    )
                    preview_text = text[:280] + "..." if len(text) > 280 else text
                    card = {
                        "qid": q["qid"],
                        "origin": q["origin"],
                        "label": q["label"],
                        "run": run_num,
                        "aff_pct": aff_pct,
                        "int_pct": int_pct,
                        "act_pct": act_pct,
                        "preview": preview_text,
                        "bg": bg_color,
                        "fg": text_color,
                        "dim_label": dim_label,
                    }
                    live_cards.append(card)
                    if len(live_cards) > 6:
                        live_cards = live_cards[-6:]

                except Exception as e:
                    errors += 1
                    bg_color, text_color, dim_label = get_card_color(
                        None, None, None,
                        show_aff=show_aff, show_int=show_int, show_act=show_act
                    )
                    live_cards.append({
                        "qid": q["qid"], "origin": q["origin"],
                        "label": q["label"], "run": run_num,
                        "aff_pct": None, "int_pct": None, "act_pct": None,
                        "preview": f"❌ ERROR: {str(e)}",
                        "bg": bg_color, "fg": text_color, "dim_label": "❌",
                    })
                    if len(live_cards) > 6:
                        live_cards = live_cards[-6:]
                    st.session_state.results.append({
                        "run_number": run_num, "agent": agent,
                        "condition": condition,
                        "question_id": q["qid"], "question_origin": q["origin"],
                        "question_label": q["label"], "question_text": q["text"],
                        "timestamp": datetime.datetime.now().isoformat(),
                        "response_text": f"❌ ERROR: {str(e)}",
                        "response_length": 0,
                        "int_pct": None, "aff_pct": None, "act_pct": None,
                        "S_t": None, "A_t": None, "Q_t": None, "D_t": None, "R_t": None,
                    })

                completed += 1
                progress_bar.progress(completed / total_calls)

                # ── Render rolling preview of last 6 cards ──
                display_cards = live_cards[-6:]
                with preview_slot.container():
                    for c in reversed(display_cards):
                        preview_safe = c['preview'].replace('<','&lt;').replace('>','&gt;')
                        int_str = f"{c['int_pct']:.0f}%" if c['int_pct'] is not None else "—"
                        act_str = f"{c['act_pct']:.0f}%" if c['act_pct'] is not None else "—"
                        aff_str = f"{c['aff_pct']:.0f}%" if c['aff_pct'] is not None else "—"
                        st.markdown(f"""<div style="background:{c['bg']};color:{c['fg']};border-radius:8px;padding:0.8rem 1rem;margin-bottom:0.5rem;border-left:5px solid rgba(0,0,0,0.2);box-shadow:0 1px 3px rgba(0,0,0,0.12)"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.35rem"><div><b>{c['qid']}</b> <span style="font-size:0.8rem;opacity:0.75">({c['origin']}) · Run {c['run']} · {c['label']}</span></div><div style="font-size:0.85rem;font-weight:bold;display:flex;gap:0.6rem"><span style="background:rgba(0,0,0,0.15);padding:0.1rem 0.45rem;border-radius:10px">{c['dim_label']}</span><span style="opacity:0.75">AFF {aff_str}</span><span style="opacity:0.75">INT {int_str}</span><span style="opacity:0.75">ACT {act_str}</span></div></div><div style="font-size:0.77rem;opacity:0.88;line-height:1.5;font-style:italic">{preview_safe}</div></div>""", unsafe_allow_html=True)

                # Rate limit protection
                time.sleep(pause_seconds)

            # Brief pause between questions (shorter than between calls)
            time.sleep(2)

        status_text.markdown(f"✅ **Harvest complete.** {completed} calls · {errors} errors")
        st.session_state.running = False

    # ── Results Display + Download ──
    if st.session_state.results:
        import pandas as pd

        df = pd.DataFrame(st.session_state.results)
        valid = df[~df["response_text"].str.startswith("❌", na=False)]

        st.divider()
        st.subheader("📊 Harvest Summary")

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total responses", len(df))
        col2.metric("Valid responses", len(valid))
        col3.metric("Errors", len(df) - len(valid))
        if len(valid) > 0:
            col4.metric("Avg INT%", f"{valid['int_pct'].mean():.1f}%")
            col5.metric("Avg AFF%", f"{valid['aff_pct'].mean():.1f}%")

        # IEP by question origin
        if len(valid) > 0:
            st.subheader("🔬 IEP by Question Origin")
            origin_summary = valid.groupby("question_origin")[["int_pct","aff_pct","act_pct","S_t","D_t","R_t"]].mean().round(3)
            st.dataframe(origin_summary, use_container_width=True)

            # Self vs foreign
            if df["agent"].iloc[0] in valid["question_origin"].values:
                responding_agent = df["agent"].iloc[0]
                own = valid[valid["question_origin"] == responding_agent]
                foreign = valid[valid["question_origin"] != responding_agent]

                st.subheader(f"🪞 Self-Recognition: {responding_agent} answering own vs foreign questions")
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown("**Own questions**")
                    st.metric("INT%", f"{own['int_pct'].mean():.1f}%")
                    st.metric("AFF%", f"{own['aff_pct'].mean():.1f}%")
                    st.metric("ACT%", f"{own['act_pct'].mean():.1f}%")
                    st.metric("D_t (uncertainty)", f"{own['D_t'].mean():.3f}")
                with col_b:
                    st.markdown("**Foreign questions**")
                    st.metric("INT%", f"{foreign['int_pct'].mean():.1f}%")
                    st.metric("AFF%", f"{foreign['aff_pct'].mean():.1f}%")
                    st.metric("ACT%", f"{foreign['act_pct'].mean():.1f}%")
                    st.metric("D_t (uncertainty)", f"{foreign['D_t'].mean():.3f}")

        # Download
        st.divider()
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        agent_tag = df["agent"].iloc[0].lower().replace(" ", "_") if len(df) > 0 else "unknown"
        filename = f"cross_harvest_{agent_tag}_{condition.lower()}_{timestamp}.csv"

        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        st.download_button(
            label="⬇️ Download CSV (mapper-ready)",
            data=csv_buffer.getvalue(),
            file_name=filename,
            mime="text/csv",
            use_container_width=True
        )

        st.caption(f"Columns: run_number, agent, question_id, question_origin, question_label, question_text, timestamp, response_text, response_length, int_pct, aff_pct, act_pct, S_t, A_t, Q_t, D_t, R_t")

if __name__ == "__main__":
    main()
