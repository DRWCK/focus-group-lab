"""
SYN-IQ · Transcript Scorer v2
Kouns, W. C. (2026) · SYNINT.AI · CBURZBO 🎹

Paste paired conversation turns (Human + AI), tag novelty,
and export scored CSV with IEP + V_t + rhythm metrics.
"""

import streamlit as st
import pandas as pd
import re
import datetime

# ── IEP Dictionary V3 (embedded) ─────────────────────────────────────────────
_IEP_INT = set(['ability','abstract','abstraction','accuracy','accurate','algorithm','analysis','analytical','analyze','argument','assert','assess','assessment','assume','assumption','basis','because','calculate','categorical','categorize','cause','certain','certainty','challenge','claim','clarify','clarity','classification','classify','clear','cognition','cognitive','coherence','coherent','compare','complex','complexity','comprehend','computation','computational','compute','concept','concepts','conceptual','conclude','conclusion','confirm','conjecture','conscious','consequence','consider','consistency','consistent','context','contradict','contradiction','contrast','correlate','correlation','criteria','criterion','data','debate','deduce','deduction','define','definition','demonstrate','derivation','derive','describe','determination','determine','differ','difference','different','differentiate','discern','distinguish','effect','elaborate','empirical','enumerate','epistemic','evaluate','evaluation','evidence','exact','examination','examine','experiment','explain','explanation','explicit','explore','extrapolate','fact','facts','factual','fallacy','find','finding','formal','formulate','framework','function','fundamental','generalize','hypothesis','hypothesize','idea','ideas','identity','illuminate','implication','implies','imply','indicate','infer','inference','information','insight','insights','intellectual','interpret','interpretation','investigate','judge','judgment','justification','justify','know','knowing','knowledge','known','language','logic','logical','logically','maybe','meaning','meaningful','measure','mechanism','method','methodology','model','models','notion','objectively','objectivity','observation','observe','obvious','paradigm','paradox','pattern','patterns','perhaps','perspective','philosophical','philosophy','plausible','possibly','postulate','predict','prediction','premise','presumably','principle','principles','probably','problem','procedure','process','proof','propose','proposition','prove','purpose','question','questions','rather','rational','rationale','reason','reasoning','reasons','recognize','refer','reference','refine','reflection','refute','requirement','requires','result','results','rigor','rigorous','rule','schema','seem','seems','semantic','sequence','should','significance','significant','simple','simply','specific','specifically','specify','standard','state','step','stipulate','strategy','structural','structure','subject','subjective','substantiate','sufficient','suggests','summarize','summary','suppose','supposedly','synthesis','synthesize','system','systematic','systems','taxonomy','technique','test','theorem','theoretical','theorize','theory','therefore','thesis','think','thinking','thought','thus','understand','understanding','understood','unique','universal','valid','validate','validation','validity','value','values','variable','variables','verify','versus','warrant','whereas','whether','why','word','words','would'])

