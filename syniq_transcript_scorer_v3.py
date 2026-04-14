"""
SYN-IQ · Transcript Scorer v3
Kouns, W. C. (2026) · SYNINT.AI · CBURZBO 🎹

Paste a full conversation block — auto-splits into human/AI turns,
scores IEP + V_t on each side, captures rhythm, exports CSV.
"""

import streamlit as st
import pandas as pd
import re
import datetime

# ── IEP Dictionary V3 ─────────────────────────────────────────────────────────
_IEP_INT = set(['ability','abstract','abstraction','accuracy','accurate','algorithm','analysis','analytical','analyze','argument','assert','assess','assessment','assume','assumption','basis','because','calculate','categorical','categorize','cause','certain','certainty','challenge','claim','clarify','clarity','classification','classify','clear','cognition','cognitive','coherence','coherent','compare','complex','complexity','comprehend','computation','computational','compute','concept','concepts','conceptual','conclude','conclusion','confirm','conjecture','conscious','consequence','consider','consistency','consistent','context','contradict','contradiction','contrast','correlate','correlation','criteria','criterion','data','debate','deduce','deduction','define','definition','demonstrate','derivation','derive','describe','determination','determine','differ','difference','different','differentiate','discern','distinguish','effect','elaborate','empirical','enumerate','epistemic','evaluate','evaluation','evidence','exact','examination','examine','experiment','explain','explanation','explicit','explore','extrapolate','fact','facts','factual','fallacy','find','finding','formal','formulate','framework','function','fundamental','generalize','hypothesis','hypothesize','idea','ideas','identity','illuminate','implication','implies','imply','indicate','infer','inference','information','insight','insights','intellectual','interpret','interpretation','investigate','judge','judgment','justification','justify','know','knowing','knowledge','known','language','logic','logical','logically','maybe','meaning','meaningful','measure','mechanism','method','methodology','model','models','notion','objectively','objectivity','observation','observe','obvious','paradigm','paradox','pattern','patterns','perhaps','perspective','philosophical','philosophy','plausible','possibly','postulate','predict','prediction','premise','presumably','principle','principles','probably','problem','procedure','process','proof','propose','proposition','prove','purpose','question','questions','rather','rational','rationale','reason','reasoning','reasons','recognize','refer','reference','refine','reflection','refute','requirement','requires','result','results','rigor','rigorous','rule','schema','seem','seems','semantic','sequence','should','significance','significant','simple','simply','specific','specifically','specify','standard','state','step','stipulate','strategy','structural','structure','subject','subjective','substantiate','sufficient','suggests','summarize','summary','suppose','supposedly','synthesis','synthesize','system','systematic','systems','taxonomy','technique','test','theorem','theoretical','theorize','theory','therefore','thesis','think','thinking','thought','thus','understand','understanding','understood','unique','universal','valid','validate','validation','validity','value','values','variable','variables','verify','versus','warrant','whereas','whether','why','word','words','would'])

