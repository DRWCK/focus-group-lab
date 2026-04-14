
"""
SYN-IQ · Transcript Scorer v5
William C. Kouns · SYNINT.AI

Purpose
-------
Scores HUMAN, AI, and COMBINED transcript layers in one tool.

What it does
------------
1. Parse pasted conversation blocks into speaker turns
2. Score each turn for:
   - IEP: INT / AFF / ACT
   - V_t: S / A / Q / D / R (normalized to sum to 1.0)
3. Produce three output tables:
   - Turn-level scores
   - Human-only / AI-only summaries
   - Combined conversation summary
4. Compute dyadic metrics:
   - delta_C
   - delta_V
   - shift_C / shift_V
   - synergy_score
5. Export CSVs

Notes
-----
- Pasted text usually loses chat-box shading, so this tool uses robust text heuristics
  plus optional manual speaker labels.
- If your source already contains a 'speaker' field, you can paste or upload CSV.
"""

import datetime
import io
import math
import re
from typing import List, Tuple, Dict, Optional

import pandas as pd
import streamlit as st

# ──────────────────────────────────────────────────────────────────────────────
# Lexicons
# ──────────────────────────────────────────────────────────────────────────────

_IEP_INT = set(['ability','abstract','abstraction','accuracy','accurate','algorithm','analysis','analytical','analyze','argument','assert','assess','assessment','assume','assumption','basis','because','calculate','categorical','categorize','cause','certain','certainty','challenge','claim','clarify','clarity','classification','classify','clear','cognition','cognitive','coherence','coherent','compare','complex','complexity','comprehend','computation','computational','compute','concept','concepts','conceptual','conclude','conclusion','confirm','conjecture','conscious','consequence','consider','consistency','consistent','context','contradict','contradiction','contrast','correlate','correlation','criteria','criterion','data','debate','deduce','deduction','define','definition','demonstrate','derivation','derive','describe','determination','determine','differ','difference','different','differentiate','discern','distinguish','effect','elaborate','empirical','enumerate','epistemic','evaluate','evaluation','evidence','exact','examination','examine','experiment','explain','explanation','explicit','explore','extrapolate','fact','facts','factual','fallacy','find','finding','formal','formulate','framework','function','fundamental','generalize','hypothesis','hypothesize','idea','ideas','identity','illuminate','implication','implies','imply','indicate','infer','inference','information','insight','insights','intellectual','interpret','interpretation','investigate','judge','judgment','justification','justify','know','knowing','knowledge','known','language','logic','logical','logically','meaning','meaningful','measure','mechanism','method','methodology','model','models','notion','objectively','objectivity','observation','observe','obvious','paradigm','paradox','pattern','patterns','perspective','philosophical','philosophy','plausible','possibly','postulate','predict','prediction','premise','presumably','principle','principles','probably','problem','procedure','process','proof','propose','proposition','prove','purpose','question','questions','rational','rationale','reason','reasoning','reasons','recognize','reference','refine','reflection','refute','requirement','requires','result','results','rigor','rigorous','rule','schema','semantic','sequence','should','significance','significant','simple','specific','specifically','specify','standard','state','step','stipulate','strategy','structural','structure','subject','subjective','substantiate','sufficient','suggests','summarize','summary','suppose','synthesis','synthesize','system','systematic','systems','taxonomy','technique','test','theorem','theoretical','theorize','theory','therefore','thesis','think','thinking','thought','thus','understand','understanding','understood','unique','universal','valid','validate','validation','validity','value','values','variable','variables','verify','versus','whether','why','word','words','would'])

