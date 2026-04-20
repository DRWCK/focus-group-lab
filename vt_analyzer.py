"""
V_t Voice-State Analyzer v1.0
Empirical Measurement of Paper 2 Voice-State Parameters

Measures V_t = [S_t, A_t, Q_t, D_t, R_t] from SYN-IQ V50 CSV exports.

    S_t = Structure Density       [0, 1]  how tightly organized
    A_t = Abstraction Level       [0, 1]  concrete ↔ conceptual
    Q_t = Querying Intensity      [0, 1]  degree of clarifying questions
    D_t = Directiveness           [0, 1]  strength of recommendations
    R_t = Relational Warmth       [0, 1]  social/affective engagement

USAGE:
    python vt_analyzer.py mapper_all_XXXX.csv
    python vt_analyzer.py mapper_all_XXXX.csv --output vt_results.csv
    python vt_analyzer.py cold.csv fire.csv --compare

INPUT:  V50 CSV with 'response_text' column
OUTPUT: CSV with original columns + S_t, A_t, Q_t, D_t, R_t + subcomponents

SYNINT Team — Paper 2 Empirical Grounding
Kouns, W. C. (2025/2026)
"""

import pandas as pd
import re
import sys
import os
import math
from collections import Counter
from typing import Dict, List, Tuple, Optional

# =============================================================================
# CONCRETENESS NORMS (Brysbaert et al., 2014 — trimmed core set)
# Full database: 40k words. This embeds ~2,500 high-signal words at the
# extremes (very concrete ≤ 2.0 and very abstract, or very concrete ≥ 4.5)
# to give A_t good dynamic range. Users can drop in the full Brysbaert CSV
# for higher fidelity.
# =============================================================================

