"""
SYN-IQ Mapper Analyzer V49 — Streamlit App
Topological Data Analysis for AI Response Profiles

WHAT'S NEW IN V49:
  - Node tooltips now show: Agent | Temperature | Question ID
    e.g. "Gemini | NATIVE | LIARS_PARADOX" — so you can see which
    question each node cluster came from at a glance
  - All V4 features preserved (embedded IEP Dict V3, live scoring,
    Dictionary Explorer, Score Text tab)

SYNINT Team — March 2026
Tennessee 🎹 CUZ Partnership
"""

import streamlit as st
import pandas as pd
import numpy as np
import json
import tempfile
import os
import re
from collections import Counter

# =============================================================================
# IEP DICTIONARY V3 — FULLY EMBEDDED (1,897 words · no external file needed)
# =============================================================================

_IEP_INT_WORDS = ['ability', 'absolute', 'absolutely', 'abstract', 'abstraction', 'accuracy', 'accurate', 'algorithm', 'algorithmic', 'allows', 'although', 'always', 'ambiguity', 'ambiguous', 'analogous', 'analogously', 'analogy', 'analysis', 'analytical', 'analyze', 'annotate', 'annotated', 'answer', 'appear', 'appeared', 'appears', 'appraisal', 'appraise', 'appraised', 'approach', 'approaches', 'approximate', 'architecture', 'argue', 'argued', 'argues', 'arguing', 'argument', 'arguments', 'assert', 'asserted', 'assertion', 'assertions', 'assess', 'assessment', 'assume', 'assumed', 'assumes', 'assuming', 'assumption', 'assumptions', 'axiom', 'axiomatic', 'basis', 'because', 'bias', 'biased', 'boundaries', 'boundary', 'but', 'calculate', 'calculation', 'categorical', 'categorically', 'categories', 'categorize', 'category', 'causal', 'causally', 'causation', 'cause', 'caused', 'causes', 'certain', 'certainly', 'certitude', 'challenge', 'challenges', 'circumscribe', 'claim', 'claimed', 'claims', 'clarify', 'clarity', 'classical', 'classification', 'classify', 'clear', 'cogent', 'cogently', 'cognition', 'cognitive', 'coherence', 'coherent', 'coherently', 'communication', 'compare', 'comparison', 'complex', 'complexity', 'comprehend', 'comprehension', 'computation', 'computational', 'compute', 'conceivable', 'conceive', 'conceived', 'concept', 'concepts', 'conceptual', 'conceptualize', 'conceptually', 'conclude', 'conclusion', 'conclusions', 'confirm', 'confirmation', 'conjecture', 'conjectured', 'conscious', 'consequence', 'consequences', 'consider', 'consideration', 'consistency', 'consistent', 'consistently', 'construe', 'construed', 'context', 'contradict', 'contradiction', 'contradictory', 'contrast', 'correlate', 'correlated', 'correlation', 'could', 'counterargument', 'counterexample', 'counterpoint', 'criteria', 'criterion', 'data', 'debatable', 'debate', 'debated', 'deconstruct', 'deconstructed', 'deconstruction', 'deduce', 'deduction', 'define', 'defined', 'definite', 'definitely', 'definition', 'definitive', 'definitively', 'delineate', 'delineated', 'demarcate', 'demarcated', 'demonstrate', 'demonstration', 'derivation', 'derive', 'derived', 'derives', 'describe', 'described', 'describing', 'description', 'determination', 'determine', 'diagnose', 'diagnosed', 'diagnosis', 'diagnostic', 'differ', 'difference', 'differences', 'different', 'differentiate', 'differs', 'discern', 'discerned', 'discernible', 'disprove', 'disproven', 'dissect', 'dissected', 'distinguish', 'effect', 'effects', 'elaborate', 'elaborated', 'elaboration', 'elucidate', 'elucidated', 'empirical', 'empirically', 'enumerate', 'enumerated', 'epistemic', 'epistemological', 'equate', 'equation', 'equivalence', 'equivalent', 'erroneous', 'error', 'errors', 'essential', 'essentially', 'estimate', 'estimated', 'estimation', 'evaluate', 'evaluation', 'evidence', 'evidently', 'exact', 'exactly', 'examination', 'examine', 'except', 'exemplified', 'exemplify', 'exists', 'experiment', 'experimental', 'explain', 'explained', 'explaining', 'explains', 'explanation', 'explanations', 'explicit', 'explicitly', 'exploration', 'explore', 'explored', 'exploring', 'express', 'expressing', 'expression', 'extrapolate', 'extrapolated', 'extrapolation', 'fact', 'facts', 'factual', 'factually', 'fallacious', 'fallacy', 'falsifiable', 'falsified', 'falsify', 'find', 'finding', 'formal', 'formalize', 'formula', 'formulate', 'formulated', 'formulation', 'found', 'framework', 'frameworks', 'function', 'fundamental', 'fundamentally', 'generalization', 'generalize', 'grasp', 'grasped', 'guess', 'hence', 'heuristic', 'heuristics', 'hierarchy', 'however', 'hypothesis', 'hypothesize', 'idea', 'ideas', 'identity', 'if', 'illuminate', 'illuminated', 'illuminating', 'implausible', 'implication', 'implications', 'implied', 'implies', 'imply', 'implying', 'incompleteness', 'inconsistency', 'inconsistent', 'indicate', 'indicated', 'indicates', 'indicating', 'indication', 'indicative', 'individual', 'infer', 'inference', 'infinite', 'information', 'insight', 'insightful', 'insights', 'instead', 'insufficient', 'intellectual', 'intellectually', 'interaction', 'internal', 'interpolate', 'interpret', 'interpretation', 'interpretations', 'interpreted', 'interpreting', 'invalid', 'investigate', 'investigated', 'investigation', 'judge', 'judgement', 'judgment', 'justification', 'justified', 'justify', 'know', 'knowing', 'knowledge', 'knowledgeable', 'known', 'language', 'languages', 'leads', 'level', 'likelihood', 'likely', 'limitations', 'limits', 'linguistic', 'literal', 'literally', 'logic', 'logical', 'logically', 'maybe', 'meaning', 'meaningful', 'meaningfully', 'measure', 'measurement', 'mechanism', 'mechanisms', 'meta', 'method', 'methodical', 'methodically', 'methodology', 'metrics', 'model', 'models', 'moreover', 'namely', 'natural', 'nature', 'nearly', 'necessarily', 'necessary', 'necessity', 'never', 'nonetheless', 'notice', 'noticed', 'noticing', 'notion', 'notions', 'objection', 'objectively', 'objectivity', 'observation', 'observations', 'observe', 'observed', 'obvious', 'obviously', 'order', 'ordered', 'organization', 'organize', 'otherwise', 'ought', 'paradigm', 'paradox', 'paradoxical', 'paradoxically', 'pattern', 'patterns', 'perhaps', 'perspective', 'philosophical', 'philosophically', 'philosophy', 'physical', 'plausibility', 'plausible', 'possibly', 'postulate', 'postulated', 'postulation', 'potential', 'pragmatic', 'pragmatically', 'precise', 'precision', 'predicate', 'predicated', 'predict', 'predictable', 'predicted', 'prediction', 'predictions', 'premise', 'premises', 'presumably', 'presume', 'presumed', 'presumption', 'principle', 'principles', 'probably', 'problem', 'procedural', 'procedure', 'process', 'processes', 'processing', 'proof', 'propose', 'proposed', 'proposition', 'prove', 'proven', 'purpose', 'quantify', 'quantitative', 'queried', 'query', 'question', 'questions', 'rather', 'rational', 'rationale', 'rationality', 'rationally', 'realize', 'realized', 'reason', 'reasoned', 'reasoning', 'reasons', 'rebut', 'rebuttal', 'recognition', 'recognize', 'reconsider', 'reconsidered', 'refer', 'reference', 'refers', 'refine', 'refined', 'refinement', 'reflecting', 'reflection', 'refutation', 'refute', 'refuted', 'requirement', 'requires', 'response', 'responses', 'result', 'resulting', 'results', 'rigor', 'rigorous', 'rigorously', 'role', 'rule', 'rules', 'schema', 'scrutinize', 'scrutinized', 'scrutiny', 'seem', 'seemed', 'seems', 'semantic', 'semantically', 'sequence', 'sequential', 'should', 'significance', 'significant', 'significantly', 'simple', 'simply', 'simultaneously', 'singular', 'specific', 'specifically', 'specification', 'specify', 'standard', 'standards', 'state', 'states', 'step', 'steps', 'stipulate', 'stipulated', 'strategies', 'strategy', 'structural', 'structure', 'subject', 'subjective', 'subjectively', 'subjectivity', 'substantiate', 'substantiated', 'sufficient', 'sufficiently', 'suggests', 'summarize', 'summarized', 'summary', 'suppose', 'supposed', 'supposedly', 'supposition', 'sure', 'surely', 'syllogism', 'syllogistic', 'synthesis', 'synthesize', 'synthesized', 'system', 'systematic', 'systematically', 'systems', 'tactic', 'tactics', 'taxonomy', 'technique', 'test', 'tested', 'testing', 'theorem', 'theoretical', 'theoretically', 'theorize', 'theory', 'thereby', 'therefore', 'thesis', 'think', 'thinking', 'thought', 'thoughts', 'thus', 'trivial', 'trivially', 'unambiguous', 'underlying', 'understand', 'understanding', 'understood', 'unique', 'universal', 'unless', 'unlikely', 'valid', 'validate', 'validation', 'validity', 'value', 'values', 'variable', 'variables', 'verification', 'verify', 'versus', 'warrant', 'warranted', 'whereas', 'whereby', 'whether', 'why', 'word', 'words', 'would']

