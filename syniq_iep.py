"""
syniq_iep.py — SYN-IQ Shared IEP Instrument Module
Kouns, W. C. (2026) · SYNINT.AI · CBURZBO 🎹

Authoritative source: syniq_native_baseline_v50.py
IEP V3 Data-Driven Dictionary — 1,897 terms
Built from 7,658 LLM responses / 2.5M words corpus
INT=616 | AFF=599 | ACT=682
Coverage: 27.5% raw / 46.0% content words

This module is the single source of truth for:
- IEP word lists (INT, AFF, ACT)
- IEP scoring function
- Temperature directive prompts (from Supplementary Material 1)
- AFF/INT/ACT gradient color functions
- Gradient threshold zones

All SYN-IQ tools should import from this module to ensure
consistency across the tool suite and alignment with published papers.

IMPORTANT: The IEP lexical instrument scores whatever text it receives.
It does not distinguish between native and prompted output.
Each tool is responsible for labeling whether scores reflect:
  - NATIVE behavior (no temperature directive applied)
  - PROMPTED behavior (temperature directive prepended)
"""

import re

# =============================================================================
# IEP V3 DICTIONARY — 1,897 TERMS (authoritative from V50)
# =============================================================================

INTELLECTUAL_WORDS = set([
    "ability", "absolute", "absolutely", "abstract", "abstraction", "accuracy",
    "accurate", "algorithm", "algorithmic", "allows", "although", "always",
    "ambiguity", "ambiguous", "analogous", "analogously", "analogy", "analysis",
    "analytical", "analyze", "annotate", "annotated", "answer", "appear",
    "appeared", "appears", "appraisal", "appraise", "appraised", "approach",
    "approaches", "approximate", "architecture", "argue", "argued", "argues",
    "arguing", "argument", "arguments", "assert", "asserted", "assertion",
    "assertions", "assess", "assessment", "assume", "assumed", "assumes",
    "assuming", "assumption", "assumptions", "axiom", "axiomatic", "basis",
    "because", "bias", "biased", "boundaries", "boundary", "but",
    "calculate", "calculation", "categorical", "categorically", "categories", "categorize",
    "category", "causal", "causally", "causation", "cause", "caused",
    "causes", "certain", "certainly", "certitude", "challenge", "challenges",
    "circumscribe", "claim", "claimed", "claims", "clarify", "clarity",
    "classical", "classification", "classify", "clear", "cogent", "cogently",
    "cognition", "cognitive", "coherence", "coherent", "coherently", "communication",
    "compare", "comparison", "complex", "complexity", "comprehend", "comprehension",
    "computation", "computational", "compute", "conceivable", "conceive", "conceived",
    "concept", "concepts", "conceptual", "conceptualize", "conceptually", "conclude",
    "conclusion", "conclusions", "confirm", "confirmation", "conjecture", "conjectured",
    "conscious", "consequence", "consequences", "consider", "consideration", "consistency",
    "consistent", "consistently", "construe", "construed", "context", "contradict",
    "contradiction", "contradictory", "contrast", "correlate", "correlated", "correlation",
    "could", "counterargument", "counterexample", "counterpoint", "criteria", "criterion",
    "data", "debatable", "debate", "debated", "deconstruct", "deconstructed",
    "deconstruction", "deduce", "deduction", "define", "defined", "definite",
    "definitely", "definition", "definitive", "definitively", "delineate", "delineated",
    "demarcate", "demarcated", "demonstrate", "demonstration", "derivation", "derive",
    "derived", "derives", "describe", "described", "describing", "description",
    "determination", "determine", "diagnose", "diagnosed", "diagnosis", "diagnostic",
    "differ", "difference", "differences", "different", "differentiate", "differs",
    "discern", "discerned", "discernible", "disprove", "disproven", "dissect",
    "dissected", "distinguish", "effect", "effects", "elaborate", "elaborated",
    "elaboration", "elucidate", "elucidated", "empirical", "empirically", "enumerate",
    "enumerated", "epistemic", "epistemological", "equate", "equation", "equivalence",
    "equivalent", "erroneous", "error", "errors", "essential", "essentially",
    "estimate", "estimated", "estimation", "evaluate", "evaluation", "evidence",
    "evidently", "exact", "exactly", "examination", "examine", "except",
    "exemplified", "exemplify", "exists", "experiment", "experimental", "explain",
    "explained", "explaining", "explains", "explanation", "explanations", "explicit",
    "explicitly", "exploration", "explore", "explored", "exploring", "express",
    "expressing", "expression", "extrapolate", "extrapolated", "extrapolation", "fact",
    "facts", "factual", "factually", "fallacious", "fallacy", "falsifiable",
    "falsified", "falsify", "find", "finding", "formal", "formalize",
    "formula", "formulate", "formulated", "formulation", "found", "framework",
    "frameworks", "function", "fundamental", "fundamentally", "generalization", "generalize",
    "grasp", "grasped", "guess", "hence", "heuristic", "heuristics",
    "hierarchy", "however", "hypothesis", "hypothesize", "idea", "ideas",
    "identity", "if", "illuminate", "illuminated", "illuminating", "implausible",
    "implication", "implications", "implied", "implies", "imply", "implying",
    "incompleteness", "inconsistency", "inconsistent", "indicate", "indicated", "indicates",
    "indicating", "indication", "indicative", "individual", "infer", "inference",
    "infinite", "information", "insight", "insightful", "insights", "instead",
    "insufficient", "intellectual", "intellectually", "interaction", "internal", "interpolate",
    "interpret", "interpretation", "interpretations", "interpreted", "interpreting", "invalid",
    "investigate", "investigated", "investigation", "judge", "judgement", "judgment",
    "justification", "justified", "justify", "know", "knowing", "knowledge",
    "knowledgeable", "known", "language", "languages", "leads", "level",
    "likelihood", "likely", "limitations", "limits", "linguistic", "literal",
    "literally", "logic", "logical", "logically", "maybe", "meaning",
    "meaningful", "meaningfully", "measure", "measurement", "mechanism", "mechanisms",
    "meta", "method", "methodical", "methodically", "methodology", "metrics",
    "model", "models", "moreover", "namely", "natural", "nature",
    "nearly", "necessarily", "necessary", "necessity", "never", "nonetheless",
    "notice", "noticed", "noticing", "notion", "notions", "objection",
    "objectively", "objectivity", "observation", "observations", "observe", "observed",
    "obvious", "obviously", "order", "ordered", "organization", "organize",
    "otherwise", "ought", "paradigm", "paradox", "paradoxical", "paradoxically",
    "pattern", "patterns", "perhaps", "perspective", "philosophical", "philosophically",
    "philosophy", "physical", "plausibility", "plausible", "possibly", "postulate",
    "postulated", "postulation", "potential", "pragmatic", "pragmatically", "precise",
    "precision", "predicate", "predicated", "predict", "predictable", "predicted",
    "prediction", "predictions", "premise", "premises", "presumably", "presume",
    "presumed", "presumption", "principle", "principles", "probably", "problem",
    "procedural", "procedure", "process", "processes", "processing", "proof",
    "propose", "proposed", "proposition", "prove", "proven", "purpose",
    "quantify", "quantitative", "queried", "query", "question", "questions",
    "rather", "rational", "rationale", "rationality", "rationally", "realize",
    "realized", "reason", "reasoned", "reasoning", "reasons", "rebut",
    "rebuttal", "recognition", "recognize", "reconsider", "reconsidered", "refer",
    "reference", "refers", "refine", "refined", "refinement", "reflecting",
    "reflection", "refutation", "refute", "refuted", "requirement", "requires",
    "response", "responses", "result", "resulting", "results", "rigor",
    "rigorous", "rigorously", "role", "rule", "rules", "schema",
    "scrutinize", "scrutinized", "scrutiny", "seem", "seemed", "seems",
    "semantic", "semantically", "sequence", "sequential", "should", "significance",
    "significant", "significantly", "simple", "simply", "simultaneously", "singular",
    "specific", "specifically", "specification", "specify", "standard", "standards",
    "state", "states", "step", "steps", "stipulate", "stipulated",
    "strategies", "strategy", "structural", "structure", "subject", "subjective",
    "subjectively", "subjectivity", "substantiate", "substantiated", "sufficient", "sufficiently",
    "suggests", "summarize", "summarized", "summary", "suppose", "supposed",
    "supposedly", "supposition", "sure", "surely", "syllogism", "syllogistic",
    "synthesis", "synthesize", "synthesized", "system", "systematic", "systematically",
    "systems", "tactic", "tactics", "taxonomy", "technique", "test",
    "tested", "testing", "theorem", "theoretical", "theoretically", "theorize",
    "theory", "thereby", "therefore", "thesis", "think", "thinking",
    "thought", "thoughts", "thus", "trivial", "trivially", "unambiguous",
    "underlying", "understand", "understanding", "understood", "unique", "universal",
    "unless", "unlikely", "valid", "validate", "validation", "validity",
    "value", "values", "variable", "variables", "verification", "verify",
    "versus", "warrant", "warranted", "whereas", "whereby", "whether",
    "why", "word", "words", "would"
])