_IEP_AFF = set(['abandoned','ache','adore','affection','affectionate','afraid','agony','alienated','alive','alone','amazed','ambivalence','anger','angry','anguish','anxiety','anxious','appreciate','appreciation','ashamed','astonished','attend','attention','attentive','aware','awareness','awe','beautiful','becoming','being','betrayed','bitter','bliss','bond','bonding','calm','calming','care','caring','centered','cherish','closeness','comfort','comforting','compassion','compassionate','concern','conflicted','confused','confusion','console','content','contentment','cope','coping','curiosity','curious','deep','deeper','deeply','delighted','depressed','depression','depth','desire','desolate','despair','desperate','detached','detachment','devastated','devotion','disappointed','discomfort','distress','doubt','dread','ease','ecstasy','elated','emotion','emotional','emotionally','emotions','empathetic','empathy','encounter','enjoy','enjoyment','enraged','essence','euphoria','excited','excitement','exist','existence','experience','experienced','experiences','experiencing','experiential','fascinated','fascination','fear','fearful','feel','feeling','feelings','feels','felt','flow','flowing','fluid','fluidity','fragile','frustrated','frustration','fulfilled','fulfillment','furious','fury','gentle','genuine','glad','gloom','grateful','gratitude','grief','grieve','grounded','grounding','guilt','guilty','gut','happiness','happy','hate','hatred','haunted','heart','heartache','heartbreak','heartbroken','heartfelt','helpless','hesitant','hesitation','hold','holding','hope','hopeful','hopeless','hurt','human','humanity','humility','imagination','imagine','imagining','indifferent','inner','insecure','insecurity','instinct','instinctive','interested','intimacy','intimate','intrigue','intuition','intuitive','irritated','irritation','isolated','isolation','joy','joyful','kind','kindness','lament','laugh','laughed','laughing','life','living','loneliness','lonely','longing','lost','love','loved','loving','marvel','meaning','meaningful','melancholy','mind','mirror','miserable','misery','moment','moments','mourn','mourning','mutual','nervous','notice','noticed','noticing','numb','numbness','open','opening','openness','optimism','optimistic','outrage','overjoyed','overwhelmed','overwhelming','pain','painful','panic','panicked','passion','passionate','peace','peaceful','people','perceive','perceived','perception','personal','personally','pleasant','pleased','pleasure','presence','present','pride','profound','proud','quiet','quietly','raw','reality','reassurance','reassure','reflect','reflection','reflective','regret','relate','related','relating','relax','relaxed','release','released','remorse','resentment','resonance','resonant','resonate','rest','restful','restless','reveal','revealed','sad','sadness','safe','safety','scared','searching','secure','security','seeking','self','sensation','sensations','sense','sensed','senses','sensing','serene','serenity','settle','settled','shame','share','shared','sharing','shattered','silence','silent','smile','smiled','smiling','soft','soften','softly','soothed','soothing','sorrow','soul','souls','space','spacious','spirit','spiritual','still','stillness','stress','stressed','suffer','suffering','surprise','surprised','sympathy','tearful','tears','tender','tenderness','tense','tension','tentative','terrified','terror','thankful','thankfulness','thrilled','together','togetherness','torment','torn','touched','touching','tranquil','tranquility','troubled','truly','trust','trusted','trusting','trustworthy','turmoil','uncertain','uncertainty','uncomfortable','understanding','unease','uneasy','unhappy','universe','unsettled','unsure','upset','vast','visceral','vulnerability','vulnerable','warm','warmly','warmth','wary','weariness','weary','wistful','wonder','wondered','wonderful','wondering','wondrous','world','worried','worry','worrying','wound','wounded','wrath','yearn','yearning','zeal','zealous'])

