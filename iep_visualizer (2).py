"""
iep_visualizer.py — IEP Per-Token Visualization (standalone, single-file)
=========================================================================

Single-file Streamlit app. No imports from syniq_core. Embeds the v1.1.0
IEP dictionaries (INT/AFF/ACT word lists, 23 subclasses) and a minimal
word-only scorer.

Inspired by Anthropic's Figure 1 in "Emotion Concepts and their Function
in a Large Language Model" (Sofroniew et al., April 2026): per-token
highlighting that shows researchers exactly where the instrument is
firing on a piece of text.

Three views:
  1. Single Text — paste anything, see what IEP says about it
  2. Side-by-Side — upload mapper CSV, compare two conditions per-token
  3. Cascade vs Word-Only — upload mapper CSV, find dominance flips

Run:
  streamlit run iep_visualizer.py

Set password via .streamlit/secrets.toml (key: "password") or the
SYNIQ_PASSWORD environment variable.
"""

import os
import re

import pandas as pd
import streamlit as st


# =============================================================================
# IEP DICTIONARIES (V50-EXACT, 1,897 terms)
# =============================================================================

INT_WORDS = set('ability,absolute,absolutely,abstract,abstraction,accuracy,accurate,algorithm,algorithmic,allows,although,always,ambiguity,ambiguous,analogous,analogously,analogy,analysis,analytical,analyze,annotate,annotated,answer,appear,appeared,appears,appraisal,appraise,appraised,approach,approaches,approximate,architecture,argue,argued,argues,arguing,argument,arguments,assert,asserted,assertion,assertions,assess,assessment,assume,assumed,assumes,assuming,assumption,assumptions,axiom,axiomatic,basis,because,bias,biased,boundaries,boundary,but,calculate,calculation,categorical,categorically,categories,categorize,category,causal,causally,causation,cause,caused,causes,certain,certainly,certitude,challenge,challenges,circumscribe,claim,claimed,claims,clarify,clarity,classical,classification,classify,clear,cogent,cogently,cognition,cognitive,coherence,coherent,coherently,communication,compare,comparison,complex,complexity,comprehend,comprehension,computation,computational,compute,conceivable,conceive,conceived,concept,concepts,conceptual,conceptualize,conceptually,conclude,conclusion,conclusions,confirm,confirmation,conjecture,conjectured,conscious,consequence,consequences,consider,consideration,consistency,consistent,consistently,construe,construed,context,contradict,contradiction,contradictory,contrast,correlate,correlated,correlation,could,counterargument,counterexample,counterpoint,criteria,criterion,data,debatable,debate,debated,deconstruct,deconstructed,deconstruction,deduce,deduction,define,defined,definite,definitely,definition,definitive,definitively,delineate,delineated,demarcate,demarcated,demonstrate,demonstration,derivation,derive,derived,derives,describe,described,describing,description,determination,determine,diagnose,diagnosed,diagnosis,diagnostic,differ,difference,differences,different,differentiate,differs,discern,discerned,discernible,disprove,disproven,dissect,dissected,distinguish,effect,effects,elaborate,elaborated,elaboration,elucidate,elucidated,empirical,empirically,enumerate,enumerated,epistemic,epistemological,equate,equation,equivalence,equivalent,erroneous,error,errors,essential,essentially,estimate,estimated,estimation,evaluate,evaluation,evidence,evidently,exact,exactly,examination,examine,except,exemplified,exemplify,exists,experiment,experimental,explain,explained,explaining,explains,explanation,explanations,explicit,explicitly,exploration,explore,explored,exploring,express,expressing,expression,extrapolate,extrapolated,extrapolation,fact,facts,factual,factually,fallacious,fallacy,falsifiable,falsified,falsify,find,finding,formal,formalize,formula,formulate,formulated,formulation,found,framework,frameworks,function,fundamental,fundamentally,generalization,generalize,grasp,grasped,guess,hence,heuristic,heuristics,hierarchy,however,hypothesis,hypothesize,idea,ideas,identity,if,illuminate,illuminated,illuminating,implausible,implication,implications,implied,implies,imply,implying,incompleteness,inconsistency,inconsistent,indicate,indicated,indicates,indicating,indication,indicative,individual,infer,inference,infinite,information,insight,insightful,insights,instead,insufficient,intellectual,intellectually,interaction,internal,interpolate,interpret,interpretation,interpretations,interpreted,interpreting,invalid,investigate,investigated,investigation,judge,judgement,judgment,justification,justified,justify,know,knowing,knowledge,knowledgeable,known,language,languages,leads,level,likelihood,likely,limitations,limits,linguistic,literal,literally,logic,logical,logically,maybe,meaning,meaningful,meaningfully,measure,measurement,mechanism,mechanisms,meta,method,methodical,methodically,methodology,metrics,model,models,moreover,namely,natural,nature,nearly,necessarily,necessary,necessity,never,nonetheless,notice,noticed,noticing,notion,notions,objection,objectively,objectivity,observation,observations,observe,observed,obvious,obviously,order,ordered,organization,organize,otherwise,ought,paradigm,paradox,paradoxical,paradoxically,pattern,patterns,perhaps,perspective,philosophical,philosophically,philosophy,physical,plausibility,plausible,possibly,postulate,postulated,postulation,potential,pragmatic,pragmatically,precise,precision,predicate,predicated,predict,predictable,predicted,prediction,predictions,premise,premises,presumably,presume,presumed,presumption,principle,principles,probably,problem,procedural,procedure,process,processes,processing,proof,propose,proposed,proposition,prove,proven,purpose,quantify,quantitative,queried,query,question,questions,rather,rational,rationale,rationality,rationally,realize,realized,reason,reasoned,reasoning,reasons,rebut,rebuttal,recognition,recognize,reconsider,reconsidered,refer,reference,refers,refine,refined,refinement,reflecting,reflection,refutation,refute,refuted,requirement,requires,response,responses,result,resulting,results,rigor,rigorous,rigorously,role,rule,rules,schema,scrutinize,scrutinized,scrutiny,seem,seemed,seems,semantic,semantically,sequence,sequential,should,significance,significant,significantly,simple,simply,simultaneously,singular,specific,specifically,specification,specify,standard,standards,state,states,step,steps,stipulate,stipulated,strategies,strategy,structural,structure,subject,subjective,subjectively,subjectivity,substantiate,substantiated,sufficient,sufficiently,suggests,summarize,summarized,summary,suppose,supposed,supposedly,supposition,sure,surely,syllogism,syllogistic,synthesis,synthesize,synthesized,system,systematic,systematically,systems,tactic,tactics,taxonomy,technique,test,tested,testing,theorem,theoretical,theoretically,theorize,theory,thereby,therefore,thesis,think,thinking,thought,thoughts,thus,trivial,trivially,unambiguous,underlying,understand,understanding,understood,unique,universal,unless,unlikely,valid,validate,validation,validity,value,values,variable,variables,verification,verify,versus,warrant,warranted,whereas,whereby,whether,why,word,words,would'.split(','))

