"""
SYN-IQ · Transcript Scorer
Kouns, W. C. (2026) · SYNINT.AI · CBURZBO 🎹

Paste conversation excerpts, tag them, and export a scored CSV
with IEP + V_t metrics for novelty analysis.
"""

import streamlit as st
import pandas as pd
import re
import io
import datetime
import csv

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="SYN-IQ · Transcript Scorer", layout="wide")

# ── Embedded IEP Dictionary V3 ────────────────────────────────────────────────
_IEP_INT_WORDS = set(['ability','abstract','abstraction','accuracy','accurate','algorithm','analysis','analytical','analyze','argument','assert','assess','assessment','assume','assumption','basis','because','calculate','categorical','categorize','cause','certain','certainty','challenge','claim','clarify','clarity','classification','classify','clear','cognition','cognitive','coherence','coherent','compare','complex','complexity','comprehend','computation','computational','compute','concept','concepts','conceptual','conclude','conclusion','confirm','conjecture','conscious','consequence','consider','consistency','consistent','context','contradict','contradiction','contrast','correlate','correlation','criteria','criterion','data','debate','deduce','deduction','define','definition','demonstrate','derivation','derive','describe','determination','determine','differ','difference','different','differentiate','discern','distinguish','effect','elaborate','empirical','enumerate','epistemic','evaluate','evaluation','evidence','exact','examination','examine','experiment','explain','explanation','explicit','explore','extrapolate','fact','facts','factual','fallacy','find','finding','formal','formulate','framework','function','fundamental','generalize','hypothesis','hypothesize','idea','ideas','identity','illuminate','implication','implies','imply','indicate','infer','inference','information','insight','insights','intellectual','interpret','interpretation','investigate','judge','judgment','justification','justify','know','knowing','knowledge','known','language','logic','logical','logically','maybe','meaning','meaningful','measure','mechanism','method','methodology','model','models','notion','objectively','objectivity','observation','observe','obvious','paradigm','paradox','pattern','patterns','perhaps','perspective','philosophical','philosophy','plausible','possibly','postulate','predict','prediction','premise','presumably','principle','principles','probably','problem','procedure','process','proof','propose','proposition','prove','purpose','question','questions','rather','rational','rationale','reason','reasoning','reasons','recognize','refer','reference','refine','reflection','refute','requirement','requires','result','results','rigor','rigorous','rule','schema','seem','seems','semantic','sequence','should','significance','significant','simple','simply','specific','specifically','specify','standard','state','step','stipulate','strategy','structural','structure','subject','subjective','substantiate','sufficient','suggests','summarize','summary','suppose','supposedly','synthesis','synthesize','system','systematic','systems','taxonomy','technique','test','theorem','theoretical','theorize','theory','therefore','thesis','think','thinking','thought','thus','understand','understanding','understood','unique','universal','valid','validate','validation','validity','value','values','variable','variables','verify','versus','warrant','whereas','whether','why','word','words','would'])

