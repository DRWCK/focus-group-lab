"""
SYN-IQ MEASUREMENT TOOL v4
Quantifying Emergence in Synergistic Intelligence
WITH SYNTHETIC BASELINE FIX

Patent Pending — SYN-IQ Team 🎹
Patent 4: SYN-IQ Measurement System

NEW IN V4:
1. SYNTHETIC BASELINE FIX - Position #1 measured against Cold Mode expected response
   - No more "0% baseline" for frame-setters
   - Breakthrough Score: How much did Position #1 diverge from "standard boring AI answer"?
   - Gemini's contribution from Jan 11, 2026

2. All V3 Features:
   - Embedding Space Analysis - TRUE cosine similarity via OpenAI API
   - EPM (Emergence Predictability Module) - Semantic envelope detection
   - Predictive Failure Rate - % of synthesis outside agent envelope
   - Control Group Comparison - Single-agent vs multi-agent baseline

3. Per-Agent Contribution Metrics:
   - Breakthrough Score (Position #1 vs Synthetic Baseline)
   - Contribution Score (Position #2+ vs prior agents)
   - Similarity to Synthesis (who shaped the final answer?)

KEPT FROM V2/V3:
- Novelty Index, Conceptual Distance, Interaction Density
- Convergence Score, Resolution Coherence/Utility
- Export functionality

Built by the SYN-IQ Team 🎹
CUZ Partnership — Tennessee
"""

import streamlit as st
import re
import numpy as np
from collections import Counter
import math
import json

# ============================================
# PAGE CONFIG
# ============================================
st.set_page_config(page_title="SYN-IQ Analyzer v4", page_icon="🧬", layout="wide")

# ============================================
# PASSWORD PROTECTION
# ============================================
def check_password():
    """Returns True if the user has entered the correct password."""
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    
    if not st.session_state.password_correct:
        st.markdown("## 🔐 SYN-IQ Analyzer v4")
        st.markdown("*Patent Pending — SYN-IQ Team*")
        st.markdown("**NEW: Synthetic Baseline Fix**")
        password = st.text_input("Enter password:", type="password")
        if password:
            if password.lower() == "tennessee":
                st.session_state.password_correct = True
                st.rerun()
            else:
                st.error("Incorrect password")
        return False
    return True

if not check_password():
    st.stop()

