"""
Pre-Inspection Heatmap Dashboard (CHUNK 6.21.1 - Part 25)
Visualizes compliance and risk dimensions across governed signals and items.
Supports multiple styling themes and uses existing analytics engines.
"""
import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional

try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False


HEATMAP_STYLES = {
    "Enterprise Blue": {
        "low": "#C7D7F7",
        "medium": "#7FA8F8",
        "high": "#3B82F6",
        "critical": "#1E40AF",
        "na": "#E5E7EB",
    },
    "Minimal Grey": {
        "low": "#F3F4F6",
        "medium": "#D1D5DB",
        "high": "#9CA3AF",
        "critical": "#4B5563",
        "na": "#F9FAFB",
    },
    "Green/Yellow/Red": {
        "low": "#4ADE80",
        "medium": "#FACC15",
        "high": "#FB923C",
        "critical": "#EF4444",
        "na": "#E5E7EB",
    },
    "Gradient Scale": {
        "low": "#D1FAE5",
        "medium": "#FDE68A",
        "high": "#FCA5A5",
        "critical": "#DC2626",
        "na": "#F3F4F6",
    }
}


def render_governance_heatmap_tab(
    heatmap_data: Optional[pd.DataFrame] = None,
    signals: Optional[List[Dict[str, Any]]] = None,
    trend_alerts: Optional[Dict[str, Any]] = None,
    governance_data: Optional[Dict[str, Any]] = None
) -> None:
    """
    Render Pre-Inspection Heatmap Dashboard tab.
    
    Args:
        heatmap_data: Pre-computed heatmap DataFrame (optional)
        signals: List of signal dictionaries
        trend_alerts: Trend alerts data
        governance_data: Governance package data
    """
    st.header("🛡️ Pre-Inspection Heatmap Dashboard")
    
    st.markdown("""
    Visualize compliance and risk dimensions across signals, trends, and governance items.
    Each cell reflects a risk or compliance dimension. Hover or click for detailed information.
    """)
    
    # Generate heatmap data if not provided
    if heatmap_data is None:
        heatmap_data = build_heatmap_schema(
            signals=signals,
            trend_alerts=trend_alerts,
            governance_data=governance_data
        )
    
    if heatmap_data is None or heatmap_data.empty:
        st.warning("No data available for heatmap visualization. Please load data and generate signals first.")
        return
    
    # CHUNK A6: Apply multi-layer filters
    try:
        from src.ui.heatmap_filters import render_heatmap_filters
        heatmap_data, filter_settings = render_heatmap_filters(heatmap_data, signals)
        
        if heatmap_data.empty:
            st.warning("No signals match the selected filters. Please adjust filter criteria.")
            return
    except ImportError:
        # Filters not available, use original data
        filter_settings = {}
        pass
    
    # Style selection
    style_col1, style_col2 = st.columns([1, 3])
    with style_col1:
        selected_style = st.selectbox(
            "Heatmap Style:",
            list(HEATMAP_STYLES.keys()),
            index=0,
            help="Choose visualization style for risk/compliance heatmap"
        )
    
    colors = HEATMAP_STYLES[selected_style]
    
    # CHUNK A7.1: Interactive drill-down support
    selected_cell = None
    
    # Display heatmap using enterprise renderer (CHUNK A4)
    try:
        from src.ui.heatmap_renderer import render_enterprise_heatmap
        render_enterprise_heatmap(heatmap_data, title="Pre-Inspection Risk & Compliance Heatmap")
        
        # Add drill-down button (CHUNK A7.1)
        st.markdown("---")
        st.markdown("### 🔍 Signal Drill-Down")
        st.info("💡 **Tip:** Select a signal from the heatmap to view detailed governance information.")
        
        # Signal selector for drill-down
        if heatmap_data is not None and not heatmap_data.empty:
            signal_options = [str(idx) for idx in heatmap_data.index]
            selected_signal = st.selectbox(
                "Select Signal for Detailed View:",
                options=signal_options,
                help="Choose a signal to drill down into governance details"
            )
            
            if selected_signal and st.button("🔍 Drill Down", key="heatmap_drill_down"):
                # Parse signal name (format: "Drug - Reaction")
                if " - " in selected_signal:
                    drug, reaction = selected_signal.split(" - ", 1)
                    
                    # Show drill-down panel
                    try:
                        from src.ui.signal_governance_panel import show_signal_governance_panel
                        
                        # Get normalized_df from session state if available
                        normalized_df = st.session_state.get("normalized_df")
                        
                        # Extract trend alerts for this signal
                        signal_trends = []
                        if trend_alerts and isinstance(trend_alerts, dict):
                            all_alerts = trend_alerts.get("alerts", [])
                            for alert in all_alerts:
                                if isinstance(alert, dict):
                                    alert_drug = alert.get("drug", "")
                                    alert_reaction = alert.get("reaction", "")
                                    if (drug.lower() in str(alert_drug).lower() or
                                        reaction.lower() in str(alert_reaction).lower()):
                                        signal_trends.append(alert)
                        
                        show_signal_governance_panel(
                            drug=drug,
                            reaction=reaction,
                            normalized_df=normalized_df,
                            signals=signals,
                            trend_alerts=signal_trends
                        )
                    except ImportError:
                        st.warning("Signal governance panel not available. Install required components.")
    except ImportError:
        # Fallback to original renderers
        if PLOTLY_AVAILABLE and len(heatmap_data) > 0:
            _render_plotly_heatmap(heatmap_data, colors)
        else:
            _render_html_heatmap(heatmap_data, colors)
    
    # Legend
    st.markdown("---")
    st.markdown("### 📊 Legend")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(f"🟢 **Low Risk**")
    with col2:
        st.markdown(f"🟡 **Medium Risk**")
    with col3:
        st.markdown(f"🟠 **High Risk**")
    with col4:
        st.markdown(f"🔴 **Critical Risk**")
    with col5:
        st.markdown(f"⚪ **N/A**")
    
    # Export options
    st.markdown("---")
    st.markdown("### 💾 Export")
    csv = heatmap_data.to_csv(index=True)
    st.download_button(
        label="📥 Download Heatmap Data (CSV)",
        data=csv,
        file_name=f"governance_heatmap_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )


def _render_plotly_heatmap(heatmap_data: pd.DataFrame, colors: Dict[str, str]) -> None:
    """Render interactive Plotly heatmap."""
    # Convert categorical levels to numeric for heatmap
    level_map = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4, "N/A": 0}
    numeric_data = heatmap_data.replace(level_map)
    
    fig = go.Figure(data=go.Heatmap(
        z=numeric_data.values,
        x=heatmap_data.columns,
        y=heatmap_data.index,
        colorscale=[[0, colors["na"]], 
                    [0.2, colors["low"]], 
                    [0.5, colors["medium"]], 
                    [0.75, colors["high"]], 
                    [1.0, colors["critical"]]],
        text=heatmap_data.values,
        texttemplate="%{text}",
        textfont={"size": 10},
        hoverongaps=False,
        showscale=True,
        colorbar=dict(
            title="Risk Level",
            tickvals=[0, 1, 2, 3, 4],
            ticktext=["N/A", "Low", "Medium", "High", "Critical"]
        )
    ))
    
    fig.update_layout(
        title="Pre-Inspection Risk & Compliance Heatmap",
        xaxis_title="Risk/Compliance Dimensions",
        yaxis_title="Governed Items",
        height=max(400, len(heatmap_data) * 30 + 150),
        template="plotly_white"
    )
    
    st.plotly_chart(fig, use_container_width=True)