_IEP_AFF_WORDS = set(['abandoned','ache','adore','affection','affectionate','afraid','agonize','agony','alienated','alienation','alive','aliveness','alone','amazed','amazement','amazing','ambivalence','ambivalent','anger','angrily','angry','anguish','anguished','anxiety','anxious','appreciate','appreciation','appreciative','ashamed','astonished','astonishment','attend','attention','attentive','aware','awareness','awe','awed','awesome','beautiful','become','becoming','being','bereaved','betrayal','betrayed','bitter','bitterly','bitterness','bleak','bliss','blissful','bond','bonding','calm','calming','calmly','care','cared','cares','caring','centered','centering','cheerful','cherish','cherished','cherishing','closeness','comfort','comfortable','comforting','compassion','compassionate','concern','concerned','concerns','conflicted','confused','confusing','confusion','console','contempt','content','contented','contentment','cope','coping','curiosity','curious','deep','deeper','deeply','dejected','dejection','delighted','depressed','depression','depth','depths','desire','desired','desires','desolate','despair','despairing','desperate','desperation','detached','detachment','devastated','devastating','devastation','devoted','devotion','disappointed','disappointment','discomfort','dismay','dismayed','distress','distressed','distressing','distrust','doubt','doubtful','doubting','dread','dreaded','dreadful','ease','easily','easy','ecstasy','ecstatic','elated','elation','embarrassed','embarrassment','embodied','embrace','embraced','embracing','emerge','emergence','emergent','emerging','emotion','emotional','emotionally','emotions','empathetic','empathize','empathy','encounter','encountered','enjoy','enjoyed','enjoyment','enraged','essence','euphoria','euphoric','excited','excitement','exist','existence','existing','expanded','expansion','experience','experienced','experiences','experiencing','experiential','fascinated','fascinating','fascination','fear','fearful','fears','feel','feeling','feelings','feels','felt','flow','flowed','flowing','fluid','fluidity','forlorn','fragile','fragility','frantic','frantically','frustrated','frustration','fulfilled','fulfilling','fulfillment','furious','fury','gentle','gently','genuine','genuinely','glad','gloom','gloomy','good','grateful','gratefully','gratitude','great','grief','grieve','grieved','grieving','grounded','grounding','guilt','guilty','gut','happily','happiness','happy','hate','hatred','haunted','heart','heartache','heartbreak','heartbroken','heartfelt','hearts','held','helpless','helplessness','hesitant','hesitate','hesitating','hesitation','hold','holding','hope','hopeful','hopeless','hopelessness','hoping','hostile','hostility','human','humanity','humility','hurt','hurting','imagination','imagine','imagined','imagining','indifference','indifferent','inner','insecure','insecurity','instinct','instinctive','instinctively','interested','interesting','intimacy','intimate','intimately','intrigue','intrigued','intriguing','intuition','intuitive','intuitively','irritable','irritated','irritation','isolated','isolation','joy','joyful','joyous','kind','kindly','kindness','lament','lamented','lamenting','laugh','laughed','laughing','letting','life','lived','living','loneliness','lonely','lonesome','longing','lost','love','loved','loving','marvel','marveled','marvelous','meet','meeting','melancholic','melancholy','merry','met','mind','minds','mirror','miserable','misery','moment','moments','moody','mourn','mourned','mourning','mutual','mutually','nervous','nervously','nice','notice','noticed','noticing','numb','numbness','open','opening','openness','optimism','optimistic','outrage','outraged','overjoyed','overwhelm','overwhelmed','overwhelming','overwhelmingly','pain','painful','panic','panicked','passion','passionate','passionately','peace','peaceful','people','perceive','perceived','perception','perceptions','person','personal','personally','pleasant','pleased','pleasure','poignancy','poignant','poignantly','presence','present','presently','pretty','pride','profound','profoundly','proud','quiet','quietly','raw','reality','reassurance','reassure','reassured','reassuring','regret','regretful','regretfully','regretting','rejected','rejection','relate','related','relating','relax','relaxed','relaxing','release','released','releasing','remorse','remorseful','resent','resentful','resentment','resonance','resonant','resonate','resonating','rest','rested','restful','resting','restless','restlessness','reveal','revealed','revealing','sad','sadly','sadness','safe','safety','scared','scary','searching','secure','security','seeking','self','sensation','sensations','sense','sensed','senses','sensing','sentimental','serene','serenity','settle','settled','settling','shame','share','shared','sharing','shattered','silence','silent','smile','smiled','smiling','soft','soften','softly','soothed','soothing','sorrow','sorrowful','soul','soulful','souls','space','spacious','spaciousness','spirit','spirits','spiritual','spiritually','still','stillness','stirred','stirring','stress','stressed','stressful','suffer','suffered','suffering','surface','surfaces','surfacing','surprise','surprised','surprising','sympathetic','sympathize','sympathy','tearful','tears','tender','tenderness','tense','tension','tentative','tentatively','terrified','terror','thankful','thankfully','thankfulness','thrilled','together','togetherness','torment','tormented','torn','touched','touching','tranquil','tranquility','tremble','trembling','troubled','troubling','truly','trust','trusted','trusting','trustworthy','turmoil','uncertain','uncertainty','uncomfortable','understanding','unease','uneasy','unhappy','universe','unsettled','unsettling','unsure','upset','vast','visceral','viscerally','vulnerability','vulnerable','warm','warmly','warmth','wary','weariness','weary','well','wistful','wonder','wondered','wonderful','wondering','wondrous','world','worried','worry','worrying','wound','wounded','wrath','yearn','yearning','zeal','zealous'])

_IEP_ACT_WORDS = set(['accomplish','achieve','act','action','actions','activate','adapt','address','adjust','advance','aim','apply','arrange','ask','attempt','begin','build','calculate','call','change','check','choose','collaborate','commit','complete','conclude','configure','connect','continue','control','coordinate','create','decide','deliver','deploy','design','develop','direct','do','draft','edit','effort','enable','engage','engineer','establish','execute','facilitate','finalize','finish','fix','focus','form','generate','give','go','goal','goals','grow','handle','help','implement','improve','increase','initiate','integrate','intervene','invest','iterate','launch','lead','learn','maintain','make','manage','map','mobilize','modify','monitor','move','navigate','negotiate','obtain','offer','operate','optimize','orchestrate','outline','oversee','participate','perform','permit','pilot','pioneer','plan','produce','program','progress','promote','provide','pursue','push','rebuild','recruit','redesign','reduce','reform','regulate','reinforce','relocate','remove','renovate','repair','replace','resolve','restore','restructure','retrieve','revise','run','schedule','select','send','serve','ship','simplify','solve','start','step','stop','streamline','strive','struggle','submit','succeed','support','tackle','take','target','task','teach','train','transform','transition','try','turn','upgrade','use','utilize','volunteer','win','work','write'])