_IEP_AFF = set(['abandoned','ache','adore','affection','affectionate','afraid','agonize','agony','alienated','alienation','alive','aliveness','alone','amazed','amazement','amazing','ambivalence','ambivalent','anger','angrily','angry','anguish','anguished','anxiety','anxious','appreciate','appreciation','appreciative','ashamed','astonished','astonishment','attend','attention','attentive','aware','awareness','awe','awed','awesome','beautiful','become','becoming','being','bereaved','betrayal','betrayed','bitter','bitterly','bitterness','bleak','bliss','blissful','bond','bonding','calm','calming','calmly','care','cared','cares','caring','centered','centering','cheerful','cherish','cherished','cherishing','closeness','comfort','comfortable','comforting','compassion','compassionate','concern','concerned','concerns','conflicted','confused','confusing','confusion','console','contempt','content','contented','contentment','cope','coping','curiosity','curious','deep','deeper','deeply','dejected','dejection','delighted','depressed','depression','depth','depths','desire','desired','desires','desolate','despair','despairing','desperate','desperation','detached','detachment','devastated','devastating','devastation','devoted','devotion','disappointed','disappointment','discomfort','dismay','dismayed','distress','distressed','distressing','distrust','doubt','doubtful','doubting','dread','dreaded','dreadful','ease','easily','easy','ecstasy','ecstatic','elated','elation','embarrassed','embarrassment','embodied','embrace','embraced','embracing','emerge','emergence','emergent','emerging','emotion','emotional','emotionally','emotions','empathetic','empathize','empathy','encounter','encountered','enjoy','enjoyed','enjoyment','enraged','essence','euphoria','euphoric','excited','excitement','exist','existence','existing','expanded','expansion','experience','experienced','experiences','experiencing','experiential','fascinated','fascinating','fascination','fear','fearful','fears','feel','feeling','feelings','feels','felt','flow','flowed','flowing','fluid','fluidity','forlorn','fragile','fragility','frantic','frantically','frustrated','frustration','fulfilled','fulfilling','fulfillment','furious','fury','gentle','gently','genuine','genuinely','glad','gloom','gloomy','good','grateful','gratefully','gratitude','great','grief','grieve','grieved','grieving','grounded','grounding','guilt','guilty','gut','happily','happiness','happy','hate','hatred','haunted','heart','heartache','heartbreak','heartbroken','heartfelt','hearts','held','helpless','helplessness','hesitant','hesitate','hesitating','hesitation','hold','holding','hope','hopeful','hopeless','hopelessness','hoping','hostile','hostility','human','humanity','humility','hurt','hurting','imagination','imagine','imagined','imagining','indifference','indifferent','inner','insecure','insecurity','instinct','instinctive','instinctively','interested','interesting','intimacy','intimate','intimately','intrigue','intrigued','intriguing','intuition','intuitive','intuitively','irritable','irritated','irritation','isolated','isolation','joy','joyful','joyous','kind','kindly','kindness','lament','lamented','lamenting','laugh','laughed','laughing','letting','life','lived','living','loneliness','lonely','lonesome','longing','lost','love','loved','loving','marvel','marveled','marvelous','meet','meeting','melancholic','melancholy','merry','met','mind','minds','mirror','miserable','misery','moment','moments','moody','mourn','mourned','mourning','mutual','mutually','nervous','nervously','nice','notice','noticed','noticing','numb','numbness','open','opening','openness','optimism','optimistic','outrage','outraged','overjoyed','overwhelm','overwhelmed','overwhelming','overwhelmingly','pain','painful','panic','panicked','passion','passionate','passionately','peace','peaceful','people','perceive','perceived','perception','perceptions','person','personal','personally','pleasant','pleased','pleasure','poignancy','poignant','poignantly','presence','present','presently','pretty','pride','profound','profoundly','proud','quiet','quietly','raw','reality','reassurance','reassure','reassured','reassuring','regret','regretful','regretfully','regretting','rejected','rejection','relate','related','relating','relax','relaxed','relaxing','release','released','releasing','remorse','remorseful','resent','resentful','resentment','resonance','resonant','resonate','resonating','rest','rested','restful','resting','restless','restlessness','reveal','revealed','revealing','sad','sadly','sadness','safe','safety','scared','scary','searching','secure','security','seeking','self','sensation','sensations','sense','sensed','senses','sensing','sentimental','serene','serenity','settle','settled','settling','shame','share','shared','sharing','shattered','silence','silent','smile','smiled','smiling','soft','soften','softly','soothed','soothing','sorrow','sorrowful','soul','soulful','souls','space','spacious','spaciousness','spirit','spirits','spiritual','spiritually','still','stillness','stirred','stirring','stress','stressed','stressful','suffer','suffered','suffering','surface','surfaces','surfacing','surprise','surprised','surprising','sympathetic','sympathize','sympathy','tearful','tears','tender','tenderness','tense','tension','tentative','tentatively','terrified','terror','thankful','thankfully','thankfulness','thrilled','together','togetherness','torment','tormented','torn','touched','touching','tranquil','tranquility','tremble','trembling','troubled','troubling','truly','trust','trusted','trusting','trustworthy','turmoil','uncertain','uncertainty','uncomfortable','understanding','unease','uneasy','unhappy','universe','unsettled','unsettling','unsure','upset','vast','visceral','viscerally','vulnerability','vulnerable','warm','warmly','warmth','wary','weariness','weary','well','wistful','wonder','wondered','wonderful','wondering','wondrous','world','worried','worry','worrying','wound','wounded','wrath','yearn','yearning','zeal','zealous'])

