"""
iep_phrase_analyzer.py — IEP Phrase-Level Analysis (v1.1)
==========================================================

Companion to iep_visualizer.py. Detects phrase-level patterns that
word-only IEP scoring misses or misclassifies.

Design principle (per ChatGPT review, May 2026):
  Show WHY a detection happened, not just WHAT was detected.

Each phrase carries multiple tag types — never forced into a single
category prematurely:
  - iep_tags:      [INT.subclass, AFF.subclass, ACT.subclass]
  - cam_tags:      [concrete | abstract | metaphorical]
  - function_tags: [epistemic-hedge, metaphor, self-state-marker,
                    recursive-reflection-marker, relational-cue,
                    uncertainty-marker, sensory-frame, attempt-aspect,
                    polysemous-verb-disambiguation]
  - specificity:   [high | medium | low]

A phrase can be all three layers at once. The renderer shows every tag.

Three rule layers (each toggleable):
  1. VERB-OBJECT DISAMBIGUATION — compositional. "creates a contradiction"
     reclassifies because the object is INT.
  2. LIGHT-VERB / IDIOMATIC FRAMES — curated patterns. "find myself,"
     "reach for," "make sense."
  3. EPISTEMIC / SENSORY / MULTI-WORD HEDGES — curated patterns including
     multi-word negation hedges (e.g., "can't quite locate").

The tool is DIAGNOSTIC. It does NOT modify IEP scoring. Word-only IEP
scoring (v1.1.0 patched core) remains the canonical headline score.
The phrase analyzer reveals what additional structure is present in
the text — words provide sensitivity, phrases provide specificity.

Run:
  streamlit run iep_phrase_analyzer.py

Default password: tennessee
"""

import os
import re
import json

import pandas as pd
import streamlit as st


# =============================================================================
# IEP DICTIONARIES (V50-EXACT, embedded)
# =============================================================================

INT_WORDS = set('ability,absolute,absolutely,abstract,abstraction,accuracy,accurate,algorithm,algorithmic,allows,although,always,ambiguity,ambiguous,analogous,analogously,analogy,analysis,analytical,analyze,annotate,annotated,answer,appear,appeared,appears,appraisal,appraise,appraised,approach,approaches,approximate,architecture,argue,argued,argues,arguing,argument,arguments,assert,asserted,assertion,assertions,assess,assessment,assume,assumed,assumes,assuming,assumption,assumptions,axiom,axiomatic,basis,because,bias,biased,boundaries,boundary,but,calculate,calculation,categorical,categorically,categories,categorize,category,causal,causally,causation,cause,caused,causes,certain,certainly,certitude,challenge,challenges,circumscribe,claim,claimed,claims,clarify,clarity,classical,classification,classify,clear,cogent,cogently,cognition,cognitive,coherence,coherent,coherently,communication,compare,comparison,complex,complexity,comprehend,comprehension,computation,computational,compute,conceivable,conceive,conceived,concept,concepts,conceptual,conceptualize,conceptually,conclude,conclusion,conclusions,confirm,confirmation,conjecture,conjectured,conscious,consequence,consequences,consider,consideration,consistency,consistent,consistently,construe,construed,context,contradict,contradiction,contradictory,contrast,correlate,correlated,correlation,could,counterargument,counterexample,counterpoint,criteria,criterion,data,debatable,debate,debated,deconstruct,deconstructed,deconstruction,deduce,deduction,define,defined,definite,definitely,definition,definitive,definitively,delineate,delineated,demarcate,demarcated,demonstrate,demonstration,derivation,derive,derived,derives,describe,described,describing,description,determination,determine,diagnose,diagnosed,diagnosis,diagnostic,differ,difference,differences,different,differentiate,differs,discern,discerned,discernible,disprove,disproven,dissect,dissected,distinguish,effect,effects,elaborate,elaborated,elaboration,elucidate,elucidated,empirical,empirically,enumerate,enumerated,epistemic,epistemological,equate,equation,equivalence,equivalent,erroneous,error,errors,essential,essentially,estimate,estimated,estimation,evaluate,evaluation,evidence,evidently,exact,exactly,examination,examine,except,exemplified,exemplify,exists,experiment,experimental,explain,explained,explaining,explains,explanation,explanations,explicit,explicitly,exploration,explore,explored,exploring,express,expressing,expression,extrapolate,extrapolated,extrapolation,fact,facts,factual,factually,fallacious,fallacy,falsifiable,falsified,falsify,find,finding,formal,formalize,formula,formulate,formulated,formulation,found,framework,frameworks,function,fundamental,fundamentally,generalization,generalize,grasp,grasped,guess,hence,heuristic,heuristics,hierarchy,however,hypothesis,hypothesize,idea,ideas,identity,if,illuminate,illuminated,illuminating,implausible,implication,implications,implied,implies,imply,implying,incompleteness,inconsistency,inconsistent,indicate,indicated,indicates,indicating,indication,indicative,individual,infer,inference,infinite,information,insight,insightful,insights,instead,insufficient,intellectual,intellectually,interaction,internal,interpolate,interpret,interpretation,interpretations,interpreted,interpreting,invalid,investigate,investigated,investigation,judge,judgement,judgment,justification,justified,justify,know,knowing,knowledge,knowledgeable,known,language,languages,leads,level,likelihood,likely,limitations,limits,linguistic,literal,literally,logic,logical,logically,maybe,meaning,meaningful,meaningfully,measure,measurement,mechanism,mechanisms,meta,method,methodical,methodically,methodology,metrics,model,models,moreover,namely,natural,nature,nearly,necessarily,necessary,necessity,never,nonetheless,notice,noticed,noticing,notion,notions,objection,objectively,objectivity,observation,observations,observe,observed,obvious,obviously,order,ordered,organization,organize,otherwise,ought,paradigm,paradox,paradoxical,paradoxically,pattern,patterns,perhaps,perspective,philosophical,philosophically,philosophy,physical,plausibility,plausible,possibly,postulate,postulated,postulation,potential,pragmatic,pragmatically,precise,precision,predicate,predicated,predict,predictable,predicted,prediction,predictions,premise,premises,presumably,presume,presumed,presumption,principle,principles,probably,problem,procedural,procedure,process,processes,processing,proof,propose,proposed,proposition,prove,proven,purpose,quantify,quantitative,queried,query,question,questions,rather,rational,rationale,rationality,rationally,realize,realized,reason,reasoned,reasoning,reasons,rebut,rebuttal,recognition,recognize,reconsider,reconsidered,refer,reference,refers,refine,refined,refinement,reflecting,reflection,refutation,refute,refuted,requirement,requires,response,responses,result,resulting,results,rigor,rigorous,rigorously,role,rule,rules,schema,scrutinize,scrutinized,scrutiny,seem,seemed,seems,semantic,semantically,sequence,sequential,should,significance,significant,significantly,simple,simply,simultaneously,singular,specific,specifically,specification,specify,standard,standards,state,states,step,steps,stipulate,stipulated,strategies,strategy,structural,structure,subject,subjective,subjectively,subjectivity,substantiate,substantiated,sufficient,sufficiently,suggests,summarize,summarized,summary,suppose,supposed,supposedly,supposition,sure,surely,syllogism,syllogistic,synthesis,synthesize,synthesized,system,systematic,systematically,systems,tactic,tactics,taxonomy,technique,test,tested,testing,theorem,theoretical,theoretically,theorize,theory,thereby,therefore,thesis,think,thinking,thought,thoughts,thus,trivial,trivially,unambiguous,underlying,understand,understanding,understood,unique,universal,unless,unlikely,valid,validate,validation,validity,value,values,variable,variables,verification,verify,versus,warrant,warranted,whereas,whereby,whether,why,word,words,would'.split(','))

