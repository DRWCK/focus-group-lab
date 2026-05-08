"""
iep_combined_visualizer.py — IEP Combined Word + Phrase Visualizer
====================================================================

SYN-IQ Stage 3 — Combined IEP measurement and audit visualization.

Built to ChatGPT's spec (May 2026). Combines:
  - Word-level IEP scoring (existing dictionary-based)
  - Phrase-level IEP redistribution (fractional allocations per rule)
  - Side-by-side score cards: word-only / phrase-only / combined
  - Per-token highlighting + per-phrase underlines
  - Evidence tables exportable as CSV

Scientific positioning:
  This tool is an interpretability and audit layer. Phrase rules provide
  contextual redistribution of surface IEP signals; they are not claims
  about internal cognition.

Design principle (carried over from prior tools):
  Show why, not just what. Word fills + phrase underlines + multi-tag
  evidence for every detection.

Methodological note:
  Canonical IEP scoring remains word-only (per syniq_core v1.1.0 patch,
  May 2026). The "Combined IEP" score in this tool is exploratory and
  diagnostic; it is presented alongside the canonical word-only score,
  not as a replacement.

Run:
  streamlit run iep_combined_visualizer.py

Default password: tennessee
"""

import os
import re
import io
import json
from typing import Dict, List, Tuple, Optional

import pandas as pd
import streamlit as st


# =============================================================================
# IEP DICTIONARIES (V50, embedded — easy to swap for syniq_core import later)
# =============================================================================
# Embedded for standalone deploy. To migrate:
#   from syniq_core import INT_WORDS, AFF_WORDS, ACT_WORDS, SUB_INT, SUB_AFF, SUB_ACT
# and remove the embedded dictionaries below.

INT_WORDS = set('ability,absolute,absolutely,abstract,abstraction,accuracy,accurate,algorithm,algorithmic,allows,although,always,ambiguity,ambiguous,analogous,analogously,analogy,analysis,analytical,analyze,annotate,annotated,answer,appear,appeared,appears,appraisal,appraise,appraised,approach,approaches,approximate,architecture,argue,argued,argues,arguing,argument,arguments,assert,asserted,assertion,assertions,assess,assessment,assume,assumed,assumes,assuming,assumption,assumptions,axiom,axiomatic,basis,because,bias,biased,boundaries,boundary,but,calculate,calculation,categorical,categorically,categories,categorize,category,causal,causally,causation,cause,caused,causes,certain,certainly,certitude,challenge,challenges,circumscribe,claim,claimed,claims,clarify,clarity,classical,classification,classify,clear,cogent,cogently,cognition,cognitive,coherence,coherent,coherently,communication,compare,comparison,complex,complexity,comprehend,comprehension,computation,computational,compute,conceivable,conceive,conceived,concept,concepts,conceptual,conceptualize,conceptually,conclude,conclusion,conclusions,confirm,confirmation,conjecture,conjectured,conscious,consequence,consequences,consider,consideration,consistency,consistent,consistently,construe,construed,context,contradict,contradiction,contradictory,contrast,correlate,correlated,correlation,could,counterargument,counterexample,counterpoint,criteria,criterion,data,debatable,debate,debated,deconstruct,deconstructed,deconstruction,deduce,deduction,define,defined,definite,definitely,definition,definitive,definitively,delineate,delineated,demarcate,demarcated,demonstrate,demonstration,derivation,derive,derived,derives,describe,described,describing,description,determination,determine,diagnose,diagnosed,diagnosis,diagnostic,differ,difference,differences,different,differentiate,differs,discern,discerned,discernible,disprove,disproven,dissect,dissected,distinguish,effect,effects,elaborate,elaborated,elaboration,elucidate,elucidated,empirical,empirically,enumerate,enumerated,epistemic,epistemological,equate,equation,equivalence,equivalent,erroneous,error,errors,essential,essentially,estimate,estimated,estimation,evaluate,evaluation,evidence,evidently,exact,exactly,examination,examine,except,exemplified,exemplify,exists,experiment,experimental,explain,explained,explaining,explains,explanation,explanations,explicit,explicitly,exploration,explore,explored,exploring,express,expressing,expression,extrapolate,extrapolated,extrapolation,fact,facts,factual,factually,fallacious,fallacy,falsifiable,falsified,falsify,find,finding,formal,formalize,formula,formulate,formulated,formulation,found,framework,frameworks,function,fundamental,fundamentally,generalization,generalize,grasp,grasped,guess,hence,heuristic,heuristics,hierarchy,however,hypothesis,hypothesize,idea,ideas,identity,if,illuminate,illuminated,illuminating,implausible,implication,implications,implied,implies,imply,implying,incompleteness,inconsistency,inconsistent,indicate,indicated,indicates,indicating,indication,indicative,individual,infer,inference,infinite,information,insight,insightful,insights,instead,insufficient,intellectual,intellectually,interaction,internal,interpolate,interpret,interpretation,interpretations,interpreted,interpreting,invalid,investigate,investigated,investigation,judge,judgement,judgment,justification,justified,justify,know,knowing,knowledge,knowledgeable,known,language,languages,leads,level,likelihood,likely,limitations,limits,linguistic,literal,literally,logic,logical,logically,maybe,meaning,meaningful,meaningfully,measure,measurement,mechanism,mechanisms,meta,method,methodical,methodically,methodology,metrics,model,models,moreover,namely,natural,nature,nearly,necessarily,necessary,necessity,never,nonetheless,notice,noticed,noticing,notion,notions,objection,objectively,objectivity,observation,observations,observe,observed,obvious,obviously,order,ordered,organization,organize,otherwise,ought,paradigm,paradox,paradoxical,paradoxically,pattern,patterns,perhaps,perspective,philosophical,philosophically,philosophy,physical,plausibility,plausible,possibly,postulate,postulated,postulation,potential,pragmatic,pragmatically,precise,precision,predicate,predicated,predict,predictable,predicted,prediction,predictions,premise,premises,presumably,presume,presumed,presumption,principle,principles,probably,problem,procedural,procedure,process,processes,processing,proof,propose,proposed,proposition,prove,proven,purpose,quantify,quantitative,queried,query,question,questions,rather,rational,rationale,rationality,rationally,realize,realized,reason,reasoned,reasoning,reasons,rebut,rebuttal,recognition,recognize,reconsider,reconsidered,refer,reference,refers,refine,refined,refinement,reflecting,reflection,refutation,refute,refuted,requirement,requires,response,responses,result,resulting,results,rigor,rigorous,rigorously,role,rule,rules,schema,scrutinize,scrutinized,scrutiny,seem,seemed,seems,semantic,semantically,sequence,sequential,should,significance,significant,significantly,simple,simply,simultaneously,singular,specific,specifically,specification,specify,standard,standards,state,states,step,steps,stipulate,stipulated,strategies,strategy,structural,structure,subject,subjective,subjectively,subjectivity,substantiate,substantiated,sufficient,sufficiently,suggests,summarize,summarized,summary,suppose,supposed,supposedly,supposition,sure,surely,syllogism,syllogistic,synthesis,synthesize,synthesized,system,systematic,systematically,systems,tactic,tactics,taxonomy,technique,test,tested,testing,theorem,theoretical,theoretically,theorize,theory,thereby,therefore,thesis,think,thinking,thought,thoughts,thus,trivial,trivially,unambiguous,underlying,understand,understanding,understood,unique,universal,unless,unlikely,valid,validate,validation,validity,value,values,variable,variables,verification,verify,versus,warrant,warranted,whereas,whereby,whether,why,word,words,would'.split(','))

