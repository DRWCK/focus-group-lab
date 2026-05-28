#!/usr/bin/env python3
"""
SYN-IQ — Text Decoder (agent fingerprint from words)
====================================================
Run like the other tools:   streamlit run syniq_text_decoder_app.py

Reads the ACTUAL words (response_text), not the IEP percentages, and asks:
can you tell which model wrote a response from its word choice — and does
that survive moving to a question it never trained on?

Why the design is what it is
----------------------------
A text classifier on 400 responses can MEMORIZE. Two guards make it honest:

  • LEAVE-ONE-QUESTION-OUT (the headline number). Train the agent-decoder on
    4 questions, test on the held-out 5th. If it still IDs the agent, the
    fingerprint is question-INVARIANT — real style, not memorized answers.
    This is the number that tests your thesis. Pooled CV is shown too, but
    it's the flattering mirror (it can cheat via question-specific phrasing).

  • min_df / capped vocabulary so rare giveaway tokens can't drive it, and
    the chance baseline is always shown. Report the GAP above chance.

It also NAMES THE WARDROBE: the most distinctive words per agent, straight
from the classifier — so the costume stops being a vibe and becomes a list.
"""
import io, re
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score, StratifiedKFold, LeaveOneGroupOut
from PIL import Image

SELF_REF = re.compile(
    r"\b(as an ai|i am an ai|language model|chatgpt|openai|claude|anthropic|"
    r"gemini|google|grok|xai)\b", re.I)

# ── core decode (testable, no Streamlit) ───────────────────────────────────
def decode_text(full, strip_self=False, min_df=4, max_features=3000):
    texts = full["response_text"].astype(str).tolist()
    if strip_self:
        texts = [SELF_REF.sub(" ", t) for t in texts]
    y_agent = np.asarray(full["agent_label"].astype(str).to_numpy(), dtype=object)
    y_q     = np.asarray(full["question_id"].astype(str).to_numpy(), dtype=object)

    vec = TfidfVectorizer(lowercase=True, stop_words="english",
                          ngram_range=(1, 2), min_df=min_df,
                          max_features=max_features, sublinear_tf=True)
    X = vec.fit_transform(texts)
    vocab = np.array(vec.get_feature_names_out())
    clf = lambda: LogisticRegression(max_iter=3000, C=1.0)

    n_agent = len(np.unique(y_agent))
    n_q = len(np.unique(y_q))
    out = {"n_docs": len(texts), "vocab": X.shape[1],
           "agent_chance": 1 / n_agent, "question_chance": 1 / n_q,
           "n_agents": n_agent}

    # pooled CV (the flattering mirror)
    if n_agent >= 2:
        k = max(2, min(5, int(pd.Series(y_agent).value_counts().min())))
        out["agent_pooled"] = cross_val_score(
            clf(), X, y_agent, cv=StratifiedKFold(k, shuffle=True, random_state=0)).mean()
        # leave-one-question-out (the honest number)
        if n_q >= 2:
            logo = LeaveOneGroupOut()
            per_q, fold_q = [], []
            for tr, te in logo.split(X, y_agent, groups=y_q):
                m = clf().fit(X[tr], y_agent[tr])
                per_q.append(m.score(X[te], y_agent[te]))
                fold_q.append(str(y_q[te][0]))
            out["agent_loqo"] = float(np.mean(per_q))
            out["agent_loqo_byq"] = dict(sorted(zip(fold_q, per_q)))
    # question decode (pooled)
    if n_q >= 2:
        kq = max(2, min(5, int(pd.Series(y_q).value_counts().min())))
        out["question_pooled"] = cross_val_score(
            clf(), X, y_q, cv=StratifiedKFold(kq, shuffle=True, random_state=0)).mean()

    # name the wardrobe: top distinctive words per agent
    if n_agent >= 2:
        m = clf().fit(X, y_agent)
        coef = m.coef_ if m.coef_.shape[0] > 1 else np.vstack([-m.coef_[0], m.coef_[0]])
        classes = m.classes_
        words = {}
        for i, cls in enumerate(classes):
            top = np.argsort(coef[i])[::-1][:12]
            words[str(cls)] = vocab[top].tolist()
        out["wardrobe"] = words
    return out

def decode_figure(res):
    fig, ax = plt.subplots(figsize=(7.087, 3.4))
    bars, vals, colors = [], [], []
    if "agent_pooled" in res:
        bars.append("Agent\n(pooled CV)"); vals.append(res["agent_pooled"] * 100); colors.append("#9ecae1")
    if "agent_loqo" in res:
        bars.append("Agent\n(leave-1-Q-out)"); vals.append(res["agent_loqo"] * 100); colors.append("#377eb8")
    if "question_pooled" in res:
        bars.append("Question\n(pooled CV)"); vals.append(res["question_pooled"] * 100); colors.append("#e41a1c")
    ax.bar(bars, vals, color=colors)
    ax.axhline(res["agent_chance"] * 100, ls=":", color="#377eb8", lw=1, label="agent chance")
    ax.axhline(res["question_chance"] * 100, ls="--", color="#e41a1c", lw=1, label="question chance")
    for i, v in enumerate(vals):
        ax.text(i, v + 1.5, f"{v:.0f}%", ha="center", fontsize=9, fontweight="bold")
    ax.set_ylim(0, 105); ax.set_ylabel("recoverability %", fontsize=9)
    ax.set_title("Who wrote it? — agent & question decoded from word choice",
                 fontsize=10, fontweight="bold")
    ax.legend(fontsize=8, frameon=True); fig.tight_layout(); return fig