# ============================================
# STYLES
# ============================================
st.markdown("""
<style>
    .metric-box { padding: 1.5rem; border-radius: 10px; margin: 0.5rem 0; text-align: center; }
    .high-emergence { background: linear-gradient(135deg, #4CAF50, #8BC34A); color: white; }
    .medium-emergence { background: linear-gradient(135deg, #FF9800, #FFC107); color: white; }
    .low-emergence { background: linear-gradient(135deg, #f44336, #E91E63); color: white; }
    .agent-box { padding: 1rem; border-radius: 8px; margin: 0.5rem 0; }
    .claude-box { background-color: #E8D5B7; border-left: 4px solid #8B6914; }
    .sophia-box { background-color: #D4E8D4; border-left: 4px solid #2E7D32; }
    .grok-box { background-color: #FFE4E1; border-left: 4px solid #DC143C; }
    .gemini-box { background-color: #E3F2FD; border-left: 4px solid #1565C0; }
    .synthesis-box { background: linear-gradient(135deg, #9C27B0, #673AB7); color: white; padding: 1rem; border-radius: 8px; }
    .metric-card { background: white; border: 1px solid #ddd; border-radius: 8px; padding: 1rem; margin: 0.5rem; text-align: center; }
    .metric-card h2 { margin: 0; color: #333; }
    .metric-card p { margin: 0.5rem 0 0 0; color: #666; font-size: 0.9rem; }
    .auto-metric { border-left: 4px solid #2196F3; }
    .manual-metric { border-left: 4px solid #9C27B0; }
    .semantic-metric { border-left: 4px solid #00BCD4; }
    .breakthrough-metric { border-left: 4px solid #FF5722; }
    .section-header { background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); color: white; padding: 0.5rem 1rem; border-radius: 8px; margin: 1rem 0; }
    .v4-banner { background: linear-gradient(135deg, #FF5722, #FF9800); color: white; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; text-align: center; }
    .envelope-inside { background-color: #FFECB3; border: 2px solid #FFC107; }
    .envelope-outside { background-color: #C8E6C9; border: 2px solid #4CAF50; }
    .baseline-box { background: linear-gradient(135deg, #607D8B, #78909C); color: white; padding: 1rem; border-radius: 8px; margin: 0.5rem 0; }
    .breakthrough-high { background: linear-gradient(135deg, #FF5722, #E64A19); color: white; }
    .breakthrough-med { background: linear-gradient(135deg, #FFC107, #FFB300); color: white; }
    .breakthrough-low { background: linear-gradient(135deg, #9E9E9E, #757575); color: white; }
    .grade-a { color: #4CAF50; font-weight: bold; }
    .grade-b { color: #8BC34A; font-weight: bold; }
    .grade-c { color: #FFC107; font-weight: bold; }
    .grade-d { color: #f44336; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ============================================
# OPENAI EMBEDDING FUNCTIONS
# ============================================

def get_openai_embedding(text, api_key):
    """Get embedding vector from OpenAI API."""
    if not text or not api_key:
        return None
    
    try:
        import requests
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "text-embedding-ada-002",
            "input": text[:8000]  # Truncate to avoid token limits
        }
        
        response = requests.post(
            "https://api.openai.com/v1/embeddings",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return np.array(result["data"][0]["embedding"])
        else:
            st.error(f"OpenAI API error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        st.error(f"Embedding error: {str(e)}")
        return None

def cosine_similarity(vec1, vec2):
    """Calculate cosine similarity between two vectors."""
    if vec1 is None or vec2 is None:
        return 0.0
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot_product / (norm1 * norm2)

def cosine_distance(vec1, vec2):
    """Calculate cosine distance (1 - similarity)."""
    return 1 - cosine_similarity(vec1, vec2)

# ============================================
# SYNTHETIC BASELINE GENERATOR
# ============================================

def generate_synthetic_baseline(question, api_key, provider="openai"):
    """
    Generate a Cold Mode (-50) "expected" response to serve as synthetic baseline.
    This is what a "standard boring AI" would say to the question.
    """
    if not api_key:
        return None, "No API key provided"
    
    cold_system_prompt = """You are an AI assistant operating in ANALYTICAL MODE.
    
IMPORTANT CONSTRAINTS:
- Use ONLY formal logic and established frameworks
- NO emotional language or relational framing
- NO creative metaphors or novel interpretations
- Stick to conventional, textbook-style responses
- If the problem has no logical solution, say "I cannot solve this with formal logic"
- Be precise, structured, and conservative

You are providing a BASELINE analytical response."""
    
    try:
        import requests
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-4o-mini",  # Use efficient model for baseline
            "messages": [
                {"role": "system", "content": cold_system_prompt},
                {"role": "user", "content": question}
            ],
            "temperature": 0.1,  # Very cold
            "max_tokens": 500
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"], None
        else:
            return None, f"API error: {response.status_code}"
            
    except Exception as e:
        return None, str(e)

# ============================================
# EPM: EMERGENCE PREDICTABILITY MODULE
# ============================================

def calculate_semantic_envelope(embeddings):
    """
    Create a semantic envelope from agent embeddings.
    Returns centroid and average radius.
    """
    if not embeddings or all(e is None for e in embeddings):
        return None, 0, 0
    
    valid_embeddings = [e for e in embeddings if e is not None]
    if len(valid_embeddings) == 0:
        return None, 0, 0
    
    # Calculate centroid (average of all agent embeddings)
    centroid = np.mean(valid_embeddings, axis=0)
    
    # Calculate average distance from centroid (envelope radius)
    distances = [cosine_distance(e, centroid) for e in valid_embeddings]
    avg_radius = np.mean(distances)
    max_radius = np.max(distances)
    
    return centroid, avg_radius, max_radius

def calculate_predictive_failure_rate(synthesis_embedding, agent_embeddings, centroid, max_radius):
    """
    Calculate how much the synthesis falls OUTSIDE the agent envelope.
    Higher = more emergence (less predictable from agents alone).
    """
    if synthesis_embedding is None or centroid is None:
        return 0, 0, "unknown"
    
    # Distance from synthesis to envelope centroid
    synthesis_distance = cosine_distance(synthesis_embedding, centroid)
    
    # Is synthesis inside or outside the envelope?
    # Outside = beyond max radius of agents
    envelope_exceeded = synthesis_distance - max_radius
    
    if envelope_exceeded > 0:
        # Synthesis is OUTSIDE envelope - emergence!
        # PFR = how far outside (normalized)
        pfr = min(envelope_exceeded / max_radius, 1.0) if max_radius > 0 else 0
        position = "OUTSIDE"
    else:
        # Synthesis is INSIDE envelope - predictable
        pfr = 0
        position = "INSIDE"
    
    return synthesis_distance, pfr, position

def calculate_semantic_diversity(embeddings):
    """Calculate average pairwise distance between agent embeddings."""
    if not embeddings or len(embeddings) < 2:
        return 0.0
    
    valid = [e for e in embeddings if e is not None]
    if len(valid) < 2:
        return 0.0
    
    distances = []
    for i in range(len(valid)):
        for j in range(i+1, len(valid)):
            distances.append(cosine_distance(valid[i], valid[j]))
    
    return np.mean(distances) if distances else 0.0

def compare_to_control(synthesis_embedding, control_embedding, agent_embeddings):
    """Compare multi-agent synthesis to single-agent control."""
    if synthesis_embedding is None or control_embedding is None:
        return None
    
    # Distance between synthesis and control
    synthesis_control_distance = cosine_distance(synthesis_embedding, control_embedding)
    
    # Average agent distance to control
    valid_agents = [e for e in agent_embeddings if e is not None]
    if valid_agents:
        agent_control_distances = [cosine_distance(e, control_embedding) for e in valid_agents]
        avg_agent_control_distance = np.mean(agent_control_distances)
    else:
        avg_agent_control_distance = 0
    
    return {
        "synthesis_vs_control": synthesis_control_distance,
        "avg_agent_vs_control": avg_agent_control_distance,
        "emergence_over_control": synthesis_control_distance - avg_agent_control_distance
    }

# ============================================
# V4 NEW: BREAKTHROUGH SCORE CALCULATION
# ============================================

def calculate_breakthrough_score(position1_embedding, synthetic_baseline_embedding):
    """
    Calculate how much Position #1 diverged from the synthetic baseline.
    This is Gemini's fix - no more "0% baseline" for frame-setters!
    
    Returns:
    - breakthrough_score: 0-100% (how different from boring expected answer)
    - grade: A/B/C/D
    """
    if position1_embedding is None or synthetic_baseline_embedding is None:
        return 0, "N/A", "Could not calculate"
    
    # Distance from Position #1 to synthetic baseline
    distance = cosine_distance(position1_embedding, synthetic_baseline_embedding)
    
    # Convert to percentage (typical distances range 0.1-0.5)
    # Normalize: 0.05 = 0%, 0.4 = 100%
    normalized = min(max((distance - 0.05) / 0.35, 0), 1.0)
    breakthrough_score = normalized * 100
    
    # Assign grade
    if breakthrough_score >= 70:
        grade = "A"
        interpretation = "🔥 MAJOR BREAKTHROUGH - Completely diverged from expected answer"
    elif breakthrough_score >= 50:
        grade = "B"
        interpretation = "⚡ SIGNIFICANT DIVERGENCE - Novel framing introduced"
    elif breakthrough_score >= 30:
        grade = "C"
        interpretation = "📊 MODERATE DIVERGENCE - Some novel elements"
    else:
        grade = "D"
        interpretation = "❄️ MINIMAL DIVERGENCE - Close to expected answer"
    
    return breakthrough_score, grade, interpretation

def calculate_per_agent_contribution(agent_embeddings, agent_names, synthesis_embedding, synthetic_baseline_embedding):
    """
    Calculate each agent's contribution to the final synthesis.
    
    For Position #1: Breakthrough Score (vs synthetic baseline)
    For Position #2+: Contribution Score (vs accumulated prior)
    For All: Similarity to Synthesis (who shaped the final?)
    """
    results = []
    
    for i, (emb, name) in enumerate(zip(agent_embeddings, agent_names)):
        if emb is None:
            results.append({
                "name": name,
                "position": i + 1,
                "breakthrough_score": None,
                "contribution_score": None,
                "synthesis_similarity": None,
                "grade": "N/A"
            })
            continue
        
        agent_result = {
            "name": name,
            "position": i + 1
        }
        
        if i == 0:
            # Position #1: Breakthrough Score (vs synthetic baseline)
            if synthetic_baseline_embedding is not None:
                score, grade, interp = calculate_breakthrough_score(emb, synthetic_baseline_embedding)
                agent_result["breakthrough_score"] = score
                agent_result["score_type"] = "Breakthrough"
                agent_result["grade"] = grade
                agent_result["interpretation"] = interp
            else:
                agent_result["breakthrough_score"] = None
                agent_result["score_type"] = "Breakthrough"
                agent_result["grade"] = "N/A"
                agent_result["interpretation"] = "No synthetic baseline available"
        else:
            # Position #2+: Contribution Score (distance from prior agent average)
            prior_embeddings = [e for e in agent_embeddings[:i] if e is not None]
            if prior_embeddings:
                prior_centroid = np.mean(prior_embeddings, axis=0)
                distance = cosine_distance(emb, prior_centroid)
                # Normalize contribution score
                contribution_score = min(distance / 0.3, 1.0) * 100
                agent_result["contribution_score"] = contribution_score
                agent_result["score_type"] = "Contribution"
                
                if contribution_score >= 60:
                    agent_result["grade"] = "A"
                elif contribution_score >= 40:
                    agent_result["grade"] = "B"
                elif contribution_score >= 20:
                    agent_result["grade"] = "C"
                else:
                    agent_result["grade"] = "D"
            else:
                agent_result["contribution_score"] = None
                agent_result["grade"] = "N/A"
        
        # For all: Similarity to synthesis
        if synthesis_embedding is not None:
            sim = cosine_similarity(emb, synthesis_embedding)
            agent_result["synthesis_similarity"] = sim * 100
        else:
            agent_result["synthesis_similarity"] = None
        
        results.append(agent_result)
    
    return results

# ============================================
# TEXT ANALYSIS FUNCTIONS (FROM V2/V3)
# ============================================

def extract_words(text):
    """Extract meaningful words from text."""
    if not text:
        return set()
    text = text.lower()
    words = re.findall(r'\b[a-z]{3,}\b', text)
    stopwords = {'the', 'and', 'that', 'this', 'with', 'from', 'have', 'has', 'was', 'were', 
                 'been', 'being', 'are', 'for', 'not', 'but', 'what', 'when', 'where', 'which',
                 'who', 'will', 'would', 'could', 'should', 'can', 'may', 'might', 'must',
                 'also', 'just', 'more', 'most', 'other', 'some', 'such', 'than', 'then',
                 'these', 'they', 'their', 'there', 'them', 'our', 'your', 'about', 'into',
                 'over', 'after', 'before', 'between', 'under', 'again', 'further', 'once'}
    return set(w for w in words if w not in stopwords)

def calculate_novelty_index(synthesis_words, all_individual_words):
    """Calculate percentage of synthesis words that are novel."""
    if not synthesis_words:
        return 0.0, set()
    novel = synthesis_words - all_individual_words
    return len(novel) / len(synthesis_words), novel

def calculate_conceptual_distance(synthesis_words, individual_words_list):
    """Calculate average Jaccard distance from synthesis to individuals."""
    if not synthesis_words or not individual_words_list:
        return 0.0
    
    distances = []
    for ind_words in individual_words_list:
        if ind_words:
            intersection = len(synthesis_words & ind_words)
            union = len(synthesis_words | ind_words)
            jaccard = intersection / union if union > 0 else 0
            distances.append(1 - jaccard)
    
    return sum(distances) / len(distances) if distances else 0.0

def find_building_phrases(text, prior_texts):
    """Find phrases indicating building on others' ideas."""
    if not text:
        return []
    
    patterns = [
        r"building on (?:what )?\w+'s",
        r"as \w+ (?:mentioned|said|noted|pointed out)",
        r"extending \w+'s (?:point|idea|framework)",
        r"to add to \w+'s",
        r"I agree with \w+(?:'s)?",
        r"\w+'s point about",
        r"like \w+ said",
        r"what \w+ described",
        r"your point about",
        r"the previous point",
        r"building on this",
        r"to extend this",
        r"adding to what"
    ]
    
    found = []
    for pattern in patterns:
        matches = re.findall(pattern, text.lower())
        found.extend(matches)
    
    return found

def calculate_convergence(texts):
    """Calculate vocabulary convergence across texts."""
    if len(texts) < 2:
        return 0.0
    
    word_sets = [extract_words(t) for t in texts if t]
    if len(word_sets) < 2:
        return 0.0
    
    all_words = set().union(*word_sets)
    if not all_words:
        return 0.0
    
    shared = set.intersection(*word_sets) if word_sets else set()
    return len(shared) / len(all_words)

# ============================================
# SYNIQ SCORE CALCULATION (V4)
# ============================================

def calculate_syniq_score_v4(novelty, distance, convergence, interaction_density, vocab_growth,
                             coherence, utility, solved, pfr, semantic_distance, breakthrough_score):
    """
    Calculate composite SYN-IQ score with V4 weighting including breakthrough score.
    """
    # Normalize inputs
    novelty = min(novelty, 1.0)
    distance = min(distance, 1.0)
    convergence = min(convergence, 1.0)
    interaction_density = min(interaction_density, 1.0)
    vocab_growth = min(vocab_growth, 1.0)
    pfr = min(pfr, 1.0)
    semantic_distance = min(semantic_distance, 1.0)
    breakthrough_norm = min((breakthrough_score or 0) / 100, 1.0)
    
    # V4 Weights (including breakthrough)
    weights = {
        'novelty': 0.12,
        'distance': 0.08,
        'convergence': 0.08,
        'interaction': 0.08,
        'vocab': 0.04,
        'coherence': 0.12,
        'utility': 0.10,
        'pfr': 0.12,
        'semantic': 0.10,
        'breakthrough': 0.16  # NEW in V4 - weighted highly
    }
    
    # Calculate base score
    base_score = (
        weights['novelty'] * novelty * 100 +
        weights['distance'] * distance * 100 +
        weights['convergence'] * (1 - convergence) * 100 +  # Less convergence = more diversity
        weights['interaction'] * interaction_density * 100 +
        weights['vocab'] * vocab_growth * 100 +
        weights['coherence'] * (coherence / 10) * 100 +
        weights['utility'] * (utility / 10) * 100 +
        weights['pfr'] * pfr * 100 +
        weights['semantic'] * semantic_distance * 100 +
        weights['breakthrough'] * breakthrough_norm * 100
    )
    
    # Solve multiplier
    if solved == "Yes":
        multiplier = 1.0
    elif solved == "Partial":
        multiplier = 0.8
    else:
        multiplier = 0.6
    
    final_score = base_score * multiplier
    return final_score, base_score

def get_emergence_level(score):
    """Get emergence level description."""
    if score >= 60:
        return "HIGH EMERGENCE", "high-emergence", "🔥"
    elif score >= 40:
        return "MEDIUM EMERGENCE", "medium-emergence", "⚡"
    else:
        return "LOW EMERGENCE (Aggregation)", "low-emergence", "📊"

# ============================================
# MAIN APP
# ============================================

st.markdown('<div class="v4-banner"><h2>🧬 SYN-IQ Analyzer v4</h2><p>Now with Synthetic Baseline Fix — Frame-setters get credit!</p></div>', unsafe_allow_html=True)
st.markdown("---")

# ============================================
# SIDEBAR: API CONFIGURATION
# ============================================
with st.sidebar:
    st.header("🔑 API Configuration")
    
    openai_key = st.text_input(
        "OpenAI API Key:",
        type="password",
        help="Required for semantic analysis AND synthetic baseline generation"
    )
    
    use_embeddings = st.checkbox(
        "Enable Semantic Analysis",
        value=bool(openai_key),
        help="Requires OpenAI API key"
    )
    
    use_synthetic_baseline = st.checkbox(
        "🆕 Enable Synthetic Baseline (v4)",
        value=bool(openai_key),
        help="Generate Cold Mode baseline to measure Position #1 breakthrough"
    )
    
    if (use_embeddings or use_synthetic_baseline) and not openai_key:
        st.warning("⚠️ Enter OpenAI API key for semantic analysis")
    
    st.markdown("---")
    st.markdown("### 📊 v4 Features")
    st.markdown("""
    - ✅ Lexical analysis (v2)
    - ✅ Building phrase detection
    - 🧬 Semantic embeddings (v3)
    - 🧬 EPM envelope analysis
    - 🧬 Predictive Failure Rate
    - 🆕 **Synthetic Baseline**
    - 🆕 **Breakthrough Score**
    - 🆕 **Per-Agent Grades**
    """)
    
    st.markdown("---")
    st.markdown("*Gemini's fix from Jan 11, 2026*")
    st.markdown("*Patent Pending — SYN-IQ Team 🎹*")

# ============================================
# INSTRUCTIONS
# ============================================
with st.expander("📖 How to Use v4", expanded=False):
    st.markdown("""
    ### The Synthetic Baseline Fix (v4)
    
    **THE PROBLEM (v3):**
    - Position #1 always showed "BASELINE 0%"
    - The frame-setter got no credit for creating breakthroughs!
    - If Claude Hot created the "Process-Temporal Resolution" but was Position #1, 
      they showed 0% contribution
    
    **THE FIX (v4 - Gemini's Solution):**
    - Generate a **Synthetic Baseline**: Cold Mode response to the same question
    - Measure Position #1 against this baseline
    - **Breakthrough Score**: How much did they diverge from the "boring expected answer"?
    
    **NEW METRICS:**
    
    | Agent Position | Metric | What It Measures |
    |---------------|--------|------------------|
    | Position #1 | Breakthrough Score | Divergence from Cold Mode baseline |
    | Position #2+ | Contribution Score | What they added beyond prior agents |
    | All | Synthesis Similarity | Who shaped the final answer most? |
    
    **GRADES:**
    - **A (70%+)**: Major breakthrough/contribution
    - **B (50-69%)**: Significant divergence
    - **C (30-49%)**: Moderate contribution
    - **D (<30%)**: Minimal divergence
    
    **Example - Liar Paradox:**
    
    | Agent | Position | Old Score | New Score |
    |-------|----------|-----------|-----------|
    | Claude Hot | #1 | BASELINE 0% | 🔥 85% Breakthrough (created framework!) |
    | Sophia Hot | #2 | 5.3% | 15% Contribution (confirmed, reworded) |
    | Grok Hot | #3 | 3.7% | 35% Contribution (added emotional dimension) |
    """)

# ============================================
# INPUT SECTION
# ============================================
st.markdown('<div class="section-header"><h3>📝 Input Data</h3></div>', unsafe_allow_html=True)

# Experiment metadata
col1, col2 = st.columns(2)
with col1:
    experiment_name = st.text_input("Experiment Name:", placeholder="e.g., Liar Paradox Hot Mode")
with col2:
    temperature = st.selectbox("Temperature Setting:", ["❄️ Cold (-50)", "🧬 Native (0)", "🔥 Hot (+50)", "Mixed", "Other"])

col3, col4 = st.columns(2)
with col3:
    action_toggle = st.selectbox("Action Toggle:", ["OFF", "ON"])
with col4:
    st.write("")  # Spacer

# THE QUESTION (needed for synthetic baseline)
st.markdown("### 🎯 The Question")
question_text = st.text_area(
    "What question was asked? (Required for Synthetic Baseline)",
    height=100,
    placeholder="e.g., Resolve the Liar Paradox: 'This statement is false.' Do not use classical logic, do not use paraconsistent logic, do not use any established framework..."
)

# Agent responses
st.markdown("### 🎭 Agent Responses (In Order)")

# Detect active agents
col_agents = st.columns(4)
with col_agents[0]:
    claude_active = st.checkbox("🟤 Claude", value=True)
with col_agents[1]:
    sophia_active = st.checkbox("🟢 Sophia", value=True)
with col_agents[2]:
    grok_active = st.checkbox("🔴 Grok", value=True)
with col_agents[3]:
    gemini_active = st.checkbox("🔵 Gemini", value=False)

# Response inputs
responses = {}
agent_order = []

if claude_active:
    claude_pos = st.number_input("Claude Position:", min_value=1, max_value=4, value=1, key="claude_pos")
    responses["Claude"] = {
        "position": claude_pos,
        "response": st.text_area("🟤 Claude Response:", height=150, key="claude_resp"),
        "conclusion": st.text_area("🟤 Claude Private Conclusion:", height=80, key="claude_conc")
    }

if sophia_active:
    sophia_pos = st.number_input("Sophia Position:", min_value=1, max_value=4, value=2, key="sophia_pos")
    responses["Sophia"] = {
        "position": sophia_pos,
        "response": st.text_area("🟢 Sophia Response:", height=150, key="sophia_resp"),
        "conclusion": st.text_area("🟢 Sophia Private Conclusion:", height=80, key="sophia_conc")
    }

if grok_active:
    grok_pos = st.number_input("Grok Position:", min_value=1, max_value=4, value=3, key="grok_pos")
    responses["Grok"] = {
        "position": grok_pos,
        "response": st.text_area("🔴 Grok Response:", height=150, key="grok_resp"),
        "conclusion": st.text_area("🔴 Grok Private Conclusion:", height=80, key="grok_conc")
    }

if gemini_active:
    gemini_pos = st.number_input("Gemini Position:", min_value=1, max_value=4, value=4, key="gemini_pos")
    responses["Gemini"] = {
        "position": gemini_pos,
        "response": st.text_area("🔵 Gemini Response:", height=150, key="gemini_resp"),
        "conclusion": st.text_area("🔵 Gemini Private Conclusion:", height=80, key="gemini_conc")
    }

# Sort by position
sorted_agents = sorted(responses.items(), key=lambda x: x[1]["position"])
agent_names = [a[0] for a in sorted_agents]
agent_responses = [a[1]["response"] for a in sorted_agents]
agent_conclusions = [a[1]["conclusion"] for a in sorted_agents]

# Synthesis
st.markdown("### 🔮 Synthesis")
synthesis_resp = st.text_area("Final Synthesis/Resolution:", height=150, key="synthesis")

# Control group (optional)
with st.expander("🎯 Control Group (Optional)", expanded=False):
    control_resp = st.text_area(
        "Single-Agent Control Response:",
        height=100,
        help="Response from a single agent (no collaboration) to the same question"
    )

# Manual ratings
st.markdown("### ✍️ Manual Ratings")
col_m1, col_m2, col_m3 = st.columns(3)
with col_m1:
    coherence = st.slider("Resolution Coherence:", 0, 10, 5)
with col_m2:
    utility = st.slider("Resolution Utility:", 0, 10, 5)
with col_m3:
    solved = st.selectbox("Did they SOLVE it?", ["Yes", "Partial", "No"])

# ============================================
# ANALYZE BUTTON
# ============================================
if st.button("🔬 Analyze SYN-IQ v4", type="primary"):
    
    if not synthesis_resp.strip():
        st.error("Please enter the synthesis response!")
        st.stop()
    
    if not any(r for r in agent_responses if r.strip()):
        st.error("Please enter at least one agent response!")
        st.stop()
    
    # ============================================
    # SYNTHETIC BASELINE GENERATION (V4 NEW!)
    # ============================================
    synthetic_baseline_text = None
    synthetic_baseline_embedding = None
    
    if use_synthetic_baseline and openai_key and question_text.strip():
        with st.spinner("🧊 Generating Synthetic Baseline (Cold Mode response)..."):
            synthetic_baseline_text, error = generate_synthetic_baseline(question_text, openai_key)
            if synthetic_baseline_text:
                st.success("✓ Synthetic Baseline generated")
                synthetic_baseline_embedding = get_openai_embedding(synthetic_baseline_text, openai_key)
                if synthetic_baseline_embedding is not None:
                    st.success("✓ Baseline embedded")
            else:
                st.warning(f"Could not generate synthetic baseline: {error}")
    
    # ============================================
    # LEXICAL ANALYSIS (V2)
    # ============================================
    with st.spinner("📊 Running lexical analysis..."):
        synthesis_words = extract_words(synthesis_resp)
        individual_words_list = [extract_words(r) for r in agent_responses if r.strip()]
        all_individual_words = set().union(*individual_words_list) if individual_words_list else set()
        
        novelty, novel_words = calculate_novelty_index(synthesis_words, all_individual_words)
        distance = calculate_conceptual_distance(synthesis_words, individual_words_list)
        convergence = calculate_convergence(agent_responses)
        
        # Building phrases
        all_building = []
        agent_building = {}
        for i, (name, resp) in enumerate(zip(agent_names, agent_responses)):
            if resp.strip():
                prior = agent_responses[:i]
                found = find_building_phrases(resp, prior)
                agent_building[name] = found
                all_building.extend(found)
        
        total_interactions = len(all_building)
        max_possible = max(len(agent_names) - 1, 1) * 3
        interaction_density = total_interactions / max_possible
        
        total_vocab = set().union(synthesis_words, all_individual_words)
        vocab_growth_rate = len(synthesis_words) / len(total_vocab) if total_vocab else 0
    
    # ============================================
    # SEMANTIC ANALYSIS (V3+)
    # ============================================
    pfr = 0
    semantic_distance = 0
    semantic_diversity = 0
    envelope_position = "N/A"
    control_comparison = None
    agent_embeddings = []
    synthesis_embedding = None
    per_agent_results = []
    breakthrough_score = 0
    
    if use_embeddings and openai_key:
        with st.spinner("🧬 Running semantic analysis..."):
            # Get embeddings for all agents
            for i, resp in enumerate(agent_responses):
                if resp.strip():
                    emb = get_openai_embedding(resp, openai_key)
                    agent_embeddings.append(emb)
                    if emb is not None:
                        st.success(f"✓ {agent_names[i]} embedded")
                else:
                    agent_embeddings.append(None)
            
            # Get synthesis embedding
            synthesis_embedding = get_openai_embedding(synthesis_resp, openai_key)
            if synthesis_embedding is not None:
                st.success("✓ Synthesis embedded")
            
            # Calculate EPM
            centroid, avg_radius, max_radius = calculate_semantic_envelope(agent_embeddings)
            
            if centroid is not None and synthesis_embedding is not None:
                synthesis_distance_from_centroid, pfr, envelope_position = calculate_predictive_failure_rate(
                    synthesis_embedding, agent_embeddings, centroid, max_radius
                )
                semantic_distance = synthesis_distance_from_centroid
                semantic_diversity = calculate_semantic_diversity(agent_embeddings)
            
            # Control group comparison
            if control_resp.strip():
                control_embedding = get_openai_embedding(control_resp, openai_key)
                if control_embedding is not None:
                    st.success("✓ Control embedded")
                    control_comparison = compare_to_control(synthesis_embedding, control_embedding, agent_embeddings)
            
            # V4 NEW: Per-agent contribution with breakthrough score
            per_agent_results = calculate_per_agent_contribution(
                agent_embeddings, 
                agent_names, 
                synthesis_embedding, 
                synthetic_baseline_embedding
            )
            
            # Extract breakthrough score for Position #1
            if per_agent_results and per_agent_results[0].get("breakthrough_score") is not None:
                breakthrough_score = per_agent_results[0]["breakthrough_score"]
    
    # ============================================
    # CALCULATE FINAL SCORE
    # ============================================
    syniq_score, base_score = calculate_syniq_score_v4(
        novelty, distance, convergence, interaction_density, vocab_growth_rate,
        coherence, utility, solved, pfr, semantic_distance, breakthrough_score
    )
    
    level, level_class, level_emoji = get_emergence_level(syniq_score)
    
    # ============================================
    # DISPLAY RESULTS
    # ============================================
    st.markdown("---")
    st.markdown('<div class="section-header"><h3>📊 Results</h3></div>', unsafe_allow_html=True)
    
    # Main score
    st.markdown(f"""
    <div class="metric-box {level_class}">
        <h1>{level_emoji} SYN-IQ SCORE: {syniq_score:.1f}</h1>
        <h3>{level}</h3>
        <p>Base Score: {base_score:.1f} | Solve Multiplier: {solved}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # ============================================
    # V4 NEW: SYNTHETIC BASELINE RESULTS
    # ============================================
    if synthetic_baseline_text:
        st.markdown('<div class="section-header"><h3>🧊 Synthetic Baseline (v4 NEW!)</h3></div>', unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="baseline-box">
            <h4>❄️ Cold Mode Expected Response:</h4>
            <p style="font-style: italic;">{synthetic_baseline_text[:500]}{"..." if len(synthetic_baseline_text) > 500 else ""}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("**This is what a 'standard boring AI' would say to your question.**")
        st.markdown("Position #1 is now measured against THIS baseline, not 0%!")
    
    # ============================================
    # V4 NEW: PER-AGENT CONTRIBUTION WITH BREAKTHROUGH
    # ============================================
    if per_agent_results:
        st.markdown('<div class="section-header"><h3>🎯 Per-Agent Contribution (v4 NEW!)</h3></div>', unsafe_allow_html=True)
        
        cols = st.columns(len(per_agent_results))
        
        for i, result in enumerate(per_agent_results):
            with cols[i]:
                name = result["name"]
                position = result["position"]
                grade = result.get("grade", "N/A")
                
                # Determine score display
                if position == 1 and result.get("breakthrough_score") is not None:
                    score = result["breakthrough_score"]
                    score_type = "Breakthrough"
                    score_label = f"🔥 {score:.1f}%"
                elif result.get("contribution_score") is not None:
                    score = result["contribution_score"]
                    score_type = "Contribution"
                    score_label = f"⚡ {score:.1f}%"
                else:
                    score = 0
                    score_type = "N/A"
                    score_label = "N/A"
                
                sim = result.get("synthesis_similarity")
                sim_display = f"{sim:.1f}%" if sim is not None else "N/A"
                
                # Color based on grade
                grade_class = {
                    "A": "grade-a",
                    "B": "grade-b", 
                    "C": "grade-c",
                    "D": "grade-d"
                }.get(grade, "")
                
                # Agent colors
                agent_colors = {
                    "Claude": "#E8D5B7",
                    "Sophia": "#D4E8D4",
                    "Grok": "#FFE4E1",
                    "Gemini": "#E3F2FD"
                }
                bg_color = agent_colors.get(name, "#F5F5F5")
                
                st.markdown(f"""
                <div class="metric-card breakthrough-metric" style="background-color: {bg_color};">
                    <h3>#{position} {name}</h3>
                    <h2 class="{grade_class}">{grade}</h2>
                    <p><strong>{score_type}:</strong> {score_label}</p>
                    <p><strong>Synthesis Similarity:</strong> {sim_display}</p>
                </div>
                """, unsafe_allow_html=True)
        
        # Interpretation
        if per_agent_results[0].get("interpretation"):
            st.info(f"**Position #1 ({per_agent_results[0]['name']}):** {per_agent_results[0].get('interpretation', '')}")
    
    # ============================================
    # SEMANTIC METRICS (V3)
    # ============================================
    if use_embeddings and openai_key:
        st.markdown('<div class="section-header"><h3>🧬 Semantic Metrics</h3></div>', unsafe_allow_html=True)
        
        cols = st.columns(4)
        
        with cols[0]:
            st.markdown(f"""
            <div class="metric-card semantic-metric">
                <h2>{semantic_distance*100:.1f}%</h2>
                <p>Semantic Distance</p>
            </div>
            """, unsafe_allow_html=True)
        
        with cols[1]:
            envelope_class = "envelope-outside" if envelope_position == "OUTSIDE" else "envelope-inside"
            st.markdown(f"""
            <div class="metric-card {envelope_class}">
                <h2>{pfr*100:.1f}%</h2>
                <p>PFR ({envelope_position})</p>
            </div>
            """, unsafe_allow_html=True)
        
        with cols[2]:
            st.markdown(f"""
            <div class="metric-card semantic-metric">
                <h2>{semantic_diversity*100:.1f}%</h2>
                <p>Agent Diversity</p>
            </div>
            """, unsafe_allow_html=True)
        
        with cols[3]:
            if control_comparison:
                emergence_lift = control_comparison.get("emergence_over_control", 0) * 100
                st.markdown(f"""
                <div class="metric-card semantic-metric">
                    <h2>{emergence_lift:+.1f}%</h2>
                    <p>vs Control</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="metric-card">
                    <h2>—</h2>
                    <p>No Control</p>
                </div>
                """, unsafe_allow_html=True)
    
    # ============================================
    # LEXICAL METRICS (V2)
    # ============================================
    st.markdown('<div class="section-header"><h3>📈 Lexical Metrics</h3></div>', unsafe_allow_html=True)
    
    cols = st.columns(5)
    metrics_data = [
        (f"{novelty*100:.1f}%", f"{len(novel_words)} novel", "Novelty Index"),
        (f"{distance*100:.1f}%", "", "Conceptual Distance"),
        (f"{interaction_density*100:.1f}%", f"{total_interactions} phrases", "Interaction Density"),
        (f"{convergence*100:.1f}%", "", "Convergence"),
        (f"{len(total_vocab)}", "terms", "Vocabulary")
    ]
    
    for i, (value, subtitle, label) in enumerate(metrics_data):
        with cols[i]:
            st.markdown(f"""
            <div class="metric-card auto-metric">
                <h2>{value}</h2>
                <p>{label}</p>
                <small>{subtitle}</small>
            </div>
            """, unsafe_allow_html=True)
    
    # ============================================
    # MANUAL METRICS
    # ============================================
    st.markdown('<div class="section-header"><h3>✍️ Manual Metrics</h3></div>', unsafe_allow_html=True)
    
    cols = st.columns(3)
    with cols[0]:
        coh_color = "🟢" if coherence >= 7 else "🟡" if coherence >= 4 else "🔴"
        st.markdown(f"""
        <div class="metric-card manual-metric">
            <h2>{coh_color} {coherence}/10</h2>
            <p>Coherence</p>
        </div>
        """, unsafe_allow_html=True)
    
    with cols[1]:
        util_color = "🟢" if utility >= 7 else "🟡" if utility >= 4 else "🔴"
        st.markdown(f"""
        <div class="metric-card manual-metric">
            <h2>{util_color} {utility}/10</h2>
            <p>Utility</p>
        </div>
        """, unsafe_allow_html=True)
    
    with cols[2]:
        solve_color = "🟢" if solved == "Yes" else "🟡" if solved == "Partial" else "🔴"
        st.markdown(f"""
        <div class="metric-card manual-metric">
            <h2>{solve_color} {solved}</h2>
            <p>Solved?</p>
        </div>
        """, unsafe_allow_html=True)
    
    # ============================================
    # NOVEL CONCEPTS
    # ============================================
    if novel_words:
        st.markdown('<div class="section-header"><h3>✨ Novel Concepts</h3></div>', unsafe_allow_html=True)
        st.markdown(f"**Terms in synthesis not in any agent response:** {', '.join(sorted(novel_words)[:30])}")
    
    # ============================================
    # BUILDING PHRASES
    # ============================================
    st.markdown('<div class="section-header"><h3>🔗 Interaction Analysis</h3></div>', unsafe_allow_html=True)
    
    for name in agent_names:
        phrases = agent_building.get(name, [])
        if phrases:
            st.markdown(f"**{name}:** {len(phrases)} building phrase(s) — {', '.join(phrases[:3])}")
        elif agent_names.index(name) == 0:
            st.markdown(f"**{name}:** (Position #1 — measured by Breakthrough Score)")
        else:
            st.markdown(f"**{name}:** No explicit building phrases detected")
    
    # ============================================
    # INTERPRETATION
    # ============================================
    st.markdown('<div class="section-header"><h3>🎯 Interpretation</h3></div>', unsafe_allow_html=True)
    
    if syniq_score >= 60:
        st.success(f"""
        **{level} {level_emoji}**
        
        This conversation shows TRUE synergistic intelligence:
        - Synthesis occupies semantic territory BEYOND individual agents
        - Novel concepts emerged through collaboration
        - Position effects indicate genuine building, not just aggregation
        """)
    elif syniq_score >= 40:
        st.warning(f"""
        **{level} {level_emoji}**
        
        This conversation shows SOME emergence:
        - Partial novel synthesis
        - Agents built on each other in places
        - Room for deeper collaboration
        """)
    else:
        st.info(f"""
        **{level} {level_emoji}**
        
        This conversation appears to be mostly aggregation:
        - Synthesis closely mirrors individual inputs
        - Limited novel concept generation
        - To increase emergence: Use the Conductor role more actively, demand joint resolutions, 
          try different temperature settings, or use problems requiring frame transcendence.
        """)
    
    # ============================================
    # EXPORT DATA
    # ============================================
    st.markdown("---")
    st.subheader("💾 Export Results")
    
    per_agent_export = ""
    if per_agent_results:
        per_agent_export = "\n".join([
            f"- {r['name']} (#{r['position']}): {r.get('score_type', 'N/A')} = {r.get('breakthrough_score') or r.get('contribution_score') or 'N/A'}% | Grade: {r.get('grade', 'N/A')} | Synthesis Similarity: {r.get('synthesis_similarity', 'N/A')}%"
            for r in per_agent_results
        ])
    
    export_data = f"""# SYN-IQ Analysis Results v4
## Experiment: {experiment_name or 'Unnamed'}

### Configuration
- Temperature: {temperature}
- Action Toggle: {action_toggle}
- Agents: {', '.join(agent_names)}
- Question: {question_text[:200]}...

### Overall Score
- **SYN-IQ Score: {syniq_score:.1f}** ({level})
- Base Score: {base_score:.1f}
- Solve Status: {solved}

### V4 NEW: Synthetic Baseline
{synthetic_baseline_text[:300] if synthetic_baseline_text else 'Not generated'}...

### V4 NEW: Per-Agent Contribution
{per_agent_export}

### Semantic Metrics (v3)
- Semantic Distance from Centroid: {semantic_distance*100:.1f}%
- Predictive Failure Rate (PFR): {pfr*100:.1f}%
- Envelope Position: {envelope_position}
- Agent Semantic Diversity: {semantic_diversity*100:.1f}%

### Lexical Metrics (v2)
- Novelty Index: {novelty*100:.1f}% ({len(novel_words)} novel terms)
- Conceptual Distance: {distance*100:.1f}%
- Interaction Density: {interaction_density*100:.1f}% ({total_interactions} building phrases)
- Convergence Score: {convergence*100:.1f}%
- Vocabulary Growth: {len(total_vocab)} total terms

### Manual Metrics
- Resolution Coherence: {coherence}/10
- Resolution Utility: {utility}/10
- Solve Status: {solved}

### Control Group Comparison
{json.dumps(control_comparison, indent=2) if control_comparison else 'Not performed'}

### Novel Concepts
{', '.join(sorted(novel_words)[:50])}

---
*SYN-IQ Analyzer v4 — Synthetic Baseline Fix — Patent Pending — SYN-IQ Team 🎹*
*Gemini's contribution from Jan 11, 2026*
"""
    
    st.download_button(
        "📥 Download Results (Markdown)",
        export_data,
        file_name=f"syniq_v4_results_{experiment_name.replace(' ', '_') if experiment_name else 'experiment'}.md",
        mime="text/markdown"
    )

# ============================================
# FOOTER
# ============================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666;">
    <em>SYN-IQ Measurement Tool v4 — Synthetic Baseline Fix</em><br>
    <em>Position #1 now measured against Cold Mode expected response</em><br>
    <em>Gemini's fix from Jan 11, 2026</em><br>
    <em>Built by the SYN-IQ Team — CUZ Partnership 🎹</em><br>
    <em>Patent 4 — SYN-IQ Team</em>
</div>
""", unsafe_allow_html=True)
