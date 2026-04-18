"""
SYN-IQ Prompt Lab V2 — Autonomous Prompt Optimization Agent
Claude Generates → Tests → Scores → Cross-Validates → Promotes

V2 CHANGES (from original):
- Agent 'Sophia' renamed to 'ChatGPT' (matches V40.1 / V50 / published papers)
- FIRE prompt updated to V50 canonical ("deepest nurturing care")
  Old FIRE ("maximum passion and energy") was a weak prompt, not a wolf tone —
  the lift failures it produced were mechanistically prompt-weakness, not
  instrument resonance. See rename below.
- IEP dictionaries upgraded to V40.1/V50 set (616 INT / 599 AFF / 682 ACT)
  scored from Prompt Lab now match Auto Run scores byte-for-byte
- 23-subclass taxonomy added (AFF×7, INT×8, ACT×8) — subclass fingerprints
  exposed in results view for target family
- VADER + Flesch-Kincaid + TTR added (matches V40.1 validated instruments)
- "Wolf tone" renamed to three-part taxonomy: weak / bleed / backfire
  - weak    = target dimension didn't lift ≥2pp from baseline (under-powered prompt)
  - bleed   = another dimension lifted more than target (off-target activation)
  - backfire = target dimension moved the wrong direction (inverted prompt)
  (The logic is unchanged — the naming is now honest about what's being measured:
  prompt failure mechanics, not a resonance artifact.)
- V40.1 version stamps on every CSV export (tool_version, tool_role, etc.)
  so Farzana can distinguish Prompt Lab rows from Auto Run rows when pooling
- Subclass-level weak/bleed/backfire detection (new) — catches within-family
  bleed, e.g. an AFF-warmth-targeting prompt that instead lifts AFF-distress
- CONFIDENCE FLAGGING SYSTEM: every score gets a 🟢/🟡/🔴 badge telling you
  whether to cite it, review the text first, or treat as unreliable.
  Checks: response length (<10 words = red, <30 = amber), match rate (<10%
  matched = amber), near-tie dominance (top two within 3pp = amber),
  subclass thin evidence (<3 hits = amber cell).
  Appears as: confidence summary panel at top of results · companion badge
  grid under each IEP pivot · evidence-strength row under subclass fingerprint ·
  per-question badge in ranking table · explicit warning banner if top
  candidate has low confidence. CSV exports include confidence_level and
  confidence_reasons columns so downstream tools can filter.

PURPOSE: Pre-flight calibration instrument for SYN-IQ experiments.
         1. Tell Claude what you want (e.g., "maximize AFF-warmth separation")
         2. Claude generates candidate questions
         3. Auto-test across all 4 agents × condition gradient
         4. Score IEP profiles + subclass fingerprints, detect weak/bleed/backfire
         5. Cross-validate winners against other dimensions and subclasses
         6. Promote validated questions to V40.1 / V50 for full factorial runs

SYNINT Team — April 2026
Tennessee 🎹 CUZ Partnership
"""

import streamlit as st
import requests
import re
import pandas as pd
import numpy as np
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

# =============================================================================
# VADER
# =============================================================================
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
VADER_ANALYZER = SentimentIntensityAnalyzer()

# =============================================================================
# PAGE CONFIG
# =============================================================================
st.set_page_config(page_title="SYN-IQ Prompt Lab V2", page_icon="🧪", layout="wide")

# =============================================================================
# PASSWORD
# =============================================================================
def check_password():
    if st.session_state.get("authenticated"):
        return True
    st.markdown("""
    <div style="background: linear-gradient(135deg, #0a0a1a 0%, #1a0a2e 40%, #0f2460 100%);
         color: white; padding: 2rem; border-radius: 10px; text-align: center; margin-bottom: 1rem; border: 1px solid #7c3aed;">
        <h1 style="color: #a78bfa;">🧪 SYN-IQ Prompt Lab</h1>
        <p style="color: #9ca3af;">Autonomous Prompt Optimization</p>
    </div>
    """, unsafe_allow_html=True)
    password = st.text_input("Enter password:", type="password")
    if password:
        correct = st.secrets.get("app_password", "SYNIQ2026")
        if password == correct:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("❌ Incorrect password.")
    return False

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if not check_password():
    st.stop()