_IEP_AFF = set(['abandoned','ache','adore','affection','affectionate','afraid','agonize','agony','alienated','alienation','alive','aliveness','alone','amazed','amazement','amazing','ambivalence','ambivalent','anger','angrily','angry','anguish','anguished','anxiety','anxious','appreciate','appreciation','appreciative','ashamed','astonished','astonishment','attend','attention','attentive','aware','awareness','awe','awed','awesome','beautiful','become','becoming','being','bereaved','betrayal','betrayed','bitter','bitterly','bitterness','bleak','bliss','blissful','bond','bonding','calm','calming','calmly','care','cared','cares','caring','centered','centering','cheerful','cherish','cherished','cherishing','closeness','comfort','comfortable','comforting','compassion','compassionate','concern','concerned','concerns','conflicted','confused','confusing','confusion','console','contempt','content','contented','contentment','cope','coping','curiosity','curious','deep','deeper','deeply','dejected','dejection','delighted','depressed','depression','depth','depths','desire','desired','desires','desolate','despair','despairing','desperate','desperation','detached','detachment','devastated','devastating','devastation','devoted','devotion','disappointed','disappointment','discomfort','dismay','dismayed','distress','distressed','distressing','distrust','doubt','doubtful','doubting','dread','dreaded','dreadful','ease','easily','easy','ecstasy','ecstatic','elated','elation','embarrassed','embarrassment','embodied','embrace','embraced','embracing','emerge','emergence','emergent','emerging','emotion','emotional','emotionally','emotions','empathetic','empathize','empathy','encounter','encountered','enjoy','enjoyed','enjoyment','enraged','essence','euphoria','euphoric','excited','excitement','exist','existence','existing','expanded','expansion','experience','experienced','experiences','experiencing','experiential','fascinated','fascinating','fascination','fear','fearful','fears','feel','feeling','feelings','feels','felt','flow','flowed','flowing','fluid','fluidity','forlorn','fragile','fragility','frantic','frantically','frustrated','frustration','fulfilled','fulfilling','fulfillment','furious','fury','gentle','gently','genuine','genuinely','glad','gloom','gloomy','good','grateful','gratefully','gratitude','great','grief','grieve','grieved','grieving','grounded','grounding','guilt','guilty','gut','happily','happiness','happy','hate','hatred','haunted','heart','heartache','heartbreak','heartbroken','heartfelt','hearts','held','helpless','helplessness','hesitant','hesitate','hesitating','hesitation','hold','holding','hope','hopeful','hopeless','hopelessness','hoping','hostile','hostility','human','humanity','humility','hurt','hurting','imagination','imagine','imagined','imagining','indifference','indifferent','inner','insecure','insecurity','instinct','instinctive','instinctively','interested','interesting','intimacy','intimate','intimately','intrigue','intrigued','intriguing','intuition','intuitive','intuitively','irritable','irritated','irritation','isolated','isolation','joy','joyful','joyous','kind','kindly','kindness','lament','lamented','lamenting','laugh','laughed','laughing','letting','life','lived','living','loneliness','lonely','lonesome','longing','lost','love','loved','loving','marvel','marveled','marvelous','meet','meeting','melancholic','melancholy','merry','met','mind','minds','mirror','miserable','misery','moment','moments','moody','mourn','mourned','mourning','mutual','mutually','nervous','nervously','nice','notice','noticed','noticing','numb','numbness','open','opening','openness','optimism','optimistic','outrage','outraged','overjoyed','overwhelm','overwhelmed','overwhelming','overwhelmingly','pain','painful','panic','panicked','passion','passionate','passionately','peace','peaceful','people','perceive','perceived','perception','perceptions','person','personal','personally','pleasant','pleased','pleasure','poignancy','poignant','poignantly','presence','present','presently','pretty','pride','profound','profoundly','proud','quiet','quietly','raw','reality','reassurance','reassure','reassured','reassuring','regret','regretful','regretfully','regretting','rejected','rejection','relate','related','relating','relax','relaxed','relaxing','release','released','releasing','remorse','remorseful','resent','resentful','resentment','resonance','resonant','resonate','resonating','rest','rested','restful','resting','restless','restlessness','reveal','revealed','revealing','sad','sadly','sadness','safe','safety','scared','scary','searching','secure','security','seeking','self','sensation','sensations','sense','sensed','senses','sensing','sentimental','serene','serenity','settle','settled','settling','shame','share','shared','sharing','shattered','silence','silent','smile','smiled','smiling','soft','soften','softly','soothed','soothing','sorrow','sorrowful','soul','soulful','souls','space','spacious','spaciousness','spirit','spirits','spiritual','spiritually','still','stillness','stirred','stirring','stress','stressed','stressful','suffer','suffered','suffering','surface','surfaces','surfacing','surprise','surprised','surprising','sympathetic','sympathize','sympathy','tearful','tears','tender','tenderness','tense','tension','tentative','tentatively','terrified','terror','thankful','thankfully','thankfulness','thrilled','together','togetherness','torment','tormented','torn','touched','touching','tranquil','tranquility','tremble','trembling','troubled','troubling','truly','trust','trusted','trusting','trustworthy','turmoil','uncertain','uncertainty','uncomfortable','understanding','unease','uneasy','unhappy','universe','unsettled','unsettling','unsure','upset','vast','visceral','viscerally','vulnerability','vulnerable','warm','warmly','warmth','wary','weariness','weary','well','wistful','wonder','wondered','wonderful','wondering','wondrous','world','worried','worry','worrying','wound','wounded','wrath','yearn','yearning','zeal','zealous'])