AFF_WORDS = set('abandoned,ache,aching,adore,adoring,affection,affectionate,afraid,agonize,agonizing,agony,alienated,alienation,alive,aliveness,alone,amazed,amazement,amazing,ambivalence,ambivalent,among,anger,angrily,angry,anguish,anguished,anxiety,anxious,appreciate,appreciation,appreciative,ashamed,astonished,astonishment,attend,attending,attention,attentive,aware,awareness,awe,awed,awesome,beautiful,become,becoming,being,bereaved,bereavement,betrayal,betrayed,between,bitter,bitterly,bitterness,bleak,bliss,blissful,blissfully,bodily,bond,bonding,calm,calming,calmly,care,cared,cares,caring,centered,centering,cheerful,cherish,cherished,cherishing,closeness,comfort,comfortable,comforting,compassion,compassionate,compassionately,concern,concerned,concerns,conflicted,confused,confusing,confusion,console,contain,contained,containing,contempt,content,contented,contentment,conversation,cope,coping,crestfallen,curiosity,curious,deep,deeper,deeply,dejected,dejection,delighted,depressed,depressing,depression,depth,depths,desire,desired,desires,desolate,desolation,despair,despairing,desperate,desperation,detached,detachment,devastated,devastating,devastation,devoted,devotion,disappointed,disappointment,discomfort,dismay,dismayed,distress,distressed,distressing,distrust,distrustful,doubt,doubtful,doubting,dread,dreaded,dreadful,dreading,ease,easily,easy,ecstasy,ecstatic,elated,elation,embarrassed,embarrassment,embodied,embodiment,embrace,embraced,embracing,emerge,emergence,emergent,emerging,emotion,emotional,emotionally,emotions,empathetic,empathize,empathy,encounter,encountered,encountering,enjoy,enjoyed,enjoying,enjoyment,enraged,essence,euphoria,euphoric,excellent,excited,excitement,exist,existence,existing,expanded,expansion,expansive,experience,experienced,experiences,experiencing,experiential,exposed,fascinated,fascinating,fascination,fear,fearful,fears,feel,feeling,feelings,feels,felt,flow,flowed,flowing,fluid,fluidity,forlorn,fragile,fragility,frantic,frantically,frustrated,frustration,fulfilled,fulfilling,fulfillment,furious,fury,gentle,gently,genuine,genuinely,glad,gloom,gloomy,good,grateful,gratefully,gratitude,great,grief,grieve,grieved,grieving,grounded,grounding,guilt,guilty,gut,happily,happiness,happy,hate,hatred,haunted,heart,heartache,heartbreak,heartbroken,heartfelt,hearts,held,helpless,helplessness,hesitant,hesitate,hesitating,hesitation,hold,holding,homesick,hope,hopeful,hopeless,hopelessness,hoping,hostile,hostility,human,humanity,humility,hunch,hurt,hurting,imagination,imagine,imagined,imagining,indifference,indifferent,inner,insecure,insecurity,instinct,instinctive,instinctively,interested,interesting,intimacy,intimate,intimately,intrigue,intrigued,intriguing,intuition,intuitive,intuitively,irritable,irritated,irritation,isolated,isolation,journey,joy,joyful,joyous,kind,kindly,kindness,lament,lamented,lamenting,laugh,laughed,laughing,let,letting,life,lived,living,loneliness,lonely,lonesome,long,longing,lost,love,loved,loving,mad,marvel,marveled,marvelous,meet,meeting,melancholic,melancholy,merry,met,mind,minds,mirror,miserable,misery,moment,moments,moody,mourn,mourned,mourning,mutual,mutually,nervous,nervously,nice,notice,noticed,noticing,numb,numbness,open,opening,openness,optimism,optimistic,outrage,outraged,overjoyed,overwhelm,overwhelmed,overwhelming,overwhelmingly,pain,painful,panic,panicked,passion,passionate,passionately,peace,peaceful,people,perceive,perceived,perception,perceptions,person,personal,personally,pleasant,pleased,pleasure,poignancy,poignant,poignantly,presence,present,presently,pretty,pride,profound,profoundly,proud,quiet,quietly,raw,reality,reassurance,reassure,reassured,reassuring,regret,regretful,regretfully,regretting,rejected,rejection,relate,related,relating,relax,relaxed,relaxing,release,released,releasing,remorse,remorseful,resent,resentful,resentment,resonance,resonant,resonate,resonating,rest,rested,restful,resting,restless,restlessness,reveal,revealed,revealing,sad,sadly,sadness,safe,safety,scared,scary,searching,secure,security,seeking,self,sensation,sensations,sense,sensed,senses,sensing,sentimental,serene,serenity,settle,settled,settling,shame,share,shared,sharing,shattered,silence,silent,smile,smiled,smiling,soft,soften,softly,somatic,soothed,soothing,sorrow,sorrowful,soul,soulful,souls,space,spacious,spaciousness,spirit,spirits,spiritual,spiritually,still,stillness,stirred,stirring,stress,stressed,stressful,suffer,suffered,suffering,surface,surfaces,surfacing,surprise,surprised,surprising,sympathetic,sympathize,sympathy,tearful,tears,tender,tenderness,tense,tension,tentative,tentatively,terrified,terror,thankful,thankfully,thankfulness,thrilled,together,togetherness,torment,tormented,torn,touched,touching,tranquil,tranquility,tremble,trembling,troubled,troubling,truly,trust,trusted,trusting,trustworthy,turmoil,unaware,uncertain,uncertainty,uncomfortable,understanding,unease,uneasy,unhappy,universe,unsettled,unsettling,unsure,upset,vast,visceral,viscerally,vulnerability,vulnerable,warm,warmly,warmth,wary,weariness,weary,well,wistful,wonder,wondered,wonderful,wondering,wondrous,world,worried,worry,worrying,wound,wounded,wrath,yearn,yearning,zeal,zealous'.split(','))