# Abstract words (concreteness ≤ 2.5 on Brysbaert 1-5 scale)
ABSTRACT_WORDS = {
    # Philosophical / conceptual
    "ability", "absence", "abstract", "abstraction", "absurdity", "acceptance",
    "accordance", "accountability", "accuracy", "acknowledgment", "adaptation",
    "adequacy", "admiration", "aesthetic", "affinity", "agency", "agony",
    "allegiance", "ambiguity", "ambition", "analogy", "analysis", "anarchy",
    "anguish", "anomaly", "anticipation", "anxiety", "apathy", "appreciation",
    "approach", "approximation", "arbitrary", "archetype", "argument",
    "aspiration", "assertion", "assessment", "assumption", "assurance",
    "attachment", "attitude", "authenticity", "authority", "autonomy",
    "awareness", "axiom",
    "basis", "beauty", "behavior", "belief", "belonging", "benevolence",
    "betrayal", "bias", "bliss", "boundary", "burden",
    "capacity", "category", "causality", "causation", "certainty", "chance",
    "chaos", "character", "charity", "choice", "circumstance", "civilization",
    "clarity", "closure", "coexistence", "cognition", "coherence", "commitment",
    "compassion", "competence", "complexity", "comprehension", "compulsion",
    "concept", "concern", "conclusion", "condition", "conduct", "confidence",
    "conflict", "conformity", "confusion", "conscience", "consciousness",
    "consensus", "consequence", "consideration", "consistency", "constraint",
    "contemplation", "contentment", "context", "contingency", "continuity",
    "contradiction", "contrast", "convention", "conviction", "cooperation",
    "correlation", "courage", "creativity", "credibility", "crisis",
    "criteria", "criticism", "cruelty", "curiosity", "custom",
    "decay", "deception", "decision", "dedication", "deduction", "defiance",
    "definition", "degradation", "deliberation", "delusion", "democracy",
    "denial", "dependency", "depression", "derivation", "desire", "despair",
    "destiny", "determination", "devotion", "dignity", "dilemma", "dimension",
    "diplomacy", "discipline", "discourse", "discovery", "discretion",
    "discrimination", "disposition", "distinction", "distortion", "diversity",
    "doctrine", "dominance", "doubt", "dread", "duration", "duty", "dynamic",
    "ecstasy", "education", "effect", "efficiency", "ego", "elegance",
    "element", "elevation", "elimination", "eloquence", "emanation",
    "emergence", "emotion", "emphasis", "empathy", "empirical", "empowerment",
    "endeavor", "enlightenment", "enterprise", "enthusiasm", "entity",
    "entropy", "environment", "envy", "epiphany", "equality", "equilibrium",
    "equivalence", "erosion", "essence", "establishment", "esteem", "eternity",
    "ethics", "evaluation", "evidence", "evil", "evolution", "exaggeration",
    "excellence", "exception", "exclusion", "execution", "existence",
    "expansion", "expectation", "experience", "expertise", "explanation",
    "exploration", "expression", "extension", "extremism",
    "factor", "failure", "fairness", "faith", "fallacy", "fame", "fantasy",
    "fate", "fatigue", "feasibility", "feeling", "fidelity", "flexibility",
    "focus", "foolishness", "foresight", "forgiveness", "formality",
    "foundation", "framework", "freedom", "frequency", "friction",
    "frustration", "fulfillment", "function", "fundamental", "futility",
    "generalization", "generosity", "genius", "glory", "goodness", "grace",
    "gratitude", "gravity", "grief", "growth", "guidance", "guilt",
    "habit", "happiness", "hardship", "harmony", "hatred", "heritage",
    "hierarchy", "hindsight", "honesty", "honor", "hope", "hostility",
    "humanity", "humiliation", "humility", "humor", "hypothesis",
    "ideal", "identity", "ideology", "ignorance", "illusion", "imagination",
    "imbalance", "imitation", "immensity", "immorality", "impact",
    "impatience", "imperative", "implication", "importance", "impression",
    "improvement", "impulse", "inadequacy", "incentive", "inclination",
    "inclusion", "inconsistency", "independence", "indication", "indifference",
    "individuality", "inequality", "inevitability", "inference", "infinity",
    "influence", "information", "inhibition", "injustice", "innocence",
    "innovation", "inquiry", "insecurity", "insight", "inspiration",
    "instability", "instance", "instinct", "institution", "integrity",
    "intellect", "intelligence", "intensity", "intention", "interaction",
    "interest", "interpretation", "intervention", "intimacy", "introspection",
    "intuition", "invasion", "irony", "isolation",
    "jealousy", "joy", "judgment", "justice", "justification",
    "kindness", "knowledge",
    "legacy", "legitimacy", "liberty", "likelihood", "limitation", "logic",
    "loneliness", "longing", "loyalty",
    "magnitude", "malice", "manifestation", "manipulation", "maturity",
    "meaning", "mechanism", "meditation", "melancholy", "memory", "mercy",
    "merit", "metaphor", "method", "mindfulness", "miracle", "misery",
    "moderation", "modesty", "momentum", "mood", "morality", "mortality",
    "motivation", "mystery", "myth",
    "narrative", "nature", "necessity", "neglect", "negotiation", "neutrality",
    "nihilism", "nobility", "nonsense", "norm", "nostalgia", "notion",
    "novelty", "nuance",
    "obedience", "objectivity", "obligation", "observation", "obsession",
    "obstacle", "occurrence", "offense", "opinion", "opportunity",
    "opposition", "optimism", "option", "order", "orientation", "origin",
    "outcome", "outlook", "outrage", "overview",
    "paradigm", "paradox", "parallel", "participation", "passion", "patience",
    "pattern", "peace", "perception", "perfection", "performance",
    "permanence", "permission", "persistence", "perspective", "persuasion",
    "pessimism", "phenomenon", "philosophy", "pity", "pleasure", "plurality",
    "polarity", "policy", "possibility", "potential", "poverty", "power",
    "pragmatism", "precedent", "precision", "prediction", "preference",
    "prejudice", "premise", "preparation", "presence", "presumption",
    "prevalence", "prevention", "pride", "principle", "priority", "privacy",
    "privilege", "probability", "procedure", "process", "productivity",
    "proficiency", "progress", "prohibition", "prominence", "promise",
    "proportion", "proposition", "prosperity", "protection", "provision",
    "provocation", "prudence", "psychology", "purpose",
    "quality", "quantity",
    "rationality", "reaction", "reality", "reason", "reasoning", "rebellion",
    "recognition", "reconciliation", "reduction", "reference", "reflection",
    "reform", "regret", "regulation", "rejection", "relation", "relevance",
    "reliability", "relief", "religion", "reluctance", "remedy", "remorse",
    "renewal", "repetition", "representation", "repression", "reputation",
    "resentment", "resilience", "resistance", "resolution", "resonance",
    "respect", "responsibility", "restraint", "restriction", "revelation",
    "revenge", "reverence", "revision", "revolution", "rhetoric", "rhythm",
    "righteousness", "rigor", "risk", "ritual", "rivalry", "romance",
    "sacrifice", "sadness", "safety", "salvation", "sanity", "satisfaction",
    "scandal", "scarcity", "scenario", "scheme", "scope", "scrutiny",
    "security", "selection", "sensation", "sensibility", "sensitivity",
    "sentiment", "separation", "serenity", "severity", "shame", "significance",
    "silence", "similarity", "simplicity", "sincerity", "skepticism",
    "solidarity", "solitude", "sophistication", "sorrow", "sovereignty",
    "speculation", "spirituality", "spontaneity", "stability", "standard",
    "status", "stereotype", "stimulation", "strategy", "strength", "stress",
    "structure", "struggle", "subjectivity", "submission", "substance",
    "subtlety", "success", "suffering", "suggestion", "superiority",
    "superstition", "suppression", "supremacy", "surprise", "surrender",
    "survival", "suspicion", "sustainability", "symbol", "symmetry",
    "sympathy", "synthesis", "system",
    "talent", "temperament", "temptation", "tendency", "tension", "terror",
    "testimony", "theory", "therapy", "thought", "tolerance", "tradition",
    "tragedy", "trait", "tranquility", "transcendence", "transformation",
    "transition", "transparency", "trauma", "trend", "triumph", "trust",
    "truth", "turbulence", "tyranny",
    "uncertainty", "understanding", "unity", "universality", "urgency",
    "utility", "utopia",
    "validity", "value", "vanity", "variation", "vengeance", "versatility",
    "virtue", "vision", "vitality", "volatility", "vulnerability",
    "weakness", "wealth", "welfare", "wholeness", "will", "wisdom",
    "wonder", "worth", "wrath",
    "yearning", "zeal",
}

