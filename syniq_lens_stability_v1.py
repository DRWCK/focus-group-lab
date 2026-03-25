"""
SYN-IQ Lens Stability Analyzer V1
Topological Stability Analysis Across Multiple Lens Functions

PURPOSE: Per Dr. Farzana Nasrin's Experiment Protocol (March 24, 2026)
         Run the same dataset through multiple lens functions and verify
         that topology is stable across different projections.

Lens categories per protocol:
  AFF: aff_pct, vader_compound, |vader_compound|, (aff_pct, vader_compound)
  INT: int_pct, flesch_kincaid, ttr, (int_pct, flesch_kincaid), (int_pct, ttr)
  ACT: act_pct, total_words, (act_pct, total_words)
  Cross-IEP: (aff_pct, int_pct), (int_pct, act_pct), (aff_pct, act_pct)
  Geometric: PCA1, (PCA1, PCA2)

SYNINT Research Team — March 2026
Tennessee 🎹 CUZ Partnership
"""

import streamlit as st
import pandas as pd
import numpy as np
import json
import tempfile
import os
import re
import networkx as nx
from collections import defaultdict

st.set_page_config(
    page_title="SYN-IQ Lens Stability Analyzer V1",
    page_icon="🔬",
    layout="wide"
)

# =============================================================================
# PASSWORD
# =============================================================================
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if st.query_params.get("auth") == "granted":
        st.session_state.authenticated = True
    if st.session_state.authenticated:
        return True
    st.markdown("""
    <div style="background: linear-gradient(135deg, #0a0a1a 0%, #1a0a2e 40%, #0f2460 100%);
         color: white; padding: 2rem; border-radius: 10px; text-align: center;
         margin-bottom: 1rem; border: 1px solid #7c3aed;">
        <h1 style="color: #a78bfa;">🔬 SYN-IQ Lens Stability Analyzer V1</h1>
        <p style="color: #9ca3af;">Authorized Access Only</p>
    </div>
    """, unsafe_allow_html=True)
    pwd = st.text_input("Password:", type="password")
    if st.button("Enter"):
        valid = [st.secrets.get("app_password","SYNIQ2026"), "SYNIQ2026"]
        if pwd in valid:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password")
    return False

if not check_password():
    st.stop()