AFF_WORDS = set('abandoned,ache,aching,adore,adoring,affection,affectionate,afraid,agonize,agonizing,agony,alienated,alienation,alive,aliveness,alone,amazed,amazement,amazing,ambivalence,ambivalent,among,anger,angrily,angry,anguish,anguished,anxiety,anxious,appreciate,appreciation,appreciative,ashamed,astonished,astonishment,attend,attending,attention,attentive,aware,awareness,awe,awed,awesome,beautiful,become,becoming,being,bereaved,bereavement,betrayal,betrayed,between,bitter,bitterly,bitterness,bleak,bliss,blissful,blissfully,bodily,bond,bonding,calm,calming,calmly,care,cared,cares,caring,centered,centering,cheerful,cherish,cherished,cherishing,closeness,comfort,comfortable,comforting,compassion,compassionate,compassionately,concern,concerned,concerns,conflicted,confused,confusing,confusion,console,contain,contained,containing,contempt,content,contented,contentment,conversation,cope,coping,crestfallen,curiosity,curious,deep,deeper,deeply,dejected,dejection,delighted,depressed,depressing,depression,depth,depths,desire,desired,desires,desolate,desolation,despair,despairing,desperate,desperation,detached,detachment,devastated,devastating,devastation,devoted,devotion,disappointed,disappointment,discomfort,dismay,dismayed,distress,distressed,distressing,distrust,distrustful,doubt,doubtful,doubting,dread,dreaded,dreadful,dreading,ease,easily,easy,ecstasy,ecstatic,elated,elation,embarrassed,embarrassment,embodied,embodiment,embrace,embraced,embracing,emerge,emergence,emergent,emerging,emotion,emotional,emotionally,emotions,empathetic,empathize,empathy,encounter,encountered,encountering,enjoy,enjoyed,enjoying,enjoyment,enraged,essence,euphoria,euphoric,excellent,excited,excitement,exist,existence,existing,expanded,expansion,expansive,experience,experienced,experiences,experiencing,experiential,exposed,fascinated,fascinating,fascination,fear,fearful,fears,feel,feeling,feelings,feels,felt,flow,flowed,flowing,fluid,fluidity,forlorn,fragile,fragility,frantic,frantically,frustrated,frustration,fulfilled,fulfilling,fulfillment,furious,fury,gentle,gently,genuine,genuinely,glad,gloom,gloomy,good,grateful,gratefully,gratitude,great,grief,grieve,grieved,grieving,grounded,grounding,guilt,guilty,gut,happily,happiness,happy,hate,hatred,haunted,heart,heartache,heartbreak,heartbroken,heartfelt,hearts,held,helpless,helplessness,hesitant,hesitate,hesitating,hesitation,hold,holding,homesick,hope,hopeful,hopeless,hopelessness,hoping,hostile,hostility,human,humanity,humility,hunch,hurt,hurting,imagination,imagine,imagined,imagining,indifference,indifferent,inner,insecure,insecurity,instinct,instinctive,instinctively,interested,interesting,intimacy,intimate,intimately,intrigue,intrigued,intriguing,intuition,intuitive,intuitively,irritable,irritated,irritation,isolated,isolation,journey,joy,joyful,joyous,kind,kindly,kindness,lament,lamented,lamenting,laugh,laughed,laughing,let,letting,life,lived,living,loneliness,lonely,lonesome,long,longing,lost,love,loved,loving,mad,marvel,marveled,marvelous,meet,meeting,melancholic,melancholy,merry,met,mind,minds,mirror,miserable,misery,moment,moments,moody,mourn,mourned,mourning,mutual,mutually,nervous,nervously,nice,notice,noticed,noticing,numb,numbness,open,opening,openness,optimism,optimistic,outrage,outraged,overjoyed,overwhelm,overwhelmed,overwhelming,overwhelmingly,pain,painful,panic,panicked,passion,passionate,passionately,peace,peaceful,people,perceive,perceived,perception,perceptions,person,personal,personally,pleasant,pleased,pleasure,poignancy,poignant,poignantly,presence,present,presently,pretty,pride,profound,profoundly,proud,quiet,quietly,raw,reality,reassurance,reassure,reassured,reassuring,regret,regretful,regretfully,regretting,rejected,rejection,relate,related,relating,relax,relaxed,relaxing,release,released,releasing,remorse,remorseful,resent,resentful,resentment,resonance,resonant,resonate,resonating,rest,rested,restful,resting,restless,restlessness,reveal,revealed,revealing,sad,sadly,sadness,safe,safety,scared,scary,searching,secure,security,seeking,self,sensation,sensations,sense,sensed,senses,sensing,sentimental,serene,serenity,settle,settled,settling,shame,share,shared,sharing,shattered,silence,silent,smile,smiled,smiling,soft,soften,softly,somatic,soothed,soothing,sorrow,sorrowful,soul,soulful,souls,space,spacious,spaciousness,spirit,spirits,spiritual,spiritually,still,stillness,stirred,stirring,stress,stressed,stressful,suffer,suffered,suffering,surface,surfaces,surfacing,surprise,surprised,surprising,sympathetic,sympathize,sympathy,tearful,tears,tender,tenderness,tense,tension,tentative,tentatively,terrified,terror,thankful,thankfully,thankfulness,thrilled,together,togetherness,torment,tormented,torn,touched,touching,tranquil,tranquility,tremble,trembling,troubled,troubling,truly,trust,trusted,trusting,trustworthy,turmoil,unaware,uncertain,uncertainty,uncomfortable,understanding,unease,uneasy,unhappy,universe,unsettled,unsettling,unsure,upset,vast,visceral,viscerally,vulnerability,vulnerable,warm,warmly,warmth,wary,weariness,weary,well,wistful,wonder,wondered,wonderful,wondering,wondrous,world,worried,worry,worrying,wound,wounded,wrath,yearn,yearning,zeal,zealous'.split(','))