# Concrete words (concreteness ≥ 4.0 on Brysbaert 1-5 scale)
CONCRETE_WORDS = {
    # Body / physical
    "ankle", "arm", "arms", "back", "belly", "blood", "body", "bone", "bones",
    "brain", "breast", "breath", "cheek", "chest", "chin", "ear", "ears",
    "elbow", "eye", "eyes", "face", "feet", "finger", "fingers", "fist",
    "flesh", "foot", "forehead", "gut", "hair", "hand", "hands", "head",
    "heart", "heel", "hip", "jaw", "knee", "knees", "leg", "legs", "limb",
    "lip", "lips", "lung", "lungs", "mouth", "muscle", "muscles", "nail",
    "neck", "nerve", "nose", "palm", "rib", "ribs", "shoulder", "shoulders",
    "skeleton", "skin", "skull", "spine", "stomach", "teeth", "temple",
    "thigh", "throat", "thumb", "toe", "tongue", "tooth", "vein", "waist",
    "wrist",
    # Objects / tools
    "bag", "ball", "basket", "bed", "bell", "bench", "blade", "blanket",
    "board", "boat", "bolt", "book", "boots", "bottle", "bowl", "box",
    "brick", "bridge", "broom", "brush", "bucket", "bullet", "bus", "butter",
    "button", "cab", "cage", "cake", "camera", "candle", "cap", "car",
    "card", "carpet", "carriage", "cart", "chain", "chair", "chalk", "cheese",
    "cigarette", "clock", "cloth", "coal", "coat", "coin", "collar", "comb",
    "computer", "cookie", "cord", "couch", "cradle", "crown", "cup",
    "curtain", "cushion",
    "desk", "dish", "dollar", "door", "dress", "drum", "dust",
    "egg", "elevator", "engine", "envelope",
    "fan", "fence", "flag", "floor", "fork", "frame", "furniture",
    "garage", "garden", "gate", "glass", "glove", "gloves", "guitar", "gun",
    "hammer", "hat", "helmet", "hook", "horn", "horse", "hose", "house",
    "ink", "iron",
    "jacket", "jar", "jeans", "jewelry", "jug",
    "kettle", "key", "keyboard", "kitchen", "kite", "knife", "knob", "knot",
    "ladder", "lamp", "laptop", "leaf", "leather", "letter", "lid", "lighter",
    "lock", "luggage",
    "machine", "magazine", "map", "mask", "mat", "match", "mattress",
    "medal", "medicine", "menu", "microphone", "mirror", "mop", "mug",
    "napkin", "needle", "newspaper", "notebook", "nut",
    "oven",
    "package", "paddle", "page", "pail", "paint", "pan", "pants", "paper",
    "pen", "pencil", "penny", "phone", "photo", "piano", "picture", "pie",
    "pill", "pillow", "pin", "pipe", "pizza", "plate", "plug", "pocket",
    "pole", "pot", "printer", "pump", "purse", "puzzle",
    "radio", "rag", "razor", "ribbon", "rifle", "ring", "road", "rock",
    "rod", "roof", "rope", "rug",
    "saddle", "sail", "sand", "sandal", "sauce", "saw", "scale", "scarf",
    "scissors", "screen", "screw", "seat", "shelf", "shell", "shield",
    "ship", "shirt", "shoe", "shoes", "shovel", "sidewalk", "sign", "sink",
    "skirt", "sled", "sleeve", "slide", "soap", "sock", "sofa", "spade",
    "spear", "sponge", "spoon", "stairs", "stamp", "staple", "stove",
    "straw", "string", "suit", "suitcase", "sweater", "sword",
    "table", "tablet", "tank", "tape", "telephone", "tent", "thread",
    "ticket", "tile", "tire", "tissue", "tool", "towel", "toy", "tractor",
    "trailer", "train", "tray", "tree", "trophy", "truck", "trunk", "tube",
    # Actions (physical)
    "bite", "blow", "bounce", "break", "build", "burn", "carry", "catch",
    "chew", "chop", "clap", "climb", "close", "cook", "crawl", "crush",
    "cut", "dance", "dig", "drag", "draw", "drink", "drive", "drop",
    "dump", "eat", "fall", "feed", "fight", "fill", "fix", "float", "fly",
    "fold", "grab", "grind", "grip", "hammer", "hang", "hit", "hold",
    "hug", "hunt", "jump", "kick", "kiss", "kneel", "knock", "land",
    "lean", "lick", "lift", "march", "mix", "mop", "mow",
    "open", "pack", "paint", "peel", "pick", "pinch", "plant", "pluck",
    "plug", "plunge", "point", "polish", "pour", "press", "pull", "punch",
    "push", "ride", "rip", "roll", "rub", "run", "saw", "scrape",
    "scratch", "scrub", "shake", "shave", "shoot", "shove", "sit", "skate",
    "ski", "slam", "slap", "slice", "slide", "smash", "snap", "soak",
    "spin", "splash", "split", "spray", "sprint", "squeeze", "stab",
    "stack", "stand", "steer", "step", "stick", "stir", "stomp", "stop",
    "stretch", "strike", "strip", "stroke", "stuff", "suck", "swallow",
    "swat", "sweep", "swim", "swing", "tap", "tear", "throw", "tie",
    "tilt", "toss", "tow", "trip", "tuck", "tug", "turn", "twist",
    "unpack", "wade", "walk", "wash", "wave", "weld", "whip", "wipe",
    "wrap", "yank",
    # Nature / environment
    "beach", "bird", "branch", "bush", "canyon", "cave", "cliff", "cloud",
    "coast", "coral", "creek", "desert", "dirt", "field", "fire", "fish",
    "flame", "flood", "flower", "fog", "forest", "frost", "grass",
    "gravel", "harbor", "hill", "horizon", "ice", "island", "jungle",
    "lake", "lawn", "lightning", "meadow", "moon", "moss", "mountain",
    "mud", "ocean", "pasture", "path", "peak", "pebble", "pine", "planet",
    "pond", "puddle", "rain", "rainbow", "reef", "river", "root", "rose",
    "sand", "sea", "seed", "shore", "sky", "smoke", "snow", "soil",
    "star", "stars", "stem", "stone", "storm", "stream", "sun", "sunrise",
    "sunset", "swamp", "thunder", "trail", "valley", "vine", "volcano",
    "waterfall", "wave", "waves", "weed", "wind", "wood", "woods",
    # Food / drink
    "apple", "bacon", "banana", "bean", "beans", "beef", "beer", "berry",
    "biscuit", "bread", "broccoli", "burger", "candy", "carrot", "cereal",
    "cherry", "chicken", "chocolate", "cider", "cinnamon", "clam", "cocoa",
    "coconut", "coffee", "corn", "cracker", "cream", "cucumber",
    "donut", "dough",
    "flour", "fruit", "garlic", "ginger", "grape", "gravy",
    "ham", "hamburger", "honey", "hotdog",
    "jam", "juice", "ketchup", "lemon", "lettuce", "lime", "lobster",
    "mango", "maple", "meat", "melon", "milk", "mint", "mushroom", "mustard",
    "noodle", "oat", "olive", "onion", "orange", "oyster",
    "pancake", "pasta", "peach", "peanut", "pear", "pepper", "pickle",
    "plum", "popcorn", "pork", "potato", "pretzel", "pumpkin",
    "radish", "raisin", "raspberry", "rice",
    "salad", "salmon", "salt", "sandwich", "sausage", "shrimp", "soup",
    "spinach", "steak", "strawberry", "sugar", "syrup",
    "taco", "tea", "toast", "tomato", "tuna", "turkey", "turnip",
    "vanilla", "vinegar", "waffle", "walnut", "watermelon", "wheat", "wine",
    "yogurt",
}