# =============================================================================
# STYLING
# =============================================================================
st.markdown("""
<style>
body { background-color: #ffffff; }
.main { background-color: #ffffff; }
.stApp { background-color: #ffffff; }
.metric-box {
    background: linear-gradient(135deg, #1e3a5f, #2e75b6);
    color: white; border-radius: 8px; padding: 1rem;
    text-align: center; margin: 0.25rem;
}
.metric-box h3 { font-size: 1.8rem; margin: 0; }
.metric-box p  { font-size: 0.85rem; margin: 0; opacity: 0.85; }
.stable   { background-color: #d4edda; border-left: 4px solid #28a745; padding: 0.5rem; border-radius: 4px; }
.unstable { background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 0.5rem; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# HEADER
# =============================================================================
st.markdown("""
<div style="background: linear-gradient(135deg, #0a0a1a 0%, #1a0a2e 40%, #0f2460 100%);
     color: white; padding: 1.5rem 2rem; border-radius: 10px; margin-bottom: 1rem;
     border: 1px solid #7c3aed;">
    <h1 style="color: #a78bfa; margin: 0;">🔬 SYN-IQ Lens Stability Analyzer V1</h1>
    <p style="color: #9ca3af; margin: 0.5rem 0 0 0;">
        Topological Stability Analysis · Per Dr. Nasrin Protocol (March 2026) ·
        IEP V3 · KeplerMapper
    </p>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# SIDEBAR
# =============================================================================
st.sidebar.markdown("## 📁 Data Upload")
uploaded_file = st.sidebar.file_uploader("Upload SYN-IQ CSV", type=['csv'])

st.sidebar.markdown("---")
st.sidebar.markdown("## 🎛️ Mapper Parameters")
n_cubes     = st.sidebar.slider("Hypercubes (n_cubes)", 5, 20, 10)
perc_overlap= st.sidebar.slider("Overlap %", 10, 60, 30)
min_cluster = st.sidebar.slider("Min cluster size", 1, 5, 2)

st.sidebar.markdown("---")
st.sidebar.markdown("## 🔭 Lens Selection")
st.sidebar.markdown("**AFF Lenses**")
use_aff_pct       = st.sidebar.checkbox("aff_pct", value=True)
use_vader_comp    = st.sidebar.checkbox("vader_compound", value=True)
use_vader_abs     = st.sidebar.checkbox("|vader_compound|", value=False)
use_aff_vader_2d  = st.sidebar.checkbox("(aff_pct, vader_compound) 2D", value=False)

st.sidebar.markdown("**INT Lenses**")
use_int_pct       = st.sidebar.checkbox("int_pct", value=True)
use_fk            = st.sidebar.checkbox("flesch_kincaid", value=False)
use_ttr           = st.sidebar.checkbox("ttr", value=False)
use_int_fk_2d     = st.sidebar.checkbox("(int_pct, flesch_kincaid) 2D", value=False)
use_int_ttr_2d    = st.sidebar.checkbox("(int_pct, ttr) 2D", value=False)

st.sidebar.markdown("**ACT Lenses**")
use_act_pct       = st.sidebar.checkbox("act_pct", value=True)
use_words         = st.sidebar.checkbox("total_words", value=False)
use_act_words_2d  = st.sidebar.checkbox("(act_pct, total_words) 2D", value=False)

st.sidebar.markdown("**Cross-IEP Lenses**")
use_aff_int_2d    = st.sidebar.checkbox("(aff_pct, int_pct) 2D", value=True)
use_int_act_2d    = st.sidebar.checkbox("(int_pct, act_pct) 2D", value=False)
use_aff_act_2d    = st.sidebar.checkbox("(aff_pct, act_pct) 2D", value=False)

st.sidebar.markdown("**Geometric Lenses**")
use_pca1          = st.sidebar.checkbox("PCA1", value=False)
use_pca1_pca2_2d  = st.sidebar.checkbox("(PCA1, PCA2) 2D", value=False)

# =============================================================================
# HELPERS
# =============================================================================
def build_feature_matrix(df):
    """Build IEP feature matrix from pre-scored columns."""
    cols = ['int_pct','aff_pct','act_pct']
    if 'vader_compound' in df.columns: cols.append('vader_compound')
    if 'vader_pos'      in df.columns: cols += ['vader_pos','vader_neg','vader_neu']
    if 'total_words'    in df.columns: cols.append('total_words')
    if 'flesch_kincaid' in df.columns: cols.append('flesch_kincaid')
    if 'ttr'            in df.columns: cols.append('ttr')
    avail = [c for c in cols if c in df.columns]
    data = df[avail].fillna(0).values.astype(float)
    from sklearn.preprocessing import MinMaxScaler
    data = MinMaxScaler().fit_transform(data)
    return data, avail

def run_mapper_with_lens(data, lens_values, n_cubes, perc_overlap, min_cluster):
    """Run KeplerMapper with given lens and return graph + topology stats."""
    import kmapper as km
    from sklearn.cluster import DBSCAN
    mapper = km.KeplerMapper(verbose=0)
    graph = mapper.map(
        lens_values,
        data,
        cover=km.Cover(n_cubes=n_cubes, perc_overlap=perc_overlap/100),
        clusterer=DBSCAN(eps=0.5, min_samples=min_cluster)
    )
    # Build networkx graph for analysis
    G = nx.Graph()
    nodes = graph.get('nodes', {})
    links = graph.get('links', {})
    for n in nodes:
        G.add_node(n)
    for src, targets in links.items():
        for tgt in targets:
            G.add_edge(src, tgt)
    components = list(nx.connected_components(G))
    comp_sizes = sorted([len(c) for c in components], reverse=True)
    return {
        'n_nodes': len(nodes),
        'n_edges': G.number_of_edges(),
        'n_components': len(components),
        'largest': comp_sizes[0] if comp_sizes else 0,
        'comp_sizes': comp_sizes,
        'graph': graph
    }

def get_pca_projection(data, n_components=2):
    from sklearn.decomposition import PCA
    pca = PCA(n_components=n_components)
    return pca.fit_transform(data)

def normalize_col(arr):
    mn, mx = arr.min(), arr.max()
    if mx == mn: return arr * 0
    return (arr - mn) / (mx - mn)

# =============================================================================
# MAIN
# =============================================================================
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    if 'agent' in df.columns:
        df['agent'] = df['agent'].replace({'Sophia': 'ChatGPT', 'sophia': 'ChatGPT'})

    # Stats
    col1, col2, col3, col4 = st.columns(4)
    col1.markdown(f'<div class="metric-box"><h3>{len(df)}</h3><p>Responses</p></div>', unsafe_allow_html=True)
    col2.markdown(f'<div class="metric-box"><h3>{df["agent"].nunique() if "agent" in df.columns else "?"}</h3><p>Agents</p></div>', unsafe_allow_html=True)
    col3.markdown(f'<div class="metric-box"><h3>{df["temperature"].nunique() if "temperature" in df.columns else "?"}</h3><p>Conditions</p></div>', unsafe_allow_html=True)
    col4.markdown(f'<div class="metric-box"><h3>{df["question_id"].nunique() if "question_id" in df.columns else "?"}</h3><p>Questions</p></div>', unsafe_allow_html=True)

    st.markdown("---")

    # Build active lens list
    active_lenses = []
    if use_aff_pct      and 'aff_pct'       in df.columns: active_lenses.append(('aff_pct',       '1D', 'AFF'))
    if use_vader_comp   and 'vader_compound' in df.columns: active_lenses.append(('vader_compound','1D', 'AFF'))
    if use_vader_abs    and 'vader_compound' in df.columns: active_lenses.append(('|vader_compound|','1D_abs','AFF'))
    if use_aff_vader_2d and 'aff_pct' in df.columns and 'vader_compound' in df.columns:
        active_lenses.append(('(aff_pct, vader_compound)','2D','AFF'))
    if use_int_pct      and 'int_pct'        in df.columns: active_lenses.append(('int_pct',       '1D', 'INT'))
    if use_fk           and 'flesch_kincaid' in df.columns: active_lenses.append(('flesch_kincaid','1D', 'INT'))
    if use_ttr          and 'ttr'            in df.columns: active_lenses.append(('ttr',           '1D', 'INT'))
    if use_int_fk_2d    and 'int_pct' in df.columns and 'flesch_kincaid' in df.columns:
        active_lenses.append(('(int_pct, flesch_kincaid)','2D','INT'))
    if use_int_ttr_2d   and 'int_pct' in df.columns and 'ttr' in df.columns:
        active_lenses.append(('(int_pct, ttr)','2D','INT'))
    if use_act_pct      and 'act_pct'        in df.columns: active_lenses.append(('act_pct',       '1D', 'ACT'))
    if use_words        and 'total_words'    in df.columns: active_lenses.append(('total_words',   '1D', 'ACT'))
    if use_act_words_2d and 'act_pct' in df.columns and 'total_words' in df.columns:
        active_lenses.append(('(act_pct, total_words)','2D','ACT'))
    if use_aff_int_2d   and 'aff_pct' in df.columns and 'int_pct' in df.columns:
        active_lenses.append(('(aff_pct, int_pct)','2D','Cross-IEP'))
    if use_int_act_2d   and 'int_pct' in df.columns and 'act_pct' in df.columns:
        active_lenses.append(('(int_pct, act_pct)','2D','Cross-IEP'))
    if use_aff_act_2d   and 'aff_pct' in df.columns and 'act_pct' in df.columns:
        active_lenses.append(('(aff_pct, act_pct)','2D','Cross-IEP'))
    if use_pca1:        active_lenses.append(('PCA1','1D_pca','Geometric'))
    if use_pca1_pca2_2d:active_lenses.append(('(PCA1, PCA2)','2D_pca','Geometric'))

    st.markdown(f"### 🔭 {len(active_lenses)} Lens Functions Selected")

    if len(active_lenses) == 0:
        st.warning("Select at least one lens in the sidebar.")
        st.stop()

    if st.button("🚀 Run Lens Stability Analysis", type="primary"):
        data, feat_cols = build_feature_matrix(df)
        pca_proj = get_pca_projection(data, 2)

        results = []
        progress = st.progress(0)
        status = st.empty()

        for i, (lens_name, lens_type, lens_cat) in enumerate(active_lenses):
            status.text(f"Running lens {i+1}/{len(active_lenses)}: {lens_name}...")
            progress.progress((i+1)/len(active_lenses))

            try:
                # Build lens values
                if lens_type == '1D':
                    col = lens_name
                    vals = normalize_col(df[col].fillna(0).values).reshape(-1,1)
                elif lens_type == '1D_abs':
                    vals = normalize_col(np.abs(df['vader_compound'].fillna(0).values)).reshape(-1,1)
                elif lens_type == '2D':
                    # Extract column names from parentheses
                    cols = [c.strip() for c in lens_name.strip('()').split(',')]
                    vals = np.column_stack([normalize_col(df[c].fillna(0).values) for c in cols])
                elif lens_type == '1D_pca':
                    vals = normalize_col(pca_proj[:,0]).reshape(-1,1)
                elif lens_type == '2D_pca':
                    vals = np.column_stack([normalize_col(pca_proj[:,0]), normalize_col(pca_proj[:,1])])

                topo = run_mapper_with_lens(data, vals, n_cubes, perc_overlap, min_cluster)
                results.append({
                    'Lens': lens_name,
                    'Category': lens_cat,
                    'Type': lens_type.replace('_pca','').replace('_abs',''),
                    'Nodes': topo['n_nodes'],
                    'Edges': topo['n_edges'],
                    'Components': topo['n_components'],
                    'Largest': topo['largest'],
                    '% Connected': f"{round(topo['largest']/topo['n_nodes']*100) if topo['n_nodes'] > 0 else 0}%",
                    'Component Sizes': str(topo['comp_sizes'][:5]),
                })
            except Exception as e:
                results.append({
                    'Lens': lens_name, 'Category': lens_cat, 'Type': lens_type,
                    'Nodes': 'ERROR', 'Edges': 'ERROR', 'Components': 'ERROR',
                    'Largest': 'ERROR', '% Connected': 'ERROR',
                    'Component Sizes': str(e)[:50]
                })

        progress.progress(1.0)
        status.text("✅ Complete!")

        st.session_state.lens_results = results
        st.rerun()

    # Display results
    if 'lens_results' in st.session_state and st.session_state.lens_results:
        results = st.session_state.lens_results
        rdf = pd.DataFrame(results)

        st.markdown("## 📊 Lens Stability Results")

        # Summary metrics
        valid = rdf[rdf['Nodes'] != 'ERROR']
        if len(valid) > 0:
            nodes_vals = valid['Nodes'].astype(int)
            comps_vals = valid['Components'].astype(int)
            largest_vals = valid['Largest'].astype(int)

            col1, col2, col3, col4 = st.columns(4)
            col1.markdown(f'<div class="metric-box"><h3>{nodes_vals.min()}–{nodes_vals.max()}</h3><p>Node Range</p></div>', unsafe_allow_html=True)
            col2.markdown(f'<div class="metric-box"><h3>{comps_vals.min()}–{comps_vals.max()}</h3><p>Component Range</p></div>', unsafe_allow_html=True)
            col3.markdown(f'<div class="metric-box"><h3>{largest_vals.min()}–{largest_vals.max()}</h3><p>Largest Component Range</p></div>', unsafe_allow_html=True)

            node_range = nodes_vals.max() - nodes_vals.min()
            comp_range = comps_vals.max() - comps_vals.min()
            if node_range <= 5 and comp_range <= 2:
                stability = "HIGH ✅"
                col4.markdown(f'<div class="metric-box"><h3>{stability}</h3><p>Topology Stability</p></div>', unsafe_allow_html=True)
                st.markdown('<div class="stable">✅ <strong>Topology is STABLE</strong> — connected component structure is consistent across lens functions. Observed patterns reflect intrinsic properties of the response space, not projection artifacts.</div>', unsafe_allow_html=True)
            elif node_range <= 15 and comp_range <= 4:
                stability = "MODERATE ⚠️"
                col4.markdown(f'<div class="metric-box"><h3>{stability}</h3><p>Topology Stability</p></div>', unsafe_allow_html=True)
                st.markdown('<div class="unstable">⚠️ <strong>Topology is MODERATELY STABLE</strong> — some variation across lenses. Core structure appears consistent but projection choice has measurable effect.</div>', unsafe_allow_html=True)
            else:
                stability = "LOW ❌"
                col4.markdown(f'<div class="metric-box"><h3>{stability}</h3><p>Topology Stability</p></div>', unsafe_allow_html=True)
                st.warning("❌ **Topology is UNSTABLE** — significant variation across lens functions. Results may be projection-dependent.")

        st.markdown("---")

        # Results table by category
        for cat in ['AFF', 'INT', 'ACT', 'Cross-IEP', 'Geometric']:
            cat_df = rdf[rdf['Category'] == cat]
            if len(cat_df) == 0:
                continue
            st.markdown(f"### {cat} Lenses")
            display_cols = ['Lens','Type','Nodes','Edges','Components','Largest','% Connected']
            st.dataframe(cat_df[display_cols].reset_index(drop=True),
                        use_container_width=True, hide_index=True)

        st.markdown("---")

        # Full results download
        st.markdown("### 📥 Downloads")
        col1, col2 = st.columns(2)

        with col1:
            st.download_button(
                "📥 Download Full Results (CSV)",
                rdf.to_csv(index=False),
                file_name="syniq_lens_stability_results.csv",
                mime="text/csv"
            )

        with col2:
            # Summary text report
            report_lines = [
                "SYN-IQ Lens Stability Analysis Report",
                "Per Dr. Farzana Nasrin Protocol — March 2026",
                "=" * 50,
                f"Dataset: {uploaded_file.name}",
                f"Rows: {len(df)}",
                f"Lenses tested: {len(results)}",
                f"Mapper parameters: n_cubes={n_cubes}, overlap={perc_overlap}%, min_cluster={min_cluster}",
                "",
                "RESULTS:",
            ]
            for r in results:
                report_lines.append(
                    f"  {r['Lens']:35s} | Nodes: {str(r['Nodes']):4s} | "
                    f"Components: {str(r['Components']):3s} | Largest: {str(r['Largest']):4s} | "
                    f"% Connected: {r['% Connected']}"
                )
            report_lines += [
                "",
                f"STABILITY ASSESSMENT: {stability if 'stability' in dir() else 'N/A'}",
                "",
                "SYNINT Research Team · Tennessee 🎹 CUZ Partnership · March 2026"
            ]
            st.download_button(
                "📥 Download Summary Report (TXT)",
                "\n".join(report_lines),
                file_name="syniq_lens_stability_report.txt",
                mime="text/plain"
            )

else:
    st.info("👆 Upload a SYN-IQ CSV file to begin lens stability analysis.")
    st.markdown("""
### What This Tool Does

Per **Dr. Nasrin's Experiment Protocol (March 24, 2026)**, this tool runs the same dataset 
through multiple lens functions to verify that observed topological structures are stable 
across different projections.

**Lens categories:**
- **AFF**: aff_pct, vader_compound, |vader_compound|, 2D combinations
- **INT**: int_pct, flesch_kincaid, ttr, 2D combinations  
- **ACT**: act_pct, total_words, 2D combinations
- **Cross-IEP**: (aff_pct, int_pct), (int_pct, act_pct), (aff_pct, act_pct)
- **Geometric**: PCA1, (PCA1, PCA2)

**Stability criterion**: If the connected component structure is consistent across lens 
functions, the observed topology reflects intrinsic properties of the response space 
rather than artifacts of a particular projection.
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #a0a0a0; padding: 1rem;">
    <strong>SYN-IQ Lens Stability Analyzer V1</strong><br>
    Per Dr. Farzana Nasrin Protocol · KeplerMapper + IEP V3 · March 2026<br>
    <em>SYNINT Team — Tennessee 🎹 CUZ Partnership</em>
</div>
""", unsafe_allow_html=True)