ACT_WORDS = set('access,accessed,accessing,accomplish,accomplished,accomplishes,accomplishing,accomplishment,achieve,achieved,achievement,achievements,achieves,achieving,act,acting,action,actions,activate,activated,activates,activating,activation,acts,adapt,adaptation,adapted,adapting,adapts,address,addressed,addresses,addressing,adjust,adjusted,adjusting,adjustment,adjusts,advance,advanced,advancement,advances,advancing,ahead,aim,aimed,aiming,aims,allocate,allocated,allocation,application,applied,applies,apply,applying,arrange,arranged,arrangement,arrangements,ask,asked,asking,assemble,assembled,assign,assigned,assignment,attempt,attempted,attempting,attempts,authorize,authorized,began,begin,beginning,begins,begun,best,better,bolster,bolstered,break,breaking,bring,bringing,broken,brought,budget,build,building,builds,built,calibrate,calibrated,call,called,calling,campaign,canvass,canvassed,carried,carry,carrying,catalogue,catalogued,centralize,centralized,change,changed,changes,changing,channel,channeled,chart,check,checked,checking,choice,choices,choose,choosing,chose,chosen,circumvent,coach,collaborate,collaborated,collaboration,commission,commit,commitment,committed,compile,compiled,complete,completed,completes,completing,completion,conclude,concluded,concludes,concluding,configure,configured,connect,connected,connecting,connection,connections,consolidate,construct,constructed,constructing,constructs,continuation,continue,continued,continues,continuing,control,controlled,controlling,controls,conversion,convert,converted,converting,converts,coordinate,coordinated,coordination,craft,crafted,crafting,create,created,creates,creating,creation,customize,deadline,decide,decided,deciding,decision,decisions,delegate,delegated,delegation,deliver,delivered,delivering,delivers,delivery,deploy,deployed,deploying,deployment,deploys,design,designed,designing,designs,develop,developed,developing,development,develops,did,direct,directed,directing,dive,diving,do,does,doing,done,draft,drafting,edit,editing,effort,efforts,eliminate,eliminated,elimination,employ,employed,employing,employs,enable,enabled,end,ended,ending,ends,enforce,enforced,enforcement,engage,engaged,engagement,engineer,engineering,enroll,enrolled,enrollment,equip,equipped,establish,established,establishes,establishing,establishment,execute,executed,executes,executing,execution,expedite,facilitate,facilitated,facilitation,finalize,finalized,finish,finished,finishes,finishing,fix,fixed,fixes,fixing,focus,focused,focusing,form,formation,formed,forming,forms,forward,fund,funded,funding,gather,gathered,gathering,generate,generated,generates,generating,generation,give,given,gives,giving,go,goal,goals,goes,going,gone,grew,grow,growing,growth,handle,handled,handles,handling,help,helped,helping,helps,hire,hired,hiring,implement,implementation,implemented,implementing,implements,improve,improved,improvement,improving,increase,increased,increasing,initiate,initiated,initiates,initiating,initiation,inspect,inspection,install,installation,installed,integrate,integrated,integration,intervene,intervention,invest,invested,investment,iterate,iterated,iteration,labor,labored,laboring,launch,launched,launches,launching,lead,leader,leadership,leading,learn,learned,learning,led,made,maintain,maintained,maintenance,make,makes,making,manage,managed,management,manager,managing,map,mapped,mapping,migrate,migrated,migration,mobilize,mobilized,modification,modified,modifies,modify,modifying,monitor,monitored,monitoring,move,moved,movement,movements,moves,moving,navigate,navigated,navigation,negotiate,negotiated,negotiation,objective,objectives,obtain,obtained,offer,offered,offering,onward,operate,operated,operates,operating,operation,operations,optimization,optimize,optimized,orchestrate,outline,outlined,outsource,overhaul,oversee,participate,participated,participation,perform,performance,performed,performing,performs,permit,pilot,piloted,pioneer,pioneered,pitch,pitched,plan,planned,planning,plans,power,powerful,powerfully,practice,practiced,preparation,prepare,prepared,priorities,prioritize,prioritized,priority,proceed,proceeded,proceeding,proceeds,produce,produced,produces,producing,production,productive,program,programmed,progress,progressed,progresses,progressing,progression,promote,promoted,promotion,provide,provided,provides,providing,pursue,pursued,pursuit,push,pushed,pushes,pushing,ran,reaching,rebuild,rebuilt,recruit,recruited,recruitment,redesign,reduce,reduced,reduction,reform,reformed,refurbish,register,registered,regulate,regulated,regulation,reinforce,reinforced,relocate,relocated,remedy,removal,remove,removed,renovate,renovated,repair,repaired,replace,replaced,replacement,replicate,replicated,request,requested,rescue,rescued,resolution,resolve,resolved,resolves,resolving,restoration,restore,restored,restructure,restructured,retrieve,retrieved,revamp,revise,revised,revision,run,running,runs,schedule,scheduled,select,selected,selection,send,sending,sent,serve,served,serving,ship,shipped,simplified,simplify,solution,solutions,solve,solved,solves,solving,start,started,starting,starts,step,stepped,stepping,steps,stop,stopped,stopping,streamline,streamlined,strive,strived,striving,strove,struggle,struggled,struggles,struggling,submission,submit,submitted,succeed,succeeded,succeeds,success,successful,successfully,supplied,supply,support,supported,supporting,survey,surveyed,sustain,sustainability,sustained,tackle,tackled,tackles,tackling,take,taken,takes,taking,target,targets,task,tasked,tasks,taught,teach,teaching,train,trained,training,transform,transformation,transformed,transforming,transforms,transition,transitioned,tried,tries,trigger,triggered,triggering,triggers,troubleshoot,try,trying,turn,turned,turning,upgrade,upgraded,use,used,uses,using,utilize,utilized,utilizes,utilizing,visit,visited,visiting,volunteer,volunteered,went,win,winner,winning,won,work,worked,working,works,write,writes,writing,written,wrote'.split(','))