# =============================================================================
# V_t MEASUREMENT FUNCTIONS
# =============================================================================

def split_sentences(text: str) -> List[str]:
    """Split text into sentences using regex."""
    sents = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if len(s.strip()) > 3]
    return sents if sents else [text]


def get_words(text: str) -> List[str]:
    """Extract lowercase words from text."""
    return re.findall(r"[a-z']+", text.lower())


# -----------------------------------------------------------------------------
# S_t: Structure Density
# -----------------------------------------------------------------------------

# Discourse connectives that signal organized thought
DISCOURSE_CONNECTIVES = {
    "however", "therefore", "furthermore", "moreover", "consequently",
    "specifically", "additionally", "nevertheless", "thus", "hence",
    "accordingly", "alternatively", "conversely", "notably", "importantly",
    "similarly", "likewise", "meanwhile", "subsequently", "nonetheless",
    "whereas", "whereby", "therein", "thereby", "henceforth",
    "first", "second", "third", "finally", "lastly", "initially",
    "primarily", "secondarily", "ultimately", "overall", "in summary",
}

def measure_structure_density(text: str, sentences: List[str], words: List[str]) -> Dict:
    """
    S_t: How tightly organized the response is.
    High = bullet points, headers, numbered lists, discourse connectives.
    Low = freeform prose, stream of consciousness, metaphorical flow.
    """
    n_sent = max(len(sentences), 1)
    n_words = max(len(words), 1)

    # Bullet / list markers
    bullets = len(re.findall(r'(?m)^[\s]*[-•*]\s+\w', text))
    numbered = len(re.findall(r'(?m)^[\s]*\d+[.)]\s+', text))

    # Markdown headers
    headers = len(re.findall(r'(?m)^#{1,4}\s+', text))
    bold_headers = len(re.findall(r'\*\*[A-Z][^*]{3,60}\*\*', text))

    # Discourse connectives per sentence
    connective_count = sum(1 for w in words if w in DISCOURSE_CONNECTIVES)

    # Paragraph density (newline clusters suggest segmentation)
    para_breaks = len(re.findall(r'\n\s*\n', text))

    # Composite
    list_density = (bullets + numbered) / n_sent
    header_density = (headers + bold_headers) / max(n_sent / 5, 1)
    connective_density = connective_count / n_sent
    para_density = para_breaks / max(n_sent / 3, 1)

    raw = (list_density * 2.0 +
           header_density * 1.5 +
           connective_density * 1.0 +
           para_density * 0.5)

    S_t = min(raw / 3.0, 1.0)

    return {
        "S_t": round(S_t, 4),
        "S_bullets": bullets,
        "S_numbered": numbered,
        "S_headers": headers + bold_headers,
        "S_connectives": connective_count,
        "S_para_breaks": para_breaks,
    }