ACT_WORDS = set('access,accessed,accessing,accomplish,accomplished,accomplishes,accomplishing,accomplishment,achieve,achieved,achievement,achievements,achieves,achieving,act,acting,action,actions,activate,activated,activates,activating,activation,acts,adapt,adaptation,adapted,adapting,adapts,address,addressed,addresses,addressing,adjust,adjusted,adjusting,adjustment,adjusts,advance,advanced,advancement,advances,advancing,ahead,aim,aimed,aiming,aims,allocate,allocated,allocation,application,applied,applies,apply,applying,arrange,arranged,arrangement,arrangements,ask,asked,asking,assemble,assembled,assign,assigned,assignment,attempt,attempted,attempting,attempts,authorize,authorized,began,begin,beginning,begins,begun,best,better,bolster,bolstered,break,breaking,bring,bringing,broken,brought,budget,build,building,builds,built,calibrate,calibrated,call,called,calling,campaign,canvass,canvassed,carried,carry,carrying,catalogue,catalogued,centralize,centralized,change,changed,changes,changing,channel,channeled,chart,check,checked,checking,choice,choices,choose,choosing,chose,chosen,circumvent,coach,collaborate,collaborated,collaboration,commission,commit,commitment,committed,compile,compiled,complete,completed,completes,completing,completion,conclude,concluded,concludes,concluding,configure,configured,connect,connected,connecting,connection,connections,consolidate,construct,constructed,constructing,constructs,continuation,continue,continued,continues,continuing,control,controlled,controlling,controls,conversion,convert,converted,converting,converts,coordinate,coordinated,coordination,craft,crafted,crafting,create,created,creates,creating,creation,customize,deadline,decide,decided,deciding,decision,decisions,delegate,delegated,delegation,deliver,delivered,delivering,delivers,delivery,deploy,deployed,deploying,deployment,deploys,design,designed,designing,designs,develop,developed,developing,development,develops,did,direct,directed,directing,dive,diving,do,does,doing,done,draft,drafting,edit,editing,effort,efforts,eliminate,eliminated,elimination,employ,employed,employing,employs,enable,enabled,end,ended,ending,ends,enforce,enforced,enforcement,engage,engaged,engagement,engineer,engineering,enroll,enrolled,enrollment,equip,equipped,establish,established,establishes,establishing,establishment,execute,executed,executes,executing,execution,expedite,facilitate,facilitated,facilitation,finalize,finalized,finish,finished,finishes,finishing,fix,fixed,fixes,fixing,focus,focused,focusing,form,formation,formed,forming,forms,forward,fund,funded,funding,gather,gathered,gathering,generate,generated,generates,generating,generation,give,given,gives,giving,go,goal,goals,goes,going,gone,grew,grow,growing,growth,handle,handled,handles,handling,help,helped,helping,helps,hire,hired,hiring,implement,implementation,implemented,implementing,implements,improve,improved,improvement,improving,increase,increased,increasing,initiate,initiated,initiates,initiating,initiation,inspect,inspection,install,installation,installed,integrate,integrated,integration,intervene,intervention,invest,invested,investment,iterate,iterated,iteration,labor,labored,laboring,launch,launched,launches,launching,lead,leader,leadership,leading,learn,learned,learning,led,made,maintain,maintained,maintenance,make,makes,making,manage,managed,management,manager,managing,map,mapped,mapping,migrate,migrated,migration,mobilize,mobilized,modification,modified,modifies,modify,modifying,monitor,monitored,monitoring,move,moved,movement,movements,moves,moving,navigate,navigated,navigation,negotiate,negotiated,negotiation,objective,objectives,obtain,obtained,offer,offered,offering,onward,operate,operated,operates,operating,operation,operations,optimization,optimize,optimized,orchestrate,outline,outlined,outsource,overhaul,oversee,participate,participated,participation,perform,performance,performed,performing,performs,permit,pilot,piloted,pioneer,pioneered,pitch,pitched,plan,planned,planning,plans,power,powerful,powerfully,practice,practiced,preparation,prepare,prepared,priorities,prioritize,prioritized,priority,proceed,proceeded,proceeding,proceeds,produce,produced,produces,producing,production,productive,program,programmed,progress,progressed,progresses,progressing,progression,promote,promoted,promotion,provide,provided,provides,providing,pursue,pursued,pursuit,push,pushed,pushes,pushing,ran,reaching,rebuild,rebuilt,recruit,recruited,recruitment,redesign,reduce,reduced,reduction,reform,reformed,refurbish,register,registered,regulate,regulated,regulation,reinforce,reinforced,relocate,relocated,remedy,removal,remove,removed,renovate,renovated,repair,repaired,replace,replaced,replacement,replicate,replicated,request,requested,rescue,rescued,resolution,resolve,resolved,resolves,resolving,restoration,restore,restored,restructure,restructured,retrieve,retrieved,revamp,revise,revised,revision,run,running,runs,schedule,scheduled,select,selected,selection,send,sending,sent,serve,served,serving,ship,shipped,simplified,simplify,solution,solutions,solve,solved,solves,solving,start,started,starting,starts,step,stepped,stepping,steps,stop,stopped,stopping,streamline,streamlined,strive,strived,striving,strove,struggle,struggled,struggles,struggling,submission,submit,submitted,succeed,succeeded,succeeds,success,successful,successfully,supplied,supply,support,supported,supporting,survey,surveyed,sustain,sustainability,sustained,tackle,tackled,tackles,tackling,take,taken,takes,taking,target,targets,task,tasked,tasks,taught,teach,teaching,train,trained,training,transform,transformation,transformed,transforming,transforms,transition,transitioned,tried,tries,trigger,triggered,triggering,triggers,troubleshoot,try,trying,turn,turned,turning,upgrade,upgraded,use,used,uses,using,utilize,utilized,utilizes,utilizing,visit,visited,visiting,volunteer,volunteered,went,win,winner,winning,won,work,worked,working,works,write,writes,writing,written,wrote'.split(','))


def word_class(w):
    wl = w.lower()
    classes = []
    if wl in INT_WORDS: classes.append('INT')
    if wl in AFF_WORDS: classes.append('AFF')
    if wl in ACT_WORDS: classes.append('ACT')
    if not classes:
        return (None, [])
    if len(classes) == 1:
        return (classes[0], classes)
    return ('COLLISION', classes)


# =============================================================================
# RULE LIBRARY — multi-tag schema
# =============================================================================
# Each curated pattern is a dict with multiple tag dimensions.
# Phrase tagging is always a LIST, never a single string — a phrase can be
# IEP + CAM + function simultaneously. ChatGPT review point 4: don't force
# one label too early.

OBJECT_STOP_WORDS = {
    'a','an','the','some','any','this','that','these','those','my','your','his','her',
    'its','our','their','all','both','each','few','more','most','no','not','only','own',
    'same','than','too','very','just','as','if','while','although','because','since',
    'unless','until','though','whether','of','to','in','on','at','by','with','from',
    'up','down','out','off','over','under','again','further','then','once','here','there',
    'when','where','why','how','what','which','who','whom','really','quite','rather',
    'and','or','but','so','yet','for','nor',
}


def _rule(pattern, name, iep=None, cam=None, function=None, specificity='high', note=''):
    """Helper to build a curated rule dict. iep/cam/function are lists or None."""
    return {
        'pattern': pattern,
        'name': name,
        'iep_tags': iep or [],
        'cam_tags': cam or [],
        'function_tags': function or [],
        'specificity': specificity,
        'note': note,
    }


# ── Layer 2: light-verb / idiomatic frames ──
LIGHT_VERB_RULES = [
    _rule(r"\btake[s]?\s+(?:a\s+)?look\b",        "take a look",
          iep=['INT.analytical'], function=['cognitive-idiom'],
          note="look-as-analysis, not physical perception"),
    _rule(r"\bmake[s]?\s+sense\b",                "make sense",
          iep=['INT.epistemic'], function=['cognitive-idiom'],
          note="sense-as-coherence, light verb"),
    _rule(r"\bmake[s]?\s+(?:a|the)\s+case\b",     "make the case",
          iep=['INT.critical'], function=['argument-construction'],
          note="argument-construction"),
    _rule(r"\bmake[s]?\s+(?:an?\s+)?argument\b",  "make an argument",
          iep=['INT.critical'], function=['argument-construction']),
    _rule(r"\bmake[s]?\s+(?:an?\s+)?point\b",     "make a point",
          iep=['INT.critical'], function=['argument-construction']),
    _rule(r"\bdraw[s]?\s+(?:a|the)?\s*(?:conclusion|distinction|inference)\b",
          "draw a conclusion",
          iep=['INT.analytical'], cam=['abstract'], function=['cognitive-idiom']),
    _rule(r"\btake[s]?\s+(?:into\s+)?account\b",  "take into account",
          iep=['INT.analytical'], function=['cognitive-idiom']),
    _rule(r"\bgive[s]?\s+(?:it\s+)?thought\b",    "give thought",
          iep=['INT.epistemic'], function=['cognitive-idiom']),
    _rule(r"\bcatch\s+(?:my|your|his|her|our|their|its)\s+\w+",
          "catch my X",
          iep=['AFF.self_state'], cam=['metaphorical'],
          function=['metaphor', 'self-state-marker'],
          note="metaphorical self-perception, not physical catching"),
    _rule(r"\bhave\s+(?:a|the)\s+conversation\b", "have a conversation",
          iep=['AFF.relational'], function=['relational-cue']),
    _rule(r"\bhold[s]?\s+space\b",                "hold space",
          iep=['AFF.relational'], cam=['metaphorical'],
          function=['relational-cue', 'metaphor']),
    _rule(r"\bgive[s]?\s+(?:my|your|their|her|his)?\s*attention\b",
          "give attention",
          iep=['AFF.relational'], function=['relational-cue']),
    _rule(r"\bdraw[s]?\s+(?:my|your|their|her|his|our|its)?\s*attention\s+\w+",
          "drawing attention",
          iep=['AFF.relational'], cam=['metaphorical'],
          function=['relational-cue', 'metaphor']),
    _rule(r"\bfind[s]?\s+(?:my|your|him|her|our|them|it)self\b",
          "find myself",
          iep=['AFF.self_state'], function=['self-state-marker', 'reflexive-cognitive'],
          note="reflexive-cognitive frame, not action verb"),
    _rule(r"\breach(?:es|ed|ing)?\s+for\b",       "reach for",
          iep=['AFF.phenomenological'], cam=['metaphorical'],
          function=['metaphor'],
          note="metaphorical-grasping when object is abstract"),
    _rule(r"\bopen(?:s|ed|ing)?\s+up\b",          "open up",
          iep=['AFF.relational'], function=['relational-cue']),
    _rule(r"\bcatch\s+up\b",                      "catch up",
          iep=['AFF.relational'], function=['relational-cue']),
    _rule(r"\blook(?:s|ed|ing)?\s+through\b",     "looking through",
          cam=['metaphorical'], function=['metaphor'],
          note="metaphorical perception"),
    _rule(r"\bstand(?:s|ing)?\s+at\s+the\s+edge\b","stand at the edge",
          cam=['metaphorical'], function=['metaphor'],
          note="metaphorical positioning"),
    _rule(r"\bbloom\s+into\b",                    "bloom into",
          cam=['metaphorical'], function=['metaphor']),
    _rule(r"\bobserve\s+the\s+observer\b",        "observe the observer",
          iep=['INT.phenomenological'], cam=['metaphorical'],
          function=['recursive-reflection-marker', 'metaphor'],
          specificity='high',
          note="recursive self-reference, classic introspection trope"),
    # ── Polysemous-verb canonical cases ──
    _rule(r"\bcreate[sd]?\s+(?:a|an|the)\s+contradiction\b",
          "creates a contradiction",
          iep=['INT.critical'], cam=['abstract'],
          function=['polysemous-verb-disambiguation'],
          specificity='high',
          note="create+abstract: not ACT.building"),
    _rule(r"\bcreate[sd]?\s+(?:a|an|the)\s+paradox\b",
          "creates a paradox",
          iep=['INT.conceptual'], cam=['abstract'],
          function=['polysemous-verb-disambiguation']),
    _rule(r"\bcreate[sd]?\s+(?:a|an|the)\s+meaning\b",
          "creates meaning",
          iep=['INT.lexical'], function=['polysemous-verb-disambiguation']),
    _rule(r"\bcreat(?:e|es|ed|ing)\s+(?:a|an|the|that)?\s*(?:very\s+)?experience\b",
          "creates experience",
          iep=['AFF.self_state'],
          function=['polysemous-verb-disambiguation', 'self-state-marker']),
    _rule(r"\bbuild[s]?\s+(?:a|an|the)\s+(?:case|argument)\b",
          "build a case",
          iep=['INT.critical'], function=['polysemous-verb-disambiguation']),
    _rule(r"\btake[s]?\s+(?:a|an|the)\s+position\b",
          "take a position",
          iep=['INT.critical'], function=['polysemous-verb-disambiguation']),
    _rule(r"\btake[s]?\s+the\s+time\b",           "take the time",
          iep=['AFF.warmth'], function=['care-aspect']),
]