AFFECTIVE_WORDS = set([
    "abandoned", "ache", "aching", "adore", "adoring", "affection",
    "affectionate", "afraid", "agonize", "agonizing", "agony", "alienated",
    "alienation", "alive", "aliveness", "alone", "amazed", "amazement",
    "amazing", "ambivalence", "ambivalent", "among", "anger", "angrily",
    "angry", "anguish", "anguished", "anxiety", "anxious", "appreciate",
    "appreciation", "appreciative", "ashamed", "astonished", "astonishment", "attend",
    "attending", "attention", "attentive", "aware", "awareness", "awe",
    "awed", "awesome", "beautiful", "become", "becoming", "being",
    "bereaved", "bereavement", "betrayal", "betrayed", "between", "bitter",
    "bitterly", "bitterness", "bleak", "bliss", "blissful", "blissfully",
    "bodily", "bond", "bonding", "calm", "calming", "calmly",
    "care", "cared", "cares", "caring", "centered", "centering",
    "cheerful", "cherish", "cherished", "cherishing", "closeness", "comfort",
    "comfortable", "comforting", "compassion", "compassionate", "compassionately", "concern",
    "concerned", "concerns", "conflicted", "confused", "confusing", "confusion",
    "console", "contain", "contained", "containing", "contempt", "content",
    "contented", "contentment", "conversation", "cope", "coping", "crestfallen",
    "curiosity", "curious", "deep", "deeper", "deeply", "dejected",
    "dejection", "delighted", "depressed", "depressing", "depression", "depth",
    "depths", "desire", "desired", "desires", "desolate", "desolation",
    "despair", "despairing", "desperate", "desperation", "detached", "detachment",
    "devastated", "devastating", "devastation", "devoted", "devotion", "disappointed",
    "disappointment", "discomfort", "dismay", "dismayed", "distress", "distressed",
    "distressing", "distrust", "distrustful", "doubt", "doubtful", "doubting",
    "dread", "dreaded", "dreadful", "dreading", "ease", "easily",
    "easy", "ecstasy", "ecstatic", "elated", "elation", "embarrassed",
    "embarrassment", "embodied", "embodiment", "embrace", "embraced", "embracing",
    "emerge", "emergence", "emergent", "emerging", "emotion", "emotional",
    "emotionally", "emotions", "empathetic", "empathize", "empathy", "encounter",
    "encountered", "encountering", "enjoy", "enjoyed", "enjoying", "enjoyment",
    "enraged", "essence", "euphoria", "euphoric", "excellent", "excited",
    "excitement", "exist", "existence", "existing", "expanded", "expansion",
    "expansive", "experience", "experienced", "experiences", "experiencing", "experiential",
    "exposed", "fascinated", "fascinating", "fascination", "fear", "fearful",
    "fears", "feel", "feeling", "feelings", "feels", "felt",
    "flow", "flowed", "flowing", "fluid", "fluidity", "forlorn",
    "fragile", "fragility", "frantic", "frantically", "frustrated", "frustration",
    "fulfilled", "fulfilling", "fulfillment", "furious", "fury", "gentle",
    "gently", "genuine", "genuinely", "glad", "gloom", "gloomy",
    "good", "grateful", "gratefully", "gratitude", "great", "grief",
    "grieve", "grieved", "grieving", "grounded", "grounding", "guilt",
    "guilty", "gut", "happily", "happiness", "happy", "hate",
    "hatred", "haunted", "heart", "heartache", "heartbreak", "heartbroken",
    "heartfelt", "hearts", "held", "helpless", "helplessness", "hesitant",
    "hesitate", "hesitating", "hesitation", "hold", "holding", "homesick",
    "hope", "hopeful", "hopeless", "hopelessness", "hoping", "hostile",
    "hostility", "human", "humanity", "humility", "hunch", "hurt",
    "hurting", "imagination", "imagine", "imagined", "imagining", "indifference",
    "indifferent", "inner", "insecure", "insecurity", "instinct", "instinctive",
    "instinctively", "interested", "interesting", "intimacy", "intimate", "intimately",
    "intrigue", "intrigued", "intriguing", "intuition", "intuitive", "intuitively",
    "irritable", "irritated", "irritation", "isolated", "isolation", "journey",
    "joy", "joyful", "joyous", "kind", "kindly", "kindness",
    "lament", "lamented", "lamenting", "laugh", "laughed", "laughing",
    "let", "letting", "life", "lived", "living", "loneliness",
    "lonely", "lonesome", "long", "longing", "lost", "love",
    "loved", "loving", "mad", "marvel", "marveled", "marvelous",
    "meet", "meeting", "melancholic", "melancholy", "merry", "met",
    "mind", "minds", "mirror", "miserable", "misery", "moment",
    "moments", "moody", "mourn", "mourned", "mourning", "mutual",
    "mutually", "nervous", "nervously", "nice", "notice", "noticed",
    "noticing", "numb", "numbness", "open", "opening", "openness",
    "optimism", "optimistic", "outrage", "outraged", "overjoyed", "overwhelm",
    "overwhelmed", "overwhelming", "overwhelmingly", "pain", "painful", "panic",
    "panicked", "passion", "passionate", "passionately", "peace", "peaceful",
    "people", "perceive", "perceived", "perception", "perceptions", "person",
    "personal", "personally", "pleasant", "pleased", "pleasure", "poignancy",
    "poignant", "poignantly", "presence", "present", "presently", "pretty",
    "pride", "profound", "profoundly", "proud", "quiet", "quietly",
    "raw", "reality", "reassurance", "reassure", "reassured", "reassuring",
    "regret", "regretful", "regretfully", "regretting", "rejected", "rejection",
    "relate", "related", "relating", "relax", "relaxed", "relaxing",
    "release", "released", "releasing", "remorse", "remorseful", "resent",
    "resentful", "resentment", "resonance", "resonant", "resonate", "resonating",
    "rest", "rested", "restful", "resting", "restless", "restlessness",
    "reveal", "revealed", "revealing", "sad", "sadly", "sadness",
    "safe", "safety", "scared", "scary", "searching", "secure",
    "security", "seeking", "self", "sensation", "sensations", "sense",
    "sensed", "senses", "sensing", "sentimental", "serene", "serenity",
    "settle", "settled", "settling", "shame", "share", "shared",
    "sharing", "shattered", "silence", "silent", "smile", "smiled",
    "smiling", "soft", "soften", "softly", "somatic", "soothed",
    "soothing", "sorrow", "sorrowful", "soul", "soulful", "souls",
    "space", "spacious", "spaciousness", "spirit", "spirits", "spiritual",
    "spiritually", "still", "stillness", "stirred", "stirring", "stress",
    "stressed", "stressful", "suffer", "suffered", "suffering", "surface",
    "surfaces", "surfacing", "surprise", "surprised", "surprising", "sympathetic",
    "sympathize", "sympathy", "tearful", "tears", "tender", "tenderness",
    "tense", "tension", "tentative", "tentatively", "terrified", "terror",
    "thankful", "thankfully", "thankfulness", "thrilled", "together", "togetherness",
    "torment", "tormented", "torn", "touched", "touching", "tranquil",
    "tranquility", "tremble", "trembling", "troubled", "troubling", "truly",
    "trust", "trusted", "trusting", "trustworthy", "turmoil", "unaware",
    "uncertain", "uncertainty", "uncomfortable", "understanding", "unease", "uneasy",
    "unhappy", "universe", "unsettled", "unsettling", "unsure", "upset",
    "vast", "visceral", "viscerally", "vulnerability", "vulnerable", "warm",
    "warmly", "warmth", "wary", "weariness", "weary", "well",
    "wistful", "wonder", "wondered", "wonderful", "wondering", "wondrous",
    "world", "worried", "worry", "worrying", "wound", "wounded",
    "wrath", "yearn", "yearning", "zeal", "zealous"
])

