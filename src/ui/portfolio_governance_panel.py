"""
Portfolio Governance Panel (PART 9.2)
Portfolio-level governance dashboard with risk propagation visualization.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from typing import Dict, Any, Optional

try:
    from src.ai.portfolio_risk_propagation import compute_portfolio_risk_propagation
    PROPAGATION_AVAILABLE = True
except ImportError:
    PROPAGATION_AVAILABLE = False

try:
    from src.ai.medical_llm import call_medical_llm
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False


def render_portfolio_governance_panel(df: Optional[pd.DataFrame] = None) -> None:
    """
    Render Portfolio Governance & Risk Propagation Panel (PART 9.2).
    
    Features:
    - Portfolio Risk Priority Scores (RPF)
    - Cross-Signal Heatmap (Drug × Reaction)
    - Class-Effect Risk Propagation
    - Reaction Clusters (SOC-level grouping)
    - AI Governance Summary
    """
    st.header("🛡️ Portfolio Governance & Risk Propagation")
    st.caption("Enterprise portfolio-level risk analysis with cross-signal patterns, class effects, and governance insights.")
    
    if df is None or df.empty:
        # Try to get from session state
        df = st.session_state.get("normalized_data")
    
    if df is None or df.empty:
        st.info("⚠️ Upload safety data to view portfolio governance. Load data from the main upload section.")
        return
    
    if not PROPAGATION_AVAILABLE:
        st.error("Portfolio risk propagation engine not available. Please install required dependencies.")
        return
    
    # Compute portfolio risk propagation
    with st.spinner("🔄 Computing portfolio risk propagation..."):
        try:
            results = compute_portfolio_risk_propagation(df)
        except Exception as e:
            st.error(f"❌ Error computing portfolio risk propagation: {str(e)}")
            return
    
    # ---- PORTFOLIO RPF ----
    st.markdown("---")
    st.subheader("📊 Portfolio Risk Priority Scores (RPF)")
    
    portfolio_rpf = results.get("portfolio_rpf", [])
    if portfolio_rpf:
        rpf_df = pd.DataFrame(portfolio_rpf)
        rpf_df = rpf_df.sort_values("rpf_score", ascending=False)
        
        # Display metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Products", len(rpf_df))
        with col2:
            st.metric("Highest RPF Score", f"{rpf_df['rpf_score'].max():.1f}")
        with col3:
            st.metric("Average RPF Score", f"{rpf_df['rpf_score'].mean():.1f}")
        
        # Bar chart
        fig1 = px.bar(
            rpf_df.head(20),  # Top 20 products
            x="drug_name",
            y="rpf_score",
            title="Top 20 Products by Risk Priority Score",
            color="rpf_score",
            color_continuous_scale="Reds",
            labels={"drug_name": "Product", "rpf_score": "RPF Score"},
            template="plotly_white"
        )
        fig1.update_xaxes(tickangle=45)
        fig1.update_layout(height=400)
        st.plotly_chart(fig1, use_container_width=True)
        
        # Data table
        st.markdown("#### 📋 Product Risk Priority Table")
        display_df = rpf_df[["drug_name", "rpf_score", "case_count"]].copy()
        display_df.columns = ["Product", "RPF Score", "Case Count"]
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("No portfolio RPF data available.")
    
    # ---- CROSS-SIGNAL HEATMAP ----
    st.markdown("---")
    st.subheader("🔥 Cross-Signal Heatmap (Drug × Reaction)")
    
    cross_links = results.get("cross_signal_links", [])
    if cross_links and len(cross_links) > 0:
        cross_df = pd.DataFrame(cross_links)
        
        # Limit to top drugs and reactions for performance
        top_drugs = cross_df.groupby("drug_name")["count"].sum().nlargest(15).index.tolist()
        top_reactions = cross_df.groupby("reaction_pt")["count"].sum().nlargest(15).index.tolist()
        
        filtered_cross = cross_df[
            (cross_df["drug_name"].isin(top_drugs)) &
            (cross_df["reaction_pt"].isin(top_reactions))
        ]
        
        if not filtered_cross.empty:
            pivot = filtered_cross.pivot(
                index="drug_name",
                columns="reaction_pt",
                values="count"
            ).fillna(0)
            
            fig2 = px.imshow(
                pivot,
                color_continuous_scale="Reds",
                title="Cross-Signal Hotspots (Top 15 Products × Top 15 Reactions)",
                labels=dict(x="Reaction", y="Drug", color="Case Count"),
                aspect="auto",
                template="plotly_white"
            )
            fig2.update_layout(height=600)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Insufficient cross-signal data for heatmap visualization.")
    else:
        st.info("No cross-signal links available.")
    
    # ---- CLASS-EFFECT PROPAGATION ----
    st.markdown("---")
    st.subheader("🧬 Class-Effect Risk Propagation")
    
    class_effects = results.get("class_effects", [])
    if class_effects:
        class_df = pd.DataFrame(class_effects)
        class_df = class_df.sort_values("total_cases", ascending=False)
        
        st.markdown("Class-effect patterns detected across drug classes:")
        display_class_df = class_df[["drug_class", "top_reaction", "total_cases", "unique_reactions"]].copy()
        display_class_df.columns = ["Drug Class", "Top Reaction", "Total Cases", "Unique Reactions"]
        st.dataframe(display_class_df, use_container_width=True, hide_index=True)
        
        # Visualize class effects
        if len(class_df) > 0:
            fig3 = px.bar(
                class_df,
                x="drug_class",
                y="total_cases",
                title="Class-Effect Case Distribution",
                color="total_cases",
                color_continuous_scale="Oranges",
                labels={"drug_class": "Drug Class", "total_cases": "Total Cases"},
                template="plotly_white"
            )
            fig3.update_xaxes(tickangle=45)
            st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("No class-effect patterns detected.")
    
    # ---- REACTION CATEGORY CLUSTERS ----
    st.markdown("---")
    st.subheader("🩺 Reaction Clusters (SOC-level grouping)")
    
    reaction_clusters = results.get("reaction_clusters", [])
    if reaction_clusters:
        clusters_df = pd.DataFrame(reaction_clusters)
        clusters_df = clusters_df.sort_values("case_count", ascending=False)
        
        # Group by SOC if available
        if "soc" in clusters_df.columns:
            soc_summary = clusters_df.groupby("soc")["case_count"].sum().reset_index()
            soc_summary = soc_summary.sort_values("case_count", ascending=False)
            
            st.markdown("#### Reaction Distribution by System Organ Class")
            fig4 = px.pie(
                soc_summary.head(10),
                names="soc",
                values="case_count",
                title="Top 10 SOC Categories by Case Count",
                template="plotly_white"
            )
            st.plotly_chart(fig4, use_container_width=True)
            
            st.markdown("#### Detailed Reaction Clusters")
            st.dataframe(clusters_df.head(20), use_container_width=True, hide_index=True)
        else:
            st.dataframe(clusters_df.head(20), use_container_width=True, hide_index=True)
    else:
        st.info("No reaction cluster data available.")
    
    # ---- AI SUMMARY ----
    st.markdown("---")
    st.subheader("🧠 AI Governance Summary")
    
    if LLM_AVAILABLE:
        if st.button("🤖 Generate AI Portfolio Governance Summary", type="primary"):
            with st.spinner("Generating portfolio-level governance narrative..."):
                try:
                    summary_prompt = f"""
                    You are a senior pharmacovigilance portfolio analyst. Generate a concise, regulator-ready 
                    governance summary for portfolio risk based on the following data:
                    
                    Cross-Signal Links (top 10): {results.get("cross_signal_links", [])[:10]}
                    Drug Classes (top 10): {results.get("drug_classes", [])[:10]}
                    Reaction Clusters (top 10): {results.get("reaction_clusters", [])[:10]}
                    Portfolio RPF (top 10): {results.get("portfolio_rpf", [])[:10]}
                    Class Effects: {results.get("class_effects", [])}
                    
                    Provide:
                    1. Executive summary of portfolio risk profile
                    2. Key emerging concerns
                    3. Class-effect observations
                    4. Highest priority products requiring attention
                    5. Regulatory considerations
                    
                    Keep the summary professional, evidence-based, and suitable for regulatory review.
                    """
                    
                    summary = call_medical_llm(summary_prompt)
                    st.markdown(summary)
                except Exception as e:
                    st.error(f"Error generating AI summary: {str(e)}")
        else:
            st.info("Click the button above to generate an AI-powered portfolio governance summary.")
    else:
        st.info("AI summary generation not available. LLM module not configured.")
    
    # ---- EXPORT OPTIONS ----
    st.markdown("---")
    st.subheader("📤 Export Portfolio Governance Report")
    
    col1, col2 = st.columns(2)
    with col1:
        # Export as JSON
        if st.button("📥 Export as JSON", use_container_width=True):
            import json
            json_str = json.dumps(results, indent=2, default=str)
            st.download_button(
                label="Download JSON",
                data=json_str,
                file_name="portfolio_governance_report.json",
                mime="application/json"
            )
    
    with col2:
        # Export summary as CSV
        if portfolio_rpf:
            csv_data = pd.DataFrame(portfolio_rpf).to_csv(index=False)
            st.download_button(
                label="📥 Export RPF Scores (CSV)",
                data=csv_data,
                file_name="portfolio_rpf_scores.csv",
                mime="text/csv",
                use_container_width=True
            )

