
"""
SYN-IQ · Transcript Scorer v4
Kouns, W. C. (2026) · SYNINT.AI · CBURZBO 🎹

Major upgrades from v3
----------------------
1. Normalized V_t vector so voice-state proportions sum to 1.0
2. Explicit dyadic distances:
   - delta_C : human vs AI center-state distance
   - delta_V : human vs AI voice-state distance
3. Trajectory tracking across turn pairs:
   - shift_C_h, shift_C_ai
   - shift_V_h, shift_V_ai
4. Improved D_t proxy:
   - combines abstraction, concept chaining, hedge density, sentence length
5. First-pass synergy score:
   - rewards cognitive difference with expressive coupling
   - adds bonus for novelty labels and convergent trajectories
6. Cleaner exports for paper analysis

Paste a full conversation block — auto-splits into human/AI turns,
scores IEP + V_t on each side, captures rhythm, exports CSV.
"""

import datetime
import re
from typing import List, Tuple

import pandas as pd
import streamlit as st

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

def tokenize(text: str) -> List[str]:
    return re.findall(r'\b[a-z]+\b', text.lower())

def normalize_vector(vals: List[float]) -> List[float]:
    total = sum(vals)
    if total <= 0:
        n = len(vals)
        return [round(1.0 / n, 4)] * n
    return [round(v / total, 4) for v in vals]

def l1_distance(v1: List[float], v2: List[float]) -> float:
    return round(sum(abs(a - b) for a, b in zip(v1, v2)) / len(v1), 4)

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
    else:
        return "Mid / Mixed"

def score_iep(text: str) -> Tuple[float, float, float]:
    words = tokenize(text)
    if not words:
        return 0.0, 0.0, 0.0
    ic = sum(1 for w in words if w in _IEP_INT)
    ec = sum(1 for w in words if w in _IEP_AFF)
    ac = sum(1 for w in words if w in _IEP_ACT)
    total = ic + ec + ac or 1
    return round(ic / total * 100, 1), round(ec / total * 100, 1), round(ac / total * 100, 1)

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

    return (
        round(max(0.0, structure_signal), 4),
        round(max(0.0, affect_signal), 4),
        round(max(0.0, questioning_signal), 4),
        round(max(0.0, depth_signal), 4),
        round(max(0.0, relational_signal), 4),
    )

def score_vt_normalized(text: str) -> Tuple[float, float, float, float, float]:
    vals = list(score_vt_raw(text))
    normed = normalize_vector(vals)
    return tuple(round(v, 4) for v in normed)

def compute_synergy_score(delta_c: float, delta_v: float, novelty_type: str,
                          shift_c_h: float, shift_c_ai: float) -> float:
    cognitive_term = 1.0 - abs(delta_c - 0.22) / 0.22
    cognitive_term = max(0.0, min(1.0, cognitive_term))

    expressive_coupling = 1.0 - min(delta_v / 0.25, 1.0)
    expressive_coupling = max(0.0, min(1.0, expressive_coupling))

    trajectory_sync = 1.0 - min(abs(shift_c_h - shift_c_ai) / 0.20, 1.0)
    trajectory_sync = max(0.0, min(1.0, trajectory_sync))

    label_bonus = _NOVELTY_WEIGHTS.get(novelty_type, 0.0)

    score = (
        0.45 * cognitive_term +
        0.35 * expressive_coupling +
        0.20 * trajectory_sync +
        label_bonus
    )
    return round(min(score, 1.0), 4)