def _render_html_heatmap(heatmap_data: pd.DataFrame, colors: Dict[str, str]) -> None:
    """Render HTML table heatmap (fallback)."""
    # Create colored HTML table
    html = """
    <style>
        .heatmap-table {
            border-collapse: collapse;
            width: 100%;
            font-size: 0.85rem;
            overflow-x: auto;
        }
        .heatmap-table th {
            background-color: #1f2937;
            color: white;
            padding: 8px;
            border: 1px solid #374151;
            text-align: center;
            font-weight: 600;
            position: sticky;
            top: 0;
            z-index: 10;
        }
        .heatmap-table td {
            padding: 8px;
            border: 1px solid #d1d5db;
            text-align: center;
            font-size: 0.8rem;
        }
        .heatmap-table tr:hover {
            background-color: #f9fafb;
        }
    </style>
    <div style="overflow-x: auto; max-height: 600px; overflow-y: auto;">
    <table class="heatmap-table">
    """
    
    # Header row
    html += "<thead><tr>"
    html += "<th style='position: sticky; left: 0; z-index: 11; background-color: #1f2937;'>Item</th>"
    for col in heatmap_data.columns:
        html += f"<th>{col}</th>"
    html += "</tr></thead><tbody>"
    
    # Data rows
    for idx, row in heatmap_data.iterrows():
        html += "<tr>"
        html += f"<td style='position: sticky; left: 0; z-index: 10; background-color: white; font-weight: bold;'>{idx}</td>"
        for col in heatmap_data.columns:
            cell = str(row[col])
            # Determine color based on cell value
            if "low" in cell.lower() or cell == "1":
                cell_color = colors["low"]
            elif "medium" in cell.lower() or cell == "2":
                cell_color = colors["medium"]
            elif "high" in cell.lower() or cell == "3":
                cell_color = colors["high"]
            elif "critical" in cell.lower() or cell == "4":
                cell_color = colors["critical"]
            else:
                cell_color = colors["na"]
            
            html += f"""
                <td style="background-color: {cell_color}; color: {'#ffffff' if cell_color in [colors['high'], colors['critical']] else '#000000'};">
                {cell}
                </td>
            """
        html += "</tr>"
    
    html += "</tbody></table></div>"
    
    st.markdown(html, unsafe_allow_html=True)


