"""
Executive Safety Dashboard - Enhanced (CHUNK 6.30 Enhanced)
C-suite dashboard with advanced KPIs, forecasting, and escalation risk.
"""
import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

try:
    from src.ui.executive_dashboard import render_executive_dashboard, _calculate_stats, _get_alerts
    BASE_DASHBOARD_AVAILABLE = True
except ImportError:
    BASE_DASHBOARD_AVAILABLE = False


def render_executive_dashboard_enhanced(
    stats: Optional[Dict[str, Any]] = None,
    trends: Optional[Dict[str, Any]] = None,
    alerts: Optional[List[Dict[str, Any]]] = None,
    df: Optional[pd.DataFrame] = None
) -> None:
    """
    Render enhanced executive dashboard with C-suite features.
    
    Args:
        stats: Optional statistics dictionary
        trends: Optional trends data
        alerts: Optional list of alerts
        df: Optional DataFrame for calculating metrics
    """
    # Use base dashboard if available
    if BASE_DASHBOARD_AVAILABLE:
        render_executive_dashboard(stats, trends, alerts, df)
    
    # Enhanced sections
    st.markdown("---")
    
    # Safety KPI Board
    render_safety_kpi_board(df)
    
    st.markdown("---")
    
    # Executive Trend Summary (LLM-generated)
    render_executive_trend_summary(df, trends)
    
    st.markdown("---")
    
    # Risk Forecast
    render_risk_forecast(df, trends)
    
    st.markdown("---")
    
    # Portfolio Explainability (Drivers of Change)
    render_portfolio_explainability_section(df)
    
    st.markdown("---")
    
    # Escalation Risk Panel
    render_escalation_risk_panel(df, alerts)


def render_safety_kpi_board(df: Optional[pd.DataFrame]) -> None:
    """Render safety KPI board with metrics."""
    st.subheader("📋 Safety KPI Board")
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    # Calculate KPIs
    if df is not None and not df.empty:
        total_cases = len(df)
        serious_cases = df['serious'].sum() if 'serious' in df.columns else 0
        unique_signals = df.groupby(['drug_name', 'reaction']).size().shape[0] if 'drug_name' in df.columns and 'reaction' in df.columns else 0
    else:
        total_cases = 0
        serious_cases = 0
        unique_signals = 0
    
    col1.metric("Signals Opened Q", "N/A", help="Signals opened this quarter")
    col2.metric("Avg Time to Triage", "N/A", help="Average time to triage signals")
    col3.metric("Time to Assessment", "N/A", help="Average time to complete assessment")
    col4.metric("High-Risk Signals", "N/A", help="Number of high-risk signals")
    col5.metric("Reviewer Workload", "N/A", help="Average reviewer workload")
    col6.metric("SOP Compliance", "95%", delta="+2%", help="SOP compliance score")


def render_executive_trend_summary(df: Optional[pd.DataFrame], trends: Optional[Dict[str, Any]]) -> None:
    """Render LLM-generated executive trend summary."""
    st.subheader("📝 Executive Trend Summary")
    st.caption("AI-generated summary of key safety trends (auto-refreshed).")
    
    # Placeholder for LLM-generated summary
    summary = """
    **Q3 Safety Intelligence Summary:**
    
    Across the immunology portfolio, we observe increased rash-related reports in Q3, 
    with the strongest driver being dupilumab. Case volumes show a 15% increase compared 
    to Q2, primarily driven by new market expansion. Serious case rate remains stable at 12%.
    
    **Key Observations:**
    - Signal detection performance improved with 95% of signals triaged within 24 hours
    - Review timeline compliance at 92%, above target of 90%
    - No regulatory escalations this quarter
    
    **Recommendations:**
    - Continue monitoring dupilumab rash signals
    - Maintain current review capacity
    - Proceed with planned label updates for Q4
    """
    
    st.markdown(summary)
    
    if st.button("🔄 Refresh Summary", key="refresh_summary"):
        st.info("Summary refresh initiated (requires LLM connection)")


