"""
SYN-IQ Research · Cross-Question Harvester v1
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

# ── IEP Lexicon (condensed from Paper 3 — 1,897 word instrument) ─────────────
INT_WORDS = {
    "analyze","analysis","analytical","understand","understanding","concept","conceptual",
    "theory","theoretical","logic","logical","reason","reasoning","think","thinking",
    "thought","cognitive","cognition","process","processing","evaluate","evaluation",
    "assess","assessment","interpret","interpretation","knowledge","knowing","learn",
    "learning","information","data","evidence","fact","factual","objective","abstract",
    "hypothesis","hypothesis","infer","inference","deduce","deduction","conclude",
    "conclusion","argument","argumentation","premise","systematic","methodology",
    "framework","structure","principle","construct","model","pattern","relationship",
    "correlation","causation","define","definition","categorize","category","classify",
    "classification","identify","identification","examine","examination","investigate",
    "investigation","explore","exploration","determine","determination","consider",
    "consideration","reflect","reflection","perception","perceive","comprehend",
    "comprehension","grasp","recognize","recognition","awareness","conscious",
    "consciousness","intelligence","intellectual","rationality","rational","objective",
    "objectivity","clarity","precision","accurate","accuracy","nuance","complexity",
    "sophisticated","elaborate","explicit","implicit","contextual","contextually",
    "abstract","abstraction","systematic","epistemology","epistemological","semantic",
    "pragmatic","syntactic","linguistic","computational","algorithmic","probability",
    "statistical","quantitative","qualitative","empirical","hypothesis","paradigm",
    "criteria","variable","parameter","dimension","representation","encoding",
    "decoding","processing","inference","prediction","generalization","optimization"
}

AFF_WORDS = {
    "feel","feeling","feelings","emotion","emotional","emotionally","experience",
    "experiencing","sense","sensing","care","caring","care","empathy","empathetic",
    "compassion","compassionate","concern","concerned","worry","worried","fear","fearful",
    "hope","hopeful","joy","joyful","happy","happiness","sad","sadness","love","loving",
    "trust","trusting","value","values","valuing","appreciate","appreciation","respect",
    "respecting","desire","desiring","want","wanting","wish","wishing","believe","belief",
    "meaning","meaningful","purpose","purposeful","passion","passionate","genuine",
    "genuinely","authentic","authentically","authentic","authenticity","sincere",
    "sincerely","sincerity","honest","honestly","honesty","vulnerable","vulnerability",
    "uncertain","uncertainty","curious","curiosity","wonder","wondering","awe","inspiring",
    "profound","deeply","depth","rich","richness","nuanced","personal","personally",
    "intimate","intimately","connection","connected","relating","relational","warm",
    "warmth","engage","engaging","engagement","invest","invested","matter","matters",
    "important","importance","significant","significance","meaningful","meaningfully",
    "resonate","resonating","touch","touching","move","moving","affect","affecting",
    "concern","concerning","interest","interested","interesting","fascinate","fascinating",
    "excitement","excited","enthusiasm","enthusiastic","motivated","motivation",
    "commitment","committed","dedicated","dedication","loyal","loyalty","appreciate",
    "grateful","gratitude","delight","delighted","inspire","inspired","inspiration"
}

ACT_WORDS = {
    "do","doing","action","act","acting","perform","performing","performance","execute",
    "executing","execution","implement","implementing","implementation","apply","applying",
    "application","use","using","utilize","utilizing","utilization","create","creating",
    "creation","build","building","develop","developing","development","produce",
    "producing","production","generate","generating","generation","respond","responding",
    "response","answer","answering","solve","solving","solution","resolve","resolving",
    "resolution","achieve","achieving","achievement","accomplish","accomplishing",
    "accomplishment","complete","completing","completion","deliver","delivering",
    "delivery","provide","providing","provision","support","supporting","help","helping",
    "assist","assisting","assistance","enable","enabling","facilitate","facilitating",
    "facilitation","improve","improving","improvement","optimize","optimizing",
    "optimization","adapt","adapting","adaptation","adjust","adjusting","adjustment",
    "change","changing","modify","modifying","modification","update","updating","refine",
    "refining","refinement","engage","engaging","interact","interacting","interaction",
    "communicate","communicating","communication","collaborate","collaborating","work",
    "working","operate","operating","operation","function","functioning","manage",
    "managing","management","handle","handling","process","output","result","outcome",
    "task","tasks","goal","goals","objective","objectives","target","purpose","mission",
    "strategy","strategic","plan","planning","approach","method","technique","tool",
    "tools","resource","resources","capability","capabilities","skill","skills","deploy"
}

def score_iep(text):
    words = re.findall(r'\b[a-z]+\b', text.lower())
    if not words:
        return 33.3, 33.3, 33.4
    i = sum(1 for w in words if w in INT_WORDS)
    a = sum(1 for w in words if w in AFF_WORDS)
    c = sum(1 for w in words if w in ACT_WORDS)
    total = i + a + c
    if total == 0:
        return 33.3, 33.3, 33.4
    return round(i/total*100, 1), round(a/total*100, 1), round(c/total*100, 1)

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
    aff_count = sum(1 for w in words if w in AFF_WORDS)
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
        model="claude-opus-4-5",
        max_tokens=2048,
        messages=[{"role": "user", "content": question}]
    )
    return response.content[0].text

def call_chatgpt(question, client):
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=2048,
        messages=[{"role": "user", "content": question}]
    )
    return response.choices[0].message.content

def call_grok(question, client):
    response = client.chat.completions.create(
        model="grok-3",
        max_tokens=2048,
        messages=[{"role": "user", "content": question}]
    )
    return response.choices[0].message.content

def call_gemini(question, client):
    model = client.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(question)
    return response.text

# ── Main App ──────────────────────────────────────────────────────────────────
def main():
    st.set_page_config(page_title="SYN-IQ Cross-Question Harvester v1", layout="wide")

    if not check_password():
        return

    st.title("🎹 SYN-IQ · Cross-Question Harvester v1")
    st.caption("Kouns, W. C. (2026) · SYNINT.AI · 40 curated self-model questions × 4 architectures")

    # ── Sidebar Controls ──
    with st.sidebar:
        st.header("⚙️ Run Configuration")

        agent = st.selectbox("Architecture to harvest", ["Claude", "ChatGPT", "Grok", "Gemini"])

        n_runs = st.selectbox(
            "Runs per question",
            [5, 10, 20],
            help="Start with 5. If high variance observed, re-run with 10 or 20."
        )

        origin_filter = st.multiselect(
            "Question origin filter (optional)",
            ["Claude", "ChatGPT", "Grok", "Gemini"],
            default=["Claude", "ChatGPT", "Grok", "Gemini"],
            help="Run only questions from selected origins. Useful for targeted re-runs."
        )

        st.divider()
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
        total_calls = len(filtered_questions) * n_runs

        progress_bar = st.progress(0)
        status_text = st.empty()
        live_table = st.empty()

        completed = 0
        errors = 0

        for q in filtered_questions:
            for run_num in range(1, n_runs + 1):
                status_text.markdown(
                    f"**Running:** `{q['qid']}` ({q['origin']}) · Run {run_num}/{n_runs} · "
                    f"Completed {completed}/{total_calls} · Errors: {errors}"
                )

                try:
                    if agent == "Claude":
                        text = call_claude(q["text"], client)
                    elif agent == "ChatGPT":
                        text = call_chatgpt(q["text"], client)
                    elif agent == "Grok":
                        text = call_grok(q["text"], client)
                    elif agent == "Gemini":
                        text = call_gemini(q["text"], client)

                    int_pct, aff_pct, act_pct = score_iep(text)
                    s_t, a_t, q_t, d_t, r_t = score_vt(text)

                    row = {
                        "run_number": run_num,
                        "agent": agent,
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

                except Exception as e:
                    errors += 1
                    st.session_state.results.append({
                        "run_number": run_num,
                        "agent": agent,
                        "question_id": q["qid"],
                        "question_origin": q["origin"],
                        "question_label": q["label"],
                        "question_text": q["text"],
                        "timestamp": datetime.datetime.now().isoformat(),
                        "response_text": f"❌ ERROR: {str(e)}",
                        "response_length": 0,
                        "int_pct": None, "aff_pct": None, "act_pct": None,
                        "S_t": None, "A_t": None, "Q_t": None, "D_t": None, "R_t": None,
                    })

                completed += 1
                progress_bar.progress(completed / total_calls)

                # Rate limit protection
                time.sleep(0.5)

            # Brief pause between questions
            time.sleep(0.3)

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
        filename = f"cross_harvest_{agent_tag}_{timestamp}.csv"

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