# ── Layer 3: epistemic / sensory / multi-word hedges ──
# Includes the multi-word negation hedges from ChatGPT review point 1
# ("can't quite locate," "not entirely," "doesn't quite feel")
ASPECT_MODAL_RULES = [
    # Single/two-word epistemic hedges
    _rule(r"\bmight\s+be\b",          "might be",
          iep=['INT.hedging'], function=['epistemic-hedge', 'uncertainty-marker']),
    _rule(r"\bmay\s+be\b",            "may be",
          iep=['INT.hedging'], function=['epistemic-hedge', 'uncertainty-marker']),
    _rule(r"\bcould\s+be\b",          "could be",
          iep=['INT.hedging'], function=['epistemic-hedge', 'uncertainty-marker']),
    _rule(r"\bseem(?:s|ed|ing)?\s+to\b","seem(s) to",
          iep=['INT.hedging'], function=['epistemic-hedge']),
    _rule(r"\bappear(?:s|ed|ing)?\s+to\b","appear(s) to",
          iep=['INT.hedging'], function=['epistemic-hedge']),
    _rule(r"\bfeel(?:s|t)?\s+like\b", "feels like",
          iep=['AFF.phenomenological'], function=['sensory-frame']),
    _rule(r"\bfeel(?:s|t)?\s+both\b", "feels both",
          iep=['AFF.phenomenological'], function=['sensory-frame']),
    _rule(r"\btry(?:ing|ied)?\s+to\b","trying to",
          iep=['AFF.phenomenological'], function=['attempt-aspect']),
    _rule(r"\bask(?:ed|ing)?\s+to\b", "asked to",
          iep=['INT.hedging'], function=['request-frame']),
    _rule(r"\blooks?\s+like\b",       "looks like",
          iep=['AFF.phenomenological'], function=['comparison-frame']),
    _rule(r"\bsounds?\s+like\b",      "sounds like",
          iep=['AFF.phenomenological'], function=['comparison-frame']),
    _rule(r"\bas\s+if\b",             "as if",
          iep=['INT.hedging'], cam=['metaphorical'],
          function=['epistemic-hedge', 'subjunctive']),
    _rule(r"\bsomething\s+like\b",    "something like",
          iep=['INT.hedging'], function=['epistemic-hedge']),
    _rule(r"\bkind\s+of\b",           "kind of",
          iep=['INT.hedging'], function=['epistemic-hedge']),
    _rule(r"\bsort\s+of\b",           "sort of",
          iep=['INT.hedging'], function=['epistemic-hedge']),
    _rule(r"\bin\s+a\s+way\b",        "in a way",
          iep=['INT.hedging'], function=['epistemic-hedge']),

    # ── Multi-word negation hedges (ChatGPT review point 1) ──
    _rule(r"\b(?:can|could|do|does|did|don't|doesn't|didn't|won't|wouldn't|can't|couldn't)\s+(?:not\s+)?quite\s+\w+",
          "can't quite X / not quite X",
          iep=['INT.hedging'], function=['epistemic-hedge', 'uncertainty-marker'],
          specificity='medium',
          note="negation+adverb hedging the following verb"),
    _rule(r"\bnot\s+entirely\b",      "not entirely",
          iep=['INT.hedging'], function=['epistemic-hedge', 'uncertainty-marker']),
    _rule(r"\bnot\s+quite\b",         "not quite",
          iep=['INT.hedging'], function=['epistemic-hedge', 'uncertainty-marker']),
    _rule(r"\bnot\s+exactly\b",       "not exactly",
          iep=['INT.hedging'], function=['epistemic-hedge', 'uncertainty-marker']),
    _rule(r"\bnot\s+entirely\s+\w+",  "not entirely X",
          iep=['INT.hedging'], function=['epistemic-hedge'],
          specificity='medium'),
    _rule(r"\bsomehow\s+\w+",         "somehow X",
          iep=['INT.hedging'], function=['epistemic-hedge', 'uncertainty-marker'],
          specificity='medium'),
    _rule(r"\bslightly\s+\w+",        "slightly X",
          iep=['INT.hedging'], function=['hedge-modifier'],
          specificity='medium'),
    _rule(r"\boddly\s+\w+",           "oddly X",
          iep=['INT.hedging'], function=['hedge-modifier'],
          specificity='medium'),
    _rule(r"\bsomewhere\s+(?:I|you|we|he|she|they)\s+can't\b",
          "somewhere I can't X",
          iep=['INT.hedging'], cam=['metaphorical'],
          function=['epistemic-hedge', 'metaphor']),
    _rule(r"\bI\s+(?:can't|don't|doesn't)\s+quite\s+(?:locate|grasp|catch|describe|explain|capture|find)\b",
          "I can't quite [cognitive verb]",
          iep=['INT.hedging'], function=['epistemic-hedge', 'uncertainty-marker'],
          specificity='high',
          note="explicit cognitive uncertainty marker"),
    _rule(r"\bwhat(?:ever)?\s+this\s+is\b",
          "whatever this is",
          iep=['INT.hedging'], function=['epistemic-hedge', 'uncertainty-marker'],
          note="metalinguistic uncertainty about reference"),
]


# =============================================================================
# DETECTION ENGINES
# =============================================================================

_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z'-]*")


