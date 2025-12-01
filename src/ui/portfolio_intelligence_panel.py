"""
Portfolio Intelligence Panel UI (CHUNK A9.2 - Step 2)
Portfolio-level safety intelligence dashboard with cross-product trends and emerging risks.
"""
import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional

try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

try:
    from src.portfolio.portfolio_trends import PortfolioTrendEngine
    from src.ai.portfolio_model import PortfolioModel
    ENGINE_AVAILABLE = True
except ImportError:
    ENGINE_AVAILABLE = False

try:
    from src.ai.hybrid_summary_engine import HybridSummaryEngine
    from src.ai.medical_llm import call_medical_llm
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False


def render_portfolio_intelligence_panel(
    normalized_df: Optional[pd.DataFrame] = None,
    signals: Optional[List[Dict[str, Any]]] = None,
    trend_alerts: Optional[List[Dict[str, Any]]] = None,
    medical_llm = None
) -> None:
    """
    Render complete Portfolio Intelligence Panel (CHUNK A9.2 - Step 2).
    
    Args:
        normalized_df: Normalized DataFrame with case data
        signals: List of signal dictionaries
        trend_alerts: Trend alerts data
        medical_llm: LLM instance for AI interpretations
    """
    st.header("📊 Portfolio Intelligence Dashboard")
    st.caption("Cross-product safety intelligence, emerging risks, and portfolio-wide trend analysis")
    
    if not ENGINE_AVAILABLE:
        st.error("Portfolio intelligence engines not available. Please install required dependencies.")
        return
    
    if normalized_df is None or normalized_df.empty:
        st.warning("⚠️ No data available for portfolio analysis. Please load your dataset first.")
        return
    
    # Get normalized_df from session state if not provided
    if normalized_df is None:
        normalized_df = st.session_state.get("normalized_df")
    
    if normalized_df is None or normalized_df.empty:
        st.warning("⚠️ No data available for portfolio analysis.")
        return
    
    # Initialize engines
    portfolio_trend_engine = PortfolioTrendEngine()
    portfolio_model = PortfolioModel(normalized_df)
    
    # Build portfolio data (combine all products if multiple datasets exist)
    # For now, treat entire dataset as one portfolio
    product_data_dict = {"Portfolio": normalized_df}
    portfolio_df = portfolio_trend_engine.combine_all_products(product_data_dict)
    
    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Portfolio Overview",
        "🔍 Cross-Product Trends",
        "⚠️ Emerging Risks",
        "🎛 Product Comparison",
        "🧠 AI Portfolio Summary"
    ])
    
    # ----------------------
    # TAB 1: Portfolio Overview
    # ----------------------
    with tab1:
        st.markdown("### 📈 Portfolio Overview")
        
        # Build portfolio summary
        portfolio_summary = portfolio_model.build_portfolio_summary(signals)
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Products", portfolio_summary["summary"]["total_products"])
        
        with col2:
            st.metric("Total Signals", portfolio_summary["summary"]["total_signals"])
        
        with col3:
            st.metric("Total Cases", portfolio_summary["summary"]["total_cases"])
        
        with col4:
            priority_dist = portfolio_summary["summary"]["priority_distribution"]
            high_priority = priority_dist.get("High", 0) + priority_dist.get("Critical", 0)
            st.metric("High Priority Signals", high_priority)
        
        st.markdown("---")
        
        # Priority distribution chart
        if priority_dist:
            st.markdown("#### Priority Distribution")
            priority_df = pd.DataFrame({
                "Priority": list(priority_dist.keys()),
                "Count": list(priority_dist.values())
            })
            
            if PLOTLY_AVAILABLE:
                fig = px.pie(
                    priority_df,
                    values="Count",
                    names="Priority",
                    title="Signal Priority Distribution Across Portfolio",
                    color_discrete_map={
                        "Critical": "#DC2626",
                        "High": "#EF4444",
                        "Medium": "#F59E0B",
                        "Low": "#10B981"
                    }
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.bar_chart(priority_df.set_index("Priority"))
        
        # Product summary table
        st.markdown("---")
        st.markdown("#### Product Summary")
        
        portfolio_data = portfolio_summary["portfolio"]
        if portfolio_data:
            product_rows = []
            for product, data in portfolio_data.items():
                product_rows.append({
                    "Product": product,
                    "Signals": data.get("signal_count", 0),
                    "Cases": data.get("case_count", 0),
                    "Serious Rate": f"{data.get('serious_case_rate', 0):.1%}" if data.get("serious_case_rate") else "N/A",
                    "Priority": data.get("rpf_priority", "Unknown"),
                    "Therapeutic Area": data.get("therapeutic_area", "N/A")
                })
            
            product_summary_df = pd.DataFrame(product_rows)
            st.dataframe(product_summary_df, use_container_width=True, hide_index=True)
    
    # ----------------------
    # TAB 2: Cross-Product Trends
    # ----------------------
    with tab2:
        st.markdown("### 🔍 Cross-Product Trends")
        
        with st.spinner("Analyzing portfolio trends..."):
            trend_results = portfolio_trend_engine.compute_cross_product_trends(portfolio_df)
        
        # Portfolio volume trend
        if trend_results.get("portfolio_volume"):
            st.markdown("#### 📊 Portfolio Case Volume Trend")
            volume_data = trend_results["portfolio_volume"]
            
            if volume_data:
                volume_df = pd.DataFrame({
                    "Quarter": list(volume_data.keys()),
                    "Case Count": list(volume_data.values())
                }).sort_values("Quarter")
                
                if PLOTLY_AVAILABLE:
                    fig = px.line(
                        volume_df,
                        x="Quarter",
                        y="Case Count",
                        title="Portfolio Case Volume Over Time",
                        markers=True
                    )
                    fig.update_layout(xaxis_tickangle=-45, height=400)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.line_chart(volume_df.set_index("Quarter"))
        
        st.markdown("---")
        
        # Top rising reactions
        if trend_results.get("top_rising_reactions"):
            st.markdown("#### 📈 Top Rising Reactions (Portfolio-Wide)")
            rising_df = pd.DataFrame(trend_results["top_rising_reactions"])
            
            if not rising_df.empty and "reaction" in rising_df.columns:
                display_cols = ["reaction", "slope", "trend_direction"]
                display_df = rising_df[display_cols].rename(columns={
                    "reaction": "Reaction",
                    "slope": "Trend Slope",
                    "trend_direction": "Direction"
                })
                st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # Cross-product spikes
        if trend_results.get("cross_product_spikes"):
            st.markdown("#### ⚠️ Cross-Product Spikes (Reactions in ≥3 Products)")
            spikes = trend_results["cross_product_spikes"]
            
            if spikes:
                spikes_data = []
                for spike in spikes:
                    spikes_data.append({
                        "Reaction": spike.get("reaction", "Unknown"),
                        "Product Count": spike.get("product_count", 0),
                        "Products": ", ".join(spike.get("products", []))[:50] + "..." if len(", ".join(spike.get("products", []))) > 50 else ", ".join(spike.get("products", [])),
                        "Total Cases": spike.get("total_cases", 0)
                    })
                
                spikes_df = pd.DataFrame(spikes_data)
                st.dataframe(spikes_df, use_container_width=True, hide_index=True)
            else:
                st.info("No cross-product spikes detected.")
        else:
            st.info("Cross-product spike analysis not available.")
    
    # ----------------------
    # TAB 3: Emerging Risks
    # ----------------------
    with tab3:
        st.markdown("### ⚠️ Emerging Portfolio Risks")
        
        trend_results = portfolio_trend_engine.compute_cross_product_trends(portfolio_df)
        
        # Class-effect emerging trends
        if trend_results.get("class_effect_emerging"):
            st.markdown("#### 🧬 Class-Effect Emerging Trends")
            class_trends = trend_results["class_effect_emerging"]
            
            if class_trends:
                class_df = pd.DataFrame(class_trends)
                if not class_df.empty:
                    st.dataframe(class_df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # Multi-product emerging risks
        if trend_results.get("multi_product_emerging"):
            st.markdown("#### 🔄 Multi-Product Emerging Risks")
            multi_product = trend_results["multi_product_emerging"]
            
            if multi_product:
                multi_df_data = []
                for risk in multi_product:
                    multi_df_data.append({
                        "Reaction": risk.get("reaction", "Unknown"),
                        "Products": ", ".join(risk.get("products", [])),
                        "Total Cases": risk.get("total_cases", 0)
                    })
                
                multi_df = pd.DataFrame(multi_df_data)
                st.dataframe(multi_df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # Portfolio spikes
        st.markdown("#### 📊 Recent Portfolio Spikes")
        with st.spinner("Detecting portfolio spikes..."):
            spikes = portfolio_trend_engine.detect_portfolio_spikes(portfolio_df)
        
        if spikes:
            spikes_df = pd.DataFrame(spikes)
            if not spikes_df.empty:
                display_cols = ["reaction", "spike_factor", "spike_count", "month"]
                display_df = spikes_df[display_cols].rename(columns={
                    "reaction": "Reaction",
                    "spike_factor": "Spike Factor",
                    "spike_count": "Cases",
                    "month": "Month"
                })
                st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # ----------------------
    # TAB 4: Product Comparison
    # ----------------------
    with tab4:
        st.markdown("### 🎛 Product Comparison Matrix")
        
        portfolio_summary = portfolio_model.build_portfolio_summary(signals)
        portfolio_data = portfolio_summary["portfolio"]
        
        if portfolio_data:
            # Create comparison matrix
            comparison_data = []
            
            for product, data in portfolio_data.items():
                comparison_data.append({
                    "Product": product,
                    "Signals": data.get("signal_count", 0),
                    "Cases": data.get("case_count", 0),
                    "Serious Rate": data.get("serious_case_rate", 0) or 0,
                    "Priority": data.get("rpf_priority", "Unknown"),
                    "Confidence": data.get("confidence_score", 0) or 0,
                    "SHMI": data.get("shmi", 0) or 0,
                    "TA": data.get("therapeutic_area", "N/A")
                })
            
            comparison_df = pd.DataFrame(comparison_data)
            
            # Heatmap of key metrics
            if PLOTLY_AVAILABLE and not comparison_df.empty:
                # Normalize metrics for heatmap
                metrics_df = comparison_df.set_index("Product")[["Signals", "Cases", "Serious Rate", "Confidence", "SHMI"]]
                
                fig = px.imshow(
                    metrics_df.T,
                    labels=dict(x="Product", y="Metric", color="Value"),
                    aspect="auto",
                    title="Product Comparison Heatmap",
                    color_continuous_scale="Reds"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Detailed comparison table
            st.dataframe(comparison_df, use_container_width=True, hide_index=True)
    
    # ----------------------
    # TAB 5: AI Portfolio Summary
    # ----------------------
    with tab5:
        st.markdown("### 🧠 AI Portfolio Summary")
        
        if LLM_AVAILABLE and medical_llm:
            portfolio_summary = portfolio_model.build_portfolio_summary(signals)
            trend_results = portfolio_trend_engine.compute_cross_product_trends(portfolio_df)
            
            if st.button("🔄 Generate AI Portfolio Summary", type="primary"):
                with st.spinner("Generating comprehensive portfolio summary..."):
                    summary_text = _generate_portfolio_ai_summary(
                        portfolio_summary,
                        trend_results,
                        medical_llm
                    )
                    
                    if summary_text:
                        st.markdown(summary_text)
                    else:
                        st.error("Failed to generate AI summary.")
        else:
            st.info("AI portfolio summary requires LLM availability.")


def _generate_portfolio_ai_summary(
    portfolio_summary: Dict[str, Any],
    trend_results: Dict[str, Any],
    medical_llm
) -> Optional[str]:
    """Generate AI-powered portfolio summary."""
    if not LLM_AVAILABLE:
        return None
    
    prompt = f"""
You are a senior pharmacovigilance executive analyzing a complete product portfolio.

PORTFOLIO SUMMARY:
{portfolio_summary["summary"]}

CROSS-PRODUCT TRENDS:
- Top Rising Reactions: {trend_results.get("top_rising_reactions", [])[:5]}
- Cross-Product Spikes: {trend_results.get("cross_product_spikes", [])[:5]}
- Class-Effect Trends: {trend_results.get("class_effect_emerging", [])[:5]}

Generate a comprehensive executive-level portfolio safety summary covering:
1. Portfolio Risk Overview
2. Key Emerging Risks
3. Cross-Product Patterns
4. Priority Signals Requiring Attention
5. Recommended Actions

Format as a professional regulatory summary suitable for executive review and safety committee presentation.
"""
    
    try:
        system_prompt = "You are a senior pharmacovigilance executive providing portfolio-level safety intelligence summaries."
        
        if callable(medical_llm):
            return medical_llm(prompt, system_prompt)
        else:
            return call_medical_llm(
                prompt=prompt,
                system_prompt=system_prompt,
                task_type="regulatory_writing",
                max_tokens=2000,
                temperature=0.3
            )
    except Exception as e:
        return f"AI summary generation error: {str(e)}"