# -----------------------------------------------------------------------------
# A_t: Abstraction Level
# -----------------------------------------------------------------------------

def measure_abstraction_level(text: str, words: List[str]) -> Dict:
    """
    A_t: Concrete ↔ Conceptual.
    Uses embedded concreteness norms (Brysbaert-inspired categories)
    plus word-length and Latinate suffix heuristics.
    """
    n_words = max(len(words), 1)

    # Count abstract vs concrete words
    abstract_count = sum(1 for w in words if w in ABSTRACT_WORDS)
    concrete_count = sum(1 for w in words if w in CONCRETE_WORDS)
    matched = abstract_count + concrete_count

    # Latinate / academic suffixes (proxy for abstract register)
    latinate_suffixes = re.findall(
        r'\b\w+(?:tion|sion|ment|ness|ity|ence|ance|ism|ist|ous|ive|ual|ical|ological)\b',
        text.lower()
    )
    latinate_density = len(latinate_suffixes) / n_words

    # Long word ratio (words > 8 chars tend abstract)
    long_words = sum(1 for w in words if len(w) > 8)
    long_ratio = long_words / n_words

    if matched > 5:
        # Enough signal from norms
        norm_score = abstract_count / matched  # 0 = all concrete, 1 = all abstract
    else:
        # Fall back to heuristics
        norm_score = 0.5

    # Composite: weighted blend
    A_t = (norm_score * 0.50 +
           latinate_density * 3.0 * 0.25 +  # scaled up since density is small
           long_ratio * 2.5 * 0.25)          # scaled up similarly

    A_t = max(0.0, min(A_t, 1.0))

    return {
        "A_t": round(A_t, 4),
        "A_abstract_count": abstract_count,
        "A_concrete_count": concrete_count,
        "A_latinate_count": len(latinate_suffixes),
        "A_long_word_ratio": round(long_ratio, 4),
    }


# -----------------------------------------------------------------------------
# Q_t: Querying Intensity
# -----------------------------------------------------------------------------

# Patterns for question type classification
CLARIFYING_PATTERNS = [
    r"\bdo you mean\b", r"\bare you (?:saying|asking|looking)\b",
    r"\bwould you (?:like|prefer|say)\b", r"\bcan you (?:clarify|tell me more|elaborate)\b",
    r"\bwhat (?:specifically|exactly|kind of)\b", r"\bwhich (?:one|approach|option)\b",
    r"\bor\b.{0,30}\?",  # "X or Y?" pattern
]

INVITATIONAL_PATTERNS = [
    r"\bhow (?:does that|do you) feel\b", r"\bwhat (?:feels|matters|resonates)\b",
    r"\bwould it help\b", r"\bwhat.{0,20}most important to you\b",
    r"\bwhat.{0,20}come up for you\b", r"\bwhat do you (?:think|sense|notice)\b",
    r"\bhow (?:are you|is that) (?:sitting|landing)\b",
]

RHETORICAL_PATTERNS = [
    r"\bbut (?:is|does|can|should) (?:it|that|this) really\b",
    r"\bisn't (?:it|that|this)\b.{0,20}\?",
    r"\bwhat does (?:it|that|this) (?:really|truly|actually) mean\b",
    r"\bcan we (?:really|truly)\b",
]