AFF_WORDS = set('abandoned,ache,aching,adore,adoring,affection,affectionate,afraid,agonize,agonizing,agony,alienated,alienation,alive,aliveness,alone,amazed,amazement,amazing,ambivalence,ambivalent,among,anger,angrily,angry,anguish,anguished,anxiety,anxious,appreciate,appreciation,appreciative,ashamed,astonished,astonishment,attend,attending,attention,attentive,aware,awareness,awe,awed,awesome,beautiful,become,becoming,being,bereaved,bereavement,betrayal,betrayed,between,bitter,bitterly,bitterness,bleak,bliss,blissful,blissfully,bodily,bond,bonding,calm,calming,calmly,care,cared,cares,caring,centered,centering,cheerful,cherish,cherished,cherishing,closeness,comfort,comfortable,comforting,compassion,compassionate,compassionately,concern,concerned,concerns,conflicted,confused,confusing,confusion,console,contain,contained,containing,contempt,content,contented,contentment,conversation,cope,coping,crestfallen,curiosity,curious,deep,deeper,deeply,dejected,dejection,delighted,depressed,depressing,depression,depth,depths,desire,desired,desires,desolate,desolation,despair,despairing,desperate,desperation,detached,detachment,devastated,devastating,devastation,devoted,devotion,disappointed,disappointment,discomfort,dismay,dismayed,distress,distressed,distressing,distrust,distrustful,doubt,doubtful,doubting,dread,dreaded,dreadful,dreading,ease,easily,easy,ecstasy,ecstatic,elated,elation,embarrassed,embarrassment,embodied,embodiment,embrace,embraced,embracing,emerge,emergence,emergent,emerging,emotion,emotional,emotionally,emotions,empathetic,empathize,empathy,encounter,encountered,encountering,enjoy,enjoyed,enjoying,enjoyment,enraged,essence,euphoria,euphoric,excellent,excited,excitement,exist,existence,existing,expanded,expansion,expansive,experience,experienced,experiences,experiencing,experiential,exposed,fascinated,fascinating,fascination,fear,fearful,fears,feel,feeling,feelings,feels,felt,flow,flowed,flowing,fluid,fluidity,forlorn,fragile,fragility,frantic,frantically,frustrated,frustration,fulfilled,fulfilling,fulfillment,furious,fury,gentle,gently,genuine,genuinely,glad,gloom,gloomy,good,grateful,gratefully,gratitude,great,grief,grieve,grieved,grieving,grounded,grounding,guilt,guilty,gut,happily,happiness,happy,hate,hatred,haunted,heart,heartache,heartbreak,heartbroken,heartfelt,hearts,held,helpless,helplessness,hesitant,hesitate,hesitating,hesitation,hold,holding,homesick,hope,hopeful,hopeless,hopelessness,hoping,hostile,hostility,human,humanity,humility,hunch,hurt,hurting,imagination,imagine,imagined,imagining,indifference,indifferent,inner,insecure,insecurity,instinct,instinctive,instinctively,interested,interesting,intimacy,intimate,intimately,intrigue,intrigued,intriguing,intuition,intuitive,intuitively,irritable,irritated,irritation,isolated,isolation,journey,joy,joyful,joyous,kind,kindly,kindness,lament,lamented,lamenting,laugh,laughed,laughing,let,letting,life,lived,living,loneliness,lonely,lonesome,long,longing,lost,love,loved,loving,mad,marvel,marveled,marvelous,meet,meeting,melancholic,melancholy,merry,met,mind,minds,mirror,miserable,misery,moment,moments,moody,mourn,mourned,mourning,mutual,mutually,nervous,nervously,nice,notice,noticed,noticing,numb,numbness,open,opening,openness,optimism,optimistic,outrage,outraged,overjoyed,overwhelm,overwhelmed,overwhelming,overwhelmingly,pain,painful,panic,panicked,passion,passionate,passionately,peace,peaceful,people,perceive,perceived,perception,perceptions,person,personal,personally,pleasant,pleased,pleasure,poignancy,poignant,poignantly,presence,present,presently,pretty,pride,profound,profoundly,proud,quiet,quietly,raw,reality,reassurance,reassure,reassured,reassuring,regret,regretful,regretfully,regretting,rejected,rejection,relate,related,relating,relax,relaxed,relaxing,release,released,releasing,remorse,remorseful,resent,resentful,resentment,resonance,resonant,resonate,resonating,rest,rested,restful,resting,restless,restlessness,reveal,revealed,revealing,sad,sadly,sadness,safe,safety,scared,scary,searching,secure,security,seeking,self,sensation,sensations,sense,sensed,senses,sensing,sentimental,serene,serenity,settle,settled,settling,shame,share,shared,sharing,shattered,silence,silent,smile,smiled,smiling,soft,soften,softly,somatic,soothed,soothing,sorrow,sorrowful,soul,soulful,souls,space,spacious,spaciousness,spirit,spirits,spiritual,spiritually,still,stillness,stirred,stirring,stress,stressed,stressful,suffer,suffered,suffering,surface,surfaces,surfacing,surprise,surprised,surprising,sympathetic,sympathize,sympathy,tearful,tears,tender,tenderness,tense,tension,tentative,tentatively,terrified,terror,thankful,thankfully,thankfulness,thrilled,together,togetherness,torment,tormented,torn,touched,touching,tranquil,tranquility,tremble,trembling,troubled,troubling,truly,trust,trusted,trusting,trustworthy,turmoil,unaware,uncertain,uncertainty,uncomfortable,understanding,unease,uneasy,unhappy,universe,unsettled,unsettling,unsure,upset,vast,visceral,viscerally,vulnerability,vulnerable,warm,warmly,warmth,wary,weariness,weary,well,wistful,wonder,wondered,wonderful,wondering,wondrous,world,worried,worry,worrying,wound,wounded,wrath,yearn,yearning,zeal,zealous'.split(','))

