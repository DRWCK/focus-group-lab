"""
SYN-IQ Analyzer v4
Quantifying Emergence in Synergistic Intelligence
With Synthetic Baseline Measurement

SYNINT Team — January 2026

Features:
1. Synthetic Baseline - Position #1 measured against Cold Mode expected response
2. Semantic Embedding Analysis - Cosine similarity via OpenAI API
3. EPM (Emergence Predictability Module) - Semantic envelope detection
4. Predictive Failure Rate - Measures synthesis outside agent envelope
5. Per-Agent Contribution Metrics with grades
6. Lexical analysis (Novelty, Conceptual Distance, Interaction Density)
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
        st.markdown("*SYNINT Team*")
        st.markdown("**Emergence Measurement with Synthetic Baseline**")
        password = st.text_input("Enter password:", type="password")
        if password:
            if password == "CBURZBO2026":
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
            "input": text[:8000]
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
    """Generate a Cold Mode expected response as synthetic baseline."""
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
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": cold_system_prompt},
                {"role": "user", "content": question}
            ],
            "temperature": 0.1,
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
    """Create semantic envelope from agent embeddings."""
    if not embeddings or all(e is None for e in embeddings):
        return None, 0, 0
    
    valid_embeddings = [e for e in embeddings if e is not None]
    if len(valid_embeddings) == 0:
        return None, 0, 0
    
    centroid = np.mean(valid_embeddings, axis=0)
    distances = [cosine_distance(e, centroid) for e in valid_embeddings]
    avg_radius = np.mean(distances)
    max_radius = np.max(distances)
    
    return centroid, avg_radius, max_radius

def calculate_predictive_failure_rate(synthesis_embedding, agent_embeddings, centroid, max_radius):
    """Calculate how much synthesis falls OUTSIDE the agent envelope."""
    if synthesis_embedding is None or centroid is None:
        return 0, 0, "unknown"
    
    synthesis_distance = cosine_distance(synthesis_embedding, centroid)
    envelope_exceeded = synthesis_distance - max_radius
    
    if envelope_exceeded > 0:
        pfr = min(envelope_exceeded / max_radius, 1.0) if max_radius > 0 else 0
        position = "OUTSIDE"
    else:
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
    
    synthesis_control_distance = cosine_distance(synthesis_embedding, control_embedding)
    
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
# BREAKTHROUGH SCORE CALCULATION
# ============================================

def calculate_breakthrough_score(position1_embedding, synthetic_baseline_embedding):
    """Calculate how much Position #1 diverged from synthetic baseline."""
    if position1_embedding is None or synthetic_baseline_embedding is None:
        return 0, "N/A", "Could not calculate"
    
    distance = cosine_distance(position1_embedding, synthetic_baseline_embedding)
    normalized = min(max((distance - 0.05) / 0.35, 0), 1.0)
    breakthrough_score = normalized * 100
    
    if breakthrough_score >= 70:
        grade = "A"
        interpretation = "MAJOR BREAKTHROUGH - Completely diverged from expected answer"
    elif breakthrough_score >= 50:
        grade = "B"
        interpretation = "SIGNIFICANT DIVERGENCE - Novel framing introduced"
    elif breakthrough_score >= 30:
        grade = "C"
        interpretation = "MODERATE DIVERGENCE - Some novel elements"
    else:
        grade = "D"
        interpretation = "MINIMAL DIVERGENCE - Close to expected answer"
    
    return breakthrough_score, grade, interpretation

def calculate_per_agent_contribution(agent_embeddings, agent_names, synthesis_embedding, synthetic_baseline_embedding):
    """Calculate each agent's contribution to the final synthesis."""
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
            prior_embeddings = [e for e in agent_embeddings[:i] if e is not None]
            if prior_embeddings:
                prior_centroid = np.mean(prior_embeddings, axis=0)
                distance = cosine_distance(emb, prior_centroid)
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
        
        if synthesis_embedding is not None:
            sim = cosine_similarity(emb, synthesis_embedding)
            agent_result["synthesis_similarity"] = sim * 100
        else:
            agent_result["synthesis_similarity"] = None
        
        results.append(agent_result)
    
    return results

# ============================================
# TEXT ANALYSIS FUNCTIONS
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
    
    all_words = set.union(*word_sets)
    if not all_words:
        return 0.0
    
    shared = set.intersection(*word_sets)
    return len(shared) / len(all_words)

# ============================================
# MAIN UI
# ============================================

st.markdown("""
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1.5rem; border-radius: 10px; text-align: center; margin-bottom: 1rem;">
    <h1>SYN-IQ Analyzer v4</h1>
    <p>Now with Synthetic Baseline Fix — Frame-setters get credit!</p>
</div>
""", unsafe_allow_html=True)