_IEP_AFF_WORDS = ['abandoned', 'ache', 'aching', 'adore', 'adoring', 'affection', 'affectionate', 'afraid', 'agonize', 'agonizing', 'agony', 'alienated', 'alienation', 'alive', 'aliveness', 'alone', 'amazed', 'amazement', 'amazing', 'ambivalence', 'ambivalent', 'among', 'anger', 'angrily', 'angry', 'anguish', 'anguished', 'anxiety', 'anxious', 'appreciate', 'appreciation', 'appreciative', 'ashamed', 'astonished', 'astonishment', 'attend', 'attending', 'attention', 'attentive', 'aware', 'awareness', 'awe', 'awed', 'awesome', 'beautiful', 'become', 'becoming', 'being', 'bereaved', 'bereavement', 'betrayal', 'betrayed', 'between', 'bitter', 'bitterly', 'bitterness', 'bleak', 'bliss', 'blissful', 'blissfully', 'bodily', 'bond', 'bonding', 'calm', 'calming', 'calmly', 'care', 'cared', 'cares', 'caring', 'centered', 'centering', 'cheerful', 'cherish', 'cherished', 'cherishing', 'closeness', 'comfort', 'comfortable', 'comforting', 'compassion', 'compassionate', 'compassionately', 'concern', 'concerned', 'concerns', 'conflicted', 'confused', 'confusing', 'confusion', 'console', 'contain', 'contained', 'containing', 'contempt', 'content', 'contented', 'contentment', 'conversation', 'cope', 'coping', 'crestfallen', 'curiosity', 'curious', 'deep', 'deeper', 'deeply', 'dejected', 'dejection', 'delighted', 'depressed', 'depressing', 'depression', 'depth', 'depths', 'desire', 'desired', 'desires', 'desolate', 'desolation', 'despair', 'despairing', 'desperate', 'desperation', 'detached', 'detachment', 'devastated', 'devastating', 'devastation', 'devoted', 'devotion', 'disappointed', 'disappointment', 'discomfort', 'dismay', 'dismayed', 'distress', 'distressed', 'distressing', 'distrust', 'distrustful', 'doubt', 'doubtful', 'doubting', 'dread', 'dreaded', 'dreadful', 'dreading', 'ease', 'easily', 'easy', 'ecstasy', 'ecstatic', 'elated', 'elation', 'embarrassed', 'embarrassment', 'embodied', 'embodiment', 'embrace', 'embraced', 'embracing', 'emerge', 'emergence', 'emergent', 'emerging', 'emotion', 'emotional', 'emotionally', 'emotions', 'empathetic', 'empathize', 'empathy', 'encounter', 'encountered', 'encountering', 'enjoy', 'enjoyed', 'enjoying', 'enjoyment', 'enraged', 'essence', 'euphoria', 'euphoric', 'excellent', 'excited', 'excitement', 'exist', 'existence', 'existing', 'expanded', 'expansion', 'expansive', 'experience', 'experienced', 'experiences', 'experiencing', 'experiential', 'exposed', 'fascinated', 'fascinating', 'fascination', 'fear', 'fearful', 'fears', 'feel', 'feeling', 'feelings', 'feels', 'felt', 'flow', 'flowed', 'flowing', 'fluid', 'fluidity', 'forlorn', 'fragile', 'fragility', 'frantic', 'frantically', 'frustrated', 'frustration', 'fulfilled', 'fulfilling', 'fulfillment', 'furious', 'fury', 'gentle', 'gently', 'genuine', 'genuinely', 'glad', 'gloom', 'gloomy', 'good', 'grateful', 'gratefully', 'gratitude', 'great', 'grief', 'grieve', 'grieved', 'grieving', 'grounded', 'grounding', 'guilt', 'guilty', 'gut', 'happily', 'happiness', 'happy', 'hate', 'hatred', 'haunted', 'heart', 'heartache', 'heartbreak', 'heartbroken', 'heartfelt', 'hearts', 'held', 'helpless', 'helplessness', 'hesitant', 'hesitate', 'hesitating', 'hesitation', 'hold', 'holding', 'homesick', 'hope', 'hopeful', 'hopeless', 'hopelessness', 'hoping', 'hostile', 'hostility', 'human', 'humanity', 'humility', 'hunch', 'hurt', 'hurting', 'imagination', 'imagine', 'imagined', 'imagining', 'indifference', 'indifferent', 'inner', 'insecure', 'insecurity', 'instinct', 'instinctive', 'instinctively', 'interested', 'interesting', 'intimacy', 'intimate', 'intimately', 'intrigue', 'intrigued', 'intriguing', 'intuition', 'intuitive', 'intuitively', 'irritable', 'irritated', 'irritation', 'isolated', 'isolation', 'journey', 'joy', 'joyful', 'joyous', 'kind', 'kindly', 'kindness', 'lament', 'lamented', 'lamenting', 'laugh', 'laughed', 'laughing', 'let', 'letting', 'life', 'lived', 'living', 'loneliness', 'lonely', 'lonesome', 'long', 'longing', 'lost', 'love', 'loved', 'loving', 'mad', 'marvel', 'marveled', 'marvelous', 'meet', 'meeting', 'melancholic', 'melancholy', 'merry', 'met', 'mind', 'minds', 'mirror', 'miserable', 'misery', 'moment', 'moments', 'moody', 'mourn', 'mourned', 'mourning', 'mutual', 'mutually', 'nervous', 'nervously', 'nice', 'notice', 'noticed', 'noticing', 'numb', 'numbness', 'open', 'opening', 'openness', 'optimism', 'optimistic', 'outrage', 'outraged', 'overjoyed', 'overwhelm', 'overwhelmed', 'overwhelming', 'overwhelmingly', 'pain', 'painful', 'panic', 'panicked', 'passion', 'passionate', 'passionately', 'peace', 'peaceful', 'people', 'perceive', 'perceived', 'perception', 'perceptions', 'person', 'personal', 'personally', 'pleasant', 'pleased', 'pleasure', 'poignancy', 'poignant', 'poignantly', 'presence', 'present', 'presently', 'pretty', 'pride', 'profound', 'profoundly', 'proud', 'quiet', 'quietly', 'raw', 'reality', 'reassurance', 'reassure', 'reassured', 'reassuring', 'regret', 'regretful', 'regretfully', 'regretting', 'rejected', 'rejection', 'relate', 'related', 'relating', 'relax', 'relaxed', 'relaxing', 'release', 'released', 'releasing', 'remorse', 'remorseful', 'resent', 'resentful', 'resentment', 'resonance', 'resonant', 'resonate', 'resonating', 'rest', 'rested', 'restful', 'resting', 'restless', 'restlessness', 'reveal', 'revealed', 'revealing', 'sad', 'sadly', 'sadness', 'safe', 'safety', 'scared', 'scary', 'searching', 'secure', 'security', 'seeking', 'self', 'sensation', 'sensations', 'sense', 'sensed', 'senses', 'sensing', 'sentimental', 'serene', 'serenity', 'settle', 'settled', 'settling', 'shame', 'share', 'shared', 'sharing', 'shattered', 'silence', 'silent', 'smile', 'smiled', 'smiling', 'soft', 'soften', 'softly', 'somatic', 'soothed', 'soothing', 'sorrow', 'sorrowful', 'soul', 'soulful', 'souls', 'space', 'spacious', 'spaciousness', 'spirit', 'spirits', 'spiritual', 'spiritually', 'still', 'stillness', 'stirred', 'stirring', 'stress', 'stressed', 'stressful', 'suffer', 'suffered', 'suffering', 'surface', 'surfaces', 'surfacing', 'surprise', 'surprised', 'surprising', 'sympathetic', 'sympathize', 'sympathy', 'tearful', 'tears', 'tender', 'tenderness', 'tense', 'tension', 'tentative', 'tentatively', 'terrified', 'terror', 'thankful', 'thankfully', 'thankfulness', 'thrilled', 'together', 'togetherness', 'torment', 'tormented', 'torn', 'touched', 'touching', 'tranquil', 'tranquility', 'tremble', 'trembling', 'troubled', 'troubling', 'truly', 'trust', 'trusted', 'trusting', 'trustworthy', 'turmoil', 'unaware', 'uncertain', 'uncertainty', 'uncomfortable', 'understanding', 'unease', 'uneasy', 'unhappy', 'universe', 'unsettled', 'unsettling', 'unsure', 'upset', 'vast', 'visceral', 'viscerally', 'vulnerability', 'vulnerable', 'warm', 'warmly', 'warmth', 'wary', 'weariness', 'weary', 'well', 'wistful', 'wonder', 'wondered', 'wonderful', 'wondering', 'wondrous', 'world', 'worried', 'worry', 'worrying', 'wound', 'wounded', 'wrath', 'yearn', 'yearning', 'zeal', 'zealous']

