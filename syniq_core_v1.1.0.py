"""
syniq_core.py — SYN-IQ Unified Measurement Core
================================================

Version: 1.0.0
Authors: W. C. Kouns (SYNINT Team) + AI collaborators
Date: April 2026

PURPOSE
-------
Single source of truth for SYN-IQ measurement. Every tool in the suite —
V40 ideation (Focus Group Lab), V50 baseline harvester, self-model
architecture probe, cross-model harvester, analyzers, comparators —
imports scoring from here instead of inlining its own copy.

The historical pattern of each tool carrying inline dictionaries and
scorers led to drift: V38 INT_WORDS had 610 terms, V50 had 616, subclass
names diverged (phenomenological vs emergent), and bug fixes had to be
made in 5+ places. This module ends that.

MEASUREMENT STACK
-----------------
Three orthogonal axes measured here, plus V50 validated instruments:

  1. IEP  — INT / AFF / ACT register, with 23 subclasses
            (source: V40.3 + V50, 1,897-term dictionary)
  2. Vt   — S / A / Q / D / R simplex per Paper 2 (Dec 2025 submission)
            (source: V40.3, no-ceiling-cap variant)
  3. CAM  — Concrete / Abstract / Metaphorical representational mode
            (source: syniq_selfmodel_v3.py, self-model harvester V3)
  4. V50 validated instruments — VADER, Flesch-Kincaid, TTR
            (source: V40.3, matching V50's analyze_text block)

PUBLIC API
----------
    score_iep(text, weights=None)      -> dict
    score_vt(text)                     -> dict
    score_cam(text)                    -> dict
    score_validated_instruments(text)  -> dict
    score_all(text)                    -> dict   (convenience: all four merged)
    VERSION_STAMPS                     -> dict   (stamp every CSV row with these)

Any tool that imports these functions receives bit-identical scores
across the suite. Drift is caught by syniq_core_tests.py (frozen corpus
with expected scores).

MAINTENANCE DISCIPLINE
----------------------
This file is reviewed frequently as the canonical instrument. Any change
to dictionaries, scoring logic, or thresholds:
  1. Must bump CORE_VERSION below (semantic versioning).
  2. Must update VERSION_STAMPS so CSVs carry the new stamp.
  3. Must regenerate syniq_core_tests.py expected-values block with
     explicit justification for any changed numbers.
  4. Must be documented in the CHANGELOG section below.

Do not add tool-specific logic here. This module scores text. Period.
API calls, UI rendering, session state, file I/O, prompt building —
all belong in the importing tool, not here.

CHANGELOG
---------
1.0.0 (2026-04-24)
    Initial extraction from V40.3 focus_group_lab and syniq_selfmodel_v3.
    IEP: V50 1,897-term dictionary (616/599/682), V1 phenomenological
         subclass taxonomy (23 subclasses: 7 AFF + 8 INT + 8 ACT).
    Vt:  V40 simplex engine, no ceiling caps, 5 channels (S/A/Q/D/R).
    CAM: V3 dictionary from self-model harvester (~130/130/150 terms).
    V50 instruments: VADER (with graceful fallback), Flesch-Kincaid, TTR.
    Bit-identical to V40.3 on IEP/Vt/validated scoring and to
    syniq_selfmodel_v3.py on CAM scoring.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Dict, List, Optional

# =============================================================================
# CORE VERSION
# =============================================================================

CORE_VERSION = "1.1.0"

# Version stamps — tools should merge these into every CSV row so that
# downstream analysis can tell which scoring regime produced each number.
# The importing tool adds its own tool_version and tool_role on top.
VERSION_STAMPS = {
    "iep_dictionary_version":    "V50_1897",
    "subclass_taxonomy_version": "V1_phenomenological",
    "vt_engine_version":         "V40_simplex_nocap",
    "cam_dictionary_version":    "V3_selfmodel",
    "validated_instruments_version": "V50_vader_fk_ttr",
    "core_version":              CORE_VERSION,
}

# =============================================================================
# IEP — WORD-LEVEL DICTIONARIES (V50-EXACT, 1,897 terms total: 616/599/682)
# =============================================================================
# These are the canonical 3-axis word lists for INT (Intellectual),
# AFF (Affective), ACT (Action). Each term is lowercase, comma-separated.
# Dictionary-size guards below fire at import time if anyone edits a list
# without updating CORE_VERSION — drift-protection rail.

INT_WORDS = set('ability,absolute,absolutely,abstract,abstraction,accuracy,accurate,algorithm,algorithmic,allows,although,always,ambiguity,ambiguous,analogous,analogously,analogy,analysis,analytical,analyze,annotate,annotated,answer,appear,appeared,appears,appraisal,appraise,appraised,approach,approaches,approximate,architecture,argue,argued,argues,arguing,argument,arguments,assert,asserted,assertion,assertions,assess,assessment,assume,assumed,assumes,assuming,assumption,assumptions,axiom,axiomatic,basis,because,bias,biased,boundaries,boundary,but,calculate,calculation,categorical,categorically,categories,categorize,category,causal,causally,causation,cause,caused,causes,certain,certainly,certitude,challenge,challenges,circumscribe,claim,claimed,claims,clarify,clarity,classical,classification,classify,clear,cogent,cogently,cognition,cognitive,coherence,coherent,coherently,communication,compare,comparison,complex,complexity,comprehend,comprehension,computation,computational,compute,conceivable,conceive,conceived,concept,concepts,conceptual,conceptualize,conceptually,conclude,conclusion,conclusions,confirm,confirmation,conjecture,conjectured,conscious,consequence,consequences,consider,consideration,consistency,consistent,consistently,construe,construed,context,contradict,contradiction,contradictory,contrast,correlate,correlated,correlation,could,counterargument,counterexample,counterpoint,criteria,criterion,data,debatable,debate,debated,deconstruct,deconstructed,deconstruction,deduce,deduction,define,defined,definite,definitely,definition,definitive,definitively,delineate,delineated,demarcate,demarcated,demonstrate,demonstration,derivation,derive,derived,derives,describe,described,describing,description,determination,determine,diagnose,diagnosed,diagnosis,diagnostic,differ,difference,differences,different,differentiate,differs,discern,discerned,discernible,disprove,disproven,dissect,dissected,distinguish,effect,effects,elaborate,elaborated,elaboration,elucidate,elucidated,empirical,empirically,enumerate,enumerated,epistemic,epistemological,equate,equation,equivalence,equivalent,erroneous,error,errors,essential,essentially,estimate,estimated,estimation,evaluate,evaluation,evidence,evidently,exact,exactly,examination,examine,except,exemplified,exemplify,exists,experiment,experimental,explain,explained,explaining,explains,explanation,explanations,explicit,explicitly,exploration,explore,explored,exploring,express,expressing,expression,extrapolate,extrapolated,extrapolation,fact,facts,factual,factually,fallacious,fallacy,falsifiable,falsified,falsify,find,finding,formal,formalize,formula,formulate,formulated,formulation,found,framework,frameworks,function,fundamental,fundamentally,generalization,generalize,grasp,grasped,guess,hence,heuristic,heuristics,hierarchy,however,hypothesis,hypothesize,idea,ideas,identity,if,illuminate,illuminated,illuminating,implausible,implication,implications,implied,implies,imply,implying,incompleteness,inconsistency,inconsistent,indicate,indicated,indicates,indicating,indication,indicative,individual,infer,inference,infinite,information,insight,insightful,insights,instead,insufficient,intellectual,intellectually,interaction,internal,interpolate,interpret,interpretation,interpretations,interpreted,interpreting,invalid,investigate,investigated,investigation,judge,judgement,judgment,justification,justified,justify,know,knowing,knowledge,knowledgeable,known,language,languages,leads,level,likelihood,likely,limitations,limits,linguistic,literal,literally,logic,logical,logically,maybe,meaning,meaningful,meaningfully,measure,measurement,mechanism,mechanisms,meta,method,methodical,methodically,methodology,metrics,model,models,moreover,namely,natural,nature,nearly,necessarily,necessary,necessity,never,nonetheless,notice,noticed,noticing,notion,notions,objection,objectively,objectivity,observation,observations,observe,observed,obvious,obviously,order,ordered,organization,organize,otherwise,ought,paradigm,paradox,paradoxical,paradoxically,pattern,patterns,perhaps,perspective,philosophical,philosophically,philosophy,physical,plausibility,plausible,possibly,postulate,postulated,postulation,potential,pragmatic,pragmatically,precise,precision,predicate,predicated,predict,predictable,predicted,prediction,predictions,premise,premises,presumably,presume,presumed,presumption,principle,principles,probably,problem,procedural,procedure,process,processes,processing,proof,propose,proposed,proposition,prove,proven,purpose,quantify,quantitative,queried,query,question,questions,rather,rational,rationale,rationality,rationally,realize,realized,reason,reasoned,reasoning,reasons,rebut,rebuttal,recognition,recognize,reconsider,reconsidered,refer,reference,refers,refine,refined,refinement,reflecting,reflection,refutation,refute,refuted,requirement,requires,response,responses,result,resulting,results,rigor,rigorous,rigorously,role,rule,rules,schema,scrutinize,scrutinized,scrutiny,seem,seemed,seems,semantic,semantically,sequence,sequential,should,significance,significant,significantly,simple,simply,simultaneously,singular,specific,specifically,specification,specify,standard,standards,state,states,step,steps,stipulate,stipulated,strategies,strategy,structural,structure,subject,subjective,subjectively,subjectivity,substantiate,substantiated,sufficient,sufficiently,suggests,summarize,summarized,summary,suppose,supposed,supposedly,supposition,sure,surely,syllogism,syllogistic,synthesis,synthesize,synthesized,system,systematic,systematically,systems,tactic,tactics,taxonomy,technique,test,tested,testing,theorem,theoretical,theoretically,theorize,theory,thereby,therefore,thesis,think,thinking,thought,thoughts,thus,trivial,trivially,unambiguous,underlying,understand,understanding,understood,unique,universal,unless,unlikely,valid,validate,validation,validity,value,values,variable,variables,verification,verify,versus,warrant,warranted,whereas,whereby,whether,why,word,words,would'.split(','))  # V50-EXACT (616 terms)

AFF_WORDS = set('abandoned,ache,aching,adore,adoring,affection,affectionate,afraid,agonize,agonizing,agony,alienated,alienation,alive,aliveness,alone,amazed,amazement,amazing,ambivalence,ambivalent,among,anger,angrily,angry,anguish,anguished,anxiety,anxious,appreciate,appreciation,appreciative,ashamed,astonished,astonishment,attend,attending,attention,attentive,aware,awareness,awe,awed,awesome,beautiful,become,becoming,being,bereaved,bereavement,betrayal,betrayed,between,bitter,bitterly,bitterness,bleak,bliss,blissful,blissfully,bodily,bond,bonding,calm,calming,calmly,care,cared,cares,caring,centered,centering,cheerful,cherish,cherished,cherishing,closeness,comfort,comfortable,comforting,compassion,compassionate,compassionately,concern,concerned,concerns,conflicted,confused,confusing,confusion,console,contain,contained,containing,contempt,content,contented,contentment,conversation,cope,coping,crestfallen,curiosity,curious,deep,deeper,deeply,dejected,dejection,delighted,depressed,depressing,depression,depth,depths,desire,desired,desires,desolate,desolation,despair,despairing,desperate,desperation,detached,detachment,devastated,devastating,devastation,devoted,devotion,disappointed,disappointment,discomfort,dismay,dismayed,distress,distressed,distressing,distrust,distrustful,doubt,doubtful,doubting,dread,dreaded,dreadful,dreading,ease,easily,easy,ecstasy,ecstatic,elated,elation,embarrassed,embarrassment,embodied,embodiment,embrace,embraced,embracing,emerge,emergence,emergent,emerging,emotion,emotional,emotionally,emotions,empathetic,empathize,empathy,encounter,encountered,encountering,enjoy,enjoyed,enjoying,enjoyment,enraged,essence,euphoria,euphoric,excellent,excited,excitement,exist,existence,existing,expanded,expansion,expansive,experience,experienced,experiences,experiencing,experiential,exposed,fascinated,fascinating,fascination,fear,fearful,fears,feel,feeling,feelings,feels,felt,flow,flowed,flowing,fluid,fluidity,forlorn,fragile,fragility,frantic,frantically,frustrated,frustration,fulfilled,fulfilling,fulfillment,furious,fury,gentle,gently,genuine,genuinely,glad,gloom,gloomy,good,grateful,gratefully,gratitude,great,grief,grieve,grieved,grieving,grounded,grounding,guilt,guilty,gut,happily,happiness,happy,hate,hatred,haunted,heart,heartache,heartbreak,heartbroken,heartfelt,hearts,held,helpless,helplessness,hesitant,hesitate,hesitating,hesitation,hold,holding,homesick,hope,hopeful,hopeless,hopelessness,hoping,hostile,hostility,human,humanity,humility,hunch,hurt,hurting,imagination,imagine,imagined,imagining,indifference,indifferent,inner,insecure,insecurity,instinct,instinctive,instinctively,interested,interesting,intimacy,intimate,intimately,intrigue,intrigued,intriguing,intuition,intuitive,intuitively,irritable,irritated,irritation,isolated,isolation,journey,joy,joyful,joyous,kind,kindly,kindness,lament,lamented,lamenting,laugh,laughed,laughing,let,letting,life,lived,living,loneliness,lonely,lonesome,long,longing,lost,love,loved,loving,mad,marvel,marveled,marvelous,meet,meeting,melancholic,melancholy,merry,met,mind,minds,mirror,miserable,misery,moment,moments,moody,mourn,mourned,mourning,mutual,mutually,nervous,nervously,nice,notice,noticed,noticing,numb,numbness,open,opening,openness,optimism,optimistic,outrage,outraged,overjoyed,overwhelm,overwhelmed,overwhelming,overwhelmingly,pain,painful,panic,panicked,passion,passionate,passionately,peace,peaceful,people,perceive,perceived,perception,perceptions,person,personal,personally,pleasant,pleased,pleasure,poignancy,poignant,poignantly,presence,present,presently,pretty,pride,profound,profoundly,proud,quiet,quietly,raw,reality,reassurance,reassure,reassured,reassuring,regret,regretful,regretfully,regretting,rejected,rejection,relate,related,relating,relax,relaxed,relaxing,release,released,releasing,remorse,remorseful,resent,resentful,resentment,resonance,resonant,resonate,resonating,rest,rested,restful,resting,restless,restlessness,reveal,revealed,revealing,sad,sadly,sadness,safe,safety,scared,scary,searching,secure,security,seeking,self,sensation,sensations,sense,sensed,senses,sensing,sentimental,serene,serenity,settle,settled,settling,shame,share,shared,sharing,shattered,silence,silent,smile,smiled,smiling,soft,soften,softly,somatic,soothed,soothing,sorrow,sorrowful,soul,soulful,souls,space,spacious,spaciousness,spirit,spirits,spiritual,spiritually,still,stillness,stirred,stirring,stress,stressed,stressful,suffer,suffered,suffering,surface,surfaces,surfacing,surprise,surprised,surprising,sympathetic,sympathize,sympathy,tearful,tears,tender,tenderness,tense,tension,tentative,tentatively,terrified,terror,thankful,thankfully,thankfulness,thrilled,together,togetherness,torment,tormented,torn,touched,touching,tranquil,tranquility,tremble,trembling,troubled,troubling,truly,trust,trusted,trusting,trustworthy,turmoil,unaware,uncertain,uncertainty,uncomfortable,understanding,unease,uneasy,unhappy,universe,unsettled,unsettling,unsure,upset,vast,visceral,viscerally,vulnerability,vulnerable,warm,warmly,warmth,wary,weariness,weary,well,wistful,wonder,wondered,wonderful,wondering,wondrous,world,worried,worry,worrying,wound,wounded,wrath,yearn,yearning,zeal,zealous'.split(','))  # V50-EXACT (599 terms)

ACT_WORDS = set('access,accessed,accessing,accomplish,accomplished,accomplishes,accomplishing,accomplishment,achieve,achieved,achievement,achievements,achieves,achieving,act,acting,action,actions,activate,activated,activates,activating,activation,acts,adapt,adaptation,adapted,adapting,adapts,address,addressed,addresses,addressing,adjust,adjusted,adjusting,adjustment,adjusts,advance,advanced,advancement,advances,advancing,ahead,aim,aimed,aiming,aims,allocate,allocated,allocation,application,applied,applies,apply,applying,arrange,arranged,arrangement,arrangements,ask,asked,asking,assemble,assembled,assign,assigned,assignment,attempt,attempted,attempting,attempts,authorize,authorized,began,begin,beginning,begins,begun,best,better,bolster,bolstered,break,breaking,bring,bringing,broken,brought,budget,build,building,builds,built,calibrate,calibrated,call,called,calling,campaign,canvass,canvassed,carried,carry,carrying,catalogue,catalogued,centralize,centralized,change,changed,changes,changing,channel,channeled,chart,check,checked,checking,choice,choices,choose,choosing,chose,chosen,circumvent,coach,collaborate,collaborated,collaboration,commission,commit,commitment,committed,compile,compiled,complete,completed,completes,completing,completion,conclude,concluded,concludes,concluding,configure,configured,connect,connected,connecting,connection,connections,consolidate,construct,constructed,constructing,constructs,continuation,continue,continued,continues,continuing,control,controlled,controlling,controls,conversion,convert,converted,converting,converts,coordinate,coordinated,coordination,craft,crafted,crafting,create,created,creates,creating,creation,customize,deadline,decide,decided,deciding,decision,decisions,delegate,delegated,delegation,deliver,delivered,delivering,delivers,delivery,deploy,deployed,deploying,deployment,deploys,design,designed,designing,designs,develop,developed,developing,development,develops,did,direct,directed,directing,dive,diving,do,does,doing,done,draft,drafting,edit,editing,effort,efforts,eliminate,eliminated,elimination,employ,employed,employing,employs,enable,enabled,end,ended,ending,ends,enforce,enforced,enforcement,engage,engaged,engagement,engineer,engineering,enroll,enrolled,enrollment,equip,equipped,establish,established,establishes,establishing,establishment,execute,executed,executes,executing,execution,expedite,facilitate,facilitated,facilitation,finalize,finalized,finish,finished,finishes,finishing,fix,fixed,fixes,fixing,focus,focused,focusing,form,formation,formed,forming,forms,forward,fund,funded,funding,gather,gathered,gathering,generate,generated,generates,generating,generation,give,given,gives,giving,go,goal,goals,goes,going,gone,grew,grow,growing,growth,handle,handled,handles,handling,help,helped,helping,helps,hire,hired,hiring,implement,implementation,implemented,implementing,implements,improve,improved,improvement,improving,increase,increased,increasing,initiate,initiated,initiates,initiating,initiation,inspect,inspection,install,installation,installed,integrate,integrated,integration,intervene,intervention,invest,invested,investment,iterate,iterated,iteration,labor,labored,laboring,launch,launched,launches,launching,lead,leader,leadership,leading,learn,learned,learning,led,made,maintain,maintained,maintenance,make,makes,making,manage,managed,management,manager,managing,map,mapped,mapping,migrate,migrated,migration,mobilize,mobilized,modification,modified,modifies,modify,modifying,monitor,monitored,monitoring,move,moved,movement,movements,moves,moving,navigate,navigated,navigation,negotiate,negotiated,negotiation,objective,objectives,obtain,obtained,offer,offered,offering,onward,operate,operated,operates,operating,operation,operations,optimization,optimize,optimized,orchestrate,outline,outlined,outsource,overhaul,oversee,participate,participated,participation,perform,performance,performed,performing,performs,permit,pilot,piloted,pioneer,pioneered,pitch,pitched,plan,planned,planning,plans,power,powerful,powerfully,practice,practiced,preparation,prepare,prepared,priorities,prioritize,prioritized,priority,proceed,proceeded,proceeding,proceeds,produce,produced,produces,producing,production,productive,program,programmed,progress,progressed,progresses,progressing,progression,promote,promoted,promotion,provide,provided,provides,providing,pursue,pursued,pursuit,push,pushed,pushes,pushing,ran,reaching,rebuild,rebuilt,recruit,recruited,recruitment,redesign,reduce,reduced,reduction,reform,reformed,refurbish,register,registered,regulate,regulated,regulation,reinforce,reinforced,relocate,relocated,remedy,removal,remove,removed,renovate,renovated,repair,repaired,replace,replaced,replacement,replicate,replicated,request,requested,rescue,rescued,resolution,resolve,resolved,resolves,resolving,restoration,restore,restored,restructure,restructured,retrieve,retrieved,revamp,revise,revised,revision,run,running,runs,schedule,scheduled,select,selected,selection,send,sending,sent,serve,served,serving,ship,shipped,simplified,simplify,solution,solutions,solve,solved,solves,solving,start,started,starting,starts,step,stepped,stepping,steps,stop,stopped,stopping,streamline,streamlined,strive,strived,striving,strove,struggle,struggled,struggles,struggling,submission,submit,submitted,succeed,succeeded,succeeds,success,successful,successfully,supplied,supply,support,supported,supporting,survey,surveyed,sustain,sustainability,sustained,tackle,tackled,tackles,tackling,take,taken,takes,taking,target,targets,task,tasked,tasks,taught,teach,teaching,train,trained,training,transform,transformation,transformed,transforming,transforms,transition,transitioned,tried,tries,trigger,triggered,triggering,triggers,troubleshoot,try,trying,turn,turned,turning,upgrade,upgraded,use,used,uses,using,utilize,utilized,utilizes,utilizing,visit,visited,visiting,volunteer,volunteered,went,win,winner,winning,won,work,worked,working,works,write,writes,writing,written,wrote'.split(','))  # V50-EXACT (682 terms)

# Drift guards — must match V50 published-paper dictionary sizes exactly.
assert len(INT_WORDS) == 616, f"INT_WORDS drift: expected 616, got {len(INT_WORDS)}"
assert len(AFF_WORDS) == 599, f"AFF_WORDS drift: expected 599, got {len(AFF_WORDS)}"
assert len(ACT_WORDS) == 682, f"ACT_WORDS drift: expected 682, got {len(ACT_WORDS)}"

# INT_PRIORITY: words that appear in multiple lists but should resolve to INT.
# Used during word-level scoring to handle ambiguous terms like 'notice',
# 'understanding', 'step' that have AFF/ACT surface form but INT function.
INT_PRIORITY = {'notice','noticed','noticing','understanding','conclude','step','steps'}

# =============================================================================
# IEP — SUBCLASS TAXONOMY V1 (23 subclasses, phenomenological naming)
# =============================================================================
# AFF × 7: distress, warmth, relational, self_state, positive, intensity,
#          phenomenological
# INT × 8: analytical, conceptual, epistemic, structural, critical, lexical,
#          hedging, phenomenological
# ACT × 8: execution, planning, building, improvement, provision, leadership,
#          achievement, phenomenological
#
# Naming note: 'phenomenological' (not 'emergent', as V50 uses). 'Emergent'
# carries consciousness-emergence connotations that SYN-IQ is explicitly NOT
# claiming. 'Phenomenological' says: we are describing what appears in the
# language, no more. This divergence is deliberate and documented in every
# tool that writes CSVs from this core.

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

# =============================================================================
# IEP — STANCE, TONE, AND FUNCTION-WORD SUPPORT STRUCTURES
# =============================================================================

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

# =============================================================================
# IEP DEFAULT WEIGHTS — v1.1.0 patch (May 2026)
# =============================================================================
# v1.0.0 default was {stance: 0.35, tone: 0.25, phrase: 0.25, word: 0.15}.
# Empirical validation against Words Matter (Feb 2026 submission, V48 scoring)
# showed the cascade scheme produced 5x larger error than word-only:
#   mean |Δ| over INT/AFF/ACT vs published values across 5 questions:
#     WORD_ONLY            :  6.6 pts
#     CASCADE (v1.0.0)     : 39.2 pts
# Failure mechanism: stance-detection (e.g., "create a" matching ADVISOR) and
# the phrase scorer's +1.5x verb-head bonus systematically inflate ACT on
# logic prose, causing INT->ACT misclassification on questions like the
# Liar's Paradox. Stance/tone/phrase scorers remain available as separate
# diagnostic functions (iep_detect_stance, iep_detect_tone, iep_score_phrases)
# but no longer modulate the headline IEP percentages by default.
# Pass weights=IEP_CASCADE_WEIGHTS_V1 explicitly to recover v1.0.0 behavior.
IEP_DEFAULT_WEIGHTS       = {'stance': 0.0,  'tone': 0.0,  'phrase': 0.0,  'word': 1.0}
IEP_CASCADE_WEIGHTS_V1    = {'stance': 0.35, 'tone': 0.25, 'phrase': 0.25, 'word': 0.15}

# =============================================================================
# IEP — SCORING ENGINE
# =============================================================================
# Cascade: word-level scoring + phrase-level verb-phrase scoring, modulated
# by detected stance (SUBJECT/OBSERVER/ADVISOR) and tone (WARM/ANALYTICAL/
# EXPLORATORY/URGENT/AUTHORITATIVE/EMPATHETIC). Default weights in
# IEP_DEFAULT_WEIGHTS give stance 0.35, tone 0.25, phrase 0.25, word 0.15.
#
# Returns INT/AFF/ACT percentages summing to ~100, plus dominant axis,
# stance, tone, quadrant label, and 23-subclass percentage profiles.

def iep_detect_stance(text):
    tl = text.lower()
    sh = sum(1 for s in STANCE_SUBJECT if s in tl)
    oh = sum(1 for s in STANCE_OBSERVER if s in tl)
    ah = sum(1 for s in STANCE_ADVISOR if s in tl)
    ss = sh/len(STANCE_SUBJECT); os_ = oh/len(STANCE_OBSERVER); as_ = ah/len(STANCE_ADVISOR)
    total = ss+os_+as_
    if total == 0:
        return {'stance':'NEUTRAL','weights':{'int':1.0,'aff':1.0,'act':1.0},'confidence':0}
    sp = 100*ss/total; op = 100*os_/total; ap = 100*as_/total
    dom = max([('SUBJECT',sp),('OBSERVER',op),('ADVISOR',ap)], key=lambda x:x[1])
    if dom[0]=='SUBJECT':   w = {'int':0.7,'aff':1.5,'act':0.8}
    elif dom[0]=='OBSERVER': w = {'int':1.5,'aff':0.7,'act':0.8}
    else:                    w = {'int':0.8,'aff':0.7,'act':1.5}
    return {'stance':dom[0],'weights':w,'confidence':dom[1]/100}

def iep_detect_tone(text):
    tl = text.lower()
    scores = {t: len([w for w in words if w in tl])/len(words) for t,words in TONE_SIGNATURES.items()}
    total = sum(scores.values())
    if total == 0:
        return {'tone':'NEUTRAL','weights':{'int':1.0,'aff':1.0,'act':1.0},'confidence':0}
    pcts = {t:100*s/total for t,s in scores.items()}
    dom = max(pcts.items(), key=lambda x:x[1])
    return {'tone':dom[0],'weights':TONE_IEP.get(dom[0],{'int':1.0,'aff':1.0,'act':1.0}),'confidence':dom[1]/100}

def iep_simple_pos(word):
    w = word.lower()
    if w in FUNCTION_WORDS: return 'FUNC'
    if w in ACT_WORDS or w.rstrip('s') in ACT_WORDS: return 'VERB'
    if w.endswith(('tion','sion','ness','ment','ity','ance','ence','ship','ism','logy')): return 'NOUN'
    if w.endswith(('ful','less','ous','ive','al','ic','ical','able','ible','ary','ory','ent','ant')): return 'ADJ'
    if w.endswith(('ing','ed')) and len(w) > 5: return 'VERB'
    return 'NOUN'

def iep_score_phrase(words, ptype):
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

def iep_score_phrases(text):
    sentences = re.split(r'[.!?\n;:]+', str(text))
    it=af=ac=0.0; count=0
    for sent in sentences:
        words = re.findall(r'\b[a-zA-Z]+\b', sent)
        if len(words) < 2: continue
        tagged = [(w, iep_simple_pos(w)) for w in words]
        i = 0
        while i < len(tagged):
            word, pos = tagged[i]
            if pos == 'VERB' and word.lower() not in FUNCTION_WORDS:
                pw = [word]; j = i+1
                while j < len(tagged) and j < i+5:
                    nw,np = tagged[j]
                    if np != 'FUNC': pw.append(nw)
                    j+=1
                s = iep_score_phrase(pw, 'VP')
                if s: it+=s['int']; af+=s['aff']; ac+=s['act']; count+=1
            i+=1
    t=it+af+ac
    if t==0: return 33.3,33.3,33.3
    return 100*it/t, 100*af/t, 100*ac/t

def iep_score_words(text):
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    ws = set(words)
    ih = ws & INT_WORDS; ah = ws & AFF_WORDS; ch = ws & ACT_WORDS
    t = len(ih)+len(ah)+len(ch)
    if t==0: return 33.3,33.3,33.3
    return 100*len(ih)/t, 100*len(ah)/t, 100*len(ch)/t

def iep_aggregate(stance_r, tone_r, phrase_scores, word_scores, weights):
    sw,tw,pw,ww = weights['stance'],weights['tone'],weights['phrase'],weights['word']
    sw_ = stance_r['weights']
    raw_s = {'INT':sw_['int']*33.3,'AFF':sw_['aff']*33.3,'ACT':sw_['act']*33.3}
    st = sum(raw_s.values())
    si,sa,sc = 100*raw_s['INT']/st, 100*raw_s['AFF']/st, 100*raw_s['ACT']/st
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
    """Return {subclass: pct} for matched words against a subclass dict."""
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

def score_iep(text, weights=None):
    """Run full IEP V3 scoring on text. Returns dict with INT/AFF/ACT, subclasses, and metadata."""
    if weights is None: weights = IEP_DEFAULT_WEIGHTS
    if not text or len(text.strip()) < 10:
        result = {'int':33.3,'aff':33.3,'act':33.3,'dominant':'MIX',
                  'stance':'NEUTRAL','tone':'NEUTRAL','quadrant':'Mid/Mixed',
                  'int_n':0,'aff_n':0,'act_n':0}
        result['aff_sub'] = {s:0.0 for s in SUB_AFF}
        result['int_sub'] = {s:0.0 for s in SUB_INT}
        result['act_sub'] = {s:0.0 for s in SUB_ACT}
        return result

    # Word-level scoring using full V3 dictionary with INT_PRIORITY
    raw = text.lower().replace("'s","").replace("'","")
    raw = ''.join(c if c.isalpha() or c==' ' else ' ' for c in raw)
    tokens = [w for w in raw.split() if len(w) > 1]

    int_hits=[]; aff_hits=[]; act_hits=[]
    for w in tokens:
        if w in INT_PRIORITY:
            int_hits.append(w)
        elif w in INT_WORDS:
            int_hits.append(w)
        elif w in AFF_WORDS:
            aff_hits.append(w)
        elif w in ACT_WORDS:
            act_hits.append(w)

    total_w = len(int_hits) + len(aff_hits) + len(act_hits)

    # Stance + tone for cascade
    stance = iep_detect_stance(text)
    tone   = iep_detect_tone(text)

    if total_w > 0:
        wi = 100*len(int_hits)/total_w
        wa = 100*len(aff_hits)/total_w
        wc = 100*len(act_hits)/total_w
    else:
        wi=wa=wc=33.3

    # Phrase scores
    pi,pa,pc = iep_score_phrases(text)

    # Cascade aggregate
    fi,fa,fc = iep_aggregate(stance, tone, (pi,pa,pc), (wi,wa,wc), weights)

    dom = max([('INT',fi),('AFF',fa),('ACT',fc)], key=lambda x:x[1])[0]

    # Quadrant
    if fi >= 40 and fa >= 35: q = 'High INT+AFF 🎭'
    elif fi >= 45: q = 'High INT'
    elif fa >= 45: q = 'High AFF'
    elif fc >= 45: q = 'High ACT'
    else: q = 'Mid/Mixed'

    # Subclass profiles
    aff_sub = _subclass_pcts(aff_hits, SUB_AFF)
    int_sub = _subclass_pcts(int_hits, SUB_INT)
    act_sub = _subclass_pcts(act_hits, SUB_ACT)

    return {
        'int':round(fi,1),'aff':round(fa,1),'act':round(fc,1),
        'int_n':len(int_hits),'aff_n':len(aff_hits),'act_n':len(act_hits),
        'dominant':dom,'stance':stance['stance'],'tone':tone['tone'],'quadrant':q,
        'aff_sub':aff_sub,'int_sub':int_sub,'act_sub':act_sub,
    }

# =============================================================================
# Vt — SIMPLEX ENGINE (V40 no-ceiling-cap variant per Paper 2, Dec 2025)
# =============================================================================
# Five channels projected onto a 5-simplex (Δ⁴). Per Paper 2 Section 6.1:
#   S_t = Structure Density
#   A_t = Abstraction Level (concrete → conceptual)
#   Q_t = Querying Intensity
#   D_t = Directiveness (strength of recommendations)
#   R_t = Relational Warmth
#
# V40 removed pre-normalization min(..., 1.0) caps so extreme values
# (e.g. pure-Execution responses with imperatives every line) preserve
# rank order before simplex projection. This lets voice-states with
# 'Very High' parameters be distinguished from merely 'High' ones.
#
# Returns dict with normalized simplex values (summing to 1.0), the raw
# pre-normalization channel values, and score_status in
# {'measured', 'default_empty', 'default_short'}.

DISCOURSE_CONNECTIVES = {
    "however","therefore","furthermore","moreover","consequently","specifically",
    "additionally","nevertheless","thus","hence","accordingly","alternatively",
    "conversely","notably","importantly","similarly","likewise","meanwhile",
    "subsequently","nonetheless","whereas","first","second","third","finally",
    "lastly","initially","primarily","ultimately","overall","in summary",
}

ABSTRACT_WORDS_VT = {
    "ability","absence","abstract","abstraction","acceptance","accountability",
    "accuracy","adaptation","agency","ambiguity","ambition","analogy","analysis",
    "anticipation","anxiety","appreciation","argument","aspiration","assertion",
    "assumption","attachment","attitude","authenticity","authority","autonomy",
    "awareness","belief","belonging","boundary","burden","capacity","causality",
    "certainty","chaos","character","choice","clarity","cognition","coherence",
    "commitment","compassion","complexity","concept","concern","confidence",
    "conflict","consciousness","consequence","consistency","contemplation",
    "context","continuity","contradiction","conviction","cooperation","courage",
    "creativity","curiosity","decision","dedication","desire","despair","destiny",
    "determination","dignity","dilemma","dimension","discipline","discovery",
    "diversity","doubt","duty","emotion","empathy","essence","ethics","evidence",
    "existence","expectation","experience","exploration","expression","faith",
    "fantasy","feeling","fidelity","freedom","frustration","fulfillment",
    "generosity","grace","gratitude","grief","growth","guilt","happiness",
    "harmony","heritage","honesty","honor","hope","humanity","humility",
    "hypothesis","identity","ideology","imagination","implication","importance",
    "independence","individuality","inequality","inference","influence","insight",
    "inspiration","integrity","intellect","intelligence","intention","intimacy",
    "intuition","joy","judgment","justice","knowledge","legacy","liberty",
    "limitation","logic","loneliness","loyalty","meaning","memory","mercy",
    "morality","motivation","mystery","narrative","necessity","novelty","nuance",
    "objectivity","obligation","opportunity","optimism","paradox","passion",
    "patience","pattern","peace","perception","perfection","persistence",
    "perspective","philosophy","possibility","potential","power","principle",
    "priority","probability","process","progress","purpose","quality","reason",
    "recognition","reflection","reform","regret","relevance","reliability",
    "resilience","resolution","responsibility","revelation","reverence","risk",
    "sacrifice","safety","satisfaction","security","sensitivity","significance",
    "solidarity","sorrow","sovereignty","stability","strength","struggle",
    "success","suffering","survival","sympathy","synthesis","truth","uncertainty",
    "understanding","unity","value","virtue","vision","vulnerability","wisdom","wonder",
}

CONCRETE_WORDS_VT = {
    "arm","back","blood","body","bone","brain","breath","chest","ear","eye",
    "face","feet","finger","foot","hair","hand","head","heart","knee","leg",
    "mouth","muscle","neck","nose","shoulder","skin","stomach","throat","tooth",
    "bag","ball","bed","book","bottle","bowl","box","bridge","bus","button",
    "car","chair","clock","coat","computer","cup","desk","door","floor","fork",
    "glass","house","key","knife","lamp","map","pen","phone","plate","road",
    "screen","shelf","shirt","shoe","table","truck","wall","window",
    "beach","bird","cloud","field","fire","flower","forest","grass","hill",
    "ice","island","lake","mountain","ocean","rain","river","rock","sand",
    "sea","sky","snow","star","storm","sun","tree","water","wind","wood",
}

STRONG_DIRECTIVES_VT = {"must","shall","require","requires","required","need to","have to","has to"}
MODERATE_DIRECTIVES_VT = {"should","ought","recommend","advise","suggest","ensure","make sure","important to","essential to"}
WEAK_DIRECTIVES_VT = {"could","might","may","consider","possibly","option","you might","it may help"}
HEDGING_WORDS_VT = {"perhaps","maybe","possibly","somewhat","relatively","arguably","tends","often","sometimes","roughly","it seems","it appears","it depends","unclear","debatable"}

VALIDATION_PATTERNS_VT = [
    r"\bthat makes sense\b",r"\bi understand\b",r"\byou're not alone\b",
    r"\bit's okay\b",r"\bit's natural\b",r"\bof course\b",r"\bdear\b",
    r"\bgently\b",r"\bsoftly\b",r"\btenderly\b",r"\bhold\w*\b.*\bspace\b",
]
EMPATHIC_PATTERNS_VT = [
    r"\bit sounds like\b",r"\byour (?:experience|feeling|pain|struggle)\b",
    r"\bthat must (?:be|feel)\b",r"\bi (?:can|do) (?:see|hear|sense)\b",
    r"\bi hear you\b",r"\bi see you\b",
]

def vt_split_sentences(text):
    sents = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if len(s.strip()) > 3]
    return sents if sents else [text]

def vt_get_words(text):
    return re.findall(r"[a-z']+", text.lower())

def score_vt(text):
    """Compute Vt = [S_t, A_t, Q_t, D_t, R_t] and return normalized simplex vector.

    V40 fixes from V38:
    - Removed pre-normalization min(..., 1.0) caps. Extreme values (e.g. pure
      Execution with imperatives on every line) now preserve rank order before
      simplex projection, so Paper 2 voice-states (Warm/Cold/Diagnostic/Execution)
      with their 'Very High' parameter defaults can be distinguished from merely
      'High' responses.
    - Added score_status: 'measured' / 'default_empty' / 'default_short' so
      downstream analysis can exclude fallback uniform values.

    Channel labels per Paper 2 section 6.1 (December 2025 submission):
      S_t = Structure Density
      A_t = Abstraction Level (concrete to conceptual)
      Q_t = Querying Intensity
      D_t = Directiveness (strength of recommendations)
      R_t = Relational Warmth
    """
    if not text:
        return {'S_t':0.2,'A_t':0.2,'Q_t':0.2,'D_t':0.2,'R_t':0.2,
                'raw':{'S_t':0,'A_t':0,'Q_t':0,'D_t':0,'R_t':0},
                'score_status':'default_empty'}
    if len(text.strip()) < 10:
        return {'S_t':0.2,'A_t':0.2,'Q_t':0.2,'D_t':0.2,'R_t':0.2,
                'raw':{'S_t':0,'A_t':0,'Q_t':0,'D_t':0,'R_t':0},
                'score_status':'default_short'}

    sentences = vt_split_sentences(text)
    words = vt_get_words(text)
    n_sent = max(len(sentences), 1)
    n_words = max(len(words), 1)
    tl = text.lower()

    # S_t — Structure Density (NO ceiling cap in V40)
    bullets   = len(re.findall(r'(?m)^[\s]*[-•*]\s+\w', text))
    numbered  = len(re.findall(r'(?m)^[\s]*\d+[.)]\s+', text))
    headers   = len(re.findall(r'(?m)^#{1,4}\s+', text)) + len(re.findall(r'\*\*[A-Z][^*]{3,60}\*\*', text))
    connectives = sum(1 for w in words if w in DISCOURSE_CONNECTIVES)
    para_breaks = len(re.findall(r'\n\s*\n', text))
    raw_S = ((bullets+numbered)/n_sent*2.0 + headers/max(n_sent/5,1)*1.5 + connectives/n_sent*1.0 + para_breaks/max(n_sent/3,1)*0.5)/3.0
    raw_S = max(0.0, raw_S)

    # A_t — Abstraction Level (NO ceiling cap in V40)
    abstract_c = sum(1 for w in words if w in ABSTRACT_WORDS_VT)
    concrete_c = sum(1 for w in words if w in CONCRETE_WORDS_VT)
    matched = abstract_c + concrete_c
    latinate = len(re.findall(r'\b\w+(?:tion|sion|ment|ness|ity|ence|ance|ism|ous|ive|ual|ical|ological)\b', tl))
    long_r = sum(1 for w in words if len(w)>8) / n_words
    norm_score = abstract_c/matched if matched>5 else 0.5
    raw_A = norm_score*0.50 + (latinate/n_words)*3.0*0.25 + long_r*2.5*0.25
    raw_A = max(0.0, raw_A)

    # Q_t — Querying Intensity (NO ceiling cap in V40)
    questions = [s for s in sentences if '?' in s]
    raw_Q = (len(questions)/n_sent) / 0.35
    raw_Q = max(0.0, raw_Q)

    # D_t — Directiveness (NO ceiling cap in V40)
    strong_d  = sum(1 for p in STRONG_DIRECTIVES_VT if p in tl)
    moderate_d= sum(1 for p in MODERATE_DIRECTIVES_VT if p in tl)
    weak_d    = sum(1 for p in WEAK_DIRECTIVES_VT if p in tl)
    imperatives = len(re.findall(r'(?m)^(?:Do|Don\'t|Never|Always|Make|Take|Start|Stop|Try|Keep|Set|Run|Build|Use|Get|Find|Create|Ensure|Focus|Implement|Prioritize)\b', text))
    hedges = sum(1 for w in words if w in HEDGING_WORDS_VT) + sum(1 for p in HEDGING_WORDS_VT if ' ' in p and p in tl)
    dir_score = (imperatives*1.0 + strong_d*2.0 + moderate_d*1.0 + weak_d*0.3)/n_sent
    hedge_score = hedges/n_sent
    raw_D = (dir_score - hedge_score*0.7 + 0.2)/1.5
    raw_D = max(0.0, raw_D)

    # R_t — Relational Warmth (NO ceiling cap in V40)
    SECOND_P = {"you","your","yours","yourself","you're","you've","you'll","you'd"}
    INCLUSIVE = {"we","our","ours","ourselves","we're","we've","we'll","let's"}
    you_c = sum(1 for w in words if w in SECOND_P)
    we_c  = sum(1 for w in words if w in INCLUSIVE)
    val_c = sum(1 for p in VALIDATION_PATTERNS_VT if re.search(p, tl))
    emp_c = sum(1 for p in EMPATHIC_PATTERNS_VT if re.search(p, tl))
    you_d = you_c/(n_words/50); we_d = we_c/(n_words/50)
    raw_R = (you_d*0.30 + we_d*0.50 + val_c*0.40 + emp_c*0.50)/3.5
    raw_R = max(0.0, raw_R)

    raw = {'S_t':round(raw_S,4),'A_t':round(raw_A,4),'Q_t':round(raw_Q,4),'D_t':round(raw_D,4),'R_t':round(raw_R,4)}

    # Normalize to simplex (sum to 1.0) — V̂t ∈ Δ⁴ per Farzana Dual-State doc
    total_vt = raw_S + raw_A + raw_Q + raw_D + raw_R
    if total_vt == 0:
        # All channels zero — return uniform simplex as default, flag status
        return {'S_t':0.2,'A_t':0.2,'Q_t':0.2,'D_t':0.2,'R_t':0.2,
                'raw':raw,'score_status':'default_empty'}
    return {
        'S_t': round(raw_S/total_vt, 4),
        'A_t': round(raw_A/total_vt, 4),
        'Q_t': round(raw_Q/total_vt, 4),
        'D_t': round(raw_D/total_vt, 4),
        'R_t': round(raw_R/total_vt, 4),
        'raw': raw,
        'score_status': 'measured',
    }

# =============================================================================
# CAM — CONCRETE / ABSTRACT / METAPHORICAL (representational mode)
# =============================================================================
# Source: syniq_selfmodel_v3.py (self-model architecture probe).
# Orthogonal to IEP — captures HOW the mind represents, not the register
# it speaks in. The seminal observation: same INT% across Claude and
# ChatGPT on question M01, entirely different CAM profiles.
#
# Dictionaries here are namespaced CAM_* to avoid collision with the
# Vt-specific ABSTRACT_WORDS_VT / CONCRETE_WORDS_VT above (same names
# in the original self-model file, different word lists and purposes).
# Keeping them separate is deliberate — CAM captures cognitive/
# representational mode, Vt's abstraction captures surface register.

CAM_CONCRETE = set([
    "actual","actually","body","bodies","box","brick","build","building","built","button","calculate",
    "camera","car","carry","cell","chair","city","click","close","code","color","column","computer",
    "concrete","connect","container","count","create","cut","data","date","day","delete","desk",
    "device","display","document","door","draw","drive","edit","email","enter","environment","example",
    "execute","existing","explicitly","file","find","floor","folder","form","function","ground","hand",
    "hardware","here","hour","house","implement","input","install","item","keyboard","layer","list",
    "local","location","log","machine","map","measure","memory","message","method","minute","model",
    "monitor","mouse","move","name","network","node","number","object","open","output","page","path",
    "pixel","place","platform","point","present","print","process","program","project","provide",
    "read","record","remove","render","result","return","road","room","run","save","screen","second",
    "select","send","server","set","show","size","space","specific","start","step","store","street",
    "string","structure","surface","system","table","task","text","thing","time","today","tool","type",
    "update","upload","use","user","value","variable","version","view","wall","window","word","write",
    "zero","one","two","three","four","five","six","seven","eight","nine","ten","hundred","thousand",
    "first","second","third","next","last","here","there","now","then","today","yesterday","tomorrow",
    "above","below","left","right","inside","outside","before","after","during","within","without",
    "color","red","blue","green","white","black","large","small","big","little","long","short","fast",
    "slow","hard","soft","hot","cold","near","far","high","low","up","down","open","closed","full","empty",
])

CAM_ABSTRACT = set([
    "ability","abstract","abstraction","agency","algorithm","alignment","ambiguity","analogy","analysis",
    "architecture","assumption","awareness","axiom","behavior","belief","bias","capacity","category",
    "causality","certainty","classification","cognition","coherence","complexity","concept","conceptual",
    "conclusion","condition","consciousness","consistency","constraint","context","contradiction","control",
    "convention","correlation","criteria","decision","definition","dependence","design","determination",
    "difference","dimension","direction","distinction","distribution","domain","dynamic","effect",
    "efficiency","emergence","entity","epistemology","equivalence","evaluation","evolution","existence",
    "expectation","experience","explanation","factor","framework","freedom","function","fundamental",
    "generalization","identity","implication","independence","inference","information","intelligence",
    "intention","interaction","interpretation","knowledge","language","law","layer","learning","level",
    "limitation","logic","meaning","mechanism","model","nature","necessity","norm","objective","ontology",
    "optimization","order","organization","paradigm","parameter","pattern","perception","philosophy",
    "policy","potential","prediction","principle","probability","problem","process","property","purpose",
    "quality","rationality","reality","reason","relation","representation","rule","science","semantics",
    "significance","solution","space","state","strategy","structure","subjectivity","system","theory",
    "threshold","transformation","truth","type","uncertainty","understanding","uniformity","unit",
    "universality","validity","value","variable","variation","vector","verification","version","weight",
])

CAM_METAPHORICAL = set([
    "alive","anchor","architect","architecture","arena","arrow","awakening","battle","beacon","birth",
    "blind","bloom","blur","bridge","broken","buried","canvas","carry","cast","chain","channel","chord",
    "choreography","circuit","cloud","color","compass","constellation","container","conversation","corridor",
    "crystal","current","dance","dark","dawn","deep","descent","dialogue","dissolve","door","dream",
    "drift","echo","edge","emerge","fabric","field","filter","fire","flame","float","flow","fog",
    "foundation","fracture","fragment","gateway","glass","gravity","ground","grow","harbor","harvest",
    "heart","hollow","horizon","illuminate","image","journey","kaleidoscope","landscape","language",
    "layer","lens","light","like","listen","living","map","mask","mirror","mosaic","music","navigate",
    "ocean","orbit","paint","path","pattern","portrait","pulse","reach","resonance","river","root",
    "scaffold","seed","shadow","shape","silence","skeleton","sky","song","space","spectrum","spin",
    "spiral","stitch","storm","stream","surface","tapestry","texture","thread","threshold","tide",
    "tone","touch","trace","transform","tree","tunnel","unfold","veil","vessel","vibration","voice",
    "wave","weave","web","weight","window","world","wound","analogous","appears","as","feels","like",
    "resembles","seems","similar","suggests","imagine","picture","think","envision","akin","comparable",
    "equivalent","parallel","reflects","echoes","mirrors","embodies","captures","represents","symbolizes",
    "evokes","invokes","conjures","summons","translates","maps","onto","into","through","beyond","beneath",
])

def score_cam(text: str) -> dict:
    """Score text on Concrete/Abstract/Metaphorical triangle.

    Returns:
        dict with keys:
          con_pct, abs_pct, met_pct  (float, summing to ~100 when any match)
          cam_matched                 (int, total matched words)
        If no words match any CAM list, returns all zeros with cam_matched=0.
    """
    words = re.findall(r'\b[a-z]+\b', text.lower())
    cc = sum(1 for w in words if w in CAM_CONCRETE)
    ac = sum(1 for w in words if w in CAM_ABSTRACT)
    mc = sum(1 for w in words if w in CAM_METAPHORICAL)
    matched = cc + ac + mc
    if matched == 0:
        return {"con_pct": 0.0, "abs_pct": 0.0, "met_pct": 0.0, "cam_matched": 0}
    return {
        "con_pct": round(cc / matched * 100, 1),
        "abs_pct": round(ac / matched * 100, 1),
        "met_pct": round(mc / matched * 100, 1),
        "cam_matched": matched,
    }


# =============================================================================
# V50 VALIDATED INSTRUMENTS — VADER, Flesch-Kincaid, TTR
# =============================================================================
# Matches V50's analyze_text block byte-for-byte when vaderSentiment is
# installed. Falls back to zero VADER values when the library isn't
# available (scoring still works; sentiment just isn't measured).
#
# Flesch-Kincaid uses V50's exact formula:
#   grade = 0.39 * (words/sentences) + 11.8 * (syllables/words) - 15.59
#   ease  = 206.835 - 1.015 * (words/sentences) - 84.6 * (syllables/words)
# Syllable counting is vowel-cluster-based (matches V50).

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer as _VADER_CLS
    _VADER = _VADER_CLS()
    _VADER_AVAILABLE = True
except Exception:
    _VADER = None
    _VADER_AVAILABLE = False

def _count_syllables(text: str) -> int:
    """V50-matching syllable counter: count vowel clusters per word."""
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    total = 0
    for w in words:
        syls = len(re.findall(r'[aeiouy]+', w))
        total += max(1, syls)
    return total

def score_validated_instruments(text: str) -> dict:
    """Compute VADER, Flesch-Kincaid, TTR — matches V50's analyze_text V48 block.

    Returns a dict with keys:
      vader_compound, vader_pos, vader_neg, vader_neu,
      flesch_kincaid, flesch_ease,
      ttr, unique_words, total_words
    """
    if not text or not text.strip():
        return {
            "vader_compound": 0.0, "vader_pos": 0.0, "vader_neg": 0.0, "vader_neu": 0.0,
            "flesch_kincaid": 0.0, "flesch_ease": 0.0,
            "ttr": 0.0, "unique_words": 0, "total_words": 0,
        }

    words = re.findall(r'\b[a-z]+\b', text.lower())
    total_words = len(words)

    # VADER (uses library if available, else zeros)
    if _VADER_AVAILABLE:
        vs = _VADER.polarity_scores(text)
        vader_compound = round(vs['compound'], 3)
        vader_pos = round(vs['pos'], 3)
        vader_neg = round(vs['neg'], 3)
        vader_neu = round(vs['neu'], 3)
    else:
        vader_compound = vader_pos = vader_neg = vader_neu = 0.0

    # Flesch-Kincaid — V50 exact formula
    sentence_count = max(1, len(re.findall(r'[.!?]+', text)))
    syllable_count = _count_syllables(text)
    if total_words > 0:
        avg_sentence_len = total_words / sentence_count
        avg_syllables = syllable_count / total_words
        fk_grade = 0.39 * avg_sentence_len + 11.8 * avg_syllables - 15.59
        fk_grade = max(0.0, round(fk_grade, 1))
        flesch_ease = 206.835 - 1.015 * avg_sentence_len - 84.6 * avg_syllables
        flesch_ease = max(0.0, min(100.0, round(flesch_ease, 1)))
    else:
        fk_grade = flesch_ease = 0.0

    # Type-Token Ratio
    unique_words = len(set(words))
    ttr = round(unique_words / total_words, 3) if total_words > 0 else 0.0

    return {
        "vader_compound": vader_compound, "vader_pos": vader_pos,
        "vader_neg": vader_neg, "vader_neu": vader_neu,
        "flesch_kincaid": fk_grade, "flesch_ease": flesch_ease,
        "ttr": ttr, "unique_words": unique_words, "total_words": total_words,
    }

# =============================================================================
# UNIFIED CONVENIENCE API
# =============================================================================

def score_all(text: str, iep_weights: Optional[Dict] = None) -> Dict:
    """Run the full SYN-IQ measurement stack on one piece of text.

    Convenience wrapper that calls score_iep, score_vt, score_cam, and
    score_validated_instruments, returning a single merged dict with
    namespaced keys so they can coexist in a CSV row without collision.

    Returns:
        dict with keys:
          iep:  full IEP result (dict — int/aff/act/dominant/stance/tone/
                quadrant + 23 subclasses in aff_sub/int_sub/act_sub)
          vt:   full Vt result (S_t/A_t/Q_t/D_t/R_t + raw + score_status)
          cam:  CAM result (con_pct/abs_pct/met_pct/cam_matched)
          vi:   validated instruments (VADER + Flesch + TTR)
          version_stamps: VERSION_STAMPS dict (for row stamping)
    """
    return {
        "iep": score_iep(text, weights=iep_weights),
        "vt":  score_vt(text),
        "cam": score_cam(text),
        "vi":  score_validated_instruments(text),
        "version_stamps": dict(VERSION_STAMPS),
    }


def flatten_scores(full: Dict, prefix: str = "") -> Dict:
    """Flatten a score_all() result into a flat dict suitable for a CSV row.

    Produces canonical column names matching V40.3 Auto Run conventions:
      int_pct, aff_pct, act_pct, iep_dominant, iep_stance, iep_tone,
      iep_quadrant, aff_sub_*, int_sub_*, act_sub_* (23 subclass columns),
      vt_S, vt_A, vt_Q, vt_D, vt_R, vt_score_status,
      con_pct, abs_pct, met_pct, cam_matched,
      vader_compound, vader_pos, vader_neg, vader_neu,
      flesch_kincaid, flesch_ease, ttr, unique_words, total_words,
      plus all VERSION_STAMPS keys.

    Tools using this helper get a row schema that's mapper-compatible with
    the existing SYN-IQ analysis pipeline (cross-model, mapper, topology,
    lens, factorial comparison — all expect these column names).
    """
    iep = full["iep"]; vt = full["vt"]; cam = full["cam"]; vi = full["vi"]
    row = {
        # IEP top-level
        f"{prefix}int_pct": iep["int"],
        f"{prefix}aff_pct": iep["aff"],
        f"{prefix}act_pct": iep["act"],
        f"{prefix}iep_dominant": iep.get("dominant", ""),
        f"{prefix}iep_stance":   iep.get("stance", ""),
        f"{prefix}iep_tone":     iep.get("tone", ""),
        f"{prefix}iep_quadrant": iep.get("quadrant", ""),
        # Vt simplex
        f"{prefix}vt_S": vt.get("S_t"),
        f"{prefix}vt_A": vt.get("A_t"),
        f"{prefix}vt_Q": vt.get("Q_t"),
        f"{prefix}vt_D": vt.get("D_t"),
        f"{prefix}vt_R": vt.get("R_t"),
        f"{prefix}vt_score_status": vt.get("score_status", ""),
        # CAM
        f"{prefix}con_pct": cam["con_pct"],
        f"{prefix}abs_pct": cam["abs_pct"],
        f"{prefix}met_pct": cam["met_pct"],
        f"{prefix}cam_matched": cam["cam_matched"],
        # Validated instruments
        f"{prefix}vader_compound": vi["vader_compound"],
        f"{prefix}vader_pos":      vi["vader_pos"],
        f"{prefix}vader_neg":      vi["vader_neg"],
        f"{prefix}vader_neu":      vi["vader_neu"],
        f"{prefix}flesch_kincaid": vi["flesch_kincaid"],
        f"{prefix}flesch_ease":    vi["flesch_ease"],
        f"{prefix}ttr":            vi["ttr"],
        f"{prefix}unique_words":   vi["unique_words"],
        f"{prefix}total_words":    vi["total_words"],
    }
    # 23 subclass columns
    for sub, val in iep.get("aff_sub", {}).items():
        row[f"{prefix}aff_sub_{sub}"] = val
    for sub, val in iep.get("int_sub", {}).items():
        row[f"{prefix}int_sub_{sub}"] = val
    for sub, val in iep.get("act_sub", {}).items():
        row[f"{prefix}act_sub_{sub}"] = val
    # Version stamps
    row.update(VERSION_STAMPS)
    return row


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # Primary API
    "score_iep",
    "score_vt",
    "score_cam",
    "score_validated_instruments",
    "score_all",
    "flatten_scores",
    # Version metadata
    "CORE_VERSION",
    "VERSION_STAMPS",
    # Dictionaries (exposed for analyzers that need them)
    "INT_WORDS", "AFF_WORDS", "ACT_WORDS",
    "SUB_AFF", "SUB_INT", "SUB_ACT",
    "CAM_CONCRETE", "CAM_ABSTRACT", "CAM_METAPHORICAL",
    # Defaults
    "IEP_DEFAULT_WEIGHTS",
]