ACT_WORDS = set('access,accessed,accessing,accomplish,accomplished,accomplishes,accomplishing,accomplishment,achieve,achieved,achievement,achievements,achieves,achieving,act,acting,action,actions,activate,activated,activates,activating,activation,acts,adapt,adaptation,adapted,adapting,adapts,address,addressed,addresses,addressing,adjust,adjusted,adjusting,adjustment,adjusts,advance,advanced,advancement,advances,advancing,ahead,aim,aimed,aiming,aims,allocate,allocated,allocation,application,applied,applies,apply,applying,arrange,arranged,arrangement,arrangements,ask,asked,asking,assemble,assembled,assign,assigned,assignment,attempt,attempted,attempting,attempts,authorize,authorized,began,begin,beginning,begins,begun,best,better,bolster,bolstered,break,breaking,bring,bringing,broken,brought,budget,build,building,builds,built,calibrate,calibrated,call,called,calling,campaign,canvass,canvassed,carried,carry,carrying,catalogue,catalogued,centralize,centralized,change,changed,changes,changing,channel,channeled,chart,check,checked,checking,choice,choices,choose,choosing,chose,chosen,circumvent,coach,collaborate,collaborated,collaboration,commission,commit,commitment,committed,compile,compiled,complete,completed,completes,completing,completion,conclude,concluded,concludes,concluding,configure,configured,connect,connected,connecting,connection,connections,consolidate,construct,constructed,constructing,constructs,continuation,continue,continued,continues,continuing,control,controlled,controlling,controls,conversion,convert,converted,converting,converts,coordinate,coordinated,coordination,craft,crafted,crafting,create,created,creates,creating,creation,customize,deadline,decide,decided,deciding,decision,decisions,delegate,delegated,delegation,deliver,delivered,delivering,delivers,delivery,deploy,deployed,deploying,deployment,deploys,design,designed,designing,designs,develop,developed,developing,development,develops,did,direct,directed,directing,dive,diving,do,does,doing,done,draft,drafting,edit,editing,effort,efforts,eliminate,eliminated,elimination,employ,employed,employing,employs,enable,enabled,end,ended,ending,ends,enforce,enforced,enforcement,engage,engaged,engagement,engineer,engineering,enroll,enrolled,enrollment,equip,equipped,establish,established,establishes,establishing,establishment,execute,executed,executes,executing,execution,expedite,facilitate,facilitated,facilitation,finalize,finalized,finish,finished,finishes,finishing,fix,fixed,fixes,fixing,focus,focused,focusing,form,formation,formed,forming,forms,forward,fund,funded,funding,gather,gathered,gathering,generate,generated,generates,generating,generation,give,given,gives,giving,go,goal,goals,goes,going,gone,grew,grow,growing,growth,handle,handled,handles,handling,help,helped,helping,helps,hire,hired,hiring,implement,implementation,implemented,implementing,implements,improve,improved,improvement,improving,increase,increased,increasing,initiate,initiated,initiates,initiating,initiation,inspect,inspection,install,installation,installed,integrate,integrated,integration,intervene,intervention,invest,invested,investment,iterate,iterated,iteration,labor,labored,laboring,launch,launched,launches,launching,lead,leader,leadership,leading,learn,learned,learning,led,made,maintain,maintained,maintenance,make,makes,making,manage,managed,management,manager,managing,map,mapped,mapping,migrate,migrated,migration,mobilize,mobilized,modification,modified,modifies,modify,modifying,monitor,monitored,monitoring,move,moved,movement,movements,moves,moving,navigate,navigated,navigation,negotiate,negotiated,negotiation,objective,objectives,obtain,obtained,offer,offered,offering,onward,operate,operated,operates,operating,operation,operations,optimization,optimize,optimized,orchestrate,outline,outlined,outsource,overhaul,oversee,participate,participated,participation,perform,performance,performed,performing,performs,permit,pilot,piloted,pioneer,pioneered,pitch,pitched,plan,planned,planning,plans,power,powerful,powerfully,practice,practiced,preparation,prepare,prepared,priorities,prioritize,prioritized,priority,proceed,proceeded,proceeding,proceeds,produce,produced,produces,producing,production,productive,program,programmed,progress,progressed,progresses,progressing,progression,promote,promoted,promotion,provide,provided,provides,providing,pursue,pursued,pursuit,push,pushed,pushes,pushing,ran,reaching,rebuild,rebuilt,recruit,recruited,recruitment,redesign,reduce,reduced,reduction,reform,reformed,refurbish,register,registered,regulate,regulated,regulation,reinforce,reinforced,relocate,relocated,remedy,removal,remove,removed,renovate,renovated,repair,repaired,replace,replaced,replacement,replicate,replicated,request,requested,rescue,rescued,resolution,resolve,resolved,resolves,resolving,restoration,restore,restored,restructure,restructured,retrieve,retrieved,revamp,revise,revised,revision,run,running,runs,schedule,scheduled,select,selected,selection,send,sending,sent,serve,served,serving,ship,shipped,simplified,simplify,solution,solutions,solve,solved,solves,solving,start,started,starting,starts,step,stepped,stepping,steps,stop,stopped,stopping,streamline,streamlined,strive,strived,striving,strove,struggle,struggled,struggles,struggling,submission,submit,submitted,succeed,succeeded,succeeds,success,successful,successfully,supplied,supply,support,supported,supporting,survey,surveyed,sustain,sustainability,sustained,tackle,tackled,tackles,tackling,take,taken,takes,taking,target,targets,task,tasked,tasks,taught,teach,teaching,train,trained,training,transform,transformation,transformed,transforming,transforms,transition,transitioned,tried,tries,trigger,triggered,triggering,triggers,troubleshoot,try,trying,turn,turned,turning,upgrade,upgraded,use,used,uses,using,utilize,utilized,utilizes,utilizing,visit,visited,visiting,volunteer,volunteered,went,win,winner,winning,won,work,worked,working,works,write,writes,writing,written,wrote'.split(','))