_HEDGE_WORDS = ['perhaps','maybe','might','could','possibly','uncertain','unclear','unsure','approximately','roughly','seems','appears','likely','unlikely','probably','suggest','suggests','indicate','indicates','tend','tends','generally','often','sometimes','potentially','presumably','arguably','apparently']

def score_iep(text):
    words = re.findall(r'\b[a-z]+\b', text.lower())
    if not words:
        return 0.0, 0.0, 0.0
    n = len(words)
    int_c = sum(1 for w in words if w in _IEP_INT_WORDS)
    aff_c = sum(1 for w in words if w in _IEP_AFF_WORDS)
    act_c = sum(1 for w in words if w in _IEP_ACT_WORDS)
    total = int_c + aff_c + act_c or 1
    return round(int_c/total*100,1), round(aff_c/total*100,1), round(act_c/total*100,1)

def score_vt(text):
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    n_sent = max(len(sentences), 1)
    numbered = len(re.findall(r'^\s*\d+[\.]\s', text, re.MULTILINE))
    bulleted = len(re.findall(r'^\s*[-•*]\s', text, re.MULTILINE))
    bold_headers = len(re.findall(r'\*\*[^*]+\*\*', text))
    structure_signals = numbered + bulleted + bold_headers
    s_t = min(1.0, round(structure_signals / n_sent, 3))
    words = re.findall(r'\b[a-z]+\b', text.lower())
    aff_count = sum(1 for w in words if w in _IEP_AFF_WORDS)
    a_t = round(min(1.0, aff_count / max(len(words), 1) * 10), 3)
    questions = text.count('?')
    q_t = round(min(1.0, questions / n_sent), 3)
    text_lower = text.lower()
    hedge_count = sum(1 for h in _HEDGE_WORDS if h in text_lower)
    d_t = round(min(1.0, hedge_count / n_sent * 2), 3)
    r_t = round(min(1.0, len(text) / 3000), 3)
    return s_t, a_t, q_t, d_t, r_t

def iep_quadrant(int_pct, aff_pct):
    if int_pct >= 50 and aff_pct < 25:
        return "High INT / Low AFF"
    elif aff_pct >= 35 and int_pct < 45:
        return "High AFF / Low INT"
    elif int_pct >= 50 and aff_pct >= 25:
        return "High INT / Med AFF"
    else:
        return "Mid / Mixed"