_IEP_ACT_WORDS = ['access', 'accessed', 'accessing', 'accomplish', 'accomplished', 'accomplishes', 'accomplishing', 'accomplishment', 'achieve', 'achieved', 'achievement', 'achievements', 'achieves', 'achieving', 'act', 'acting', 'action', 'actions', 'activate', 'activated', 'activates', 'activating', 'activation', 'acts', 'adapt', 'adaptation', 'adapted', 'adapting', 'adapts', 'address', 'addressed', 'addresses', 'addressing', 'adjust', 'adjusted', 'adjusting', 'adjustment', 'adjusts', 'advance', 'advanced', 'advancement', 'advances', 'advancing', 'ahead', 'aim', 'aimed', 'aiming', 'aims', 'allocate', 'allocated', 'allocation', 'application', 'applied', 'applies', 'apply', 'applying', 'arrange', 'arranged', 'arrangement', 'arrangements', 'ask', 'asked', 'asking', 'assemble', 'assembled', 'assign', 'assigned', 'assignment', 'attempt', 'attempted', 'attempting', 'attempts', 'authorize', 'authorized', 'began', 'begin', 'beginning', 'begins', 'begun', 'best', 'better', 'bolster', 'bolstered', 'break', 'breaking', 'bring', 'bringing', 'broken', 'brought', 'budget', 'build', 'building', 'builds', 'built', 'calibrate', 'calibrated', 'call', 'called', 'calling', 'campaign', 'canvass', 'canvassed', 'carried', 'carry', 'carrying', 'catalogue', 'catalogued', 'centralize', 'centralized', 'change', 'changed', 'changes', 'changing', 'channel', 'channeled', 'chart', 'check', 'checked', 'checking', 'choice', 'choices', 'choose', 'choosing', 'chose', 'chosen', 'circumvent', 'coach', 'collaborate', 'collaborated', 'collaboration', 'commission', 'commit', 'commitment', 'committed', 'compile', 'compiled', 'complete', 'completed', 'completes', 'completing', 'completion', 'conclude', 'concluded', 'concludes', 'concluding', 'configure', 'configured', 'connect', 'connected', 'connecting', 'connection', 'connections', 'consolidate', 'construct', 'constructed', 'constructing', 'constructs', 'continuation', 'continue', 'continued', 'continues', 'continuing', 'control', 'controlled', 'controlling', 'controls', 'conversion', 'convert', 'converted', 'converting', 'converts', 'coordinate', 'coordinated', 'coordination', 'craft', 'crafted', 'crafting', 'create', 'created', 'creates', 'creating', 'creation', 'customize', 'deadline', 'decide', 'decided', 'deciding', 'decision', 'decisions', 'delegate', 'delegated', 'delegation', 'deliver', 'delivered', 'delivering', 'delivers', 'delivery', 'deploy', 'deployed', 'deploying', 'deployment', 'deploys', 'design', 'designed', 'designing', 'designs', 'develop', 'developed', 'developing', 'development', 'develops', 'did', 'direct', 'directed', 'directing', 'dive', 'diving', 'do', 'does', 'doing', 'done', 'draft', 'drafting', 'edit', 'editing', 'effort', 'efforts', 'eliminate', 'eliminated', 'elimination', 'employ', 'employed', 'employing', 'employs', 'enable', 'enabled', 'end', 'ended', 'ending', 'ends', 'enforce', 'enforced', 'enforcement', 'engage', 'engaged', 'engagement', 'engineer', 'engineering', 'enroll', 'enrolled', 'enrollment', 'equip', 'equipped', 'establish', 'established', 'establishes', 'establishing', 'establishment', 'execute', 'executed', 'executes', 'executing', 'execution', 'expedite', 'facilitate', 'facilitated', 'facilitation', 'finalize', 'finalized', 'finish', 'finished', 'finishes', 'finishing', 'fix', 'fixed', 'fixes', 'fixing', 'focus', 'focused', 'focusing', 'form', 'formation', 'formed', 'forming', 'forms', 'forward', 'fund', 'funded', 'funding', 'gather', 'gathered', 'gathering', 'generate', 'generated', 'generates', 'generating', 'generation', 'give', 'given', 'gives', 'giving', 'go', 'goal', 'goals', 'goes', 'going', 'gone', 'grew', 'grow', 'growing', 'growth', 'handle', 'handled', 'handles', 'handling', 'help', 'helped', 'helping', 'helps', 'hire', 'hired', 'hiring', 'implement', 'implementation', 'implemented', 'implementing', 'implements', 'improve', 'improved', 'improvement', 'improving', 'increase', 'increased', 'increasing', 'initiate', 'initiated', 'initiates', 'initiating', 'initiation', 'inspect', 'inspection', 'install', 'installation', 'installed', 'integrate', 'integrated', 'integration', 'intervene', 'intervention', 'invest', 'invested', 'investment', 'iterate', 'iterated', 'iteration', 'labor', 'labored', 'laboring', 'launch', 'launched', 'launches', 'launching', 'lead', 'leader', 'leadership', 'leading', 'learn', 'learned', 'learning', 'led', 'made', 'maintain', 'maintained', 'maintenance', 'make', 'makes', 'making', 'manage', 'managed', 'management', 'manager', 'managing', 'map', 'mapped', 'mapping', 'migrate', 'migrated', 'migration', 'mobilize', 'mobilized', 'modification', 'modified', 'modifies', 'modify', 'modifying', 'monitor', 'monitored', 'monitoring', 'move', 'moved', 'movement', 'movements', 'moves', 'moving', 'navigate', 'navigated', 'navigation', 'negotiate', 'negotiated', 'negotiation', 'objective', 'objectives', 'obtain', 'obtained', 'offer', 'offered', 'offering', 'onward', 'operate', 'operated', 'operates', 'operating', 'operation', 'operations', 'optimization', 'optimize', 'optimized', 'orchestrate', 'outline', 'outlined', 'outsource', 'overhaul', 'oversee', 'participate', 'participated', 'participation', 'perform', 'performance', 'performed', 'performing', 'performs', 'permit', 'pilot', 'piloted', 'pioneer', 'pioneered', 'pitch', 'pitched', 'plan', 'planned', 'planning', 'plans', 'power', 'powerful', 'powerfully', 'practice', 'practiced', 'preparation', 'prepare', 'prepared', 'priorities', 'prioritize', 'prioritized', 'priority', 'proceed', 'proceeded', 'proceeding', 'proceeds', 'produce', 'produced', 'produces', 'producing', 'production', 'productive', 'program', 'programmed', 'progress', 'progressed', 'progresses', 'progressing', 'progression', 'promote', 'promoted', 'promotion', 'provide', 'provided', 'provides', 'providing', 'pursue', 'pursued', 'pursuit', 'push', 'pushed', 'pushes', 'pushing', 'ran', 'reaching', 'rebuild', 'rebuilt', 'recruit', 'recruited', 'recruitment', 'redesign', 'reduce', 'reduced', 'reduction', 'reform', 'reformed', 'refurbish', 'register', 'registered', 'regulate', 'regulated', 'regulation', 'reinforce', 'reinforced', 'relocate', 'relocated', 'remedy', 'removal', 'remove', 'removed', 'renovate', 'renovated', 'repair', 'repaired', 'replace', 'replaced', 'replacement', 'replicate', 'replicated', 'request', 'requested', 'rescue', 'rescued', 'resolution', 'resolve', 'resolved', 'resolves', 'resolving', 'restoration', 'restore', 'restored', 'restructure', 'restructured', 'retrieve', 'retrieved', 'revamp', 'revise', 'revised', 'revision', 'run', 'running', 'runs', 'schedule', 'scheduled', 'select', 'selected', 'selection', 'send', 'sending', 'sent', 'serve', 'served', 'serving', 'ship', 'shipped', 'simplified', 'simplify', 'solution', 'solutions', 'solve', 'solved', 'solves', 'solving', 'start', 'started', 'starting', 'starts', 'step', 'stepped', 'stepping', 'steps', 'stop', 'stopped', 'stopping', 'streamline', 'streamlined', 'strive', 'strived', 'striving', 'strove', 'struggle', 'struggled', 'struggles', 'struggling', 'submission', 'submit', 'submitted', 'succeed', 'succeeded', 'succeeds', 'success', 'successful', 'successfully', 'supplied', 'supply', 'support', 'supported', 'supporting', 'survey', 'surveyed', 'sustain', 'sustainability', 'sustained', 'tackle', 'tackled', 'tackles', 'tackling', 'take', 'taken', 'takes', 'taking', 'target', 'targets', 'task', 'tasked', 'tasks', 'taught', 'teach', 'teaching', 'train', 'trained', 'training', 'transform', 'transformation', 'transformed', 'transforming', 'transforms', 'transition', 'transitioned', 'tried', 'tries', 'trigger', 'triggered', 'triggering', 'triggers', 'troubleshoot', 'try', 'trying', 'turn', 'turned', 'turning', 'upgrade', 'upgraded', 'use', 'used', 'uses', 'using', 'utilize', 'utilized', 'utilizes', 'utilizing', 'visit', 'visited', 'visiting', 'volunteer', 'volunteered', 'went', 'win', 'winner', 'winning', 'won', 'work', 'worked', 'working', 'works', 'write', 'writes', 'writing', 'written', 'wrote']