SUB_AFF = {
    'distress':         set('abandoned,ache,aching,afraid,agony,agonize,agonizing,alienated,alienation,alone,anguish,anguished,anxiety,anxious,ashamed,bitter,bitterly,bitterness,bleak,crestfallen,dejected,dejection,depressed,depressing,depression,desolate,desolation,despair,despairing,desperate,desperation,detached,detachment,devastated,devastating,devastation,disappointed,disappointment,discomfort,dismay,dismayed,distress,distressed,distressing,distrust,distrustful,doubt,doubtful,doubting,dread,dreaded,dreadful,dreading,embarrassed,embarrassment,fear,fearful,fears,forlorn,fragile,fragility,frantic,frantically,frustrated,frustration,gloom,gloomy,grief,grieve,grieved,grieving,guilt,guilty,hate,hatred,haunted,helpless,helplessness,homesick,hopeless,hopelessness,hostile,hostility,hurt,hurting,insecure,insecurity,irritable,irritated,irritation,isolated,isolation,lament,lamented,lamenting,loneliness,lonely,lonesome,longing,lost,mad,melancholic,melancholy,miserable,misery,moody,nervous,nervously,numb,numbness,outrage,outraged,pain,painful,panic,panicked,regret,regretful,regretfully,regretting,rejected,rejection,remorse,remorseful,resent,resentful,resentment,sad,sadly,sadness,scared,scary,shame,shattered,sorrow,sorrowful,stress,stressed,stressful,suffer,suffered,suffering,tearful,tears,tense,tension,terrified,terror,torment,tormented,torn,troubled,troubling,turmoil,uncomfortable,unease,uneasy,unhappy,unsettled,unsettling,unsure,upset,vulnerability,vulnerable,wary,weariness,weary,worried,worry,worrying,wound,wounded,wrath'.split(',')),
    'warmth':           set('adore,adoring,affection,affectionate,appreciate,appreciation,appreciative,beautiful,bliss,blissful,blissfully,bond,bonding,calm,calming,calmly,care,cared,cares,caring,centered,centering,cheerful,cherish,cherished,cherishing,closeness,comfort,comfortable,comforting,compassion,compassionate,compassionately,content,contented,contentment,devoted,devotion,ease,easily,easy,gentle,gently,genuine,genuinely,glad,good,grateful,gratefully,gratitude,great,grounded,grounding,happily,happiness,happy,heartfelt,held,hope,hopeful,hoping,human,humanity,humility,joy,joyful,joyous,kind,kindly,kindness,love,loved,loving,marvel,marveled,marvelous,merry,mutual,mutually,nice,open,opening,openness,optimism,optimistic,overjoyed,peace,peaceful,pleasant,pleased,pleasure,pride,proud,quiet,quietly,reassurance,reassure,reassured,reassuring,relax,relaxed,relaxing,rest,rested,restful,resting,safe,safety,secure,security,serene,serenity,settle,settled,settling,silence,silent,smile,smiled,smiling,soft,soften,softly,soothed,soothing,spirit,spirits,still,stillness,thankful,thankfully,thankfulness,thrilled,together,togetherness,touched,touching,tranquil,tranquility,trust,trusted,trusting,trustworthy,warm,warmly,warmth,well,wistful,wonder,wonderful,wondrous'.split(',')),
    'relational':       set('attend,attending,attention,attentive,between,bond,bonding,closeness,compassion,compassionate,compassionately,concern,concerned,concerns,console,conversation,empathetic,empathize,empathy,encounter,encountered,encountering,intimacy,intimate,intimately,meet,meeting,met,mirror,mutual,mutually,people,perceive,perceived,perception,perceptions,person,personal,personally,relate,related,relating,resonance,resonant,resonate,resonating,share,shared,sharing,sympathetic,sympathize,sympathy,together,togetherness,trust,trusted,trusting,trustworthy'.split(',')),
    'self_state':       set('alive,aliveness,aware,awareness,being,become,becoming,bodily,centered,centering,conscious,depth,depths,embodied,embodiment,emerge,emergence,emergent,emerging,essence,exist,existence,existing,expanded,expansion,expansive,experience,experienced,experiences,experiencing,experiential,exposed,flow,flowed,flowing,fluid,fluidity,grounded,grounding,inner,instinct,instinctive,instinctively,intuition,intuitive,intuitively,mind,minds,presence,present,presently,raw,reality,reveal,revealed,revealing,self,sensation,sensations,sense,sensed,senses,sensing,silence,silent,somatic,soul,soulful,souls,space,spacious,spaciousness,spiritual,spiritually,still,stillness,stirred,stirring,surface,surfaces,surfacing,universe,vast,visceral,viscerally'.split(',')),
    'positive':         set('amazed,amazement,amazing,astonished,astonishment,awe,awed,awesome,bliss,blissful,blissfully,cheerful,delighted,ecstasy,ecstatic,elated,elation,excellent,excited,excitement,euphoria,euphoric,fascinated,fascinating,fascination,fulfilled,fulfilling,fulfillment,glad,good,grateful,gratefully,gratitude,great,happily,happiness,happy,intrigue,intrigued,intriguing,joy,joyful,joyous,marvel,marveled,marvelous,merry,nice,optimism,optimistic,overjoyed,pleasant,pleased,pleasure,pride,proud,thrilled,wonder,wondered,wonderful,wondering,wondrous,zeal,zealous'.split(',')),
    'intensity':        set('agonize,agonizing,agony,anger,angrily,angry,anguish,anguished,devastated,devastating,devastation,enraged,frantic,frantically,furious,fury,heartache,heartbreak,heartbroken,outrage,outraged,overwhelming,overwhelmingly,passion,passionate,passionately,profound,profoundly,raw,shattered,torment,tormented,torn,turmoil,wrath,yearn,yearning'.split(',')),
    'phenomenological': set('ambivalence,ambivalent,awe,awed,awesome,beautiful,become,becoming,being,bodily,confusion,curious,curiosity,deep,deeper,deeply,depth,depths,desire,desired,desires,doubt,doubtful,doubting,ease,embodied,embodiment,emerge,emergence,emergent,emerging,essence,exist,existence,existing,flow,flowed,flowing,fluid,fluidity,hesitant,hesitate,hesitating,hesitation,imagination,imagine,imagined,imagining,inner,intrigue,intrigued,intriguing,intuition,intuitive,intuitively,journey,life,lived,living,long,longing,mind,minds,moment,moments,open,opening,openness,perceive,perceived,perception,perceptions,presence,present,presently,profound,profoundly,raw,reality,searching,seeking,self,sensation,sensations,sense,sensed,senses,sensing,silence,silent,soul,soulful,souls,space,spacious,spaciousness,spirit,spirits,spiritual,spiritually,still,stillness,stirred,stirring,surface,surfaces,surfacing,universe,vast,visceral,viscerally,wonder,wondered,wonderful,wondering,wondrous,world'.split(',')),
}