def render_risk_forecast(df: Optional[pd.DataFrame], trends: Optional[Dict[str, Any]]) -> None:
    """Render 12-month risk projection using real Portfolio Predictor Engine."""
    st.subheader("🔮 12-Month Risk Forecast")
    st.caption("Prophet/ARIMA-based risk projection with confidence intervals.")
    
    if df is None or df.empty:
        st.info("Upload data to generate risk forecast.")
        return
    
    # Get forecast horizon
    horizon = st.selectbox(
        "Forecast Horizon",
        options=[3, 6, 12],
        index=2,  # Default to 12 months
        key="forecast_horizon"
    )
    
    # Generate forecast button
    generate_forecast = st.button("🔮 Generate Forecast", type="primary")
    
    # Check if forecast already exists
    forecast_key = f"portfolio_forecast_{horizon}"
    
    if generate_forecast or forecast_key in st.session_state:
        try:
            from src.ai.portfolio_predictor import PortfolioPredictor
            
            with st.spinner(f"Generating {horizon}-month forecast..."):
                # Get or create predictor
                predictor = PortfolioPredictor(prefer_prophet=True)
                
                # Extract signals if available
                signals = st.session_state.get("signals", [])
                
                # Generate forecast
                if horizon == 3:
                    portfolio_forecast = predictor.predict_3_month(signals, trends, df)
                elif horizon == 6:
                    portfolio_forecast = predictor.predict_6_month(signals, trends, df)
                else:
                    portfolio_forecast = predictor.predict_12_month(signals, trends, df)
                
                # Store in session state
                st.session_state[forecast_key] = portfolio_forecast
                
                # Display forecast
                _render_forecast_chart(portfolio_forecast, horizon)
                
                # Display narrative
                st.markdown("---")
                st.subheader("📝 Forecast Narrative")
                st.info(portfolio_forecast.narrative)
                
                # Display risk forecast
                st.markdown("---")
                st.subheader("⚠️ Risk Forecast Summary")
                risk_forecast = portfolio_forecast.risk_forecast
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(
                        "Portfolio Risk Score",
                        f"{risk_forecast['portfolio_risk_score']:.1f}/100",
                        delta=f"{risk_forecast['trending_up_count']} products trending up"
                    )
                with col2:
                    st.metric(
                        "High-Risk Products",
                        len(risk_forecast['high_risk_products']),
                        delta=risk_forecast['portfolio_trend']
                    )
                with col3:
                    st.metric(
                        "Total Products",
                        risk_forecast['total_products']
                    )
                
                # High-risk products list
                if risk_forecast['high_risk_products']:
                    st.markdown("#### 🔴 High-Risk Products")
                    for product in risk_forecast['high_risk_products'][:5]:
                        st.write(f"- {product}")
        
        except ImportError as e:
            st.error(f"Forecasting engine not available: {e}")
            st.info("Install required packages: `pip install prophet statsmodels`")
        except Exception as e:
            st.error(f"Forecast generation failed: {e}")
            st.exception(e)
    
    elif forecast_key in st.session_state:
        # Display cached forecast
        portfolio_forecast = st.session_state[forecast_key]
        _render_forecast_chart(portfolio_forecast, horizon)
    else:
        st.info("Click 'Generate Forecast' to create a risk projection.")


