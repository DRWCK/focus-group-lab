"""
SYN-IQ Mapper Analyzer V1 — Streamlit App
Topological Data Analysis for AI Response Profiles

PURPOSE: Apply the Mapper algorithm to SYN-IQ data
         to reveal topological structure in AI response space

SYNINT Team — February 2026
Tennessee 🎹 CUZ Partnership
"""

import streamlit as st
import pandas as pd
import numpy as np
import json
import tempfile
import os

# =============================================================================
# PAGE CONFIG
# =============================================================================
st.set_page_config(
    page_title="SYN-IQ Mapper Analyzer",
    page_icon="🗺️",
    layout="wide"
)

# =============================================================================
# PASSWORD PROTECTION
# =============================================================================
def check_password():
    """Simple password gate for the app."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

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
        # Check against secrets or hardcoded fallback
        correct = st.secrets.get("app_password", "SYNIQ2026") if hasattr(st, 'secrets') else "SYNIQ2026"
        try:
            correct = st.secrets["app_password"]
        except (FileNotFoundError, KeyError):
            correct = "SYNIQ2026"

        if password == correct:
            st.session_state.authenticated = True
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
</style>
""", unsafe_allow_html=True)

# =============================================================================
# HEADER
# =============================================================================
st.markdown("""
<div class="main-header">
    <h1>🗺️ SYN-IQ Mapper Analyzer</h1>
    <p class="subtitle">Topological Data Analysis for AI Response Profiles</p>
    <p class="subtitle">KeplerMapper + IEP Framework</p>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# CHECK DEPENDENCIES
# =============================================================================
@st.cache_resource
def check_and_import():
    """Check dependencies and import."""
    try:
        import kmapper as km
        from sklearn.cluster import DBSCAN
        from sklearn.preprocessing import StandardScaler
        from sklearn.decomposition import PCA
        return True, km, DBSCAN, StandardScaler, PCA
    except ImportError as e:
        return False, None, None, None, None

deps_ok, km, DBSCAN, StandardScaler, PCA = check_and_import()

if not deps_ok:
    st.error("❌ Missing dependencies! Make sure `kmapper` and `scikit-learn` are in requirements.txt")
    st.code("kmapper\nscikit-learn", language="text")
    st.stop()

st.success("✅ All dependencies loaded!")

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def parse_embeddings(df):
    """Parse embeddings from JSON strings."""
    embeddings = []
    valid_indices = []
    
    for idx, row in df.iterrows():
        try:
            emb_str = row.get('embedding', '[]')
            if pd.isna(emb_str) or emb_str == '[]' or emb_str == '':
                continue
            
            emb = json.loads(emb_str) if isinstance(emb_str, str) else emb_str
            
            if isinstance(emb, list) and len(emb) > 0:
                embeddings.append(emb)
                valid_indices.append(idx)
        except (json.JSONDecodeError, TypeError):
            continue
    
    if not embeddings:
        return np.array([]), []
    
    return np.array(embeddings), valid_indices


def build_iep_features(df):
    """Build feature matrix from IEP dimensions (12-15 transparent features)."""
    has_italic_cols = 'has_italics' in df.columns
    features = []
    valid_indices = []
    
    for idx, row in df.iterrows():
        try:
            feature_vec = [
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
            # Add italic features if available
            if has_italic_cols:
                feature_vec.extend([
                    float(row.get('has_italics', 0) or 0),
                    float(row.get('italic_count', 0) or 0),
                    float(row.get('italic_density', 0) or 0),
                ])
            features.append(feature_vec)
            valid_indices.append(idx)
        except (ValueError, TypeError):
            continue
    
    return np.array(features), valid_indices


def run_mapper_analysis(data, df, valid_indices, n_cubes, overlap, eps, min_samples, projection_type):
    """Run KeplerMapper and return results."""
    
    # Initialize Mapper
    mapper = km.KeplerMapper(verbose=0)
    
    # Projection
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
    
    # Create cover
    cover = km.Cover(n_cubes=n_cubes, perc_overlap=overlap)
    
    # Build graph
    graph = mapper.map(
        projected,
        data,
        cover=cover,
        clusterer=DBSCAN(eps=eps, min_samples=min_samples)
    )
    
    return mapper, graph


def analyze_graph(graph, df, valid_indices):
    """Analyze the mapper graph."""
    subset = df.iloc[valid_indices].reset_index(drop=True)
    
    analysis = {
        "n_nodes": len(graph['nodes']),
        "n_edges": len(graph['links']),
        "nodes": {}
    }
    
    cold_nodes = set()
    hot_nodes = set()
    
    for node_id, indices in graph['nodes'].items():
        node_data = subset.iloc[indices]
        
        temps = node_data['temperature'].value_counts().to_dict() if 'temperature' in node_data.columns else {}
        agents = node_data['agent'].value_counts().to_dict() if 'agent' in node_data.columns else {}
        
        avg_int = node_data['int_pct'].mean() if 'int_pct' in node_data.columns else 0
        avg_aff = node_data['aff_pct'].mean() if 'aff_pct' in node_data.columns else 0
        avg_act = node_data['act_pct'].mean() if 'act_pct' in node_data.columns else 0
        
        analysis["nodes"][node_id] = {
            "size": len(indices),
            "temps": temps,
            "agents": agents,
            "avg_int": avg_int,
            "avg_aff": avg_aff,
            "avg_act": avg_act,
        }
        
        if 'COLD' in temps:
            cold_nodes.add(node_id)
        if 'HOT' in temps or 'FIRE' in temps:
            hot_nodes.add(node_id)
    
    # Temperature separation
    analysis["cold_nodes"] = cold_nodes
    analysis["hot_nodes"] = hot_nodes
    analysis["overlap_nodes"] = cold_nodes & hot_nodes
    analysis["cold_only"] = cold_nodes - hot_nodes
    analysis["hot_only"] = hot_nodes - cold_nodes
    
    return analysis


# =============================================================================
# SIDEBAR — CONFIGURATION
# =============================================================================
st.sidebar.markdown("## ⚙️ Configuration")

# File upload
uploaded_file = st.sidebar.file_uploader("📁 Upload Data (CSV or JSON)", type=['csv', 'json'])

st.sidebar.markdown("---")
st.sidebar.markdown("### Data Source")

# Determine available options
feature_options = ["IEP Features (12D transparent)"]
if 'embedding' in (df.columns if uploaded_file else []):
    feature_options.append("Embeddings (pre-computed)")
if 'response_text' in (df.columns if uploaded_file else []):
    feature_options.append("SBERT Embeddings (from text)")

use_iep = st.sidebar.radio(
    "Feature Type:",
    feature_options,
    index=0
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Mapper Parameters")

n_cubes = st.sidebar.slider("N Cubes (cover resolution)", 5, 30, 10)
overlap = st.sidebar.slider("Overlap %", 0.1, 0.9, 0.5)
eps = st.sidebar.slider("DBSCAN eps", 0.1, 5.0, 2.0, step=0.1,
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

# =============================================================================
# MAIN AREA
# =============================================================================

if uploaded_file is not None:
    # Load data — CSV or JSON
    if uploaded_file.name.endswith('.json'):
        raw_data = json.loads(uploaded_file.read().decode('utf-8'))
        df = pd.DataFrame(raw_data)
        # Rename JSON fields to match expected columns
        rename_map = {}
        if 'full_int_pct' in df.columns and 'int_pct' not in df.columns:
            rename_map['full_int_pct'] = 'int_pct'
            rename_map['full_aff_pct'] = 'aff_pct'
            rename_map['full_act_pct'] = 'act_pct'
            rename_map['full_vader_compound'] = 'vader_compound'
            rename_map['full_total_words'] = 'total_words'
        if 'condition' in df.columns and 'temperature' not in df.columns:
            rename_map['condition'] = 'temperature'
        if rename_map:
            df = df.rename(columns=rename_map)
        # Convert has_italics to int
        if 'has_italics' in df.columns:
            df['has_italics'] = df['has_italics'].astype(int)
        # Extract response text for embeddings
        if 'q2_response' in df.columns:
            df['response_text'] = df['q2_response']
            st.sidebar.success(f"✅ JSON loaded with response text for embeddings")
        st.sidebar.info(f"Loaded {len(df)} records from JSON")
    else:
        df = pd.read_csv(uploaded_file)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown('<div class="stats-box"><h3>' + str(len(df)) + '</h3><p>Records</p></div>', unsafe_allow_html=True)
    with col2:
        n_agents = df['agent'].nunique() if 'agent' in df.columns else 0
        st.markdown(f'<div class="stats-box"><h3>{n_agents}</h3><p>Agents</p></div>', unsafe_allow_html=True)
    with col3:
        n_temps = df['temperature'].nunique() if 'temperature' in df.columns else 0
        st.markdown(f'<div class="stats-box"><h3>{n_temps}</h3><p>Temperatures</p></div>', unsafe_allow_html=True)
    with col4:
        feature_dim = "12D" if "IEP" in use_iep else "384D"
        st.markdown(f'<div class="stats-box"><h3>{feature_dim}</h3><p>Features</p></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Preview data
    with st.expander("📋 Preview Data"):
        preview_cols = ['agent', 'temperature', 'int_pct', 'aff_pct', 'act_pct', 'vader_compound']
        preview_cols = [c for c in preview_cols if c in df.columns]
        st.dataframe(df[preview_cols].head(20))
    
    # Run Mapper button
    if st.button("🚀 Run Mapper Analysis", type="primary"):
        
        with st.spinner("Preparing data..."):
            # Get features
            if "IEP" in use_iep:
                data, valid_indices = build_iep_features(df)
                if len(data) > 0:
                    scaler = StandardScaler()
                    data = scaler.fit_transform(data)
            elif "SBERT" in use_iep:
                try:
                    from sentence_transformers import SentenceTransformer
                    model = SentenceTransformer('all-MiniLM-L6-v2')
                    texts = df['response_text'].fillna('').tolist()
                    valid_indices = [i for i, t in enumerate(texts) if len(t.strip()) > 0]
                    valid_texts = [texts[i] for i in valid_indices]
                    data = model.encode(valid_texts)
                    st.success(f"✅ Generated SBERT embeddings: {data.shape}")
                except ImportError:
                    st.error("❌ sentence-transformers not installed. Add it to requirements.txt")
                    st.stop()
            else:
                data, valid_indices = parse_embeddings(df)
            
            if len(data) == 0:
                st.error("❌ No valid data found! Check your CSV format.")
                st.stop()
            
            st.success(f"✅ Loaded {len(data)} data points with {data.shape[1]} dimensions")
        
        with st.spinner("Running Mapper algorithm..."):
            mapper, graph = run_mapper_analysis(
                data, df, valid_indices,
                n_cubes, overlap, eps, min_samples, projection_type
            )
        
        # Check for empty graph
        if len(graph['nodes']) == 0:
            st.error("❌ **Mapper produced 0 nodes!** DBSCAN couldn't form clusters with these parameters.")
            st.markdown("""
            **Try adjusting:**
            - **Increase DBSCAN eps** (most common fix) — try 2.0–3.5 for 12D IEP features
            - **Decrease min_samples** to 2
            - **Decrease N Cubes** to put more points per bin
            - **Increase Overlap %** to 0.5–0.7
            
            *Tip: Larger datasets with more dimensions need higher eps values.*
            """)
            st.stop()
        
        with st.spinner("Analyzing graph..."):
            analysis = analyze_graph(graph, df, valid_indices)
        
        # Results
        st.markdown("## 📊 Results")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Nodes", analysis["n_nodes"])
        with col2:
            st.metric("Edges", analysis["n_edges"])
        
        # Temperature separation
        st.markdown("### 🌡️ Temperature Separation")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("COLD-only nodes", len(analysis["cold_only"]))
        with col2:
            st.metric("HOT-only nodes", len(analysis["hot_only"]))
        with col3:
            st.metric("Mixed nodes", len(analysis["overlap_nodes"]))
        
        if analysis["cold_only"] and analysis["hot_only"]:
            st.success("✅ **COLD and HOT show TOPOLOGICAL SEPARATION!** Different temperatures occupy different regions of the response space.")
        elif analysis["overlap_nodes"] and not (analysis["cold_only"] or analysis["hot_only"]):
            st.warning("⚠️ **COLD and HOT are MIXED** — no clear separation in topology.")
        else:
            st.info("🔶 **Partial separation** — some overlap but distinct regions exist.")
        
        # Node details
        st.markdown("### 🔬 Node Analysis")
        
        for node_id, node_info in analysis["nodes"].items():
            with st.expander(f"Node {node_id} ({node_info['size']} points)"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Temperatures:**", node_info["temps"])
                    st.write("**Agents:**", node_info["agents"])
                with col2:
                    st.write(f"**Avg INT%:** {node_info['avg_int']:.1f}")
                    st.write(f"**Avg AFF%:** {node_info['avg_aff']:.1f}")
                    st.write(f"**Avg ACT%:** {node_info['avg_act']:.1f}")
        
        # Generate visualization
        st.markdown("### 🖼️ Visualization")
        
        with st.spinner("Generating interactive visualization..."):
            subset = df.iloc[valid_indices].reset_index(drop=True)
            
            # Color values
            if color_by in subset.columns:
                if subset[color_by].dtype == 'object':
                    # Categorical
                    categories = subset[color_by].unique().tolist()
                    color_values = subset[color_by].map({c: i for i, c in enumerate(categories)}).values
                else:
                    color_values = subset[color_by].values
            else:
                color_values = subset['aff_pct'].values if 'aff_pct' in subset.columns else np.zeros(len(subset))
            
            # Tooltips
            if 'temperature' in subset.columns and 'agent' in subset.columns:
                tooltips = np.array([f"{row['agent']} | {row['temperature']}" for _, row in subset.iterrows()])
            else:
                tooltips = subset.index.astype(str).values
            
            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as tmp:
                mapper.visualize(
                    graph,
                    path_html=tmp.name,
                    title="SYN-IQ Mapper Analysis",
                    color_values=color_values,
                    color_function_name=color_by,
                    custom_tooltips=tooltips
                )
                
                # Read and display
                with open(tmp.name, 'r') as f:
                    html_content = f.read()
                
                # Download button
                st.download_button(
                    "📥 Download Mapper HTML",
                    html_content,
                    file_name="syniq_mapper_output.html",
                    mime="text/html"
                )
                
                # Display inline (iframe)
                st.components.v1.html(html_content, height=700, scrolling=True)
                
                # Cleanup
                os.unlink(tmp.name)

else:
    st.info("👆 Upload a SYN-IQ CSV file to begin analysis.")
    
    st.markdown("### Expected Data Format")
    st.markdown("""
    **CSV** should include: `agent`, `temperature`, `int_pct`, `aff_pct`, `act_pct`, `vader_compound`
    
    **JSON** (from Italics Experiment): Auto-extracts response text for SBERT embeddings.
    Also reads `has_italics`, `italic_count`, `italic_density` for feature analysis.
    
    **Optional columns:** `has_italics`, `italic_count`, `italic_density`, `embedding`
    
    **Tip:** Use IEP Features for transparent analysis. Upload JSON for SBERT embeddings from response text!
    """)

# =============================================================================
# FOOTER
# =============================================================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #a0a0a0; padding: 1rem;">
    <strong>SYN-IQ Mapper Analyzer V1</strong><br>
    KeplerMapper + IEP Framework<br>
    <em>SYNINT Team — Tennessee 🎹 CUZ Partnership — February 2026</em>
</div>
""", unsafe_allow_html=True)