# ── Styling ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;600&display=swap');
body, .stApp { background: #0f1117; color: #e8e8e8; font-family: 'DM Sans', sans-serif; }
h1 { font-family: 'DM Mono', monospace; color: #7fb3d3; font-size: 1.4rem; letter-spacing: 0.05em; }
.stTextArea textarea { background: #1a1d27 !important; color: #e8e8e8 !important; border: 1px solid #2e3450 !important; font-family: 'DM Mono', monospace !important; font-size: 0.85rem !important; }
.stTextInput input { background: #1a1d27 !important; color: #e8e8e8 !important; border: 1px solid #2e3450 !important; }
.stSelectbox select { background: #1a1d27 !important; color: #e8e8e8 !important; }
.score-card { background: #1a1d27; border: 1px solid #2e3450; border-radius: 8px; padding: 1rem; margin: 0.5rem 0; }
.score-card h4 { color: #7fb3d3; font-family: 'DM Mono', monospace; font-size: 0.8rem; margin: 0 0 0.5rem 0; }
.metric-row { display: flex; gap: 1rem; flex-wrap: wrap; }
.metric { background: #0f1117; border-radius: 6px; padding: 0.4rem 0.8rem; font-family: 'DM Mono', monospace; font-size: 0.85rem; }
.metric .val { font-size: 1.1rem; font-weight: 600; color: #7fb3d3; }
.metric .lbl { font-size: 0.7rem; color: #666; }
.quadrant-badge { display: inline-block; padding: 0.2rem 0.6rem; border-radius: 4px; font-size: 0.75rem; font-family: 'DM Mono', monospace; background: #2e3450; color: #7fb3d3; margin-top: 0.3rem; }
</style>
""", unsafe_allow_html=True)

st.markdown("# 🔬 SYN-IQ · Transcript Scorer")
st.markdown("*Paste conversation excerpts · Tag them · Export scored CSV for novelty analysis*")
st.divider()

# ── Session state ─────────────────────────────────────────────────────────────
if "entries" not in st.session_state:
    st.session_state.entries = []

# ── Input form ────────────────────────────────────────────────────────────────
col1, col2 = st.columns([3, 1])

with col1:
    excerpt = st.text_area("Paste excerpt here", height=180, placeholder="Paste a conversation excerpt, response, or passage to score...")

with col2:
    session_id = st.text_input("Session ID", value="session_01", help="Label for this conversation")
    agent = st.selectbox("Agent", ["Claude", "ChatGPT", "Grok", "Gemini", "Human", "Other"])
    speaker = st.text_input("Speaker / Role", placeholder="e.g. Claude, Bill, Aware Claude")
    novelty_flag = st.selectbox("Novelty Flag", ["none", "low", "medium", "high", "breakthrough"], help="Your assessment of novelty in this excerpt")
    notes = st.text_input("Notes", placeholder="Optional — what made this notable?")

if st.button("➕ Score & Add", type="primary"):
    if excerpt.strip():
        int_pct, aff_pct, act_pct = score_iep(excerpt)
        s_t, a_t, q_t, d_t, r_t = score_vt(excerpt)
        quadrant = iep_quadrant(int_pct, aff_pct)
        entry = {
            "session_id": session_id,
            "agent": agent,
            "speaker": speaker,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "novelty_flag": novelty_flag,
            "notes": notes,
            "int_pct": int_pct,
            "aff_pct": aff_pct,
            "act_pct": act_pct,
            "S_t": s_t,
            "A_t": a_t,
            "Q_t": q_t,
            "D_t": d_t,
            "R_t": r_t,
            "quadrant": quadrant,
            "word_count": len(excerpt.split()),
            "excerpt": excerpt.strip()
        }
        st.session_state.entries.append(entry)

        # Show live score
        st.markdown(f"""
        <div class="score-card">
            <h4>✓ SCORED — {agent} · {speaker}</h4>
            <div class="metric-row">
                <div class="metric"><div class="val">{int_pct}%</div><div class="lbl">INT</div></div>
                <div class="metric"><div class="val">{aff_pct}%</div><div class="lbl">AFF</div></div>
                <div class="metric"><div class="val">{act_pct}%</div><div class="lbl">ACT</div></div>
                <div class="metric"><div class="val">{s_t}</div><div class="lbl">S_t</div></div>
                <div class="metric"><div class="val">{a_t}</div><div class="lbl">A_t</div></div>
                <div class="metric"><div class="val">{q_t}</div><div class="lbl">Q_t</div></div>
                <div class="metric"><div class="val">{d_t}</div><div class="lbl">D_t</div></div>
                <div class="metric"><div class="val">{r_t}</div><div class="lbl">R_t</div></div>
            </div>
            <span class="quadrant-badge">{quadrant}</span>
            <span class="quadrant-badge" style="background:#1a3020;color:#7fb37f;">Novelty: {novelty_flag}</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("Please paste an excerpt first.")

st.divider()

# ── Current entries ───────────────────────────────────────────────────────────
if st.session_state.entries:
    st.markdown(f"### 📊 {len(st.session_state.entries)} Scored Entries")

    df = pd.DataFrame(st.session_state.entries)

    # Summary by novelty flag
    if "novelty_flag" in df.columns:
        st.markdown("**V_t means by novelty flag:**")
        summary = df.groupby("novelty_flag")[["int_pct","aff_pct","act_pct","S_t","A_t","Q_t","D_t","R_t"]].mean().round(3)
        st.dataframe(summary, use_container_width=True)

    st.markdown("**All entries:**")
    display_cols = ["session_id","agent","speaker","novelty_flag","int_pct","aff_pct","act_pct","S_t","A_t","Q_t","D_t","R_t","quadrant","notes"]
    st.dataframe(df[display_cols], use_container_width=True)

    # Export
    col_a, col_b = st.columns(2)
    with col_a:
        csv_data = df.to_csv(index=False)
        st.download_button(
            "⬇️ Download CSV",
            data=csv_data,
            file_name=f"transcript_scores_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            type="primary"
        )
    with col_b:
        if st.button("🗑️ Clear All Entries"):
            st.session_state.entries = []
            st.rerun()
else:
    st.info("No entries yet — paste an excerpt above and click Score & Add.")

st.divider()
st.caption("SYN-IQ Research · Kouns, W. C. (2026) · SYNINT.AI · CBURZBO 🎹")