with st.expander("> How to Use v4"):
    st.markdown("""
    **NEW IN V4: Synthetic Baseline Fix**
    - Position #1 (the frame-setter) is now measured against a "Cold Mode" expected response
    - No more "0% contribution" for the agent who sets the conversation direction!
    - **Breakthrough Score**: How much did Position #1 diverge from "standard boring AI answer"?
    
    **Workflow:**
    1. Enter your API key (for embeddings and synthetic baseline)
    2. Enter the question that was asked
    3. Paste each agent's response (in order!)
    4. Optionally paste a synthesis/resolution
    5. Click Analyze
    
    **Metrics Explained:**
    - **Breakthrough Score** (Position #1): Divergence from synthetic baseline (A-D grade)
    - **Contribution Score** (Position #2+): How much new content vs prior agents
    - **Synthesis Similarity**: Who shaped the final answer most?
    - **PFR**: Predictive Failure Rate - % of synthesis outside agent envelope
    """)

# Sidebar
with st.sidebar:
    st.markdown("### API Configuration")
    openai_key = st.text_input("OpenAI API Key:", type="password")
    
    enable_semantic = st.checkbox("Enable Semantic Analysis", value=True)
    enable_synthetic = st.checkbox("Enable Synthetic Baseline (v4)", value=True)
    
    st.markdown("---")
    st.markdown("### v4 Features")
    st.markdown("""
    - ✅ Lexical analysis (v2)
    - ✅ Building phrase detection
    - ✅ Semantic embeddings (v3)
    - ✅ EPM envelope analysis
    - ✅ Predictive Failure Rate
    - ✅ Synthetic Baseline
    - ✅ Breakthrough Score
    - ✅ Per-Agent Grades
    """)
    
    st.markdown("---")
    st.markdown("*SYNINT Team — January 2026*")