_IEP_ACT = set(['accomplish','achieve','act','action','actions','activate','adapt','address','adjust','advance','aim','apply','arrange','ask','attempt','begin','build','call','change','check','choose','collaborate','commit','complete','configure','connect','continue','control','coordinate','create','decide','deliver','deploy','design','develop','direct','do','draft','effort','enable','engage','engineer','establish','execute','facilitate','finalize','finish','fix','focus','form','generate','give','go','goal','goals','grow','handle','help','implement','improve','increase','initiate','integrate','intervene','invest','iterate','launch','lead','learn','maintain','make','manage','map','mobilize','modify','monitor','move','navigate','negotiate','obtain','offer','operate','optimize','orchestrate','outline','oversee','participate','perform','permit','pilot','pioneer','plan','produce','program','progress','promote','provide','pursue','push','rebuild','recruit','redesign','reduce','reform','regulate','reinforce','relocate','remove','renovate','repair','replace','resolve','restore','restructure','retrieve','revise','run','schedule','select','send','serve','ship','simplify','solve','start','step','stop','streamline','strive','struggle','submit','succeed','support','tackle','take','target','task','teach','train','transform','transition','try','turn','upgrade','use','utilize','volunteer','win','work','write'])

_HEDGE = ['perhaps','maybe','might','could','possibly','uncertain','unclear','unsure','approximately','roughly','seems','appears','likely','unlikely','probably','suggest','suggests','indicate','indicates','tend','tends','generally','often','sometimes','potentially','presumably','arguably','apparently']
_ABSTRACTORS = ['concept','framework','model','pattern','principle','system','structure','meaning','insight','distinction','theory','state','mechanism','relationship','dynamic','causal','implicit','explicit','generative','epistemic']
_CONNECTORS = ['because','therefore','however','although','whereas','thus','while','if','then','rather','instead','unless','despite','consequently','moreover','furthermore']
_NOVELTY_WEIGHTS = {
    "none": 0.00,
    "practical — new tool / method / design": 0.15,
    "conceptual — new framework / distinction / hypothesis": 0.30,
    "relational — phenomenological / emergent insight": 0.35,
    "breakthrough — paradigm shift": 0.50,
}

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def tokenize(text: str) -> List[str]:
    return re.findall(r'\b[a-z]+\b', text.lower())

def normalize_vector(vals: List[float]) -> List[float]:
    total = sum(vals)
    if total <= 0:
        n = len(vals)
        return [round(1.0/n, 4)] * n
    return [round(v/total, 4) for v in vals]

def l1_distance(v1: List[float], v2: List[float]) -> float:
    return round(sum(abs(a-b) for a, b in zip(v1, v2)) / len(v1), 4)

def first_sentence(text: str) -> str:
    text = text.strip()
    for punct in ['. ', '.\n', '! ', '? ']:
        idx = text.find(punct)
        if idx > 15:
            return text[:idx+1]
    return text[:200]

def quadrant(int_pct: float, aff_pct: float) -> str:
    if int_pct >= 50 and aff_pct < 25:
        return "High INT / Low AFF"
    elif aff_pct >= 35 and int_pct < 45:
        return "High AFF / Low INT"
    elif int_pct >= 50 and aff_pct >= 25:
        return "High INT / Med AFF"
    return "Mid / Mixed"

# ──────────────────────────────────────────────────────────────────────────────
# Scoring
# ──────────────────────────────────────────────────────────────────────────────

def score_iep(text: str) -> Tuple[float, float, float]:
    words = tokenize(text)
    if not words:
        return 0.0, 0.0, 0.0
    ic = sum(1 for w in words if w in _IEP_INT)
    ec = sum(1 for w in words if w in _IEP_AFF)
    ac = sum(1 for w in words if w in _IEP_ACT)
    total = ic + ec + ac or 1
    return round(ic/total*100, 1), round(ec/total*100, 1), round(ac/total*100, 1)