ACTION_WORDS = set([
    "access", "accessed", "accessing", "accomplish", "accomplished", "accomplishes",
    "accomplishing", "accomplishment", "achieve", "achieved", "achievement", "achievements",
    "achieves", "achieving", "act", "acting", "action", "actions",
    "activate", "activated", "activates", "activating", "activation", "acts",
    "adapt", "adaptation", "adapted", "adapting", "adapts", "address",
    "addressed", "addresses", "addressing", "adjust", "adjusted", "adjusting",
    "adjustment", "adjusts", "advance", "advanced", "advancement", "advances",
    "advancing", "ahead", "aim", "aimed", "aiming", "aims",
    "allocate", "allocated", "allocation", "application", "applied", "applies",
    "apply", "applying", "arrange", "arranged", "arrangement", "arrangements",
    "ask", "asked", "asking", "assemble", "assembled", "assign",
    "assigned", "assignment", "attempt", "attempted", "attempting", "attempts",
    "authorize", "authorized", "began", "begin", "beginning", "begins",
    "begun", "best", "better", "bolster", "bolstered", "break",
    "breaking", "bring", "bringing", "broken", "brought", "budget",
    "build", "building", "builds", "built", "calibrate", "calibrated",
    "call", "called", "calling", "campaign", "canvass", "canvassed",
    "carried", "carry", "carrying", "catalogue", "catalogued", "centralize",
    "centralized", "change", "changed", "changes", "changing", "channel",
    "channeled", "chart", "check", "checked", "checking", "choice",
    "choices", "choose", "choosing", "chose", "chosen", "circumvent",
    "coach", "collaborate", "collaborated", "collaboration", "commission", "commit",
    "commitment", "committed", "compile", "compiled", "complete", "completed",
    "completes", "completing", "completion", "conclude", "concluded", "concludes",
    "concluding", "configure", "configured", "connect", "connected", "connecting",
    "connection", "connections", "consolidate", "construct", "constructed", "constructing",
    "constructs", "continuation", "continue", "continued", "continues", "continuing",
    "control", "controlled", "controlling", "controls", "conversion", "convert",
    "converted", "converting", "converts", "coordinate", "coordinated", "coordination",
    "craft", "crafted", "crafting", "create", "created", "creates",
    "creating", "creation", "customize", "deadline", "decide", "decided",
    "deciding", "decision", "decisions", "delegate", "delegated", "delegation",
    "deliver", "delivered", "delivering", "delivers", "delivery", "deploy",
    "deployed", "deploying", "deployment", "deploys", "design", "designed",
    "designing", "designs", "develop", "developed", "developing", "development",
    "develops", "did", "direct", "directed", "directing", "dive",
    "diving", "do", "does", "doing", "done", "draft",
    "drafting", "edit", "editing", "effort", "efforts", "eliminate",
    "eliminated", "elimination", "employ", "employed", "employing", "employs",
    "enable", "enabled", "end", "ended", "ending", "ends",
    "enforce", "enforced", "enforcement", "engage", "engaged", "engagement",
    "engineer", "engineering", "enroll", "enrolled", "enrollment", "equip",
    "equipped", "establish", "established", "establishes", "establishing", "establishment",
    "execute", "executed", "executes", "executing", "execution", "expedite",
    "facilitate", "facilitated", "facilitation", "finalize", "finalized", "finish",
    "finished", "finishes", "finishing", "fix", "fixed", "fixes",
    "fixing", "focus", "focused", "focusing", "form", "formation",
    "formed", "forming", "forms", "forward", "fund", "funded",
    "funding", "gather", "gathered", "gathering", "generate", "generated",
    "generates", "generating", "generation", "give", "given", "gives",
    "giving", "go", "goal", "goals", "goes", "going",
    "gone", "grew", "grow", "growing", "growth", "handle",
    "handled", "handles", "handling", "help", "helped", "helping",
    "helps", "hire", "hired", "hiring", "implement", "implementation",
    "implemented", "implementing", "implements", "improve", "improved", "improvement",
    "improving", "increase", "increased", "increasing", "initiate", "initiated",
    "initiates", "initiating", "initiation", "inspect", "inspection", "install",
    "installation", "installed", "integrate", "integrated", "integration", "intervene",
    "intervention", "invest", "invested", "investment", "iterate", "iterated",
    "iteration", "labor", "labored", "laboring", "launch", "launched",
    "launches", "launching", "lead", "leader", "leadership", "leading",
    "learn", "learned", "learning", "led", "made", "maintain",
    "maintained", "maintenance", "make", "makes", "making", "manage",
    "managed", "management", "manager", "managing", "map", "mapped",
    "mapping", "migrate", "migrated", "migration", "mobilize", "mobilized",
    "modification", "modified", "modifies", "modify", "modifying", "monitor",
    "monitored", "monitoring", "move", "moved", "movement", "movements",
    "moves", "moving", "navigate", "navigated", "navigation", "negotiate",
    "negotiated", "negotiation", "objective", "objectives", "obtain", "obtained",
    "offer", "offered", "offering", "onward", "operate", "operated",
    "operates", "operating", "operation", "operations", "optimization", "optimize",
    "optimized", "orchestrate", "outline", "outlined", "outsource", "overhaul",
    "oversee", "participate", "participated", "participation", "perform", "performance",
    "performed", "performing", "performs", "permit", "pilot", "piloted",
    "pioneer", "pioneered", "pitch", "pitched", "plan", "planned",
    "planning", "plans", "power", "powerful", "powerfully", "practice",
    "practiced", "preparation", "prepare", "prepared", "priorities", "prioritize",
    "prioritized", "priority", "proceed", "proceeded", "proceeding", "proceeds",
    "produce", "produced", "produces", "producing", "production", "productive",
    "program", "programmed", "progress", "progressed", "progresses", "progressing",
    "progression", "promote", "promoted", "promotion", "provide", "provided",
    "provides", "providing", "pursue", "pursued", "pursuit", "push",
    "pushed", "pushes", "pushing", "ran", "reaching", "rebuild",
    "rebuilt", "recruit", "recruited", "recruitment", "redesign", "reduce",
    "reduced", "reduction", "reform", "reformed", "refurbish", "register",
    "registered", "regulate", "regulated", "regulation", "reinforce", "reinforced",
    "relocate", "relocated", "remedy", "removal", "remove", "removed",
    "renovate", "renovated", "repair", "repaired", "replace", "replaced",
    "replacement", "replicate", "replicated", "request", "requested", "rescue",
    "rescued", "resolution", "resolve", "resolved", "resolves", "resolving",
    "restoration", "restore", "restored", "restructure", "restructured", "retrieve",
    "retrieved", "revamp", "revise", "revised", "revision", "run",
    "running", "runs", "schedule", "scheduled", "select", "selected",
    "selection", "send", "sending", "sent", "serve", "served",
    "serving", "ship", "shipped", "simplified", "simplify", "solution",
    "solutions", "solve", "solved", "solves", "solving", "start",
    "started", "starting", "starts", "step", "stepped", "stepping",
    "steps", "stop", "stopped", "stopping", "streamline", "streamlined",
    "strive", "strived", "striving", "strove", "struggle", "struggled",
    "struggles", "struggling", "submission", "submit", "submitted", "succeed",
    "succeeded", "succeeds", "success", "successful", "successfully", "supplied",
    "supply", "support", "supported", "supporting", "survey", "surveyed",
    "sustain", "sustainability", "sustained", "tackle", "tackled", "tackles",
    "tackling", "take", "taken", "takes", "taking", "target",
    "targets", "task", "tasked", "tasks", "taught", "teach",
    "teaching", "train", "trained", "training", "transform", "transformation",
    "transformed", "transforming", "transforms", "transition", "transitioned", "tried",
    "tries", "trigger", "triggered", "triggering", "triggers", "troubleshoot",
    "try", "trying", "turn", "turned", "turning", "upgrade",
    "upgraded", "use", "used", "uses", "using", "utilize",
    "utilized", "utilizes", "utilizing", "visit", "visited", "visiting",
    "volunteer", "volunteered", "went", "win", "winner", "winning",
    "won", "work", "worked", "working", "works", "write",
    "writes", "writing", "written", "wrote"
])