def build_heatmap_schema(
    signals: Optional[List[Dict[str, Any]]] = None,
    trend_alerts: Optional[Dict[str, Any]] = None,
    governance_data: Optional[Dict[str, Any]] = None
) -> Optional[pd.DataFrame]:
    """
    Build heatmap DataFrame using heatmap_builder (CHUNK A2).
    """
    try:
        from src.ai.heatmap_builder import build_heatmap_levels
    except ImportError:
        # Fallback to old implementation
        return _build_heatmap_schema_legacy(signals, trend_alerts, governance_data)
    
    if not signals:
        return None
    
    # Build heatmap for each signal
    heatmap_rows = []
    
    for signal in signals[:20]:  # Limit to top 20 for performance
        drug = signal.get("drug", "Unknown")
        reaction = signal.get("reaction", signal.get("event", "Unknown"))
        signal_name = f"{drug} - {reaction}"
        
        # Extract trend alerts for this signal
        signal_trends = []
        if trend_alerts and isinstance(trend_alerts, dict):
            all_alerts = trend_alerts.get("alerts", [])
            for alert in all_alerts:
                if isinstance(alert, dict):
                    alert_drug = alert.get("drug", "")
                    alert_reaction = alert.get("reaction", "")
                    if (drug.lower() in str(alert_drug).lower() or 
                        str(alert_drug).lower() in drug.lower() or
                        reaction.lower() in str(alert_reaction).lower() or
                        str(alert_reaction).lower() in reaction.lower()):
                        signal_trends.append(alert)
        
        # Build levels for this signal
        levels_df = build_heatmap_levels(
            trend_alerts=signal_trends,
            rpf_scores=signal,
            confidence_scores=signal.get("confidence_score", {}),
            label_impact_scores=signal.get("label_impact", {}),
            subgroup_scores=signal.get("subgroups", {}),
            shmi_score=governance_data.get("shmi", {}) if governance_data else {},
            governance_gaps=governance_data.get("governance_findings", {}) if governance_data else {},
            timing_deviations=signal.get("timeline_status", {}),
            lifecycle_stage=signal.get("lifecycle", signal.get("qsp_priority", "Unknown")),
            capa_findings=signal.get("capa", {}),
            signal_name=signal_name
        )
        
        heatmap_rows.append(levels_df)
    
    if heatmap_rows:
        return pd.concat(heatmap_rows, ignore_index=False)
    
    return None