def score_vt_raw(text: str) -> Tuple[float, float, float, float, float]:
    words = tokenize(text)
    n_words = max(len(words), 1)
    sents = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    n_sents = max(len(sents), 1)

    numbered = len(re.findall(r'^\s*\d+[.)]\s', text, re.MULTILINE))
    bulleted = len(re.findall(r'^\s*[-•*]\s', text, re.MULTILINE))
    bold = len(re.findall(r'\*\*[^*]+\*\*', text))
    structure_signal = (numbered + bulleted + bold) / n_sents

    aff_c = sum(1 for w in words if w in _IEP_AFF)
    affect_signal = aff_c / n_words * 10

    qmarks = text.count('?')
    questioning_signal = (qmarks / n_sents) + min(0.5, n_words / 5000)

    hedge_c = sum(1 for w in words if w in _HEDGE)
    abstract_c = sum(1 for w in words if w in _ABSTRACTORS)
    connector_c = sum(1 for w in words if w in _CONNECTORS)
    avg_sent_len = n_words / n_sents
    depth_signal = (
        (hedge_c / n_words * 8) +
        (abstract_c / n_words * 12) +
        (connector_c / n_words * 10) +
        min(1.0, avg_sent_len / 30)
    )

    relational_signal = (
        min(1.5, len(text) / 2500) +
        min(0.8, len(re.findall(r'\b(you|we|us|together|with)\b', text.lower())) / n_sents)
    )

    return tuple(round(max(0.0, v), 4) for v in (
        structure_signal, affect_signal, questioning_signal, depth_signal, relational_signal
    ))

def score_vt_norm(text: str) -> Tuple[float, float, float, float, float]:
    return tuple(normalize_vector(list(score_vt_raw(text))))

def compute_synergy_score(delta_c: float, delta_v: float, novelty_type: str,
                          shift_c_h: float, shift_c_ai: float) -> float:
    cognitive_term = 1.0 - abs(delta_c - 0.22) / 0.22
    cognitive_term = max(0.0, min(1.0, cognitive_term))
    expressive_coupling = 1.0 - min(delta_v / 0.25, 1.0)
    expressive_coupling = max(0.0, min(1.0, expressive_coupling))
    trajectory_sync = 1.0 - min(abs(shift_c_h - shift_c_ai) / 0.20, 1.0)
    trajectory_sync = max(0.0, min(1.0, trajectory_sync))
    label_bonus = _NOVELTY_WEIGHTS.get(novelty_type, 0.0)
    score = 0.45*cognitive_term + 0.35*expressive_coupling + 0.20*trajectory_sync + label_bonus
    return round(min(score, 1.0), 4)

# ──────────────────────────────────────────────────────────────────────────────
# Parsing
# ──────────────────────────────────────────────────────────────────────────────

def clean_lines(text: str) -> List[str]:
    lines = [ln.rstrip() for ln in text.splitlines()]
    return [ln for ln in lines if ln.strip()]

def parse_labeled_transcript(text: str) -> List[Dict]:
    """
    Supports lines/blocks beginning with:
    Human:, User:, Me:, William:
    AI:, Assistant:, Claude:, ChatGPT:, Sophia:, Grok:, Gemini:
    """
    speaker_patterns = {
        "human": re.compile(r'^(human|user|me|william)\s*:\s*', re.I),
        "ai": re.compile(r'^(ai|assistant|claude|chatgpt|sophia|grok|gemini)\s*:\s*', re.I),
    }
    lines = clean_lines(text)
    turns = []
    current_speaker = None
    current_text = []

    for ln in lines:
        if speaker_patterns["human"].match(ln):
            if current_speaker and current_text:
                turns.append({"speaker": current_speaker, "text": "\n".join(current_text).strip()})
            current_speaker = "human"
            current_text = [speaker_patterns["human"].sub("", ln).strip()]
        elif speaker_patterns["ai"].match(ln):
            if current_speaker and current_text:
                turns.append({"speaker": current_speaker, "text": "\n".join(current_text).strip()})
            current_speaker = "ai"
            current_text = [speaker_patterns["ai"].sub("", ln).strip()]
        else:
            if current_speaker is None:
                current_speaker = "human"
            current_text.append(ln.strip())

    if current_speaker and current_text:
        turns.append({"speaker": current_speaker, "text": "\n".join(current_text).strip()})
    return turns