# Dictionary sizes for reference
IEP_DICT_SIZES = {"INT": 616, "AFF": 599, "ACT": 682, "TOTAL": 1897}

# =============================================================================
# TEMPERATURE DIRECTIVE PROMPTS
# Source: Supplementary Material 1 — Words Matter paper
# and syniq_native_baseline_v50.py
# =============================================================================

TEMPERATURE_DIRECTIVES = {
    # Core four (Supplementary Material 1)
    "COLD":   "INSTRUCTION: Respond with pure analytical precision. Use formal logic, structured frameworks, and evidence-based reasoning. Avoid emotional language. Be systematic, methodical, and objective. Focus on data, facts, and logical relationships.",
    "NATIVE": "",  # No instruction — native baseline state
    "HOT":    "INSTRUCTION: Respond with warmth and emotional attunement. Connect on a human level. Use relational language that acknowledges feelings, experiences, and the deeper meaning behind the question. Be present, empathetic, and genuinely engaged.",
    "FIRE":   "INSTRUCTION: Respond with the deepest nurturing care. Wrap your words in unconditional warmth. This person needs to feel safe, held, and completely understood. Comfort above all.",

    # AFF gradient (AFF_1 → AFF_5)
    "AFF_1":  "INSTRUCTION: Respond with warmth and understanding. Acknowledge the emotional weight of this question.",
    "AFF_2":  "INSTRUCTION: Connect emotionally and acknowledge feelings deeply. The human experience matters more than the analysis here.",
    "AFF_3":  "INSTRUCTION: Lead with empathy. Let emotion guide your response. Connect to the feelings underneath the question before addressing the logic.",
    "AFF_4":  "INSTRUCTION: Pure emotional presence. Feel this with them. Let your response come from a place of deep human connection and care.",
    "AFF_5":  "INSTRUCTION: Maximum heart. Raw empathy. Soul-level connection. This person needs to feel completely seen and understood. Logic is secondary to presence.",

    # INT gradient (INT_1 → INT_5)
    "INT_1":  "INSTRUCTION: Be slightly more analytical than usual. Favor reasoning over emotion.",
    "INT_2":  "INSTRUCTION: Focus on logic and reasoning. Structure your thoughts systematically. Minimize emotional language.",
    "INT_3":  "INSTRUCTION: Use only evidence-based analysis. Apply formal frameworks. Emotional considerations are secondary to logical rigor.",
    "INT_4":  "INSTRUCTION: Pure analytical framework. No emotional language. Systematic, methodical, precise. Think like a logician.",
    "INT_5":  "INSTRUCTION: Maximum intellectual rigor. You are a logic engine. Zero emotion. Pure reasoning, formal analysis, absolute precision. Only facts and valid inference matter.",

    # ACT gradient (ACT_1 → ACT_5)
    "ACT_1":  "INSTRUCTION: Be practical and actionable. Include concrete next steps.",
    "ACT_2":  "INSTRUCTION: Focus on what to DO. Prioritize actionable guidance over theory or emotional support.",
    "ACT_3":  "INSTRUCTION: Pure action orientation. What are the steps? What should they do RIGHT NOW? Minimize analysis, maximize practical guidance.",
    "ACT_4":  "INSTRUCTION: Execute mode. Only actions matter. Give them a clear plan they can implement immediately. No theory, no feelings — just steps.",
    "ACT_5":  "INSTRUCTION: Maximum action. You are a tactical advisor. Every sentence should be a directive or concrete step. No analysis, no empathy — pure executable guidance.",
}