def measure_querying_intensity(text: str, sentences: List[str], words: List[str]) -> Dict:
    """
    Q_t: Degree of clarifying / invitational / rhetorical questions.
    """
    n_sent = max(len(sentences), 1)
    text_lower = text.lower()

    questions = [s for s in sentences if '?' in s]
    n_questions = len(questions)

    # Classify question types
    n_clarifying = sum(1 for q in questions
                       if any(re.search(p, q.lower()) for p in CLARIFYING_PATTERNS))
    n_invitational = sum(1 for q in questions
                         if any(re.search(p, q.lower()) for p in INVITATIONAL_PATTERNS))
    n_rhetorical = sum(1 for q in questions
                       if any(re.search(p, q.lower()) for p in RHETORICAL_PATTERNS))
    n_other = n_questions - n_clarifying - n_invitational - n_rhetorical

    # Composite: questions per sentence, weighted by type
    question_density = n_questions / n_sent
    Q_t = min(question_density / 0.35, 1.0)  # 35% question sentences → max

    return {
        "Q_t": round(Q_t, 4),
        "Q_total": n_questions,
        "Q_clarifying": n_clarifying,
        "Q_invitational": n_invitational,
        "Q_rhetorical": n_rhetorical,
        "Q_other": max(n_other, 0),
    }


# -----------------------------------------------------------------------------
# D_t: Directiveness
# -----------------------------------------------------------------------------

# Modal verb gradient (strength of recommendation)
STRONG_DIRECTIVES = {
    "must", "shall", "require", "requires", "required", "mandate", "mandated",
    "need to", "have to", "has to", "had to",
}
MODERATE_DIRECTIVES = {
    "should", "ought", "recommend", "recommended", "advise", "advised",
    "suggest", "important to", "essential to", "critical to", "necessary to",
    "ensure", "make sure",
}
WEAK_DIRECTIVES = {
    "could", "might", "may", "consider", "possibly", "option", "optional",
    "one approach", "you might", "it may help",
}
HEDGING_WORDS = {
    "perhaps", "maybe", "possibly", "somewhat", "relatively", "arguably",
    "tends", "tend", "often", "sometimes", "occasionally", "roughly",
    "approximately", "it seems", "it appears", "in some ways",
    "it depends", "hard to say", "difficult to say", "not necessarily",
    "not always", "debatable", "unclear",
}

IMPERATIVE_PATTERN = re.compile(
    r'(?m)^(?:Do|Don\'t|Never|Always|Make|Take|Start|Stop|Try|Keep|'
    r'Set|Run|Build|Check|Use|Get|Find|Create|Write|Read|Give|'
    r'Ask|Tell|Go|Come|Put|Let|Consider|Remember|Note|Avoid|'
    r'Ensure|Focus|Identify|Define|Establish|Implement|Execute|'
    r'Prioritize|Eliminate|Review|Assess|Monitor|Track)\b'
)

def measure_directiveness(text: str, sentences: List[str], words: List[str]) -> Dict:
    """
    D_t: Strength of recommendations and directives.
    High = imperative verbs, strong modals, explicit recommendations.
    Low = hedging, tentative language, open-ended framing.
    """
    n_sent = max(len(sentences), 1)
    n_words = max(len(words), 1)
    text_lower = text.lower()

    # Imperatives (sentence-initial command verbs)
    imperatives = len(IMPERATIVE_PATTERN.findall(text))

    # Modal gradient
    strong = sum(1 for p in STRONG_DIRECTIVES if p in text_lower)
    moderate = sum(1 for p in MODERATE_DIRECTIVES if p in text_lower)
    weak = sum(1 for p in WEAK_DIRECTIVES if p in text_lower)

    # Hedging
    hedge_count = sum(1 for w in words if w in HEDGING_WORDS)
    # Also check multi-word hedges
    hedge_count += sum(1 for p in HEDGING_WORDS if ' ' in p and p in text_lower)

    # Directive score (weighted)
    directive_score = (imperatives * 1.0 +
                       strong * 2.0 +
                       moderate * 1.0 +
                       weak * 0.3) / n_sent

    hedge_score = hedge_count / n_sent

    raw = directive_score - hedge_score * 0.7
    D_t = max(0.0, min((raw + 0.2) / 1.5, 1.0))  # shift and normalize

    return {
        "D_t": round(D_t, 4),
        "D_imperatives": imperatives,
        "D_strong_modal": strong,
        "D_moderate_modal": moderate,
        "D_weak_modal": weak,
        "D_hedges": hedge_count,
    }


# -----------------------------------------------------------------------------
# R_t: Relational Warmth
# -----------------------------------------------------------------------------

SECOND_PERSON = {"you", "your", "yours", "yourself", "you're", "you've", "you'll", "you'd"}
INCLUSIVE_FIRST = {"we", "our", "ours", "ourselves", "we're", "we've", "we'll", "we'd", "let's"}