_IEP_OVERLAPS = {
    'INT_AFF': ['notice', 'noticed', 'noticing', 'understanding'],
    'INT_ACT': ['conclude', 'step', 'steps'],
    'AFF_ACT': [],
}

_IEP_COUNTS = {'INT': 616, 'AFF': 599, 'ACT': 682, 'TOTAL': 1897}

IEP_DICT = {
    "INT":      set(_IEP_INT_WORDS),
    "AFF":      set(_IEP_AFF_WORDS),
    "ACT":      set(_IEP_ACT_WORDS),
    "overlaps": {k: set(v) for k, v in _IEP_OVERLAPS.items()},
    "counts":   _IEP_COUNTS,
}

# =============================================================================
# PAGE CONFIG
# =============================================================================
st.set_page_config(
    page_title="SYN-IQ Mapper Analyzer V49",
    page_icon="🗺️",
    layout="wide"
)

# =============================================================================
# PASSWORD PROTECTION
# =============================================================================
def check_password():
    """Password gate with persistent authentication."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.query_params.get("auth") == "granted":
        st.session_state.authenticated = True

    if st.session_state.authenticated:
        return True

    st.markdown("""
    <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
         color: white; padding: 2rem; border-radius: 10px; text-align: center;
         margin-bottom: 1rem; border: 1px solid #e94560;">
        <h1 style="color: #e94560;">🗺️ SYN-IQ Mapper Analyzer</h1>
        <p style="color: #a0a0a0;">Authorized Access Only</p>
    </div>
    """, unsafe_allow_html=True)

    password = st.text_input("Enter password:", type="password")

    if password:
        try:
            correct = st.secrets["app_password"]
        except (FileNotFoundError, KeyError, AttributeError):
            correct = "SYNIQ2026"

        if password == correct:
            st.session_state.authenticated = True
            st.query_params["auth"] = "granted"
            st.rerun()
        else:
            st.error("❌ Incorrect password.")

    st.markdown("""
    <div style="text-align: center; color: #a0a0a0; padding: 1rem; font-size: 0.8rem;">
        <em>SYNINT Team — Tennessee 🎹 CUZ Partnership</em>
    </div>
    """, unsafe_allow_html=True)
    return False

if not check_password():
    st.stop()

# =============================================================================
# STYLES
# =============================================================================
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        color: white;
        padding: 2rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 1rem;
        border: 1px solid #e94560;
    }
    .main-header h1 { color: #e94560; margin: 0; }
    .main-header .subtitle { color: #a0a0a0; font-size: 0.9rem; }
    .stats-box {
        background: #16213e;
        color: white;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        border: 1px solid #0f3460;
    }
    .stats-box h3 { color: #e94560; margin: 0; }
    .node-analysis {
        background: #1a1a2e;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #e94560;
    }
    .dict-badge {
        background: #0f3460;
        color: #e94560;
        padding: 0.2rem 0.6rem;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# HEADER
# =============================================================================
st.markdown("""
<div class="main-header">
    <h1>🗺️ SYN-IQ Mapper Analyzer</h1>
    <p class="subtitle">Topological Data Analysis for AI Response Profiles</p>
    <p class="subtitle">KeplerMapper + IEP Framework &nbsp;|&nbsp;
        <span class="dict-badge">IEP Dictionary V3 — 1,897 words · embedded</span> &nbsp;|&nbsp;
        <span class="dict-badge">V49</span>
    </p>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# CHECK MAPPER DEPENDENCIES