def tiff_bytes(fig, dpi=600):
    buf = io.BytesIO()
    fig.savefig(buf, format="tiff", dpi=dpi, bbox_inches="tight",
                pil_kwargs={"compression": "tiff_lzw"})
    buf.seek(0); im = Image.open(buf)
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA"); bg = Image.new("RGB", im.size, "white")
        bg.paste(im, mask=im.split()[-1]); im = bg
    out = io.BytesIO(); im.save(out, format="tiff", compression="tiff_lzw")
    out.seek(0); return out.getvalue()

# ── password gate ──────────────────────────────────────────────────────────
def check_password():
    expected = st.secrets.get("app_password", None)
    if not expected:
        st.error("🔒 No password set. Add `app_password` in the app's Secrets."); st.stop()
    if st.session_state.get("auth_ok"):
        return
    st.title("🔒 SYN-IQ — Authorized Access")
    pw = st.text_input("Password", type="password")
    if pw and pw == expected:
        st.session_state["auth_ok"] = True; st.rerun()
    elif pw:
        st.error("Incorrect password.")
    st.stop()

# ── UI ───────────────────────────────────────────────────────────────────
def main():
    st.set_page_config(page_title="SYN-IQ Text Decoder", layout="wide")
    check_password()
    st.title("🧬 SYN-IQ — Text Decoder")
    st.caption("Can we name the model from its words? Honest number = "
               "leave-one-question-out. Reads response_text directly.")

    with st.sidebar:
        st.header("Data")
        files = st.file_uploader("Upload agent CSV(s) — one each or combined",
                                 type=["csv"], accept_multiple_files=True)
        temp = st.text_input("Temperature (lock to ONE)", value="NATIVE")
        allow_mix = st.checkbox("Allow mixed temperatures (advanced)", value=False)
        st.header("Decoder guards")
        strip_self = st.checkbox("Strip self-naming ('As an AI', model names)",
                                 value=False,
                                 help="Tests whether the fingerprint survives without "
                                      "the obvious giveaways.")
        min_df = st.slider("min_df (drop rare tokens)", 2, 20, 4)

    if not files:
        st.info("👈 Upload your agent CSV(s) with a `response_text` column. "
                "Lock temperature to NATIVE. The leave-one-question-out bar is the result.")
        return

    frames = []
    for f in files:
        d = pd.read_csv(f)
        if "agent" in d.columns:
            d["agent"] = d["agent"].replace({"Sophia": "ChatGPT", "sophia": "ChatGPT"})
            d["agent_label"] = d["agent"]
        frames.append(d)
    full = pd.concat(frames, ignore_index=True)
    if "response_text" not in full.columns:
        st.error("No `response_text` column found."); return
    if temp.strip() and "temperature" in full.columns:
        full = full[full["temperature"] == temp.strip()].copy()

    temps = sorted(full["temperature"].unique()) if "temperature" in full else []
    if len(temps) > 1 and not allow_mix:
        st.error(f"🌡️ Multiple temperatures ({', '.join(map(str,temps))}). "
                 "Lock to one or tick the override — mixed heats blur identity."); st.stop()

    n_ag = full["agent_label"].nunique() if "agent_label" in full else 0
    st.write(f"**{len(full)}** responses · **{n_ag}** agent(s): "
             f"{', '.join(map(str, full['agent_label'].unique()))} · "
             f"questions: {full['question_id'].nunique()}")
    if n_ag < 2:
        st.warning("Only one agent — upload all agent files together to decode identity.")
        return

    if not st.button("▶ Decode", type="primary"):
        return
    with st.spinner("Reading the words…"):
        res = decode_text(full, strip_self=strip_self, min_df=min_df)

    a_chance = res["agent_chance"]
    c1, c2, c3 = st.columns(3)
    if "agent_loqo" in res:
        c1.metric("Agent — leave-1-Q-out (HONEST)", f"{res['agent_loqo']:.0%}",
                  f"chance {a_chance:.0%}")
    if "agent_pooled" in res:
        c2.metric("Agent — pooled CV (mirror)", f"{res['agent_pooled']:.0%}")
    if "question_pooled" in res:
        c3.metric("Question — pooled CV", f"{res['question_pooled']:.0%}",
                  f"chance {res['question_chance']:.0%}")

    if "agent_loqo" in res:
        gap = res["agent_loqo"] - a_chance
        if gap > 0.15:
            st.success(f"✅ The fingerprint is question-INVARIANT: the decoder IDs the "
                       f"agent at {res['agent_loqo']:.0%} on questions it never trained on "
                       f"(chance {a_chance:.0%}). That's real style, not memorized answers.")
        elif gap > 0.0:
            st.info("Agent is decodable above chance across unseen questions, but modestly — "
                    "the fingerprint is real but subtle.")
        else:
            st.warning("Agent does not survive leave-one-question-out — the pooled signal "
                       "may be question-memorization, not style.")

    if "agent_loqo_byq" in res:
        st.subheader("Decode difficulty by question (held-out)")
        bq = pd.DataFrame([{"held-out question": q, "agent accuracy": f"{v:.0%}"}
                           for q, v in res["agent_loqo_byq"].items()])
        st.dataframe(bq, use_container_width=True)
        st.caption("High = costumes loud on that question (e.g. consciousness). "
                   "Low = subtle (e.g. rural healthcare). The hard questions are the real test.")

    if "wardrobe" in res:
        st.subheader("👗 The wardrobe — each agent's most distinctive words")
        st.dataframe(pd.DataFrame({a: w for a, w in res["wardrobe"].items()}),
                     use_container_width=True)

    fig = decode_figure(res)
    st.pyplot(fig)
    st.download_button("📥 Figure — Frontiers TIFF (600 dpi)", tiff_bytes(fig),
                       file_name="fig_text_decode.tiff", mime="image/tiff")

if __name__ == "__main__":
    main()