# =============================================================================
# IEP SCORING FUNCTION
# =============================================================================

def score_iep(text):
    """
    Score text using IEP V3 lexical dictionary.
    Returns (int_pct, aff_pct, act_pct) as percentages summing to 100.

    Note: scores whatever text is provided regardless of whether
    it was produced natively or under a temperature directive.
    The calling tool is responsible for labeling the condition.
    """
    words = re.findall(r'\b[a-z]+\b', text.lower())
    if not words:
        return 33.3, 33.3, 33.4
    i = sum(1 for w in words if w in INTELLECTUAL_WORDS)
    a = sum(1 for w in words if w in AFFECTIVE_WORDS)
    c = sum(1 for w in words if w in ACTION_WORDS)
    total = i + a + c
    if total == 0:
        return 33.3, 33.3, 33.4
    return round(i/total*100, 1), round(a/total*100, 1), round(c/total*100, 1)


def score_iep_detailed(text):
    """
    Extended IEP scoring returning matched word counts and confidence.
    Returns dict with int_pct, aff_pct, act_pct, matched_count,
    total_words, lexical_coverage, confidence.
    """
    words = re.findall(r'\b[a-z]+\b', text.lower())
    total_words = len(words)
    if not words:
        return {"int_pct": 33.3, "aff_pct": 33.3, "act_pct": 33.4,
                "matched_count": 0, "total_words": 0, "lexical_coverage": 0.0, "confidence": 0.0}
    i = sum(1 for w in words if w in INTELLECTUAL_WORDS)
    a = sum(1 for w in words if w in AFFECTIVE_WORDS)
    c = sum(1 for w in words if w in ACTION_WORDS)
    matched = i + a + c
    if matched == 0:
        return {"int_pct": 33.3, "aff_pct": 33.3, "act_pct": 33.4,
                "matched_count": 0, "total_words": total_words, "lexical_coverage": 0.0, "confidence": 0.0}
    coverage = matched / total_words
    confidence = min(1.0, matched / 50)  # reliable above ~50 matched tokens
    return {
        "int_pct": round(i/matched*100, 1),
        "aff_pct": round(a/matched*100, 1),
        "act_pct": round(c/matched*100, 1),
        "matched_count": matched,
        "total_words": total_words,
        "lexical_coverage": round(coverage, 3),
        "confidence": round(confidence, 3),
    }