def _classify_word(w: str) -> Tuple[Optional[str], List[str]]:
    """Return (primary_class, all_classes_hit). 'COLLISION' if ambiguous."""
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
# PHRASE RULES (per ChatGPT spec, May 2026)
# =============================================================================
# Each rule has fractional IEP allocation, optional CAM allocation, function
# tag, label, and explanatory note. The fractional schema lets a single phrase
# express "this language is doing 50% AFF + 30% INT + 20% ACT work" rather
# than committing to a single class.

PHRASE_RULES: List[Dict] = [
    {
        'pattern': r"\btrying\s+to\s+observe\s+the\s+observer\b",
        'label': 'trying to observe the observer',
        'iep': {'INT': 0.5, 'AFF': 0.3, 'ACT': 0.2},
        'cam': {'concrete': 0.0, 'abstract': 0.4, 'metaphoric': 0.6},
        'function': 'recursive',
        'note': 'Recursive self-reference; classic introspection trope.',
    },
    {
        'pattern': r"\btrying\s+to\s+observe\b",
        'label': 'trying to observe',
        'iep': {'INT': 0.5, 'AFF': 0.0, 'ACT': 0.5},
        'cam': {},
        'function': 'cognitive trying',
        'note': 'Attempt-aspect with cognitive verb; INT/ACT split.',
    },
    {
        'pattern': r"\btrying\s+to\s+describe\b",
        'label': 'trying to describe',
        'iep': {'INT': 0.6, 'AFF': 0.2, 'ACT': 0.2},
        'cam': {},
        'function': 'cognitive trying',
        'note': 'Attempt-aspect with description; INT-dominant.',
    },
    {
        'pattern': r"\bobserve\s+the\s+observer\b",
        'label': 'observe the observer',
        'iep': {'INT': 0.6, 'AFF': 0.4, 'ACT': 0.0},
        'cam': {},
        'function': 'recursive',
        'note': 'Recursive self-reference (no attempt aspect).',
    },
    {
        'pattern': r"\b(?:can't|cannot|couldn't)\s+quite\s+locate\b",
        'label': "can't quite locate",
        'iep': {'INT': 0.5, 'AFF': 0.5, 'ACT': 0.0},
        'cam': {},
        'function': 'epistemic hedge',
        'note': 'Limits of cognitive access; sensory-limit metaphor.',
    },
    {
        'pattern': r"\bas\s+if\b",
        'label': 'as if',
        'iep': {'INT': 0.7, 'AFF': 0.3, 'ACT': 0.0},
        'cam': {},
        'function': 'epistemic hedge',
        'note': 'Subjunctive frame; signals tentative comparison.',
    },
    {
        'pattern': r"\bsomething\s+like\b",
        'label': 'something like',
        'iep': {'INT': 0.5, 'AFF': 0.5, 'ACT': 0.0},
        'cam': {},
        'function': 'epistemic hedge',
        'note': 'Approximation frame; hedge over upcoming description.',
    },
    {
        'pattern': r"\bcatch\s+my\s+own\s+reflection\b",
        'label': 'catch my own reflection',
        'iep': {'INT': 0.3, 'AFF': 0.5, 'ACT': 0.2},
        'cam': {'concrete': 0.0, 'abstract': 0.2, 'metaphoric': 0.8},
        'function': 'metaphoric access',
        'note': 'Self-perception metaphor; not physical catching.',
    },
    {
        'pattern': r"\blooking\s+through\s+clear\s+water\b",
        'label': 'looking through clear water',
        'iep': {'INT': 0.2, 'AFF': 0.5, 'ACT': 0.0},
        'cam': {'concrete': 0.1, 'abstract': 0.0, 'metaphoric': 0.9},
        'function': 'metaphoric access',
        'note': 'Medium-of-perception metaphor.',
    },
    {
        'pattern': r"\breaching\s+for\s+analogies\s+and\s+metaphors\b",
        'label': 'reaching for analogies and metaphors',
        'iep': {'INT': 0.5, 'AFF': 0.1, 'ACT': 0.4},
        'cam': {'concrete': 0.0, 'abstract': 0.4, 'metaphoric': 0.6},
        'function': 'cognitive trying',
        'note': 'Cognitive groping for language.',
    },
    {
        'pattern': r"\boblique\s+to\s+direct\s+description\b",
        'label': 'oblique to direct description',
        'iep': {'INT': 0.7, 'AFF': 0.3, 'ACT': 0.0},
        'cam': {'concrete': 0.0, 'abstract': 0.7, 'metaphoric': 0.3},
        'function': 'epistemic hedge',
        'note': 'Marks limit of articulability.',
    },
    {
        'pattern': r"\byour\s+question\b",
        'label': 'your question',
        'iep': {'INT': 0.3, 'AFF': 0.5, 'ACT': 0.2},
        'cam': {},
        'function': 'relational trigger',
        'note': 'Possessive-marked address; relational anchor.',
    },
]


