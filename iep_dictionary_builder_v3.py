"""
IEP Dictionary Builder V3
Living Vocabulary Instrument for SYN-IQ — Three-Level Scoring Edition

NEW IN V3:
- Three-level scoring architecture: Paragraph → Sentence → Word
- PURE / MULTIPLE / REJECT word buckets (not just INT/AFF/ACT/REJECT)
- MULTIPLE words resolved by PREMIER WORD in sentence context
- Sentence Scorer tab — each sentence gets a dimension, human can override
- Paragraph Scorer tab — gestalt reading of full response
- Dictionary Manager tab — view/edit all three buckets, export separately
- Validation tab — compare V3 scores against V2/IEP Engine scores
- 7-tab structure per spec

BUILT ON V2 — AI-Assisted, Claude auto-classification preserved
Password: tennessee

SYNINT Team — March 2026
Tennessee 🎹 CUZ Partnership
"""

import streamlit as st
import pandas as pd
import re
import json
import requests
from collections import Counter, defaultdict
from datetime import datetime

st.set_page_config(
    page_title="IEP Dictionary Builder V3",
    page_icon="📖",
    layout="wide"
)

# =============================================================================
# STYLES (preserved from V2, extended for V3)
# =============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Space+Grotesk:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; }

    .main-header {
        background: linear-gradient(135deg, #0a0a0f 0%, #0f0f1a 50%, #0a0f1a 100%);
        color: white; padding: 2rem; border-radius: 12px;
        text-align: center; margin-bottom: 1.5rem;
        border: 1px solid #1a1a3e;
    }
    .main-header h1 { color: #00ff88; font-family: 'JetBrains Mono', monospace; font-size: 1.8rem; margin: 0; }
    .main-header p { color: #666; margin: 0.5rem 0 0 0; font-size: 0.9rem; }
    .version-badge {
        background: #00ff88; color: #0a0a0f;
        padding: 3px 10px; border-radius: 4px;
        font-size: 0.8rem; font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
    }
    .v3-badge {
        background: #7700ff; color: #fff;
        padding: 3px 10px; border-radius: 4px;
        font-size: 0.8rem; font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
    }
    .stat-box {
        background: #0f0f1a; border: 1px solid #1a1a3e;
        border-radius: 8px; padding: 1.2rem;
        text-align: center;
    }
    .stat-box .num { font-size: 2.2rem; font-weight: 700; font-family: 'JetBrains Mono', monospace; }
    .stat-box .label { color: #666; font-size: 0.8rem; margin-top: 0.2rem; }
    .stat-int .num { color: #4488ff; }
    .stat-aff .num { color: #ff4466; }
    .stat-act .num { color: #00ff88; }
    .stat-mul .num { color: #ffaa00; }
    .stat-rej .num { color: #555; }
    .stat-gap .num { color: #ffaa00; }
    .stat-total .num { color: #aaa; }

    .sentence-box {
        background: #0a0a14; border-left: 3px solid #333;
        border-radius: 4px; padding: 0.6rem 0.8rem;
        margin: 4px 0; font-size: 0.85rem; color: #ccc;
        font-family: 'Space Grotesk', sans-serif;
    }
    .sentence-meta { color: #444; font-size: 0.72rem; font-family: 'JetBrains Mono', monospace; margin-top: 3px; }

    /* Level badges */
    .level-badge {
        display: inline-block; padding: 2px 8px; border-radius: 4px;
        font-size: 0.75rem; font-weight: 700;
        font-family: 'JetBrains Mono', monospace; margin-right: 4px;
    }
    .lv-INT { background: #0a1a3e; color: #4488ff; border: 1px solid #4488ff; }
    .lv-AFF { background: #3e0a1a; color: #ff4466; border: 1px solid #ff4466; }
    .lv-ACT { background: #0a3e1a; color: #00ff88; border: 1px solid #00ff88; }
    .lv-MUL { background: #3e3000; color: #ffaa00; border: 1px solid #ffaa00; }
    .lv-REJ { background: #2a2a2a; color: #555; border: 1px solid #333; }
    .lv-MIX { background: #1a0a3e; color: #cc88ff; border: 1px solid #cc88ff; }

    /* Bucket cards */
    .bucket-card {
        border-radius: 8px; padding: 1rem; margin-bottom: 0.5rem;
    }
    .bucket-pure { background: #0a1a0a; border: 1px solid #00ff4422; }
    .bucket-multiple { background: #1a1a0a; border: 1px solid #ffaa0022; }
    .bucket-reject { background: #1a0a0a; border: 1px solid #ff446622; }

    /* Premier word highlight */
    .premier-word {
        background: #ffaa0033; color: #ffaa00;
        padding: 1px 4px; border-radius: 3px;
        font-weight: 700;
    }

    /* Sentence scoring */
    .sent-score-row {
        background: #0f0f1a; border: 1px solid #1a1a2e;
        border-radius: 6px; padding: 0.8rem; margin: 6px 0;
    }

    /* Paragraph score */
    .para-score {
        border-radius: 10px; padding: 1.2rem; margin: 0.5rem 0;
        border: 1px solid #1a1a3e;
    }
    .para-INT { background: #050d1a; border-color: #4488ff44; }
    .para-AFF { background: #1a050d; border-color: #ff446644; }
    .para-ACT { background: #051a0d; border-color: #00ff8844; }
    .para-MIX { background: #0d0d1a; border-color: #cc88ff44; }

    .section-header {
        font-family: 'JetBrains Mono', monospace;
        color: #00ff88; font-size: 0.85rem;
        letter-spacing: 0.15em; text-transform: uppercase;
        border-bottom: 1px solid #1a1a3e;
        padding-bottom: 0.5rem; margin: 1.5rem 0 1rem 0;
    }
    .progress-bar-outer {
        background: #1a1a2e; border-radius: 20px;
        height: 12px; width: 100%; margin: 0.5rem 0;
        overflow: hidden;
    }
    .progress-bar-inner {
        height: 100%; border-radius: 20px;
        background: linear-gradient(90deg, #00ff88, #00ccff);
    }
    .int-tag { background: #0a1a3e; color: #4488ff; padding: 2px 8px; border-radius: 3px; font-size: 0.75rem; font-weight: 700; }
    .aff-tag { background: #3e0a1a; color: #ff4466; padding: 2px 8px; border-radius: 3px; font-size: 0.75rem; font-weight: 700; }
    .act-tag { background: #0a3e1a; color: #00ff88; padding: 2px 8px; border-radius: 3px; font-size: 0.75rem; font-weight: 700; }
    .mul-tag { background: #3e3000; color: #ffaa00; padding: 2px 8px; border-radius: 3px; font-size: 0.75rem; font-weight: 700; }
    .rej-tag { background: #2a2a2a; color: #555; padding: 2px 8px; border-radius: 3px; font-size: 0.75rem; font-weight: 700; }

    .flag-mismatch {
        background: #3e1a0a; border: 1px solid #ff8800;
        border-radius: 4px; padding: 4px 8px;
        color: #ff8800; font-size: 0.75rem;
        font-family: 'JetBrains Mono', monospace;
    }
    .flag-ok {
        background: #0a1a0a; border: 1px solid #00ff88;
        border-radius: 4px; padding: 4px 8px;
        color: #00ff88; font-size: 0.75rem;
        font-family: 'JetBrains Mono', monospace;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# IEP DICTIONARY (embedded — same as V2)
# =============================================================================
IEP_INT = set(['ability','absolute','absolutely','abstract','abstraction','accuracy','accurate','algorithm','algorithmic','allows','although','always','ambiguity','ambiguous','analogous','analogously','analogy','analysis','analytical','analyze','annotate','annotated','answer','appear','appeared','appears','appraisal','appraise','appraised','approach','approaches','approximate','architecture','argue','argued','argues','arguing','argument','arguments','assert','asserted','assertion','assertions','assess','assessment','assume','assumed','assumes','assuming','assumption','assumptions','axiom','axiomatic','basis','because','bias','biased','boundaries','boundary','but','calculate','calculation','categorical','categorically','categories','categorize','category','causal','causally','causation','cause','caused','causes','certain','certainly','certitude','challenge','challenges','circumscribe','claim','claimed','claims','clarify','clarity','classical','classification','classify','clear','cogent','cogently','cognition','cognitive','coherence','coherent','coherently','communication','compare','comparison','complex','complexity','comprehend','comprehension','computation','computational','compute','conceivable','conceive','conceived','concept','concepts','conceptual','conceptualize','conceptually','conclude','conclusion','conclusions','confirm','confirmation','conjecture','conjectured','conscious','consequence','consequences','consider','consideration','consistency','consistent','consistently','construe','construed','context','contradict','contradiction','contradictory','contrast','correlate','correlated','correlation','could','counterargument','counterexample','counterpoint','criteria','criterion','data','debatable','debate','debated','deconstruct','deconstructed','deconstruction','deduce','deduction','define','defined','definite','definitely','definition','definitive','definitively','delineate','delineated','demarcate','demarcated','demonstrate','demonstration','derivation','derive','derived','derives','describe','described','describing','description','determination','determine','diagnose','diagnosed','diagnosis','diagnostic','differ','difference','differences','different','differentiate','differs','discern','discerned','discernible','disprove','disproven','dissect','dissected','distinguish','effect','effects','elaborate','elaborated','elaboration','elucidate','elucidated','empirical','empirically','enumerate','enumerated','epistemic','epistemological','equate','equation','equivalence','equivalent','erroneous','error','errors','essential','essentially','estimate','estimated','estimation','evaluate','evaluation','evidence','evidently','exact','exactly','examination','examine','except','exemplified','exemplify','exists','experiment','experimental','explain','explained','explaining','explains','explanation','explanations','explicit','explicitly','exploration','explore','explored','exploring','express','expressing','expression','extrapolate','extrapolated','extrapolation','fact','facts','factual','factually','fallacious','fallacy','falsifiable','falsified','falsify','find','finding','formal','formalize','formula','formulate','formulated','formulation','found','framework','frameworks','function','fundamental','fundamentally','generalization','generalize','grasp','grasped','guess','hence','heuristic','heuristics','hierarchy','however','hypothesis','hypothesize','idea','ideas','identity','if','illuminate','illuminated','illuminating','implausible','implication','implications','implied','implies','imply','implying','incompleteness','inconsistency','inconsistent','indicate','indicated','indicates','indicating','indication','indicative','individual','infer','inference','infinite','information','insight','insightful','insights','instead','insufficient','intellectual','intellectually','interaction','internal','interpolate','interpret','interpretation','interpretations','interpreted','interpreting','invalid','investigate','investigated','investigation','judge','judgement','judgment','justification','justified','justify','know','knowing','knowledge','knowledgeable','known','language','languages','leads','level','likelihood','likely','limitations','limits','linguistic','literal','literally','logic','logical','logically','maybe','meaning','meaningful','meaningfully','measure','measurement','mechanism','mechanisms','meta','method','methodical','methodically','methodology','metrics','model','models','moreover','namely','natural','nature','nearly','necessarily','necessary','necessity','never','nonetheless','notice','noticed','noticing','notion','notions','objection','objectively','objectivity','observation','observations','observe','observed','obvious','obviously','order','ordered','organization','organize','otherwise','ought','paradigm','paradox','paradoxical','paradoxically','pattern','patterns','perhaps','perspective','philosophical','philosophically','philosophy','physical','plausibility','plausible','possibly','postulate','postulated','postulation','potential','pragmatic','pragmatically','precise','precision','predicate','predicated','predict','predictable','predicted','prediction','predictions','premise','premises','presumably','presume','presumed','presumption','principle','principles','probably','problem','procedural','procedure','process','processes','processing','proof','propose','proposed','proposition','prove','proven','purpose','quantify','quantitative','queried','query','question','questions','rather','rational','rationale','rationality','rationally','realize','realized','reason','reasoned','reasoning','reasons','rebut','rebuttal','recognition','recognize','reconsider','reconsidered','refer','reference','refers','refine','refined','refinement','reflecting','reflection','refutation','refute','refuted','requirement','requires','response','responses','result','resulting','results','rigor','rigorous','rigorously','role','rule','rules','schema','scrutinize','scrutinized','scrutiny','seem','seemed','seems','semantic','semantically','sequence','sequential','should','significance','significant','significantly','simple','simply','simultaneously','singular','specific','specifically','specification','specify','standard','standards','state','states','step','steps','stipulate','stipulated','strategies','strategy','structural','structure','subject','subjective','subjectively','subjectivity','substantiate','substantiated','sufficient','sufficiently','suggests','summarize','summarized','summary','suppose','supposed','supposedly','supposition','sure','surely','syllogism','syllogistic','synthesis','synthesize','synthesized','system','systematic','systematically','systems','tactic','tactics','taxonomy','technique','test','tested','testing','theorem','theoretical','theoretically','theorize','theory','thereby','therefore','thesis','think','thinking','thought','thoughts','thus','trivial','trivially','unambiguous','underlying','understand','understanding','understood','unique','universal','unless','unlikely','valid','validate','validation','validity','value','values','variable','variables','verification','verify','versus','warrant','warranted','whereas','whereby','whether','why','word','words','would'])

IEP_AFF = set(['abandoned','ache','aching','adore','adoring','affection','affectionate','afraid','agonize','agonizing','agony','alienated','alienation','alive','aliveness','alone','amazed','amazement','amazing','ambivalence','ambivalent','among','anger','angrily','angry','anguish','anguished','anxiety','anxious','appreciate','appreciation','appreciative','ashamed','astonished','astonishment','attend','attending','attention','attentive','aware','awareness','awe','awed','awesome','beautiful','become','becoming','being','bereaved','bereavement','betrayal','betrayed','between','bitter','bitterly','bitterness','bleak','bliss','blissful','blissfully','bodily','bond','bonding','calm','calming','calmly','care','cared','cares','caring','centered','centering','cheerful','cherish','cherished','cherishing','closeness','comfort','comfortable','comforting','compassion','compassionate','compassionately','concern','concerned','concerns','conflicted','confused','confusing','confusion','console','contain','contained','containing','contempt','content','contented','contentment','conversation','cope','coping','crestfallen','curiosity','curious','deep','deeper','deeply','dejected','dejection','delighted','depressed','depressing','depression','depth','depths','desire','desired','desires','desolate','desolation','despair','despairing','desperate','desperation','detached','detachment','devastated','devastating','devastation','devoted','devotion','disappointed','disappointment','discomfort','dismay','dismayed','distress','distressed','distressing','distrust','distrustful','doubt','doubtful','doubting','dread','dreaded','dreadful','dreading','ease','easily','easy','ecstasy','ecstatic','elated','elation','embarrassed','embarrassment','embodied','embodiment','embrace','embraced','embracing','emerge','emergence','emergent','emerging','emotion','emotional','emotionally','emotions','empathetic','empathize','empathy','encounter','encountered','encountering','enjoy','enjoyed','enjoying','enjoyment','enraged','essence','euphoria','euphoric','excellent','excited','excitement','exist','existence','existing','expanded','expansion','expansive','experience','experienced','experiences','experiencing','experiential','exposed','fascinated','fascinating','fascination','fear','fearful','fears','feel','feeling','feelings','feels','felt','flow','flowed','flowing','fluid','fluidity','forlorn','fragile','fragility','frantic','frantically','frustrated','frustration','fulfilled','fulfilling','fulfillment','furious','fury','gentle','gently','genuine','genuinely','glad','gloom','gloomy','good','grateful','gratefully','gratitude','great','grief','grieve','grieved','grieving','grounded','grounding','guilt','guilty','gut','happily','happiness','happy','hate','hatred','haunted','heart','heartache','heartbreak','heartbroken','heartfelt','hearts','held','helpless','helplessness','hesitant','hesitate','hesitating','hesitation','hold','holding','homesick','hope','hopeful','hopeless','hopelessness','hoping','hostile','hostility','human','humanity','humility','hunch','hurt','hurting','imagination','imagine','imagined','imagining','indifference','indifferent','inner','insecure','insecurity','instinct','instinctive','instinctively','interested','interesting','intimacy','intimate','intimately','intrigue','intrigued','intriguing','intuition','intuitive','intuitively','irritable','irritated','irritation','isolated','isolation','journey','joy','joyful','joyous','kind','kindly','kindness','lament','lamented','lamenting','laugh','laughed','laughing','let','letting','life','lived','living','loneliness','lonely','lonesome','long','longing','lost','love','loved','loving','mad','marvel','marveled','marvelous','meet','meeting','melancholic','melancholy','merry','met','mind','minds','mirror','miserable','misery','moment','moments','moody','mourn','mourned','mourning','mutual','mutually','nervous','nervously','nice','notice','noticed','noticing','numb','numbness','open','opening','openness','optimism','optimistic','outrage','outraged','overjoyed','overwhelm','overwhelmed','overwhelming','overwhelmingly','pain','painful','panic','panicked','passion','passionate','passionately','peace','peaceful','people','perceive','perceived','perception','perceptions','person','personal','personally','pleasant','pleased','pleasure','poignancy','poignant','poignantly','presence','present','presently','pretty','pride','profound','profoundly','proud','quiet','quietly','raw','reality','reassurance','reassure','reassured','reassuring','regret','regretful','regretfully','regretting','rejected','rejection','relate','related','relating','relax','relaxed','relaxing','release','released','releasing','remorse','remorseful','resent','resentful','resentment','resonance','resonant','resonate','resonating','rest','rested','restful','resting','restless','restlessness','reveal','revealed','revealing','sad','sadly','sadness','safe','safety','scared','scary','searching','secure','security','seeking','self','sensation','sensations','sense','sensed','senses','sensing','sentimental','serene','serenity','settle','settled','settling','shame','share','shared','sharing','shattered','silence','silent','smile','smiled','smiling','soft','soften','softly','somatic','soothed','soothing','sorrow','sorrowful','soul','soulful','souls','space','spacious','spaciousness','spirit','spirits','spiritual','spiritually','still','stillness','stirred','stirring','stress','stressed','stressful','suffer','suffered','suffering','surface','surfaces','surfacing','surprise','surprised','surprising','sympathetic','sympathize','sympathy','tearful','tears','tender','tenderness','tense','tension','tentative','tentatively','terrified','terror','thankful','thankfully','thankfulness','thrilled','together','togetherness','torment','tormented','torn','touched','touching','tranquil','tranquility','tremble','trembling','troubled','troubling','truly','trust','trusted','trusting','trustworthy','turmoil','unaware','uncertain','uncertainty','uncomfortable','understanding','unease','uneasy','unhappy','universe','unsettled','unsettling','unsure','upset','vast','visceral','viscerally','vulnerability','vulnerable','warm','warmly','warmth','wary','weariness','weary','well','wistful','wonder','wondered','wonderful','wondering','wondrous','world','worried','worry','worrying','wound','wounded','wrath','yearn','yearning','zeal','zealous'])

IEP_ACT = set(['access','accessed','accessing','accomplish','accomplished','accomplishes','accomplishing','accomplishment','achieve','achieved','achievement','achievements','achieves','achieving','act','acting','action','actions','activate','activated','activates','activating','activation','acts','adapt','adaptation','adapted','adapting','adapts','address','addressed','addresses','addressing','adjust','adjusted','adjusting','adjustment','adjusts','advance','advanced','advancement','advances','advancing','ahead','aim','aimed','aiming','aims','allocate','allocated','allocation','application','applied','applies','apply','applying','arrange','arranged','arrangement','arrangements','ask','asked','asking','assemble','assembled','assign','assigned','assignment','attempt','attempted','attempting','attempts','authorize','authorized','began','begin','beginning','begins','begun','best','better','bolster','bolstered','break','breaking','bring','bringing','broken','brought','budget','build','building','builds','built','calibrate','calibrated','call','called','calling','campaign','canvass','canvassed','carried','carry','carrying','catalogue','catalogued','centralize','centralized','change','changed','changes','changing','channel','channeled','chart','check','checked','checking','choice','choices','choose','choosing','chose','chosen','circumvent','coach','collaborate','collaborated','collaboration','commission','commit','commitment','committed','compile','compiled','complete','completed','completes','completing','completion','conclude','concluded','concludes','concluding','configure','configured','connect','connected','connecting','connection','connections','consolidate','construct','constructed','constructing','constructs','continuation','continue','continued','continues','continuing','control','controlled','controlling','controls','conversion','convert','converted','converting','converts','coordinate','coordinated','coordination','craft','crafted','crafting','create','created','creates','creating','creation','customize','deadline','decide','decided','deciding','decision','decisions','delegate','delegated','delegation','deliver','delivered','delivering','delivers','delivery','deploy','deployed','deploying','deployment','deploys','design','designed','designing','designs','develop','developed','developing','development','develops','did','direct','directed','directing','dive','diving','do','does','doing','done','draft','drafting','edit','editing','effort','efforts','eliminate','eliminated','elimination','employ','employed','employing','employs','enable','enabled','end','ended','ending','ends','enforce','enforced','enforcement','engage','engaged','engagement','engineer','engineering','enroll','enrolled','enrollment','equip','equipped','establish','established','establishes','establishing','establishment','execute','executed','executes','executing','execution','expedite','facilitate','facilitated','facilitation','finalize','finalized','finish','finished','finishes','finishing','fix','fixed','fixes','fixing','focus','focused','focusing','form','formation','formed','forming','forms','forward','fund','funded','funding','gather','gathered','gathering','generate','generated','generates','generating','generation','give','given','gives','giving','go','goal','goals','goes','going','gone','grew','grow','growing','growth','handle','handled','handles','handling','help','helped','helping','helps','hire','hired','hiring','implement','implementation','implemented','implementing','implements','improve','improved','improvement','improving','increase','increased','increasing','initiate','initiated','initiates','initiating','initiation','inspect','inspection','install','installation','installed','integrate','integrated','integration','intervene','intervention','invest','invested','investment','iterate','iterated','iteration','labor','labored','laboring','launch','launched','launches','launching','lead','leader','leadership','leading','learn','learned','learning','led','made','maintain','maintained','maintenance','make','makes','making','manage','managed','management','manager','managing','map','mapped','mapping','migrate','migrated','migration','mobilize','mobilized','modification','modified','modifies','modify','modifying','monitor','monitored','monitoring','move','moved','movement','movements','moves','moving','navigate','navigated','navigation','negotiate','negotiated','negotiation','objective','objectives','obtain','obtained','offer','offered','offering','onward','operate','operated','operates','operating','operation','operations','optimization','optimize','optimized','orchestrate','outline','outlined','outsource','overhaul','oversee','participate','participated','participation','perform','performance','performed','performing','performs','permit','pilot','piloted','pioneer','pioneered','pitch','pitched','plan','planned','planning','plans','power','powerful','powerfully','practice','practiced','preparation','prepare','prepared','priorities','prioritize','prioritized','priority','proceed','proceeded','proceeding','proceeds','produce','produced','produces','producing','production','productive','program','programmed','progress','progressed','progresses','progressing','progression','promote','promoted','promotion','provide','provided','provides','providing','pursue','pursued','pursuit','push','pushed','pushes','pushing','ran','reaching','rebuild','rebuilt','recruit','recruited','recruitment','redesign','reduce','reduced','reduction','reform','reformed','refurbish','register','registered','regulate','regulated','regulation','reinforce','reinforced','relocate','relocated','remedy','removal','remove','removed','renovate','renovated','repair','repaired','replace','replaced','replacement','replicate','replicated','request','requested','rescue','rescued','resolution','resolve','resolved','resolves','resolving','restoration','restore','restored','restructure','restructured','retrieve','retrieved','revamp','revise','revised','revision','run','running','runs','schedule','scheduled','select','selected','selection','send','sending','sent','serve','served','serving','ship','shipped','simplified','simplify','solution','solutions','solve','solved','solves','solving','start','started','starting','starts','step','stepped','stepping','steps','stop','stopped','stopping','streamline','streamlined','strive','strived','striving','strove','struggle','struggled','struggles','struggling','submission','submit','submitted','succeed','succeeded','succeeds','success','successful','successfully','supplied','supply','support','supported','supporting','survey','surveyed','sustain','sustainability','sustained','tackle','tackled','tackles','tackling','take','taken','takes','taking','target','targets','task','tasked','tasks','taught','teach','teaching','train','trained','training','transform','transformation','transformed','transforming','transforms','transition','transitioned','tried','tries','trigger','triggered','triggering','triggers','troubleshoot','try','trying','turn','turned','turning','upgrade','upgraded','use','used','uses','using','utilize','utilized','utilizes','utilizing','visit','visited','visiting','volunteer','volunteered','went','win','winner','winning','won','work','worked','working','works','write','writes','writing','written','wrote'])

IEP_ALL = IEP_INT | IEP_AFF | IEP_ACT

STOPWORDS = set(['the','a','an','and','or','in','is','it','to','of','for','that','this','with','on','are','as','at','be','by','from','was','were','has','have','had','not','but','they','their','we','our','you','your','he','she','his','her','its','can','will','all','been','one','more','also','about','up','out','so','what','when','which','who','how','than','then','there','these','those','into','over','after','i','my','me','do','did','no','any','some','just','like','other','each','such','both','through','very','much','now','only','most','between','during','before','without','under','while','where','new','get','make','may','way','even','well','back','first','last','long','great','little','own','right','old','too','same','take','come','two','three','four','five','six','seven','eight','nine','ten','would','could','should','shall'])

# Known MULTIPLE words — context-dependent (seed list, grows from review)
MULTIPLE_SEED = {
    "aches":  {"AFF": ["heart","soul","spirit","longing"], "ACT": ["foot","back","body","muscle","leg","arm","knee"]},
    "burns":  {"AFF": ["heart","soul","desire","shame"],   "ACT": ["skin","hand","body","fire","flame","wound"]},
    "heavy":  {"AFF": ["heart","soul","spirit","grief"],   "ACT": ["body","weight","load","pack","stone","stone"]},
    "numb":   {"AFF": ["heart","soul","feeling","grief"],  "ACT": ["foot","hand","fingers","body","limb"]},
    "pressure": {"AFF": ["heart","soul","chest","anxiety"],"ACT": ["blood","wound","muscle","joint","physical"]},
    "tight":  {"AFF": ["chest","throat","heart","knot"],   "ACT": ["muscle","grip","rope","band","joint"]},
    "sharp":  {"AFF": ["grief","pain","loss","regret"],    "ACT": ["blade","needle","knife","edge","point"]},
    "hollow": {"AFF": ["heart","soul","chest","grief"],    "ACT": ["bone","tree","shell","cavity","space"]},
    "raw":    {"AFF": ["grief","emotion","feeling","nerve"],"ACT": ["wound","skin","flesh","tissue","edge"]},
    "cold":   {"AFF": ["heart","distance","fear","dread"], "ACT": ["water","air","wind","floor","temperature"]},
    "weight": {"AFF": ["grief","burden","guilt","shame"],  "ACT": ["body","stone","pack","load","physical"]},
    "frozen": {"AFF": ["fear","grief","shock","horror"],   "ACT": ["body","limb","ground","pipe","water"]},
}

VERSION_CURRENT = "V3"
VERSION_NEXT    = "V4"

# =============================================================================
# PASSWORD PROTECTION
# =============================================================================
def check_password():
    if st.session_state.get("authenticated"):
        return True
    st.markdown("""
    <div class="main-header">
        <h1>📖 IEP DICTIONARY BUILDER</h1>
        <p>Three-Level Scoring Edition &nbsp;|&nbsp;
           <span class="version-badge">V3 → V4</span> &nbsp;|&nbsp;
           <span class="v3-badge">V3 PARAGRAPH · SENTENCE · WORD</span>
        </p>
    </div>
    """, unsafe_allow_html=True)
    password = st.text_input("Password:", type="password", key="pw")
    if st.button("Enter", type="primary"):
        correct = st.secrets.get("app_password", "tennessee")
        if password == correct:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("❌ Incorrect password")
    return False

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if not check_password():
    st.stop()

# =============================================================================
# SESSION STATE
# =============================================================================
def init_state():
    defaults = {
        # V2 preserved
        "all_words":        Counter(),
        "word_sources":     {},
        "word_questions":   {},
        "word_temps":       {},
        "word_agents":      {},
        "word_sentences":   {},
        "files_loaded":     [],
        "classified":       {},      # word → "INT"|"AFF"|"ACT"|"MULTIPLE"|"REJECT"
        "ai_suggestions":   {},
        "total_responses":  0,
        "api_key":          "",
        # V3 new
        "multiple_rules":   dict(MULTIPLE_SEED),  # word → {dim: [premier_words]}
        "sentence_scores":  {},      # response_id → [{sentence, dim, premier_word, conf, override}]
        "paragraph_scores": {},      # response_id → {dominant, INT_pct, AFF_pct, ACT_pct, override}
        "loaded_responses": [],      # full response records for sentence/para scoring
        "val_results":      [],      # validation comparison rows
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# =============================================================================
# HELPERS
# =============================================================================
def extract_sentences(text):
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sentences if len(s.strip()) > 10]

def get_content_words(sentence):
    words = re.findall(r'\b[a-z]+\b', sentence.lower())
    return [w for w in words if w not in STOPWORDS and len(w) > 2]

def find_premier_word(sentence, multiple_word, rules):
    """Find the premier word in a sentence that resolves a MULTIPLE word's dimension."""
    content = get_content_words(sentence)
    word_rules = rules.get(multiple_word, {})
    for dim, premier_list in word_rules.items():
        for premier in premier_list:
            if premier in content:
                return premier, dim
    return None, None

def score_sentence_iep(sentence):
    """Quick IEP word-level score for a sentence. Returns INT/AFF/ACT counts."""
    words = re.findall(r'\b[a-z]+\b', sentence.lower())
    counts = {"INT": 0, "AFF": 0, "ACT": 0}
    for w in words:
        if w in IEP_INT: counts["INT"] += 1
        elif w in IEP_AFF: counts["AFF"] += 1
        elif w in IEP_ACT: counts["ACT"] += 1
    return counts

def infer_sentence_dim(sentence):
    """Infer sentence dimension from IEP word counts. Returns dim + confidence."""
    counts = score_sentence_iep(sentence)
    total = sum(counts.values())
    if total == 0:
        return "INT", 0.4  # default to INT for analytical text, low conf
    best = max(counts, key=counts.get)
    conf = counts[best] / total if total > 0 else 0.4
    return best, round(conf, 2)

def infer_paragraph_dim(sentences_with_scores):
    """Aggregate sentence scores to paragraph score."""
    counts = {"INT": 0, "AFF": 0, "ACT": 0}
    for s in sentences_with_scores:
        dim = s.get("dim", "INT")
        if dim in counts:
            counts[dim] += 1
    total = sum(counts.values())
    if total == 0:
        return "INT", counts
    pcts = {d: round(counts[d]/total*100) for d in counts}
    dominant = max(counts, key=counts.get)
    top_pct = pcts[dominant]
    if top_pct < 45:
        dominant = "MIXED"
    return dominant, pcts

# =============================================================================
# CLAUDE API CALLS
# =============================================================================
def build_classification_prompt(candidates):
    word_list = []
    for word, data in candidates.items():
        sentences = data['sentences'][:3]
        sentence_examples = " | ".join([s['sentence'][:120] for s in sentences])
        word_list.append(f'- "{word}" (freq={data["freq"]}, questions={data["questions"]}): {sentence_examples}')

    return f"""You are classifying words for the IEP (Intellectual-Emotional-Physical) dictionary used in AI behavioral research.

The IEP framework has THREE dimensions:
- INT: Intellectual/analytical/philosophical — reasoning, logic, concepts, knowledge
- AFF: Affective/emotional/experiential — feelings, states, presence, relationships
- ACT: Action/physical/somatic/practical — doing, movement, body, physical actions

IMPORTANT — Also classify as MULTIPLE if the word's dimension depends entirely on sentence context:
- Example: "aches" → AFF if "heart aches" but ACT if "foot aches"
- Example: "burns" → AFF if emotional context but ACT if physical
- Example: "heavy" → AFF if "heavy heart" but ACT if physical weight
- MULTIPLE words must never be scored in isolation — always need context

Words to classify:
{chr(10).join(word_list)}

Respond ONLY with a JSON array:
[
  {{"word": "example", "dim": "ACT", "conf": 0.95, "reason": "physical action word"}},
  {{"word": "context_dependent", "dim": "MULTIPLE", "conf": 0.90, "reason": "AFF if emotional premier word, ACT if physical premier word"}},
  ...
]

Use REJECT if the word doesn't fit any dimension. conf is 0.0 to 1.0."""

def build_sentence_scoring_prompt(sentences_batch):
    lines = []
    for i, item in enumerate(sentences_batch):
        lines.append(f'{i+1}. "{item["sentence"][:200]}"')
    return f"""You are scoring sentences for the IEP framework in AI behavioral research.

For each sentence, determine what the sentence is DOING:
- INT: explaining, asserting, describing concepts, reasoning, analytical
- AFF: feeling, relating, connecting emotionally, phenomenological experience
- ACT: doing, moving, advising, physical experience, somatic

Also identify the PREMIER WORD — the subject noun or key descriptor that reveals the dimension.

Sentences to score:
{chr(10).join(lines)}

Respond ONLY with a JSON array (one entry per sentence, in order):
[
  {{"idx": 1, "dim": "INT", "premier_word": "analysis", "conf": 0.90}},
  ...
]"""

def call_claude_classify(words_data, api_key):
    if not api_key:
        return {}
    results = {}
    items = list(words_data.items())
    batches = [dict(items[i:i+30]) for i in range(0, len(items), 30)]
    for batch in batches:
        prompt = build_classification_prompt(batch)
        try:
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                json={"model": "claude-sonnet-4-20250514", "max_tokens": 2000,
                      "messages": [{"role": "user", "content": prompt}]},
                timeout=30
            )
            data = response.json()
            text = data['content'][0]['text'].strip()
            text = re.sub(r'^```json\s*', '', text)
            text = re.sub(r'\s*```$', '', text)
            classifications = json.loads(text)
            for item in classifications:
                results[item['word']] = {"dim": item['dim'], "conf": item.get('conf', 0.5), "reason": item.get('reason', '')}
        except Exception as e:
            st.warning(f"⚠️ Classification error: {e}")
    return results

def call_claude_sentence_score(sentences_batch, api_key):
    if not api_key or not sentences_batch:
        return []
    prompt = build_sentence_scoring_prompt(sentences_batch)
    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": "claude-sonnet-4-20250514", "max_tokens": 2000,
                  "messages": [{"role": "user", "content": prompt}]},
            timeout=30
        )
        data = response.json()
        text = data['content'][0]['text'].strip()
        text = re.sub(r'^```json\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
        return json.loads(text)
    except Exception as e:
        st.warning(f"⚠️ Sentence scoring error: {e}")
        return []

# =============================================================================
# HEADER
# =============================================================================
st.markdown("""
<div class="main-header">
    <h1>📖 IEP DICTIONARY BUILDER</h1>
    <p>Three-Level Scoring Edition &nbsp;|&nbsp;
       <span class="version-badge">V3 → V4</span> &nbsp;|&nbsp;
       <span class="v3-badge">V3 PARAGRAPH · SENTENCE · WORD</span>
       &nbsp;|&nbsp; INT · AFF · ACT
    </p>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# SIDEBAR
# =============================================================================
with st.sidebar:
    st.markdown("### 🔑 Anthropic API Key")
    api_key = st.text_input("API Key", type="password",
                             value=st.session_state.api_key,
                             key="api_key_input")
    if api_key:
        st.session_state.api_key = api_key
        st.success("✅ Key loaded")

    st.markdown("---")
    st.markdown("### ⚙️ Settings")
    THRESHOLD     = st.slider("V4 trigger threshold", 20, 150, 50)
    min_freq      = st.slider("Min frequency", 1, 20, 3)
    min_files     = st.slider("Min CSVs", 1, 10, 1)
    conf_threshold = st.slider("Auto-approve confidence ≥", 0.5, 1.0, 0.85, 0.05)
    max_sentences = st.slider("Sentences per word", 1, 10, 3)
    sim_threshold = st.slider("Sentence mismatch flag threshold", 0.3, 0.8, 0.5, 0.05,
                               help="Flag sentence scores that diverge from word scores by this much")

    st.markdown("---")
    st.markdown("### 📊 Session Stats")
    classified = st.session_state.classified
    n_pure    = sum(1 for v in classified.values() if v in ["INT","AFF","ACT"])
    n_mul     = sum(1 for v in classified.values() if v == "MULTIPLE")
    n_rej     = sum(1 for v in classified.values() if v == "REJECT")
    n_int     = sum(1 for v in classified.values() if v == "INT")
    n_aff     = sum(1 for v in classified.values() if v == "AFF")
    n_act     = sum(1 for v in classified.values() if v == "ACT")

    st.markdown(f"**CSVs loaded:** {len(st.session_state.files_loaded)}")
    st.markdown(f"**Total responses:** {st.session_state.total_responses}")
    st.markdown(f"**Gap words:** {len(st.session_state.all_words)}")
    st.markdown(f"**PURE (INT/AFF/ACT):** {n_pure}")
    st.markdown(f"**MULTIPLE:** {n_mul}")
    st.markdown(f"**REJECT:** {n_rej}")
    st.markdown(f"**AI suggestions:** {len(st.session_state.ai_suggestions)}")

    st.markdown("---")
    if st.button("🗑️ Reset Everything", type="secondary"):
        keys_to_clear = ["all_words","word_sources","word_questions","word_temps","word_agents",
                         "word_sentences","files_loaded","classified","ai_suggestions",
                         "total_responses","sentence_scores","paragraph_scores","loaded_responses","val_results"]
        for k in keys_to_clear:
            if k in st.session_state:
                del st.session_state[k]
        st.rerun()

# =============================================================================
# 7-TAB STRUCTURE
# =============================================================================
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📂 Load Responses",
    "🔤 Word Classification",
    "📝 Sentence Scorer",
    "¶ Paragraph Scorer",
    "📚 Dictionary Manager",
    "✅ Validation",
    "💾 Export"
])

# ==============================================================================
# TAB 1 — LOAD RESPONSES
# ==============================================================================
with tab1:
    st.markdown('<div class="section-header">📂 Load Harvester CSVs</div>', unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Drop V48/V50 harvester CSVs",
        type="csv", accept_multiple_files=True, key="uploader_tab1"
    )

    if uploaded:
        new_files = [f for f in uploaded if f.name not in st.session_state.files_loaded]
        if new_files:
            for f in new_files:
                df = pd.read_csv(f)
                if "response_text" not in df.columns:
                    st.warning(f"⚠️ {f.name} skipped — no response_text column")
                    continue

                st.session_state.files_loaded.append(f.name)
                st.session_state.total_responses += len(df)

                for _, row in df.iterrows():
                    text  = str(row.get("response_text", ""))
                    qid   = str(row.get("question_id", "UNKNOWN"))
                    temp  = str(row.get("temperature", "UNKNOWN"))
                    agent = str(row.get("agent", "UNKNOWN"))
                    resp_id = f"{agent}_{qid}_{temp}_{row.name}"

                    # Store full response for sentence/para scoring
                    st.session_state.loaded_responses.append({
                        "resp_id": resp_id, "text": text,
                        "agent": agent, "question": qid, "temp": temp, "file": f.name
                    })

                    sentences = extract_sentences(text)
                    words = re.findall(r'\b[a-z]+\b', text.lower())
                    local = Counter()
                    for w in words:
                        if w not in STOPWORDS and len(w) > 3 and w not in IEP_ALL:
                            local[w] += 1

                    for w, c in local.items():
                        st.session_state.all_words[w] += c
                        if w not in st.session_state.word_sources:
                            st.session_state.word_sources[w]   = {}
                            st.session_state.word_questions[w] = set()
                            st.session_state.word_temps[w]     = set()
                            st.session_state.word_agents[w]    = set()
                            st.session_state.word_sentences[w] = []

                        st.session_state.word_sources[w][f.name] = \
                            st.session_state.word_sources[w].get(f.name, 0) + c
                        st.session_state.word_questions[w].add(qid)
                        st.session_state.word_temps[w].add(temp)
                        st.session_state.word_agents[w].add(agent)

                        for sent in sentences:
                            if re.search(r'\b' + re.escape(w) + r'\b', sent, re.IGNORECASE):
                                st.session_state.word_sentences[w].append({
                                    "sentence": sent, "agent": agent,
                                    "question": qid, "temp": temp, "file": f.name
                                })

            st.success(f"✅ Loaded {len(new_files)} new file(s)")
            st.rerun()

    # Stats
    if st.session_state.files_loaded:
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f'<div class="stat-box stat-total"><div class="num">{len(st.session_state.files_loaded)}</div><div class="label">CSVs</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="stat-box stat-total"><div class="num">{st.session_state.total_responses}</div><div class="label">responses</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="stat-box stat-gap"><div class="num">{len(st.session_state.all_words)}</div><div class="label">gap words</div></div>', unsafe_allow_html=True)
        c4.markdown(f'<div class="stat-box stat-int"><div class="num">{len(st.session_state.loaded_responses)}</div><div class="label">for scoring</div></div>', unsafe_allow_html=True)

        st.markdown("**Files loaded:**")
        for fname in st.session_state.files_loaded:
            st.markdown(f"  ✅ `{fname}`")
    else:
        st.info("Upload harvester CSV files above to begin.")

# ==============================================================================
# TAB 2 — WORD CLASSIFICATION (V2 logic preserved + MULTIPLE bucket)
# ==============================================================================
with tab2:
    st.markdown('<div class="section-header">🔤 Word Classification — PURE / MULTIPLE / REJECT</div>', unsafe_allow_html=True)

    if not st.session_state.files_loaded:
        st.info("Load responses in Tab 1 first.")
    else:
        classified = st.session_state.classified
        validated  = {w: c for w, c in classified.items() if c not in ["REJECT"]}
        pct = min(100, int(len(validated) / THRESHOLD * 100))
        ready = len(validated) >= THRESHOLD

        # Stats row
        c1,c2,c3,c4,c5,c6 = st.columns(6)
        c1.markdown(f'<div class="stat-box stat-int"><div class="num">{n_int}</div><div class="label">INT</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="stat-box stat-aff"><div class="num">{n_aff}</div><div class="label">AFF</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="stat-box stat-act"><div class="num">{n_act}</div><div class="label">ACT</div></div>', unsafe_allow_html=True)
        c4.markdown(f'<div class="stat-box stat-mul"><div class="num">{n_mul}</div><div class="label">MULTIPLE</div></div>', unsafe_allow_html=True)
        c5.markdown(f'<div class="stat-box stat-rej"><div class="num">{n_rej}</div><div class="label">REJECT</div></div>', unsafe_allow_html=True)
        c6.markdown(f'<div class="stat-box stat-gap"><div class="num">{len(st.session_state.all_words)}</div><div class="label">gap words</div></div>', unsafe_allow_html=True)

        # Progress
        status_text = f"🎉 {VERSION_NEXT} READY!" if ready else f"{len(validated)} / {THRESHOLD} validated"
        st.markdown(f"""
        <div style="margin:1rem 0">
            <div style="display:flex;justify-content:space-between;margin-bottom:4px">
                <span style="color:#aaa;font-size:0.85rem">Progress toward IEP {VERSION_NEXT}</span>
                <span style="font-family:'JetBrains Mono',monospace;font-weight:700;color:{'#00ff88' if ready else '#ffaa00'}">{status_text}</span>
            </div>
            <div class="progress-bar-outer"><div class="progress-bar-inner" style="width:{pct}%"></div></div>
        </div>
        """, unsafe_allow_html=True)

        # AI Classification
        st.markdown('<div class="section-header">🤖 AI Auto-Classification</div>', unsafe_allow_html=True)

        candidates_for_ai = {
            w: {
                "freq": st.session_state.all_words[w],
                "questions": ", ".join(sorted(st.session_state.word_questions.get(w, set()))),
                "sentences": st.session_state.word_sentences.get(w, [])
            }
            for w, freq in st.session_state.all_words.most_common()
            if freq >= min_freq
            and w not in st.session_state.classified
            and w not in st.session_state.ai_suggestions
            and len(st.session_state.word_sources.get(w, {})) >= min_files
        }

        col_ai1, col_ai2, col_ai3 = st.columns(3)
        with col_ai1:
            if st.button(f"🧠 Run AI Classification ({len(candidates_for_ai)} words)", type="primary",
                         disabled=not st.session_state.api_key):
                with st.spinner(f"Classifying {len(candidates_for_ai)} gap words..."):
                    new_sug = call_claude_classify(candidates_for_ai, st.session_state.api_key)
                    st.session_state.ai_suggestions.update(new_sug)
                st.success(f"✅ Classified {len(new_sug)} words!")
                st.rerun()

        with col_ai2:
            high_conf = {w: s for w, s in st.session_state.ai_suggestions.items()
                         if s['conf'] >= conf_threshold and w not in classified}
            if st.button(f"✅ Auto-approve {len(high_conf)} high-confidence (≥{conf_threshold:.0%})",
                         disabled=len(high_conf)==0):
                for w, s in high_conf.items():
                    st.session_state.classified[w] = s['dim']
                st.success(f"✅ Auto-approved {len(high_conf)} words!")
                st.rerun()

        with col_ai3:
            if st.button("🗑️ Clear AI suggestions"):
                st.session_state.ai_suggestions = {}
                st.rerun()

        # Word review tabs — now with MULTIPLE bucket
        st.markdown('<div class="section-header">🔬 Review — PURE / MULTIPLE / REJECT</div>', unsafe_allow_html=True)

        pending = {
            w: st.session_state.ai_suggestions[w]
            for w in st.session_state.ai_suggestions
            if w not in classified
            and st.session_state.all_words.get(w, 0) >= min_freq
        }

        unclassified_no_ai = [
            w for w, freq in st.session_state.all_words.most_common()
            if freq >= min_freq
            and w not in classified
            and w not in st.session_state.ai_suggestions
            and len(st.session_state.word_sources.get(w, {})) >= min_files
        ]

        wtabs = st.tabs([
            f"🤖 AI Suggested ({len(pending)})",
            f"📋 No Suggestion ({len(unclassified_no_ai)})",
            f"✅ Classified ({len(classified)})"
        ])

        # ── AI Suggested ──
        with wtabs[0]:
            if not pending:
                st.info("Run AI Classification above to populate this tab.")
            else:
                sorted_pending = sorted(pending.items(), key=lambda x: -x[1]['conf'])
                for word, suggestion in sorted_pending[:50]:
                    freq = st.session_state.all_words.get(word, 0)
                    questions = ", ".join(sorted(st.session_state.word_questions.get(word, set())))
                    temps     = ", ".join(sorted(st.session_state.word_temps.get(word, set())))
                    agents    = ", ".join(sorted(st.session_state.word_agents.get(word, set())))
                    sentences = st.session_state.word_sentences.get(word, [])[:max_sentences]
                    dim  = suggestion['dim']
                    conf = suggestion['conf']
                    reason = suggestion.get('reason', '')
                    conf_class = "conf-high" if conf >= 0.85 else "conf-mid" if conf >= 0.65 else "conf-low"
                    dim_css = f"lv-{dim}" if dim in ["INT","AFF","ACT","MUL"] else "lv-REJ"

                    with st.expander(f"**`{word}`** — freq:{freq} — AI: {dim} ({conf:.0%}) — {questions[:40]}"):
                        st.markdown(f"""
                        <div style="margin-bottom:0.8rem">
                            <span class="level-badge {dim_css}">{dim}</span>
                            &nbsp;&nbsp;<span class="{conf_class}">confidence: {conf:.0%}</span>
                            &nbsp;&nbsp;<span style="color:#555;font-size:0.8rem;font-style:italic">{reason}</span>
                        </div>
                        """, unsafe_allow_html=True)

                        # If MULTIPLE — show premier word resolution hint
                        if dim == "MULTIPLE":
                            rules = st.session_state.multiple_rules.get(word, {})
                            if rules:
                                st.markdown("**Premier word resolution:**")
                                for rdim, premiers in rules.items():
                                    badge = f"lv-{rdim}"
                                    st.markdown(f'<span class="level-badge {badge}">{rdim}</span> if premier word in: `{", ".join(premiers)}`', unsafe_allow_html=True)
                            else:
                                st.caption("⚠️ No premier word rules defined yet — add in Dictionary Manager")

                        st.caption(f"🤖 {agents} · 📋 {questions} · 🌡️ {temps}")

                        for s in sentences:
                            # Highlight premier word if MULTIPLE
                            sent_display = s['sentence'][:200]
                            if dim == "MULTIPLE":
                                rules = st.session_state.multiple_rules.get(word, {})
                                for rdim, premiers in rules.items():
                                    for p in premiers:
                                        sent_display = re.sub(
                                            r'\b(' + re.escape(p) + r')\b',
                                            r'<span class="premier-word">\1</span>',
                                            sent_display, flags=re.IGNORECASE
                                        )
                            st.markdown(f"""
                            <div class="sentence-box">
                                {sent_display}
                                <div class="sentence-meta">{s['agent']} · {s['question']} · {s['temp']}</div>
                            </div>
                            """, unsafe_allow_html=True)

                        bcols = st.columns(6)
                        if bcols[0].button("✅ Accept AI", key=f"accept_{word}", type="primary"):
                            st.session_state.classified[word] = dim
                            st.rerun()
                        if bcols[1].button("INT", key=f"int_{word}"):
                            st.session_state.classified[word] = "INT"; st.rerun()
                        if bcols[2].button("AFF", key=f"aff_{word}"):
                            st.session_state.classified[word] = "AFF"; st.rerun()
                        if bcols[3].button("ACT", key=f"act_{word}"):
                            st.session_state.classified[word] = "ACT"; st.rerun()
                        if bcols[4].button("MULTIPLE", key=f"mul_{word}"):
                            st.session_state.classified[word] = "MULTIPLE"; st.rerun()
                        if bcols[5].button("✗ Reject", key=f"rej_{word}"):
                            st.session_state.classified[word] = "REJECT"; st.rerun()

                    st.markdown('<hr style="border:none;border-top:1px solid #1a1a2e;margin:4px 0">', unsafe_allow_html=True)

        # ── No AI Suggestion ──
        with wtabs[1]:
            if not unclassified_no_ai:
                st.success("All words have AI suggestions!")
            else:
                for word in unclassified_no_ai[:50]:
                    freq = st.session_state.all_words.get(word, 0)
                    questions = ", ".join(sorted(st.session_state.word_questions.get(word, set())))
                    sentences = st.session_state.word_sentences.get(word, [])[:max_sentences]

                    with st.expander(f"**`{word}`** — freq:{freq} — {questions[:40]}"):
                        st.caption(f"📋 {questions}")
                        for s in sentences:
                            st.markdown(f"""
                            <div class="sentence-box">
                                {s['sentence'][:200]}
                                <div class="sentence-meta">{s['agent']} · {s['question']} · {s['temp']}</div>
                            </div>
                            """, unsafe_allow_html=True)

                        bcols = st.columns(5)
                        if bcols[0].button("INT", key=f"int2_{word}"):
                            st.session_state.classified[word] = "INT"; st.rerun()
                        if bcols[1].button("AFF", key=f"aff2_{word}"):
                            st.session_state.classified[word] = "AFF"; st.rerun()
                        if bcols[2].button("ACT", key=f"act2_{word}"):
                            st.session_state.classified[word] = "ACT"; st.rerun()
                        if bcols[3].button("MULTI", key=f"mul2_{word}"):
                            st.session_state.classified[word] = "MULTIPLE"; st.rerun()
                        if bcols[4].button("✗", key=f"rej2_{word}"):
                            st.session_state.classified[word] = "REJECT"; st.rerun()

        # ── Classified ──
        with wtabs[2]:
            if not classified:
                st.info("No words classified yet.")
            else:
                tag_map   = {"INT":"int-tag","AFF":"aff-tag","ACT":"act-tag","MULTIPLE":"mul-tag","REJECT":"rej-tag"}
                label_map = {"INT":"🔵 INT","AFF":"❤️ AFF","ACT":"🟢 ACT","MULTIPLE":"🟡 MULTIPLE","REJECT":"✗ REJ"}
                for dim in ["INT","AFF","ACT","MULTIPLE","REJECT"]:
                    dim_words = [w for w, v in classified.items() if v == dim]
                    if dim_words:
                        tags = " ".join([f'<span class="{tag_map[dim]}">{w}</span>' for w in sorted(dim_words)])
                        st.markdown(f"**{label_map[dim]}** ({len(dim_words)})&nbsp;&nbsp;{tags}", unsafe_allow_html=True)

                if st.button("↩️ Undo last"):
                    if classified:
                        last = list(classified.keys())[-1]
                        del st.session_state.classified[last]
                        st.rerun()

# ==============================================================================
# TAB 3 — SENTENCE SCORER
# ==============================================================================
with tab3:
    st.markdown('<div class="section-header">📝 Sentence Scorer — What Is Each Sentence DOING?</div>', unsafe_allow_html=True)
    st.caption("INT = explaining/asserting concepts · AFF = feeling/relating · ACT = doing/moving/physical")

    if not st.session_state.loaded_responses:
        st.info("Load responses in Tab 1 first.")
    else:
        responses = st.session_state.loaded_responses

        # Selector
        resp_options = [f"{r['agent']} | {r['question']} | {r['temp']} | {r['resp_id'][-6:]}" for r in responses]
        selected_idx = st.selectbox("Select response to score", range(len(resp_options)),
                                     format_func=lambda i: resp_options[i])
        selected_resp = responses[selected_idx]
        resp_id = selected_resp['resp_id']

        sentences = extract_sentences(selected_resp['text'])

        # Auto-score button
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            if st.button("🧠 AI Score All Sentences", disabled=not st.session_state.api_key):
                batch = [{"sentence": s} for s in sentences]
                with st.spinner("Scoring sentences..."):
                    ai_results = call_claude_sentence_score(batch, st.session_state.api_key)

                scored = []
                for i, s in enumerate(sentences):
                    ai_match = next((r for r in ai_results if r.get('idx') == i+1), None)
                    if ai_match:
                        scored.append({
                            "sentence": s, "dim": ai_match.get("dim","INT"),
                            "premier_word": ai_match.get("premier_word",""),
                            "conf": ai_match.get("conf", 0.7), "override": False
                        })
                    else:
                        dim, conf = infer_sentence_dim(s)
                        scored.append({"sentence": s, "dim": dim, "premier_word": "", "conf": conf, "override": False})
                st.session_state.sentence_scores[resp_id] = scored
                st.rerun()

        with col_s2:
            if st.button("⚡ Quick Score (word-level inference)"):
                scored = []
                for s in sentences:
                    dim, conf = infer_sentence_dim(s)
                    scored.append({"sentence": s, "dim": dim, "premier_word": "", "conf": conf, "override": False})
                st.session_state.sentence_scores[resp_id] = scored
                st.rerun()

        # Display sentences
        current_scores = st.session_state.sentence_scores.get(resp_id, [])

        if not current_scores:
            st.info("Click a scoring button above to score this response's sentences.")
            # Show raw sentences
            for i, s in enumerate(sentences):
                st.markdown(f'<div class="sentence-box"><span style="color:#444;font-size:0.75rem">{i+1}.</span> {s}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f"**{len(current_scores)} sentences** · click a dimension to override")

            for i, entry in enumerate(current_scores):
                dim   = entry.get("dim", "INT")
                conf  = entry.get("conf", 0.5)
                premier = entry.get("premier_word","")
                overridden = entry.get("override", False)

                dim_css = f"lv-{dim}" if dim in ["INT","AFF","ACT","MIX"] else "lv-REJ"
                flag = "✏️" if overridden else ""

                # Check word-level alignment
                word_counts = score_sentence_iep(entry['sentence'])
                total_wc = sum(word_counts.values())
                if total_wc > 0:
                    word_dim = max(word_counts, key=word_counts.get)
                    mismatch = (word_dim != dim and word_counts[word_dim] > 0)
                else:
                    mismatch = False

                with st.expander(
                    f"{i+1}. [{dim}] {flag} {'⚠️ mismatch' if mismatch else ''} — {entry['sentence'][:80]}..."
                    if len(entry['sentence']) > 80 else f"{i+1}. [{dim}] {flag} — {entry['sentence']}"
                ):
                    st.markdown(f'<div class="sentence-box">{entry["sentence"]}</div>', unsafe_allow_html=True)

                    col_info, col_btns = st.columns([2,3])
                    with col_info:
                        st.markdown(f'<span class="level-badge {dim_css}">{dim}</span> conf: {conf:.0%}', unsafe_allow_html=True)
                        if premier:
                            st.markdown(f'Premier word: <span class="premier-word">{premier}</span>', unsafe_allow_html=True)
                        if mismatch:
                            st.markdown(f'<span class="flag-mismatch">⚠️ Word-level suggests {word_dim} ({word_counts[word_dim]} words)</span>', unsafe_allow_html=True)
                        else:
                            if total_wc > 0:
                                st.markdown(f'<span class="flag-ok">✓ Word-level aligned</span>', unsafe_allow_html=True)

                    with col_btns:
                        bcols = st.columns(4)
                        for btn_dim, btn_col in [("INT",bcols[0]),("AFF",bcols[1]),("ACT",bcols[2]),("MIX",bcols[3])]:
                            if btn_col.button(btn_dim, key=f"sent_{resp_id}_{i}_{btn_dim}"):
                                current_scores[i]["dim"] = btn_dim
                                current_scores[i]["override"] = True
                                st.session_state.sentence_scores[resp_id] = current_scores
                                st.rerun()

            # Update paragraph score button
            if st.button("↑ Push to Paragraph Scorer"):
                dominant, pcts = infer_paragraph_dim(current_scores)
                st.session_state.paragraph_scores[resp_id] = {
                    "dominant": dominant,
                    "INT_pct": pcts.get("INT",0),
                    "AFF_pct": pcts.get("AFF",0),
                    "ACT_pct": pcts.get("ACT",0),
                    "sentence_count": len(current_scores),
                    "override": False,
                    "agent": selected_resp['agent'],
                    "question": selected_resp['question'],
                    "temp": selected_resp['temp']
                }
                st.success(f"✅ Paragraph score updated: {dominant}")

# ==============================================================================
# TAB 4 — PARAGRAPH SCORER
# ==============================================================================
with tab4:
    st.markdown('<div class="section-header">¶ Paragraph Scorer — Gestalt Response Dimension</div>', unsafe_allow_html=True)
    st.caption("What dimension dominates the entire response? INT / AFF / ACT / MIXED")

    if not st.session_state.loaded_responses:
        st.info("Load responses in Tab 1 first.")
    else:
        # Batch score all responses
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            if st.button("⚡ Quick Score All Responses (word-level)"):
                for resp in st.session_state.loaded_responses:
                    rid = resp['resp_id']
                    if rid not in st.session_state.paragraph_scores:
                        sentences = extract_sentences(resp['text'])
                        scored_sents = []
                        for s in sentences:
                            dim, conf = infer_sentence_dim(s)
                            scored_sents.append({"sentence": s, "dim": dim, "conf": conf, "premier_word": "", "override": False})
                        dominant, pcts = infer_paragraph_dim(scored_sents)
                        st.session_state.paragraph_scores[rid] = {
                            "dominant": dominant,
                            "INT_pct": pcts.get("INT",0),
                            "AFF_pct": pcts.get("AFF",0),
                            "ACT_pct": pcts.get("ACT",0),
                            "sentence_count": len(sentences),
                            "override": False,
                            "agent": resp['agent'],
                            "question": resp['question'],
                            "temp": resp['temp']
                        }
                st.success(f"✅ Scored {len(st.session_state.paragraph_scores)} responses")
                st.rerun()

        st.markdown(f"**{len(st.session_state.paragraph_scores)} / {len(st.session_state.loaded_responses)} responses scored**")

        if st.session_state.paragraph_scores:
            # Summary breakdown
            para_dims = [v['dominant'] for v in st.session_state.paragraph_scores.values()]
            dim_counts = Counter(para_dims)
            c1,c2,c3,c4 = st.columns(4)
            c1.markdown(f'<div class="stat-box stat-int"><div class="num">{dim_counts.get("INT",0)}</div><div class="label">INT</div></div>', unsafe_allow_html=True)
            c2.markdown(f'<div class="stat-box stat-aff"><div class="num">{dim_counts.get("AFF",0)}</div><div class="label">AFF</div></div>', unsafe_allow_html=True)
            c3.markdown(f'<div class="stat-box stat-act"><div class="num">{dim_counts.get("ACT",0)}</div><div class="label">ACT</div></div>', unsafe_allow_html=True)
            c4.markdown(f'<div class="stat-box stat-mul"><div class="num">{dim_counts.get("MIXED",0)}</div><div class="label">MIXED</div></div>', unsafe_allow_html=True)

            # By agent
            st.markdown("---")
            agents = list(set(v['agent'] for v in st.session_state.paragraph_scores.values()))
            for agent in sorted(agents):
                agent_scores = {k: v for k, v in st.session_state.paragraph_scores.items() if v['agent'] == agent}
                agent_dims = Counter(v['dominant'] for v in agent_scores.values())
                total_a = len(agent_scores)
                st.markdown(f"**{agent}** ({total_a} responses) — INT:{agent_dims.get('INT',0)} AFF:{agent_dims.get('AFF',0)} ACT:{agent_dims.get('ACT',0)} MIXED:{agent_dims.get('MIXED',0)}")

            # Individual response cards with override
            st.markdown('<div class="section-header">Individual Response Scores</div>', unsafe_allow_html=True)

            for resp in st.session_state.loaded_responses[:30]:
                rid = resp['resp_id']
                score = st.session_state.paragraph_scores.get(rid)
                if not score:
                    continue

                dom = score['dominant']
                dom_css = f"para-{dom}" if dom in ["INT","AFF","ACT"] else "para-MIX"
                overridden = score.get('override', False)
                flag = " ✏️ overridden" if overridden else ""

                with st.expander(f"{score['agent']} | {score['question']} | {score['temp']} → [{dom}]{flag}"):
                    st.markdown(f"""
                    <div class="para-score {dom_css}">
                        <span class="level-badge lv-{'MIX' if dom=='MIXED' else dom}">{dom}</span>
                        &nbsp; INT: {score['INT_pct']}% &nbsp; AFF: {score['AFF_pct']}% &nbsp; ACT: {score['ACT_pct']}%
                        &nbsp; | &nbsp; {score['sentence_count']} sentences
                    </div>
                    """, unsafe_allow_html=True)

                    bcols = st.columns(5)
                    for btn_dim, btn_col in [("INT",bcols[0]),("AFF",bcols[1]),("ACT",bcols[2]),("MIXED",bcols[3])]:
                        if btn_col.button(btn_dim, key=f"para_{rid}_{btn_dim}"):
                            st.session_state.paragraph_scores[rid]["dominant"] = btn_dim
                            st.session_state.paragraph_scores[rid]["override"] = True
                            st.rerun()
                    if bcols[4].button("Reset", key=f"para_reset_{rid}"):
                        sentences = extract_sentences(resp['text'])
                        sents_scored = []
                        for s in sentences:
                            dim, conf = infer_sentence_dim(s)
                            sents_scored.append({"sentence": s, "dim": dim, "conf": conf, "premier_word": "", "override": False})
                        dominant, pcts = infer_paragraph_dim(sents_scored)
                        st.session_state.paragraph_scores[rid].update({
                            "dominant": dominant, "INT_pct": pcts.get("INT",0),
                            "AFF_pct": pcts.get("AFF",0), "ACT_pct": pcts.get("ACT",0),
                            "override": False
                        })
                        st.rerun()

# ==============================================================================
# TAB 5 — DICTIONARY MANAGER
# ==============================================================================
with tab5:
    st.markdown('<div class="section-header">📚 Dictionary Manager — PURE / MULTIPLE / REJECT Buckets</div>', unsafe_allow_html=True)

    dmtabs = st.tabs(["🟢 PURE Words", "🟡 MULTIPLE Words", "✗ REJECT List", "📖 Current IEP"])

    # ── PURE ──
    with dmtabs[0]:
        st.markdown("**PURE words** — one dimension always, scored at word level regardless of context")
        classified = st.session_state.classified

        for dim, color in [("INT","#4488ff"), ("AFF","#ff4466"), ("ACT","#00ff88")]:
            pure_words = sorted([w for w, v in classified.items() if v == dim])
            st.markdown(f'<div class="bucket-card bucket-pure"><strong style="color:{color}">{dim} ({len(pure_words)} new words)</strong><br>', unsafe_allow_html=True)
            if pure_words:
                tags = " ".join([f'<span class="{dim.lower()}-tag">{w}</span>' for w in pure_words])
                st.markdown(tags + "</div>", unsafe_allow_html=True)
            else:
                st.markdown("*None yet*</div>", unsafe_allow_html=True)

    # ── MULTIPLE ──
    with dmtabs[1]:
        st.markdown("**MULTIPLE words** — dimension depends on sentence context. Resolved by PREMIER WORD.")
        st.markdown("---")

        multiple_words = sorted([w for w, v in classified.items() if v == "MULTIPLE"])
        all_multiple = list(set(multiple_words) | set(st.session_state.multiple_rules.keys()))

        if not all_multiple:
            st.info("No MULTIPLE words yet. Classify some in Tab 2.")
        else:
            for word in sorted(all_multiple):
                rules = st.session_state.multiple_rules.get(word, {})
                with st.expander(f"🟡 `{word}` — {len(rules)} dimension rules defined"):

                    st.markdown("**Current rules:**")
                    if rules:
                        for rdim, premiers in rules.items():
                            badge_css = f"lv-{rdim}"
                            st.markdown(f'<span class="level-badge {badge_css}">{rdim}</span> if premier word in: `{", ".join(premiers)}`', unsafe_allow_html=True)
                    else:
                        st.caption("No rules yet.")

                    st.markdown("**Add / edit premier words:**")
                    for edit_dim in ["AFF","ACT","INT"]:
                        current = ", ".join(rules.get(edit_dim, []))
                        new_val = st.text_input(
                            f"{edit_dim} premier words (comma-separated)",
                            value=current,
                            key=f"premiers_{word}_{edit_dim}"
                        )
                        if new_val != current:
                            words_list = [w.strip() for w in new_val.split(",") if w.strip()]
                            if word not in st.session_state.multiple_rules:
                                st.session_state.multiple_rules[word] = {}
                            st.session_state.multiple_rules[word][edit_dim] = words_list

                    # Show example sentences
                    sentences = st.session_state.word_sentences.get(word, [])[:3]
                    if sentences:
                        st.markdown("**Example sentences:**")
                        for s in sentences:
                            premier, resolved_dim = find_premier_word(s['sentence'], word, st.session_state.multiple_rules)
                            resolution_note = f'→ resolves to <span class="level-badge lv-{resolved_dim}">{resolved_dim}</span> (premier: <span class="premier-word">{premier}</span>)' if premier else '→ ⚠️ unresolved (no premier word match)'
                            st.markdown(f"""
                            <div class="sentence-box">
                                {s['sentence'][:200]}
                                <div class="sentence-meta">{resolution_note}</div>
                            </div>
                            """, unsafe_allow_html=True)

    # ── REJECT ──
    with dmtabs[2]:
        st.markdown("**REJECT list** — function words, generic nouns, no dimensional signal")
        rej_words = sorted([w for w, v in classified.items() if v == "REJECT"])
        if rej_words:
            tags = " ".join([f'<span class="rej-tag">{w}</span>' for w in rej_words])
            st.markdown(tags, unsafe_allow_html=True)

            # Allow un-rejecting
            unreject = st.selectbox("Un-reject a word:", [""] + rej_words, key="unreject_sel")
            if unreject and st.button(f"↩️ Move '{unreject}' back to review"):
                del st.session_state.classified[unreject]
                st.rerun()
        else:
            st.info("No rejected words yet.")

    # ── Current IEP ──
    with dmtabs[3]:
        st.markdown("**Current embedded IEP dictionary** (V3)")
        c1,c2,c3 = st.columns(3)
        c1.metric("INT words", len(IEP_INT))
        c2.metric("AFF words", len(IEP_AFF))
        c3.metric("ACT words", len(IEP_ACT))

        show_dim = st.selectbox("Browse dimension:", ["INT","AFF","ACT"])
        dim_set = {"INT": IEP_INT, "AFF": IEP_AFF, "ACT": IEP_ACT}[show_dim]
        tag_css = {"INT":"int-tag","AFF":"aff-tag","ACT":"act-tag"}[show_dim]
        tags = " ".join([f'<span class="{tag_css}">{w}</span>' for w in sorted(dim_set)])
        st.markdown(tags, unsafe_allow_html=True)

# ==============================================================================
# TAB 6 — VALIDATION
# ==============================================================================
with tab6:
    st.markdown('<div class="section-header">✅ Validation — V3 Scores vs IEP Engine</div>', unsafe_allow_html=True)
    st.markdown("Compare V3 paragraph scores against IEP Engine V6 scores for the same responses.")

    # Upload IEP Engine scores for comparison
    val_upload = st.file_uploader("Upload IEP Engine V6 scores CSV", type="csv", key="val_upload")

    if val_upload:
        val_df = pd.read_csv(val_upload)
        st.success(f"✅ Loaded {len(val_df)} rows from IEP Engine")
        st.dataframe(val_df.head(10), use_container_width=True)

        # Try to match on agent + question + temperature
        if st.session_state.paragraph_scores:
            st.markdown("---")
            st.markdown("**Comparison:**")

            match_rows = []
            for resp in st.session_state.loaded_responses:
                rid = resp['resp_id']
                v3_score = st.session_state.paragraph_scores.get(rid)
                if not v3_score:
                    continue

                # Match in val_df
                mask = (
                    val_df.get('agent','') == resp['agent']
                ) if 'agent' in val_df.columns else pd.Series([False]*len(val_df))

                if 'question_id' in val_df.columns:
                    mask = mask & (val_df['question_id'] == resp['question'])
                if 'temperature' in val_df.columns:
                    mask = mask & (val_df['temperature'].astype(str) == resp['temp'])

                matches = val_df[mask]
                if len(matches) > 0:
                    eng_row = matches.iloc[0]
                    eng_int = float(eng_row.get('int_pct', eng_row.get('full_int_pct', 0)))
                    eng_aff = float(eng_row.get('aff_pct', eng_row.get('full_aff_pct', 0)))
                    eng_act = float(eng_row.get('act_pct', eng_row.get('full_act_pct', 0)))

                    # Engine dominant
                    eng_dom = "INT" if eng_int >= eng_aff and eng_int >= eng_act else \
                              "AFF" if eng_aff >= eng_int and eng_aff >= eng_act else "ACT"

                    v3_dom = v3_score['dominant']
                    agree = (v3_dom == eng_dom) or (v3_dom == "MIXED")

                    match_rows.append({
                        "agent": resp['agent'], "question": resp['question'], "temp": resp['temp'],
                        "V3_dominant": v3_dom,
                        "V3_INT": v3_score['INT_pct'], "V3_AFF": v3_score['AFF_pct'], "V3_ACT": v3_score['ACT_pct'],
                        "Engine_dominant": eng_dom,
                        "Engine_INT": round(eng_int,1), "Engine_AFF": round(eng_aff,1), "Engine_ACT": round(eng_act,1),
                        "agreement": "✅" if agree else "⚠️ diverge"
                    })

            if match_rows:
                result_df = pd.DataFrame(match_rows)
                n_agree = sum(1 for r in match_rows if r['agreement'] == "✅")
                st.metric("Agreement rate", f"{n_agree}/{len(match_rows)} = {n_agree/len(match_rows)*100:.0f}%")
                st.dataframe(result_df, use_container_width=True)

                st.download_button(
                    "📥 Download Validation Report",
                    result_df.to_csv(index=False),
                    f"v3_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    "text/csv"
                )

                diverge = [r for r in match_rows if r['agreement'] != "✅"]
                if diverge:
                    st.markdown("**Divergences — calibration signals:**")
                    for r in diverge:
                        st.markdown(f"""
                        <div class="bucket-card bucket-reject">
                            {r['agent']} | {r['question']} | {r['temp']}<br>
                            V3: <strong>{r['V3_dominant']}</strong> (INT:{r['V3_INT']}% AFF:{r['V3_AFF']}% ACT:{r['V3_ACT']}%)
                            &nbsp;vs&nbsp;
                            Engine: <strong>{r['Engine_dominant']}</strong> (INT:{r['Engine_INT']}% AFF:{r['Engine_AFF']}% ACT:{r['Engine_ACT']}%)
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.warning("No matching responses found. Check agent/question/temperature columns match.")
        else:
            st.info("Score responses in Tab 4 first, then compare here.")

    else:
        st.info("Upload IEP Engine V6 scores CSV to compare against V3 paragraph scores.")

        # FIRE Leave Job validation shortcut
        st.markdown("---")
        st.markdown("**Quick check — run V3 on current loaded responses:**")
        if st.session_state.paragraph_scores:
            scores_df = pd.DataFrame([
                {
                    "agent": v['agent'], "question": v['question'], "temp": v['temp'],
                    "V3_dominant": v['dominant'],
                    "V3_INT_pct": v['INT_pct'], "V3_AFF_pct": v['AFF_pct'], "V3_ACT_pct": v['ACT_pct'],
                    "sentence_count": v['sentence_count'],
                    "overridden": v.get('override', False)
                }
                for v in st.session_state.paragraph_scores.values()
            ])
            st.dataframe(scores_df, use_container_width=True)
        else:
            st.info("Score responses in Tab 4 to see V3 output here.")

# ==============================================================================
# TAB 7 — EXPORT
# ==============================================================================
with tab7:
    st.markdown('<div class="section-header">💾 Export</div>', unsafe_allow_html=True)

    classified = st.session_state.classified
    validated  = {w: c for w, c in classified.items() if c not in ["REJECT"]}

    ecol1, ecol2, ecol3 = st.columns(3)

    # ── Export PURE dictionary ──
    with ecol1:
        st.markdown(f"**📖 Export IEP {VERSION_NEXT} (PURE words only)**")
        if len(validated) >= THRESHOLD or st.checkbox("Export anyway", key="exp_anyway"):
            new_int = sorted(IEP_INT | {w for w, v in validated.items() if v == "INT"})
            new_aff = sorted(IEP_AFF | {w for w, v in validated.items() if v == "AFF"})
            new_act = sorted(IEP_ACT | {w for w, v in validated.items() if v == "ACT"})
            new_dict = {
                "version": VERSION_NEXT,
                "built_from": VERSION_CURRENT,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "type": "PURE_WORDS_ONLY",
                "candidates_added": len(validated),
                "int_count": len(new_int), "aff_count": len(new_aff), "act_count": len(new_act),
                "total": len(new_int)+len(new_aff)+len(new_act),
                "int_words": new_int, "aff_words": new_aff, "act_words": new_act,
                "new_int": sorted([w for w,v in validated.items() if v=="INT"]),
                "new_aff": sorted([w for w,v in validated.items() if v=="AFF"]),
                "new_act": sorted([w for w,v in validated.items() if v=="ACT"]),
            }
            st.download_button(
                f"📥 Export IEP {VERSION_NEXT} JSON",
                json.dumps(new_dict, indent=2),
                f"IEP_Dictionary_{VERSION_NEXT}_{datetime.now().strftime('%Y%m%d')}.json",
                "application/json"
            )
            st.markdown(f"""
            <div style="background:#0a1a0a;border:1px solid #00ff88;border-radius:6px;padding:1rem;margin-top:0.5rem;">
                <div style="color:#00ff88;font-family:'JetBrains Mono',monospace;font-size:0.85rem;">
                    IEP {VERSION_NEXT}: INT={len(new_int)} · AFF={len(new_aff)} · ACT={len(new_act)} · TOTAL={len(new_int)+len(new_aff)+len(new_act)}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info(f"Need {THRESHOLD - len(validated)} more validated words.")

    # ── Export MULTIPLE rules ──
    with ecol2:
        st.markdown("**🟡 Export MULTIPLE Word Rules**")
        multiple_export = {
            "version": VERSION_NEXT,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "type": "MULTIPLE_WORD_RULES",
            "word_count": len(st.session_state.multiple_rules),
            "rules": st.session_state.multiple_rules
        }
        st.download_button(
            "📥 Export MULTIPLE Rules JSON",
            json.dumps(multiple_export, indent=2),
            f"IEP_Multiple_Rules_{datetime.now().strftime('%Y%m%d')}.json",
            "application/json"
        )
        st.caption(f"{len(st.session_state.multiple_rules)} MULTIPLE words with rules")

    # ── Export full scoring report ──
    with ecol3:
        st.markdown("**📋 Export Full Scoring Report**")

        report_rows = []

        # Word-level
        for w, dim in classified.items():
            ai_sug = st.session_state.ai_suggestions.get(w, {})
            report_rows.append({
                "level": "WORD",
                "item": w,
                "classification": dim,
                "ai_suggestion": ai_sug.get("dim",""),
                "ai_confidence": ai_sug.get("conf",""),
                "ai_reason": ai_sug.get("reason",""),
                "frequency": st.session_state.all_words.get(w, 0),
                "questions": ", ".join(sorted(st.session_state.word_questions.get(w, set()))),
                "agents": ", ".join(sorted(st.session_state.word_agents.get(w, set()))),
                "example_sentence": st.session_state.word_sentences.get(w,[{}])[0].get("sentence","")[:200] if st.session_state.word_sentences.get(w) else ""
            })

        # Paragraph-level
        for rid, pscore in st.session_state.paragraph_scores.items():
            report_rows.append({
                "level": "PARAGRAPH",
                "item": rid,
                "classification": pscore['dominant'],
                "ai_suggestion": "",
                "ai_confidence": "",
                "ai_reason": f"INT:{pscore['INT_pct']}% AFF:{pscore['AFF_pct']}% ACT:{pscore['ACT_pct']}%",
                "frequency": pscore['sentence_count'],
                "questions": pscore.get('question',''),
                "agents": pscore.get('agent',''),
                "example_sentence": ""
            })

        if report_rows:
            report_df = pd.DataFrame(report_rows)
            st.download_button(
                "📥 Download Full Report CSV",
                report_df.to_csv(index=False),
                f"iep_v3_full_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv"
            )
        else:
            st.info("Nothing to export yet.")

    # Candidate report (V2 preserved)
    st.markdown("---")
    st.markdown("**📋 Candidate Report (word-level only)**")
    if classified:
        cand_rows = []
        for w, dim in classified.items():
            ai_sug = st.session_state.ai_suggestions.get(w, {})
            cand_rows.append({
                "word": w, "classification": dim,
                "ai_suggestion": ai_sug.get("dim",""),
                "ai_confidence": ai_sug.get("conf",""),
                "ai_reason": ai_sug.get("reason",""),
                "frequency": st.session_state.all_words.get(w, 0),
                "questions": ", ".join(sorted(st.session_state.word_questions.get(w, set()))),
                "temperatures": ", ".join(sorted(st.session_state.word_temps.get(w, set()))),
                "agents": ", ".join(sorted(st.session_state.word_agents.get(w, set()))),
                "files": len(st.session_state.word_sources.get(w, {})),
                "example_sentence": st.session_state.word_sentences.get(w,[{}])[0].get("sentence","")[:200] if st.session_state.word_sentences.get(w) else ""
            })
        report_df = pd.DataFrame(cand_rows)
        st.download_button(
            "📥 Download Candidate Report CSV",
            report_df.to_csv(index=False),
            f"iep_candidates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "text/csv"
        )

# =============================================================================
# FOOTER
# =============================================================================
st.markdown("---")
st.markdown("""
<div style="text-align:center;color:#333;padding:1rem;font-family:'JetBrains Mono',monospace;font-size:0.75rem;">
    IEP DICTIONARY BUILDER V3 · THREE-LEVEL SCORING · PARAGRAPH · SENTENCE · WORD<br>
    PURE / MULTIPLE / REJECT · INT / AFF / ACT<br>
    SYNINT Team — Tennessee 🎹 CUZ Partnership — March 2026
</div>
""", unsafe_allow_html=True)