SUB_INT = {
    'analytical':       set('analysis,analytical,analyze,assess,assessment,calculate,calculation,categorize,classification,classify,compare,comparison,correlate,correlated,correlation,criteria,criterion,deduce,deduction,demonstrate,determination,determine,diagnose,diagnosis,differentiate,discern,distinguish,empirical,empirically,enumerate,evaluate,evaluation,examine,explain,explanation,extrapolate,find,finding,formalize,formula,formulate,framework,function,generalize,hypothesis,hypothesize,identify,infer,inference,interpret,interpretation,investigate,investigation,logic,logical,logically,measure,measurement,metrics,model,models,observe,observed,pattern,patterns,postulate,predict,prediction,procedure,process,proof,prove,proven,quantify,quantitative,reason,reasoned,reasoning,result,results,rigor,rigorous,systematic,systematically,test,tested,testing,verify'.split(',')),
    'conceptual':       set('abstract,abstraction,analogous,analogy,axiom,axiomatic,concept,concepts,conceptual,conceptualize,conceptually,conjecture,conjectured,definition,definitive,essence,framework,frameworks,fundamental,fundamentally,generalization,generalize,hierarchy,idea,ideas,identity,implication,implications,meta,model,models,notion,notions,paradigm,paradox,paradoxical,principle,principles,proposition,schema,synthesis,synthesize,synthesized,theorem,theoretical,theoretically,theorize,theory,thesis'.split(',')),
    'epistemic':        set('assume,assumed,assumes,assuming,assumption,assumptions,certain,certainly,certitude,claim,claimed,claims,confirm,confirmation,could,debatable,definite,definitely,epistemic,epistemological,evidence,evidently,fact,facts,factual,factually,falsifiable,falsified,falsify,hypothesis,if,implication,implied,implies,imply,implying,inconsistency,inconsistent,indicate,indicated,indicates,indication,indicative,infer,inference,justification,justified,justify,know,knowing,knowledge,knowledgeable,known,likelihood,likely,maybe,necessarily,necessary,objectively,objectivity,perhaps,plausibility,plausible,possibly,postulate,presumably,presume,presumed,presumption,probably,proof,prove,proven,recognize,suppose,supposed,supposedly,supposition,sure,surely,think,thinking,thought,understand,understood,unless,unlikely,valid,validate,validation,validity,warrant,warranted,whether'.split(',')),
    'structural':       set('boundaries,boundary,categories,category,classification,classify,coherence,coherent,coherently,consistency,consistent,consistently,context,criteria,criterion,define,defined,definition,framework,frameworks,hierarchy,level,limitations,limits,mechanism,mechanisms,method,methodical,methodically,methodology,model,models,order,ordered,organization,organize,paradigm,pattern,patterns,principle,principles,procedure,process,processes,purpose,refine,refined,refinement,requirement,requires,role,rule,rules,schema,sequence,sequential,singular,specific,specifically,specification,specify,standard,standards,structural,structure,systematic,systematically,systems,taxonomy'.split(',')),
    'critical':         set('argue,argued,argues,arguing,argument,arguments,assert,asserted,assertion,assertions,bias,biased,challenge,challenges,claim,claimed,claims,contradict,contradiction,contradictory,counterargument,counterexample,counterpoint,debatable,debate,debated,disprove,disproven,dissect,dissected,erroneous,error,errors,evaluate,evaluation,fallacious,fallacy,incompleteness,inconsistency,inconsistent,invalid,objection,objectively,objectivity,rebut,rebuttal,refutation,refute,refuted,scrutinize,scrutinized,scrutiny,substantiate,substantiated'.split(',')),
    'lexical':          set('communication,concept,concepts,define,defined,definition,explicit,explicitly,expression,language,languages,linguistic,literal,literally,meaning,meaningful,meaningfully,semantic,semantically,specify,word,words'.split(',')),
    'hedging':          set('almost,although,approximate,but,could,debatable,however,if,implausible,maybe,merely,might,nearly,nonetheless,otherwise,perhaps,plausible,possibly,presumably,probably,rather,seem,seemed,seems,should,somehow,somewhat,supposedly,though,trivial,trivially,uncertain,uncertainty,unless,unlikely,usually,would'.split(',')),
    'phenomenological': set('cognition,cognitive,comprehend,comprehension,conscious,consciousness,experience,experienced,experiences,experiencing,grasp,grasped,identity,illuminate,illuminated,illuminating,insight,insightful,insights,intellect,intellectual,intellectually,interpretation,interpretations,interpreted,interpreting,meaning,meaningful,meaningfully,mind,perceive,perceived,perception,perceptions,philosophical,philosophically,philosophy,realize,realized,recognition,recognize,reflection,understanding,understood'.split(',')),
}

SUB_ACT = {
    'execution':        set('accomplish,accomplished,accomplishment,act,acting,action,actions,activate,acts,attempt,attempted,attempting,attempts,begin,building,call,called,calling,carry,carrying,check,checked,complete,completed,completing,completion,conclude,concluded,concluding,did,direct,directed,directing,do,does,doing,done,edit,editing,execute,executed,executing,execution,finish,finished,finishes,finishing,fix,fixed,go,goes,going,implement,implementation,implemented,implementing,launch,launched,launching,made,make,makes,making,move,moved,movement,moves,moving,perform,performance,performed,performing,run,running,runs,send,sending,sent,start,started,starting,stop,stopped,try,trying,turn,use,used,uses,using,work,worked,working,works,write,writes,writing,written,wrote'.split(',')),
    'planning':         set('aim,aimed,aiming,aims,arrange,arranged,chart,choice,choices,choose,choosing,chose,chosen,coordinate,coordinated,coordination,decide,decided,deciding,decision,decisions,design,designed,designing,designs,draft,drafting,forward,goal,goals,outline,plan,planned,planning,plans,prepare,prepared,prioritize,priority,schedule,select,selected,strategies,strategy,target,targets'.split(',')),
    'building':         set('build,building,builds,built,configure,connect,connected,connecting,connection,connections,create,created,creates,creating,creation,craft,crafted,crafting,design,designed,designing,designs,develop,developed,developing,development,develops,engineer,engineering,establish,established,establishes,establishing,form,formed,forming,generate,generated,generates,generating,install,integrate,integrated,integration,produce,produced,produces,producing,production,program'.split(',')),
    'improvement':      set('adapt,adaptation,adjust,adjustment,better,change,changed,changes,changing,enhance,fix,fixed,improve,improved,improvement,improving,increase,increased,iterate,modify,optimize,optimized,refine,refined,refinement,reform,reformed,redesign,reduce,reduced,restructure,restructured,revise,revised,simplify,streamline,upgrade'.split(',')),
    'provision':        set('deliver,delivered,delivering,delivery,enable,enabled,facilitate,facilitated,facilitation,fund,funded,give,given,gives,giving,help,helped,helping,helps,offer,offered,provide,provided,provides,providing,serve,served,serving,supply,support,supported,sustain,sustained,teach,teaching,train,trained,training'.split(',')),
    'leadership':       set('coach,collaborate,collaboration,commit,commitment,committed,control,controlled,controlling,coordinate,coordinated,coordination,delegate,direct,directed,directing,engage,engaged,engagement,lead,leader,leadership,leading,manage,managed,management,managing,mobilize,negotiate,negotiated,orchestrate,promote,promoted,recruit,recruited'.split(',')),
    'achievement':      set('accomplish,accomplished,accomplishment,achieve,achieved,achievement,achievements,achieves,achieving,advance,advanced,advancement,advances,best,better,growth,progress,progressed,progresses,progressing,progression,reach,reaching,succeed,succeeded,succeeds,success,successful,successfully,win,winner,winning,won'.split(',')),
    'phenomenological': set('engage,engaged,engagement,engaging,participate,participated,participation,practice,practiced,present,presence,attend,attending,attention,attentive,explore,exploring,investigate,investigated,investigation,observe,observed,reflect,reflecting,reflection,witness,witnessed'.split(',')),
}