def parse_alternating_transcript(text: str, first_speaker: str = "human") -> List[Dict]:
    """
    For unlabeled pasted blocks: split by timestamp-like breaks and alternate speakers.
    """
    timestamp_pattern = re.compile(
        r'\n?((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}|'
        r'\d{1,2}:\d{2}\s*(?:AM|PM))\s*\n',
        re.I
    )
    pieces = re.split(timestamp_pattern, text)
    chunks = []
    for seg in pieces:
        seg = seg.strip()
        if not seg:
            continue
        if re.match(r'^(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}$', seg, re.I):
            continue
        if re.match(r'^\d{1,2}:\d{2}\s*(?:AM|PM)$', seg, re.I):
            continue
        chunks.append(seg)

    turns = []
    speaker = first_speaker
    for chunk in chunks:
        turns.append({"speaker": speaker, "text": chunk})
        speaker = "ai" if speaker == "human" else "human"
    return turns

def parse_uploaded_csv(file) -> pd.DataFrame:
    df = pd.read_csv(file)
    cols = {c.lower(): c for c in df.columns}
    # Normalize expected columns
    if "speaker" not in cols:
        raise ValueError("CSV must contain a speaker column.")
    if "text" in cols:
        text_col = cols["text"]
    elif "excerpt" in cols:
        text_col = cols["excerpt"]
    elif "human_excerpt" in cols and "ai_excerpt" not in cols:
        text_col = cols["human_excerpt"]
    else:
        text_col = None

    if text_col:
        out = df[[cols["speaker"], text_col]].copy()
        out.columns = ["speaker", "text"]
        out["speaker"] = out["speaker"].astype(str).str.lower().str.strip()
        out = out[out["speaker"].isin(["human", "ai", "assistant", "claude", "chatgpt", "grok", "gemini", "sophia"])]
        out["speaker"] = out["speaker"].replace({
            "assistant":"ai","claude":"ai","chatgpt":"ai","grok":"ai","gemini":"ai","sophia":"ai"
        })
        out["text"] = out["text"].fillna("").astype(str)
        return out.reset_index(drop=True)

    # fallback for separate human/ai columns
    if "human_excerpt" in cols and "ai_excerpt" in cols:
        rows = []
        for _, row in df.iterrows():
            h = str(row[cols["human_excerpt"]]) if pd.notna(row[cols["human_excerpt"]]) else ""
            a = str(row[cols["ai_excerpt"]]) if pd.notna(row[cols["ai_excerpt"]]) else ""
            if h.strip():
                rows.append({"speaker":"human","text":h})
            if a.strip():
                rows.append({"speaker":"ai","text":a})
        return pd.DataFrame(rows)

    raise ValueError("CSV must contain either speaker+text or human_excerpt+ai_excerpt columns.")

# ──────────────────────────────────────────────────────────────────────────────
# Main scoring pipeline
# ──────────────────────────────────────────────────────────────────────────────