def parse_conversation(raw_text: str, ai_agent: str = "Claude") -> List[Tuple[str, str]]:
    timestamp_pattern = re.compile(
        r'\n?((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}|'
        r'\d{1,2}:\d{2}\s*(?:AM|PM))\s*\n',
        re.IGNORECASE
    )

    segments = re.split(timestamp_pattern, raw_text)
    turns = []
    for seg in segments:
        seg = seg.strip()
        if not seg:
            continue
        if re.match(r'^(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}$', seg, re.IGNORECASE):
            continue
        if re.match(r'^\d{1,2}:\d{2}\s*(?:AM|PM)$', seg, re.IGNORECASE):
            continue
        turns.append(seg)

    pairs = []
    i = 0
    while i < len(turns):
        turn = turns[i]
        wc = len(turn.split())
        ends_with_piano = '🎹' in turn
        is_short = wc < 40

        if is_short and not ends_with_piano:
            human_turn = turn
            ai_turn = turns[i+1] if i+1 < len(turns) else ""
            pairs.append((human_turn, ai_turn))
            i += 2
        elif ends_with_piano:
            pairs.append(("", turn))
            i += 1
        else:
            if wc < 60:
                human_turn = turn
                ai_turn = turns[i+1] if i+1 < len(turns) else ""
                pairs.append((human_turn, ai_turn))
                i += 2
            else:
                pairs.append(("", turn))
                i += 1
    return pairs

st.set_page_config(page_title="SYN-IQ · Transcript Scorer v4", layout="wide")
st.markdown("# 🔬 SYN-IQ · Transcript Scorer v4")
st.markdown("*Normalized V_t · Dyadic distances · Trajectory shifts · First-pass synergy score*")
st.divider()

if "all_pairs_v4" not in st.session_state:
    st.session_state.all_pairs_v4 = []

col1, col2, col3, col4 = st.columns(4)
with col1:
    session_id = st.text_input("Session ID", value="session_01")
with col2:
    ai_agent = st.selectbox("AI Agent", ["Claude", "ChatGPT", "Grok", "Gemini", "Other"])
with col3:
    novelty_type = st.selectbox("Novelty Type (block default)", list(_NOVELTY_WEIGHTS.keys()), index=0)
with col4:
    notes = st.text_input("Block notes", placeholder="What's notable here?")

st.divider()
raw_block = st.text_area("Paste full conversation block here", height=250)

if st.button("🔍 Parse & Preview Turns", type="secondary") and raw_block.strip():
    pairs = parse_conversation(raw_block, ai_agent)
    st.session_state.preview_pairs_v4 = pairs
    st.write(f"Found {len(pairs)} turn pairs")
    for i, (h, a) in enumerate(pairs):
        ch, ca = st.columns(2)
        with ch:
            st.code(f"HUMAN {i+1} ({len(h.split())} words)\n{h[:220]}")
        with ca:
            st.code(f"{ai_agent} {i+1} ({len(a.split())} words)\n{a[:220]}")