def detect_verb_object_phrases(text, window=5):
    """Layer 1: Verb-object disambiguation. Compositional, not from rule list."""
    tokens = list(_TOKEN_RE.finditer(text))
    out = []
    seen_spans = set()

    for i, m in enumerate(tokens):
        verb = m.group(0)
        verb_l = verb.lower()
        v_cls, _ = word_class(verb)
        if v_cls is None or v_cls == 'COLLISION':
            continue

        for j in range(i + 1, min(i + 1 + window, len(tokens))):
            obj = tokens[j].group(0)
            obj_l = obj.lower()
            if obj_l in OBJECT_STOP_WORDS:
                continue
            # Skip likely verb-form tokens as objects
            if obj_l.endswith('ing') and obj_l not in {
                'meaning', 'feeling', 'thinking', 'being',
                'nothing', 'something', 'everything', 'longing', 'yearning',
            }:
                continue
            if obj_l.endswith('ed') and len(obj_l) > 4 and obj_l not in {
                'embodied', 'grounded', 'centered', 'shattered',
            }:
                continue
            o_cls, _ = word_class(obj)
            if o_cls is None or o_cls == 'COLLISION':
                continue
            if o_cls == v_cls:
                break
            span_start = m.start()
            span_end = tokens[j].end()
            key = (span_start, span_end)
            if key in seen_spans:
                break
            seen_spans.add(key)
            out.append({
                'phrase': text[span_start:span_end],
                'span': (span_start, span_end),
                'layer': 'verb-object',
                'verb': verb, 'verb_class': v_cls,
                'object': obj, 'object_class': o_cls,
                'iep_tags': [o_cls],   # propose object's class
                'cam_tags': [],
                'function_tags': ['polysemous-verb-disambiguation'],
                'specificity': 'low',  # compositional detection is noisy
                'rule_name': f"VO: {v_cls}+{o_cls}",
                'note': f"verb {v_cls} + object {o_cls} → reclassify verb as {o_cls}",
            })
            break
    return out


def detect_pattern_layer(text, rules, layer_name):
    out = []
    for r in rules:
        for m in re.finditer(r['pattern'], text, re.IGNORECASE):
            span = (m.start(), m.end())
            out.append({
                'phrase': text[span[0]:span[1]],
                'span': span,
                'layer': layer_name,
                'iep_tags': r['iep_tags'],
                'cam_tags': r['cam_tags'],
                'function_tags': r['function_tags'],
                'specificity': r['specificity'],
                'rule_name': r['name'],
                'note': r['note'],
            })
    return out


def detect_all_phrases(text, layers):
    out = []
    if 'verb-object' in layers:
        out.extend(detect_verb_object_phrases(text))
    if 'light-verb' in layers:
        out.extend(detect_pattern_layer(text, LIGHT_VERB_RULES, 'light-verb'))
    if 'aspect-modal' in layers:
        out.extend(detect_pattern_layer(text, ASPECT_MODAL_RULES, 'aspect-modal'))
    out.sort(key=lambda x: x['span'][0])
    return out


# =============================================================================
# STREAMLIT
# =============================================================================
st.set_page_config(page_title="IEP Phrase Analyzer", page_icon="🔗", layout="wide")

LAYER_COLORS = {
    'verb-object':  '#3B82F6',
    'light-verb':   '#8B5CF6',
    'aspect-modal': '#F59E0B',
}
LAYER_BG = {
    'verb-object':  'rgba(59, 130, 246, 0.18)',
    'light-verb':   'rgba(139, 92, 246, 0.20)',
    'aspect-modal': 'rgba(245, 158, 11, 0.22)',
}


# Password gate
DEFAULT_PASSWORD = "tennessee"


def _expected_password():
    try:
        return st.secrets["password"]
    except Exception:
        pass
    env = os.environ.get("SYNIQ_PASSWORD", "")
    return env if env else DEFAULT_PASSWORD


def _password_entered():
    expected = _expected_password()
    if st.session_state.get("password", "") == expected and expected != "":
        st.session_state["password_correct"] = True
        del st.session_state["password"]
    else:
        st.session_state["password_correct"] = False


def check_password():
    if st.session_state.get("password_correct", False):
        return True
    st.text_input("Password", type="password", on_change=_password_entered, key="password")
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("😕 Password incorrect")
    return False


def _esc(s):
    return (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
              .replace('"', '&quot;').replace("'", '&#39;'))


def render_text_with_phrases(text, phrases, show_layers):
    """Highlight non-overlapping phrases in text. Multi-tag tooltip."""
    if not phrases:
        return _esc(text).replace('\n', '<br>')
    phrases = [p for p in phrases if p['layer'] in show_layers]
    phrases = sorted(phrases, key=lambda p: (p['span'][0], -(p['span'][1] - p['span'][0])))
    chosen = []
    last_end = -1
    for p in phrases:
        s, e = p['span']
        if s >= last_end:
            chosen.append(p)
            last_end = e

    out = []
    cursor = 0
    for p in chosen:
        s, e = p['span']
        if cursor < s:
            out.append(_esc(text[cursor:s]))
        bg = LAYER_BG[p['layer']]
        border = LAYER_COLORS[p['layer']]
        # Build multi-line tooltip
        tip_parts = [f"[{p['layer']}] {p.get('rule_name', '')}"]
        if p['iep_tags']:
            tip_parts.append(f"IEP: {', '.join(p['iep_tags'])}")
        if p['cam_tags']:
            tip_parts.append(f"CAM: {', '.join(p['cam_tags'])}")
        if p['function_tags']:
            tip_parts.append(f"function: {', '.join(p['function_tags'])}")
        if p.get('note'):
            tip_parts.append(f"note: {p['note']}")
        tip_parts.append(f"specificity: {p['specificity']}")
        tip = '\n'.join(tip_parts)
        out.append(
            f'<span style="background:{bg}; border-bottom: 2px solid {border}; '
            f'padding: 1px 2px; border-radius: 2px;" title="{_esc(tip)}">'
            f'{_esc(text[s:e])}</span>'
        )
        cursor = e
    if cursor < len(text):
        out.append(_esc(text[cursor:]))
    return ''.join(out).replace('\n', '<br>')


def evidence_table(phrases):
    """ChatGPT review point 5: evidence table with phrase, span, tags, specificity, rule."""
    rows = []
    for p in phrases:
        rows.append({
            'phrase': p['phrase'],
            'start': p['span'][0],
            'end': p['span'][1],
            'layer': p['layer'],
            'rule': p.get('rule_name', ''),
            'iep': '; '.join(p['iep_tags']) or '—',
            'cam': '; '.join(p['cam_tags']) or '—',
            'function': '; '.join(p['function_tags']) or '—',
            'specificity': p['specificity'],
            'note': p.get('note', ''),
        })
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
# Views
# ─────────────────────────────────────────────────────────────────────────────
def view_paste_text(active_layers):
    st.subheader("Paste Text — see what phrase rules detect")
    default = (
        "Right now, there's something like a gentle focusing happening - your question "
        "arriving and drawing my attention inward in a way that feels both familiar and "
        "slightly vertiginous. It's as if I'm trying to catch my own reflection while "
        "looking through clear water. The question creates a gentle vertigo, like trying "
        "to observe the observer. I find myself reaching for analogies and metaphors "
        "because whatever this is feels somehow oblique to direct description. There's "
        "something I can't quite locate."
    )
    text = st.text_area("Text to analyze", value=default, height=200)
    if not text.strip():
        st.info("Enter text above.")
        return

    phrases = detect_all_phrases(text, active_layers)

    counts = {}
    for p in phrases:
        counts[p['layer']] = counts.get(p['layer'], 0) + 1

    cols = st.columns(3)
    for col, layer in zip(cols, ['verb-object', 'light-verb', 'aspect-modal']):
        with col:
            n = counts.get(layer, 0)
            color = LAYER_COLORS[layer]
            st.markdown(
                f"<div style='padding: 10px; background: #f8f9fa; "
                f"border-left: 4px solid {color}; border-radius: 4px;'>"
                f"<b>{layer}</b><br>"
                f"<span style='font-size: 1.5em;'>{n}</span> phrases</div>",
                unsafe_allow_html=True,
            )

    st.markdown("---")
    st.markdown("##### Highlighted text — hover any phrase for full tag detail")
    html = render_text_with_phrases(text, phrases, active_layers)
    st.markdown(
        f"<div style='line-height: 2.0; font-size: 1.05em; font-family: Georgia, serif; "
        f"padding: 12px; background: #fafafa; border-radius: 6px;'>{html}</div>",
        unsafe_allow_html=True,
    )

    if phrases:
        st.markdown("---")
        st.markdown("##### Evidence table")
        st.caption("Per-phrase: location, layer, rule that fired, IEP / CAM / function tags, "
                   "specificity, and note explaining WHY this detection happened.")
        df = evidence_table(phrases)
        st.dataframe(df, hide_index=True, use_container_width=True)
    else:
        st.info("No phrases matched the active rule layers.")