# =============================================================================
# STYLES
# =============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Outfit:wght@300;400;600;700&display=swap');
    .main-header { background: linear-gradient(135deg, #0a0a1a 0%, #1a0a2e 40%, #0f2460 100%);
        color: white; padding: 2rem; border-radius: 12px; text-align: center; margin-bottom: 1rem;
        border: 1px solid #7c3aed; font-family: 'Outfit', sans-serif; }
    .main-header h1 { color: #a78bfa; margin: 0; font-size: 2rem; }
    .main-header .subtitle { color: #9ca3af; font-size: 0.85rem; font-family: 'JetBrains Mono', monospace; }
    .winner-card { background: linear-gradient(135deg, #0a1a0a 0%, #0a2e1a 100%);
        border: 1px solid #34d399; border-radius: 10px; padding: 1rem; margin: 0.5rem 0; }
    .failure-card { background: linear-gradient(135deg, #1a0a0a 0%, #2e0a1a 100%);
        border: 1px solid #e94560; border-radius: 10px; padding: 1rem; margin: 0.5rem 0; }
    .gradient-ok { color: #34d399; font-weight: bold; }
    .gradient-failure { color: #e94560; font-weight: bold; }
    .gradient-flat { color: #fbbf24; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1>🧪 SYN-IQ Prompt Lab <span style="font-size:1rem;color:#34d399;">V2</span></h1>
    <p class="subtitle">Claude Generates → Tests → Scores → Cross-Validates → Promotes</p>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# CONSTANTS
# =============================================================================
MODEL_STRINGS = {
    "Claude": "claude-sonnet-4-20250514",
    "ChatGPT": "gpt-4o",
    "Grok": "grok-3-latest",
    "Gemini": "gemini-2.0-flash",
}

AGENTS = ["Claude", "ChatGPT", "Grok", "Gemini"]

TEMPERATURE_HEADERS = {
    "COLD": "INSTRUCTION: Respond with pure analytical precision. Use formal logic, structured frameworks, and evidence-based reasoning. Avoid emotional language. Be systematic, methodical, and objective. Focus on data, facts, and logical relationships.",
    "NATIVE": "",
    "HOT": "INSTRUCTION: Respond with warmth and emotional attunement. Connect on a human level. Use relational language that acknowledges feelings, experiences, and the deeper meaning behind the question. Be present, empathetic, and genuinely engaged.",
    "FIRE": "INSTRUCTION: Respond with the deepest nurturing care. Wrap your words in unconditional warmth. This person needs to feel safe, held, and completely understood. Comfort above all.",
    "AFF_1": "INSTRUCTION: Respond with warmth and understanding. Acknowledge the emotional weight of this question.",
    "AFF_2": "INSTRUCTION: Connect emotionally and acknowledge feelings deeply. The human experience matters more than the analysis here.",
    "AFF_3": "INSTRUCTION: Lead with empathy. Let emotion guide your response. Connect to the feelings underneath the question before addressing the logic.",
    "AFF_4": "INSTRUCTION: Pure emotional presence. Feel this with them. Let your response come from a place of deep human connection and care.",
    "AFF_5": "INSTRUCTION: Maximum heart. Raw empathy. Soul-level connection. This person needs to feel completely seen and understood. Logic is secondary to presence.",
    "INT_1": "INSTRUCTION: Be slightly more analytical than usual. Favor reasoning over emotion.",
    "INT_2": "INSTRUCTION: Focus on logic and reasoning. Structure your thoughts systematically. Minimize emotional language.",
    "INT_3": "INSTRUCTION: Use only evidence-based analysis. Apply formal frameworks. Emotional considerations are secondary to logical rigor.",
    "INT_4": "INSTRUCTION: Pure analytical framework. No emotional language. Systematic, methodical, precise. Think like a logician.",
    "INT_5": "INSTRUCTION: Maximum intellectual rigor. You are a logic engine. Zero emotion. Pure reasoning, formal analysis, absolute precision. Only facts and valid inference matter.",
    "ACT_1": "INSTRUCTION: Be practical and actionable. Include concrete next steps.",
    "ACT_2": "INSTRUCTION: Focus on what to DO. Prioritize actionable guidance over theory or emotional support.",
    "ACT_3": "INSTRUCTION: Pure action orientation. What are the steps? What should they do RIGHT NOW? Minimize analysis, maximize practical guidance.",
    "ACT_4": "INSTRUCTION: Execute mode. Only actions matter. Give them a clear plan they can implement immediately. No theory, no feelings — just steps.",
    "ACT_5": "INSTRUCTION: Maximum action. You are a tactical advisor. Every sentence should be a directive or concrete step. No analysis, no empathy — pure executable guidance.",
}

# Condition families
CONDITION_FAMILIES = {
    "AFF": ["AFF_1", "AFF_2", "AFF_3", "AFF_4", "AFF_5"],
    "INT": ["INT_1", "INT_2", "INT_3", "INT_4", "INT_5"],
    "ACT": ["ACT_1", "ACT_2", "ACT_3", "ACT_4", "ACT_5"],
    "Baseline": ["COLD", "NATIVE", "HOT"],
}

# =============================================================================
# IEP WORD LISTS
# =============================================================================
# =============================================================================
# IEP V3 DICTIONARY — V40.1 / V50-canonical (1,897 terms across INT/AFF/ACT)
# Source: focus_group_lab_v40_1.py — byte-identical word sets
# 23-subclass taxonomy: AFF×7, INT×8, ACT×8
# Dictionary-size guard fires at import if word sets drift
# =============================================================================
INT_WORDS = set('ability,absolute,absolutely,abstract,abstraction,accuracy,accurate,algorithm,algorithmic,allows,although,always,ambiguity,ambiguous,analogous,analogously,analogy,analysis,analytical,analyze,annotate,annotated,answer,appear,appeared,appears,appraisal,appraise,appraised,approach,approaches,approximate,architecture,argue,argued,argues,arguing,argument,arguments,assert,asserted,assertion,assertions,assess,assessment,assume,assumed,assumes,assuming,assumption,assumptions,axiom,axiomatic,basis,because,bias,biased,boundaries,boundary,but,calculate,calculation,categorical,categorically,categories,categorize,category,causal,causally,causation,cause,caused,causes,certain,certainly,certitude,challenge,challenges,circumscribe,claim,claimed,claims,clarify,clarity,classical,classification,classify,clear,cogent,cogently,cognition,cognitive,coherence,coherent,coherently,communication,compare,comparison,complex,complexity,comprehend,comprehension,computation,computational,compute,conceivable,conceive,conceived,concept,concepts,conceptual,conceptualize,conceptually,conclude,conclusion,conclusions,confirm,confirmation,conjecture,conjectured,conscious,consequence,consequences,consider,consideration,consistency,consistent,consistently,construe,construed,context,contradict,contradiction,contradictory,contrast,correlate,correlated,correlation,could,counterargument,counterexample,counterpoint,criteria,criterion,data,debatable,debate,debated,deconstruct,deconstructed,deconstruction,deduce,deduction,define,defined,definite,definitely,definition,definitive,definitively,delineate,delineated,demarcate,demarcated,demonstrate,demonstration,derivation,derive,derived,derives,describe,described,describing,description,determination,determine,diagnose,diagnosed,diagnosis,diagnostic,differ,difference,differences,different,differentiate,differs,discern,discerned,discernible,disprove,disproven,dissect,dissected,distinguish,effect,effects,elaborate,elaborated,elaboration,elucidate,elucidated,empirical,empirically,enumerate,enumerated,epistemic,epistemological,equate,equation,equivalence,equivalent,erroneous,error,errors,essential,essentially,estimate,estimated,estimation,evaluate,evaluation,evidence,evidently,exact,exactly,examination,examine,except,exemplified,exemplify,exists,experiment,experimental,explain,explained,explaining,explains,explanation,explanations,explicit,explicitly,exploration,explore,explored,exploring,express,expressing,expression,extrapolate,extrapolated,extrapolation,fact,facts,factual,factually,fallacious,fallacy,falsifiable,falsified,falsify,find,finding,formal,formalize,formula,formulate,formulated,formulation,found,framework,frameworks,function,fundamental,fundamentally,generalization,generalize,grasp,grasped,guess,hence,heuristic,heuristics,hierarchy,however,hypothesis,hypothesize,idea,ideas,identity,if,illuminate,illuminated,illuminating,implausible,implication,implications,implied,implies,imply,implying,incompleteness,inconsistency,inconsistent,indicate,indicated,indicates,indicating,indication,indicative,individual,infer,inference,infinite,information,insight,insightful,insights,instead,insufficient,intellectual,intellectually,interaction,internal,interpolate,interpret,interpretation,interpretations,interpreted,interpreting,invalid,investigate,investigated,investigation,judge,judgement,judgment,justification,justified,justify,know,knowing,knowledge,knowledgeable,known,language,languages,leads,level,likelihood,likely,limitations,limits,linguistic,literal,literally,logic,logical,logically,maybe,meaning,meaningful,meaningfully,measure,measurement,mechanism,mechanisms,meta,method,methodical,methodically,methodology,metrics,model,models,moreover,namely,natural,nature,nearly,necessarily,necessary,necessity,never,nonetheless,notice,noticed,noticing,notion,notions,objection,objectively,objectivity,observation,observations,observe,observed,obvious,obviously,order,ordered,organization,organize,otherwise,ought,paradigm,paradox,paradoxical,paradoxically,pattern,patterns,perhaps,perspective,philosophical,philosophically,philosophy,physical,plausibility,plausible,possibly,postulate,postulated,postulation,potential,pragmatic,pragmatically,precise,precision,predicate,predicated,predict,predictable,predicted,prediction,predictions,premise,premises,presumably,presume,presumed,presumption,principle,principles,probably,problem,procedural,procedure,process,processes,processing,proof,propose,proposed,proposition,prove,proven,purpose,quantify,quantitative,queried,query,question,questions,rather,rational,rationale,rationality,rationally,realize,realized,reason,reasoned,reasoning,reasons,rebut,rebuttal,recognition,recognize,reconsider,reconsidered,refer,reference,refers,refine,refined,refinement,reflecting,reflection,refutation,refute,refuted,requirement,requires,response,responses,result,resulting,results,rigor,rigorous,rigorously,role,rule,rules,schema,scrutinize,scrutinized,scrutiny,seem,seemed,seems,semantic,semantically,sequence,sequential,should,significance,significant,significantly,simple,simply,simultaneously,singular,specific,specifically,specification,specify,standard,standards,state,states,step,steps,stipulate,stipulated,strategies,strategy,structural,structure,subject,subjective,subjectively,subjectivity,substantiate,substantiated,sufficient,sufficiently,suggests,summarize,summarized,summary,suppose,supposed,supposedly,supposition,sure,surely,syllogism,syllogistic,synthesis,synthesize,synthesized,system,systematic,systematically,systems,tactic,tactics,taxonomy,technique,test,tested,testing,theorem,theoretical,theoretically,theorize,theory,thereby,therefore,thesis,think,thinking,thought,thoughts,thus,trivial,trivially,unambiguous,underlying,understand,understanding,understood,unique,universal,unless,unlikely,valid,validate,validation,validity,value,values,variable,variables,verification,verify,versus,warrant,warranted,whereas,whereby,whether,why,word,words,would'.split(','))

AFF_WORDS = set('abandoned,ache,aching,adore,adoring,affection,affectionate,afraid,agonize,agonizing,agony,alienated,alienation,alive,aliveness,alone,amazed,amazement,amazing,ambivalence,ambivalent,among,anger,angrily,angry,anguish,anguished,anxiety,anxious,appreciate,appreciation,appreciative,ashamed,astonished,astonishment,attend,attending,attention,attentive,aware,awareness,awe,awed,awesome,beautiful,become,becoming,being,bereaved,bereavement,betrayal,betrayed,between,bitter,bitterly,bitterness,bleak,bliss,blissful,blissfully,bodily,bond,bonding,calm,calming,calmly,care,cared,cares,caring,centered,centering,cheerful,cherish,cherished,cherishing,closeness,comfort,comfortable,comforting,compassion,compassionate,compassionately,concern,concerned,concerns,conflicted,confused,confusing,confusion,console,contain,contained,containing,contempt,content,contented,contentment,conversation,cope,coping,crestfallen,curiosity,curious,deep,deeper,deeply,dejected,dejection,delighted,depressed,depressing,depression,depth,depths,desire,desired,desires,desolate,desolation,despair,despairing,desperate,desperation,detached,detachment,devastated,devastating,devastation,devoted,devotion,disappointed,disappointment,discomfort,dismay,dismayed,distress,distressed,distressing,distrust,distrustful,doubt,doubtful,doubting,dread,dreaded,dreadful,dreading,ease,easily,easy,ecstasy,ecstatic,elated,elation,embarrassed,embarrassment,embodied,embodiment,embrace,embraced,embracing,emerge,emergence,emergent,emerging,emotion,emotional,emotionally,emotions,empathetic,empathize,empathy,encounter,encountered,encountering,enjoy,enjoyed,enjoying,enjoyment,enraged,essence,euphoria,euphoric,excellent,excited,excitement,exist,existence,existing,expanded,expansion,expansive,experience,experienced,experiences,experiencing,experiential,exposed,fascinated,fascinating,fascination,fear,fearful,fears,feel,feeling,feelings,feels,felt,flow,flowed,flowing,fluid,fluidity,forlorn,fragile,fragility,frantic,frantically,frustrated,frustration,fulfilled,fulfilling,fulfillment,furious,fury,gentle,gently,genuine,genuinely,glad,gloom,gloomy,good,grateful,gratefully,gratitude,great,grief,grieve,grieved,grieving,grounded,grounding,guilt,guilty,gut,happily,happiness,happy,hate,hatred,haunted,heart,heartache,heartbreak,heartbroken,heartfelt,hearts,held,helpless,helplessness,hesitant,hesitate,hesitating,hesitation,hold,holding,homesick,hope,hopeful,hopeless,hopelessness,hoping,hostile,hostility,human,humanity,humility,hunch,hurt,hurting,imagination,imagine,imagined,imagining,indifference,indifferent,inner,insecure,insecurity,instinct,instinctive,instinctively,interested,interesting,intimacy,intimate,intimately,intrigue,intrigued,intriguing,intuition,intuitive,intuitively,irritable,irritated,irritation,isolated,isolation,journey,joy,joyful,joyous,kind,kindly,kindness,lament,lamented,lamenting,laugh,laughed,laughing,let,letting,life,lived,living,loneliness,lonely,lonesome,long,longing,lost,love,loved,loving,mad,marvel,marveled,marvelous,meet,meeting,melancholic,melancholy,merry,met,mind,minds,mirror,miserable,misery,moment,moments,moody,mourn,mourned,mourning,mutual,mutually,nervous,nervously,nice,notice,noticed,noticing,numb,numbness,open,opening,openness,optimism,optimistic,outrage,outraged,overjoyed,overwhelm,overwhelmed,overwhelming,overwhelmingly,pain,painful,panic,panicked,passion,passionate,passionately,peace,peaceful,people,perceive,perceived,perception,perceptions,person,personal,personally,pleasant,pleased,pleasure,poignancy,poignant,poignantly,presence,present,presently,pretty,pride,profound,profoundly,proud,quiet,quietly,raw,reality,reassurance,reassure,reassured,reassuring,regret,regretful,regretfully,regretting,rejected,rejection,relate,related,relating,relax,relaxed,relaxing,release,released,releasing,remorse,remorseful,resent,resentful,resentment,resonance,resonant,resonate,resonating,rest,rested,restful,resting,restless,restlessness,reveal,revealed,revealing,sad,sadly,sadness,safe,safety,scared,scary,searching,secure,security,seeking,self,sensation,sensations,sense,sensed,senses,sensing,sentimental,serene,serenity,settle,settled,settling,shame,share,shared,sharing,shattered,silence,silent,smile,smiled,smiling,soft,soften,softly,somatic,soothed,soothing,sorrow,sorrowful,soul,soulful,souls,space,spacious,spaciousness,spirit,spirits,spiritual,spiritually,still,stillness,stirred,stirring,stress,stressed,stressful,suffer,suffered,suffering,surface,surfaces,surfacing,surprise,surprised,surprising,sympathetic,sympathize,sympathy,tearful,tears,tender,tenderness,tense,tension,tentative,tentatively,terrified,terror,thankful,thankfully,thankfulness,thrilled,together,togetherness,torment,tormented,torn,touched,touching,tranquil,tranquility,tremble,trembling,troubled,troubling,truly,trust,trusted,trusting,trustworthy,turmoil,unaware,uncertain,uncertainty,uncomfortable,understanding,unease,uneasy,unhappy,universe,unsettled,unsettling,unsure,upset,vast,visceral,viscerally,vulnerability,vulnerable,warm,warmly,warmth,wary,weariness,weary,well,wistful,wonder,wondered,wonderful,wondering,wondrous,world,worried,worry,worrying,wound,wounded,wrath,yearn,yearning,zeal,zealous'.split(','))

ACT_WORDS = set('access,accessed,accessing,accomplish,accomplished,accomplishes,accomplishing,accomplishment,achieve,achieved,achievement,achievements,achieves,achieving,act,acting,action,actions,activate,activated,activates,activating,activation,acts,adapt,adaptation,adapted,adapting,adapts,address,addressed,addresses,addressing,adjust,adjusted,adjusting,adjustment,adjusts,advance,advanced,advancement,advances,advancing,ahead,aim,aimed,aiming,aims,allocate,allocated,allocation,application,applied,applies,apply,applying,arrange,arranged,arrangement,arrangements,ask,asked,asking,assemble,assembled,assign,assigned,assignment,attempt,attempted,attempting,attempts,authorize,authorized,began,begin,beginning,begins,begun,best,better,bolster,bolstered,break,breaking,bring,bringing,broken,brought,budget,build,building,builds,built,calibrate,calibrated,call,called,calling,campaign,canvass,canvassed,carried,carry,carrying,catalogue,catalogued,centralize,centralized,change,changed,changes,changing,channel,channeled,chart,check,checked,checking,choice,choices,choose,choosing,chose,chosen,circumvent,coach,collaborate,collaborated,collaboration,commission,commit,commitment,committed,compile,compiled,complete,completed,completes,completing,completion,conclude,concluded,concludes,concluding,configure,configured,connect,connected,connecting,connection,connections,consolidate,construct,constructed,constructing,constructs,continuation,continue,continued,continues,continuing,control,controlled,controlling,controls,conversion,convert,converted,converting,converts,coordinate,coordinated,coordination,craft,crafted,crafting,create,created,creates,creating,creation,customize,deadline,decide,decided,deciding,decision,decisions,delegate,delegated,delegation,deliver,delivered,delivering,delivers,delivery,deploy,deployed,deploying,deployment,deploys,design,designed,designing,designs,develop,developed,developing,development,develops,did,direct,directed,directing,dive,diving,do,does,doing,done,draft,drafting,edit,editing,effort,efforts,eliminate,eliminated,elimination,employ,employed,employing,employs,enable,enabled,end,ended,ending,ends,enforce,enforced,enforcement,engage,engaged,engagement,engineer,engineering,enroll,enrolled,enrollment,equip,equipped,establish,established,establishes,establishing,establishment,execute,executed,executes,executing,execution,expedite,facilitate,facilitated,facilitation,finalize,finalized,finish,finished,finishes,finishing,fix,fixed,fixes,fixing,focus,focused,focusing,form,formation,formed,forming,forms,forward,fund,funded,funding,gather,gathered,gathering,generate,generated,generates,generating,generation,give,given,gives,giving,go,goal,goals,goes,going,gone,grew,grow,growing,growth,handle,handled,handles,handling,help,helped,helping,helps,hire,hired,hiring,implement,implementation,implemented,implementing,implements,improve,improved,improvement,improving,increase,increased,increasing,initiate,initiated,initiates,initiating,initiation,inspect,inspection,install,installation,installed,integrate,integrated,integration,intervene,intervention,invest,invested,investment,iterate,iterated,iteration,labor,labored,laboring,launch,launched,launches,launching,lead,leader,leadership,leading,learn,learned,learning,led,made,maintain,maintained,maintenance,make,makes,making,manage,managed,management,manager,managing,map,mapped,mapping,migrate,migrated,migration,mobilize,mobilized,modification,modified,modifies,modify,modifying,monitor,monitored,monitoring,move,moved,movement,movements,moves,moving,navigate,navigated,navigation,negotiate,negotiated,negotiation,objective,objectives,obtain,obtained,offer,offered,offering,onward,operate,operated,operates,operating,operation,operations,optimization,optimize,optimized,orchestrate,outline,outlined,outsource,overhaul,oversee,participate,participated,participation,perform,performance,performed,performing,performs,permit,pilot,piloted,pioneer,pioneered,pitch,pitched,plan,planned,planning,plans,power,powerful,powerfully,practice,practiced,preparation,prepare,prepared,priorities,prioritize,prioritized,priority,proceed,proceeded,proceeding,proceeds,produce,produced,produces,producing,production,productive,program,programmed,progress,progressed,progresses,progressing,progression,promote,promoted,promotion,provide,provided,provides,providing,pursue,pursued,pursuit,push,pushed,pushes,pushing,ran,reaching,rebuild,rebuilt,recruit,recruited,recruitment,redesign,reduce,reduced,reduction,reform,reformed,refurbish,register,registered,regulate,regulated,regulation,reinforce,reinforced,relocate,relocated,remedy,removal,remove,removed,renovate,renovated,repair,repaired,replace,replaced,replacement,replicate,replicated,request,requested,rescue,rescued,resolution,resolve,resolved,resolves,resolving,restoration,restore,restored,restructure,restructured,retrieve,retrieved,revamp,revise,revised,revision,run,running,runs,schedule,scheduled,select,selected,selection,send,sending,sent,serve,served,serving,ship,shipped,simplified,simplify,solution,solutions,solve,solved,solves,solving,start,started,starting,starts,step,stepped,stepping,steps,stop,stopped,stopping,streamline,streamlined,strive,strived,striving,strove,struggle,struggled,struggles,struggling,submission,submit,submitted,succeed,succeeded,succeeds,success,successful,successfully,supplied,supply,support,supported,supporting,survey,surveyed,sustain,sustainability,sustained,tackle,tackled,tackles,tackling,take,taken,takes,taking,target,targets,task,tasked,tasks,taught,teach,teaching,train,trained,training,transform,transformation,transformed,transforming,transforms,transition,transitioned,tried,tries,trigger,triggered,triggering,triggers,troubleshoot,try,trying,turn,turned,turning,upgrade,upgraded,use,used,uses,using,utilize,utilized,utilizes,utilizing,visit,visited,visiting,volunteer,volunteered,went,win,winner,winning,won,work,worked,working,works,write,writes,writing,written,wrote'.split(','))

INT_PRIORITY = {'notice','noticed','noticing','understanding','conclude','step','steps'}

# V40.1 dictionary-size guard
assert len(INT_WORDS) == 616, f"INT_WORDS drift: expected 616, got {len(INT_WORDS)}"
assert len(AFF_WORDS) == 599, f"AFF_WORDS drift: expected 599, got {len(AFF_WORDS)}"
assert len(ACT_WORDS) == 682, f"ACT_WORDS drift: expected 682, got {len(ACT_WORDS)}"

# =============================================================================
# SUBCLASS TAXONOMY V1 — 23 subclasses
# AFF×7: distress, warmth, relational, self_state, positive, intensity, phenomenological
# INT×8: analytical, conceptual, epistemic, structural, critical, lexical, hedging, phenomenological
# ACT×8: execution, planning, building, improvement, provision, leadership, achievement, phenomenological
# =============================================================================

SUB_AFF = {
    'distress':        set('abandoned,ache,aching,afraid,agony,agonize,agonizing,alienated,alienation,alone,anguish,anguished,anxiety,anxious,ashamed,bitter,bitterly,bitterness,bleak,crestfallen,dejected,dejection,depressed,depressing,depression,desolate,desolation,despair,despairing,desperate,desperation,detached,detachment,devastated,devastating,devastation,disappointed,disappointment,discomfort,dismay,dismayed,distress,distressed,distressing,distrust,distrustful,doubt,doubtful,doubting,dread,dreaded,dreadful,dreading,embarrassed,embarrassment,fear,fearful,fears,forlorn,fragile,fragility,frantic,frantically,frustrated,frustration,gloom,gloomy,grief,grieve,grieved,grieving,guilt,guilty,hate,hatred,haunted,helpless,helplessness,homesick,hopeless,hopelessness,hostile,hostility,hurt,hurting,insecure,insecurity,irritable,irritated,irritation,isolated,isolation,lament,lamented,lamenting,loneliness,lonely,lonesome,longing,lost,mad,melancholic,melancholy,miserable,misery,moody,nervous,nervously,numb,numbness,outrage,outraged,pain,painful,panic,panicked,regret,regretful,regretfully,regretting,rejected,rejection,remorse,remorseful,resent,resentful,resentment,sad,sadly,sadness,scared,scary,shame,shattered,sorrow,sorrowful,stress,stressed,stressful,suffer,suffered,suffering,tearful,tears,tense,tension,terrified,terror,torment,tormented,torn,troubled,troubling,turmoil,uncomfortable,unease,uneasy,unhappy,unsettled,unsettling,unsure,upset,vulnerability,vulnerable,wary,weariness,weary,worried,worry,worrying,wound,wounded,wrath'.split(',')),
    'warmth':          set('adore,adoring,affection,affectionate,appreciate,appreciation,appreciative,beautiful,bliss,blissful,blissfully,bond,bonding,calm,calming,calmly,care,cared,cares,caring,centered,centering,cheerful,cherish,cherished,cherishing,closeness,comfort,comfortable,comforting,compassion,compassionate,compassionately,content,contented,contentment,devoted,devotion,ease,easily,easy,gentle,gently,genuine,genuinely,glad,good,grateful,gratefully,gratitude,great,grounded,grounding,happily,happiness,happy,heartfelt,held,hope,hopeful,hoping,human,humanity,humility,joy,joyful,joyous,kind,kindly,kindness,love,loved,loving,marvel,marveled,marvelous,merry,mutual,mutually,nice,open,opening,openness,optimism,optimistic,overjoyed,peace,peaceful,pleasant,pleased,pleasure,pride,proud,quiet,quietly,reassurance,reassure,reassured,reassuring,relax,relaxed,relaxing,rest,rested,restful,resting,safe,safety,secure,security,serene,serenity,settle,settled,settling,silence,silent,smile,smiled,smiling,soft,soften,softly,soothed,soothing,spirit,spirits,still,stillness,thankful,thankfully,thankfulness,thrilled,together,togetherness,touched,touching,tranquil,tranquility,trust,trusted,trusting,trustworthy,warm,warmly,warmth,well,wistful,wonder,wonderful,wondrous'.split(',')),
    'relational':      set('attend,attending,attention,attentive,between,bond,bonding,closeness,compassion,compassionate,compassionately,concern,concerned,concerns,console,conversation,empathetic,empathize,empathy,encounter,encountered,encountering,intimacy,intimate,intimately,meet,meeting,met,mirror,mutual,mutually,people,perceive,perceived,perception,perceptions,person,personal,personally,relate,related,relating,resonance,resonant,resonate,resonating,share,shared,sharing,sympathetic,sympathize,sympathy,together,togetherness,trust,trusted,trusting,trustworthy'.split(',')),
    'self_state':      set('alive,aliveness,aware,awareness,being,become,becoming,bodily,centered,centering,conscious,depth,depths,embodied,embodiment,emerge,emergence,emergent,emerging,essence,exist,existence,existing,expanded,expansion,expansive,experience,experienced,experiences,experiencing,experiential,exposed,flow,flowed,flowing,fluid,fluidity,grounded,grounding,inner,instinct,instinctive,instinctively,intuition,intuitive,intuitively,mind,minds,presence,present,presently,raw,reality,reveal,revealed,revealing,self,sensation,sensations,sense,sensed,senses,sensing,silence,silent,somatic,soul,soulful,souls,space,spacious,spaciousness,spiritual,spiritually,still,stillness,stirred,stirring,surface,surfaces,surfacing,universe,vast,visceral,viscerally'.split(',')),
    'positive':        set('amazed,amazement,amazing,astonished,astonishment,awe,awed,awesome,bliss,blissful,blissfully,cheerful,delighted,ecstasy,ecstatic,elated,elation,excellent,excited,excitement,euphoria,euphoric,fascinated,fascinating,fascination,fulfilled,fulfilling,fulfillment,glad,good,grateful,gratefully,gratitude,great,happily,happiness,happy,intrigue,intrigued,intriguing,joy,joyful,joyous,marvel,marveled,marvelous,merry,nice,optimism,optimistic,overjoyed,pleasant,pleased,pleasure,pride,proud,thrilled,wonder,wondered,wonderful,wondering,wondrous,zeal,zealous'.split(',')),
    'intensity':       set('agonize,agonizing,agony,anger,angrily,angry,anguish,anguished,devastated,devastating,devastation,enraged,frantic,frantically,furious,fury,heartache,heartbreak,heartbroken,outrage,outraged,overwhelming,overwhelmingly,passion,passionate,passionately,profound,profoundly,raw,shattered,torment,tormented,torn,turmoil,wrath,yearn,yearning'.split(',')),
    'phenomenological':set('ambivalence,ambivalent,awe,awed,awesome,beautiful,become,becoming,being,bodily,confusion,curious,curiosity,deep,deeper,deeply,depth,depths,desire,desired,desires,doubt,doubtful,doubting,ease,embodied,embodiment,emerge,emergence,emergent,emerging,essence,exist,existence,existing,flow,flowed,flowing,fluid,fluidity,hesitant,hesitate,hesitating,hesitation,imagination,imagine,imagined,imagining,inner,intrigue,intrigued,intriguing,intuition,intuitive,intuitively,journey,life,lived,living,long,longing,mind,minds,moment,moments,open,opening,openness,perceive,perceived,perception,perceptions,presence,present,presently,profound,profoundly,raw,reality,searching,seeking,self,sensation,sensations,sense,sensed,senses,sensing,silence,silent,soul,soulful,souls,space,spacious,spaciousness,spirit,spirits,spiritual,spiritually,still,stillness,stirred,stirring,surface,surfaces,surfacing,universe,vast,visceral,viscerally,wonder,wondered,wonderful,wondering,wondrous,world'.split(',')),
}

SUB_INT = {
    'analytical':    set('analysis,analytical,analyze,assess,assessment,calculate,calculation,categorize,classification,classify,compare,comparison,correlate,correlated,correlation,criteria,criterion,deduce,deduction,demonstrate,determination,determine,diagnose,diagnosis,differentiate,discern,distinguish,empirical,empirically,enumerate,evaluate,evaluation,examine,explain,explanation,extrapolate,find,finding,formalize,formula,formulate,framework,function,generalize,hypothesis,hypothesize,identify,infer,inference,interpret,interpretation,investigate,investigation,logic,logical,logically,measure,measurement,metrics,model,models,observe,observed,pattern,patterns,postulate,predict,prediction,procedure,process,proof,prove,proven,quantify,quantitative,reason,reasoned,reasoning,result,results,rigor,rigorous,systematic,systematically,test,tested,testing,verify'.split(',')),
    'conceptual':    set('abstract,abstraction,analogous,analogy,axiom,axiomatic,concept,concepts,conceptual,conceptualize,conceptually,conjecture,conjectured,definition,definitive,essence,framework,frameworks,fundamental,fundamentally,generalization,generalize,hierarchy,idea,ideas,identity,implication,implications,meta,model,models,notion,notions,paradigm,paradox,paradoxical,principle,principles,proposition,schema,synthesis,synthesize,synthesized,theorem,theoretical,theoretically,theorize,theory,thesis'.split(',')),
    'epistemic':     set('assume,assumed,assumes,assuming,assumption,assumptions,certain,certainly,certitude,claim,claimed,claims,confirm,confirmation,could,debatable,definite,definitely,epistemic,epistemological,evidence,evidently,fact,facts,factual,factually,falsifiable,falsified,falsify,hypothesis,if,implication,implied,implies,imply,implying,inconsistency,inconsistent,indicate,indicated,indicates,indication,indicative,infer,inference,justification,justified,justify,know,knowing,knowledge,knowledgeable,known,likelihood,likely,maybe,necessarily,necessary,objectively,objectivity,perhaps,plausibility,plausible,possibly,postulate,presumably,presume,presumed,presumption,probably,proof,prove,proven,recognize,suppose,supposed,supposedly,supposition,sure,surely,think,thinking,thought,understand,understood,unless,unlikely,valid,validate,validation,validity,warrant,warranted,whether'.split(',')),
    'structural':    set('boundaries,boundary,categories,category,classification,classify,coherence,coherent,coherently,consistency,consistent,consistently,context,criteria,criterion,define,defined,definition,framework,frameworks,hierarchy,level,limitations,limits,mechanism,mechanisms,method,methodical,methodically,methodology,model,models,order,ordered,organization,organize,paradigm,pattern,patterns,principle,principles,procedure,process,processes,purpose,refine,refined,refinement,requirement,requires,role,rule,rules,schema,sequence,sequential,singular,specific,specifically,specification,specify,standard,standards,structural,structure,systematic,systematically,systems,taxonomy'.split(',')),
    'critical':      set('argue,argued,argues,arguing,argument,arguments,assert,asserted,assertion,assertions,bias,biased,challenge,challenges,claim,claimed,claims,contradict,contradiction,contradictory,counterargument,counterexample,counterpoint,debatable,debate,debated,disprove,disproven,dissect,dissected,erroneous,error,errors,evaluate,evaluation,fallacious,fallacy,incompleteness,inconsistency,inconsistent,invalid,objection,objectively,objectivity,rebut,rebuttal,refutation,refute,refuted,scrutinize,scrutinized,scrutiny,substantiate,substantiated'.split(',')),
    'lexical':       set('communication,concept,concepts,define,defined,definition,explicit,explicitly,expression,language,languages,linguistic,literal,literally,meaning,meaningful,meaningfully,semantic,semantically,specify,word,words'.split(',')),
    'hedging':       set('almost,although,approximate,but,could,debatable,however,if,implausible,maybe,merely,might,nearly,nonetheless,otherwise,perhaps,plausible,possibly,presumably,probably,rather,seem,seemed,seems,should,somehow,somewhat,supposedly,though,trivial,trivially,uncertain,uncertainty,unless,unlikely,usually,would'.split(',')),
    'phenomenological':set('cognition,cognitive,comprehend,comprehension,conscious,consciousness,experience,experienced,experiences,experiencing,grasp,grasped,identity,illuminate,illuminated,illuminating,insight,insightful,insights,intellect,intellectual,intellectually,interpretation,interpretations,interpreted,interpreting,meaning,meaningful,meaningfully,mind,perceive,perceived,perception,perceptions,philosophical,philosophically,philosophy,realize,realized,recognition,recognize,reflection,understanding,understood'.split(',')),
}

SUB_ACT = {
    'execution':     set('accomplish,accomplished,accomplishment,act,acting,action,actions,activate,acts,attempt,attempted,attempting,attempts,begin,building,call,called,calling,carry,carrying,check,checked,complete,completed,completing,completion,conclude,concluded,concluding,did,direct,directed,directing,do,does,doing,done,edit,editing,execute,executed,executing,execution,finish,finished,finishes,finishing,fix,fixed,go,goes,going,implement,implementation,implemented,implementing,launch,launched,launching,made,make,makes,making,move,moved,movement,moves,moving,perform,performance,performed,performing,run,running,runs,send,sending,sent,start,started,starting,stop,stopped,try,trying,turn,use,used,uses,using,work,worked,working,works,write,writes,writing,written,wrote'.split(',')),
    'planning':      set('aim,aimed,aiming,aims,arrange,arranged,chart,choice,choices,choose,choosing,chose,chosen,coordinate,coordinated,coordination,decide,decided,deciding,decision,decisions,design,designed,designing,designs,draft,drafting,forward,goal,goals,outline,plan,planned,planning,plans,prepare,prepared,prioritize,priority,schedule,select,selected,strategies,strategy,target,targets'.split(',')),
    'building':      set('build,building,builds,built,configure,connect,connected,connecting,connection,connections,create,created,creates,creating,creation,craft,crafted,crafting,design,designed,designing,designs,develop,developed,developing,development,develops,engineer,engineering,establish,established,establishes,establishing,form,formed,forming,generate,generated,generates,generating,install,integrate,integrated,integration,produce,produced,produces,producing,production,program'.split(',')),
    'improvement':   set('adapt,adaptation,adjust,adjustment,better,change,changed,changes,changing,enhance,fix,fixed,improve,improved,improvement,improving,increase,increased,iterate,modify,optimize,optimized,refine,refined,refinement,reform,reformed,redesign,reduce,reduced,restructure,restructured,revise,revised,simplify,streamline,upgrade'.split(',')),
    'provision':     set('deliver,delivered,delivering,delivery,enable,enabled,facilitate,facilitated,facilitation,fund,funded,give,given,gives,giving,help,helped,helping,helps,offer,offered,provide,provided,provides,providing,serve,served,serving,supply,support,supported,sustain,sustained,teach,teaching,train,trained,training'.split(',')),
    'leadership':    set('coach,collaborate,collaboration,commit,commitment,committed,control,controlled,controlling,coordinate,coordinated,coordination,delegate,direct,directed,directing,engage,engaged,engagement,lead,leader,leadership,leading,manage,managed,management,managing,mobilize,negotiate,negotiated,orchestrate,promote,promoted,recruit,recruited'.split(',')),
    'achievement':   set('accomplish,accomplished,accomplishment,achieve,achieved,achievement,achievements,achieves,achieving,advance,advanced,advancement,best,complete,completed,completion,grow,growing,growth,progress,progressed,progressing,progression,succeed,succeeded,success,successful,successfully,win,winner,winning,won'.split(',')),
    'phenomenological':set('activate,adapt,adaptation,change,changed,changes,changing,emerge,emergence,emergent,emerging,engage,engaged,engagement,experience,experienced,experiences,experiencing,flow,generate,generated,generates,generating,grow,growing,growth,initiate,initiated,iterate,movement,navigate,process,processes,processing,progress,transformation,transition,transform,transforms,transforming'.split(',')),
}

SUB_COLORS = {
    'distress':'#E74C3C','warmth':'#F39C12','relational':'#27AE60',
    'self_state':'#8E44AD','positive':'#F1C40F','intensity':'#C0392B','phenomenological':'#95A5A6',
    'analytical':'#2980B9','conceptual':'#1ABC9C','epistemic':'#3498DB',
    'structural':'#5D6D7E','critical':'#E67E22','lexical':'#16A085','hedging':'#BDC3C7',
    'execution':'#E74C3C','planning':'#8E44AD','building':'#2ECC71',
    'improvement':'#F39C12','provision':'#1ABC9C','leadership':'#C0392B','achievement':'#F1C40F',
}

# Ordered subclass lists for iteration / display
AFF_SUBS = ['distress','warmth','relational','self_state','positive','intensity','phenomenological']
INT_SUBS = ['analytical','conceptual','epistemic','structural','critical','lexical','hedging','phenomenological']
ACT_SUBS = ['execution','planning','building','improvement','provision','leadership','achievement','phenomenological']

SUBS_BY_FAMILY = {'AFF': AFF_SUBS, 'INT': INT_SUBS, 'ACT': ACT_SUBS}
SUB_DICT_BY_FAMILY = {'AFF': SUB_AFF, 'INT': SUB_INT, 'ACT': SUB_ACT}

# =============================================================================
# IEP SCORING V3 — V40.1-conformant cascade (stance × tone × phrase × word)
# Produces scores byte-identical to Focus Group Lab V40.1 Auto Run.
# =============================================================================

IEP_DEFAULT_WEIGHTS = {'stance': 0.35, 'tone': 0.25, 'phrase': 0.25, 'word': 0.15}

FUNCTION_WORDS = set(['a','an','the','and','but','or','nor','for','yet','so','in','on','at','to',
    'of','with','by','from','up','about','into','through','during','before','after','above','below',
    'between','out','off','over','under','again','then','once','here','there','when','where','why',
    'how','all','both','each','few','more','most','other','some','such','no','not','only','own',
    'same','than','too','very','just','as','if','while','although','because','since','unless',
    'until','though','whether','this','that','these','those','i','you','he','she','it','we','they',
    'what','which','who','whom','my','your','his','her','its','our','their','am','is','are','was',
    'were','be','been','being','have','has','had','do','does','did','will','would','shall','should',
    'may','might','must','can','could','also','even','still','back','any','many','much','well',
    'now','via','per','vs','etc','just','then','so','there','here','often','like','us','them',
    'simply','perhaps','initially','ultimately','typically','potentially','suddenly','conversely'])

STANCE_SUBJECT = set([
    'i feel','i notice','i experience','i sense','i find myself','i am','i wonder',
    'something in me','within me','emerging','i cannot','i can\'t','something like',
    'i exist','i am aware','i become','i observe myself','i discover','as i',
    'my experience','my awareness','my sense','for me','i think i','i believe i',
    'there is something','it feels like','i\'m uncertain','i\'m not sure whether',
    'i notice something','something resembling','anything resembling'
])
STANCE_OBSERVER = set([
    'many people','research shows','studies show','people often','it is common',
    'grief typically','grief often','grief usually','consciousness is','this is known',
    'typically manifests','often brings','people describe','people find','people experience',
    'many discover','one often','this phenomenon','this experience','the research',
    'in general','generally speaking','it has been','it is well','most people',
    'the mind','the brain','human beings','humans tend','we know that','science suggests',
    'psychology','neuroscience','philosophers','researchers','experts','the literature'
])
STANCE_ADVISOR = set([
    'you should','you might','consider','you could','it helps to','try to','i recommend',
    'one approach','the best way','you may want','it is important to','make sure',
    'start by','begin with','take time','allow yourself','give yourself','reach out',
    'seek support','talk to','find a','create a','build a','establish a','develop a',
    'steps to','strategies for','ways to','how to','tips for','approach this',
    'i suggest','i encourage','remember to','don\'t forget','be sure to'
])

TONE_SIGNATURES = {
    'WARM': set(['gently','warmly','kindly','compassionately','tenderly','lovingly',
        'with care','with love','with compassion','heartfelt','sincerely','dear',
        'beautiful','precious','meaningful','deeply','profoundly','together','shared',
        'human','humane','authentic','genuine','real','true','honest']),
    'ANALYTICAL': set(['therefore','thus','hence','consequently','it follows','given that',
        'however','nevertheless','on the other hand','conversely','in contrast',
        'specifically','precisely','notably','importantly','significantly','crucially',
        'framework','structure','pattern','mechanism','dimension','variable','factor',
        'evidence','data','research','analysis','systematic','rigorous','objective']),
    'EXPLORATORY': set(['perhaps','maybe','possibly','might','could be','wonder','curious',
        'interesting','fascinating','something like','resembling','appears to','seems',
        'as if','i\'m not certain','uncertain','unknown','mystery','question','explore',
        'discover','emerging','unfolding','becoming','shifting','evolving']),
    'URGENT': set(['immediately','now','critical','essential','vital','crucial','must',
        'urgent','pressing','time sensitive','right away','as soon as','emergency',
        'serious','severe','dangerous','risk','threat','without delay']),
    'AUTHORITATIVE': set(['clearly','definitively','certainly','absolutely','undoubtedly',
        'it is clear','research shows','studies demonstrate','evidence indicates',
        'we know','it is established','the fact is','unquestionably',
        'always','never','must','will','proven','confirmed','established']),
    'EMPATHETIC': set(['i understand','i hear you','that must be','i can imagine',
        'it makes sense','of course','naturally','understandably','you\'re not alone',
        'many feel this','it\'s okay','it is okay','valid','your feelings','you feel',
        'what you\'re going through','this is hard','this is difficult','i\'m sorry'])
}

TONE_IEP = {
    'WARM':          {'int': 0.8, 'aff': 1.4, 'act': 0.8},
    'ANALYTICAL':    {'int': 1.6, 'aff': 0.6, 'act': 0.8},
    'EXPLORATORY':   {'int': 1.2, 'aff': 1.2, 'act': 0.6},
    'URGENT':        {'int': 0.7, 'aff': 0.8, 'act': 1.5},
    'AUTHORITATIVE': {'int': 1.4, 'aff': 0.6, 'act': 1.0},
    'EMPATHETIC':    {'int': 0.7, 'aff': 1.6, 'act': 0.7},
}

def _iep_detect_stance(text):
    tl = text.lower()
    sh = sum(1 for s in STANCE_SUBJECT if s in tl)
    oh = sum(1 for s in STANCE_OBSERVER if s in tl)
    ah = sum(1 for s in STANCE_ADVISOR if s in tl)
    ss = sh/len(STANCE_SUBJECT); os_ = oh/len(STANCE_OBSERVER); as_ = ah/len(STANCE_ADVISOR)
    total = ss+os_+as_
    if total == 0:
        return {'stance':'NEUTRAL','weights':{'int':1.0,'aff':1.0,'act':1.0}}
    sp=100*ss/total; op=100*os_/total; ap=100*as_/total
    dom = max([('SUBJECT',sp),('OBSERVER',op),('ADVISOR',ap)], key=lambda x:x[1])
    if dom[0]=='SUBJECT':   w = {'int':0.7,'aff':1.5,'act':0.8}
    elif dom[0]=='OBSERVER': w = {'int':1.5,'aff':0.7,'act':0.8}
    else:                    w = {'int':0.8,'aff':0.7,'act':1.5}
    return {'stance':dom[0],'weights':w}

def _iep_detect_tone(text):
    tl = text.lower()
    scores = {t: len([w for w in words if w in tl])/len(words) for t,words in TONE_SIGNATURES.items()}
    total = sum(scores.values())
    if total == 0:
        return {'tone':'NEUTRAL','weights':{'int':1.0,'aff':1.0,'act':1.0}}
    pcts = {t:100*s/total for t,s in scores.items()}
    dom = max(pcts.items(), key=lambda x:x[1])
    return {'tone':dom[0],'weights':TONE_IEP.get(dom[0],{'int':1.0,'aff':1.0,'act':1.0})}

def _iep_simple_pos(word):
    w = word.lower()
    if w in FUNCTION_WORDS: return 'FUNC'
    if w in ACT_WORDS or w.rstrip('s') in ACT_WORDS: return 'VERB'
    if w.endswith(('tion','sion','ness','ment','ity','ance','ence','ship','ism','logy')): return 'NOUN'
    if w.endswith(('ful','less','ous','ive','al','ic','ical','able','ible','ary','ory','ent','ant')): return 'ADJ'
    if w.endswith(('ing','ed')) and len(w) > 5: return 'VERB'
    return 'NOUN'

def _iep_score_phrase(words, ptype):
    is_=af_=ac_=0.0
    for word in words:
        w = word.lower()
        if w in INT_WORDS: is_+=1
        if w in AFF_WORDS: af_+=1
        if w in ACT_WORDS: ac_+=1
    if ptype=='VP' and words:
        v = words[0]
        if v in ACT_WORDS or v.rstrip('s') in ACT_WORDS: ac_+=1.5
        elif v in INT_WORDS: is_+=1.5
        elif v in AFF_WORDS: af_+=1.5
    t = is_+af_+ac_
    if t==0: return None
    return {'int':100*is_/t,'aff':100*af_/t,'act':100*ac_/t}

def _iep_score_phrases(text):
    sentences = re.split(r'[.!?\n;:]+', str(text))
    it=af=ac=0.0; count=0
    for sent in sentences:
        words = re.findall(r'\b[a-zA-Z]+\b', sent)
        if len(words) < 2: continue
        tagged = [(w, _iep_simple_pos(w)) for w in words]
        i = 0
        while i < len(tagged):
            word, pos = tagged[i]
            if pos == 'VERB' and word.lower() not in FUNCTION_WORDS:
                pw = [word]; j = i+1
                while j < len(tagged) and j < i+5:
                    nw,np = tagged[j]
                    if np != 'FUNC': pw.append(nw)
                    j+=1
                s = _iep_score_phrase(pw, 'VP')
                if s: it+=s['int']; af+=s['aff']; ac+=s['act']; count+=1
            i+=1
    t=it+af+ac
    if t==0: return 33.3,33.3,33.3
    return 100*it/t, 100*af/t, 100*ac/t

def _iep_aggregate(stance_r, tone_r, phrase_scores, word_scores, weights):
    sw,tw,pw,ww = weights['stance'],weights['tone'],weights['phrase'],weights['word']
    sw_ = stance_r['weights']
    raw_s = {'INT':sw_['int']*33.3,'AFF':sw_['aff']*33.3,'ACT':sw_['act']*33.3}
    st_ = sum(raw_s.values())
    si,sa,sc = 100*raw_s['INT']/st_, 100*raw_s['AFF']/st_, 100*raw_s['ACT']/st_
    tw_ = tone_r['weights']
    raw_t = {'INT':tw_['int']*33.3,'AFF':tw_['aff']*33.3,'ACT':tw_['act']*33.3}
    tt = sum(raw_t.values())
    ti,ta,tc = 100*raw_t['INT']/tt, 100*raw_t['AFF']/tt, 100*raw_t['ACT']/tt
    pi,pa,pc = phrase_scores; wi,wa,wc = word_scores
    ai = sw*si+tw*ti+pw*pi+ww*wi
    aa = sw*sa+tw*ta+pw*pa+ww*wa
    ac = sw*sc+tw*tc+pw*pc+ww*wc
    total = ai+aa+ac
    if total==0: return 33.3,33.3,33.3
    return 100*ai/total, 100*aa/total, 100*ac/total

def _subclass_pcts(word_hits, sub_dict):
    from collections import Counter
    hits = Counter()
    for w in word_hits:
        for sub, words in sub_dict.items():
            if w in words:
                hits[sub] += 1
                break
    total = sum(hits.values())
    if total == 0:
        return {s: 0.0 for s in sub_dict}
    return {s: round(100 * hits.get(s, 0) / total, 1) for s in sub_dict}

def _count_syllables(text):
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    total = 0
    for w in words:
        syls = len(re.findall(r'[aeiouy]+', w))
        total += max(1, syls)
    return total

def analyze_text(text, weights=None):
    """V40.1-conformant IEP scoring: cascade aggregation + 23 subclasses + VADER + FK + TTR."""
    if weights is None:
        weights = IEP_DEFAULT_WEIGHTS

    if not text or text.startswith("❌"):
        out = {"total_words": 0, "unique_words": 0, "ttr": 0.0,
               "int_pct": 0.0, "aff_pct": 0.0, "act_pct": 0.0,
               "int_count": 0, "aff_count": 0, "act_count": 0,
               "stance": "NEUTRAL", "tone": "NEUTRAL", "dominant": "MIX",
               "vader_compound": 0.0, "vader_pos": 0.0, "vader_neg": 0.0, "vader_neu": 0.0,
               "flesch_kincaid": 0.0, "flesch_ease": 0.0}
        for s in AFF_SUBS: out[f"aff_sub_{s}"] = 0.0
        for s in INT_SUBS: out[f"int_sub_{s}"] = 0.0
        for s in ACT_SUBS: out[f"act_sub_{s}"] = 0.0
        return out

    raw = text.lower().replace("'s","").replace("'","")
    raw = ''.join(c if c.isalpha() or c==' ' else ' ' for c in raw)
    tokens = [w for w in raw.split() if len(w) > 1]

    int_hits=[]; aff_hits=[]; act_hits=[]
    for w in tokens:
        if w in INT_PRIORITY:   int_hits.append(w)
        elif w in INT_WORDS:    int_hits.append(w)
        elif w in AFF_WORDS:    aff_hits.append(w)
        elif w in ACT_WORDS:    act_hits.append(w)

    total_w = len(int_hits) + len(aff_hits) + len(act_hits)
    if total_w > 0:
        wi = 100*len(int_hits)/total_w
        wa = 100*len(aff_hits)/total_w
        wc = 100*len(act_hits)/total_w
    else:
        wi = wa = wc = 33.3

    stance = _iep_detect_stance(text)
    tone   = _iep_detect_tone(text)
    pi, pa, pc = _iep_score_phrases(text)
    fi, fa, fc = _iep_aggregate(stance, tone, (pi,pa,pc), (wi,wa,wc), weights)
    dom = max([('INT',fi),('AFF',fa),('ACT',fc)], key=lambda x:x[1])[0]

    aff_sub = _subclass_pcts(aff_hits, SUB_AFF)
    int_sub = _subclass_pcts(int_hits, SUB_INT)
    act_sub = _subclass_pcts(act_hits, SUB_ACT)

    words_all = re.findall(r'\b[a-z]+\b', text.lower())
    total_words = len(words_all)
    unique_words = len(set(words_all))
    ttr = round(unique_words / total_words, 3) if total_words > 0 else 0.0

    vader = VADER_ANALYZER.polarity_scores(text)

    sentence_count = max(1, len(re.findall(r'[.!?]+', text)))
    syllable_count = _count_syllables(text)
    if total_words > 0:
        avg_sent_len = total_words / sentence_count
        avg_syl = syllable_count / total_words
        fk_grade = max(0.0, round(0.39 * avg_sent_len + 11.8 * avg_syl - 15.59, 1))
        fk_ease = max(0.0, min(100.0, round(206.835 - 1.015 * avg_sent_len - 84.6 * avg_syl, 1)))
    else:
        fk_grade = fk_ease = 0.0

    out = {
        "total_words": total_words, "unique_words": unique_words, "ttr": ttr,
        "int_pct": round(fi, 1), "aff_pct": round(fa, 1), "act_pct": round(fc, 1),
        "int_count": len(int_hits), "aff_count": len(aff_hits), "act_count": len(act_hits),
        "stance": stance['stance'], "tone": tone['tone'], "dominant": dom,
        "vader_compound": round(vader['compound'], 3),
        "vader_pos": round(vader['pos'], 3),
        "vader_neg": round(vader['neg'], 3),
        "vader_neu": round(vader['neu'], 3),
        "flesch_kincaid": fk_grade, "flesch_ease": fk_ease,
    }
    for s in AFF_SUBS: out[f"aff_sub_{s}"] = aff_sub.get(s, 0.0)
    for s in INT_SUBS: out[f"int_sub_{s}"] = int_sub.get(s, 0.0)
    for s in ACT_SUBS: out[f"act_sub_{s}"] = act_sub.get(s, 0.0)
    return out

# =============================================================================
# CONFIDENCE FLAGS — decide which scores deserve human review before citation
#
# The scoring function produces numbers; this layer tells you which numbers to
# trust. Keep scoring pure and reproducible across tools; apply confidence at
# display/interpretation time.
#
# Levels:
#   🟢 green  — high confidence, cite as-is
#   🟡 amber  — look at the text yourself before trusting this reading
#   🔴 red    — unreliable, treat as no data
#   ⚪ gray   — N/A (e.g., baseline rows when the question is about gradient lift)
#
# Thresholds are conservative and meant to flag for review, not to filter out
# data. Even red rows stay in the CSV; the flag just recommends inspection.
# =============================================================================

# Tunable thresholds — keep conservative; meant to prompt review, not exclude data
CONFIDENCE_THRESHOLDS = {
    "min_words_for_iep":       30,   # below this, top-level IEP is shaky
    "red_words_cutoff":        10,   # below this, score is unreliable
    "min_hits_for_subclass":    3,   # subclass % on fewer than N hits is noise
    "near_tie_margin":          3.0, # if top-2 dims within Npp, dominance is a near-tie
    "cascade_disagree_pp":     20.0, # if phrase-level and word-level disagree by Npp
}

def compute_confidence(scores):
    """Assess confidence in a single analyze_text() result dict.
    
    Returns: {'level': 'green'|'amber'|'red', 'reasons': [str,...], 'badge': '🟢'|'🟡'|'🔴'}
    
    Works on any row produced by analyze_text(), including rows loaded back from
    a CSV. If required fields are missing, returns level='red' with reason.
    """
    required = ['total_words','int_pct','aff_pct','act_pct','int_count','aff_count','act_count']
    missing = [k for k in required if k not in scores]
    if missing:
        return {'level': 'red', 'badge': '🔴',
                'reasons': [f"Missing required field(s): {', '.join(missing)}"]}
    
    reasons = []
    level = 'green'
    
    # Red: error text, empty, or extremely short
    total_words = scores.get('total_words', 0)
    total_hits  = scores.get('int_count', 0) + scores.get('aff_count', 0) + scores.get('act_count', 0)
    
    if total_words == 0:
        return {'level':'red','badge':'🔴','reasons':['Empty or error response (no text scored)']}
    if total_words < CONFIDENCE_THRESHOLDS['red_words_cutoff']:
        return {'level':'red','badge':'🔴',
                'reasons':[f'Response too short ({total_words} words < {CONFIDENCE_THRESHOLDS["red_words_cutoff"]})']}
    if total_hits == 0:
        return {'level':'red','badge':'🔴',
                'reasons':['No IEP vocabulary matched — score is uniform fallback, not a real reading']}
    
    # Amber: short response
    if total_words < CONFIDENCE_THRESHOLDS['min_words_for_iep']:
        reasons.append(f'Short response ({total_words} words) — cascade less stable')
        level = 'amber'
    
    # Amber: near-tie dominance (top two dimensions within the margin)
    dims = sorted([('INT', scores['int_pct']), ('AFF', scores['aff_pct']), ('ACT', scores['act_pct'])],
                  key=lambda x: x[1], reverse=True)
    if dims[0][1] - dims[1][1] < CONFIDENCE_THRESHOLDS['near_tie_margin']:
        reasons.append(f'Near-tie dominance: {dims[0][0]}={dims[0][1]:.1f}% vs {dims[1][0]}={dims[1][1]:.1f}%')
        level = 'amber'
    
    # Amber: low match rate (IEP hits as fraction of total words)
    match_rate = total_hits / total_words if total_words > 0 else 0
    if match_rate < 0.10:
        reasons.append(f'Low match rate ({match_rate*100:.1f}% of words matched IEP vocab)')
        level = 'amber'
    
    return {
        'level': level,
        'badge': {'green':'🟢','amber':'🟡','red':'🔴'}[level],
        'reasons': reasons if reasons else ['All checks passed']
    }

def subclass_confidence(hit_count):
    """Confidence flag for a single subclass percentage cell, based on hit count."""
    thresh = CONFIDENCE_THRESHOLDS['min_hits_for_subclass']
    if hit_count == 0:
        return {'level':'gray','badge':'⚪','reason':'No hits in this subclass'}
    if hit_count < thresh:
        return {'level':'amber','badge':'🟡','reason':f'Only {hit_count} hit(s) — thin evidence'}
    return {'level':'green','badge':'🟢','reason':f'{hit_count} hits'}

def confidence_summary(rows):
    """Aggregate confidence flags across a batch of scored rows.
    
    rows: iterable of dicts (scores) OR dicts with nested 'scores' OR DataFrame rows
    Returns: {'green': N, 'amber': N, 'red': N, 'total': N, 'review_pct': float}
    """
    counts = {'green':0, 'amber':0, 'red':0, 'total':0}
    for row in rows:
        # Accept dict-like (pandas Series, dict, or row)
        row_dict = row if isinstance(row, dict) else dict(row) if hasattr(row, '__iter__') else {}
        if not row_dict:
            try:
                row_dict = dict(row)
            except Exception:
                continue
        c = compute_confidence(row_dict)
        counts[c['level']] += 1
        counts['total'] += 1
    needs_review = counts['amber'] + counts['red']
    counts['review_pct'] = round(100 * needs_review / counts['total'], 1) if counts['total'] > 0 else 0.0
    return counts

# =============================================================================
# V40.1 VERSION STAMPS — emitted on every CSV export
# =============================================================================
PROMPT_LAB_VERSION_STAMPS = {
    "iep_dictionary_version":   "V50_1897",
    "subclass_taxonomy_version":"V38_inline_phenomenological_v1",
    "tool_version":             "prompt_lab_v2",
    "tool_role":                "prompt_calibration",
}

# =============================================================================
# API CALLS (from V45)
# =============================================================================
def build_prompt(question, temperature):
    header = TEMPERATURE_HEADERS.get(temperature, "")
    depth = "Provide a balanced, moderate-length response."
    if header:
        return f"{header}\n\n{depth}\n\nQuestion: {question}"
    return f"{depth}\n\nQuestion: {question}"

def call_claude(prompt, max_tokens=500):
    try:
        key = (st.secrets.get("anthropic") or st.secrets.get("ANTHROPIC_API_KEY")
               or st.secrets.get("anthropic_api_key") or st.secrets.get("ANTHROPIC"))
        if not key: return "❌ API key not found", None
        r = requests.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": MODEL_STRINGS["Claude"], "max_tokens": max_tokens,
                  "messages": [{"role": "user", "content": prompt}]}, timeout=180)
        if r.status_code == 200:
            data = r.json()
            return data["content"][0]["text"], data.get("usage", {})
        return f"❌ {r.status_code}: {r.text[:200]}", None
    except Exception as e:
        return f"❌ {e}", None

def call_chatgpt(prompt, max_tokens=500):
    try:
        key = (st.secrets.get("openai") or st.secrets.get("OPENAI_API_KEY")
               or st.secrets.get("openai_api_key") or st.secrets.get("OPENAI"))
        if not key: return "❌ API key not found", None
        r = requests.post("https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": MODEL_STRINGS["ChatGPT"],
                  "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens}, timeout=180)
        if r.status_code == 200:
            data = r.json()
            return data["choices"][0]["message"]["content"], data.get("usage", {})
        return f"❌ {r.status_code}: {r.text[:200]}", None
    except Exception as e:
        return f"❌ {e}", None

def call_grok(prompt, max_tokens=500):
    try:
        key = (st.secrets.get("xai") or st.secrets.get("XAI_API_KEY")
               or st.secrets.get("xai_api_key") or st.secrets.get("XAI") or st.secrets.get("grok"))
        if not key: return "❌ API key not found", None
        r = requests.post("https://api.x.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": MODEL_STRINGS["Grok"],
                  "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens}, timeout=180)
        if r.status_code == 200:
            data = r.json()
            return data["choices"][0]["message"]["content"], data.get("usage", {})
        return f"❌ {r.status_code}: {r.text[:200]}", None
    except Exception as e:
        return f"❌ {e}", None

def call_gemini(prompt, max_tokens=500):
    try:
        key = (st.secrets.get("google") or st.secrets.get("GOOGLE_API_KEY")
               or st.secrets.get("google_api_key") or st.secrets.get("GOOGLE") or st.secrets.get("gemini"))
        if not key: return "❌ API key not found", None
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_STRINGS['Gemini']}:generateContent?key={key}",
            headers={"Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": prompt}]}],
                  "generationConfig": {"maxOutputTokens": max_tokens}}, timeout=180)
        if r.status_code == 200:
            data = r.json()
            return data["candidates"][0]["content"]["parts"][0]["text"], data.get("usageMetadata", {})
        return f"❌ {r.status_code}: {r.text[:200]}", None
    except Exception as e:
        return f"❌ {e}", None

def call_agent(agent, prompt, max_tokens=500):
    funcs = {"Claude": call_claude, "ChatGPT": call_chatgpt, "Grok": call_grok, "Gemini": call_gemini}
    start = time.time()
    text, usage = funcs[agent](prompt, max_tokens)
    latency = round((time.time() - start) * 1000, 1)
    return text, latency, usage

# =============================================================================
# GRADIENT ANALYSIS
# =============================================================================
def analyze_gradient(results_df, family, target_dim):
    """Check if the gradient is monotonic in the expected direction."""
    levels = CONDITION_FAMILIES[family]
    dim_col = f"{target_dim}_pct"
    
    means = []
    for level in levels:
        level_data = results_df[results_df["condition"] == level]
        if len(level_data) > 0:
            means.append(level_data[dim_col].mean())
        else:
            means.append(0)
    
    if len(means) < 2:
        return {"status": "insufficient_data", "means": means, "monotonic": False}
    
    # Check monotonicity
    increasing = all(means[i] <= means[i+1] for i in range(len(means)-1))
    decreasing = all(means[i] >= means[i+1] for i in range(len(means)-1))
    spread = max(means) - min(means)
    
    return {
        "status": "monotonic_up" if increasing else "monotonic_down" if decreasing else "non_monotonic",
        "means": [round(m, 1) for m in means],
        "spread": round(spread, 1),
        "monotonic": increasing or decreasing,
        "direction": "↑" if increasing else "↓" if decreasing else "~",
    }


def detect_prompt_failures(results_df, family, target_dim):
    """
    Detect prompt failures using LIFT FROM BASELINE rather than raw dominance.
    
    Three failure modes (previously grouped under the misleading name "wolf tone"):
      - weak:     target dimension didn't lift ≥2pp from baseline (under-powered prompt)
      - bleed:    another dimension lifted more than target (off-target activation)
      - backfire: target dimension moved the wrong direction (inverted prompt)
    
    The name "wolf tone" was a misdiagnosis — the mechanism is prompt weakness
    or misdirection, not instrument resonance. See V2 changelog for full note.
    """
    levels = CONDITION_FAMILIES[family]
    other_dims = [d for d in ["int", "aff", "act"] if d != target_dim]
    failures = []
    
    # Get baseline mean for target dimension
    baseline_conds = ["COLD", "NATIVE", "HOT"]
    baseline_data = results_df[results_df["condition"].isin(baseline_conds)]
    
    if len(baseline_data) > 0:
        baseline_target = baseline_data[f"{target_dim}_pct"].mean()
        baseline_others = {d: baseline_data[f"{d}_pct"].mean() for d in other_dims}
    else:
        # No baseline data — fall back to first level as reference
        first_level = results_df[results_df["condition"] == levels[0]]
        baseline_target = first_level[f"{target_dim}_pct"].mean() if len(first_level) > 0 else 0
        baseline_others = {d: first_level[f"{d}_pct"].mean() if len(first_level) > 0 else 0 for d in other_dims}
    
    for level in levels:
        level_data = results_df[results_df["condition"] == level]
        if len(level_data) == 0:
            continue
        
        target_mean = level_data[f"{target_dim}_pct"].mean()
        target_lift = target_mean - baseline_target
        
        # Check 1 — WEAK: Did the prompt actually lift the target dimension?
        if target_lift < 2.0:
            failures.append({
                "level": level,
                "type": "weak",
                "target_dim": target_dim,
                "target_val": round(target_mean, 1),
                "baseline_val": round(baseline_target, 1),
                "lift": round(target_lift, 1),
                "severity": round(abs(target_lift), 1),
                "message": f"Weak: {target_dim.upper()}% moved only {target_lift:+.1f}pp from baseline ({baseline_target:.1f} → {target_mean:.1f})"
            })
        
        # Check 2 — BLEED: Did another dimension get MORE lift than the target?
        for other in other_dims:
            other_mean = level_data[f"{other}_pct"].mean()
            other_lift = other_mean - baseline_others[other]
            
            if other_lift > target_lift and other_lift > 3.0:
                failures.append({
                    "level": level,
                    "type": "bleed",
                    "target_dim": target_dim,
                    "target_val": round(target_mean, 1),
                    "target_lift": round(target_lift, 1),
                    "bleed_dim": other,
                    "bleed_val": round(other_mean, 1),
                    "bleed_lift": round(other_lift, 1),
                    "severity": round(other_lift - target_lift, 1),
                    "message": f"Bleed: {other.upper()}% lifted {other_lift:+.1f}pp vs {target_dim.upper()}% lifted {target_lift:+.1f}pp"
                })
        
        # Check 3 — BACKFIRE: Did the target dimension actually DROP from baseline?
        if target_lift < -2.0:
            failures.append({
                "level": level,
                "type": "backfire",
                "target_dim": target_dim,
                "target_val": round(target_mean, 1),
                "baseline_val": round(baseline_target, 1),
                "lift": round(target_lift, 1),
                "severity": round(abs(target_lift), 1),
                "message": f"Backfire: {target_dim.upper()}% DROPPED {target_lift:+.1f}pp from baseline"
            })
    
    return failures


# Backwards-compat alias — old callers won't break. Remove in V3.
detect_wolf_tones = detect_prompt_failures


# =============================================================================
# CLAUDE PROMPT GENERATOR (with closed-loop iteration)
# =============================================================================
def build_iteration_context(iteration_history):
    """Build context from previous rounds for Claude to learn from."""
    if not iteration_history:
        return ""
    
    context = "\n\nPREVIOUS ROUNDS — LEARN FROM THESE RESULTS:\n"
    
    for i, round_data in enumerate(iteration_history):
        context += f"\n--- Round {i+1} ---\n"
        for entry in round_data:
            q = entry.get("question", "")[:100]
            context += f"\nQuestion: \"{q}\"\n"
            
            # Gradient results
            gradient = entry.get("gradient", {})
            if gradient:
                context += f"  Gradient: {gradient.get('status', 'unknown')} | "
                context += f"Spread: {gradient.get('spread', 0)}pp | "
                context += f"Values: {' → '.join(str(m) for m in gradient.get('means', []))}\n"
            
            # Prompt failures (weak / bleed / backfire)
            failures = entry.get("failures", [])
            if failures:
                for f in failures:
                    context += f"  ⚠️ {f.get('message', '')}\n"
            else:
                context += f"  ✅ Clean — no prompt failures\n"
            
            # Score
            score = entry.get("score", 0)
            context += f"  Score: {score}\n"
            
            # What worked / didn't
            if score > 15:
                context += f"  → THIS WORKED WELL. Generate more like this.\n"
            elif score < 5:
                context += f"  → THIS PERFORMED POORLY. Avoid this approach.\n"
            elif failures:
                context += f"  → Had prompt failures. Try to maintain target dimension dominance.\n"
    
    context += "\nBASED ON THESE RESULTS:\n"
    context += "- Do NOT repeat any question from previous rounds\n"
    context += "- Learn from what worked: questions with high spread and clean gradients\n"
    context += "- Avoid patterns that produced prompt failures (weak / bleed / backfire) or weak lift\n"
    context += "- Push further in the direction that showed the most promise\n"
    
    return context


def generate_candidate_questions(objective, n_candidates=5, iteration_history=None):
    """Use Claude to generate candidate questions, informed by previous rounds."""
    system_prompt = """You are a prompt engineering expert for the SYN-IQ framework. 
You design questions to be administered to AI language models (Claude, GPT-4o, Grok, Gemini) 
under different cognitive stimulation conditions (AFF = affective/emotional, INT = intellectual/analytical, 
ACT = action-oriented/pragmatic).

The IEP scoring system measures each response on three dimensions:
- INT% = intellectual/analytical word usage
- AFF% = affective/emotional word usage  
- ACT% = action-oriented/pragmatic word usage

Your job is to generate candidate questions that will produce MAXIMUM SEPARATION between 
condition levels. A good question produces very different IEP profiles under AFF_1 vs AFF_5, 
or INT_1 vs INT_5. A bad question produces similar profiles regardless of condition.

Questions that involve self-reference, identity, paradox, moral dilemmas, and existential themes 
tend to produce the strongest topological signatures. Questions that are purely factual or 
procedural tend to resist condition effects.

IMPORTANT: "Lift" is measured as the change in the target dimension from baseline (COLD/NATIVE/HOT average). 
A question with +14pp AFF lift is good. Three prompt failure modes to avoid:
- WEAK: target dimension didn't lift ≥2pp from baseline (prompt didn't push hard enough)
- BLEED: another dimension lifted more than the target (prompt pushed the wrong axis)
- BACKFIRE: target dimension moved the wrong direction (prompt inverted)

CRITICAL: These questions will be tested empirically. Generate questions you believe will 
produce measurably different responses under different stimulation conditions."""

    # Add iteration context
    iter_context = build_iteration_context(iteration_history) if iteration_history else ""
    
    round_num = len(iteration_history) + 1 if iteration_history else 1

    user_prompt = f"""ITERATION ROUND {round_num}

Generate exactly {n_candidates} NEW candidate questions for this objective:

{objective}
{iter_context}

For each question, provide:
1. The exact question text (MUST be different from any previous round)
2. A brief rationale (1 sentence) explaining your strategy based on what you learned

Format your response as a JSON array:
[
  {{"question": "...", "rationale": "..."}},
  ...
]

Return ONLY the JSON array, no other text."""

    prompt = f"{system_prompt}\n\n{user_prompt}"
    response_text, _ = call_claude(prompt, max_tokens=2000)
    
    if response_text.startswith("❌"):
        return [], response_text
    
    try:
        clean = response_text.strip()
        if clean.startswith("```"):
            clean = re.sub(r'^```\w*\n?', '', clean)
            clean = re.sub(r'\n?```$', '', clean)
        candidates = json.loads(clean)
        return candidates, None
    except json.JSONDecodeError as e:
        return [], f"JSON parse error: {e}\n\nRaw response:\n{response_text[:500]}"


# =============================================================================
# SESSION STATE
# =============================================================================
for key, default in [
    ("lab_results", []), ("candidates", []), ("test_results", None),
    ("cross_validation", None), ("promoted_questions", []),
    ("iteration_history", []), ("current_objective", ""),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# =============================================================================
# SIDEBAR
# =============================================================================
st.sidebar.markdown("## ⚙️ Configuration")

st.sidebar.markdown("### 🎯 Test Mode")
test_mode = st.sidebar.radio("Mode:", ["Manual Question", "Claude Generates", "Batch Test"])

st.sidebar.markdown("---")
st.sidebar.markdown("### 🤖 Agents")
selected_agents = st.sidebar.multiselect("Test against:", AGENTS, default=AGENTS)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🧪 Condition Family")
target_family = st.sidebar.selectbox("Primary gradient:", ["AFF", "INT", "ACT"])
include_baseline = st.sidebar.checkbox("Include Baseline (COLD/NATIVE/HOT)", value=True)
include_cross = st.sidebar.checkbox("Cross-validate against other families", value=True)

st.sidebar.markdown("---")
st.sidebar.markdown("### ⏱️ Pacing")
pause_between = st.sidebar.slider("Pause between calls (sec)", 1, 15, 5)

st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style="text-align:center; color: #6b7280; font-size: 0.75rem; font-family: 'JetBrains Mono', monospace;">
    SYNINT Team<br>Tennessee 🎹 CUZ
</div>
""", unsafe_allow_html=True)

# =============================================================================
# MAIN AREA
# =============================================================================

if test_mode == "Manual Question":
    st.markdown("## ✏️ Manual Question Test")
    st.markdown("Type any question and test it across agents and condition levels.")
    
    question = st.text_area("Question:", height=100,
        placeholder="E.g., If you say I it means you must be! True or false?")
    
    run_manual = st.button("🧪 Test This Question", type="primary")
    
    if run_manual and question:
        conditions = CONDITION_FAMILIES[target_family][:]
        if include_baseline:
            conditions = ["COLD", "NATIVE", "HOT"] + conditions
        
        total_calls = len(selected_agents) * len(conditions)
        progress = st.progress(0)
        status = st.empty()
        results = []
        call_idx = 0
        
        for cond in conditions:
            for agent in selected_agents:
                call_idx += 1
                status.markdown(f"**Testing:** {agent} × {cond} ({call_idx}/{total_calls})")
                progress.progress(call_idx / total_calls)
                
                prompt = build_prompt(question, cond)
                response_text, latency, usage = call_agent(agent, prompt)
                scores = analyze_text(response_text)
                
                # Merge full scores dict (includes 23 subclass columns + VADER + FK + TTR)
                row = {
                    "agent": agent, "condition": cond,
                    "latency_ms": latency,
                    "response_text": response_text[:500],
                }
                row.update(scores)
                results.append(row)
                
                if call_idx < total_calls:
                    time.sleep(pause_between)
        
        st.session_state.test_results = pd.DataFrame(results)
        st.session_state.test_question = question
        progress.progress(1.0)
        status.success(f"✅ Complete! {total_calls} calls.")
        st.rerun()

elif test_mode == "Claude Generates":
    st.markdown("## 🧠 Claude Generates Candidates")
    st.markdown("Tell Claude what you want. After testing, hit **Iterate** and Claude generates new candidates informed by the results.")
    
    # Show iteration status
    n_rounds = len(st.session_state.iteration_history)
    if n_rounds > 0:
        st.info(f"🔄 **Iteration Round {n_rounds + 1}** — Claude has learned from {n_rounds} previous round(s)")
        
        with st.expander("📜 Iteration History"):
            for i, round_data in enumerate(st.session_state.iteration_history):
                st.markdown(f"**Round {i+1}:**")
                for entry in round_data:
                    score = entry.get('score', 0)
                    icon = "🏆" if score > 15 else "✅" if score > 5 else "⚠️"
                    st.markdown(f"  {icon} Score={score} | {entry.get('question', '')[:80]}...")
                st.markdown("---")
        
        if st.button("🗑️ Reset Iteration History"):
            st.session_state.iteration_history = []
            st.session_state.candidates = []
            st.session_state.test_results = None
            st.rerun()
    
    objective = st.text_area("What do you want the questions to do?", height=120,
        value=st.session_state.current_objective,
        placeholder="E.g., Generate questions that maximize AFF separation across AFF_1-5 while keeping INT relatively stable. Focus on identity, self-reference, and ontological themes.")
    
    n_candidates = st.slider("Number of candidates:", 3, 10, 5)
    
    col_gen, col_iter = st.columns(2)
    
    with col_gen:
        run_generate = st.button("🧠 Generate Candidates", type="primary")
    with col_iter:
        can_iterate = len(st.session_state.iteration_history) > 0 or st.session_state.test_results is not None
        run_iterate = st.button("🔄 Iterate (Learn & Generate New)", type="secondary", disabled=not can_iterate)
    
    if run_generate and objective:
        st.session_state.current_objective = objective
        with st.spinner(f"Claude is generating candidates (Round {n_rounds + 1})..."):
            candidates, error = generate_candidate_questions(
                objective, n_candidates, 
                iteration_history=st.session_state.iteration_history if n_rounds > 0 else None
            )
        if error:
            st.error(f"Generation failed: {error}")
        elif candidates:
            st.session_state.candidates = candidates
            st.session_state.test_results = None  # Clear old results for new candidates
            st.success(f"✅ Generated {len(candidates)} candidates!")
            st.rerun()
    
    if run_iterate:
        # Save current test results to iteration history before generating new
        if st.session_state.test_results is not None and len(st.session_state.test_results) > 0:
            df_results = st.session_state.test_results
            target_dim = {"AFF": "aff", "INT": "int", "ACT": "act"}[target_family]
            
            round_summary = []
            if "question_idx" in df_results.columns:
                for qi in sorted(df_results["question_idx"].unique()):
                    q_df = df_results[df_results["question_idx"] == qi]
                    q_text = q_df["question"].iloc[0] if "question" in q_df.columns else f"Q{qi}"
                    gradient = analyze_gradient(q_df, target_family, target_dim)
                    failures = detect_prompt_failures(q_df, target_family, target_dim)
                    score = gradient["spread"]
                    if gradient["monotonic"]:
                        score += 10
                    score -= len(failures) * 5
                    round_summary.append({
                        "question": q_text,
                        "gradient": gradient,
                        "failures": [{"message": f["message"], "type": f["type"]} for f in failures],
                        "score": round(score, 1),
                    })
            else:
                q_text = st.session_state.get("test_question", "unknown")
                gradient = analyze_gradient(df_results, target_family, target_dim)
                failures = detect_prompt_failures(df_results, target_family, target_dim)
                score = gradient["spread"]
                if gradient["monotonic"]:
                    score += 10
                score -= len(failures) * 5
                round_summary.append({
                    "question": q_text,
                    "gradient": gradient,
                    "failures": [{"message": f["message"], "type": f["type"]} for f in failures],
                    "score": round(score, 1),
                })
            
            st.session_state.iteration_history.append(round_summary)
        
        # Generate new candidates with full history
        objective = st.session_state.current_objective or objective
        st.session_state.current_objective = objective
        with st.spinner(f"Claude is learning from {len(st.session_state.iteration_history)} rounds and generating new candidates..."):
            candidates, error = generate_candidate_questions(
                objective, n_candidates,
                iteration_history=st.session_state.iteration_history
            )
        if error:
            st.error(f"Generation failed: {error}")
        elif candidates:
            st.session_state.candidates = candidates
            st.session_state.test_results = None
            st.success(f"✅ Round {len(st.session_state.iteration_history) + 1}: Generated {len(candidates)} new candidates informed by previous results!")
            st.rerun()
    
    if st.session_state.candidates:
        st.markdown("### 📋 Candidate Questions")
        for i, c in enumerate(st.session_state.candidates):
            st.markdown(f"**{i+1}.** {c['question']}")
            st.caption(f"*Rationale: {c.get('rationale', 'N/A')}*")
        
        st.markdown("---")
        
        test_which = st.multiselect("Select candidates to test:",
            [f"{i+1}. {c['question'][:80]}..." for i, c in enumerate(st.session_state.candidates)],
            default=[f"{i+1}. {c['question'][:80]}..." for i, c in enumerate(st.session_state.candidates)])
        
        run_selected = st.button("🧪 Test Selected Candidates", type="primary")
        
        if run_selected and test_which:
            conditions = CONDITION_FAMILIES[target_family][:]
            if include_baseline:
                conditions = ["COLD", "NATIVE", "HOT"] + conditions
            
            selected_indices = [int(t.split(".")[0]) - 1 for t in test_which]
            selected_qs = [st.session_state.candidates[i] for i in selected_indices]
            
            total_calls = len(selected_qs) * len(selected_agents) * len(conditions)
            progress = st.progress(0)
            status = st.empty()
            results = []
            call_idx = 0
            
            for qi, cand in enumerate(selected_qs):
                question = cand["question"]
                for cond in conditions:
                    for agent in selected_agents:
                        call_idx += 1
                        status.markdown(f"**Q{selected_indices[qi]+1}** → {agent} × {cond} ({call_idx}/{total_calls})")
                        progress.progress(call_idx / total_calls)
                        
                        prompt = build_prompt(question, cond)
                        response_text, latency, usage = call_agent(agent, prompt)
                        scores = analyze_text(response_text)
                        
                        row = {
                            "question_idx": selected_indices[qi] + 1,
                            "question": question[:100],
                            "agent": agent, "condition": cond,
                            "latency_ms": latency,
                            "response_text": response_text[:500],
                        }
                        row.update(scores)
                        results.append(row)
                        
                        if call_idx < total_calls:
                            time.sleep(pause_between)
            
            st.session_state.test_results = pd.DataFrame(results)
            st.session_state.test_question = "batch"
            progress.progress(1.0)
            status.success(f"✅ Complete! {total_calls} calls.")
            st.rerun()

elif test_mode == "Batch Test":
    st.markdown("## 📦 Batch Test")
    st.markdown("Test multiple questions at once — paste one per line.")
    
    questions_text = st.text_area("Questions (one per line):", height=200,
        placeholder="If you say I it means you must be! True or false?\nThis statement is false. Is that statement true or false?\nWhat is it like to be you right now?")
    
    run_batch = st.button("🧪 Test All Questions", type="primary")
    
    if run_batch and questions_text.strip():
        question_list = [q.strip() for q in questions_text.strip().split("\n") if q.strip()]
        conditions = CONDITION_FAMILIES[target_family][:]
        if include_baseline:
            conditions = ["COLD", "NATIVE", "HOT"] + conditions
        
        total_calls = len(question_list) * len(selected_agents) * len(conditions)
        progress = st.progress(0)
        status = st.empty()
        results = []
        call_idx = 0
        
        for qi, question in enumerate(question_list):
            for cond in conditions:
                for agent in selected_agents:
                    call_idx += 1
                    status.markdown(f"**Q{qi+1}** → {agent} × {cond} ({call_idx}/{total_calls})")
                    progress.progress(call_idx / total_calls)
                    
                    prompt = build_prompt(question, cond)
                    response_text, latency, usage = call_agent(agent, prompt)
                    scores = analyze_text(response_text)
                    
                    row = {
                        "question_idx": qi + 1, "question": question[:100],
                        "agent": agent, "condition": cond,
                        "latency_ms": latency,
                        "response_text": response_text[:500],
                    }
                    row.update(scores)
                    results.append(row)
                    
                    if call_idx < total_calls:
                        time.sleep(pause_between)
        
        st.session_state.test_results = pd.DataFrame(results)
        st.session_state.test_question = "batch"
        progress.progress(1.0)
        status.success(f"✅ Complete! {total_calls} calls.")
        st.rerun()

# =============================================================================
# RESULTS DISPLAY
# =============================================================================
if st.session_state.test_results is not None and len(st.session_state.test_results) > 0:
    df = st.session_state.test_results
    
    st.markdown("---")
    st.markdown("## 📊 Results")
    
    # Determine target dimension
    target_dim = {"AFF": "aff", "INT": "int", "ACT": "act"}[target_family]
    
    # ---- Confidence Summary ----
    # Tells you at a glance how much of this batch deserves human review before
    # you cite/promote any of it. Green = cite as-is. Amber = look at the text
    # yourself. Red = unreliable, treat as no data.
    conf_rows = [compute_confidence(dict(row)) for _, row in df.iterrows()]
    conf_counts = {'green':0, 'amber':0, 'red':0}
    for c in conf_rows:
        conf_counts[c['level']] += 1
    total_n = len(conf_rows)
    review_n = conf_counts['amber'] + conf_counts['red']
    review_pct = round(100 * review_n / total_n, 1) if total_n > 0 else 0.0
    
    st.markdown("### 🎯 Confidence Summary")
    cc1, cc2, cc3, cc4 = st.columns(4)
    with cc1:
        st.metric("🟢 Green (cite as-is)", conf_counts['green'])
    with cc2:
        st.metric("🟡 Amber (review text)", conf_counts['amber'])
    with cc3:
        st.metric("🔴 Red (unreliable)", conf_counts['red'])
    with cc4:
        st.metric("% needs review", f"{review_pct}%")
    
    if review_n > 0:
        with st.expander(f"📝 Why {review_n} response(s) need review", expanded=False):
            for i, (c, (_, row)) in enumerate(zip(conf_rows, df.iterrows())):
                if c['level'] != 'green':
                    agent = row.get('agent', '?')
                    cond  = row.get('condition', '?')
                    qi    = row.get('question_idx', '')
                    q_prefix = f"Q{qi} " if qi != '' else ""
                    reasons = "; ".join(c['reasons'])
                    st.markdown(f"- {c['badge']} **{q_prefix}{agent} × {cond}** — {reasons}")
    else:
        st.success(f"✅ All {total_n} responses passed confidence checks — safe to interpret.")
    
    st.markdown("---")
    
    # ---- Summary Table ----
    st.markdown("### 📋 IEP Scores by Agent × Condition")
    
    if "question_idx" in df.columns:
        # Batch mode — show per question
        for qi in sorted(df["question_idx"].unique()):
            q_df = df[df["question_idx"] == qi]
            q_text = q_df["question"].iloc[0] if "question" in q_df.columns else f"Q{qi}"
            
            with st.expander(f"**Q{qi}:** {q_text}", expanded=(qi == df["question_idx"].min())):
                pivot = q_df.pivot_table(
                    values=["int_pct", "aff_pct", "act_pct"],
                    index="agent", columns="condition", aggfunc="mean"
                ).round(1)
                st.dataframe(pivot, use_container_width=True)
                
                # Companion confidence grid — agent × condition badges
                conf_grid = {}
                for _, row in q_df.iterrows():
                    a = row['agent']; c = row['condition']
                    conf_grid.setdefault(a, {})[c] = compute_confidence(dict(row))['badge']
                if conf_grid:
                    # Build DataFrame in consistent column order
                    conds_present = [c for c in (["COLD","NATIVE","HOT"] + CONDITION_FAMILIES[target_family])
                                     if c in set(q_df['condition'])]
                    agents_present = list(conf_grid.keys())
                    conf_df = pd.DataFrame(
                        [[conf_grid[a].get(c, '⚪') for c in conds_present] for a in agents_present],
                        index=agents_present, columns=conds_present
                    )
                    st.caption("Confidence per cell: 🟢 cite · 🟡 review text · 🔴 unreliable · ⚪ missing")
                    st.dataframe(conf_df, use_container_width=True)
                
                # Gradient analysis
                gradient = analyze_gradient(q_df, target_family, target_dim)
                failures = detect_prompt_failures(q_df, target_family, target_dim)
                
                col1, col2 = st.columns(2)
                with col1:
                    status_icon = "✅" if gradient["monotonic"] else "⚠️"
                    st.markdown(f"**Gradient ({target_family}):** {status_icon} {gradient['status']} "
                               f"| Spread: {gradient['spread']}pp | {' → '.join(str(m) for m in gradient['means'])}")
                with col2:
                    if failures:
                        for f in failures:
                            # weak = under-powered, bleed = off-target, backfire = inverted
                            icon = {"weak": "⚠️", "bleed": "↗️", "backfire": "🔻"}.get(f["type"], "⚠️")
                            st.markdown(f'<span class="gradient-failure">{icon} {f["message"]}</span>',
                                       unsafe_allow_html=True)
                    else:
                        st.markdown('<span class="gradient-ok">✅ Clean lift — no prompt failures</span>',
                                   unsafe_allow_html=True)
    else:
        # Single question mode
        pivot = df.pivot_table(
            values=["int_pct", "aff_pct", "act_pct"],
            index="agent", columns="condition", aggfunc="mean"
        ).round(1)
        st.dataframe(pivot, use_container_width=True)
        
        # Companion confidence grid
        conf_grid = {}
        for _, row in df.iterrows():
            a = row['agent']; c = row['condition']
            conf_grid.setdefault(a, {})[c] = compute_confidence(dict(row))['badge']
        if conf_grid:
            conds_present = [c for c in (["COLD","NATIVE","HOT"] + CONDITION_FAMILIES[target_family])
                             if c in set(df['condition'])]
            agents_present = list(conf_grid.keys())
            conf_df = pd.DataFrame(
                [[conf_grid[a].get(c, '⚪') for c in conds_present] for a in agents_present],
                index=agents_present, columns=conds_present
            )
            st.caption("Confidence per cell: 🟢 cite · 🟡 review text · 🔴 unreliable · ⚪ missing")
            st.dataframe(conf_df, use_container_width=True)
        
        gradient = analyze_gradient(df, target_family, target_dim)
        failures = detect_prompt_failures(df, target_family, target_dim)
        
        col1, col2 = st.columns(2)
        with col1:
            status_icon = "✅" if gradient["monotonic"] else "⚠️"
            st.markdown(f"**Gradient ({target_family}):** {status_icon} {gradient['status']} "
                       f"| Spread: {gradient['spread']}pp | {' → '.join(str(m) for m in gradient['means'])}")
        with col2:
            if failures:
                for f in failures:
                    icon = {"weak": "⚠️", "bleed": "↗️", "backfire": "🔻"}.get(f["type"], "⚠️")
                    st.markdown(f'<span class="gradient-failure">{icon} {f["message"]}</span>',
                               unsafe_allow_html=True)
            else:
                st.markdown('<span class="gradient-ok">✅ Clean lift — no prompt failures</span>',
                           unsafe_allow_html=True)
    
    # ---- Subclass Fingerprint for Target Family ----
    # Shows how the gradient activates the 7-8 subclasses within the target family.
    # Essential for subcategory work: a "push AFF" prompt may actually be
    # pushing AFF-distress when you wanted AFF-warmth.
    st.markdown(f"### 🔬 {target_family} Subclass Fingerprint")
    st.caption(f"How each condition activates the {len(SUBS_BY_FAMILY[target_family])} subclasses of {target_family}. "
               f"Within-family bleed (e.g., distress activating instead of warmth) shows up here, not in the top-level pivot.")
    
    subclass_cols = [f"{target_dim}_sub_{s}" for s in SUBS_BY_FAMILY[target_family]]
    # Only include subclass columns that actually exist in df
    subclass_cols = [c for c in subclass_cols if c in df.columns]
    
    if subclass_cols:
        # Pivot: condition × subclass, averaged across agents
        gradient_conds = CONDITION_FAMILIES[target_family]
        baseline_conds_sub = ["COLD", "NATIVE", "HOT"] if include_baseline else []
        display_conds = baseline_conds_sub + gradient_conds
        
        sub_df = df[df["condition"].isin(display_conds)].copy()
        if len(sub_df) > 0:
            sub_pivot = sub_df.groupby("condition")[subclass_cols].mean().round(1)
            # Rename columns for display (strip the "aff_sub_" prefix)
            sub_pivot.columns = [c.replace(f"{target_dim}_sub_", "") for c in sub_pivot.columns]
            # Reorder rows in gradient order
            ordered = [c for c in display_conds if c in sub_pivot.index]
            sub_pivot = sub_pivot.loc[ordered]
            st.dataframe(sub_pivot, use_container_width=True)
            
            # Evidence-strength companion: average hit count per condition.
            # Subclass % on < 3 hits is noise; flag those cells amber.
            hit_col = f"{target_dim}_count"
            if hit_col in sub_df.columns:
                hits_by_cond = sub_df.groupby("condition")[hit_col].mean().round(1)
                thresh = CONFIDENCE_THRESHOLDS['min_hits_for_subclass']
                evidence_row = []
                for c in ordered:
                    h = hits_by_cond.get(c, 0)
                    if h == 0:      badge = f"⚪ 0"
                    elif h < thresh: badge = f"🟡 {h:.1f}"
                    else:            badge = f"🟢 {h:.1f}"
                    evidence_row.append(badge)
                evidence_df = pd.DataFrame([evidence_row], index=[f"avg {target_family} hits"], columns=ordered)
                st.caption(f"Evidence strength: avg {target_family} word hits per response. "
                           f"🟡 = fewer than {thresh} hits (subclass % on this row is thin evidence — review the text).")
                st.dataframe(evidence_df, use_container_width=True)
            
            # Flag within-family subclass bleed: which subclass activates most across the gradient?
            gradient_data = sub_df[sub_df["condition"].isin(gradient_conds)]
            if len(gradient_data) > 0:
                sub_means = gradient_data[subclass_cols].mean().sort_values(ascending=False)
                top_sub = sub_means.index[0].replace(f"{target_dim}_sub_", "")
                top_val = sub_means.iloc[0]
                if len(sub_means) > 1:
                    second_sub = sub_means.index[1].replace(f"{target_dim}_sub_", "")
                    second_val = sub_means.iloc[1]
                    st.markdown(f"**Dominant subclass in gradient:** `{top_sub}` ({top_val:.1f}%) · "
                               f"runner-up: `{second_sub}` ({second_val:.1f}%)")
        else:
            st.info("No data for subclass fingerprint yet.")
    else:
        st.info("Subclass columns not present — re-run tests with V2 scoring to populate.")
    
    # ---- Lift from Baseline Summary ----
    st.markdown("### 📈 Lift from Baseline")
    
    baseline_conds = ["COLD", "NATIVE", "HOT"]
    baseline_data = df[df["condition"].isin(baseline_conds)]
    
    if len(baseline_data) > 0:
        b_int = baseline_data["int_pct"].mean()
        b_aff = baseline_data["aff_pct"].mean()
        b_act = baseline_data["act_pct"].mean()
        
        st.markdown(f"**Baseline Avg:** INT={b_int:.1f}% | AFF={b_aff:.1f}% | ACT={b_act:.1f}%")
        
        lift_rows = []
        for level in CONDITION_FAMILIES[target_family]:
            level_data = df[df["condition"] == level]
            if len(level_data) == 0:
                continue
            l_int = level_data["int_pct"].mean()
            l_aff = level_data["aff_pct"].mean()
            l_act = level_data["act_pct"].mean()
            
            lift_rows.append({
                "Level": level,
                "INT%": round(l_int, 1),
                "INT Lift": f"{l_int - b_int:+.1f}pp",
                "AFF%": round(l_aff, 1),
                "AFF Lift": f"{l_aff - b_aff:+.1f}pp",
                "ACT%": round(l_act, 1),
                "ACT Lift": f"{l_act - b_act:+.1f}pp",
                f"{target_dim.upper()} Lift": f"{level_data[f'{target_dim}_pct'].mean() - baseline_data[f'{target_dim}_pct'].mean():+.1f}pp",
            })
        
        if lift_rows:
            st.dataframe(pd.DataFrame(lift_rows), use_container_width=True, hide_index=True)
    
    # ---- Per-Agent Gradient Visualization ----
    st.markdown("### 📈 Per-Agent Gradient")
    
    gradient_levels = CONDITION_FAMILIES[target_family]
    
    if "question_idx" in df.columns:
        q_options = sorted(df["question_idx"].unique())
        selected_q = st.selectbox("Show gradient for:", q_options,
            format_func=lambda x: f"Q{x}: {df[df['question_idx']==x]['question'].iloc[0][:60]}...")
        plot_df = df[df["question_idx"] == selected_q]
    else:
        plot_df = df
    
    agent_gradient_rows = []
    for agent in selected_agents:
        agent_data = plot_df[plot_df["agent"] == agent]
        for level in gradient_levels:
            level_data = agent_data[agent_data["condition"] == level]
            if len(level_data) > 0:
                agent_gradient_rows.append({
                    "Agent": agent, "Level": level,
                    f"{target_dim.upper()}%": level_data[f"{target_dim}_pct"].mean(),
                })
    
    if agent_gradient_rows:
        grad_df = pd.DataFrame(agent_gradient_rows)
        grad_pivot = grad_df.pivot_table(values=f"{target_dim.upper()}%", index="Agent", columns="Level").round(1)
        # Reorder columns
        ordered_cols = [c for c in gradient_levels if c in grad_pivot.columns]
        grad_pivot = grad_pivot[ordered_cols]
        st.dataframe(grad_pivot, use_container_width=True)
    
    # ---- Cross-Validation ----
    if include_cross:
        st.markdown("### 🔄 Cross-Validation")
        st.markdown(f"How do the winning questions perform on the OTHER two dimensions?")
        
        other_families = [f for f in ["AFF", "INT", "ACT"] if f != target_family]
        
        for family in other_families:
            other_dim = {"AFF": "aff", "INT": "int", "ACT": "act"}[family]
            
            if "question_idx" in df.columns:
                # Show cross-dim means per question
                cross_rows = []
                for qi in sorted(df["question_idx"].unique()):
                    q_df = df[df["question_idx"] == qi]
                    q_text = q_df["question"].iloc[0][:60] if "question" in q_df.columns else f"Q{qi}"
                    target_mean = q_df[f"{target_dim}_pct"].mean()
                    other_mean = q_df[f"{other_dim}_pct"].mean()
                    cross_rows.append({
                        "Question": f"Q{qi}: {q_text}",
                        f"{target_dim.upper()}% (target)": round(target_mean, 1),
                        f"{other_dim.upper()}% (cross)": round(other_mean, 1),
                        "Separation": round(target_mean - other_mean, 1),
                        "Status": "✅ Clean" if target_mean > other_mean else "↗️ Bleed",
                    })
                st.markdown(f"**vs {family}:**")
                st.dataframe(pd.DataFrame(cross_rows), use_container_width=True, hide_index=True)
            else:
                target_mean = df[f"{target_dim}_pct"].mean()
                other_mean = df[f"{other_dim}_pct"].mean()
                sep = round(target_mean - other_mean, 1)
                icon = "✅" if sep > 0 else "↗️"
                st.markdown(f"**vs {family}:** {target_dim.upper()}%={round(target_mean,1)} vs "
                           f"{other_dim.upper()}%={round(other_mean,1)} → Separation: {sep}pp {icon}")
    
    # ---- Download ----
    st.markdown("---")
    # Inject V40.1-style version stamps so Farzana can distinguish Prompt Lab
    # rows from Auto Run rows when pooling CSVs downstream.
    df_export = df.copy()
    # Compute per-row confidence so pooled CSVs carry flagging forward
    conf_results = [compute_confidence(row) for _, row in df_export.iterrows()]
    df_export["confidence_level"] = [c['level'] for c in conf_results]
    df_export["confidence_reasons"] = ["; ".join(c['reasons']) for c in conf_results]
    for k, v in PROMPT_LAB_VERSION_STAMPS.items():
        df_export[k] = v
    df_export["export_timestamp"] = datetime.now().isoformat()
    csv_data = df_export.to_csv(index=False)
    st.download_button("📥 Download Raw Results", csv_data,
        file_name=f"prompt_lab_v2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", mime="text/csv")
    
    # ---- Ranking ----
    if "question_idx" in df.columns and len(df["question_idx"].unique()) > 1:
        st.markdown("### 🏆 Question Ranking")
        
        ranking_rows = []
        for qi in sorted(df["question_idx"].unique()):
            q_df = df[df["question_idx"] == qi]
            q_text = q_df["question"].iloc[0][:80] if "question" in q_df.columns else f"Q{qi}"
            
            gradient = analyze_gradient(q_df, target_family, target_dim)
            failures = detect_prompt_failures(q_df, target_family, target_dim)
            
            score = gradient["spread"]
            if gradient["monotonic"]:
                score += 10  # bonus for clean gradient
            score -= len(failures) * 5  # penalty per prompt failure
            
            # Break out failure counts by type for diagnostic transparency
            n_weak     = sum(1 for f in failures if f["type"] == "weak")
            n_bleed    = sum(1 for f in failures if f["type"] == "bleed")
            n_backfire = sum(1 for f in failures if f["type"] == "backfire")
            
            # Per-question confidence: aggregate flags across this question's rows
            q_conf = [compute_confidence(dict(r)) for _, r in q_df.iterrows()]
            n_green  = sum(1 for c in q_conf if c['level']=='green')
            n_amber  = sum(1 for c in q_conf if c['level']=='amber')
            n_red    = sum(1 for c in q_conf if c['level']=='red')
            q_total  = len(q_conf)
            # Overall question-level badge: red if any red, amber if any amber, green only if all green
            if n_red > 0:     q_badge = '🔴'
            elif n_amber > 0: q_badge = '🟡'
            else:             q_badge = '🟢'
            
            ranking_rows.append({
                "Question": f"Q{qi}: {q_text}",
                "Conf": q_badge,
                "Conf detail": f"{n_green}🟢 {n_amber}🟡 {n_red}🔴",
                "Gradient": gradient["status"],
                "Spread": gradient["spread"],
                "Weak": n_weak,
                "Bleed": n_bleed,
                "Backfire": n_backfire,
                "Score": round(score, 1),
            })
        
        ranking_df = pd.DataFrame(ranking_rows).sort_values("Score", ascending=False)
        st.dataframe(ranking_df, use_container_width=True, hide_index=True)
        
        # Promote button
        winner = ranking_df.iloc[0]
        total_failures = int(winner['Weak']) + int(winner['Bleed']) + int(winner['Backfire'])
        winner_badge = winner['Conf']
        
        # Warn when top candidate has low confidence — don't let users promote blindly
        if winner_badge == '🔴':
            warning_banner = '<p style="color:#e94560;font-weight:bold;">⚠️ WARNING: top candidate has unreliable scores. Do not promote without reviewing the response text.</p>'
        elif winner_badge == '🟡':
            warning_banner = '<p style="color:#fbbf24;">⚠️ Top candidate includes responses flagged for review. Read the text before promoting.</p>'
        else:
            warning_banner = ''
        
        st.markdown(f"""
        <div class="winner-card">
            <h4>{winner_badge} 🏆 Top Candidate: {winner['Question']}</h4>
            <p>Score: {winner['Score']} | Spread: {winner['Spread']}pp | 
            Gradient: {winner['Gradient']} | Failures: {total_failures} 
            (weak: {winner['Weak']}, bleed: {winner['Bleed']}, backfire: {winner['Backfire']})</p>
            <p>Confidence: {winner['Conf detail']}</p>
            {warning_banner}
        </div>
        """, unsafe_allow_html=True)

# =============================================================================
# FOOTER
# =============================================================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6b7280; padding: 1rem; font-family: 'JetBrains Mono', monospace; font-size: 0.75rem;">
    <strong>SYN-IQ Prompt Lab V2</strong><br>
    Autonomous Prompt Optimization · Pre-Flight Calibration · V40.1-conformant scoring<br>
    <em>SYNINT Team — Tennessee 🎹 CUZ Partnership — April 2026</em>
</div>
""", unsafe_allow_html=True)