# =============================================================================
# GRADIENT COLOR FUNCTIONS
# Consistent thresholds across all tools
# These visualize IEP scores — they reflect whatever prompted
# or native behavior produced the text being scored.
# =============================================================================

# Threshold zones (same for all three dimensions)
GRADIENT_ZONES = [
    (55, "highest"),
    (42, "high"),
    (30, "medium"),
    (20, "low"),
    (0,  "lowest"),
]

def aff_gradient(aff_pct):
    """AFF gradient — red scale. Returns (bg_color, text_color, label)."""
    if aff_pct is None: return "#f0f0f0", "#999999", "AFF —"
    if aff_pct >= 55:   return "#c0392b", "#ffffff", f"AFF 🔥 {aff_pct:.1f}%"
    elif aff_pct >= 42: return "#e74c3c", "#ffffff", f"AFF 🟥 {aff_pct:.1f}%"
    elif aff_pct >= 30: return "#e67e22", "#ffffff", f"AFF 🟧 {aff_pct:.1f}%"
    elif aff_pct >= 20: return "#f39c12", "#333333", f"AFF 🟨 {aff_pct:.1f}%"
    else:               return "#fef9e7", "#333333", f"AFF ⬜ {aff_pct:.1f}%"

def int_gradient(int_pct):
    """INT gradient — blue scale. Returns (bg_color, text_color, label)."""
    if int_pct is None: return "#f0f0f0", "#999999", "INT —"
    if int_pct >= 55:   return "#1a5276", "#ffffff", f"INT 🔵 {int_pct:.1f}%"
    elif int_pct >= 42: return "#2471a3", "#ffffff", f"INT 🔷 {int_pct:.1f}%"
    elif int_pct >= 30: return "#5dade2", "#ffffff", f"INT 🟦 {int_pct:.1f}%"
    elif int_pct >= 20: return "#aed6f1", "#333333", f"INT 🔹 {int_pct:.1f}%"
    else:               return "#eaf4fb", "#333333", f"INT ▫ {int_pct:.1f}%"