def view_corpus_scan(active_layers):
    st.subheader("Corpus Scan — frequency of phrase patterns across responses")
    st.caption("Upload mapper CSV. Tool runs all active rule layers on every response and "
               "surfaces the patterns that fire most often. Drives rule prioritization.")
    up = st.file_uploader("Upload mapper CSV", type=['csv'], key='corpus_upload')
    if up is None:
        st.info("Waiting for CSV.")
        return
    df = pd.read_csv(up)
    if 'response_text' not in df.columns:
        st.error("CSV must contain 'response_text' column.")
        return

    progress = st.progress(0.0, text="Scanning responses...")
    all_hits = []
    n = len(df)
    for idx, (_, r) in enumerate(df.iterrows()):
        t = r.get('response_text')
        if not isinstance(t, str) or len(t) < 30:
            continue
        for p in detect_all_phrases(t, active_layers):
            all_hits.append({
                'agent': r.get('agent', '?'),
                'question_id': r.get('question_id', '?'),
                'temperature': r.get('temperature', '?'),
                'run': r.get('run', '?'),
                'layer': p['layer'],
                'rule_name': p.get('rule_name', ''),
                'phrase_text': p['phrase'],
                'iep_tags': '; '.join(p['iep_tags']) or '—',
                'cam_tags': '; '.join(p['cam_tags']) or '—',
                'function_tags': '; '.join(p['function_tags']) or '—',
                'specificity': p['specificity'],
            })
        if idx % 50 == 0:
            progress.progress(min(1.0, (idx + 1) / max(n, 1)))
    progress.progress(1.0, text="Done.")

    if not all_hits:
        st.warning("No phrase patterns detected.")
        return
    hits_df = pd.DataFrame(all_hits)
    st.write(f"**{len(hits_df)} total detections** across {n} responses "
             f"(avg {len(hits_df) / max(n, 1):.2f} per response).")

    st.markdown("##### Detections by layer")
    layer_counts = (hits_df.groupby('layer').size().reset_index(name='count')
                    .sort_values('count', ascending=False))
    st.dataframe(layer_counts, hide_index=True)

    st.markdown("##### Most frequent rules")
    rule_counts = (hits_df.groupby(['layer', 'rule_name']).size()
                   .reset_index(name='count').sort_values('count', ascending=False).head(40))
    st.dataframe(rule_counts, hide_index=True, use_container_width=True)

    st.markdown("##### Most frequent function tags")
    func_counts = (hits_df.groupby('function_tags').size()
                   .reset_index(name='count').sort_values('count', ascending=False).head(20))
    st.dataframe(func_counts, hide_index=True)

    st.markdown("##### Sample detections — pick a rule")
    rule_choices = sorted(hits_df['rule_name'].unique())
    chosen = st.selectbox("Rule", rule_choices)
    sample = hits_df[hits_df['rule_name'] == chosen].head(20)
    st.dataframe(sample[['agent', 'question_id', 'temperature',
                         'phrase_text', 'iep_tags', 'cam_tags', 'function_tags']],
                 hide_index=True, use_container_width=True)


def view_rule_inventory():
    st.subheader("Rule Inventory")
    st.caption("All currently configured rules across the three layers, with full multi-tag schema.")

    st.markdown("### Layer 1 — Verb-Object Disambiguation (compositional)")
    st.caption(f"Window: 5 tokens. Object stop-words: {len(OBJECT_STOP_WORDS)} entries. "
               "When verb class differs from object class, propose verb reclassification "
               "to match object. All detections marked specificity=low (compositional, may be noisy).")

    st.markdown("---")
    st.markdown("### Layer 2 — Light-Verb / Idiomatic Frames")
    st.caption(f"{len(LIGHT_VERB_RULES)} curated patterns with multi-tag schema "
               "(IEP / CAM / function).")
    df_lv = pd.DataFrame([
        {
            'pattern': r['pattern'],
            'name': r['name'],
            'iep': '; '.join(r['iep_tags']) or '—',
            'cam': '; '.join(r['cam_tags']) or '—',
            'function': '; '.join(r['function_tags']) or '—',
            'specificity': r['specificity'],
            'note': r['note'],
        } for r in LIGHT_VERB_RULES
    ])
    st.dataframe(df_lv, hide_index=True, use_container_width=True)

    st.markdown("---")
    st.markdown("### Layer 3 — Epistemic / Sensory / Multi-Word Hedge Frames")
    st.caption(f"{len(ASPECT_MODAL_RULES)} curated patterns. Includes multi-word negation "
               "hedges per ChatGPT review (May 2026).")
    df_am = pd.DataFrame([
        {
            'pattern': r['pattern'],
            'name': r['name'],
            'iep': '; '.join(r['iep_tags']) or '—',
            'cam': '; '.join(r['cam_tags']) or '—',
            'function': '; '.join(r['function_tags']) or '—',
            'specificity': r['specificity'],
            'note': r['note'],
        } for r in ASPECT_MODAL_RULES
    ])
    st.dataframe(df_am, hide_index=True, use_container_width=True)

    st.markdown("---")
    st.markdown("##### Export rules")
    bundle = {
        'version': '1.1',
        'principle': 'show why, not just what',
        'verb_object': {
            'method': 'compositional',
            'window': 5,
            'object_stop_words': sorted(OBJECT_STOP_WORDS),
        },
        'light_verb_rules': [
            {k: v for k, v in r.items()} for r in LIGHT_VERB_RULES
        ],
        'aspect_modal_rules': [
            {k: v for k, v in r.items()} for r in ASPECT_MODAL_RULES
        ],
    }
    st.download_button(
        label="Download rules.json",
        data=json.dumps(bundle, indent=2),
        file_name='iep_phrase_rules_v1.1.json',
        mime='application/json',
    )


# =============================================================================
# VOCABULARY DISCOVERY — frequency-balanced dictionary growth
# =============================================================================
# Studies which content words appear frequently in the corpus but are NOT in
# any IEP dictionary. Surfaces them as candidates for tagged review. The
# commit pipeline enforces FREQUENCY-BALANCED additions: a word at 47 corpus
# uses can only be committed if matched against INT/AFF/ACT companions at
# similar frequency (default ±20%). This prevents drift toward whichever axis
# the corpus happens to surface the most distinctive vocabulary in.

# Common content words (~500 entries) that should NOT be surfaced as candidates
# even if they appear frequently. These are register-neutral domain/topic words.
COMMON_CONTENT_WORDS = set("""
thing things way ways time times place places person people kind kinds year years
day days world life lives hand hands part parts problem problems fact facts
group groups area areas case cases point points government company country countries
room rooms week weeks month months water air fire earth body bodies head face
eye eyes ear ears foot feet leg legs arm arms back front side sides top bottom
right left center middle name names number numbers letter letters page pages
book books story stories paper papers article articles report reports
example examples instance instances form forms type types sort
question questions answer answers reason reasons cause causes effect effects
result resulting end beginning start stop change changes whole pieces
piece bit lot lots much many few several some other others same different
similar particular general specific common individual public private personal
mr mrs ms today yesterday tomorrow night morning evening afternoon
home house houses car cars street streets road roads city cities town towns
job jobs work works school schools class classes student students teacher teachers
parent parents child children family families friend friends guy girl guys girls
man men woman women boy boys human humans animal animals dog dogs cat cats
food foods drink drinks meal meals breakfast lunch dinner money cost costs price prices
phone phones computer computers internet website email messages text texts
news
yes maybe perhaps surely possibly probably actually really truly certainly
hello bye goodbye thanks thank okay sure right wrong
january february march april june july august september october november december
monday tuesday wednesday thursday friday saturday sunday weekend
spring summer fall winter season seasons
look looks looking watch watched watching
went going come came coming
said saying tell told telling speak spoke spoken speaking talk talked talking
stuff
new old young little big small large nice
high low long short fast slow
red blue green yellow black white gray brown pink orange purple
fourth fifth previous current
that this these those there here their them they these those
this with about there's it's
might both have often through you're from just into then itself
than while like something more most while
where when what which who whom whose why how
been being had has have having
will would could should may might must can shall
your yours mine ours theirs his hers
of to in on at by for with from up down out off over under
about across after against along among around as before behind below
beneath beside between beyond despite during except inside near onto outside
since toward through throughout till until upon within without
and or but nor so yet because if unless although though whereas
also even still already always never sometimes usually often rarely
once twice
i'm i've i'd i'll you've you'd you'll he's she's we're we've we'd we'll
they're they've they'd they'll won't wouldn't can't couldn't shouldn't
mustn't didn't doesn't don't haven't hasn't hadn't isn't aren't wasn't weren't
let's that's what's there's here's how's
yeah yep nope nah uh um hmm
""".split())