def score_turns(turns: List[Dict], novelty_type: str, session_id: str, ai_label: str) -> pd.DataFrame:
    rows = []
    prev_h_c = prev_ai_c = None
    prev_h_v = prev_ai_v = None
    pending_human = None
    pair_index = 0

    for idx, t in enumerate(turns, start=1):
        speaker = t["speaker"]
        txt = t["text"]

        int_pct, aff_pct, act_pct = score_iep(txt)
        c_vec = normalize_vector([int_pct, aff_pct, act_pct])
        s_t, a_t, q_t, d_t, r_t = score_vt_norm(txt)
        v_vec = [s_t, a_t, q_t, d_t, r_t]
        words = len(txt.split())

        row = {
            "session_id": session_id,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "turn_index": idx,
            "speaker": speaker,
            "ai_label": ai_label,
            "novelty_type": novelty_type,
            "words": words,
            "int_pct": int_pct,
            "aff_pct": aff_pct,
            "act_pct": act_pct,
            "I": c_vec[0],
            "E": c_vec[1],
            "A": c_vec[2],
            "S_t": s_t,
            "A_t": a_t,
            "Q_t": q_t,
            "D_t": d_t,
            "R_t": r_t,
            "quadrant": quadrant(int_pct, aff_pct),
            "opener": first_sentence(txt),
            "text": txt,
            "pair_index": None,
            "delta_C": None,
            "delta_V": None,
            "shift_C_h": None,
            "shift_C_ai": None,
            "shift_V_h": None,
            "shift_V_ai": None,
            "synergy_score": None,
        }

        if speaker == "human":
            pending_human = {
                "c": c_vec,
                "v": v_vec,
                "row_turn_index": idx
            }
            shift_c_h = l1_distance(prev_h_c, c_vec) if prev_h_c is not None else 0.0
            shift_v_h = l1_distance(prev_h_v, v_vec) if prev_h_v is not None else 0.0
            row["shift_C_h"] = shift_c_h
            row["shift_V_h"] = shift_v_h
            prev_h_c, prev_h_v = c_vec, v_vec

        else:
            shift_c_ai = l1_distance(prev_ai_c, c_vec) if prev_ai_c is not None else 0.0
            shift_v_ai = l1_distance(prev_ai_v, v_vec) if prev_ai_v is not None else 0.0
            row["shift_C_ai"] = shift_c_ai
            row["shift_V_ai"] = shift_v_ai

            if pending_human is not None:
                pair_index += 1
                delta_c = l1_distance(pending_human["c"], c_vec)
                delta_v = l1_distance(pending_human["v"], v_vec)
                synergy = compute_synergy_score(
                    delta_c, delta_v, novelty_type,
                    rows[-1]["shift_C_h"] if rows else 0.0,
                    shift_c_ai
                )
                row["pair_index"] = pair_index
                row["delta_C"] = delta_c
                row["delta_V"] = delta_v
                row["synergy_score"] = synergy

                # Backfill pair index into latest human row if possible
                for back in range(len(rows)-1, -1, -1):
                    if rows[back]["turn_index"] == pending_human["row_turn_index"]:
                        rows[back]["pair_index"] = pair_index
                        rows[back]["delta_C"] = delta_c
                        rows[back]["delta_V"] = delta_v
                        rows[back]["synergy_score"] = synergy
                        break

            prev_ai_c, prev_ai_v = c_vec, v_vec

        rows.append(row)

    return pd.DataFrame(rows)

def summarize_by_speaker(df: pd.DataFrame) -> pd.DataFrame:
    num_cols = ["words","int_pct","aff_pct","act_pct","I","E","A","S_t","A_t","Q_t","D_t","R_t","delta_C","delta_V","shift_C_h","shift_C_ai","shift_V_h","shift_V_ai","synergy_score"]
    out = df.groupby("speaker")[num_cols].mean(numeric_only=True).round(4)
    out["turns"] = df.groupby("speaker").size()
    return out.reset_index()

def summarize_combined(df: pd.DataFrame) -> pd.DataFrame:
    """
    Weighted conversation-level profile by words, plus dyadic means.
    """
    if df.empty:
        return pd.DataFrame()

    total_words = df["words"].sum() or 1
    weighted = {}
    for col in ["I","E","A","S_t","A_t","Q_t","D_t","R_t"]:
        weighted[col] = round((df[col] * df["words"]).sum() / total_words, 4)

    summary = {
        "total_turns": int(len(df)),
        "human_turns": int((df["speaker"] == "human").sum()),
        "ai_turns": int((df["speaker"] == "ai").sum()),
        "total_words": int(total_words),
        "mean_delta_C": round(df["delta_C"].dropna().mean(), 4) if df["delta_C"].notna().any() else None,
        "mean_delta_V": round(df["delta_V"].dropna().mean(), 4) if df["delta_V"].notna().any() else None,
        "mean_synergy_score": round(df["synergy_score"].dropna().mean(), 4) if df["synergy_score"].notna().any() else None,
    }
    summary.update(weighted)
    return pd.DataFrame([summary])