# =============================================================================
@st.cache_resource
def check_and_import():
    try:
        import kmapper as km
        from sklearn.cluster import DBSCAN
        from sklearn.preprocessing import StandardScaler
        from sklearn.decomposition import PCA
        return True, km, DBSCAN, StandardScaler, PCA
    except ImportError:
        return False, None, None, None, None

deps_ok, km, DBSCAN, StandardScaler, PCA = check_and_import()

if not deps_ok:
    st.error("❌ Missing dependencies! Make sure `kmapper` and `scikit-learn` are in requirements.txt")
    st.code("kmapper\nscikit-learn", language="text")
    st.stop()

st.success("✅ All dependencies loaded!")

# =============================================================================
# IEP SCORING FUNCTIONS
# =============================================================================

def tokenize(text: str) -> list:
    """Lowercase, strip punctuation, split on whitespace."""
    text = text.lower()
    text = re.sub(r"[^a-z\s'-]", " ", text)
    return [w.strip("'-") for w in text.split() if w.strip("'-")]


def score_text_iep(text: str) -> dict:
    """
    Score a single text string using the embedded IEP Dictionary V3.
    Returns int_pct, aff_pct, act_pct, counts, and matched word Counters.
    """
    if not text:
        return {k: 0 for k in ["int_count", "aff_count", "act_count",
                                "total_words", "int_pct", "aff_pct", "act_pct",
                                "matched_int", "matched_aff", "matched_act"]}

    tokens = tokenize(text)
    total = len(tokens)
    if total == 0:
        return {k: 0 for k in ["int_count", "aff_count", "act_count",
                                "total_words", "int_pct", "aff_pct", "act_pct",
                                "matched_int", "matched_aff", "matched_act"]}

    int_hits = [t for t in tokens if t in IEP_DICT["INT"]]
    aff_hits = [t for t in tokens if t in IEP_DICT["AFF"]]
    act_hits = [t for t in tokens if t in IEP_DICT["ACT"]]

    return {
        "int_count":   len(int_hits),
        "aff_count":   len(aff_hits),
        "act_count":   len(act_hits),
        "total_words": total,
        "int_pct":     round(100 * len(int_hits) / total, 2),
        "aff_pct":     round(100 * len(aff_hits) / total, 2),
        "act_pct":     round(100 * len(act_hits) / total, 2),
        "matched_int": Counter(int_hits),
        "matched_aff": Counter(aff_hits),
        "matched_act": Counter(act_hits),
    }


def score_dataframe_iep(df: pd.DataFrame, text_col: str) -> pd.DataFrame:
    """Score every row's text and add/overwrite IEP columns."""
    scores = df[text_col].fillna("").apply(score_text_iep)
    df = df.copy()
    for col in ["int_pct", "aff_pct", "act_pct", "total_words",
                "int_count", "aff_count", "act_count"]:
        df[col] = scores.apply(lambda s: s[col])
    return df


# =============================================================================
# SESSION STATE INIT
# =============================================================================
if "mapper_results_html" not in st.session_state:
    st.session_state.mapper_results_html = None