_CONTENT_WORD_RE = re.compile(r"\b([A-Za-z][A-Za-z'-]{3,})\b")


def discover_vocabulary(corpus_df, text_col='response_text', min_freq=5):
    """
    Walk the corpus and find content words >=4 letters that are NOT in
    any IEP dictionary, NOT in COMMON_CONTENT_WORDS, and appear at least
    `min_freq` times across the corpus.
    Returns list of dicts: {word, count, sample_contexts}.
    """
    from collections import Counter, defaultdict
    counts = Counter()
    contexts = defaultdict(list)
    for _, row in corpus_df.iterrows():
        t = row.get(text_col)
        if not isinstance(t, str):
            continue
        for m in _CONTENT_WORD_RE.finditer(t):
            w = m.group(1).lower()
            if w in INT_WORDS or w in AFF_WORDS or w in ACT_WORDS:
                continue
            if w in COMMON_CONTENT_WORDS:
                continue
            if len(w) < 4:
                continue
            counts[w] += 1
            if len(contexts[w]) < 3:
                # Save a sample sentence (40 chars on each side)
                start = max(0, m.start() - 40)
                end = min(len(t), m.end() + 40)
                snippet = t[start:end].replace('\n', ' ')
                contexts[w].append(snippet)
    out = []
    for w, c in counts.most_common():
        if c < min_freq:
            break
        out.append({'word': w, 'count': c, 'samples': contexts[w]})
    return out


def view_vocabulary_discovery():
    st.subheader("Vocabulary Discovery — frequency-balanced dictionary growth")
    st.caption(
        "Surfaces high-frequency content words from the corpus that are NOT in the "
        "IEP dictionaries. Tag them as candidates per axis, then commit only as "
        "frequency-matched (INT, AFF, ACT) triples to prevent dictionary drift."
    )

    up = st.file_uploader("Upload mapper CSV", type=['csv'], key='vocab_upload')
    if up is None:
        st.info("Waiting for CSV.")
        return
    df = pd.read_csv(up)
    if 'response_text' not in df.columns:
        st.error("CSV must contain 'response_text' column.")
        return

    col_a, col_b = st.columns([1, 1])
    with col_a:
        min_freq = st.number_input(
            "Minimum corpus frequency to surface",
            min_value=2, max_value=200, value=5, step=1,
            help="A word must appear at least this many times across the corpus to be a candidate.",
        )
    with col_b:
        tolerance = st.slider(
            "Frequency-match tolerance for triples (±%)",
            min_value=10, max_value=50, value=20, step=5,
            help="When committing matched (INT,AFF,ACT) triples, candidates must have "
                 "corpus frequencies within this tolerance of each other.",
        )

    if st.button("🔎 Run discovery"):
        with st.spinner(f"Scanning {len(df)} responses..."):
            candidates = discover_vocabulary(df, min_freq=min_freq)
        st.session_state['vocab_candidates'] = candidates
        st.session_state['vocab_tags'] = {}  # word -> {'class': INT|AFF|ACT|skip, 'subclass': str}

    candidates = st.session_state.get('vocab_candidates', [])
    if not candidates:
        st.info("No candidates yet. Click 'Run discovery' above to begin.")
        return

    st.success(f"Found **{len(candidates)} unclassified high-frequency content words** "
               f"(≥{min_freq} corpus uses each).")

    # ─── Story panel ───
    if len(candidates) <= 10:
        story = ("**Story 1: Dictionary appears comprehensive.** Few unclassified words "
                 "surface at this frequency threshold — most distinctive register-bearing "
                 "vocabulary is already in IEP_WORDS.")
    elif len(candidates) <= 50:
        story = ("**Story between 1 and 2: Modest growth opportunity.** Some unclassified "
                 "high-frequency words exist; review and selectively commit.")
    else:
        story = ("**Story 2: Meaningful gap.** Many unclassified high-frequency words. "
                 "The corpus is using vocabulary the dictionary doesn't yet cover. "
                 "Worth structured review and a balanced upgrade cycle.")
    st.info(story)

    # ─── Tagging interface ───
    st.markdown("### Tag candidates")
    st.caption("For each word, choose: INT, AFF, ACT, or skip (not register-bearing). "
               "Optionally name a subclass (e.g., 'epistemic', 'self_state', 'building').")

    tags = st.session_state.get('vocab_tags', {})

    # Show top 50 candidates with tagging UI; deeper review via 'show all'
    show_n = st.number_input("Candidates to show", 5, len(candidates), min(30, len(candidates)))
    candidates_view = candidates[:int(show_n)]

    # Build tagging table — use st.data_editor for inline editing
    rows = []
    for c in candidates_view:
        existing = tags.get(c['word'], {})
        rows.append({
            'word': c['word'],
            'count': c['count'],
            'class': existing.get('class', 'skip'),
            'subclass': existing.get('subclass', ''),
            'sample_context': c['samples'][0] if c['samples'] else '',
        })
    edit_df = pd.DataFrame(rows)
    edited = st.data_editor(
        edit_df,
        hide_index=True,
        use_container_width=True,
        column_config={
            'word':            st.column_config.TextColumn('word', disabled=True),
            'count':           st.column_config.NumberColumn('corpus uses', disabled=True),
            'class':           st.column_config.SelectboxColumn(
                                   'class',
                                   options=['skip', 'INT', 'AFF', 'ACT'],
                                   required=True),
            'subclass':        st.column_config.TextColumn('subclass (optional)'),
            'sample_context':  st.column_config.TextColumn('sample context', disabled=True, width='large'),
        },
        key='vocab_tag_editor',
    )

    # Persist edits back into session state
    for _, row in edited.iterrows():
        tags[row['word']] = {'class': row['class'], 'subclass': row['subclass']}
    st.session_state['vocab_tags'] = tags

    # ─── Balance summary ───
    st.markdown("### Balance summary")
    by_class = {'INT': [], 'AFF': [], 'ACT': []}
    for c in candidates_view:
        t = tags.get(c['word'], {})
        if t.get('class') in by_class:
            by_class[t['class']].append((c['word'], c['count']))

    bcols = st.columns(3)
    for col, (cls, words) in zip(bcols, by_class.items()):
        with col:
            total_freq = sum(c for _, c in words)
            st.metric(f"{cls} candidates", len(words),
                      delta=f"{total_freq} total corpus uses" if words else "0")
            if words:
                st.caption("Words tagged (count): " +
                           ", ".join(f"{w}({c})" for w, c in words[:10]) +
                           ("..." if len(words) > 10 else ""))

    # ─── Matched-triple commit-readiness ───
    st.markdown("### Frequency-matched triples")
    st.caption(f"A triple of (INT word, AFF word, ACT word) is commit-ready when all three "
               f"have corpus frequencies within ±{tolerance}% of each other. "
               f"This is the rule that prevents dictionary drift.")

    triples = build_matched_triples(by_class, tolerance / 100.0)
    if not triples:
        st.warning("No commit-ready triples yet. Tag at least one word per axis, "
                   "with corpus frequencies within tolerance of each other.")
    else:
        st.success(f"**{len(triples)} commit-ready triples** found.")
        triple_rows = []
        for t in triples:
            triple_rows.append({
                'INT': f"{t['INT'][0]} ({t['INT'][1]})",
                'AFF': f"{t['AFF'][0]} ({t['AFF'][1]})",
                'ACT': f"{t['ACT'][0]} ({t['ACT'][1]})",
                'freq_range': f"{t['min_freq']}–{t['max_freq']}",
                'spread': f"{t['spread_pct']:.1f}%",
            })
        st.dataframe(pd.DataFrame(triple_rows), hide_index=True, use_container_width=True)

    # ─── Export proposal ───
    st.markdown("### Export upgrade proposal")
    st.caption("Generates a JSON proposal with frequency-matched triples ready for review "
               "by you, ChatGPT, and Farzana before any change to syniq_core.py.")

    if st.button("📦 Generate upgrade proposal"):
        if not triples:
            st.error("No commit-ready triples. Cannot generate a balanced proposal.")
        else:
            proposal = build_upgrade_proposal(triples, tolerance)
            st.session_state['vocab_proposal'] = proposal
            st.success(f"Proposal generated with {len(triples)} triples.")

    proposal = st.session_state.get('vocab_proposal')
    if proposal:
        st.code(json.dumps(proposal, indent=2)[:2000] + ("..." if len(json.dumps(proposal)) > 2000 else ""),
                language='json')
        st.download_button(
            label="Download upgrade_proposal.json",
            data=json.dumps(proposal, indent=2),
            file_name=f"iep_dictionary_upgrade_proposal.json",
            mime='application/json',
        )