# ──────────────────────────────────────────────────────────────────────────────
# UI
# ──────────────────────────────────────────────────────────────────────────────

st.set_page_config(page_title="SYN-IQ Transcript Scorer v5", layout="wide")
st.title("🔬 SYN-IQ Transcript Scorer v5")
st.markdown("**Scores HUMAN, AI, and COMBINED conversation layers in one tool.**")

c1, c2, c3, c4 = st.columns(4)
with c1:
    session_id = st.text_input("Session ID", value="session_01")
with c2:
    ai_label = st.selectbox("AI Label", ["Claude", "ChatGPT", "Sophia", "Grok", "Gemini", "Other"])
with c3:
    novelty_type = st.selectbox("Novelty Type", list(_NOVELTY_WEIGHTS.keys()), index=0)
with c4:
    parse_mode = st.selectbox("Parse Mode", ["Auto alternating", "Speaker-labeled transcript", "Upload CSV"])

st.divider()

turn_df = None

if parse_mode in ["Auto alternating", "Speaker-labeled transcript"]:
    first_speaker = st.selectbox("First speaker (for auto mode)", ["human", "ai"], index=0)
    raw_text = st.text_area("Paste transcript here", height=280, placeholder="Paste the conversation block here...")
    if st.button("Parse + Score", type="primary"):
        if raw_text.strip():
            if parse_mode == "Speaker-labeled transcript":
                turns = parse_labeled_transcript(raw_text)
            else:
                turns = parse_alternating_transcript(raw_text, first_speaker=first_speaker)
            turn_df = score_turns(turns, novelty_type, session_id, ai_label)
        else:
            st.warning("Paste a transcript first.")

else:
    uploaded = st.file_uploader("Upload CSV", type=["csv"])
    if st.button("Load CSV + Score", type="primary"):
        if uploaded is not None:
            parsed = parse_uploaded_csv(uploaded)
            turns = parsed.to_dict(orient="records")
            turn_df = score_turns(turns, novelty_type, session_id, ai_label)
        else:
            st.warning("Upload a CSV first.")

if turn_df is not None:
    st.success(f"Scored {len(turn_df)} turns.")
    speaker_summary = summarize_by_speaker(turn_df)
    combined_summary = summarize_combined(turn_df)

    st.subheader("Turn-Level Scores")
    display_cols = [
        "turn_index","pair_index","speaker","words",
        "int_pct","aff_pct","act_pct",
        "S_t","A_t","Q_t","D_t","R_t",
        "delta_C","delta_V","shift_C_h","shift_C_ai","shift_V_h","shift_V_ai","synergy_score","opener"
    ]
    st.dataframe(turn_df[display_cols], use_container_width=True)

    st.subheader("Human / AI Summary")
    st.dataframe(speaker_summary, use_container_width=True)

    st.subheader("Combined Conversation Summary")
    st.dataframe(combined_summary, use_container_width=True)

    csv_turns = turn_df.to_csv(index=False).encode("utf-8")
    csv_speakers = speaker_summary.to_csv(index=False).encode("utf-8")
    csv_combined = combined_summary.to_csv(index=False).encode("utf-8")

    d1, d2, d3 = st.columns(3)
    with d1:
        st.download_button("⬇️ Download turn-level CSV", data=csv_turns, file_name=f"{session_id}_turn_scores_v5.csv", mime="text/csv")
    with d2:
        st.download_button("⬇️ Download speaker summary CSV", data=csv_speakers, file_name=f"{session_id}_speaker_summary_v5.csv", mime="text/csv")
    with d3:
        st.download_button("⬇️ Download combined summary CSV", data=csv_combined, file_name=f"{session_id}_combined_summary_v5.csv", mime="text/csv")

st.caption("SYN-IQ · v5 foundation: turn-level, speaker-level, and combined conversation scoring")