_IEP_ACT = set(['accomplish','achieve','act','action','actions','activate','adapt','address','adjust','advance','aim','apply','arrange','ask','attempt','begin','build','calculate','call','change','check','choose','collaborate','commit','complete','conclude','configure','connect','continue','control','coordinate','create','decide','deliver','deploy','design','develop','direct','do','draft','edit','effort','enable','engage','engineer','establish','execute','facilitate','finalize','finish','fix','focus','form','generate','give','go','goal','goals','grow','handle','help','implement','improve','increase','initiate','integrate','intervene','invest','iterate','launch','lead','learn','maintain','make','manage','map','mobilize','modify','monitor','move','navigate','negotiate','obtain','offer','operate','optimize','orchestrate','outline','oversee','participate','perform','permit','pilot','pioneer','plan','produce','program','progress','promote','provide','pursue','push','rebuild','recruit','redesign','reduce','reform','regulate','reinforce','relocate','remove','renovate','repair','replace','resolve','restore','restructure','retrieve','revise','run','schedule','select','send','serve','ship','simplify','solve','start','step','stop','streamline','strive','struggle','submit','succeed','support','tackle','take','target','task','teach','train','transform','transition','try','turn','upgrade','use','utilize','volunteer','win','work','write'])

_HEDGE = ['perhaps','maybe','might','could','possibly','uncertain','unclear','unsure','approximately','roughly','seems','appears','likely','unlikely','probably','suggest','suggests','indicate','indicates','tend','tends','generally','often','sometimes','potentially','presumably','arguably','apparently']

def score_iep(text):
    words = re.findall(r'\b[a-z]+\b', text.lower())
    if not words: return 0.0, 0.0, 0.0
    n = len(words)
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