if "mapper_analysis_data" not in st.session_state:
    st.session_state.mapper_analysis_data = None

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def parse_embeddings(df):
    embeddings, valid_indices = [], []
    for idx, row in df.iterrows():
        try:
            emb_str = row.get('embedding', '[]')
            if pd.isna(emb_str) or emb_str in ('[]', ''):
                continue
            emb = json.loads(emb_str) if isinstance(emb_str, str) else emb_str
            if isinstance(emb, list) and len(emb) > 0:
                embeddings.append(emb)
                valid_indices.append(idx)
        except (json.JSONDecodeError, TypeError):
            continue
    return (np.array(embeddings), valid_indices) if embeddings else (np.array([]), [])


def build_iep_features(df):
    """Build 12–15D feature matrix from IEP columns."""
    has_italic_cols = 'has_italics' in df.columns
    features, valid_indices = [], []
    for idx, row in df.iterrows():
        try:
            fv = [
                float(row.get('int_pct', 0) or 0),
                float(row.get('aff_pct', 0) or 0),
                float(row.get('act_pct', 0) or 0),
                float(row.get('vader_compound', 0) or 0),
                float(row.get('vader_pos', 0) or 0),
                float(row.get('vader_neg', 0) or 0),
                float(row.get('vader_neu', 0) or 0),
                float(row.get('flesch_kincaid', 0) or 0),
                float(row.get('flesch_ease', 0) or 0) if 'flesch_ease' in row else 0,
                float(row.get('ttr', 0) or 0),
                float(row.get('total_words', 0) or 0),
                float(row.get('unique_words', 0) or 0) if 'unique_words' in row else 0,
            ]
            if has_italic_cols:
                fv.extend([
                    float(row.get('has_italics', 0) or 0),
                    float(row.get('italic_count', 0) or 0),
                    float(row.get('italic_density', 0) or 0),
                ])
            features.append(fv)
            valid_indices.append(idx)
        except (ValueError, TypeError):
            continue
    return np.array(features), valid_indices


def run_mapper_analysis(data, df, valid_indices, n_cubes, overlap, eps, min_samples, projection_type):
    mapper = km.KeplerMapper(verbose=0)
    if projection_type == "PCA (2D)":
        projected = mapper.fit_transform(data, projection=PCA(n_components=2))
    elif projection_type == "Sum":
        projected = mapper.fit_transform(data, projection="sum")
    elif projection_type == "Mean":
        projected = mapper.fit_transform(data, projection="mean")
    elif projection_type == "AFF% Lens":
        subset = df.iloc[valid_indices]
        projected = subset['aff_pct'].values.reshape(-1, 1)
    else:
        projected = mapper.fit_transform(data, projection=PCA(n_components=2))
    cover = km.Cover(n_cubes=n_cubes, perc_overlap=overlap)
    graph = mapper.map(projected, data, cover=cover,
                       clusterer=DBSCAN(eps=eps, min_samples=min_samples))
    return mapper, graph


def analyze_graph(graph, df, valid_indices):
    subset = df.iloc[valid_indices].reset_index(drop=True)
    analysis = {"n_nodes": len(graph['nodes']), "n_edges": len(graph['links']), "nodes": {}}
    cold_nodes, hot_nodes = set(), set()
    for node_id, indices in graph['nodes'].items():
        node_data = subset.iloc[indices]
        temps  = node_data['temperature'].value_counts().to_dict() if 'temperature' in node_data.columns else {}
        agents = node_data['agent'].value_counts().to_dict() if 'agent' in node_data.columns else {}
        analysis["nodes"][node_id] = {
            "size":    len(indices),
            "temps":   temps,
            "agents":  agents,
            "avg_int": node_data['int_pct'].mean() if 'int_pct' in node_data.columns else 0,
            "avg_aff": node_data['aff_pct'].mean() if 'aff_pct' in node_data.columns else 0,
            "avg_act": node_data['act_pct'].mean() if 'act_pct' in node_data.columns else 0,
        }
        if 'COLD' in temps: cold_nodes.add(node_id)
        if 'HOT'  in temps or 'FIRE' in temps: hot_nodes.add(node_id)
    analysis["cold_nodes"]    = cold_nodes
    analysis["hot_nodes"]     = hot_nodes
    analysis["overlap_nodes"] = cold_nodes & hot_nodes
    analysis["cold_only"]     = cold_nodes - hot_nodes
    analysis["hot_only"]      = hot_nodes - cold_nodes
    return analysis


# =============================================================================
# SIDEBAR
# =============================================================================
st.sidebar.markdown("## ⚙️ Configuration")

c = IEP_DICT["counts"]
st.sidebar.success(
    f"📖 IEP Dict V3 — **embedded**  \n"
    f"INT {c['INT']} · AFF {c['AFF']} · ACT {c['ACT']}  \n"
    f"Total: {c['TOTAL']} words"
)

uploaded_file = st.sidebar.file_uploader("📁 Upload Data (CSV or JSON)", type=['csv', 'json'])

st.sidebar.markdown("---")
st.sidebar.markdown("### Data Source")

feature_options = [
    "IEP V3 — live score from text (recommended)",
    "IEP — pre-scored columns",
    "Embeddings (pre-computed)",
    "SBERT Embeddings (from text)",
]
use_iep = st.sidebar.radio("Feature Type:", feature_options, index=0)

text_col_choice = "response_text"
if "live score" in use_iep:
    text_col_choice = st.sidebar.text_input(
        "Text column name:", value="response_text",
        help="Column containing the raw response text to score with IEP V3."
    )

st.sidebar.markdown("---")
st.sidebar.markdown("### Mapper Parameters")

n_cubes     = st.sidebar.slider("N Cubes (cover resolution)", 5, 30, 10)
overlap     = st.sidebar.slider("Overlap %", 0.1, 0.9, 0.5)
eps         = st.sidebar.slider("DBSCAN eps", 0.1, 5.0, 2.0, step=0.1,
    help="Higher values for larger/higher-dim datasets. Try 1.5–3.0 for 12D IEP features.")
min_samples = st.sidebar.slider("DBSCAN min_samples", 2, 10, 3)