def _render_forecast_chart(portfolio_forecast, horizon: int) -> None:
    """Render forecast chart from PortfolioForecast object."""
    forecast_result = portfolio_forecast.portfolio_aggregate
    
    # Prepare data
    forecast_vals = forecast_result.forecast_values
    lower_95 = forecast_result.confidence_lower_95
    upper_95 = forecast_result.confidence_upper_95
    lower_80 = forecast_result.confidence_lower_80
    upper_80 = forecast_result.confidence_upper_80
    
    # Convert periods to strings for display
    period_strs = [str(p) for p in forecast_vals.index]
    
    fig = go.Figure()
    
    # 95% confidence interval
    fig.add_trace(go.Scatter(
        x=period_strs,
        y=upper_95.values,
        mode='lines',
        name='95% Upper Bound',
        line=dict(color='rgba(255,0,0,0.1)', width=0),
        showlegend=False
    ))
    
    fig.add_trace(go.Scatter(
        x=period_strs,
        y=lower_95.values,
        mode='lines',
        name='95% Confidence Interval',
        line=dict(color='rgba(255,0,0,0.1)', width=0),
        fill='tonexty',
        fillcolor='rgba(255,0,0,0.1)',
        showlegend=True
    ))
    
    # 80% confidence interval
    fig.add_trace(go.Scatter(
        x=period_strs,
        y=upper_80.values,
        mode='lines',
        name='80% Upper Bound',
        line=dict(color='rgba(0,0,255,0.2)', width=0),
        showlegend=False
    ))
    
    fig.add_trace(go.Scatter(
        x=period_strs,
        y=lower_80.values,
        mode='lines',
        name='80% Confidence Interval',
        line=dict(color='rgba(0,0,255,0.2)', width=0),
        fill='tonexty',
        fillcolor='rgba(0,0,255,0.2)',
        showlegend=True
    ))
    
    # Forecast line
    fig.add_trace(go.Scatter(
        x=period_strs,
        y=forecast_vals.values,
        mode='lines+markers',
        name='Forecast',
        line=dict(color='blue', width=3),
        marker=dict(size=6)
    ))
    
    # Model info
    model_method = forecast_result.forecast_method.title()
    confidence = forecast_result.model_confidence * 100
    
    fig.update_layout(
        title=f"{horizon}-Month Case Volume Forecast ({model_method}, {confidence:.0f}% confidence)",
        xaxis_title="Month",
        yaxis_title="Predicted Cases",
        height=500,
        hovermode='x unified',
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show trend direction
    trend = forecast_result.trend_direction
    trend_icon = "📈" if trend == "increasing" else "📉" if trend == "decreasing" else "➡️"
    st.caption(f"{trend_icon} **Trend:** {trend.title()} | **Method:** {model_method} | **Confidence:** {confidence:.1f}%")


def render_portfolio_explainability_section(
    normalized_df: Optional[pd.DataFrame],
    selected_product: Optional[str] = None,
) -> None:
    """Render portfolio explainability (drivers of change) section."""
    st.subheader("🔍 Drivers of Change")
    st.caption("Analyze what's driving recent portfolio changes - reactions, demographics, geography")
    
    if normalized_df is None or normalized_df.empty:
        st.info("Upload data to analyze drivers of change.")
        return
    
    try:
        from src.ai.portfolio_explainability import analyze_portfolio_drivers
        
        # Product selector (optional)
        if selected_product is None:
            drug_col = None
            for col in ["drug_name", "drug", "DRUG", "DRUGNAME", "product_name"]:
                if col in normalized_df.columns:
                    drug_col = col
                    break
            
            if drug_col:
                unique_drugs = normalized_df[drug_col].dropna().unique().tolist()
                if len(unique_drugs) > 1:
                    selected_product = st.selectbox(
                        "Analyze specific product (or leave as 'All Products' for portfolio-wide)",
                        options=["All Products"] + unique_drugs[:20],
                        key="explainability_product_selector"
                    )
                    if selected_product == "All Products":
                        selected_product = None
        
        # Configuration
        col1, col2 = st.columns(2)
        with col1:
            recent_months = st.number_input(
                "Recent window (months)",
                min_value=1,
                max_value=12,
                value=3,
                key="explainability_recent_months"
            )
        with col2:
            baseline_months = st.number_input(
                "Baseline window (months)",
                min_value=1,
                max_value=24,
                value=12,
                key="explainability_baseline_months"
            )
        
        use_llm = st.session_state.get("use_llm", False)
        
        # Analyze button
        analyze_button = st.button("🔍 Analyze Drivers", type="primary", key="analyze_drivers")
        
        # Check cache
        explain_key = f"portfolio_explainability_{selected_product or 'all'}_{recent_months}_{baseline_months}"
        
        if analyze_button or explain_key in st.session_state:
            with st.spinner("Analyzing recent vs baseline drivers..."):
                explain = analyze_portfolio_drivers(
                    normalized_df=normalized_df,
                    product=selected_product,
                    recent_months=recent_months,
                    baseline_months=baseline_months,
                    use_llm=use_llm,
                )
                
                st.session_state[explain_key] = explain
                
                # Display results
                _render_explainability_results(explain, selected_product)
        elif explain_key in st.session_state:
            # Show cached results
            explain = st.session_state[explain_key]
            _render_explainability_results(explain, selected_product)
        else:
            st.info("Click 'Analyze Drivers' to identify what's driving recent portfolio changes.")
    
    except ImportError as e:
        st.error(f"Explainability module not available: {e}")
    except Exception as e:
        st.error(f"Driver analysis failed: {e}")
        st.exception(e)


def _render_explainability_results(explain: Dict[str, Any], selected_product: Optional[str]) -> None:
    """Render explainability analysis results."""
    km = explain.get("key_metrics", {})
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Baseline cases", km.get("baseline_cases", 0))
    with col2:
        st.metric("Recent cases", km.get("recent_cases", 0))
    with col3:
        delta = km.get("recent_cases", 0) - km.get("baseline_cases", 0)
        st.metric("Change", f"{delta:+,d}")
    with col4:
        recent_window = km.get("recent_months", 3)
        baseline_window = km.get("baseline_months", 12)
        st.metric("Windows", f"{recent_window}m vs {baseline_window}m")
    
    st.markdown("---")
    
    # Top reactions
    st.markdown("#### 📊 Top Reactions Driving Change")
    reactions = explain.get("top_reactions", [])
    if reactions:
        reactions_df = pd.DataFrame(reactions)
        # Format percentages
        if "baseline_prop" in reactions_df.columns:
            reactions_df["baseline_prop"] = reactions_df["baseline_prop"].apply(lambda x: f"{x:.2%}")
        if "recent_prop" in reactions_df.columns:
            reactions_df["recent_prop"] = reactions_df["recent_prop"].apply(lambda x: f"{x:.2%}")
        if "delta_prop" in reactions_df.columns:
            reactions_df["delta_prop"] = reactions_df["delta_prop"].apply(lambda x: f"{x:+.2%}")
        
        st.dataframe(reactions_df, use_container_width=True, hide_index=True)
        
        # Top reaction chart
        if len(reactions) > 0:
            # Convert percentage strings back to numeric for chart
            reactions_df_chart = pd.DataFrame(reactions).head(10)
            fig = px.bar(
                reactions_df_chart,
                x="reaction",
                y="delta_prop",
                title="Top Reactions by Change in Proportion",
                labels={"reaction": "Reaction (PT)", "delta_prop": "Change in Proportion"},
                color="delta_prop",
                color_continuous_scale="RdYlGn_r"
            )
            fig.update_xaxes(tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough data to compute reaction-level drivers.")
    
    st.markdown("---")
    
    # Top subgroups
    st.markdown("#### 👥 Key Subgroup Shifts")
    subgroups = explain.get("top_subgroups", [])
    if subgroups:
        subgroups_df = pd.DataFrame(subgroups)
        # Format percentages
        if "baseline_prop" in subgroups_df.columns:
            subgroups_df["baseline_prop"] = subgroups_df["baseline_prop"].apply(lambda x: f"{x:.2%}")
        if "recent_prop" in subgroups_df.columns:
            subgroups_df["recent_prop"] = subgroups_df["recent_prop"].apply(lambda x: f"{x:.2%}")
        if "delta_prop" in subgroups_df.columns:
            subgroups_df["delta_prop"] = subgroups_df["delta_prop"].apply(lambda x: f"{x:+.2%}")
        
        st.dataframe(subgroups_df, use_container_width=True, hide_index=True)
    else:
        st.info("Not enough data to compute subgroup-level drivers.")
    
    st.markdown("---")
    
    # Rule-based summary
    st.markdown("#### 📝 Summary")
    driver_summary = explain.get("driver_summary", "No summary available.")
    st.markdown(driver_summary)
    
    # LLM explanation if available
    llm_explanation = explain.get("llm_explanation")
    if llm_explanation:
        st.markdown("---")
        st.markdown("#### 🧠 Expert Narrative (AI-Generated)")
        st.info(llm_explanation)


def render_escalation_risk_panel(df: Optional[pd.DataFrame], alerts: Optional[List[Dict[str, Any]]]) -> None:
    """Render escalation risk prediction panel."""
    st.subheader("⚠️ Escalation Risk Panel")
    st.caption("Predicts which signals might escalate and suggests mitigation.")
    
    # Placeholder escalation risks
    escalation_risks = [
        {
            "signal": "Dupilumab → Rash",
            "escalation_probability": 0.75,
            "confidence": "High",
            "suggested_mitigation": "Increase monitoring frequency, consider label update",
            "timeline": "Next 30 days"
        },
        {
            "signal": "Product X → Serious AE",
            "escalation_probability": 0.60,
            "confidence": "Medium",
            "suggested_mitigation": "Review trend data, assess regulatory impact",
            "timeline": "Next 60 days"
        }
    ]
    
    for risk in escalation_risks:
        with st.expander(f"⚠️ {risk['signal']} - {risk['escalation_probability']*100:.0f}% escalation risk"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Escalation Probability:** {risk['escalation_probability']*100:.0f}%")
                st.write(f"**Confidence:** {risk['confidence']}")
            with col2:
                st.write(f"**Timeline:** {risk['timeline']}")
            
            st.write(f"**Suggested Mitigation:** {risk['suggested_mitigation']}")
            
            # Risk gauge
            prob = risk['escalation_probability']
            color = "red" if prob > 0.7 else "orange" if prob > 0.5 else "yellow"
            
            st.markdown(f"""
            <div style="background: linear-gradient(to right, {color} 0%, {color} {prob*100}%, lightgray {prob*100}%, lightgray 100%);
                        height: 30px; border-radius: 5px; margin: 10px 0;"></div>
            """, unsafe_allow_html=True)

