"""
Hybrid Trend Alerts Fusion Engine (CHUNK 7.4.4)
Combines local numeric anomaly detection with AI narrative interpretation and regulatory significance.
Local compute (fast) + Server AI (intelligent) = Enterprise-grade trend intelligence.
"""
from typing import Dict, List, Any, Optional
import json
import pandas as pd
from datetime import datetime

try:
    from src.ai.medical_llm import call_medical_llm
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

try:
    from src.ai.trend_alerts import detect_trend_alerts_light
    TREND_ALERTS_AVAILABLE = True
except ImportError:
    TREND_ALERTS_AVAILABLE = False

try:
    from src.ai.risk_prioritization import RiskPrioritizationEngine
    RPF_AVAILABLE = True
except ImportError:
    RPF_AVAILABLE = False

try:
    from src.ai.hybrid_subgroup_engine import compute_local_subgroups
    SUBGROUP_AVAILABLE = True
except ImportError:
    SUBGROUP_AVAILABLE = False


def compute_local_trend_signals(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute numeric trend signals entirely locally (fast, no LLM).
    
    This runs in Pyodide/browser for speed.
    
    Args:
        df: Safety data DataFrame
        
    Returns:
        Dictionary with local trend signals
    """
    if df is None or df.empty:
        return {}
    
    signals = {}
    
    # Find date column
    date_col = next(
        (col for col in ["event_date", "event_dt", "report_date", "date", "received_date"]
         if col in df.columns),
        None
    )
    
    if not date_col:
        return signals
    
    try:
        df_date = df.copy()
        df_date["date_parsed"] = pd.to_datetime(df_date[date_col], errors="coerce")
        df_date = df_date.dropna(subset=["date_parsed"])
        df_date["year_month"] = df_date["date_parsed"].dt.to_period("M")
        
        # Monthly case counts
        monthly_counts = df_date.groupby("year_month").size().reset_index(name="count")
        monthly_counts["year_month_str"] = monthly_counts["year_month"].astype(str)
        
        if len(monthly_counts) >= 3:
            # Calculate trend slope (simple linear regression)
            x = list(range(len(monthly_counts)))
            y = monthly_counts["count"].values
            
            # Simple slope calculation
            n = len(x)
            slope = (n * sum(x[i] * y[i] for i in range(n)) - sum(x) * sum(y)) / (n * sum(x[i]**2 for i in range(n)) - sum(x)**2) if n > 1 else 0
            
            signals["portfolio_volume_trend"] = {
                "slope": float(slope),
                "trend": "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable",
                "monthly_counts": monthly_counts[["year_month_str", "count"]].to_dict("records")
            }
            
            # Detect spikes (months with >2x average)
            avg_count = monthly_counts["count"].mean()
            spikes = monthly_counts[monthly_counts["count"] > (avg_count * 2)]
            signals["volume_spikes"] = spikes.to_dict("records") if not spikes.empty else []
        
        # Drug-level trends
        drug_col = next((col for col in ["drug_normalized", "drug_name", "drug"] if col in df.columns), None)
        if drug_col:
            drug_trends = []
            for drug in df[drug_col].unique()[:20]:  # Limit to top 20 drugs
                drug_df = df_date[df_date[drug_col] == drug]
                drug_monthly = drug_df.groupby("year_month").size().reset_index(name="count")
                
                if len(drug_monthly) >= 3:
                    x = list(range(len(drug_monthly)))
                    y = drug_monthly["count"].values
                    n = len(x)
                    slope = (n * sum(x[i] * y[i] for i in range(n)) - sum(x) * sum(y)) / (n * sum(x[i]**2 for i in range(n)) - sum(x)**2) if n > 1 else 0
                    
                    if abs(slope) > 1:  # Significant trend
                        drug_trends.append({
                            "drug": drug,
                            "trend_slope": float(slope),
                            "trend": "increasing" if slope > 0 else "decreasing",
                            "latest_month_count": int(drug_monthly["count"].iloc[-1]) if not drug_monthly.empty else 0
                        })
            
            signals["drug_trends"] = sorted(drug_trends, key=lambda x: abs(x["trend_slope"]), reverse=True)[:10]
        
        # Reaction-level trends
        reaction_col = next((col for col in ["reaction_normalized", "reaction_pt", "reaction"] if col in df.columns), None)
        if reaction_col:
            reaction_trends = []
            reaction_counts = df_date[reaction_col].value_counts().head(20)  # Top 20 reactions
            
            for reaction in reaction_counts.index:
                reaction_df = df_date[df_date[reaction_col] == reaction]
                reaction_monthly = reaction_df.groupby("year_month").size().reset_index(name="count")
                
                if len(reaction_monthly) >= 3:
                    x = list(range(len(reaction_monthly)))
                    y = reaction_monthly["count"].values
                    n = len(x)
                    slope = (n * sum(x[i] * y[i] for i in range(n)) - sum(x) * sum(y)) / (n * sum(x[i]**2 for i in range(n)) - sum(x)**2) if n > 1 else 0
                    
                    if abs(slope) > 0.5:
                        reaction_trends.append({
                            "reaction": reaction,
                            "trend_slope": float(slope),
                            "trend": "increasing" if slope > 0 else "decreasing",
                            "total_cases": int(reaction_counts[reaction])
                        })
            
            signals["reaction_trends"] = sorted(reaction_trends, key=lambda x: abs(x["trend_slope"]), reverse=True)[:10]
        
    except Exception:
        pass
    
    return signals


def fuse_trend_intelligence(
    local_alerts: Optional[Dict[str, Any]] = None,
    rpf_scores: Optional[List[Dict[str, Any]]] = None,
    subgroup_risks: Optional[Dict[str, Any]] = None,
    trend_alerts: Optional[List[Dict[str, Any]]] = None,
    signal_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Fuse local numeric signals with AI narrative interpretation and regulatory significance.
    
    Combines:
    - Local numeric anomaly detection
    - RPF risk scores
    - Subgroup risk patterns
    - Trend alerts
    - AI-powered clinical interpretation
    - Regulatory impact assessment
    
    Args:
        local_alerts: Local trend signals from compute_local_trend_signals()
        rpf_scores: Risk Prioritization Framework scores
        subgroup_risks: Subgroup analysis results
        trend_alerts: Trend alerts from trend_alerts engine
        signal_data: Signal-specific data
        
    Returns:
        Dictionary with fused trend intelligence including AI interpretation
    """
    # Prepare local summary (no raw data, just key metrics)
    local_summary = {
        "portfolio_trend": local_alerts.get("portfolio_volume_trend", {}) if local_alerts else {},
        "volume_spikes": local_alerts.get("volume_spikes", []) if local_alerts else [],
        "top_drug_trends": local_alerts.get("drug_trends", [])[:5] if local_alerts else [],
        "top_reaction_trends": local_alerts.get("reaction_trends", [])[:5] if local_alerts else [],
        "rpf_summary": {
            "high_risk_signals": len([s for s in (rpf_scores or []) if isinstance(s, dict) and s.get("rpf_score", 0) >= 70]),
            "top_rpf": [s for s in (rpf_scores or []) if isinstance(s, dict)][:3]
        },
        "subgroup_highlights": {
            "geriatric_risk": len(subgroup_risks.get("geriatric_signals", [])) if subgroup_risks else 0,
            "pediatric_risk": len(subgroup_risks.get("pediatric_signals", [])) if subgroup_risks else 0,
            "sex_differentials": subgroup_risks.get("sex_risk_ratios", [])[:3] if subgroup_risks else []
        },
        "trend_alerts_count": len(trend_alerts) if trend_alerts else 0,
        "critical_trend_alerts": [
            a for a in (trend_alerts or [])
            if isinstance(a, dict) and a.get("severity") in ["critical", "high"]
        ][:5]
    }
    
    # Generate AI interpretation
    ai_interpretation = None
    if LLM_AVAILABLE:
        prompt = f"""
        You are a senior pharmacovigilance safety scientist analyzing trend intelligence.
        
        Local Trend Signals:
        {json.dumps(local_summary, indent=2, default=str)}
        
        Signal Context:
        {json.dumps(signal_data or {}, indent=2, default=str)}
        
        Provide a comprehensive, regulator-ready analysis covering:
        
        1. **High-Risk Trends**: Identify the most significant upward trends requiring immediate attention
        
        2. **Newly Emerging Risks**: Highlight any newly detected patterns or accelerations
        
        3. **Subgroup-Specific Accelerations**: Analyze if any population subgroups show elevated risk trends
        
        4. **Regulatory Considerations**: 
           - Should any of these trends trigger a formal signal?
           - Regulatory reporting requirements
           - Potential label impact
        
        5. **Label Impact Potential**: Assess if trends indicate need for labeling updates
        
        6. **Clinical Significance**: Explain the clinical relevance of detected trends
        
        7. **Recommendations**: 
           - Immediate actions required
           - Monitoring recommendations
           - Additional analyses needed
        
        Maintain professional, evidence-based tone suitable for regulatory documentation.
        """
        
        system_prompt = "You are a senior pharmacovigilance safety scientist specializing in trend analysis and signal detection."
        
        try:
            ai_interpretation = call_medical_llm(
                prompt,
                system_prompt,
                task_type="general",
                max_tokens=2000,
                temperature=0.3
            )
        except Exception:
            pass
    
    if not ai_interpretation:
        ai_interpretation = _generate_fallback_interpretation(local_summary)
    
    # Compile fused intelligence
    fused_intelligence = {
        "local_signals": local_summary,
        "ai_interpretation": ai_interpretation,
        "risk_assessment": _assess_combined_risk(local_summary, rpf_scores, subgroup_risks),
        "regulatory_priority": _determine_regulatory_priority(local_summary, rpf_scores),
        "recommended_actions": _generate_hybrid_recommendations(local_summary, ai_interpretation),
        "timestamp": datetime.now().isoformat()
    }
    
    return fused_intelligence


def _generate_fallback_interpretation(local_summary: Dict[str, Any]) -> str:
    """Generate fallback interpretation if LLM unavailable."""
    interpretation = "Trend Intelligence Summary:\n\n"
    
    portfolio_trend = local_summary.get("portfolio_volume_trend", {})
    if portfolio_trend:
        trend = portfolio_trend.get("trend", "stable")
        interpretation += f"Portfolio Volume Trend: {trend.title()}\n"
    
    top_drug_trends = local_summary.get("top_drug_trends", [])
    if top_drug_trends:
        interpretation += "\nTop Drug Trends:\n"
        for trend in top_drug_trends[:5]:
            interpretation += f"- {trend.get('drug', 'Unknown')}: {trend.get('trend', 'stable')} trend\n"
    
    critical_alerts = local_summary.get("critical_trend_alerts", [])
    if critical_alerts:
        interpretation += f"\nCritical Trend Alerts: {len(critical_alerts)} alerts detected\n"
    
    return interpretation


def _assess_combined_risk(
    local_summary: Dict[str, Any],
    rpf_scores: Optional[List[Dict]],
    subgroup_risks: Optional[Dict]
) -> Dict[str, Any]:
    """Assess combined risk level from all sources."""
    risk_level = "Low"
    risk_score = 0
    
    # Portfolio trend risk
    portfolio_trend = local_summary.get("portfolio_volume_trend", {})
    if portfolio_trend.get("trend") == "increasing":
        risk_score += 20
    
    # Critical alerts
    critical_count = len(local_summary.get("critical_trend_alerts", []))
    risk_score += critical_count * 15
    
    # High RPF signals
    high_rpf_count = local_summary.get("rpf_summary", {}).get("high_risk_signals", 0)
    risk_score += high_rpf_count * 10
    
    # Subgroup risks
    geriatric = local_summary.get("subgroup_highlights", {}).get("geriatric_risk", 0)
    pediatric = local_summary.get("subgroup_highlights", {}).get("pediatric_risk", 0)
    risk_score += (geriatric + pediatric) * 5
    
    # Determine risk level
    if risk_score >= 60:
        risk_level = "High"
    elif risk_score >= 30:
        risk_level = "Medium"
    else:
        risk_level = "Low"
    
    return {
        "overall_risk_level": risk_level,
        "risk_score": min(100, risk_score),
        "contributing_factors": {
            "portfolio_trend": portfolio_trend.get("trend", "stable"),
            "critical_alerts": critical_count,
            "high_rpf_signals": high_rpf_count,
            "subgroup_risks": geriatric + pediatric
        }
    }


def _determine_regulatory_priority(
    local_summary: Dict[str, Any],
    rpf_scores: Optional[List[Dict]]
) -> str:
    """Determine regulatory priority level."""
    critical_alerts = len(local_summary.get("critical_trend_alerts", []))
    high_rpf = local_summary.get("rpf_summary", {}).get("high_risk_signals", 0)
    
    if critical_alerts >= 3 or high_rpf >= 5:
        return "Immediate Regulatory Action Required"
    elif critical_alerts >= 1 or high_rpf >= 2:
        return "High Priority - Regulatory Review Recommended"
    elif local_summary.get("trend_alerts_count", 0) > 5:
        return "Medium Priority - Enhanced Monitoring Recommended"
    else:
        return "Standard Monitoring"


def _generate_hybrid_recommendations(
    local_summary: Dict[str, Any],
    ai_interpretation: Optional[str]
) -> List[str]:
    """Generate actionable recommendations from hybrid analysis."""
    recommendations = []
    
    critical_alerts = len(local_summary.get("critical_trend_alerts", []))
    if critical_alerts > 0:
        recommendations.append(f"Immediate review of {critical_alerts} critical trend alert(s)")
    
    high_rpf = local_summary.get("rpf_summary", {}).get("high_risk_signals", 0)
    if high_rpf > 0:
        recommendations.append(f"Prioritize {high_rpf} high-RPF signal(s) for assessment")
    
    portfolio_trend = local_summary.get("portfolio_volume_trend", {})
    if portfolio_trend.get("trend") == "increasing":
        recommendations.append("Investigate portfolio-wide volume increase - potential class effect")
    
    if local_summary.get("subgroup_highlights", {}).get("geriatric_risk", 0) > 0:
        recommendations.append("Enhanced monitoring recommended for geriatric population")
    
    if local_summary.get("subgroup_highlights", {}).get("pediatric_risk", 0) > 0:
        recommendations.append("Enhanced monitoring recommended for pediatric population")
    
    if not recommendations:
        recommendations.append("Continue standard monitoring - no immediate actions required")
    
    return recommendations