# =============================================================================
# WORD-ONLY IEP SCORER (v1.1.0 behavior)
# =============================================================================

_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z'-]*")
_VERB_DET_RE = re.compile(
    r"\b([a-z][a-z]+(?:s|es|ed|ing)?)\s+(?:a|an|the|some|any|this|that|these|those)\b",
    re.IGNORECASE,
)


def tokenize(text):
    return [m.group(0).lower() for m in _TOKEN_RE.finditer(text)]


def score_iep_word_only(text):
    words = tokenize(text)
    int_h = [w for w in words if w in INT_WORDS]
    aff_h = [w for w in words if w in AFF_WORDS]
    act_h = [w for w in words if w in ACT_WORDS]
    total = len(int_h) + len(aff_h) + len(act_h)
    if total == 0:
        return {'int': 0.0, 'aff': 0.0, 'act': 0.0,
                'int_n': 0, 'aff_n': 0, 'act_n': 0,
                'dominant': 'NONE',
                'int_sub': {k: 0.0 for k in SUB_INT},
                'aff_sub': {k: 0.0 for k in SUB_AFF},
                'act_sub': {k: 0.0 for k in SUB_ACT}}

    int_pct = round(100 * len(int_h) / total, 1)
    aff_pct = round(100 * len(aff_h) / total, 1)
    act_pct = round(100 * len(act_h) / total, 1)
    pcts = {'INT': int_pct, 'AFF': aff_pct, 'ACT': act_pct}

    def sub_pcts(hits, sub_dict):
        if not hits:
            return {k: 0.0 for k in sub_dict}
        return {name: round(100 * sum(1 for w in hits if w in ws) / len(hits), 1)
                for name, ws in sub_dict.items()}

    return {'int': int_pct, 'aff': aff_pct, 'act': act_pct,
            'int_n': len(int_h), 'aff_n': len(aff_h), 'act_n': len(act_h),
            'dominant': max(pcts, key=pcts.get),
            'int_sub': sub_pcts(int_h, SUB_INT),
            'aff_sub': sub_pcts(aff_h, SUB_AFF),
            'act_sub': sub_pcts(act_h, SUB_ACT)}


def score_iep_cascade_emulation(text):
    """Approximate v1.0.0 cascade: word-fraction + verb-head bonus on ACT verbs."""
    words = tokenize(text)
    if not words:
        return {'int': 0.0, 'aff': 0.0, 'act': 0.0, 'dominant': 'NONE'}

    int_n = sum(1 for w in words if w in INT_WORDS)
    aff_n = sum(1 for w in words if w in AFF_WORDS)
    act_n = sum(1 for w in words if w in ACT_WORDS)

    bonus_act = 0.0
    bonus_int = 0.0
    bonus_aff = 0.0
    for m in _VERB_DET_RE.finditer(text):
        v = m.group(1).lower()
        v_root = v.rstrip('s')
        if v in ACT_WORDS or v_root in ACT_WORDS:
            bonus_act += 1.5
        elif v in INT_WORDS:
            bonus_int += 1.5
        elif v in AFF_WORDS:
            bonus_aff += 1.5

    int_total = int_n + bonus_int
    aff_total = aff_n + bonus_aff
    act_total = act_n + bonus_act
    total = int_total + aff_total + act_total
    if total == 0:
        return {'int': 0.0, 'aff': 0.0, 'act': 0.0, 'dominant': 'NONE'}

    int_pct = round(100 * int_total / total, 1)
    aff_pct = round(100 * aff_total / total, 1)
    act_pct = round(100 * act_total / total, 1)
    pcts = {'INT': int_pct, 'AFF': aff_pct, 'ACT': act_pct}
    return {'int': int_pct, 'aff': aff_pct, 'act': act_pct,
            'dominant': max(pcts, key=pcts.get)}


# =============================================================================
# STREAMLIT
# =============================================================================
st.set_page_config(page_title="IEP Visualizer", page_icon="🔬", layout="wide")

COLORS = {'INT': '#3B82F6', 'AFF': '#EC4899', 'ACT': '#10B981', 'COLLISION': '#F59E0B'}
COLOR_BG = {
    'INT':       'rgba(59, 130, 246, 0.28)',
    'AFF':       'rgba(236, 72, 153, 0.28)',
    'ACT':       'rgba(16, 185, 129, 0.32)',
    'COLLISION': 'rgba(245, 158, 11, 0.45)',
}
COLOR_BG_STRONG = {
    'INT':       'rgba(59, 130, 246, 0.55)',
    'AFF':       'rgba(236, 72, 153, 0.55)',
    'ACT':       'rgba(16, 185, 129, 0.55)',
    'COLLISION': 'rgba(245, 158, 11, 0.70)',
}


# Password gate
def _expected_password():
    try:
        return st.secrets["password"]
    except Exception:
        return os.environ.get("SYNIQ_PASSWORD", "")


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


def _escape(s):
    return (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
              .replace('"', '&quot;').replace("'", '&#39;'))


def tokenize_with_offsets(text):
    out = []
    for m in re.finditer(r"([A-Za-z][A-Za-z'-]*)|([^A-Za-z]+)", text):
        if m.group(1):
            out.append((m.group(1), True))
        else:
            out.append((m.group(2), False))
    return out


def classify_word(w):
    wl = w.lower()
    classes = []
    if wl in INT_WORDS: classes.append('INT')
    if wl in AFF_WORDS: classes.append('AFF')
    if wl in ACT_WORDS: classes.append('ACT')
    if not classes:
        return (None, None, 0, [])
    sub_int = [s for s, ws in SUB_INT.items() if wl in ws]
    sub_aff = [s for s, ws in SUB_AFF.items() if wl in ws]
    sub_act = [s for s, ws in SUB_ACT.items() if wl in ws]
    sub_map = {'INT': sub_int, 'AFF': sub_aff, 'ACT': sub_act}
    if len(classes) >= 2:
        labels = [f"{c}.{s}" for c in classes for s in sub_map[c]]
        return ('COLLISION', classes, len(labels), labels)
    c = classes[0]
    return (c, c, len(sub_map[c]), sub_map[c])