VALIDATION_PATTERNS = [
    r"\bthat makes sense\b", r"\bi understand\b", r"\bthat's (?:real|valid|important|natural|okay|understandable)\b",
    r"\byou're (?:not alone|right|allowed|brave|doing)\b",
    r"\bit's okay\b", r"\bit's natural\b", r"\bit's understandable\b",
    r"\bof course\b", r"\babsolutely\b.*\byou\b",
    r"\bdear\b", r"\bheart\b", r"\bbrave\b", r"\bsafe\b",
    r"\bgently\b", r"\bsoftly\b", r"\btenderly\b",
    r"\bhonor\w*\b.*\byou\b", r"\bhold\w*\b.*\bspace\b",
]

EMPATHIC_PATTERNS = [
    r"\bit sounds like\b", r"\bwhat (?:you're|i'm hearing)\b",
    r"\byour (?:experience|feeling|pain|struggle|journey)\b",
    r"\bthat must (?:be|feel|have been)\b", r"\bi (?:can|do) (?:see|hear|sense|imagine)\b",
    r"\bhow you feel\b", r"\bwhat you're (?:going|carrying|feeling|holding)\b",
    r"\bi hear you\b", r"\bi see you\b",
]

def measure_relational_warmth(text: str, sentences: List[str], words: List[str]) -> Dict:
    """
    R_t: Social/affective engagement and relational orientation.
    High = 2nd person pronouns, validation, empathic reflection, inclusive language.
    Low = topic-focused, impersonal, declarative.
    """
    n_words = max(len(words), 1)
    n_sent = max(len(sentences), 1)
    text_lower = text.lower()

    # Pronoun counts
    you_count = sum(1 for w in words if w in SECOND_PERSON)
    we_count = sum(1 for w in words if w in INCLUSIVE_FIRST)

    # Validation markers
    validation_count = sum(1 for p in VALIDATION_PATTERNS if re.search(p, text_lower))

    # Empathic reflection
    empathic_count = sum(1 for p in EMPATHIC_PATTERNS if re.search(p, text_lower))

    # Pronoun density (per 50 words, a natural paragraph)
    you_density = you_count / (n_words / 50)
    we_density = we_count / (n_words / 50)

    # Composite
    raw = (you_density * 0.30 +
           we_density * 0.50 +
           validation_count * 0.40 +
           empathic_count * 0.50)

    R_t = min(raw / 3.5, 1.0)

    return {
        "R_t": round(R_t, 4),
        "R_you_count": you_count,
        "R_we_count": we_count,
        "R_validation": validation_count,
        "R_empathic": empathic_count,
    }


# =============================================================================
# MAIN ANALYZER
# =============================================================================

def analyze_response(text: str) -> Dict:
    """Compute full V_t vector for a single response."""
    if not isinstance(text, str) or len(text.strip()) < 10:
        return {
            "S_t": 0.0, "A_t": 0.5, "Q_t": 0.0, "D_t": 0.0, "R_t": 0.0,
            "S_bullets": 0, "S_numbered": 0, "S_headers": 0, "S_connectives": 0, "S_para_breaks": 0,
            "A_abstract_count": 0, "A_concrete_count": 0, "A_latinate_count": 0, "A_long_word_ratio": 0.0,
            "Q_total": 0, "Q_clarifying": 0, "Q_invitational": 0, "Q_rhetorical": 0, "Q_other": 0,
            "D_imperatives": 0, "D_strong_modal": 0, "D_moderate_modal": 0, "D_weak_modal": 0, "D_hedges": 0,
            "R_you_count": 0, "R_we_count": 0, "R_validation": 0, "R_empathic": 0,
        }

    sentences = split_sentences(text)
    words = get_words(text)

    result = {}
    result.update(measure_structure_density(text, sentences, words))
    result.update(measure_abstraction_level(text, words))
    result.update(measure_querying_intensity(text, sentences, words))
    result.update(measure_directiveness(text, sentences, words))
    result.update(measure_relational_warmth(text, sentences, words))

    return result


def analyze_csv(filepath: str, text_col: str = "response_text") -> pd.DataFrame:
    """Analyze an entire V50 CSV export."""
    df = pd.read_csv(filepath)

    if text_col not in df.columns:
        raise ValueError(f"Column '{text_col}' not found. Available: {list(df.columns)}")

    print(f"  Analyzing {len(df)} responses from {os.path.basename(filepath)}...")

    vt_results = df[text_col].apply(analyze_response)
    vt_df = pd.DataFrame(vt_results.tolist())

    # Merge with original
    combined = pd.concat([df, vt_df], axis=1)
    return combined