if st.button("✅ Score & Add All Pairs", type="primary"):
    source = st.session_state.get("preview_pairs_v4", None)
    if source is None and raw_block.strip():
        source = parse_conversation(raw_block, ai_agent)

    if source:
        prev_h_c = prev_a_c = None
        prev_h_v = prev_a_v = None

        for idx, (h_text, a_text) in enumerate(source):
            h_int, h_aff, h_act = score_iep(h_text) if h_text.strip() else (0.0, 0.0, 0.0)
            h_c = normalize_vector([h_int, h_aff, h_act])
            h_S, h_A, h_Q, h_D, h_R = score_vt_normalized(h_text) if h_text.strip() else (0.2, 0.2, 0.2, 0.2, 0.2)
            h_v = [h_S, h_A, h_Q, h_D, h_R]
            h_words = len(h_text.split())

            a_int, a_aff, a_act = score_iep(a_text) if a_text.strip() else (0.0, 0.0, 0.0)
            a_c = normalize_vector([a_int, a_aff, a_act])
            a_S, a_A, a_Q, a_D, a_R = score_vt_normalized(a_text) if a_text.strip() else (0.2, 0.2, 0.2, 0.2, 0.2)
            a_v = [a_S, a_A, a_Q, a_D, a_R]
            a_words = len(a_text.split())

            delta_c = l1_distance(h_c, a_c)
            delta_v = l1_distance(h_v, a_v)

            shift_c_h = l1_distance(prev_h_c, h_c) if prev_h_c is not None else 0.0
            shift_c_ai = l1_distance(prev_a_c, a_c) if prev_a_c is not None else 0.0
            shift_v_h = l1_distance(prev_h_v, h_v) if prev_h_v is not None else 0.0
            shift_v_ai = l1_distance(prev_a_v, a_v) if prev_a_v is not None else 0.0

            synergy = compute_synergy_score(delta_c, delta_v, novelty_type, shift_c_h, shift_c_ai)

            pair = {
                "session_id": session_id,
                "ai_agent": ai_agent,
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "pair_index": idx + 1,
                "novelty_type": novelty_type,
                "notes": notes,
                "h_words": h_words,
                "h_int_pct": h_int, "h_aff_pct": h_aff, "h_act_pct": h_act,
                "h_I": h_c[0], "h_E": h_c[1], "h_A": h_c[2],
                "h_S_t": h_S, "h_A_t": h_A, "h_Q_t": h_Q, "h_D_t": h_D, "h_R_t": h_R,
                "h_quadrant": quadrant(h_int, h_aff),
                "h_opener": first_sentence(h_text),
                "a_words": a_words,
                "a_int_pct": a_int, "a_aff_pct": a_aff, "a_act_pct": a_act,
                "a_I": a_c[0], "a_E": a_c[1], "a_A": a_c[2],
                "a_S_t": a_S, "a_A_t": a_A, "a_Q_t": a_Q, "a_D_t": a_D, "a_R_t": a_R,
                "a_quadrant": quadrant(a_int, a_aff),
                "a_opener": first_sentence(a_text),
                "word_ratio_ai_human": round(a_words / max(h_words, 1), 3),
                "delta_C": delta_c,
                "delta_V": delta_v,
                "shift_C_h": shift_c_h,
                "shift_C_ai": shift_c_ai,
                "shift_V_h": shift_v_h,
                "shift_V_ai": shift_v_ai,
                "delta_aff_pct": round(a_aff - h_aff, 1),
                "delta_depth": round(a_D - h_D, 4),
                "synergy_score": synergy,
                "human_excerpt": h_text.strip(),
                "ai_excerpt": a_text.strip(),
            }

            st.session_state.all_pairs_v4.append(pair)
            prev_h_c, prev_a_c = h_c, a_c
            prev_h_v, prev_a_v = h_v, a_v

        st.success(f"Added {len(source)} scored pairs to V4.")
        if "preview_pairs_v4" in st.session_state:
            del st.session_state.preview_pairs_v4
    else:
        st.warning("Paste a conversation block and parse it first.")

if st.session_state.all_pairs_v4:
    df = pd.DataFrame(st.session_state.all_pairs_v4)
    st.subheader(f"{len(df)} Scored Pairs")

    summary_cols = [
        "synergy_score", "delta_C", "delta_V",
        "shift_C_h", "shift_C_ai", "shift_V_h", "shift_V_ai",
        "word_ratio_ai_human", "delta_depth", "delta_aff_pct"
    ]
    st.dataframe(df.groupby("novelty_type")[summary_cols].mean().round(4), use_container_width=True)

    display_cols = [
        "pair_index", "novelty_type", "h_words", "a_words", "word_ratio_ai_human",
        "delta_C", "delta_V", "shift_C_h", "shift_C_ai",
        "h_I", "h_E", "h_A", "a_I", "a_E", "a_A",
        "h_S_t", "h_A_t", "h_Q_t", "h_D_t", "h_R_t",
        "a_S_t", "a_A_t", "a_Q_t", "a_D_t", "a_R_t",
        "synergy_score", "notes"
    ]
    st.dataframe(df[display_cols], use_container_width=True)

    st.download_button(
        "⬇️ Download CSV",
        data=df.to_csv(index=False),
        file_name=f"syniq_transcript_scorer_v4_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        type="primary"
    )
else:
    st.info("No scored pairs yet — paste a conversation block above.")

st.caption("SYN-IQ Research · Transcript Scorer v4 · Kouns, W. C. (2026) · SYNINT.AI · CBURZBO 🎹")