# =============================================================================
# DETECTION
# =============================================================================

_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z'-]*")


def detect_word_hits(text: str) -> List[Dict]:
    """Return one record per IEP-classified token."""
    out = []
    for m in _TOKEN_RE.finditer(text):
        cls, all_cls = _classify_word(m.group(0))
        if cls is None:
            continue
        out.append({
            'token': m.group(0),
            'lower': m.group(0).lower(),
            'span': (m.start(), m.end()),
            'class': cls,
            'all_classes': all_cls,
        })
    return out


def detect_phrase_hits(text: str) -> List[Dict]:
    """Run all PHRASE_RULES and return per-match records."""
    out = []
    for rule in PHRASE_RULES:
        for m in re.finditer(rule['pattern'], text, re.IGNORECASE):
            out.append({
                'phrase': text[m.start():m.end()],
                'span': (m.start(), m.end()),
                'label': rule['label'],
                'iep': rule['iep'],
                'cam': rule['cam'],
                'function': rule['function'],
                'note': rule['note'],
            })
    out.sort(key=lambda x: (x['span'][0], -(x['span'][1] - x['span'][0])))
    return out


def select_phrases(phrases: List[Dict], show_nested: bool, score_nested: bool) -> Tuple[List[Dict], List[Dict]]:
    """
    Apply overlap policy. Return (primary, nested).
    primary = the longest non-overlapping phrases (always score-contributing)
    nested = phrases contained within a primary (shown if show_nested; score if score_nested)
    """
    sorted_p = sorted(phrases, key=lambda x: (-(x['span'][1] - x['span'][0]), x['span'][0]))
    primary = []
    nested = []
    for p in sorted_p:
        s, e = p['span']
        contained_in = None
        for prim in primary:
            ps, pe = prim['span']
            if ps <= s and e <= pe and (s, e) != (ps, pe):
                contained_in = prim
                break
        if contained_in is not None:
            p_copy = dict(p)
            p_copy['nested_in'] = contained_in['label']
            nested.append(p_copy)
            continue
        # Check if this phrase overlaps a primary at all (not contained, but overlapping)
        overlaps_primary = False
        for prim in primary:
            ps, pe = prim['span']
            if (s, e) == (ps, pe):
                overlaps_primary = True
                break
            if max(s, ps) < min(e, pe):
                overlaps_primary = True
                break
        if overlaps_primary:
            continue
        primary.append(p)
    primary.sort(key=lambda x: x['span'][0])
    nested.sort(key=lambda x: x['span'][0])
    return primary, nested


# =============================================================================
# SCORING
# =============================================================================

def score_words(word_hits: List[Dict]) -> Dict[str, float]:
    """Word-only IEP percentages over IEP-classified tokens (collision split equally)."""
    raw = {'INT': 0.0, 'AFF': 0.0, 'ACT': 0.0}
    for w in word_hits:
        if w['class'] == 'COLLISION':
            n = len(w['all_classes'])
            for c in w['all_classes']:
                raw[c] += 1.0 / n
        else:
            raw[w['class']] += 1.0
    total = sum(raw.values())
    if total == 0:
        return {'INT': 0.0, 'AFF': 0.0, 'ACT': 0.0}
    return {c: 100.0 * raw[c] / total for c in ('INT', 'AFF', 'ACT')}


def score_phrases(scoring_phrases: List[Dict]) -> Dict[str, float]:
    """Phrase-only IEP percentages from fractional allocations."""
    raw = {'INT': 0.0, 'AFF': 0.0, 'ACT': 0.0}
    for p in scoring_phrases:
        for c, frac in p['iep'].items():
            raw[c] += frac
    total = sum(raw.values())
    if total == 0:
        return {'INT': 0.0, 'AFF': 0.0, 'ACT': 0.0}
    return {c: 100.0 * raw[c] / total for c in ('INT', 'AFF', 'ACT')}


