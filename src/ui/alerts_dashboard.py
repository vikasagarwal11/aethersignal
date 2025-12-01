"""
Alerts Dashboard UI (Phase 2D.6)
Streamlit UI for viewing and managing alerts.
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

from src.alerts.alerts_engine import AlertsEngine
from src.alerts.alert_router import AlertRouter

logger = logging.getLogger(__name__)


def render_alerts_dashboard(
    df: Optional[pd.DataFrame] = None,
    drug: Optional[str] = None
):
    """
    Render alerts dashboard.
    
    Args:
        df: Optional DataFrame with AE entries
        drug: Optional drug filter
    """
    st.header("🚨 AetherSignal Alerts Dashboard")
    st.caption("Real-time alerts based on quantum scoring, burst detection, consensus, and novelty")
    
    # Initialize engines
    alerts_engine = AlertsEngine()
    alert_router = AlertRouter()
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔔 Active Alerts",
        "📊 Alert Inspector",
        "⚙️ Settings",
        "📈 Statistics"
    ])
    
    with tab1:
        render_active_alerts_tab(df, drug, alerts_engine, alert_router)
    
    with tab2:
        render_alert_inspector_tab(df, drug, alerts_engine)
    
    with tab3:
        render_settings_tab(alert_router)
    
    with tab4:
        render_statistics_tab(df, drug, alerts_engine)


def render_active_alerts_tab(
    df: Optional[pd.DataFrame],
    drug: Optional[str],
    alerts_engine: AlertsEngine,
    alert_router: AlertRouter
):
    """Render active alerts tab."""
    st.subheader("🔔 Active Alerts")
    
    if df is None or df.empty:
        st.info("👆 Load AE data first to generate alerts")
        return
    
    # Generate alerts
    if st.button("🔄 Generate Alerts", type="primary"):
        with st.spinner("Analyzing data and generating alerts..."):
            alerts = alerts_engine.generate_alerts(df, drug=drug)
            
            if not alerts:
                st.success("✅ No alerts generated. All signals are within normal thresholds.")
            else:
                st.success(f"🔔 Generated {len(alerts)} alert(s)")
                
                # Store in session state
                st.session_state["alerts"] = alerts
                
                # Auto-dispatch high priority alerts
                high_priority = [a for a in alerts if a.get("alert_type") == "high_priority"]
                if high_priority:
                    with st.spinner("Dispatching high-priority alerts..."):
                        for alert in high_priority:
                            results = alert_router.dispatch(alert)
                            st.session_state[f"alert_delivery_{alert['alert_id']}"] = results
    
    # Display alerts
    if "alerts" in st.session_state:
        alerts = st.session_state["alerts"]
        
        # Filter options
        col1, col2, col3 = st.columns(3)
        with col1:
            alert_type_filter = st.multiselect(
                "Filter by Type",
                options=["high_priority", "burst", "novel_ae", "watchlist"],
                default=None
            )
        with col2:
            severity_filter = st.multiselect(
                "Filter by Severity",
                options=["critical", "high", "moderate", "watchlist", "low"],
                default=None
            )
        with col3:
            sort_by = st.selectbox(
                "Sort by",
                options=["quantum_score", "timestamp", "total_cases"],
                index=0
            )
        
        # Filter alerts
        filtered_alerts = alerts
        if alert_type_filter:
            filtered_alerts = [a for a in filtered_alerts if a.get("alert_type") in alert_type_filter]
        if severity_filter:
            filtered_alerts = [a for a in filtered_alerts if a.get("severity") in severity_filter]
        
        # Sort
        filtered_alerts.sort(key=lambda x: x.get(sort_by, 0), reverse=True)
        
        # Display
        for alert in filtered_alerts:
            with st.expander(
                f"**{alert.get('drug')} → {alert.get('reaction')}** "
                f"({alert.get('alert_type').replace('_', ' ').title()}) - "
                f"Quantum Score: {alert.get('quantum_score', 0):.2f}",
                expanded=False
            ):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Quantum Score", f"{alert.get('quantum_score', 0):.3f}")
                    st.metric("Total Cases", alert.get("total_cases", 0))
                    st.metric("Sources", alert.get("source_count", 0))
                
                with col2:
                    st.metric("Severity", alert.get("severity", "unknown").title())
                    st.metric("Alert Type", alert.get("alert_type", "unknown").replace("_", " ").title())
                    st.metric("Consensus", f"{alert.get('consensus', {}).get('consensus_score', 0):.2f}")
                
                st.markdown("---")
                st.write("**Summary:**", alert.get("summary", ""))
                st.write("**Suggested Action:**", alert.get("suggested_action", ""))
                
                # Component breakdown
                components = alert.get("components", {})
                if components:
                    st.markdown("**Component Scores:**")
                    comp_df = pd.DataFrame([
                        {"Component": k.replace("_", " ").title(), "Score": v}
                        for k, v in components.items()
                    ])
                    st.dataframe(comp_df, use_container_width=True, hide_index=True)
                
                # Source breakdown
                consensus = alert.get("consensus", {})
                source_breakdown = consensus.get("source_breakdown", {})
                if source_breakdown:
                    st.markdown("**Source Breakdown:**")
                    source_df = pd.DataFrame([
                        {
                            "Source": source,
                            "Count": info.get("count", 0),
                            "Weight": info.get("weight", 0),
                            "Avg Confidence": info.get("avg_confidence", 0)
                        }
                        for source, info in source_breakdown.items()
                    ])
                    st.dataframe(source_df, use_container_width=True, hide_index=True)
                
                # Delivery status
                alert_id = alert.get("alert_id")
                if alert_id and f"alert_delivery_{alert_id}" in st.session_state:
                    delivery = st.session_state[f"alert_delivery_{alert_id}"]
                    st.markdown("**Delivery Status:**")
                    for channel, result in delivery.items():
                        status = result.get("status", "unknown")
                        emoji = "✅" if status == "sent" or status == "stored" else "❌"
                        st.write(f"{emoji} {channel}: {status}")


def render_alert_inspector_tab(
    df: Optional[pd.DataFrame],
    drug: Optional[str],
    alerts_engine: AlertsEngine
):
    """Render alert inspector tab."""
    st.subheader("📊 Alert Inspector")
    
    if df is None or df.empty:
        st.info("👆 Load AE data first")
        return
    
    # Drug and reaction selectors
    col1, col2 = st.columns(2)
    with col1:
        selected_drug = st.selectbox(
            "Select Drug",
            options=sorted(df["drug"].unique()) if "drug" in df.columns else [],
            key="inspector_drug"
        )
    with col2:
        if selected_drug and "reaction" in df.columns:
            drug_df = df[df["drug"].str.contains(selected_drug, case=False, na=False)]
            selected_reaction = st.selectbox(
                "Select Reaction",
                options=sorted(drug_df["reaction"].unique()),
                key="inspector_reaction"
            )
        else:
            selected_reaction = None
    
    if selected_drug and selected_reaction:
        # Compute detailed analysis
        with st.spinner("Analyzing drug-reaction pair..."):
            from src.ai.multi_source_quantum_scoring import MultiSourceQuantumScoring
            from src.ai.cross_source_consensus import CrossSourceConsensusEngine
            from src.ai.novelty_detection import NoveltyDetectionEngine
            
            quantum_scoring = MultiSourceQuantumScoring()
            consensus_engine = CrossSourceConsensusEngine()
            novelty_engine = NoveltyDetectionEngine()
            
            # Quantum score
            quantum_result = quantum_scoring.compute_quantum_score(
                selected_drug, selected_reaction, df
            )
            
            # Consensus
            consensus = consensus_engine.compute_consensus(
                selected_drug, selected_reaction, df
            )
            
            # Novelty
            novelty = novelty_engine.compute_novelty_score(
                selected_drug, selected_reaction, df
            )
            
            # Display results
            st.markdown("### Quantum Score Breakdown")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Quantum Score", f"{quantum_result['quantum_score']:.3f}")
            with col2:
                st.metric("Alert Level", quantum_result['alert_level'].title())
            with col3:
                st.metric("Total Cases", quantum_result['total_cases'])
            
            # Components
            st.markdown("### Component Scores")
            components = quantum_result['components']
            comp_df = pd.DataFrame([
                {"Component": k.replace("_", " ").title(), "Score": v, "Weight": quantum_scoring.weights.get(k, 0)}
                for k, v in components.items()
            ])
            st.dataframe(comp_df, use_container_width=True, hide_index=True)
            
            # Consensus
            st.markdown("### Cross-Source Consensus")
            st.metric("Consensus Score", f"{consensus.get('consensus_score', 0):.3f}")
            st.metric("Source Count", consensus.get('source_count', 0))
            st.write("**Sources:**", ", ".join(consensus.get('sources', [])))
            
            # Novelty
            st.markdown("### Novelty Analysis")
            st.metric("Novelty Score", f"{novelty.get('novelty_score', 0):.3f}")
            st.metric("Is Novel", "Yes" if novelty.get('is_novel', False) else "No")
            st.write("**Novelty Level:**", novelty.get('novelty_level', 'unknown').replace('_', ' ').title())


def render_settings_tab(alert_router: AlertRouter):
    """Render settings tab."""
    st.subheader("⚙️ Alert Settings")
    
    st.markdown("### Channel Configuration")
    
    config = alert_router.config.get("channels", {})
    
    email_enabled = st.checkbox("Email Alerts", value=config.get("email", False))
    slack_enabled = st.checkbox("Slack Alerts", value=config.get("slack", False))
    webhook_enabled = st.checkbox("Webhook Alerts", value=config.get("webhook", False))
    api_enabled = st.checkbox("API Alerts", value=config.get("api", True))
    inapp_enabled = st.checkbox("In-App Notifications", value=config.get("inapp", True))
    
    st.markdown("### Thresholds")
    
    thresholds = alert_router.config.get("thresholds", {})
    
    col1, col2 = st.columns(2)
    with col1:
        high_priority_threshold = st.slider(
            "High Priority Threshold",
            0.0, 1.0, thresholds.get("high_priority", 0.80), 0.05
        )
        watchlist_threshold = st.slider(
            "Watchlist Threshold",
            0.0, 1.0, thresholds.get("watchlist", 0.45), 0.05
        )
    with col2:
        burst_threshold = st.slider(
            "Burst Threshold",
            0.0, 1.0, thresholds.get("burst", 0.5), 0.05
        )
        novelty_threshold = st.slider(
            "Novelty Threshold",
            0.0, 1.0, thresholds.get("novel_ae", 0.7), 0.05
        )
    
    if st.button("💾 Save Settings"):
        # In production, would save to config file
        st.success("✅ Settings saved (in-memory only in demo)")


def render_statistics_tab(
    df: Optional[pd.DataFrame],
    drug: Optional[str],
    alerts_engine: AlertsEngine
):
    """Render statistics tab."""
    st.subheader("📈 Alert Statistics")
    
    if df is None or df.empty:
        st.info("👆 Load AE data first")
        return
    
    if "alerts" not in st.session_state:
        st.info("👆 Generate alerts first")
        return
    
    alerts = st.session_state["alerts"]
    
    # Summary statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Alerts", len(alerts))
    
    with col2:
        high_priority = len([a for a in alerts if a.get("alert_type") == "high_priority"])
        st.metric("High Priority", high_priority)
    
    with col3:
        avg_score = sum(a.get("quantum_score", 0) for a in alerts) / len(alerts) if alerts else 0
        st.metric("Avg Quantum Score", f"{avg_score:.2f}")
    
    with col4:
        total_cases = sum(a.get("total_cases", 0) for a in alerts)
        st.metric("Total Cases", total_cases)
    
    # Alert type breakdown
    st.markdown("### Alert Type Breakdown")
    alert_types = {}
    for alert in alerts:
        alert_type = alert.get("alert_type", "unknown")
        alert_types[alert_type] = alert_types.get(alert_type, 0) + 1
    
    type_df = pd.DataFrame([
        {"Type": k.replace("_", " ").title(), "Count": v}
        for k, v in alert_types.items()
    ])
    st.dataframe(type_df, use_container_width=True, hide_index=True)