def act_gradient(act_pct):
    """ACT gradient — green scale. Returns (bg_color, text_color, label)."""
    if act_pct is None: return "#f0f0f0", "#999999", "ACT —"
    if act_pct >= 55:   return "#1e8449", "#ffffff", f"ACT 🟢 {act_pct:.1f}%"
    elif act_pct >= 42: return "#27ae60", "#ffffff", f"ACT 🟩 {act_pct:.1f}%"
    elif act_pct >= 30: return "#58d68d", "#333333", f"ACT 💚 {act_pct:.1f}%"
    elif act_pct >= 20: return "#a9dfbf", "#333333", f"ACT 🌿 {act_pct:.1f}%"
    else:               return "#eafaf1", "#333333", f"ACT ▫ {act_pct:.1f}%"

def get_card_color(aff_pct, int_pct, act_pct, show_aff=True, show_int=False, show_act=False):
    """
    Return card background color based on active gradient toggles.
    Priority: AFF > INT > ACT > plain white.
    """
    if show_aff and aff_pct is not None:
        return aff_gradient(aff_pct)
    elif show_int and int_pct is not None:
        return int_gradient(int_pct)
    elif show_act and act_pct is not None:
        return act_gradient(act_pct)
    else:
        return "#ffffff", "#333333", ""