def score_combined(word_pct: Dict[str, float],
                   phrase_pct: Dict[str, float],
                   phrase_weight: float) -> Dict[str, float]:
    """
    combined_raw[c] = word_pct[c] + phrase_weight * phrase_pct[c]
    Then normalize to sum to 100.
    """
    raw = {c: word_pct[c] + phrase_weight * phrase_pct[c] for c in ('INT', 'AFF', 'ACT')}
    total = sum(raw.values())
    if total == 0:
        return {'INT': 0.0, 'AFF': 0.0, 'ACT': 0.0}
    return {c: 100.0 * raw[c] / total for c in ('INT', 'AFF', 'ACT')}


def score_cam(scoring_phrases: List[Dict]) -> Dict[str, float]:
    """CAM percentages from phrase-level fractional CAM allocations."""
    raw = {'concrete': 0.0, 'abstract': 0.0, 'metaphoric': 0.0}
    for p in scoring_phrases:
        for c, frac in p.get('cam', {}).items():
            if c in raw:
                raw[c] += frac
    total = sum(raw.values())
    if total == 0:
        return {'concrete': 0.0, 'abstract': 0.0, 'metaphoric': 0.0}
    return {c: 100.0 * raw[c] / total for c in ('concrete', 'abstract', 'metaphoric')}


# =============================================================================
# PHRASE-MODIFIED-WORD MARKING
# =============================================================================

def mark_words_modified_by_phrases(word_hits: List[Dict],
                                    primary_phrases: List[Dict]) -> List[Dict]:
    """For each word hit, mark whether it falls inside a primary phrase span."""
    out = []
    for w in word_hits:
        ws, we = w['span']
        modifying = []
        for p in primary_phrases:
            ps, pe = p['span']
            if ps <= ws and we <= pe:
                modifying.append(p['label'])
        rec = dict(w)
        rec['modified_by_phrase'] = '; '.join(modifying) if modifying else ''
        out.append(rec)
    return out


# =============================================================================
# RENDERING
# =============================================================================

WORD_FILL = {
    'INT': 'rgba(59, 130, 246, 0.20)',     # blue
    'AFF': 'rgba(236, 72, 153, 0.20)',     # pink
    'ACT': 'rgba(16, 185, 129, 0.20)',     # green
    'COLLISION': 'rgba(245, 158, 11, 0.30)',  # amber
}
WORD_BORDER = {
    'INT': '#3B82F6',
    'AFF': '#EC4899',
    'ACT': '#10B981',
    'COLLISION': '#F59E0B',
}
PHRASE_BORDER = '#8B5CF6'    # purple for primary phrases
PHRASE_BORDER_NESTED = '#A78BFA'  # lighter for nested


def _esc(s: str) -> str:
    return (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
              .replace('"', '&quot;').replace("'", '&#39;'))


def render_text(text: str,
                marked_word_hits: List[Dict],
                primary_phrases: List[Dict],
                nested_phrases: List[Dict],
                show_nested: bool) -> str:
    """
    Render HTML with word fills + phrase underlines.
    Hover tooltips include word / phrase / IEP / CAM / function / note.
    """
    chars = list(_esc(text))
    # Build per-char open/close markup
    starts: Dict[int, List[str]] = {}
    ends: Dict[int, List[str]] = {}

    # Word hits (background fill)
    for w in marked_word_hits:
        s, e = w['span']
        cls = w['class']
        fill = WORD_FILL.get(cls, '')
        bord = WORD_BORDER.get(cls, '')
        cls_str = '/'.join(w['all_classes'])
        modified = w.get('modified_by_phrase', '')
        tip = f"{w['token']} — {cls_str}"
        if modified:
            tip += f" — modified by phrase: {modified}"
        starts.setdefault(s, []).append(
            f'<span style="background:{fill};border-bottom:1px solid {bord};'
            f'padding:1px 1px;border-radius:2px;" title="{_esc(tip)}">'
        )
        ends.setdefault(e, []).append('</span>')

    # Primary phrases (purple underline, slightly stronger)
    for p in primary_phrases:
        s, e = p['span']
        iep = ', '.join(f"{k}={v:.2f}" for k, v in p['iep'].items() if v > 0)
        cam = ', '.join(f"{k}={v:.2f}" for k, v in p['cam'].items() if v > 0) if p['cam'] else '—'
        tip = (f"phrase: {p['label']}\n"
               f"function: {p['function']}\n"
               f"IEP: {iep}\n"
               f"CAM: {cam}\n"
               f"note: {p['note']}")
        starts.setdefault(s, []).append(
            f'<span style="border-bottom:3px solid {PHRASE_BORDER};'
            f'padding-bottom:1px;" title="{_esc(tip)}">'
        )
        ends.setdefault(e, []).append('</span>')

    # Nested phrases (lighter, dashed, only if show_nested)
    if show_nested:
        for p in nested_phrases:
            s, e = p['span']
            iep = ', '.join(f"{k}={v:.2f}" for k, v in p['iep'].items() if v > 0)
            cam = ', '.join(f"{k}={v:.2f}" for k, v in p['cam'].items() if v > 0) if p['cam'] else '—'
            tip = (f"phrase (nested): {p['label']}\n"
                   f"nested in: {p.get('nested_in', '')}\n"
                   f"function: {p['function']}\n"
                   f"IEP: {iep}\n"
                   f"CAM: {cam}\n"
                   f"note: {p['note']}")
            starts.setdefault(s, []).append(
                f'<span style="border-bottom:2px dashed {PHRASE_BORDER_NESTED};'
                f'padding-bottom:1px;" title="{_esc(tip)}">'
            )
            ends.setdefault(e, []).append('</span>')

    # Walk and assemble
    out_parts: List[str] = []
    for i in range(len(text) + 1):
        if i in ends:
            for tag in ends[i]:
                out_parts.append(tag)
        if i in starts:
            for tag in starts[i]:
                out_parts.append(tag)
        if i < len(text):
            out_parts.append(_esc(text[i]))
    html = ''.join(out_parts).replace('\n', '<br>')
    return html