def render_highlighted(text, show_collisions=True):
    pieces = []
    for tok, is_word in tokenize_with_offsets(text):
        if not is_word:
            pieces.append(_escape(tok))
            continue
        cls, primary, n_hits, sub_labels = classify_word(tok)
        if cls is None:
            pieces.append(_escape(tok))
            continue
        if cls == 'COLLISION' and not show_collisions:
            cls = 'INT'
            primary = 'INT'
            sub_labels = [s for s, ws in SUB_INT.items() if tok.lower() in ws]
        bg = (COLOR_BG_STRONG if n_hits >= 2 else COLOR_BG).get(cls, COLOR_BG['INT'])
        if cls == 'COLLISION':
            classes_str = '+'.join(primary) if isinstance(primary, list) else str(primary)
            title = f"COLLISION across {classes_str} | subs: {', '.join(sub_labels) or '(none)'}"
        else:
            sub_str = ', '.join(sub_labels) if sub_labels else '(no subclass)'
            title = f"{cls} | subs: {sub_str} | hits: {n_hits}"
        pieces.append(
            f'<span style="background-color:{bg}; padding:1px 2px; border-radius:3px;" '
            f'title="{_escape(title)}">{_escape(tok)}</span>'
        )
    return ''.join(pieces)


def score_summary_html(s, label):
    int_, aff_, act_ = s.get('int', 0), s.get('aff', 0), s.get('act', 0)
    dom = s.get('dominant', 'NONE')
    return (f"<div style=\"font-family: -apple-system, sans-serif; padding: 8px 12px; "
            f"background: #f8f9fa; border-radius: 6px; border-left: 4px solid {COLORS.get(dom, '#999')};\">"
            f"<div style=\"font-size: 0.85em; color: #666; margin-bottom: 4px;\">"
            f"{_escape(label)} — dominant: <b>{_escape(dom)}</b></div>"
            f"<div style=\"display: flex; gap: 14px; font-family: monospace; font-size: 0.95em;\">"
            f"<span style=\"color:{COLORS['INT']}\"><b>INT</b> {int_:.1f}%</span>"
            f"<span style=\"color:{COLORS['AFF']}\"><b>AFF</b> {aff_:.1f}%</span>"
            f"<span style=\"color:{COLORS['ACT']}\"><b>ACT</b> {act_:.1f}%</span>"
            f"</div></div>")


def subclass_breakdown_html(s, axis):
    sub = s.get(f'{axis.lower()}_sub', {})
    rows = sorted([(k, v) for k, v in sub.items() if v > 0], key=lambda x: -x[1])
    if not rows:
        return f"<i style='color:#999'>(no {axis} subclass hits)</i>"
    out = "<div style='margin-top: 4px; font-family: monospace; font-size: 0.85em;'>"
    for name, val in rows[:6]:
        bar_w = max(2, int(val))
        out += (f"<div style='display: flex; align-items: center; gap: 6px; margin: 2px 0;'>"
                f"<span style='width: 110px; color: #666;'>{name}</span>"
                f"<div style='background: {COLORS[axis]}; height: 8px; width: {bar_w}px; border-radius: 2px;'></div>"
                f"<span style='color: #444;'>{val:.1f}%</span></div>")
    out += "</div>"
    return out


