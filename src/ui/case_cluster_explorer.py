"""
Case Cluster Explorer UI (CHUNK 6.24 Enhanced)
Enhanced UI for case clustering with drill-down capabilities.
"""
import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional
import plotly.express as px
import plotly.graph_objects as go

try:
    from src.local_ai.case_clustering import LocalCaseClustering
    CLUSTERING_AVAILABLE = True
except ImportError:
    CLUSTERING_AVAILABLE = False


def render_case_cluster_explorer(df: Optional[pd.DataFrame] = None, cluster_data: Optional[Dict[str, Any]] = None) -> None:
    """
    Render enhanced case cluster explorer with drill-down.
    
    Args:
        df: DataFrame with case records
        cluster_data: Optional pre-computed cluster data
    """
    if not CLUSTERING_AVAILABLE:
        st.error("Case clustering engine not available.")
        return
    
    st.header("⚛️ Case Cluster Explorer")
    st.markdown("Discover hidden patient subgroups and case patterns through unsupervised clustering.")
    
    if df is None or df.empty:
        st.info("Upload data to perform case clustering.")
        return
    
    # Clustering configuration
    with st.expander("⚙️ Clustering Configuration", expanded=False):
        n_clusters = st.slider(
            "Number of Clusters",
            min_value=3,
            max_value=15,
            value=6,
            help="Increase for more granular clusters, decrease for broader patterns"
        )
        
        cluster_button = st.button("🔬 Run Clustering Analysis", type="primary")
    
    # Perform clustering
    if cluster_button or cluster_data:
        with st.spinner("Clustering cases... This may take a moment."):
            if cluster_data is None:
                engine = LocalCaseClustering(n_clusters=n_clusters)
                try:
                    df_clustered, model, encoder = engine.fit(df)
                    cluster_summaries = engine.get_cluster_summary(df_clustered)
                    cluster_data = {
                        "df": df_clustered,
                        "clusters": cluster_summaries,
                        "model": model,
                        "encoder": encoder
                    }
                except Exception as e:
                    st.error(f"Clustering failed: {e}")
                    return
            else:
                df_clustered = cluster_data.get("df")
                cluster_summaries = cluster_data.get("clusters", [])
    else:
        st.info("Configure clustering settings and click 'Run Clustering Analysis' to begin.")
        return
    
    if df_clustered is None or cluster_summaries is None:
        st.warning("Clustering analysis failed.")
        return
    
    # Display cluster summaries
    st.subheader("📊 Cluster Profiles")
    st.caption(f"Found {len(cluster_summaries)} distinct patient subgroups.")
    
    # Cluster summary table
    if cluster_summaries:
        summary_df = pd.DataFrame(cluster_summaries)
        st.dataframe(summary_df, use_container_width=True)
        
        # Visualize cluster sizes
        fig = px.bar(
            summary_df,
            x='cluster_id',
            y='size',
            title="Cluster Sizes",
            labels={'cluster_id': 'Cluster ID', 'size': 'Number of Cases'},
            color='size',
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Cluster comparison chart
    st.subheader("📈 Cluster Characteristics Comparison")
    
    if cluster_summaries and len(cluster_summaries) > 0:
        # Create comparison visualization
        cluster_ids = [c.get('cluster_id') for c in cluster_summaries]
        sizes = [c.get('size', 0) for c in cluster_summaries]
        mean_ages = [c.get('mean_age') for c in cluster_summaries if c.get('mean_age')]
        serious_pcts = [c.get('serious_pct') for c in cluster_summaries if c.get('serious_pct')]
        
        # Multi-metric comparison
        fig = go.Figure()
        
        # Normalize metrics for comparison
        if mean_ages and serious_pcts:
            fig.add_trace(go.Bar(
                name='Normalized Mean Age',
                x=cluster_ids,
                y=[(age - min(mean_ages)) / (max(mean_ages) - min(mean_ages)) if max(mean_ages) > min(mean_ages) else 0.5 
                   for age in mean_ages],
                yaxis='y',
                offsetgroup=1
            ))
            
            fig.add_trace(go.Bar(
                name='Serious %',
                x=cluster_ids,
                y=[pct / 100 for pct in serious_pcts],
                yaxis='y',
                offsetgroup=2
            ))
        
        fig.update_layout(
            title="Cluster Characteristics Comparison",
            xaxis_title="Cluster ID",
            yaxis_title="Normalized Score",
            barmode='group',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Drill-down: Explore individual clusters
    st.subheader("🔍 Cluster Drill-Down")
    
    if cluster_summaries:
        selected_cluster = st.selectbox(
            "Select Cluster to Explore",
            options=[c.get('cluster_id') for c in cluster_summaries],
            format_func=lambda x: f"Cluster {x} ({next((c.get('size', 0) for c in cluster_summaries if c.get('cluster_id') == x), 0)} cases)"
        )
        
        if selected_cluster is not None and df_clustered is not None:
            # Filter to selected cluster
            if isinstance(df_clustered, pd.DataFrame) and 'CLUSTER' in df_clustered.columns:
                cluster_cases = df_clustered[df_clustered['CLUSTER'] == selected_cluster]
                
                st.write(f"**Cluster {selected_cluster} Details:**")
                st.write(f"Total cases: {len(cluster_cases):,}")
                
                # Show sample cases
                with st.expander(f"View Cases in Cluster {selected_cluster}"):
                    # Select columns to display
                    display_cols = ['drug_name', 'reaction', 'AGE', 'SEX', 'serious'] if all(col in cluster_cases.columns for col in ['drug_name', 'reaction', 'AGE', 'SEX', 'serious']) else cluster_cases.columns[:10]
                    st.dataframe(cluster_cases[display_cols].head(100), use_container_width=True)
                
                # Cluster characteristics
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Demographics:**")
                    if 'AGE' in cluster_cases.columns:
                        st.write(f"- Mean Age: {cluster_cases['AGE'].mean():.1f}")
                    if 'SEX' in cluster_cases.columns:
                        sex_dist = cluster_cases['SEX'].value_counts()
                        st.write(f"- Sex Distribution: {dict(sex_dist)}")
                
                with col2:
                    st.write("**Safety Profile:**")
                    if 'serious' in cluster_cases.columns:
                        serious_count = cluster_cases['serious'].sum() if cluster_cases['serious'].dtype == bool else len(cluster_cases[cluster_cases['serious'] == True])
                        st.write(f"- Serious Cases: {serious_count} ({serious_count/len(cluster_cases)*100:.1f}%)")
    
    # Export options
    with st.expander("💾 Export Clustering Results"):
        if st.button("📥 Download Cluster Assignments (CSV)"):
            if isinstance(df_clustered, pd.DataFrame):
                csv = df_clustered.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name="case_clusters.csv",
                    mime="text/csv"
                )