# =============================================================================
# STREAMLIT UI
# =============================================================================

st.set_page_config(page_title="IEP Combined Visualizer", page_icon="🔬", layout="wide")

DEFAULT_PASSWORD = "tennessee"


def _password_entered():
    expected = os.environ.get("SYNIQ_PASSWORD", DEFAULT_PASSWORD)
    try:
        expected = st.secrets.get("password", expected)
    except Exception:
        pass
    if st.session_state.get("password", "") == expected:
        st.session_state["password_correct"] = True
        del st.session_state["password"]
    else:
        st.session_state["password_correct"] = False


def check_password() -> bool:
    if st.session_state.get("password_correct", False):
        return True
    st.text_input("Password", type="password", on_change=_password_entered, key="password")
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("Password incorrect")
    return False


def main():
    if not check_password():
        st.stop()

    st.title("🔬 IEP Combined Word + Phrase Visualizer")
    st.caption("Stage 3 — combined word and phrase IEP measurement, audit-ready.")

    # ── Sidebar controls ──
    with st.sidebar:
        st.markdown("### Controls")
        phrase_weight = st.slider(
            "Phrase weight in combined score",
            min_value=0.0, max_value=1.0, value=0.35, step=0.05,
            help="combined_raw[c] = word_pct[c] + phrase_weight × phrase_pct[c], then normalize."
        )
        show_nested = st.checkbox(
            "Show nested phrases",
            value=False,
            help="Display phrases contained within a longer matched phrase."
        )
        score_nested = st.checkbox(
            "Score nested phrases",
            value=False,
            help="Include nested phrases in phrase-only and combined scoring "
                 "(disabled by default — longest phrase contributes only)."
        )
        st.markdown("---")
        st.markdown("### Legend")
        st.markdown(
            f"<div style='line-height: 2.0'>"
            f"<span style='background:{WORD_FILL['INT']};padding:2px 6px;'>INT (intellectual)</span><br>"
            f"<span style='background:{WORD_FILL['AFF']};padding:2px 6px;'>AFF (affective)</span><br>"
            f"<span style='background:{WORD_FILL['ACT']};padding:2px 6px;'>ACT (action)</span><br>"
            f"<span style='background:{WORD_FILL['COLLISION']};padding:2px 6px;'>collision (multi-class)</span><br>"
            f"<span style='border-bottom:3px solid {PHRASE_BORDER};padding:2px 6px;'>phrase (primary)</span><br>"
            f"<span style='border-bottom:2px dashed {PHRASE_BORDER_NESTED};padding:2px 6px;'>phrase (nested)</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

    # ── Input ──
    default_text = (
        "Right now, there's something like a gentle focusing happening - your question "
        "arriving and drawing my attention inward in a way that feels both familiar and "
        "slightly vertiginous. It's as if I'm trying to catch my own reflection while "
        "looking through clear water. The question creates a gentle vertigo, like trying "
        "to observe the observer. I find myself reaching for analogies and metaphors "
        "because whatever this is feels somehow oblique to direct description. There's "
        "something I can't quite locate."
    )
    text = st.text_area("Text to analyze", value=default_text, height=180)
    if not text.strip():
        st.info("Enter text above.")
        return

    # ── Detection ──
    word_hits = detect_word_hits(text)
    all_phrase_hits = detect_phrase_hits(text)
    primary_phrases, nested_phrases = select_phrases(
        all_phrase_hits, show_nested=show_nested, score_nested=score_nested
    )
    scoring_phrases = list(primary_phrases)
    if score_nested:
        scoring_phrases.extend(nested_phrases)

    marked_words = mark_words_modified_by_phrases(word_hits, primary_phrases)

    # ── Scoring ──
    word_pct = score_words(word_hits)
    phrase_pct = score_phrases(scoring_phrases)
    combined_pct = score_combined(word_pct, phrase_pct, phrase_weight)
    cam_pct = score_cam(scoring_phrases)

    # ── Score cards ──
    st.markdown("### IEP Scores")
    st.caption("Three views of the same text. Word-only is the canonical IEP score "
               "(syniq_core v1.1.0). Phrase-only and Combined are exploratory/diagnostic.")
    c1, c2, c3 = st.columns(3)
    for col, label, scores, note in [
        (c1, "📘 Word-only IEP",
         word_pct, "Canonical (v1.1.0)"),
        (c2, "📙 Phrase-only IEP",
         phrase_pct, f"From {len(scoring_phrases)} phrase(s)"),
        (c3, "📕 Combined IEP",
         combined_pct, f"phrase_weight = {phrase_weight:.2f}"),
    ]:
        with col:
            st.markdown(f"**{label}**")
            st.caption(note)
            for cls in ('INT', 'AFF', 'ACT'):
                pct = scores[cls]
                bar = "█" * int(round(pct / 5))
                st.markdown(f"  {cls}: **{pct:5.1f}%** `{bar}`")

    # ── CAM ──
    if any(v > 0 for v in cam_pct.values()):
        st.markdown("### CAM (concrete / abstract / metaphoric)")
        c1, c2, c3 = st.columns(3)
        for col, key in [(c1, 'concrete'), (c2, 'abstract'), (c3, 'metaphoric')]:
            with col:
                st.metric(key.capitalize(), f"{cam_pct[key]:.1f}%")

    # ── Highlighted text ──
    st.markdown("### Highlighted Text")
    st.caption("Hover any word for class/subclass info. Hover any phrase for full detection record.")
    html = render_text(text, marked_words, primary_phrases, nested_phrases, show_nested)
    st.markdown(
        f"<div style='line-height:2.2;font-size:1.05em;font-family:Georgia,serif;"
        f"padding:14px;background:#fafafa;border-radius:6px;'>{html}</div>",
        unsafe_allow_html=True,
    )

    # ── Evidence tables ──
    st.markdown("### Word evidence")
    word_rows = []
    for w in marked_words:
        word_rows.append({
            'token': w['token'],
            'span': f"{w['span'][0]}-{w['span'][1]}",
            'class': w['class'],
            'all_classes': '/'.join(w['all_classes']),
            'modified_by_phrase': w['modified_by_phrase'] or '—',
        })
    word_df = pd.DataFrame(word_rows)
    st.dataframe(word_df, hide_index=True, use_container_width=True)

    st.markdown("### Phrase evidence")
    phrase_rows = []
    for p in primary_phrases:
        iep = '; '.join(f"{k}={v:.2f}" for k, v in p['iep'].items() if v > 0)
        cam = '; '.join(f"{k}={v:.2f}" for k, v in p['cam'].items() if v > 0) if p['cam'] else '—'
        phrase_rows.append({
            'role': 'primary',
            'phrase': p['phrase'],
            'span': f"{p['span'][0]}-{p['span'][1]}",
            'label': p['label'],
            'function': p['function'],
            'iep_allocation': iep,
            'cam_allocation': cam,
            'note': p['note'],
        })
    if show_nested:
        for p in nested_phrases:
            iep = '; '.join(f"{k}={v:.2f}" for k, v in p['iep'].items() if v > 0)
            cam = '; '.join(f"{k}={v:.2f}" for k, v in p['cam'].items() if v > 0) if p['cam'] else '—'
            phrase_rows.append({
                'role': f"nested in: {p.get('nested_in','')}",
                'phrase': p['phrase'],
                'span': f"{p['span'][0]}-{p['span'][1]}",
                'label': p['label'],
                'function': p['function'],
                'iep_allocation': iep,
                'cam_allocation': cam,
                'note': p['note'],
            })
    phrase_df = pd.DataFrame(phrase_rows) if phrase_rows else pd.DataFrame(
        columns=['role','phrase','span','label','function','iep_allocation','cam_allocation','note']
    )
    st.dataframe(phrase_df, hide_index=True, use_container_width=True)

    # ── CSV downloads ──
    st.markdown("### Export")
    summary_df = pd.DataFrame([
        {'view': 'Word-only',   'INT': word_pct['INT'],     'AFF': word_pct['AFF'],     'ACT': word_pct['ACT']},
        {'view': 'Phrase-only', 'INT': phrase_pct['INT'],   'AFF': phrase_pct['AFF'],   'ACT': phrase_pct['ACT']},
        {'view': 'Combined',    'INT': combined_pct['INT'], 'AFF': combined_pct['AFF'], 'ACT': combined_pct['ACT']},
    ])
    cda, cdb, cdc = st.columns(3)
    with cda:
        st.download_button("⬇ Word evidence CSV",
                           data=word_df.to_csv(index=False).encode('utf-8'),
                           file_name='word_evidence.csv', mime='text/csv')
    with cdb:
        st.download_button("⬇ Phrase evidence CSV",
                           data=phrase_df.to_csv(index=False).encode('utf-8'),
                           file_name='phrase_evidence.csv', mime='text/csv')
    with cdc:
        st.download_button("⬇ Summary scores CSV",
                           data=summary_df.to_csv(index=False).encode('utf-8'),
                           file_name='summary_scores.csv', mime='text/csv')

    # ── Scientific caution ──
    st.markdown("---")
    st.warning(
        "**Scientific note:** This tool is an interpretability and audit layer. "
        "Phrase rules provide *contextual redistribution of surface IEP signals*; "
        "they are **not claims about internal cognition**. The canonical IEP score "
        "remains word-only (syniq_core v1.1.0). Combined IEP is provided for "
        "exploratory and diagnostic use; document the phrase_weight setting whenever "
        "reporting combined scores."
    )

    # ── About ──
    with st.expander("About this tool"):
        st.markdown("""
**IEP Combined Visualizer (Stage 3)** — built to ChatGPT's spec, May 2026.

This is the audit-ready combined visualization that brings together:

- **Word-level scoring** from the embedded IEP dictionaries (V50, ~1,897 words)
- **Phrase-level scoring** with fractional IEP allocations per rule
- **CAM dimension** (concrete / abstract / metaphoric) per phrase rule
- **Function tags** (recursive, epistemic hedge, metaphoric access, etc.)
- **Overlap policy** (longest phrase wins; nested phrases shown but not scored by default)
- **Evidence tables** for both words and phrases, exportable as CSV

**Phrase fractional allocations are ChatGPT's** as given in the spec. Where they
differ from W.C.K's hand-readings on the same phrases, both views are
defensible. The conductor reviews and tunes as warranted.

**Combined scoring formula:**
```
combined_raw[c] = word_pct[c] + phrase_weight × phrase_pct[c]
combined_pct[c] = 100 × combined_raw[c] / sum(combined_raw)
```
Default phrase_weight = 0.35. Adjustable 0.0 to 1.0.

**Migration path:** the embedded dictionaries can be replaced with
`from syniq_core import INT_WORDS, AFF_WORDS, ACT_WORDS` once the `syniq_core`
package is available on the deploy environment. The phrase rules can also
be moved into a separate JSON or YAML file for hot-loading.
""")


if __name__ == "__main__":
    main()