def _build_heatmap_schema_legacy(
    signals: Optional[List[Dict[str, Any]]] = None,
    trend_alerts: Optional[Dict[str, Any]] = None,
    governance_data: Optional[Dict[str, Any]] = None
) -> Optional[pd.DataFrame]:
    """
    Build heatmap DataFrame from existing analytics engines (Stage 1 - Option 1).
    
    This function uses ONLY existing engines:
    - Trend Alerts
    - RPF
    - Confidence Score
    - Label Impact
    - Subgroup Analysis
    - SHMI
    - Governance gaps
    - Lifecycle stage
    
    Args:
        signals: List of signal dictionaries
        trend_alerts: Trend alerts data
        governance_data: Governance package data
        
    Returns:
        DataFrame with rows = governed items, columns = risk dimensions
    """
    if not signals and not trend_alerts:
        return None
    
    # Initialize lists for rows and data
    row_labels = []
    trend_levels = []
    rpf_levels = []
    confidence_levels = []
    label_impact_levels = []
    subgroup_levels = []
    shmi_levels = []
    governance_levels = []
    timing_levels = []
    lifecycle_levels = []
    capa_levels = []
    
    # Process signals
    if signals:
        for signal in signals[:20]:  # Limit to top 20 for performance
            drug = signal.get("drug", "Unknown")
            reaction = signal.get("reaction", signal.get("event", "Unknown"))
            row_label = f"{drug} - {reaction}"
            row_labels.append(row_label)
            
            # Trend Severity
            trend_severity = signal.get("trend_severity", signal.get("severity", "N/A"))
            trend_levels.append(_normalize_level(trend_severity))
            
            # RPF Priority
            rpf_score = signal.get("qsp_score", signal.get("rpf_score", 0))
            if rpf_score >= 70:
                rpf_levels.append("High")
            elif rpf_score >= 40:
                rpf_levels.append("Medium")
            else:
                rpf_levels.append("Low")
            
            # Confidence Score
            confidence = signal.get("confidence_score", signal.get("signal_confidence", 0))
            if confidence >= 0.8:
                confidence_levels.append("High")
            elif confidence >= 0.5:
                confidence_levels.append("Medium")
            else:
                confidence_levels.append("Low")
            
            # Label Impact
            label_impact = signal.get("label_impact", "N/A")
            label_impact_levels.append(_normalize_level(label_impact))
            
            # Subgroup Risk
            subgroups = signal.get("subgroups", {})
            if subgroups and isinstance(subgroups, dict) and len(subgroups) > 0:
                subgroup_levels.append("Medium")  # Placeholder
            else:
                subgroup_levels.append("N/A")
            
            # SHMI
            shmi = signal.get("shmi_score", governance_data.get("shmi_score", 0) if governance_data else 0)
            if shmi >= 80:
                shmi_levels.append("High")
            elif shmi >= 60:
                shmi_levels.append("Medium")
            else:
                shmi_levels.append("Low")
            
            # Governance Completeness
            gov_score = signal.get("governance_score", 100)
            if gov_score >= 80:
                governance_levels.append("High")
            elif gov_score >= 60:
                governance_levels.append("Medium")
            else:
                governance_levels.append("Low")
            
            # Timing Compliance
            timeline_status = signal.get("timeline_status", {})
            if isinstance(timeline_status, dict):
                assessment_status = timeline_status.get("assessment_status", "On Time")
                if assessment_status == "On Time":
                    timing_levels.append("Low")
                elif "Delay" in assessment_status:
                    timing_levels.append("High")
                else:
                    timing_levels.append("Medium")
            else:
                timing_levels.append("N/A")
            
            # Lifecycle Stage
            lifecycle = signal.get("lifecycle", signal.get("qsp_priority", "Unknown"))
            if lifecycle in ["High", "Critical", "Validated Signal"]:
                lifecycle_levels.append("High")
            elif lifecycle in ["Medium", "Emerging Signal"]:
                lifecycle_levels.append("Medium")
            else:
                lifecycle_levels.append("Low")
            
            # CAPA Requirement
            capa_needed = signal.get("capa_required", False)
            if capa_needed:
                capa_levels.append("High")
            else:
                capa_levels.append("Low")
    
    # Add trend alerts as rows if available
    if trend_alerts and trend_alerts.get("alerts"):
        alerts = trend_alerts.get("alerts", [])
        for alert in alerts[:10]:  # Limit to top 10
            title = alert.get("title", "Unknown Alert")
            if isinstance(title, dict):
                title = title.get("title", "Unknown")
            row_labels.append(f"Trend: {title}")
            
            severity = alert.get("severity", "info")
            trend_levels.append(_severity_to_level(severity))
            rpf_levels.append("N/A")
            confidence_levels.append("N/A")
            label_impact_levels.append("N/A")
            subgroup_levels.append("N/A")
            shmi_levels.append("N/A")
            governance_levels.append("Medium")
            timing_levels.append("N/A")
            lifecycle_levels.append("N/A")
            capa_levels.append("Medium" if severity in ["warning", "critical"] else "Low")
    
    # Create DataFrame
    if not row_labels:
        return None
    
    heatmap_df = pd.DataFrame({
        "Trend Severity": trend_levels[:len(row_labels)],
        "RPF Priority": rpf_levels[:len(row_labels)],
        "Confidence Score": confidence_levels[:len(row_labels)],
        "Label Impact": label_impact_levels[:len(row_labels)],
        "Subgroup Risk": subgroup_levels[:len(row_labels)],
        "SHMI Maturity": shmi_levels[:len(row_labels)],
        "Governance Completeness": governance_levels[:len(row_labels)],
        "Timing Compliance": timing_levels[:len(row_labels)],
        "Lifecycle Stage": lifecycle_levels[:len(row_labels)],
        "CAPA Requirement": capa_levels[:len(row_labels)],
    }, index=row_labels[:len(trend_levels)])
    
    return heatmap_df


def _normalize_level(value: Any) -> str:
    """Normalize risk/compliance level to standard values."""
    if value is None:
        return "N/A"
    
    value_str = str(value).lower()
    if value_str in ["low", "1", "green", "pass", "on time"]:
        return "Low"
    elif value_str in ["medium", "2", "yellow", "warning", "moderate"]:
        return "Medium"
    elif value_str in ["high", "3", "red", "critical", "severe"]:
        return "High"
    elif value_str in ["critical", "4", "urgent", "severe delay"]:
        return "Critical"
    else:
        return "N/A"


def _severity_to_level(severity: str) -> str:
    """Convert alert severity to heatmap level."""
    severity_lower = str(severity).lower()
    if severity_lower in ["critical", "error", "fatal"]:
        return "Critical"
    elif severity_lower in ["warning", "high"]:
        return "High"
    elif severity_lower in ["info", "medium"]:
        return "Medium"
    else:
        return "Low"