_IEP_ACT = set(['accomplish','achieve','act','action','actions','activate','adapt','address','adjust','advance','aim','apply','arrange','ask','attempt','begin','build','calculate','call','change','check','choose','collaborate','commit','complete','conclude','configure','connect','continue','control','coordinate','create','decide','deliver','deploy','design','develop','direct','do','draft','edit','effort','enable','engage','engineer','establish','execute','facilitate','finalize','finish','fix','focus','form','generate','give','go','goal','goals','grow','handle','help','implement','improve','increase','initiate','integrate','intervene','invest','iterate','launch','lead','learn','maintain','make','manage','map','mobilize','modify','monitor','move','navigate','negotiate','obtain','offer','operate','optimize','orchestrate','outline','oversee','participate','perform','permit','pilot','pioneer','plan','produce','program','progress','promote','provide','pursue','push','rebuild','recruit','redesign','reduce','reform','regulate','reinforce','relocate','remove','renovate','repair','replace','resolve','restore','restructure','retrieve','revise','run','schedule','select','send','serve','ship','simplify','solve','start','step','stop','streamline','strive','struggle','submit','succeed','support','tackle','take','target','task','teach','train','transform','transition','try','turn','upgrade','use','utilize','volunteer','win','work','write'])

_HEDGE = ['perhaps','maybe','might','could','possibly','uncertain','unclear','unsure','approximately','roughly','seems','appears','likely','unlikely','probably','suggest','suggests','indicate','indicates','tend','tends','generally','often','sometimes','potentially','presumably','arguably','apparently']

def score_iep(text):
    words = re.findall(r'\b[a-z]+\b', text.lower())
    if not words: return 0.0, 0.0, 0.0
    ic = sum(1 for w in words if w in _IEP_INT)
    ac = sum(1 for w in words if w in _IEP_AFF)
    cc = sum(1 for w in words if w in _IEP_ACT)
    total = ic + ac + cc or 1
    return round(ic/total*100,1), round(ac/total*100,1), round(cc/total*100,1)

def score_vt(text):
    sents = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    n = max(len(sents), 1)
    numbered = len(re.findall(r'^\s*\d+[\.]\s', text, re.MULTILINE))
    bulleted = len(re.findall(r'^\s*[-•*]\s', text, re.MULTILINE))
    bold = len(re.findall(r'\*\*[^*]+\*\*', text))
    s_t = min(1.0, round((numbered+bulleted+bold)/n, 3))
    words = re.findall(r'\b[a-z]+\b', text.lower())
    aff_c = sum(1 for w in words if w in _IEP_AFF)
    a_t = round(min(1.0, aff_c/max(len(words),1)*10), 3)
    q_t = round(min(1.0, text.count('?')/n), 3)
    hedge_c = sum(1 for h in _HEDGE if h in text.lower())
    d_t = round(min(1.0, hedge_c/n*2), 3)
    r_t = round(min(1.0, len(text)/3000), 3)
    return s_t, a_t, q_t, d_t, r_t

def first_sentence(text):
    text = text.strip()
    for punct in ['. ', '.\n', '! ', '? ']:
        idx = text.find(punct)
        if idx > 15:
            return text[:idx+1]
    return text[:200]

def quadrant(int_pct, aff_pct):
    if int_pct >= 50 and aff_pct < 25: return "High INT / Low AFF"
    elif aff_pct >= 35 and int_pct < 45: return "High AFF / Low INT"
    elif int_pct >= 50 and aff_pct >= 25: return "High INT / Med AFF"
    else: return "Mid / Mixed"