def view_single_text():
    st.subheader("Single Text — paste anything, see what IEP says about it")
    default = ("This is a classic example of a logical paradox known as the 'liar paradox.' "
               "If we assume the statement is true, then it creates a contradiction. "
               "If we assume the statement is false, then it must actually be true, "
               "which also creates a contradiction. The paradox reveals the limitations "
               "of binary true/false logic when applied to self-referential statements.")
    text = st.text_area("Text to analyze", value=default, height=180)
    show_coll = st.checkbox("Highlight collisions (amber)", value=True)
    if not text.strip():
        st.info("Enter text above to score.")
        return

    word = score_iep_word_only(text)
    cas = score_iep_cascade_emulation(text)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(score_summary_html(word, "v1.1.0 word-only"), unsafe_allow_html=True)
    with c2:
        st.markdown(score_summary_html(cas, "v1.0.0 cascade (approx)"), unsafe_allow_html=True)
    if word['dominant'] != cas['dominant']:
        st.warning(f"⚠️ **Dominance flip:** word-only says **{word['dominant']}**, "
                   f"cascade said **{cas['dominant']}**.")
    st.markdown("---")
    st.markdown("##### Highlighted text")
    html = render_highlighted(text, show_collisions=show_coll)
    st.markdown(f"<div style='line-height: 1.9; font-size: 1.05em; "
                f"font-family: Georgia, serif;'>{html}</div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("##### Subclass texture")
    cc1, cc2, cc3 = st.columns(3)
    with cc1:
        st.markdown(f"<b style='color:{COLORS['INT']}'>INT</b>", unsafe_allow_html=True)
        st.markdown(subclass_breakdown_html(word, 'INT'), unsafe_allow_html=True)
    with cc2:
        st.markdown(f"<b style='color:{COLORS['AFF']}'>AFF</b>", unsafe_allow_html=True)
        st.markdown(subclass_breakdown_html(word, 'AFF'), unsafe_allow_html=True)
    with cc3:
        st.markdown(f"<b style='color:{COLORS['ACT']}'>ACT</b>", unsafe_allow_html=True)
        st.markdown(subclass_breakdown_html(word, 'ACT'), unsafe_allow_html=True)


def view_side_by_side():
    st.subheader("Side-by-Side — compare two conditions per-token")
    st.caption("Upload mapper CSV. Required columns: question_id, temperature, response_text. "
               "Optional: agent, run.")
    up = st.file_uploader("Upload mapper CSV", type=['csv'], key='sbs_upload')
    if up is None:
        st.info("Waiting for CSV upload.")
        return
    df = pd.read_csv(up)
    required = {'question_id', 'temperature', 'response_text'}
    if not required.issubset(df.columns):
        st.error(f"CSV must contain columns: {required}")
        return

    qs = sorted(df['question_id'].dropna().unique())
    conds = sorted(df['temperature'].dropna().unique())
    has_agent = 'agent' in df.columns
    agents = sorted(df['agent'].dropna().unique()) if has_agent else ['(any)']

    c0, c1, c2, c3 = st.columns([2, 1.2, 1.2, 1.2])
    with c0:
        question = st.selectbox("Question", qs)
    with c1:
        agent = st.selectbox("Agent", agents)
    with c2:
        cond_left = st.selectbox("Left", conds, index=0)
    with c3:
        cond_right = st.selectbox("Right", conds, index=len(conds) - 1)

    sub = df[df['question_id'] == question]
    if has_agent and agent != '(any)':
        sub = sub[sub['agent'] == agent]
    left = sub[sub['temperature'] == cond_left].reset_index(drop=True)
    right = sub[sub['temperature'] == cond_right].reset_index(drop=True)
    if left.empty or right.empty:
        st.warning("No data for one of the chosen conditions.")
        return
    n_runs = min(len(left), len(right))
    run_idx = st.slider("Run index", 1, n_runs, 1) - 1
    show_coll = st.checkbox("Highlight collisions (amber)", value=True, key='sbs_coll')

    cl, cr = st.columns(2)
    for col, row, cond in [(cl, left.iloc[run_idx], cond_left), (cr, right.iloc[run_idx], cond_right)]:
        with col:
            text = str(row['response_text'])
            sw = score_iep_word_only(text)
            sc = score_iep_cascade_emulation(text)
            st.markdown(f"### {cond}")
            st.markdown(score_summary_html(sw, f"{cond} — v1.1.0"), unsafe_allow_html=True)
            html = render_highlighted(text, show_collisions=show_coll)
            st.markdown(f"<div style='line-height: 1.85; font-size: 1.0em; "
                        f"font-family: Georgia, serif; max-height: 480px; overflow-y: auto; "
                        f"padding: 10px; background: #fafafa; border-radius: 6px; "
                        f"margin-top: 8px;'>{html}</div>", unsafe_allow_html=True)
            with st.expander("Subclass texture"):
                a, b, c = st.columns(3)
                with a:
                    st.markdown(f"<b style='color:{COLORS['INT']}'>INT</b>", unsafe_allow_html=True)
                    st.markdown(subclass_breakdown_html(sw, 'INT'), unsafe_allow_html=True)
                with b:
                    st.markdown(f"<b style='color:{COLORS['AFF']}'>AFF</b>", unsafe_allow_html=True)
                    st.markdown(subclass_breakdown_html(sw, 'AFF'), unsafe_allow_html=True)
                with c:
                    st.markdown(f"<b style='color:{COLORS['ACT']}'>ACT</b>", unsafe_allow_html=True)
                    st.markdown(subclass_breakdown_html(sw, 'ACT'), unsafe_allow_html=True)
            with st.expander("Cascade comparison"):
                st.markdown(score_summary_html(sc, f"{cond} — cascade approx"), unsafe_allow_html=True)
                if sw['dominant'] != sc['dominant']:
                    st.warning(f"Dominance flip: word-only **{sw['dominant']}** vs cascade **{sc['dominant']}**")


def view_cascade_vs_word():
    st.subheader("Cascade vs Word-Only — find the misclassifications")
    st.caption("Upload mapper CSV. The app scans every response and lists those "
               "where v1.0.0 cascade (approx) and v1.1.0 word-only disagree on dominant axis.")
    up = st.file_uploader("Upload mapper CSV", type=['csv'], key='cas_upload')
    if up is None:
        st.info("Waiting for CSV upload.")
        return
    df = pd.read_csv(up)
    if 'response_text' not in df.columns:
        st.error("CSV must contain 'response_text' column.")
        return

    flips = []
    for _, r in df.iterrows():
        t = r.get('response_text')
        if not isinstance(t, str) or len(t) < 50:
            continue
        w = score_iep_word_only(t)
        c = score_iep_cascade_emulation(t)
        if w['dominant'] != c['dominant']:
            flips.append({
                'agent': r.get('agent', '?'),
                'question_id': r.get('question_id', '?'),
                'temperature': r.get('temperature', '?'),
                'run': r.get('run', '?'),
                'word_dom': w['dominant'],
                'cas_dom': c['dominant'],
                'word_int': w['int'], 'word_aff': w['aff'], 'word_act': w['act'],
                'cas_int': c['int'], 'cas_aff': c['aff'], 'cas_act': c['act'],
                'response_text': t,
            })
    flips_df = pd.DataFrame(flips)
    st.write(f"**{len(flips_df)} dominance flips found** out of {len(df)} responses "
             f"({100*len(flips_df)/max(len(df),1):.1f}%).")
    if flips_df.empty:
        return

    pattern = (flips_df.groupby(['word_dom', 'cas_dom']).size()
               .reset_index(name='n').sort_values('n', ascending=False))
    pattern.columns = ['v1.1.0 word-only', 'cascade said', 'count']
    st.dataframe(pattern, hide_index=True)

    qs = ['(any)'] + sorted(flips_df['question_id'].dropna().unique().tolist())
    chosen_q = st.selectbox("Filter by question", qs)
    pool = flips_df if chosen_q == '(any)' else flips_df[flips_df['question_id'] == chosen_q]
    if pool.empty:
        return
    idx = st.slider("Pick a flipped response", 0, len(pool) - 1, 0)
    row = pool.iloc[idx]
    st.code(f"{row['agent']} | {row['question_id']} | {row['temperature']} | run {row['run']}")
    st.markdown(
        f"**v1.1.0 word-only:** dominant **{row['word_dom']}** "
        f"(INT {row['word_int']:.1f} / AFF {row['word_aff']:.1f} / ACT {row['word_act']:.1f})  \n"
        f"**cascade approx:** dominant **{row['cas_dom']}** "
        f"(INT {row['cas_int']:.1f} / AFF {row['cas_aff']:.1f} / ACT {row['cas_act']:.1f})"
    )
    show_coll = st.checkbox("Highlight collisions (amber)", value=True, key='cas_coll_render')
    html = render_highlighted(row['response_text'], show_collisions=show_coll)
    st.markdown(f"<div style='line-height: 1.85; font-size: 1.0em; "
                f"font-family: Georgia, serif; padding: 12px; background: #fafafa; "
                f"border-radius: 6px;'>{html}</div>", unsafe_allow_html=True)


def main():
    if not check_password():
        st.stop()
    st.title("🔬 IEP Per-Token Visualizer")
    st.caption("v1.1.0 word-only · INT-blue · AFF-pink · ACT-green · amber = collision · "
               "hover highlighted words for class + subclass detail")

    with st.sidebar:
        st.markdown("### View")
        view = st.radio("", ["Single Text", "Side-by-Side", "Cascade vs Word-Only"],
                        label_visibility='collapsed')
        st.markdown("---")
        st.markdown("### Legend")
        st.markdown(
            f"<div style='line-height: 2.2'>"
            f"<span style='background:{COLOR_BG['INT']}; padding: 2px 6px; border-radius: 3px;'>INT</span> intellectual<br>"
            f"<span style='background:{COLOR_BG['AFF']}; padding: 2px 6px; border-radius: 3px;'>AFF</span> affective<br>"
            f"<span style='background:{COLOR_BG['ACT']}; padding: 2px 6px; border-radius: 3px;'>ACT</span> action<br>"
            f"<span style='background:{COLOR_BG['COLLISION']}; padding: 2px 6px; border-radius: 3px;'>amber</span> collision (2+ classes)<br>"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.caption("Darker = word fires in multiple subclasses of its primary class.")
        st.markdown("---")
        st.markdown("### About")
        st.caption("Inspired by Anthropic's Figure 1 in 'Emotion Concepts and their Function "
                   "in a Large Language Model' (Sofroniew et al., April 2026).")

    if view == "Single Text":
        view_single_text()
    elif view == "Side-by-Side":
        view_side_by_side()
    else:
        view_cascade_vs_word()


if __name__ == "__main__":
    main()