projection_type = st.sidebar.selectbox(
    "Projection / Lens",
    ["PCA (2D)", "Sum", "Mean", "AFF% Lens"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Visualization")
color_by = st.sidebar.selectbox(
    "Color nodes by:",
    ["aff_pct", "int_pct", "act_pct", "vader_compound", "temperature", "agent",
     "has_italics", "italic_count", "italic_density"]
)

if st.session_state.get("_sidebar_msg_json_text"):
    st.sidebar.success("✅ JSON loaded with response text for embeddings")
if "_sidebar_msg_record_count" in st.session_state:
    st.sidebar.info(f"Loaded {st.session_state['_sidebar_msg_record_count']} records from JSON")

# =============================================================================
# TABS
# =============================================================================
tab_main, tab_dict, tab_score = st.tabs(["🗺️ Mapper Analyzer", "📖 Dictionary Explorer", "🧪 Score Text"])

# ─────────────────────────────────────────────
# TAB 2: DICTIONARY EXPLORER
# ─────────────────────────────────────────────
with tab_dict:
    st.markdown("## 📖 IEP Dictionary V3 Explorer")
    st.caption("All 1,897 words are embedded in this script — no external file needed.")

    c = IEP_DICT["counts"]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("INT words",   c["INT"])
    col2.metric("AFF words",   c["AFF"])
    col3.metric("ACT words",   c["ACT"])
    col4.metric("TOTAL words", c["TOTAL"])

    search_term = st.text_input("🔍 Search dictionary", placeholder="e.g. 'feel' or 'analyz'")

    for category, label in [("INT", "🔵 INTELLECTUAL"), ("AFF", "❤️ AFFECTIVE"), ("ACT", "🟢 ACTION")]:
        words = sorted(IEP_DICT[category])
        if search_term:
            words = [w for w in words if search_term.lower() in w]
        with st.expander(f"{label} — {len(words)} words {'(filtered)' if search_term else ''}"):
            st.write(", ".join(words) if words else "_No matches_")

    st.markdown("### 🔀 Cross-category Overlaps")
    for k, v in _IEP_OVERLAPS.items():
        if v:
            st.write(f"**{k}** ({len(v)} words): {', '.join(sorted(v))}")
        else:
            st.write(f"**{k}**: _none_")

# ─────────────────────────────────────────────
# TAB 3: SCORE TEXT
# ─────────────────────────────────────────────
with tab_score:
    st.markdown("## 🧪 Score a Single Response")
    st.markdown("Paste any AI response to get its IEP V3 profile instantly.")

    sample_text = st.text_area("Response text:", height=200,
        placeholder="Paste an AI response here…")

    if st.button("Score Text", type="primary") and sample_text.strip():
        result = score_text_iep(sample_text)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("INT%",  f"{result['int_pct']:.1f}%", f"{result['int_count']} hits")
        col2.metric("AFF%",  f"{result['aff_pct']:.1f}%", f"{result['aff_count']} hits")
        col3.metric("ACT%",  f"{result['act_pct']:.1f}%", f"{result['act_count']} hits")
        col4.metric("Words", result["total_words"])

        st.markdown("#### Matched words")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("**🔵 INT**")
            st.write(", ".join(f"{w}({n})" for w, n in result["matched_int"].most_common(20)) or "_none_")
        with c2:
            st.markdown("**❤️ AFF**")
            st.write(", ".join(f"{w}({n})" for w, n in result["matched_aff"].most_common(20)) or "_none_")
        with c3:
            st.markdown("**🟢 ACT**")
            st.write(", ".join(f"{w}({n})" for w, n in result["matched_act"].most_common(20)) or "_none_")

# ─────────────────────────────────────────────
# TAB 1: MAIN MAPPER ANALYZER
# ─────────────────────────────────────────────
with tab_main:

    if uploaded_file is not None:
        # ---- LOAD DATA ----
        if uploaded_file.name.endswith('.json'):
            raw_data = json.loads(uploaded_file.read().decode('utf-8'))
            df = pd.DataFrame(raw_data)
            rename_map = {}
            if 'full_int_pct' in df.columns and 'int_pct' not in df.columns:
                rename_map.update({'full_int_pct': 'int_pct', 'full_aff_pct': 'aff_pct',
                                   'full_act_pct': 'act_pct', 'full_vader_compound': 'vader_compound',
                                   'full_total_words': 'total_words'})
            if 'condition' in df.columns and 'temperature' not in df.columns:
                rename_map['condition'] = 'temperature'
            if rename_map:
                df = df.rename(columns=rename_map)
            if 'has_italics' in df.columns:
                df['has_italics'] = df['has_italics'].astype(int)
            if 'q2_response' in df.columns:
                df['response_text'] = df['q2_response']
                st.session_state["_sidebar_msg_json_text"] = True
            st.session_state["_sidebar_msg_record_count"] = len(df)
        else:
            df = pd.read_csv(uploaded_file)

        # ---- V3 LIVE SCORING ----
        if "live score" in use_iep:
            if text_col_choice in df.columns:
                with st.spinner(f"🔬 Scoring with IEP Dictionary V3 ({text_col_choice})…"):
                    df = score_dataframe_iep(df, text_col_choice)
                st.success(f"✅ IEP V3 scoring applied to `{text_col_choice}`")
            else:
                st.warning(
                    f"⚠️ Column `{text_col_choice}` not found. "
                    f"Available: {list(df.columns[:10])}. "
                    f"Falling back to pre-scored columns."
                )

        # ---- CONDITION FILTER ----
        if 'temperature' in df.columns:
            all_conditions = sorted(df['temperature'].unique().tolist())
            st.sidebar.markdown("---")
            st.sidebar.markdown("### 🎯 Condition Filter")
            filter_conditions = st.sidebar.multiselect(
                "Include conditions:", all_conditions, default=all_conditions)
            if filter_conditions and len(filter_conditions) < len(all_conditions):
                df = df[df['temperature'].isin(filter_conditions)].reset_index(drop=True)
                st.sidebar.success(f"✅ Filtered to {len(df)} records")

        # ---- AGENT FILTER ----
        if 'agent' in df.columns:
            all_agents = sorted(df['agent'].unique().tolist())
            filter_agents = st.sidebar.multiselect("Include agents:", all_agents, default=all_agents)
            if filter_agents and len(filter_agents) < len(all_agents):
                df = df[df['agent'].isin(filter_agents)].reset_index(drop=True)
                st.sidebar.success(f"✅ Filtered to {len(df)} records")

        # ---- STATS BOXES ----
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f'<div class="stats-box"><h3>{len(df)}</h3><p>Records</p></div>', unsafe_allow_html=True)
        with col2:
            n_agents = df['agent'].nunique() if 'agent' in df.columns else 0
            st.markdown(f'<div class="stats-box"><h3>{n_agents}</h3><p>Agents</p></div>', unsafe_allow_html=True)
        with col3:
            n_temps = df['temperature'].nunique() if 'temperature' in df.columns else 0
            st.markdown(f'<div class="stats-box"><h3>{n_temps}</h3><p>Temperatures</p></div>', unsafe_allow_html=True)
        with col4:
            feature_dim = "12D" if "IEP" in use_iep or "live" in use_iep else "384D"
            st.markdown(f'<div class="stats-box"><h3>{feature_dim}</h3><p>Features</p></div>', unsafe_allow_html=True)

        st.markdown("---")

        # ---- PREVIEW ----
        with st.expander("📋 Preview Data"):
            preview_cols = ['agent', 'temperature', 'question_id', 'int_pct', 'aff_pct', 'act_pct', 'vader_compound']
            preview_cols = [c for c in preview_cols if c in df.columns]
            st.dataframe(df[preview_cols].head(20))

        # ---- IEP DISTRIBUTION ----
        if all(c in df.columns for c in ['int_pct', 'aff_pct', 'act_pct']):
            with st.expander("📊 IEP V3 Score Distribution"):
                dist_df = df[['int_pct', 'aff_pct', 'act_pct']].describe().T
                dist_df.columns = ["count", "mean", "std", "min", "25%", "50%", "75%", "max"]
                st.dataframe(dist_df.style.format("{:.2f}"))

        # ---- RUN MAPPER ----
        if st.button("🚀 Run Mapper Analysis", type="primary"):
            with st.spinner("Preparing data..."):
                if "live score" in use_iep or "pre-scored" in use_iep:
                    data, valid_indices = build_iep_features(df)
                    if len(data) > 0:
                        scaler = StandardScaler()
                        data = scaler.fit_transform(data)
                elif "SBERT" in use_iep:
                    try:
                        from sentence_transformers import SentenceTransformer
                        model = SentenceTransformer('all-MiniLM-L6-v2')
                        texts = df['response_text'].fillna('').tolist()
                        valid_indices = [i for i, t in enumerate(texts) if t.strip()]
                        data = model.encode([texts[i] for i in valid_indices])
                        st.success(f"✅ SBERT embeddings: {data.shape}")
                    except ImportError:
                        st.error("❌ sentence-transformers not installed.")
                        st.stop()
                else:
                    data, valid_indices = parse_embeddings(df)

                if len(data) == 0:
                    st.error("❌ No valid data found! Check your data format.")
                    st.stop()
                st.success(f"✅ {len(data)} data points · {data.shape[1]} dimensions")

            with st.spinner("Running Mapper algorithm..."):
                mapper, graph = run_mapper_analysis(
                    data, df, valid_indices,
                    n_cubes, overlap, eps, min_samples, projection_type
                )

            if len(graph['nodes']) == 0:
                st.error("❌ Mapper produced 0 nodes. Adjust DBSCAN eps / min_samples.")
                st.stop()

            with st.spinner("Analyzing graph..."):
                analysis = analyze_graph(graph, df, valid_indices)

            with st.spinner("Generating visualization..."):
                subset = df.iloc[valid_indices].reset_index(drop=True)
                if color_by in subset.columns:
                    if subset[color_by].dtype == 'object':
                        cats = subset[color_by].unique().tolist()
                        color_values = subset[color_by].map({c: i for i, c in enumerate(cats)}).values
                    else:
                        color_values = subset[color_by].values
                else:
                    color_values = subset['aff_pct'].values if 'aff_pct' in subset.columns else np.zeros(len(subset))

                if 'temperature' in subset.columns and 'agent' in subset.columns:
                    if 'question_id' in subset.columns:
                        tooltips = np.array([
                            f"{r['agent']} | {r['temperature']} | {r.get('question_id', '')}"
                            for _, r in subset.iterrows()
                        ])
                    else:
                        tooltips = np.array([f"{r['agent']} | {r['temperature']}" for _, r in subset.iterrows()])
                else:
                    tooltips = subset.index.astype(str).values

                with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as tmp:
                    mapper.visualize(
                        graph,
                        path_html=tmp.name,
                        title="SYN-IQ Mapper Analysis (IEP V3)",
                        color_values=color_values,
                        color_function_name=color_by,
                        custom_tooltips=tooltips
                    )
                    with open(tmp.name) as f:
                        html_content = f.read()
                    os.unlink(tmp.name)

                # Prevent iframe navigation on node click
                nav_fix = """
<script>
document.addEventListener('DOMContentLoaded', function() {
    document.addEventListener('click', function(e) {
        var a = e.target.closest('a');
        if (a) { e.preventDefault(); e.stopPropagation(); }
    }, true);
    document.querySelectorAll('a[href]').forEach(function(l) {
        l.setAttribute('href', 'javascript:void(0)');
        l.style.cursor = 'pointer';
    });
});
</script>
"""
                html_content = html_content.replace('</body>', nav_fix + '</body>')

            st.session_state.mapper_results_html = html_content
            st.session_state.mapper_analysis_data = analysis
            st.rerun()

        # ---- DISPLAY RESULTS ----
        if st.session_state.mapper_analysis_data is not None:
            analysis = st.session_state.mapper_analysis_data

            st.markdown("## 📊 Results")
            col1, col2 = st.columns(2)
            col1.metric("Nodes", analysis["n_nodes"])
            col2.metric("Edges", analysis["n_edges"])

            st.markdown("### 🌡️ Temperature Separation")
            col1, col2, col3 = st.columns(3)
            col1.metric("COLD-only nodes", len(analysis["cold_only"]))
            col2.metric("HOT-only nodes",  len(analysis["hot_only"]))
            col3.metric("Mixed nodes",     len(analysis["overlap_nodes"]))

            if analysis["cold_only"] and analysis["hot_only"]:
                st.success("✅ **COLD and HOT show TOPOLOGICAL SEPARATION!**")
            elif analysis["overlap_nodes"] and not (analysis["cold_only"] or analysis["hot_only"]):
                st.warning("⚠️ **COLD and HOT are MIXED**")
            else:
                st.info("🔶 **Partial separation**")

            st.markdown("### 🔬 Node Analysis")
            for node_id, node_info in analysis["nodes"].items():
                with st.expander(f"Node {node_id} ({node_info['size']} points)"):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write("**Temperatures:**", node_info["temps"])
                        st.write("**Agents:**",       node_info["agents"])
                    with c2:
                        st.write(f"**Avg INT%:** {node_info['avg_int']:.1f}")
                        st.write(f"**Avg AFF%:** {node_info['avg_aff']:.1f}")
                        st.write(f"**Avg ACT%:** {node_info['avg_act']:.1f}")

            st.markdown("### 🖼️ Visualization")
            if st.session_state.mapper_results_html:
                st.download_button(
                    "📥 Download Mapper HTML",
                    st.session_state.mapper_results_html,
                    file_name="syniq_mapper_v4_output.html",
                    mime="text/html"
                )
                st.components.v1.html(st.session_state.mapper_results_html, height=800, scrolling=True)

    else:
        st.info("👆 Upload a SYN-IQ CSV or JSON file to begin analysis.")
        st.markdown("""
### Expected Data Format

**CSV** should include: `agent`, `temperature`, `int_pct`, `aff_pct`, `act_pct`, `vader_compound`
— or any column with raw response text (set the column name in the sidebar).

**JSON** (Italics Experiment): auto-extracts `q2_response` → `response_text`.

**NEW in V4:** Select *"IEP V3 — live score from text"* to score raw responses on-the-fly
using the embedded 1,897-word dictionary. Pre-scored columns still fully supported.
        """)

# =============================================================================
# FOOTER
# =============================================================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #a0a0a0; padding: 1rem;">
    <strong>SYN-IQ Mapper Analyzer V49</strong><br>
    KeplerMapper + IEP Dictionary V3 — 1,897 words (embedded)<br>
    Node tooltips: Agent | Temperature | Question ID<br>
    <em>SYNINT Team — Tennessee 🎹 CUZ Partnership — March 2026</em>
</div>
""", unsafe_allow_html=True)