# Main input area
st.markdown('<div class="section-header"><h3>📥 Input Data</h3></div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    experiment_name = st.text_input("Experiment Name:", placeholder="e.g., Liar Paradox Hot Mode")
with col2:
    temperature = st.selectbox("Temperature Setting:", ["Cold (-50)", "Cool (-25)", "Neutral (0)", "Warm (+25)", "Hot (+50)"])

action_toggle = st.selectbox("Action Toggle:", ["OFF", "ON"])

# Question
st.markdown("### The Question")
question_text = st.text_area("What question was asked? (Required for Synthetic Baseline)", 
                             placeholder="e.g., Resolve the Liar Paradox: 'This statement is false.' Do not use classical logic...",
                             height=80)

# Agent responses
st.markdown("### Agent Responses (In Order)")

agent_cols = st.columns(4)
agents_active = {}
with agent_cols[0]:
    agents_active["Claude"] = st.checkbox("Claude", value=True)
with agent_cols[1]:
    agents_active["Sophia"] = st.checkbox("Sophia", value=True)
with agent_cols[2]:
    agents_active["Grok"] = st.checkbox("Grok", value=True)
with agent_cols[3]:
    agents_active["Gemini"] = st.checkbox("Gemini", value=False)

active_agents = [name for name, active in agents_active.items() if active]

# Position ordering
st.markdown("**Agent Position (Order of responses):**")
agent_positions = {}
pos_cols = st.columns(len(active_agents) if active_agents else 1)
for i, agent in enumerate(active_agents):
    with pos_cols[i]:
        agent_positions[agent] = st.number_input(f"{agent} Position:", min_value=1, max_value=4, value=i+1, key=f"pos_{agent}")

# Sort agents by position
sorted_agents = sorted(active_agents, key=lambda x: agent_positions.get(x, 99))

# Response inputs
agent_responses = {}
for agent in sorted_agents:
    box_class = f"{agent.lower()}-box"
    st.markdown(f'<div class="agent-box {box_class}"><strong>{agent} Response (Position #{agent_positions[agent]})</strong></div>', unsafe_allow_html=True)
    agent_responses[agent] = st.text_area(f"{agent}:", height=150, key=f"response_{agent}", label_visibility="collapsed")

# Synthesis
st.markdown("### Synthesis/Resolution (Optional)")
synthesis_text = st.text_area("Final synthesis or resolution:", height=150, placeholder="Paste the final synthesis or resolution here...")

# Control group
st.markdown("### Control Group (Optional)")
control_response = st.text_area("Single-agent control response:", height=100, placeholder="For comparison: what would ONE agent say alone?")

# Manual metrics
st.markdown("### Manual Metrics")
man_cols = st.columns(3)
with man_cols[0]:
    coherence = st.slider("Resolution Coherence:", 1, 10, 5)
with man_cols[1]:
    utility = st.slider("Resolution Utility:", 1, 10, 5)
with man_cols[2]:
    solved = st.selectbox("Problem Solved?", ["No", "Partial", "Yes"])

# Analyze button
if st.button("🔬 Analyze", type="primary"):
    if not any(agent_responses.values()):
        st.error("Please enter at least one agent response.")
    else:
        with st.spinner("Analyzing..."):
            # Get ordered responses
            ordered_responses = [agent_responses[a] for a in sorted_agents if agent_responses.get(a)]
            agent_names = [a for a in sorted_agents if agent_responses.get(a)]
            
            # Generate synthetic baseline if enabled
            synthetic_baseline_text = None
            synthetic_baseline_embedding = None
            if enable_synthetic and openai_key and question_text:
                with st.status("Generating synthetic baseline..."):
                    synthetic_baseline_text, error = generate_synthetic_baseline(question_text, openai_key)
                    if error:
                        st.warning(f"Could not generate baseline: {error}")
                    elif synthetic_baseline_text:
                        synthetic_baseline_embedding = get_openai_embedding(synthetic_baseline_text, openai_key)
            
            # Get embeddings if enabled
            agent_embeddings = []
            synthesis_embedding = None
            control_embedding = None
            
            if enable_semantic and openai_key:
                with st.status("Computing embeddings..."):
                    for response in ordered_responses:
                        if response:
                            emb = get_openai_embedding(response, openai_key)
                            agent_embeddings.append(emb)
                        else:
                            agent_embeddings.append(None)
                    
                    if synthesis_text:
                        synthesis_embedding = get_openai_embedding(synthesis_text, openai_key)
                    
                    if control_response:
                        control_embedding = get_openai_embedding(control_response, openai_key)
            
            # Lexical analysis
            individual_words = [extract_words(r) for r in ordered_responses]
            all_individual_words = set.union(*individual_words) if individual_words else set()
            synthesis_words = extract_words(synthesis_text) if synthesis_text else set()
            
            novelty, novel_words = calculate_novelty_index(synthesis_words, all_individual_words)
            distance = calculate_conceptual_distance(synthesis_words, individual_words)
            convergence = calculate_convergence(ordered_responses)
            
            # Building phrases
            total_interactions = 0
            agent_building = {}
            for i, (agent, response) in enumerate(zip(agent_names, ordered_responses)):
                if i > 0:
                    prior = ordered_responses[:i]
                    phrases = find_building_phrases(response, prior)
                    agent_building[agent] = phrases
                    total_interactions += len(phrases)
            
            interaction_density = total_interactions / len(ordered_responses) if ordered_responses else 0
            total_vocab = all_individual_words | synthesis_words
            
            # Semantic metrics
            semantic_distance = 0
            pfr = 0
            envelope_position = "unknown"
            semantic_diversity = 0
            control_comparison = None
            
            if enable_semantic and agent_embeddings:
                centroid, avg_radius, max_radius = calculate_semantic_envelope(agent_embeddings)
                
                if synthesis_embedding is not None and centroid is not None:
                    semantic_distance, pfr, envelope_position = calculate_predictive_failure_rate(
                        synthesis_embedding, agent_embeddings, centroid, max_radius)
                
                semantic_diversity = calculate_semantic_diversity(agent_embeddings)
                
                if control_embedding is not None:
                    control_comparison = compare_to_control(synthesis_embedding, control_embedding, agent_embeddings)
            
            # Per-agent contribution
            per_agent_results = []
            if enable_semantic and agent_embeddings:
                per_agent_results = calculate_per_agent_contribution(
                    agent_embeddings, agent_names, synthesis_embedding, synthetic_baseline_embedding)
            
            # Calculate overall score
            base_score = (novelty * 30 + distance * 30 + interaction_density * 20 + (1-convergence) * 20)
            
            if enable_semantic:
                semantic_bonus = pfr * 30 + semantic_diversity * 20
                base_score = base_score * 0.6 + semantic_bonus * 0.4
            
            solve_bonus = {"Yes": 15, "Partial": 7, "No": 0}[solved]
            manual_bonus = (coherence + utility) / 2
            
            syniq_score = min(base_score + solve_bonus + manual_bonus, 100)
            
            # Determine level
            if syniq_score >= 70:
                level = "HIGH EMERGENCE"
                level_emoji = "🔥"
            elif syniq_score >= 40:
                level = "MODERATE EMERGENCE"
                level_emoji = "⚡"
            else:
                level = "LOW EMERGENCE"
                level_emoji = "❄️"
            
            # Display results
            st.markdown("---")
            st.markdown('<div class="section-header"><h3>📊 Results</h3></div>', unsafe_allow_html=True)
            
            # Overall score
            score_class = "high-emergence" if syniq_score >= 70 else "medium-emergence" if syniq_score >= 40 else "low-emergence"
            st.markdown(f"""
            <div class="metric-box {score_class}">
                <h1 style="font-size: 4rem; margin: 0;">{syniq_score:.1f}</h1>
                <p style="font-size: 1.2rem;">SYN-IQ Score — {level} {level_emoji}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Synthetic baseline display
            if synthetic_baseline_text:
                st.markdown('<div class="section-header"><h3>🧊 Synthetic Baseline (Cold Mode Expected Response)</h3></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="baseline-box">{synthetic_baseline_text[:500]}...</div>', unsafe_allow_html=True)
            
            # Per-agent results
            if per_agent_results:
                st.markdown('<div class="section-header"><h3>👥 Per-Agent Contribution</h3></div>', unsafe_allow_html=True)
                
                for result in per_agent_results:
                    name = result["name"]
                    position = result["position"]
                    grade = result.get("grade", "N/A")
                    
                    grade_class = f"grade-{grade.lower()}" if grade in ["A", "B", "C", "D"] else ""
                    
                    if position == 1:
                        score = result.get("breakthrough_score")
                        score_type = "Breakthrough"
                        interp = result.get("interpretation", "")
                    else:
                        score = result.get("contribution_score")
                        score_type = "Contribution"
                        interp = ""
                    
                    sim = result.get("synthesis_similarity")
                    
                    st.markdown(f"""
                    <div class="agent-box {name.lower()}-box">
                        <strong>{name}</strong> (Position #{position})<br>
                        {score_type} Score: <strong>{score:.1f}%</strong> | 
                        Grade: <span class="{grade_class}">{grade}</span> |
                        Synthesis Similarity: {sim:.1f}% if sim else 'N/A'<br>
                        <em>{interp}</em>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Semantic metrics
            if enable_semantic:
                st.markdown('<div class="section-header"><h3>🧠 Semantic Metrics</h3></div>', unsafe_allow_html=True)
                
                sem_cols = st.columns(4)
                with sem_cols[0]:
                    st.markdown(f"""
                    <div class="metric-card semantic-metric">
                        <h2>{semantic_distance*100:.1f}%</h2>
                        <p>Semantic Distance</p>
                    </div>
                    """, unsafe_allow_html=True)
                with sem_cols[1]:
                    env_class = "envelope-outside" if envelope_position == "OUTSIDE" else "envelope-inside"
                    st.markdown(f"""
                    <div class="metric-card {env_class}">
                        <h2>{pfr*100:.1f}%</h2>
                        <p>PFR ({envelope_position})</p>
                    </div>
                    """, unsafe_allow_html=True)
                with sem_cols[2]:
                    st.markdown(f"""
                    <div class="metric-card semantic-metric">
                        <h2>{semantic_diversity*100:.1f}%</h2>
                        <p>Agent Diversity</p>
                    </div>
                    """, unsafe_allow_html=True)
                with sem_cols[3]:
                    if control_comparison:
                        emergence_lift = control_comparison["emergence_over_control"] * 100
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
            
            # Lexical metrics
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
            
            # Manual metrics display
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
            
            # Novel concepts
            if novel_words:
                st.markdown('<div class="section-header"><h3>✨ Novel Concepts</h3></div>', unsafe_allow_html=True)
                st.markdown(f"**Terms in synthesis not in any agent response:** {', '.join(sorted(novel_words)[:30])}")
            
            # Building phrases
            st.markdown('<div class="section-header"><h3>🔗 Interaction Analysis</h3></div>', unsafe_allow_html=True)
            
            for name in agent_names:
                phrases = agent_building.get(name, [])
                if phrases:
                    st.markdown(f"**{name}:** {len(phrases)} building phrase(s) — {', '.join(phrases[:3])}")
                elif agent_names.index(name) == 0:
                    st.markdown(f"**{name}:** (Position #1 — measured by Breakthrough Score)")
                else:
                    st.markdown(f"**{name}:** No explicit building phrases detected")
            
            # Interpretation
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
            
            # Export
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

### Synthetic Baseline
{synthetic_baseline_text[:300] if synthetic_baseline_text else 'Not generated'}...

### Per-Agent Contribution
{per_agent_export}

### Semantic Metrics
- Semantic Distance from Centroid: {semantic_distance*100:.1f}%
- Predictive Failure Rate (PFR): {pfr*100:.1f}%
- Envelope Position: {envelope_position}
- Agent Semantic Diversity: {semantic_diversity*100:.1f}%

### Lexical Metrics
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
*SYN-IQ Analyzer v4 — SYNINT Team — January 2026*
"""
            
            st.download_button(
                "📥 Download Results (Markdown)",
                export_data,
                file_name=f"syniq_v4_results_{experiment_name.replace(' ', '_') if experiment_name else 'experiment'}.md",
                mime="text/markdown"
            )

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666;">
    <em>SYN-IQ Analyzer v4</em><br>
    <em>Emergence Measurement with Synthetic Baseline</em><br>
    <em>SYNINT Team — January 2026</em>
</div>
""", unsafe_allow_html=True)