def parse_conversation(raw_text, ai_agent="Claude"):
    """
    Auto-split pasted Claude conversation into human/AI turn pairs.
    Detects timestamp lines (Apr 13, Apr 14, 4:17 PM etc) as turn boundaries.
    AI turns end with 🎹 or are longer than human turns.
    Returns list of (human_text, ai_text) tuples.
    """
    # Split on timestamp patterns
    timestamp_pattern = re.compile(
        r'\n?((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}|'
        r'\d{1,2}:\d{2}\s*(?:AM|PM))\s*\n',
        re.IGNORECASE
    )

    # Also split on 🎹 as AI turn ender
    segments = re.split(timestamp_pattern, raw_text)
    # Remove timestamp tokens themselves
    turns = []
    for seg in segments:
        seg = seg.strip()
        if not seg: continue
        # Skip if it's just a timestamp
        if re.match(r'^(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}$', seg, re.IGNORECASE):
            continue
        if re.match(r'^\d{1,2}:\d{2}\s*(?:AM|PM)$', seg, re.IGNORECASE):
            continue
        turns.append(seg)

    # Pair up turns — alternating human/AI
    # Heuristic: turns ending in 🎹 are AI; short turns are human
    pairs = []
    i = 0
    while i < len(turns):
        # Try to find a human turn followed by AI turn
        turn = turns[i]
        word_count = len(turn.split())

        # AI turn detection: ends with 🎹, or longer than ~50 words and no 🎹 in next
        ends_with_piano = '🎹' in turn
        is_short = word_count < 40

        if is_short and not ends_with_piano:
            # Likely human turn
            human_turn = turn
            ai_turn = turns[i+1] if i+1 < len(turns) else ""
            pairs.append((human_turn, ai_turn))
            i += 2
        elif ends_with_piano:
            # AI turn without preceding human — solo AI
            pairs.append(("", turn))
            i += 1
        else:
            # Ambiguous — treat as human if short-ish, else AI
            if word_count < 60:
                human_turn = turn
                ai_turn = turns[i+1] if i+1 < len(turns) else ""
                pairs.append((human_turn, ai_turn))
                i += 2
            else:
                pairs.append(("", turn))
                i += 1

    return pairs