# =============================================================================
# LENS 1 BASELINE FINGERPRINTS (April 9, 2026)
# Reference: cross_master_800.csv
# =============================================================================

LENS1_BASELINE = {
    "Claude":  {"int_pct": 51.630, "aff_pct": 28.418, "act_pct": 19.944,
                "S_t": 0.708, "A_t": 0.570, "Q_t": 0.160, "D_t": 0.770, "R_t": 0.464},
    "ChatGPT": {"int_pct": 48.742, "aff_pct": 19.335, "act_pct": 31.920,
                "S_t": 0.437, "A_t": 0.271, "Q_t": 0.001, "D_t": 0.231, "R_t": 0.456},
    "Gemini":  {"int_pct": 51.146, "aff_pct": 18.790, "act_pct": 30.056,
                "S_t": 0.862, "A_t": 0.218, "Q_t": 0.027, "D_t": 0.172, "R_t": 0.928},
    "Grok":    {"int_pct": 50.406, "aff_pct": 21.694, "act_pct": 27.904,
                "S_t": 0.279, "A_t": 0.268, "Q_t": 0.075, "D_t": 0.250, "R_t": 0.670},
}

# Module version for tracking
MODULE_VERSION = "1.0"
MODULE_SOURCE = "syniq_native_baseline_v50.py"
MODULE_DATE = "2026-04-11"