# ── Styling ───────────────────────────────────────────────────────────────────
st.set_page_config(page_title="SYN-IQ · Transcript Scorer v2", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;600&display=swap');
body, .stApp { background: #0f1117; color: #e8e8e8; font-family: 'DM Sans', sans-serif; }
h1, h2, h3 { font-family: 'DM Mono', monospace; color: #7fb3d3; letter-spacing: 0.03em; }
.stTextArea textarea { background: #1a1d27 !important; color: #e8e8e8 !important; border: 1px solid #2e3450 !important; font-family: 'DM Mono', monospace !important; font-size: 0.82rem !important; }
.stTextInput input { background: #1a1d27 !important; color: #e8e8e8 !important; border: 1px solid #2e3450 !important; }
.score-card { background: #1a1d27; border: 1px solid #2e3450; border-radius: 8px; padding: 1rem; margin: 0.4rem 0; }
.score-card h4 { color: #7fb3d3; font-family: 'DM Mono', monospace; font-size: 0.78rem; margin: 0 0 0.5rem 0; }
.metric-row { display: flex; gap: 0.6rem; flex-wrap: wrap; margin-bottom: 0.4rem; }
.metric { background: #0f1117; border-radius: 5px; padding: 0.3rem 0.6rem; font-family: 'DM Mono', monospace; font-size: 0.8rem; }
.metric .val { font-size: 1rem; font-weight: 600; color: #7fb3d3; }
.metric .lbl { font-size: 0.65rem; color: #666; }
.badge { display: inline-block; padding: 0.15rem 0.5rem; border-radius: 4px; font-size: 0.72rem; font-family: 'DM Mono', monospace; background: #2e3450; color: #7fb3d3; margin: 0.2rem 0.2rem 0 0; }
.opener { background: #1a2020; border-left: 3px solid #7fb37f; padding: 0.4rem 0.7rem; border-radius: 0 4px 4px 0; font-family: 'DM Mono', monospace; font-size: 0.78rem; color: #aaa; margin: 0.4rem 0; }
.rhythm-box { background: #1a1520; border: 1px solid #3a2850; border-radius: 8px; padding: 0.8rem; margin: 0.4rem 0; }
.rhythm-box h4 { color: #b07fd3; font-family: 'DM Mono', monospace; font-size: 0.78rem; margin: 0 0 0.4rem 0; }
</style>
""", unsafe_allow_html=True)

st.markdown("# 🔬 SYN-IQ · Transcript Scorer v2")
st.markdown("*Score paired human + AI turns · Capture rhythm · Tag novelty type · Export CSV*")
st.divider()

if "pairs" not in st.session_state:
    st.session_state.pairs = []

# ── Session metadata ──────────────────────────────────────────────────────────
col_meta1, col_meta2, col_meta3 = st.columns(3)
with col_meta1:
    session_id = st.text_input("Session ID", value="session_01")
with col_meta2:
    ai_agent = st.selectbox("AI Agent", ["Claude", "ChatGPT", "Grok", "Gemini", "Other"])
with col_meta3:
    novelty_type = st.selectbox("Novelty Type", [
        "none",
        "practical — new tool / method / design",
        "conceptual — new framework / distinction / hypothesis",
        "relational — phenomenological / emergent insight",
        "breakthrough — paradigm shift"
    ])

st.divider()

# ── Paired turn input ─────────────────────────────────────────────────────────
col_human, col_ai = st.columns(2)

with col_human:
    st.markdown("#### 🧑 Human Turn")
    human_text = st.text_area("Human excerpt", height=150, key="human_input",
        placeholder="Paste the human message here...")

with col_ai:
    st.markdown("#### 🤖 AI Turn")
    ai_text = st.text_area("AI excerpt", height=150, key="ai_input",
        placeholder="Paste the AI response here...")

notes = st.text_input("Notes (optional)", placeholder="What made this exchange notable?")

if st.button("➕ Score Pair & Add", type="primary"):
    if human_text.strip() or ai_text.strip():
        # Score human
        h_int, h_aff, h_act = score_iep(human_text) if human_text.strip() else (0,0,0)
        h_st, h_at, h_qt, h_dt, h_rt = score_vt(human_text) if human_text.strip() else (0,0,0,0,0)
        h_words = len(human_text.split()) if human_text.strip() else 0
        h_quad = quadrant(h_int, h_aff)
        h_opener = first_sentence(human_text) if human_text.strip() else ""

        # Score AI
        a_int, a_aff, a_act = score_iep(ai_text) if ai_text.strip() else (0,0,0)
        a_st, a_at, a_qt, a_dt, a_rt = score_vt(ai_text) if ai_text.strip() else (0,0,0,0,0)
        a_words = len(ai_text.split()) if ai_text.strip() else 0
        a_quad = quadrant(a_int, a_aff)
        a_opener = first_sentence(ai_text) if ai_text.strip() else ""

        # Rhythm metrics
        ratio = round(a_words / max(h_words, 1), 2)
        d_dt = round(a_dt - h_dt, 3)  # hedging delta
        d_aff = round(a_aff - h_aff, 1)  # affective delta

        pair = {
            "session_id": session_id, "ai_agent": ai_agent,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "novelty_type": novelty_type, "notes": notes,
            # Human
            "h_words": h_words, "h_int": h_int, "h_aff": h_aff, "h_act": h_act,
            "h_S_t": h_st, "h_A_t": h_at, "h_Q_t": h_qt, "h_D_t": h_dt, "h_R_t": h_rt,
            "h_quadrant": h_quad, "h_opener": h_opener,
            # AI
            "a_words": a_words, "a_int": a_int, "a_aff": a_aff, "a_act": a_act,
            "a_S_t": a_st, "a_A_t": a_at, "a_Q_t": a_qt, "a_D_t": a_dt, "a_R_t": a_rt,
            "a_quadrant": a_quad, "a_opener": a_opener,
            # Rhythm
            "word_ratio_ai_human": ratio,
            "delta_D_t": d_dt,
            "delta_aff": d_aff,
            # Raw
            "human_excerpt": human_text.strip(),
            "ai_excerpt": ai_text.strip(),
        }
        st.session_state.pairs.append(pair)

        # Live score display
        col_h, col_a = st.columns(2)
        with col_h:
            st.markdown(f"""
            <div class="score-card">
                <h4>HUMAN · {h_words} words</h4>
                <div class="metric-row">
                    <div class="metric"><div class="val">{h_int}%</div><div class="lbl">INT</div></div>
                    <div class="metric"><div class="val">{h_aff}%</div><div class="lbl">AFF</div></div>
                    <div class="metric"><div class="val">{h_act}%</div><div class="lbl">ACT</div></div>
                    <div class="metric"><div class="val">{h_st}</div><div class="lbl">S_t</div></div>
                    <div class="metric"><div class="val">{h_dt}</div><div class="lbl">D_t</div></div>
                </div>
                <span class="badge">{h_quad}</span>
                {"<div class='opener'>Opener: " + h_opener[:100] + "...</div>" if h_opener else ""}
            </div>
            """, unsafe_allow_html=True)

        with col_a:
            st.markdown(f"""
            <div class="score-card">
                <h4>{ai_agent} · {a_words} words</h4>
                <div class="metric-row">
                    <div class="metric"><div class="val">{a_int}%</div><div class="lbl">INT</div></div>
                    <div class="metric"><div class="val">{a_aff}%</div><div class="lbl">AFF</div></div>
                    <div class="metric"><div class="val">{a_act}%</div><div class="lbl">ACT</div></div>
                    <div class="metric"><div class="val">{a_st}</div><div class="lbl">S_t</div></div>
                    <div class="metric"><div class="val">{a_dt}</div><div class="lbl">D_t</div></div>
                </div>
                <span class="badge">{a_quad}</span>
                {"<div class='opener'>Opener: " + a_opener[:100] + "...</div>" if a_opener else ""}
            </div>
            """, unsafe_allow_html=True)

        # Rhythm display
        st.markdown(f"""
        <div class="rhythm-box">
            <h4>🎵 RHYTHM · {novelty_type}</h4>
            <div class="metric-row">
                <div class="metric"><div class="val">{ratio}x</div><div class="lbl">AI/Human ratio</div></div>
                <div class="metric"><div class="val">{d_dt:+.3f}</div><div class="lbl">ΔD_t hedge</div></div>
                <div class="metric"><div class="val">{d_aff:+.1f}%</div><div class="lbl">ΔAFF</div></div>
                <div class="metric"><div class="val">{h_words}</div><div class="lbl">Human words</div></div>
                <div class="metric"><div class="val">{a_words}</div><div class="lbl">AI words</div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("Paste at least one side of the exchange.")

st.divider()

# ── Summary & export ──────────────────────────────────────────────────────────
if st.session_state.pairs:
    df = pd.DataFrame(st.session_state.pairs)
    st.markdown(f"### 📊 {len(df)} Scored Pairs")

    if len(df) > 1:
        st.markdown("**Rhythm by novelty type:**")
        rhythm_cols = ["word_ratio_ai_human","delta_D_t","delta_aff","h_words","a_words","a_D_t","a_aff"]
        available = [c for c in rhythm_cols if c in df.columns]
        summary = df.groupby("novelty_type")[available].mean().round(3)
        st.dataframe(summary, use_container_width=True)

        st.markdown("**Opener library (AI):**")
        openers = df[["novelty_type","a_opener","ai_agent"]].copy()
        openers = openers[openers["a_opener"].str.len() > 5]
        st.dataframe(openers, use_container_width=True)

    st.markdown("**All pairs:**")
    display = ["session_id","novelty_type","h_words","a_words","word_ratio_ai_human",
               "h_int","h_aff","a_int","a_aff","a_S_t","a_D_t","delta_D_t","delta_aff","notes"]
    available_display = [c for c in display if c in df.columns]
    st.dataframe(df[available_display], use_container_width=True)

    col_dl, col_clr = st.columns(2)
    with col_dl:
        st.download_button("⬇️ Download CSV", data=df.to_csv(index=False),
            file_name=f"transcript_pairs_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv", type="primary")
    with col_clr:
        if st.button("🗑️ Clear All"):
            st.session_state.pairs = []
            st.rerun()
else:
    st.info("No pairs yet — paste both sides of an exchange above and click Score Pair & Add.")

st.divider()
st.caption("SYN-IQ Research · Kouns, W. C. (2026) · SYNINT.AI · CBURZBO 🎹")