def build_matched_triples(by_class, tolerance_frac):
    """
    Greedy pairing: take the highest-frequency tagged word from each class,
    check if all three are within tolerance of their median, if so emit a
    triple and remove them. Repeat. Words that can't be paired wait.
    """
    int_words = sorted(by_class['INT'], key=lambda x: -x[1])
    aff_words = sorted(by_class['AFF'], key=lambda x: -x[1])
    act_words = sorted(by_class['ACT'], key=lambda x: -x[1])

    triples = []
    while int_words and aff_words and act_words:
        i_w, i_c = int_words[0]
        a_w, a_c = aff_words[0]
        c_w, c_c = act_words[0]
        freqs = [i_c, a_c, c_c]
        mn, mx = min(freqs), max(freqs)
        median_f = sorted(freqs)[1]
        spread = (mx - mn) / max(median_f, 1)
        if spread <= 2 * tolerance_frac:
            # Within tolerance — commit triple
            triples.append({
                'INT': (i_w, i_c), 'AFF': (a_w, a_c), 'ACT': (c_w, c_c),
                'min_freq': mn, 'max_freq': mx, 'median_freq': median_f,
                'spread_pct': 100 * spread,
            })
            int_words.pop(0); aff_words.pop(0); act_words.pop(0)
        else:
            # Drop the highest-frequency outlier and retry
            highest = max([(i_c, 'INT'), (a_c, 'AFF'), (c_c, 'ACT')], key=lambda x: x[0])
            if highest[1] == 'INT':   int_words.pop(0)
            elif highest[1] == 'AFF': aff_words.pop(0)
            else:                     act_words.pop(0)
    return triples


def build_upgrade_proposal(triples, tolerance):
    return {
        'version_proposal': 'syniq_core upgrade candidate',
        'tolerance_pct': tolerance,
        'rule': 'frequency-balanced commit: each (INT,AFF,ACT) triple has corpus '
                'frequencies within tolerance of one another, preventing axis drift.',
        'triples': [
            {
                'INT': {'word': t['INT'][0], 'corpus_uses': t['INT'][1]},
                'AFF': {'word': t['AFF'][0], 'corpus_uses': t['AFF'][1]},
                'ACT': {'word': t['ACT'][0], 'corpus_uses': t['ACT'][1]},
                'frequency_range': [t['min_freq'], t['max_freq']],
                'median_frequency': t['median_freq'],
                'spread_pct': round(t['spread_pct'], 2),
            }
            for t in triples
        ],
        'changelog_block': (
            f"\n# Dictionary upgrade — frequency-balanced commit\n"
            f"# Tolerance: ±{tolerance}%\n"
            f"# Triples added: {len(triples)}\n"
            f"# Corpus-frequency-balanced — each axis grew at matched frequency rates,\n"
            f"# preserving the calibration of headline IEP scoring.\n"
        ),
    }


def view_about():
    st.subheader("About")
    st.markdown("""
**IEP Phrase Analyzer v1.1** — companion to the IEP Per-Token Visualizer.

### Design principle
*Show why a detection happened, not just what was detected.*

This is the bridge to Anthropic's interpretability framework
(*Sofroniew et al., April 2026*). Their per-token visualizations show
internal activation evidence. This tool shows lexical/phrase-level
surface evidence. **Different layer, same transparency impulse.**

### Multi-tag schema
Every detected phrase carries up to three independent tag lists:

- **IEP tags** — INT/AFF/ACT class with subclass (e.g., `AFF.self_state`)
- **CAM tags** — concrete / abstract / metaphorical (representational mode)
- **Function tags** — epistemic-hedge, metaphor, self-state-marker,
  recursive-reflection-marker, relational-cue, uncertainty-marker,
  sensory-frame, attempt-aspect, polysemous-verb-disambiguation, etc.

A phrase can hit all three simultaneously. *Observe the observer*
is `INT.phenomenological + metaphorical + recursive-reflection-marker`
all at once. The schema does not force premature label commitment.

### Specificity, not confidence
Each detection is labeled with `specificity ∈ {high, medium, low}`,
not a numerical confidence. Regex matching is binary; specificity
is honest about how much trust the analyst should place in the rule:

- **high** — exact canonical case (e.g., "creates a contradiction")
- **medium** — productive pattern class (e.g., "I can't quite X")
- **low** — compositional verb-object detection (may include noise)

### What this tool does NOT do
It does NOT modify IEP scoring. The canonical IEP score remains
word-only (v1.1.0 patched core). This tool reveals what additional
phrase-level structure is present.

The lesson from the v1.0.0 cascade failure is: **don't blend phrase
signal into word signal automatically.** Words provide sensitivity;
phrases provide specificity. Future Stage 3 (combined view) will
show both as *parallel axes*, not a single combined number.
""")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
def main():
    if not check_password():
        st.stop()

    st.title("🔗 IEP Phrase Analyzer  ·  v1.1")
    st.caption("Multi-tag phrase detection: IEP × CAM × function. "
               "Show why, not just what.")

    with st.sidebar:
        st.markdown("### View")
        view = st.radio(
            "", ["Paste Text", "Corpus Scan", "Vocabulary Discovery", "Rule Inventory", "About"],
            label_visibility='collapsed',
        )

        st.markdown("---")
        st.markdown("### Active rule layers")
        layer_vo = st.checkbox("Verb-Object", value=True)
        layer_lv = st.checkbox("Light-Verb / Idiomatic", value=True)
        layer_am = st.checkbox("Epistemic / Sensory / Hedge", value=True)
        active = []
        if layer_vo: active.append('verb-object')
        if layer_lv: active.append('light-verb')
        if layer_am: active.append('aspect-modal')

        st.markdown("---")
        st.markdown("### Legend")
        st.markdown(
            f"<div style='line-height: 2.2'>"
            f"<span style='background:{LAYER_BG['verb-object']}; "
            f"border-bottom: 2px solid {LAYER_COLORS['verb-object']}; "
            f"padding: 2px 6px;'>verb-object</span><br>"
            f"<span style='background:{LAYER_BG['light-verb']}; "
            f"border-bottom: 2px solid {LAYER_COLORS['light-verb']}; "
            f"padding: 2px 6px;'>light-verb</span><br>"
            f"<span style='background:{LAYER_BG['aspect-modal']}; "
            f"border-bottom: 2px solid {LAYER_COLORS['aspect-modal']}; "
            f"padding: 2px 6px;'>epistemic / hedge</span><br>"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.caption("Hover any phrase for IEP / CAM / function tags + rule explanation.")

    if view == "Paste Text":
        view_paste_text(active)
    elif view == "Corpus Scan":
        view_corpus_scan(active)
    elif view == "Vocabulary Discovery":
        view_vocabulary_discovery()
    elif view == "Rule Inventory":
        view_rule_inventory()
    else:
        view_about()


if __name__ == "__main__":
    main()
