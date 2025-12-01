"""
Cross-Signal Correlation Panel (CHUNK 6.28 UI)
UI component for displaying cross-signal correlations and class effects.
"""
import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

try:
    from src.ai.cross_signal_correlation import CrossSignalCorrelationEngine, analyze_cross_signal_correlation
    CORRELATION_ENGINE_AVAILABLE = True
except ImportError:
    CORRELATION_ENGINE_AVAILABLE = False


def render_cross_signal_correlation_panel(df: pd.DataFrame) -> None:
    """
    Render cross-signal correlation analysis panel.
    
    Args:
        df: Safety data DataFrame
    """
    if not CORRELATION_ENGINE_AVAILABLE:
        st.error("Cross-signal correlation engine not available.")
        return
    
    if df is None or df.empty:
        st.info("Upload data to perform cross-signal correlation analysis.")
        return
    
    st.header("🔗 Cross-Signal Correlation Analysis")
    st.markdown(
        "Identifies relationships across multiple signals, including class effects, "
        "cross-drug correlations, and shared reaction patterns."
    )
    
    # Analyze correlations
    with st.spinner("Analyzing cross-signal correlations..."):
        try:
            results = analyze_cross_signal_correlation(df)
        except Exception as e:
            st.error(f"Error analyzing correlations: {e}")
            return
    
    if not results:
        st.warning("No correlation results available.")
        return
    
    # Display correlation matrix
    correlation_matrix = results.get("correlation_matrix")
    if correlation_matrix is not None and not correlation_matrix.empty:
        st.subheader("📊 Drug-Drug Correlation Matrix")
        st.caption("Shows how similar drugs are based on their reaction profiles (cosine similarity).")
        
        # Create heatmap
        fig = px.imshow(
            correlation_matrix,
            text_auto=True,
            aspect="auto",
            color_continuous_scale="Blues",
            title="Cross-Signal Correlation Heatmap"
        )
        fig.update_layout(height=600)
        st.plotly_chart(fig, use_container_width=True)
        
        # Display matrix as table
        with st.expander("📋 View Correlation Matrix Table"):
            st.dataframe(correlation_matrix, use_container_width=True)
    
    # Display class effects
    class_effects = results.get("class_effects", [])
    if class_effects:
        st.subheader("🧬 Class Effects Detected")
        st.caption("Drugs showing similar reaction patterns (potential class effects).")
        
        for effect in class_effects[:10]:  # Top 10
            with st.expander(f"Class Effect: {effect.get('description', 'Unknown')}"):
                st.write(f"**Correlation Strength:** {effect.get('correlation_strength', 0):.2f}")
                st.write(f"**Type:** {effect.get('cluster_type', 'Unknown')}")
                signals = effect.get('signals', [])
                if signals:
                    st.write("**Signals:**")
                    for signal in signals[:5]:  # Show first 5
                        st.write(f"- {signal}")
    
    # Display reaction clusters
    reaction_clusters = results.get("reaction_clusters", [])
    if reaction_clusters:
        st.subheader("⚛️ Reaction Clusters")
        st.caption("Groups of reactions that frequently co-occur across multiple drugs.")
        
        for cluster in reaction_clusters[:10]:  # Top 10
            with st.expander(f"Reaction Cluster #{cluster.get('cluster_id', 'Unknown')}"):
                st.write(f"**Strength:** {cluster.get('correlation_strength', 0):.2f}")
                signals = cluster.get('signals', [])
                if signals:
                    st.write("**Signals:**")
                    for signal in signals[:5]:
                        st.write(f"- {signal}")
    
    # Display summary statistics
    st.subheader("📈 Summary Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_signals = results.get("total_signals", 0)
    strong_correlations = results.get("strong_correlations_count", 0)
    class_effects_count = len(class_effects) if class_effects else 0
    reaction_clusters_count = len(reaction_clusters) if reaction_clusters else 0
    
    col1.metric("Total Signals", f"{total_signals:,}")
    col2.metric("Strong Correlations", f"{strong_correlations:,}")
    col3.metric("Class Effects", class_effects_count)
    col4.metric("Reaction Clusters", reaction_clusters_count)
    
    # Export options
    with st.expander("💾 Export Results"):
        if st.button("📥 Download Correlation Matrix (CSV)"):
            if correlation_matrix is not None and not correlation_matrix.empty:
                csv = correlation_matrix.to_csv()
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name="cross_signal_correlations.csv",
                    mime="text/csv"
                )