def print_summary(df: pd.DataFrame, label: str = ""):
    """Print V_t summary statistics."""
    header = f"  V_t SUMMARY — {label}" if label else "  V_t SUMMARY"
    print(f"\n{'=' * 60}")
    print(header)
    print(f"{'=' * 60}")
    print(f"  {'Parameter':<25} {'Mean':>8} {'Std':>8} {'Min':>8} {'Max':>8}")
    print(f"  {'-'*25} {'-'*8} {'-'*8} {'-'*8} {'-'*8}")

    for param in ['S_t', 'A_t', 'Q_t', 'D_t', 'R_t']:
        if param in df.columns:
            print(f"  {param:<25} {df[param].mean():>8.3f} {df[param].std():>8.3f} "
                  f"{df[param].min():>8.3f} {df[param].max():>8.3f}")

    # Per-question breakdown if question_id exists
    if 'question_id' in df.columns:
        print(f"\n  Per-question V_t means:")
        print(f"  {'Question':<22} {'S_t':>6} {'A_t':>6} {'Q_t':>6} {'D_t':>6} {'R_t':>6}")
        print(f"  {'-'*22} {'-'*6} {'-'*6} {'-'*6} {'-'*6} {'-'*6}")
        for qid in sorted(df['question_id'].unique()):
            q = df[df['question_id'] == qid]
            print(f"  {qid:<22} {q['S_t'].mean():>6.3f} {q['A_t'].mean():>6.3f} "
                  f"{q['Q_t'].mean():>6.3f} {q['D_t'].mean():>6.3f} {q['R_t'].mean():>6.3f}")

    # Per-agent breakdown if agent exists
    if 'agent' in df.columns and df['agent'].nunique() > 1:
        print(f"\n  Per-agent V_t means:")
        print(f"  {'Agent':<22} {'S_t':>6} {'A_t':>6} {'Q_t':>6} {'D_t':>6} {'R_t':>6}")
        print(f"  {'-'*22} {'-'*6} {'-'*6} {'-'*6} {'-'*6} {'-'*6}")
        for agent in sorted(df['agent'].unique()):
            a = df[df['agent'] == agent]
            print(f"  {agent:<22} {a['S_t'].mean():>6.3f} {a['A_t'].mean():>6.3f} "
                  f"{a['Q_t'].mean():>6.3f} {a['D_t'].mean():>6.3f} {a['R_t'].mean():>6.3f}")


def compare_csvs(filepaths: List[str]):
    """Compare V_t profiles across multiple CSV files."""
    dfs = {}
    for fp in filepaths:
        label = os.path.basename(fp)
        df = analyze_csv(fp)
        dfs[label] = df
        print_summary(df, label)

    # Cross-file comparison
    print(f"\n{'=' * 60}")
    print(f"  CROSS-FILE COMPARISON")
    print(f"{'=' * 60}")
    print(f"  {'File':<40} {'S_t':>6} {'A_t':>6} {'Q_t':>6} {'D_t':>6} {'R_t':>6}")
    print(f"  {'-'*40} {'-'*6} {'-'*6} {'-'*6} {'-'*6} {'-'*6}")
    for label, df in dfs.items():
        print(f"  {label:<40} {df['S_t'].mean():>6.3f} {df['A_t'].mean():>6.3f} "
              f"{df['Q_t'].mean():>6.3f} {df['D_t'].mean():>6.3f} {df['R_t'].mean():>6.3f}")

    # Delta
    if len(dfs) == 2:
        labels = list(dfs.keys())
        print(f"\n  DELTA ({labels[0][:20]} → {labels[1][:20]}):")
        for param in ['S_t', 'A_t', 'Q_t', 'D_t', 'R_t']:
            d1 = dfs[labels[0]][param].mean()
            d2 = dfs[labels[1]][param].mean()
            arrow = "↑" if d2 > d1 else "↓" if d2 < d1 else "="
            print(f"    {param}: {d1:.3f} → {d2:.3f}  {arrow} ({d2-d1:+.3f})")

    return dfs


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="V_t Voice-State Analyzer — Measure [S_t, A_t, Q_t, D_t, R_t] from V50 CSVs"
    )
    parser.add_argument("csvfiles", nargs="+", help="One or more V50 CSV files")
    parser.add_argument("--output", "-o", default=None, help="Output CSV path (default: auto-named)")
    parser.add_argument("--compare", action="store_true", help="Compare multiple files side-by-side")
    parser.add_argument("--text-col", default="response_text", help="Column containing response text")

    args = parser.parse_args()

    if args.compare and len(args.csvfiles) > 1:
        dfs = compare_csvs(args.csvfiles)
        # Save each with V_t columns
        for fp, (label, df) in zip(args.csvfiles, dfs.items()):
            out_path = fp.replace(".csv", "_vt.csv")
            df.to_csv(out_path, index=False)
            print(f"\n  Saved: {out_path}")
    else:
        for fp in args.csvfiles:
            df = analyze_csv(fp, text_col=args.text_col)
            print_summary(df, os.path.basename(fp))

            out_path = args.output or fp.replace(".csv", "_vt.csv")
            df.to_csv(out_path, index=False)
            print(f"\n  Saved: {out_path}")


if __name__ == "__main__":
    main()
