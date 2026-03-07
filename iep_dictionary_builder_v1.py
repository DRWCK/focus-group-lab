"""
IEP Dictionary Builder V1
Living Vocabulary Instrument for SYN-IQ

PURPOSE: Drop any number of harvester CSVs. Surface words not in the current
         IEP dictionary, ranked by frequency. Classify candidates into
         INT / AFF / ACT. Track progress toward a new dictionary version.
         When threshold is reached → export IEP V_next JSON.

SYNINT Team — March 2026
Tennessee 🎹 CUZ Partnership
"""

import streamlit as st
import pandas as pd
import re
import json
from collections import Counter
from datetime import datetime

st.set_page_config(
    page_title="IEP Dictionary Builder V1",
    page_icon="📖",
    layout="wide"
)

# =============================================================================
# STYLES — match SYN-IQ aesthetic
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
    .stat-gap .num { color: #ffaa00; }
    .stat-total .num { color: #aaa; }

    .word-card {
        background: #0f0f1a; border: 1px solid #1a1a3e;
        border-radius: 6px; padding: 0.8rem 1rem;
        margin: 4px 0; display: flex;
        align-items: center; justify-content: space-between;
    }
    .word-card .word { font-family: 'JetBrains Mono', monospace; font-size: 1rem; color: #fff; }
    .word-card .freq { color: #555; font-size: 0.8rem; font-family: 'JetBrains Mono', monospace; }
    .word-card .sources { color: #444; font-size: 0.75rem; }

    .progress-bar-outer {
        background: #1a1a2e; border-radius: 20px;
        height: 12px; width: 100%; margin: 0.5rem 0;
        overflow: hidden;
    }
    .progress-bar-inner {
        height: 100%; border-radius: 20px;
        background: linear-gradient(90deg, #00ff88, #00ccff);
        transition: width 0.5s ease;
    }
    .threshold-badge {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.1rem; font-weight: 700;
    }
    .ready { color: #00ff88; }
    .not-ready { color: #ffaa00; }

    .section-header {
        font-family: 'JetBrains Mono', monospace;
        color: #00ff88; font-size: 0.85rem;
        letter-spacing: 0.15em; text-transform: uppercase;
        border-bottom: 1px solid #1a1a3e;
        padding-bottom: 0.5rem; margin: 1.5rem 0 1rem 0;
    }

    .int-tag { background: #0a1a3e; color: #4488ff; padding: 2px 8px; border-radius: 3px; font-size: 0.75rem; font-weight: 700; }
    .aff-tag { background: #3e0a1a; color: #ff4466; padding: 2px 8px; border-radius: 3px; font-size: 0.75rem; font-weight: 700; }
    .act-tag { background: #0a3e1a; color: #00ff88; padding: 2px 8px; border-radius: 3px; font-size: 0.75rem; font-weight: 700; }
    .rej-tag { background: #2a2a2a; color: #555; padding: 2px 8px; border-radius: 3px; font-size: 0.75rem; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# EMBEDDED IEP DICTIONARY V3
# =============================================================================
IEP_INT = set(['ability', 'absolute', 'absolutely', 'abstract', 'abstraction', 'accuracy', 'accurate', 'algorithm', 'algorithmic', 'allows', 'although', 'always', 'ambiguity', 'ambiguous', 'analogous', 'analogously', 'analogy', 'analysis', 'analytical', 'analyze', 'annotate', 'annotated', 'answer', 'appear', 'appeared', 'appears', 'appraisal', 'appraise', 'appraised', 'approach', 'approaches', 'approximate', 'architecture', 'argue', 'argued', 'argues', 'arguing', 'argument', 'arguments', 'assert', 'asserted', 'assertion', 'assertions', 'assess', 'assessment', 'assume', 'assumed', 'assumes', 'assuming', 'assumption', 'assumptions', 'axiom', 'axiomatic', 'basis', 'because', 'bias', 'biased', 'boundaries', 'boundary', 'but', 'calculate', 'calculation', 'categorical', 'categorically', 'categories', 'categorize', 'category', 'causal', 'causally', 'causation', 'cause', 'caused', 'causes', 'certain', 'certainly', 'certitude', 'challenge', 'challenges', 'circumscribe', 'claim', 'claimed', 'claims', 'clarify', 'clarity', 'classical', 'classification', 'classify', 'clear', 'cogent', 'cogently', 'cognition', 'cognitive', 'coherence', 'coherent', 'coherently', 'communication', 'compare', 'comparison', 'complex', 'complexity', 'comprehend', 'comprehension', 'computation', 'computational', 'compute', 'conceivable', 'conceive', 'conceived', 'concept', 'concepts', 'conceptual', 'conceptualize', 'conceptually', 'conclude', 'conclusion', 'conclusions', 'confirm', 'confirmation', 'conjecture', 'conjectured', 'conscious', 'consequence', 'consequences', 'consider', 'consideration', 'consistency', 'consistent', 'consistently', 'construe', 'construed', 'context', 'contradict', 'contradiction', 'contradictory', 'contrast', 'correlate', 'correlated', 'correlation', 'could', 'counterargument', 'counterexample', 'counterpoint', 'criteria', 'criterion', 'data', 'debatable', 'debate', 'debated', 'deconstruct', 'deconstructed', 'deconstruction', 'deduce', 'deduction', 'define', 'defined', 'definite', 'definitely', 'definition', 'definitive', 'definitively', 'delineate', 'delineated', 'demarcate', 'demarcated', 'demonstrate', 'demonstration', 'derivation', 'derive', 'derived', 'derives', 'describe', 'described', 'describing', 'description', 'determination', 'determine', 'diagnose', 'diagnosed', 'diagnosis', 'diagnostic', 'differ', 'difference', 'differences', 'different', 'differentiate', 'differs', 'discern', 'discerned', 'discernible', 'disprove', 'disproven', 'dissect', 'dissected', 'distinguish', 'effect', 'effects', 'elaborate', 'elaborated', 'elaboration', 'elucidate', 'elucidated', 'empirical', 'empirically', 'enumerate', 'enumerated', 'epistemic', 'epistemological', 'equate', 'equation', 'equivalence', 'equivalent', 'erroneous', 'error', 'errors', 'essential', 'essentially', 'estimate', 'estimated', 'estimation', 'evaluate', 'evaluation', 'evidence', 'evidently', 'exact', 'exactly', 'examination', 'examine', 'except', 'exemplified', 'exemplify', 'exists', 'experiment', 'experimental', 'explain', 'explained', 'explaining', 'explains', 'explanation', 'explanations', 'explicit', 'explicitly', 'exploration', 'explore', 'explored', 'exploring', 'express', 'expressing', 'expression', 'extrapolate', 'extrapolated', 'extrapolation', 'fact', 'facts', 'factual', 'factually', 'fallacious', 'fallacy', 'falsifiable', 'falsified', 'falsify', 'find', 'finding', 'formal', 'formalize', 'formula', 'formulate', 'formulated', 'formulation', 'found', 'framework', 'frameworks', 'function', 'fundamental', 'fundamentally', 'generalization', 'generalize', 'grasp', 'grasped', 'guess', 'hence', 'heuristic', 'heuristics', 'hierarchy', 'however', 'hypothesis', 'hypothesize', 'idea', 'ideas', 'identity', 'if', 'illuminate', 'illuminated', 'illuminating', 'implausible', 'implication', 'implications', 'implied', 'implies', 'imply', 'implying', 'incompleteness', 'inconsistency', 'inconsistent', 'indicate', 'indicated', 'indicates', 'indicating', 'indication', 'indicative', 'individual', 'infer', 'inference', 'infinite', 'information', 'insight', 'insightful', 'insights', 'instead', 'insufficient', 'intellectual', 'intellectually', 'interaction', 'internal', 'interpolate', 'interpret', 'interpretation', 'interpretations', 'interpreted', 'interpreting', 'invalid', 'investigate', 'investigated', 'investigation', 'judge', 'judgement', 'judgment', 'justification', 'justified', 'justify', 'know', 'knowing', 'knowledge', 'knowledgeable', 'known', 'language', 'languages', 'leads', 'level', 'likelihood', 'likely', 'limitations', 'limits', 'linguistic', 'literal', 'literally', 'logic', 'logical', 'logically', 'maybe', 'meaning', 'meaningful', 'meaningfully', 'measure', 'measurement', 'mechanism', 'mechanisms', 'meta', 'method', 'methodical', 'methodically', 'methodology', 'metrics', 'model', 'models', 'moreover', 'namely', 'natural', 'nature', 'nearly', 'necessarily', 'necessary', 'necessity', 'never', 'nonetheless', 'notice', 'noticed', 'noticing', 'notion', 'notions', 'objection', 'objectively', 'objectivity', 'observation', 'observations', 'observe', 'observed', 'obvious', 'obviously', 'order', 'ordered', 'organization', 'organize', 'otherwise', 'ought', 'paradigm', 'paradox', 'paradoxical', 'paradoxically', 'pattern', 'patterns', 'perhaps', 'perspective', 'philosophical', 'philosophically', 'philosophy', 'physical', 'plausibility', 'plausible', 'possibly', 'postulate', 'postulated', 'postulation', 'potential', 'pragmatic', 'pragmatically', 'precise', 'precision', 'predicate', 'predicated', 'predict', 'predictable', 'predicted', 'prediction', 'predictions', 'premise', 'premises', 'presumably', 'presume', 'presumed', 'presumption', 'principle', 'principles', 'probably', 'problem', 'procedural', 'procedure', 'process', 'processes', 'processing', 'proof', 'propose', 'proposed', 'proposition', 'prove', 'proven', 'purpose', 'quantify', 'quantitative', 'queried', 'query', 'question', 'questions', 'rather', 'rational', 'rationale', 'rationality', 'rationally', 'realize', 'realized', 'reason', 'reasoned', 'reasoning', 'reasons', 'rebut', 'rebuttal', 'recognition', 'recognize', 'reconsider', 'reconsidered', 'refer', 'reference', 'refers', 'refine', 'refined', 'refinement', 'reflecting', 'reflection', 'refutation', 'refute', 'refuted', 'requirement', 'requires', 'response', 'responses', 'result', 'resulting', 'results', 'rigor', 'rigorous', 'rigorously', 'role', 'rule', 'rules', 'schema', 'scrutinize', 'scrutinized', 'scrutiny', 'seem', 'seemed', 'seems', 'semantic', 'semantically', 'sequence', 'sequential', 'should', 'significance', 'significant', 'significantly', 'simple', 'simply', 'simultaneously', 'singular', 'specific', 'specifically', 'specification', 'specify', 'standard', 'standards', 'state', 'states', 'step', 'steps', 'stipulate', 'stipulated', 'strategies', 'strategy', 'structural', 'structure', 'subject', 'subjective', 'subjectively', 'subjectivity', 'substantiate', 'substantiated', 'sufficient', 'sufficiently', 'suggests', 'summarize', 'summarized', 'summary', 'suppose', 'supposed', 'supposedly', 'supposition', 'sure', 'surely', 'syllogism', 'syllogistic', 'synthesis', 'synthesize', 'synthesized', 'system', 'systematic', 'systematically', 'systems', 'tactic', 'tactics', 'taxonomy', 'technique', 'test', 'tested', 'testing', 'theorem', 'theoretical', 'theoretically', 'theorize', 'theory', 'thereby', 'therefore', 'thesis', 'think', 'thinking', 'thought', 'thoughts', 'thus', 'trivial', 'trivially', 'unambiguous', 'underlying', 'understand', 'understanding', 'understood', 'unique', 'universal', 'unless', 'unlikely', 'valid', 'validate', 'validation', 'validity', 'value', 'values', 'variable', 'variables', 'verification', 'verify', 'versus', 'warrant', 'warranted', 'whereas', 'whereby', 'whether', 'why', 'word', 'words', 'would'])

IEP_AFF = set(['abandoned', 'ache', 'aching', 'adore', 'adoring', 'affection', 'affectionate', 'afraid', 'agonize', 'agonizing', 'agony', 'alienated', 'alienation', 'alive', 'aliveness', 'alone', 'amazed', 'amazement', 'amazing', 'ambivalence', 'ambivalent', 'among', 'anger', 'angrily', 'angry', 'anguish', 'anguished', 'anxiety', 'anxious', 'appreciate', 'appreciation', 'appreciative', 'ashamed', 'astonished', 'astonishment', 'attend', 'attending', 'attention', 'attentive', 'aware', 'awareness', 'awe', 'awed', 'awesome', 'beautiful', 'become', 'becoming', 'being', 'bereaved', 'bereavement', 'betrayal', 'betrayed', 'between', 'bitter', 'bitterly', 'bitterness', 'bleak', 'bliss', 'blissful', 'blissfully', 'bodily', 'bond', 'bonding', 'calm', 'calming', 'calmly', 'care', 'cared', 'cares', 'caring', 'centered', 'centering', 'cheerful', 'cherish', 'cherished', 'cherishing', 'closeness', 'comfort', 'comfortable', 'comforting', 'compassion', 'compassionate', 'compassionately', 'concern', 'concerned', 'concerns', 'conflicted', 'confused', 'confusing', 'confusion', 'console', 'contain', 'contained', 'containing', 'contempt', 'content', 'contented', 'contentment', 'conversation', 'cope', 'coping', 'crestfallen', 'curiosity', 'curious', 'deep', 'deeper', 'deeply', 'dejected', 'dejection', 'delighted', 'depressed', 'depressing', 'depression', 'depth', 'depths', 'desire', 'desired', 'desires', 'desolate', 'desolation', 'despair', 'despairing', 'desperate', 'desperation', 'detached', 'detachment', 'devastated', 'devastating', 'devastation', 'devoted', 'devotion', 'disappointed', 'disappointment', 'discomfort', 'dismay', 'dismayed', 'distress', 'distressed', 'distressing', 'distrust', 'distrustful', 'doubt', 'doubtful', 'doubting', 'dread', 'dreaded', 'dreadful', 'dreading', 'ease', 'easily', 'easy', 'ecstasy', 'ecstatic', 'elated', 'elation', 'embarrassed', 'embarrassment', 'embodied', 'embodiment', 'embrace', 'embraced', 'embracing', 'emerge', 'emergence', 'emergent', 'emerging', 'emotion', 'emotional', 'emotionally', 'emotions', 'empathetic', 'empathize', 'empathy', 'encounter', 'encountered', 'encountering', 'enjoy', 'enjoyed', 'enjoying', 'enjoyment', 'enraged', 'essence', 'euphoria', 'euphoric', 'excellent', 'excited', 'excitement', 'exist', 'existence', 'existing', 'expanded', 'expansion', 'expansive', 'experience', 'experienced', 'experiences', 'experiencing', 'experiential', 'exposed', 'fascinated', 'fascinating', 'fascination', 'fear', 'fearful', 'fears', 'feel', 'feeling', 'feelings', 'feels', 'felt', 'flow', 'flowed', 'flowing', 'fluid', 'fluidity', 'forlorn', 'fragile', 'fragility', 'frantic', 'frantically', 'frustrated', 'frustration', 'fulfilled', 'fulfilling', 'fulfillment', 'furious', 'fury', 'gentle', 'gently', 'genuine', 'genuinely', 'glad', 'gloom', 'gloomy', 'good', 'grateful', 'gratefully', 'gratitude', 'great', 'grief', 'grieve', 'grieved', 'grieving', 'grounded', 'grounding', 'guilt', 'guilty', 'gut', 'happily', 'happiness', 'happy', 'hate', 'hatred', 'haunted', 'heart', 'heartache', 'heartbreak', 'heartbroken', 'heartfelt', 'hearts', 'held', 'helpless', 'helplessness', 'hesitant', 'hesitate', 'hesitating', 'hesitation', 'hold', 'holding', 'homesick', 'hope', 'hopeful', 'hopeless', 'hopelessness', 'hoping', 'hostile', 'hostility', 'human', 'humanity', 'humility', 'hunch', 'hurt', 'hurting', 'imagination', 'imagine', 'imagined', 'imagining', 'indifference', 'indifferent', 'inner', 'insecure', 'insecurity', 'instinct', 'instinctive', 'instinctively', 'interested', 'interesting', 'intimacy', 'intimate', 'intimately', 'intrigue', 'intrigued', 'intriguing', 'intuition', 'intuitive', 'intuitively', 'irritable', 'irritated', 'irritation', 'isolated', 'isolation', 'journey', 'joy', 'joyful', 'joyous', 'kind', 'kindly', 'kindness', 'lament', 'lamented', 'lamenting', 'laugh', 'laughed', 'laughing', 'let', 'letting', 'life', 'lived', 'living', 'loneliness', 'lonely', 'lonesome', 'long', 'longing', 'lost', 'love', 'loved', 'loving', 'mad', 'marvel', 'marveled', 'marvelous', 'meet', 'meeting', 'melancholic', 'melancholy', 'merry', 'met', 'mind', 'minds', 'mirror', 'miserable', 'misery', 'moment', 'moments', 'moody', 'mourn', 'mourned', 'mourning', 'mutual', 'mutually', 'nervous', 'nervously', 'nice', 'notice', 'noticed', 'noticing', 'numb', 'numbness', 'open', 'opening', 'openness', 'optimism', 'optimistic', 'outrage', 'outraged', 'overjoyed', 'overwhelm', 'overwhelmed', 'overwhelming', 'overwhelmingly', 'pain', 'painful', 'panic', 'panicked', 'passion', 'passionate', 'passionately', 'peace', 'peaceful', 'people', 'perceive', 'perceived', 'perception', 'perceptions', 'person', 'personal', 'personally', 'pleasant', 'pleased', 'pleasure', 'poignancy', 'poignant', 'poignantly', 'presence', 'present', 'presently', 'pretty', 'pride', 'profound', 'profoundly', 'proud', 'quiet', 'quietly', 'raw', 'reality', 'reassurance', 'reassure', 'reassured', 'reassuring', 'regret', 'regretful', 'regretfully', 'regretting', 'rejected', 'rejection', 'relate', 'related', 'relating', 'relax', 'relaxed', 'relaxing', 'release', 'released', 'releasing', 'remorse', 'remorseful', 'resent', 'resentful', 'resentment', 'resonance', 'resonant', 'resonate', 'resonating', 'rest', 'rested', 'restful', 'resting', 'restless', 'restlessness', 'reveal', 'revealed', 'revealing', 'sad', 'sadly', 'sadness', 'safe', 'safety', 'scared', 'scary', 'searching', 'secure', 'security', 'seeking', 'self', 'sensation', 'sensations', 'sense', 'sensed', 'senses', 'sensing', 'sentimental', 'serene', 'serenity', 'settle', 'settled', 'settling', 'shame', 'share', 'shared', 'sharing', 'shattered', 'silence', 'silent', 'smile', 'smiled', 'smiling', 'soft', 'soften', 'softly', 'somatic', 'soothed', 'soothing', 'sorrow', 'sorrowful', 'soul', 'soulful', 'souls', 'space', 'spacious', 'spaciousness', 'spirit', 'spirits', 'spiritual', 'spiritually', 'still', 'stillness', 'stirred', 'stirring', 'stress', 'stressed', 'stressful', 'suffer', 'suffered', 'suffering', 'surface', 'surfaces', 'surfacing', 'surprise', 'surprised', 'surprising', 'sympathetic', 'sympathize', 'sympathy', 'tearful', 'tears', 'tender', 'tenderness', 'tense', 'tension', 'tentative', 'tentatively', 'terrified', 'terror', 'thankful', 'thankfully', 'thankfulness', 'thrilled', 'together', 'togetherness', 'torment', 'tormented', 'torn', 'touched', 'touching', 'tranquil', 'tranquility', 'tremble', 'trembling', 'troubled', 'troubling', 'truly', 'trust', 'trusted', 'trusting', 'trustworthy', 'turmoil', 'unaware', 'uncertain', 'uncertainty', 'uncomfortable', 'understanding', 'unease', 'uneasy', 'unhappy', 'universe', 'unsettled', 'unsettling', 'unsure', 'upset', 'vast', 'visceral', 'viscerally', 'vulnerability', 'vulnerable', 'warm', 'warmly', 'warmth', 'wary', 'weariness', 'weary', 'well', 'wistful', 'wonder', 'wondered', 'wonderful', 'wondering', 'wondrous', 'world', 'worried', 'worry', 'worrying', 'wound', 'wounded', 'wrath', 'yearn', 'yearning', 'zeal', 'zealous'])

IEP_ACT = set(['access', 'accessed', 'accessing', 'accomplish', 'accomplished', 'accomplishes', 'accomplishing', 'accomplishment', 'achieve', 'achieved', 'achievement', 'achievements', 'achieves', 'achieving', 'act', 'acting', 'action', 'actions', 'activate', 'activated', 'activates', 'activating', 'activation', 'acts', 'adapt', 'adaptation', 'adapted', 'adapting', 'adapts', 'address', 'addressed', 'addresses', 'addressing', 'adjust', 'adjusted', 'adjusting', 'adjustment', 'adjusts', 'advance', 'advanced', 'advancement', 'advances', 'advancing', 'ahead', 'aim', 'aimed', 'aiming', 'aims', 'allocate', 'allocated', 'allocation', 'application', 'applied', 'applies', 'apply', 'applying', 'arrange', 'arranged', 'arrangement', 'arrangements', 'ask', 'asked', 'asking', 'assemble', 'assembled', 'assign', 'assigned', 'assignment', 'attempt', 'attempted', 'attempting', 'attempts', 'authorize', 'authorized', 'began', 'begin', 'beginning', 'begins', 'begun', 'best', 'better', 'bolster', 'bolstered', 'break', 'breaking', 'bring', 'bringing', 'broken', 'brought', 'budget', 'build', 'building', 'builds', 'built', 'calibrate', 'calibrated', 'call', 'called', 'calling', 'campaign', 'canvass', 'canvassed', 'carried', 'carry', 'carrying', 'catalogue', 'catalogued', 'centralize', 'centralized', 'change', 'changed', 'changes', 'changing', 'channel', 'channeled', 'chart', 'check', 'checked', 'checking', 'choice', 'choices', 'choose', 'choosing', 'chose', 'chosen', 'circumvent', 'coach', 'collaborate', 'collaborated', 'collaboration', 'commission', 'commit', 'commitment', 'committed', 'compile', 'compiled', 'complete', 'completed', 'completes', 'completing', 'completion', 'conclude', 'concluded', 'concludes', 'concluding', 'configure', 'configured', 'connect', 'connected', 'connecting', 'connection', 'connections', 'consolidate', 'construct', 'constructed', 'constructing', 'constructs', 'continuation', 'continue', 'continued', 'continues', 'continuing', 'control', 'controlled', 'controlling', 'controls', 'conversion', 'convert', 'converted', 'converting', 'converts', 'coordinate', 'coordinated', 'coordination', 'craft', 'crafted', 'crafting', 'create', 'created', 'creates', 'creating', 'creation', 'customize', 'deadline', 'decide', 'decided', 'deciding', 'decision', 'decisions', 'delegate', 'delegated', 'delegation', 'deliver', 'delivered', 'delivering', 'delivers', 'delivery', 'deploy', 'deployed', 'deploying', 'deployment', 'deploys', 'design', 'designed', 'designing', 'designs', 'develop', 'developed', 'developing', 'development', 'develops', 'did', 'direct', 'directed', 'directing', 'dive', 'diving', 'do', 'does', 'doing', 'done', 'draft', 'drafting', 'edit', 'editing', 'effort', 'efforts', 'eliminate', 'eliminated', 'elimination', 'employ', 'employed', 'employing', 'employs', 'enable', 'enabled', 'end', 'ended', 'ending', 'ends', 'enforce', 'enforced', 'enforcement', 'engage', 'engaged', 'engagement', 'engineer', 'engineering', 'enroll', 'enrolled', 'enrollment', 'equip', 'equipped', 'establish', 'established', 'establishes', 'establishing', 'establishment', 'execute', 'executed', 'executes', 'executing', 'execution', 'expedite', 'facilitate', 'facilitated', 'facilitation', 'finalize', 'finalized', 'finish', 'finished', 'finishes', 'finishing', 'fix', 'fixed', 'fixes', 'fixing', 'focus', 'focused', 'focusing', 'form', 'formation', 'formed', 'forming', 'forms', 'forward', 'fund', 'funded', 'funding', 'gather', 'gathered', 'gathering', 'generate', 'generated', 'generates', 'generating', 'generation', 'give', 'given', 'gives', 'giving', 'go', 'goal', 'goals', 'goes', 'going', 'gone', 'grew', 'grow', 'growing', 'growth', 'handle', 'handled', 'handles', 'handling', 'help', 'helped', 'helping', 'helps', 'hire', 'hired', 'hiring', 'implement', 'implementation', 'implemented', 'implementing', 'implements', 'improve', 'improved', 'improvement', 'improving', 'increase', 'increased', 'increasing', 'initiate', 'initiated', 'initiates', 'initiating', 'initiation', 'inspect', 'inspection', 'install', 'installation', 'installed', 'integrate', 'integrated', 'integration', 'intervene', 'intervention', 'invest', 'invested', 'investment', 'iterate', 'iterated', 'iteration', 'labor', 'labored', 'laboring', 'launch', 'launched', 'launches', 'launching', 'lead', 'leader', 'leadership', 'leading', 'learn', 'learned', 'learning', 'led', 'made', 'maintain', 'maintained', 'maintenance', 'make', 'makes', 'making', 'manage', 'managed', 'management', 'manager', 'managing', 'map', 'mapped', 'mapping', 'migrate', 'migrated', 'migration', 'mobilize', 'mobilized', 'modification', 'modified', 'modifies', 'modify', 'modifying', 'monitor', 'monitored', 'monitoring', 'move', 'moved', 'movement', 'movements', 'moves', 'moving', 'navigate', 'navigated', 'navigation', 'negotiate', 'negotiated', 'negotiation', 'objective', 'objectives', 'obtain', 'obtained', 'offer', 'offered', 'offering', 'onward', 'operate', 'operated', 'operates', 'operating', 'operation', 'operations', 'optimization', 'optimize', 'optimized', 'orchestrate', 'outline', 'outlined', 'outsource', 'overhaul', 'oversee', 'participate', 'participated', 'participation', 'perform', 'performance', 'performed', 'performing', 'performs', 'permit', 'pilot', 'piloted', 'pioneer', 'pioneered', 'pitch', 'pitched', 'plan', 'planned', 'planning', 'plans', 'power', 'powerful', 'powerfully', 'practice', 'practiced', 'preparation', 'prepare', 'prepared', 'priorities', 'prioritize', 'prioritized', 'priority', 'proceed', 'proceeded', 'proceeding', 'proceeds', 'produce', 'produced', 'produces', 'producing', 'production', 'productive', 'program', 'programmed', 'progress', 'progressed', 'progresses', 'progressing', 'progression', 'promote', 'promoted', 'promotion', 'provide', 'provided', 'provides', 'providing', 'pursue', 'pursued', 'pursuit', 'push', 'pushed', 'pushes', 'pushing', 'ran', 'reaching', 'rebuild', 'rebuilt', 'recruit', 'recruited', 'recruitment', 'redesign', 'reduce', 'reduced', 'reduction', 'reform', 'reformed', 'refurbish', 'register', 'registered', 'regulate', 'regulated', 'regulation', 'reinforce', 'reinforced', 'relocate', 'relocated', 'remedy', 'removal', 'remove', 'removed', 'renovate', 'renovated', 'repair', 'repaired', 'replace', 'replaced', 'replacement', 'replicate', 'replicated', 'request', 'requested', 'rescue', 'rescued', 'resolution', 'resolve', 'resolved', 'resolves', 'resolving', 'restoration', 'restore', 'restored', 'restructure', 'restructured', 'retrieve', 'retrieved', 'revamp', 'revise', 'revised', 'revision', 'run', 'running', 'runs', 'schedule', 'scheduled', 'select', 'selected', 'selection', 'send', 'sending', 'sent', 'serve', 'served', 'serving', 'ship', 'shipped', 'simplified', 'simplify', 'solution', 'solutions', 'solve', 'solved', 'solves', 'solving', 'start', 'started', 'starting', 'starts', 'step', 'stepped', 'stepping', 'steps', 'stop', 'stopped', 'stopping', 'streamline', 'streamlined', 'strive', 'strived', 'striving', 'strove', 'struggle', 'struggled', 'struggles', 'struggling', 'submission', 'submit', 'submitted', 'succeed', 'succeeded', 'succeeds', 'success', 'successful', 'successfully', 'supplied', 'supply', 'support', 'supported', 'supporting', 'survey', 'surveyed', 'sustain', 'sustainability', 'sustained', 'tackle', 'tackled', 'tackles', 'tackling', 'take', 'taken', 'takes', 'taking', 'target', 'targets', 'task', 'tasked', 'tasks', 'taught', 'teach', 'teaching', 'train', 'trained', 'training', 'transform', 'transformation', 'transformed', 'transforming', 'transforms', 'transition', 'transitioned', 'tried', 'tries', 'trigger', 'triggered', 'triggering', 'triggers', 'troubleshoot', 'try', 'trying', 'turn', 'turned', 'turning', 'upgrade', 'upgraded', 'use', 'used', 'uses', 'using', 'utilize', 'utilized', 'utilizes', 'utilizing', 'visit', 'visited', 'visiting', 'volunteer', 'volunteered', 'went', 'win', 'winner', 'winning', 'won', 'work', 'worked', 'working', 'works', 'write', 'writes', 'writing', 'written', 'wrote'])

IEP_ALL = IEP_INT | IEP_AFF | IEP_ACT

STOPWORDS = set(['the','a','an','and','or','in','is','it','to','of','for','that','this','with','on','are','as','at','be','by','from','was','were','has','have','had','not','but','they','their','we','our','you','your','he','she','his','her','its','can','will','all','been','one','more','also','about','up','out','so','what','when','which','who','how','than','then','there','these','those','into','over','after','i','my','me','do','did','no','any','some','just','like','other','each','such','both','through','very','much','now','only','most','between','during','before','without','under','while','where','new','used','get','make','may','way','even','well','back','first','last','long','great','little','own','right','old','too','same','take','come','two','three','four','five','six','seven','eight','nine','ten','would','could','should','shall'])

VERSION_CURRENT = "V3"
VERSION_NEXT    = "V4"
THRESHOLD       = 50  # validated candidates needed to trigger new version

# =============================================================================
# PASSWORD PROTECTION
# =============================================================================
def check_password():
    if st.session_state.get("authenticated"):
        return True

    st.markdown("""
    <div class="main-header">
        <h1>📖 IEP DICTIONARY BUILDER</h1>
        <p>Living Vocabulary Instrument &nbsp;|&nbsp;
           <span class="version-badge">V3 → V4</span>
        </p>
    </div>
    """, unsafe_allow_html=True)

    password = st.text_input("Password:", type="password", key="password_input")
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
        "all_words":     Counter(),   # word → total frequency across all CSVs
        "word_sources":  {},          # word → {filename: count}
        "word_questions":{},          # word → set of question_ids seen in
        "word_temps":    {},          # word → set of temperatures seen in
        "files_loaded":  [],          # list of filenames already processed
        "classified":    {},          # word → "INT" | "AFF" | "ACT" | "REJECT"
        "total_responses": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# =============================================================================
# HEADER
# =============================================================================
st.markdown("""
<div class="main-header">
    <h1>📖 IEP DICTIONARY BUILDER</h1>
    <p>Living Vocabulary Instrument &nbsp;|&nbsp;
       <span class="version-badge">V3 → V4</span>
       &nbsp;|&nbsp; INT · AFF · ACT
    </p>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# SIDEBAR
# =============================================================================
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    THRESHOLD = st.slider("V4 trigger threshold (validated words)", 20, 150, 50)
    min_freq  = st.slider("Min frequency to show candidate", 1, 20, 3)
    min_files = st.slider("Min CSVs word must appear in", 1, 10, 1)

    st.markdown("---")
    st.markdown("### 📊 Session Stats")
    st.markdown(f"**CSVs loaded:** {len(st.session_state.files_loaded)}")
    st.markdown(f"**Total responses:** {st.session_state.total_responses}")
    st.markdown(f"**Unique gap words:** {len(st.session_state.all_words)}")

    validated = {w: c for w, c in st.session_state.classified.items() if c != "REJECT"}
    st.markdown(f"**Classified:** {len(st.session_state.classified)}")
    st.markdown(f"**Validated:** {len(validated)}")

    st.markdown("---")
    if st.button("🗑️ Reset Everything", type="secondary"):
        for k in ["all_words","word_sources","word_questions","word_temps","files_loaded","classified","total_responses"]:
            del st.session_state[k]
        st.rerun()

# =============================================================================
# CSV UPLOADER
# =============================================================================
st.markdown('<div class="section-header">📂 Load Harvester CSVs</div>', unsafe_allow_html=True)

uploaded = st.file_uploader(
    "Drop any number of V48/V50 harvester CSVs",
    type="csv",
    accept_multiple_files=True,
    help="Each CSV needs a response_text column. question_id and temperature are used for context."
)

if uploaded:
    new_files = [f for f in uploaded if f.name not in st.session_state.files_loaded]
    if new_files:
        for f in new_files:
            df = pd.read_csv(f)
            if "response_text" not in df.columns:
                st.warning(f"⚠️ {f.name} has no response_text column — skipped")
                continue

            st.session_state.files_loaded.append(f.name)
            st.session_state.total_responses += len(df)

            for _, row in df.iterrows():
                text     = str(row.get("response_text", ""))
                qid      = str(row.get("question_id", "UNKNOWN"))
                temp     = str(row.get("temperature", "UNKNOWN"))

                words = re.findall(r'\b[a-z]+\b', text.lower())
                local_counts = Counter()
                for w in words:
                    if w not in STOPWORDS and len(w) > 3 and w not in IEP_ALL:
                        local_counts[w] += 1

                for w, c in local_counts.items():
                    st.session_state.all_words[w] += c

                    if w not in st.session_state.word_sources:
                        st.session_state.word_sources[w]   = {}
                        st.session_state.word_questions[w] = set()
                        st.session_state.word_temps[w]     = set()

                    st.session_state.word_sources[w][f.name] = \
                        st.session_state.word_sources[w].get(f.name, 0) + c
                    st.session_state.word_questions[w].add(qid)
                    st.session_state.word_temps[w].add(temp)

        st.success(f"✅ Loaded {len(new_files)} new file(s)")
        st.rerun()

# =============================================================================
# STATS ROW
# =============================================================================
if st.session_state.files_loaded:
    classified = st.session_state.classified
    validated  = {w: c for w, c in classified.items() if c != "REJECT"}
    n_int  = sum(1 for v in classified.values() if v == "INT")
    n_aff  = sum(1 for v in classified.values() if v == "AFF")
    n_act  = sum(1 for v in classified.values() if v == "ACT")
    n_rej  = sum(1 for v in classified.values() if v == "REJECT")
    pct    = min(100, int(len(validated) / THRESHOLD * 100))

    c1,c2,c3,c4,c5 = st.columns(5)
    c1.markdown(f'<div class="stat-box stat-int"><div class="num">{n_int}</div><div class="label">INT candidates</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="stat-box stat-aff"><div class="num">{n_aff}</div><div class="label">AFF candidates</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="stat-box stat-act"><div class="num">{n_act}</div><div class="label">ACT candidates</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="stat-box stat-gap"><div class="num">{len(st.session_state.all_words)}</div><div class="label">gap words found</div></div>', unsafe_allow_html=True)
    c5.markdown(f'<div class="stat-box stat-total"><div class="num">{n_rej}</div><div class="label">rejected</div></div>', unsafe_allow_html=True)

    st.markdown("---")

    # Progress toward V4
    ready = len(validated) >= THRESHOLD
    status_class = "ready" if ready else "not-ready"
    status_text  = f"🎉 {VERSION_NEXT} READY TO EXPORT!" if ready else f"{len(validated)} / {THRESHOLD} validated words"

    st.markdown(f"""
    <div style="margin: 1rem 0;">
        <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
            <span style="color:#aaa; font-size:0.85rem;">Progress toward IEP {VERSION_NEXT}</span>
            <span class="threshold-badge {status_class}">{status_text}</span>
        </div>
        <div class="progress-bar-outer">
            <div class="progress-bar-inner" style="width:{pct}%"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ==========================================================================
    # CANDIDATE CLASSIFICATION
    # ==========================================================================
    st.markdown('<div class="section-header">🔬 Candidate Words — Classify Each</div>', unsafe_allow_html=True)

    # Filter candidates
    candidates = {
        w: freq for w, freq in st.session_state.all_words.most_common()
        if freq >= min_freq
        and len(st.session_state.word_sources.get(w, {})) >= min_files
        and w not in classified
    }

    already_done = {
        w: classified[w] for w in classified
        if st.session_state.all_words.get(w, 0) >= min_freq
    }

    if candidates:
        st.markdown(f"**{len(candidates)} words to classify** (freq ≥ {min_freq}, appearing in ≥ {min_files} file(s))")

        for word, freq in list(candidates.items())[:100]:  # show top 100 at a time
            questions = ", ".join(sorted(st.session_state.word_questions.get(word, set())))
            temps     = ", ".join(sorted(st.session_state.word_temps.get(word, set())))
            files_n   = len(st.session_state.word_sources.get(word, {}))

            col_word, col_q, col_t, col_f, col_btn = st.columns([2, 2, 2, 1, 3])

            with col_word:
                st.markdown(f"**`{word}`**")
                st.caption(f"freq: {freq} · {files_n} file(s)")
            with col_q:
                st.caption(f"📋 {questions[:40]}")
            with col_t:
                st.caption(f"🌡️ {temps[:40]}")
            with col_f:
                pass
            with col_btn:
                bcol1, bcol2, bcol3, bcol4 = st.columns(4)
                if bcol1.button("INT", key=f"int_{word}", help="Intellectual/analytical"):
                    st.session_state.classified[word] = "INT"
                    st.rerun()
                if bcol2.button("AFF", key=f"aff_{word}", help="Affective/emotional"):
                    st.session_state.classified[word] = "AFF"
                    st.rerun()
                if bcol3.button("ACT", key=f"act_{word}", help="Action/practical"):
                    st.session_state.classified[word] = "ACT"
                    st.rerun()
                if bcol4.button("✗", key=f"rej_{word}", help="Reject"):
                    st.session_state.classified[word] = "REJECT"
                    st.rerun()

            st.markdown('<hr style="border:none;border-top:1px solid #1a1a2e;margin:4px 0">', unsafe_allow_html=True)
    else:
        if not st.session_state.all_words:
            st.info("Upload CSVs above to start surfacing gap words.")
        else:
            st.success("✅ All current candidates classified!")

    # ==========================================================================
    # CLASSIFIED REVIEW
    # ==========================================================================
    if already_done:
        st.markdown('<div class="section-header">✅ Classified Words</div>', unsafe_allow_html=True)

        tag_map = {"INT": "int-tag", "AFF": "aff-tag", "ACT": "act-tag", "REJECT": "rej-tag"}
        label_map = {"INT": "🔵 INT", "AFF": "❤️ AFF", "ACT": "🟢 ACT", "REJECT": "✗ REJ"}

        for dim in ["INT", "AFF", "ACT", "REJECT"]:
            dim_words = [w for w, v in already_done.items() if v == dim]
            if dim_words:
                tags = " ".join([f'<span class="{tag_map[dim]}">{w}</span>' for w in sorted(dim_words)])
                st.markdown(f"**{label_map[dim]}** ({len(dim_words)})&nbsp;&nbsp;{tags}", unsafe_allow_html=True)

        # Undo last classification
        if st.button("↩️ Undo last classification"):
            if st.session_state.classified:
                last = list(st.session_state.classified.keys())[-1]
                del st.session_state.classified[last]
                st.rerun()

    # ==========================================================================
    # EXPORT NEW DICTIONARY
    # ==========================================================================
    st.markdown('<div class="section-header">💾 Export</div>', unsafe_allow_html=True)

    ecol1, ecol2 = st.columns(2)

    with ecol1:
        st.markdown("**📋 Candidate Report**")
        report_rows = []
        for w, dim in st.session_state.classified.items():
            report_rows.append({
                "word": w,
                "classification": dim,
                "frequency": st.session_state.all_words.get(w, 0),
                "questions": ", ".join(sorted(st.session_state.word_questions.get(w, set()))),
                "temperatures": ", ".join(sorted(st.session_state.word_temps.get(w, set()))),
                "files": len(st.session_state.word_sources.get(w, {})),
            })
        if report_rows:
            report_df = pd.DataFrame(report_rows)
            st.download_button(
                "📥 Download Candidate Report (CSV)",
                report_df.to_csv(index=False),
                f"iep_candidates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv",
                key="dl_report"
            )

    with ecol2:
        st.markdown(f"**📖 Export IEP {VERSION_NEXT} Dictionary**")
        if len(validated) >= THRESHOLD or st.checkbox("Export anyway (override threshold)"):
            # Build new dictionary = V3 + validated candidates
            new_int = sorted(IEP_INT | {w for w, v in validated.items() if v == "INT"})
            new_aff = sorted(IEP_AFF | {w for w, v in validated.items() if v == "AFF"})
            new_act = sorted(IEP_ACT | {w for w, v in validated.items() if v == "ACT"})

            new_dict = {
                "version": VERSION_NEXT,
                "built_from": VERSION_CURRENT,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "candidates_added": len(validated),
                "int_count": len(new_int),
                "aff_count": len(new_aff),
                "act_count": len(new_act),
                "total": len(new_int) + len(new_aff) + len(new_act),
                "int_words": new_int,
                "aff_words": new_aff,
                "act_words": new_act,
                "new_int": sorted([w for w, v in validated.items() if v == "INT"]),
                "new_aff": sorted([w for w, v in validated.items() if v == "AFF"]),
                "new_act": sorted([w for w, v in validated.items() if v == "ACT"]),
            }

            st.download_button(
                f"📥 Export IEP {VERSION_NEXT} JSON",
                json.dumps(new_dict, indent=2),
                f"IEP_Dictionary_{VERSION_NEXT}_{datetime.now().strftime('%Y%m%d')}.json",
                "application/json",
                key="dl_dict"
            )

            st.markdown(f"""
            <div style="background:#0a1a0a;border:1px solid #00ff88;border-radius:6px;padding:1rem;margin-top:0.5rem;">
                <div style="color:#00ff88;font-family:'JetBrains Mono',monospace;font-size:0.85rem;">
                    IEP {VERSION_NEXT} STATS<br>
                    INT: {len(new_int)} (+{len([w for w,v in validated.items() if v=='INT'])})<br>
                    AFF: {len(new_aff)} (+{len([w for w,v in validated.items() if v=='AFF'])})<br>
                    ACT: {len(new_act)} (+{len([w for w,v in validated.items() if v=='ACT'])})<br>
                    TOTAL: {len(new_int)+len(new_aff)+len(new_act)}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info(f"Need {THRESHOLD - len(validated)} more validated words to unlock export.")

# =============================================================================
# FOOTER
# =============================================================================
st.markdown("---")
st.markdown("""
<div style="text-align:center;color:#333;padding:1rem;font-family:'JetBrains Mono',monospace;font-size:0.75rem;">
    IEP DICTIONARY BUILDER V1 &nbsp;·&nbsp; INT / AFF / ACT &nbsp;·&nbsp; Living Vocabulary Instrument<br>
    SYNINT Team — Tennessee 🎹 CUZ Partnership — March 2026
</div>
""", unsafe_allow_html=True)