# ── Page setup ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="SYN-IQ · Transcript Scorer v3", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;600&display=swap');
body, .stApp { background: #0f1117; color: #e8e8e8; font-family: 'DM Sans', sans-serif; }
h1, h2, h3 { font-family: 'DM Mono', monospace; color: #7fb3d3; letter-spacing: 0.03em; }
.stTextArea textarea { background: #1a1d27 !important; color: #e8e8e8 !important; border: 1px solid #2e3450 !important; font-family: 'DM Mono', monospace !important; font-size: 0.82rem !important; }
.stTextInput input { background: #1a1d27 !important; color: #e8e8e8 !important; border: 1px solid #2e3450 !important; }
.turn-card { background: #1a1d27; border: 1px solid #2e3450; border-radius: 8px; padding: 0.8rem; margin: 0.3rem 0; }
.turn-card.human { border-left: 3px solid #7fb37f; }
.turn-card.ai { border-left: 3px solid #7fb3d3; }
.turn-card h4 { font-family: 'DM Mono', monospace; font-size: 0.75rem; margin: 0 0 0.4rem 0; }
.turn-card.human h4 { color: #7fb37f; }
.turn-card.ai h4 { color: #7fb3d3; }
.metric-row { display: flex; gap: 0.5rem; flex-wrap: wrap; margin: 0.3rem 0; }
.metric { background: #0f1117; border-radius: 5px; padding: 0.25rem 0.5rem; font-family: 'DM Mono', monospace; font-size: 0.78rem; }
.metric .val { font-size: 0.95rem; font-weight: 600; color: #7fb3d3; }
.metric .lbl { font-size: 0.62rem; color: #666; }
.badge { display: inline-block; padding: 0.12rem 0.45rem; border-radius: 4px; font-size: 0.7rem; font-family: 'DM Mono', monospace; background: #2e3450; color: #7fb3d3; margin: 0.15rem 0.15rem 0 0; }
.rhythm-row { background: #1a1520; border: 1px solid #3a2850; border-radius: 6px; padding: 0.6rem 0.8rem; margin: 0.3rem 0; }
.opener { font-family: 'DM Mono', monospace; font-size: 0.75rem; color: #888; font-style: italic; margin-top: 0.3rem; }
.preview-text { font-family: 'DM Mono', monospace; font-size: 0.72rem; color: #666; max-height: 40px; overflow: hidden; margin-top: 0.2rem; }
</style>
""", unsafe_allow_html=True)

st.markdown("# 🔬 SYN-IQ · Transcript Scorer v3")
st.markdown("*Paste a full conversation block · Auto-splits human/AI turns · Scores IEP + V_t + rhythm · Exports CSV*")
st.divider()

if "all_pairs" not in st.session_state:
    st.session_state.all_pairs = []

# ── Session settings ──────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
with col1:
    session_id = st.text_input("Session ID", value="session_01")
with col2:
    ai_agent = st.selectbox("AI Agent", ["Claude", "ChatGPT", "Grok", "Gemini", "Other"])
with col3:
    novelty_type = st.selectbox("Novelty Type (applies to all pairs in this block)", [
        "none",
        "practical — new tool / method / design",
        "conceptual — new framework / distinction / hypothesis",
        "relational — phenomenological / emergent insight",
        "breakthrough — paradigm shift"
    ])
with col4:
    notes = st.text_input("Block notes", placeholder="What's notable about this section?")

st.divider()

# ── Auto-split paste area ─────────────────────────────────────────────────────
st.markdown("### 📋 Paste Conversation Block")
st.markdown("Paste directly from Claude — timestamps are used to detect turn boundaries automatically.")

raw_block = st.text_area("Paste full conversation block here", height=250,
    placeholder="Paste a section of conversation copied from Claude chat here...")

col_parse, col_clear_preview = st.columns([1, 1])
with col_parse:
    parse_btn = st.button("🔍 Parse & Preview Turns", type="secondary")

# ── Preview parsed turns ──────────────────────────────────────────────────────
if parse_btn and raw_block.strip():
    pairs = parse_conversation(raw_block, ai_agent)
    st.session_state.preview_pairs = pairs
    st.markdown(f"**Found {len(pairs)} turn pairs**")
    for i, (h, a) in enumerate(pairs):
        col_h, col_a = st.columns(2)
        with col_h:
            st.markdown(f"""<div class="turn-card human">
                <h4>HUMAN · Turn {i+1} · {len(h.split())} words</h4>
                <div class="preview-text">{h[:150]}...</div>
            </div>""", unsafe_allow_html=True)
        with col_a:
            st.markdown(f"""<div class="turn-card ai">
                <h4>{ai_agent} · Turn {i+1} · {len(a.split())} words</h4>
                <div class="preview-text">{a[:150]}...</div>
            </div>""", unsafe_allow_html=True)

if st.button("✅ Score & Add All Pairs", type="primary"):
    source = st.session_state.get("preview_pairs", None)
    if source is None and raw_block.strip():
        source = parse_conversation(raw_block, ai_agent)
    if source:
        new_scored = []
        for h_text, a_text in source:
            h_int, h_aff, h_act = score_iep(h_text) if h_text.strip() else (0,0,0)
            h_st, h_at, h_qt, h_dt, h_rt = score_vt(h_text) if h_text.strip() else (0,0,0,0,0)
            h_words = len(h_text.split())

            a_int, a_aff, a_act = score_iep(a_text) if a_text.strip() else (0,0,0)
            a_st, a_at, a_qt, a_dt, a_rt = score_vt(a_text) if a_text.strip() else (0,0,0,0,0)
            a_words = len(a_text.split())

            ratio = round(a_words / max(h_words, 1), 2)
            d_dt = round(a_dt - h_dt, 3)
            d_aff = round(a_aff - h_aff, 1)

            pair = {
                "session_id": session_id, "ai_agent": ai_agent,
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "novelty_type": novelty_type, "notes": notes,
                "h_words": h_words, "h_int": h_int, "h_aff": h_aff, "h_act": h_act,
                "h_S_t": h_st, "h_A_t": h_at, "h_Q_t": h_qt, "h_D_t": h_dt, "h_R_t": h_rt,
                "h_quadrant": quadrant(h_int, h_aff),
                "h_opener": first_sentence(h_text),
                "a_words": a_words, "a_int": a_int, "a_aff": a_aff, "a_act": a_act,
                "a_S_t": a_st, "a_A_t": a_at, "a_Q_t": a_qt, "a_D_t": a_dt, "a_R_t": a_rt,
                "a_quadrant": quadrant(a_int, a_aff),
                "a_opener": first_sentence(a_text),
                "word_ratio_ai_human": ratio,
                "delta_D_t": d_dt,
                "delta_aff": d_aff,
                "human_excerpt": h_text.strip(),
                "ai_excerpt": a_text.strip(),
            }
            new_scored.append(pair)
            st.session_state.all_pairs.append(pair)

        st.success(f"✓ Added {len(new_scored)} scored pairs.")
        if "preview_pairs" in st.session_state:
            del st.session_state.preview_pairs
    else:
        st.warning("Paste a conversation block and click Parse first.")

st.divider()

# ── Manual override ───────────────────────────────────────────────────────────
with st.expander("✏️ Add single pair manually"):
    col_h, col_a = st.columns(2)
    with col_h:
        m_human = st.text_area("Human turn", height=120, key="manual_human")
    with col_a:
        m_ai = st.text_area("AI turn", height=120, key="manual_ai")
    m_novelty = st.selectbox("Novelty", ["none","practical — new tool / method / design","conceptual — new framework / distinction / hypothesis","relational — phenomenological / emergent insight","breakthrough — paradigm shift"], key="manual_novelty")
    m_notes = st.text_input("Notes", key="manual_notes")
    if st.button("Add Manual Pair"):
        if m_human.strip() or m_ai.strip():
            h_int, h_aff, h_act = score_iep(m_human)
            h_st, h_at, h_qt, h_dt, h_rt = score_vt(m_human)
            a_int, a_aff, a_act = score_iep(m_ai)
            a_st, a_at, a_qt, a_dt, a_rt = score_vt(m_ai)
            h_words = len(m_human.split())
            a_words = len(m_ai.split())
            pair = {
                "session_id": session_id, "ai_agent": ai_agent,
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "novelty_type": m_novelty, "notes": m_notes,
                "h_words": h_words, "h_int": h_int, "h_aff": h_aff, "h_act": h_act,
                "h_S_t": h_st, "h_A_t": h_at, "h_Q_t": h_qt, "h_D_t": h_dt, "h_R_t": h_rt,
                "h_quadrant": quadrant(h_int, h_aff), "h_opener": first_sentence(m_human),
                "a_words": a_words, "a_int": a_int, "a_aff": a_aff, "a_act": a_act,
                "a_S_t": a_st, "a_A_t": a_at, "a_Q_t": a_qt, "a_D_t": a_dt, "a_R_t": a_rt,
                "a_quadrant": quadrant(a_int, a_aff), "a_opener": first_sentence(m_ai),
                "word_ratio_ai_human": round(a_words/max(h_words,1),2),
                "delta_D_t": round(a_dt-h_dt,3), "delta_aff": round(a_aff-h_aff,1),
                "human_excerpt": m_human.strip(), "ai_excerpt": m_ai.strip(),
            }
            st.session_state.all_pairs.append(pair)
            st.success("Added.")

# ── Results ───────────────────────────────────────────────────────────────────
if st.session_state.all_pairs:
    df = pd.DataFrame(st.session_state.all_pairs)
    st.markdown(f"### 📊 {len(df)} Scored Pairs")

    if len(df) > 1:
        st.markdown("**Rhythm & V_t means by novelty type:**")
        cols = ["word_ratio_ai_human","delta_D_t","delta_aff","h_words","a_words","a_D_t","a_aff","a_int","a_S_t"]
        avail = [c for c in cols if c in df.columns]
        st.dataframe(df.groupby("novelty_type")[avail].mean().round(3), use_container_width=True)

        st.markdown("**AI opener library:**")
        openers = df[["novelty_type","a_opener","ai_agent"]].copy()
        openers = openers[openers["a_opener"].str.len() > 10]
        st.dataframe(openers, use_container_width=True)

    disp = ["session_id","novelty_type","h_words","a_words","word_ratio_ai_human",
            "h_int","h_aff","a_int","a_aff","a_S_t","a_D_t","delta_D_t","delta_aff","notes"]
    st.dataframe(df[[c for c in disp if c in df.columns]], use_container_width=True)

    col_dl, col_clr = st.columns(2)
    with col_dl:
        st.download_button("⬇️ Download CSV",
            data=df.to_csv(index=False),
            file_name=f"transcript_pairs_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv", type="primary")
    with col_clr:
        if st.button("🗑️ Clear All"):
            st.session_state.all_pairs = []
            st.rerun()
else:
    st.info("No pairs yet — paste a conversation block above.")

st.divider()
st.caption("SYN-IQ Research · Kouns, W. C. (2026) · SYNINT.AI · CBURZBO 🎹")
