"""
Hybrid RPF Fusion Engine (CHUNK 7.4.5)
Combines local quantitative RPF scoring with AI interpretive reasoning and cross-signal prioritization.
Local compute (fast) + Server AI (intelligent) = Enterprise-grade risk prioritization.
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
    from src.ai.risk_prioritization import RiskPrioritizationEngine
    RPF_AVAILABLE = True
except ImportError:
    RPF_AVAILABLE = False

try:
    from src.ai.trend_alerts import detect_trend_alerts_light
    TREND_ALERTS_AVAILABLE = True
except ImportError:
    TREND_ALERTS_AVAILABLE = False

try:
    from src.ai.hybrid_trend_fusion import compute_local_trend_signals
    TREND_FUSION_AVAILABLE = True
except ImportError:
    TREND_FUSION_AVAILABLE = False

try:
    from src.ai.hybrid_subgroup_engine import compute_local_subgroups
    SUBGROUP_AVAILABLE = True
except ImportError:
    SUBGROUP_AVAILABLE = False


def compute_local_rpf(
    drug_trend: Optional[Dict[str, Any]] = None,
    reaction_trend: Optional[Dict[str, Any]] = None,
    alerts: Optional[Dict[str, Any]] = None,
    case_count: int = 0,
    serious_count: int = 0,
    disproportionality_score: float = 0.0
) -> Dict[str, Any]:
    """
    Compute local numeric RPF score (fast, no LLM).
    
    Runs entirely locally (e.g., in Pyodide) for speed.
    
    Args:
        drug_trend: Drug-level trend data with slope, direction, etc.
        reaction_trend: Reaction-level trend data
        alerts: Trend alerts dictionary
        case_count: Total case count
        serious_count: Serious case count
        disproportionality_score: Disproportionality metric (ROR, PRR, etc.)
        
    Returns:
        Dictionary with local RPF score and components
    """
    score = 0.0
    components = {}
    
    # Disproportionality component (30% weight)
    if disproportionality_score > 0:
        disproportionality_component = min(disproportionality_score / 10.0 * 30, 30)
        score += disproportionality_component
        components["disproportionality"] = round(disproportionality_component, 1)
    
    # Trend component (20% weight)
    if drug_trend:
        trend_slope = abs(drug_trend.get("slope", 0))
        trend_component = min(trend_slope * 4, 20)
        score += trend_component
        components["drug_trend"] = round(trend_component, 1)
    
    if reaction_trend:
        reaction_slope = abs(reaction_trend.get("slope", 0))
        reaction_trend_component = min(reaction_slope * 4, 20)
        score += reaction_trend_component
        components["reaction_trend"] = round(reaction_trend_component, 1)
    else:
        # Use drug trend for reaction if not available (combined trend score)
        if drug_trend:
            trend_component = components.get("drug_trend", 0)
            score += trend_component * 0.5  # Half weight for reaction
    
    # Seriousness component (25% weight)
    seriousness_ratio = (serious_count / case_count) if case_count > 0 else 0
    seriousness_component = seriousness_ratio * 25
    score += seriousness_component
    components["seriousness"] = round(seriousness_component, 1)
    
    # Alert component (15% weight)
    if alerts:
        high_risk_alerts = alerts.get("high_risk", False)
        critical_alerts = alerts.get("critical", False)
        if critical_alerts:
            alert_component = 15
        elif high_risk_alerts:
            alert_component = 10
        else:
            alert_component = 5
        score += alert_component
        components["alerts"] = round(alert_component, 1)
    
    # Case count component (10% weight)
    if case_count > 100:
        case_component = 10
    elif case_count > 50:
        case_component = 7
    elif case_count > 20:
        case_component = 5
    else:
        case_component = min(case_count / 4, 3)
    score += case_component
    components["case_count"] = round(case_component, 1)
    
    # Ensure score is 0-100
    final_score = min(100, max(0, score))
    
    # Determine priority level
    if final_score >= 70:
        priority = "High"
    elif final_score >= 50:
        priority = "Medium"
    else:
        priority = "Low"
    
    return {
        "local_rpf_score": round(final_score, 1),
        "priority": priority,
        "components": components,
        "computation_method": "local_numeric"
    }


def compute_local_rpf_from_df(
    df: pd.DataFrame,
    drug: str,
    reaction: str
) -> Dict[str, Any]:
    """
    Compute local RPF from DataFrame (convenience function).
    
    Args:
        df: Safety data DataFrame
        drug: Drug name
        reaction: Reaction name
        
    Returns:
        Local RPF score dictionary
    """
    # Filter to drug-reaction combination
    drug_col = next((col for col in ["drug_normalized", "drug_name", "drug"] if col in df.columns), None)
    reaction_col = next((col for col in ["reaction_normalized", "reaction_pt", "reaction"] if col in df.columns), None)
    
    if not drug_col or not reaction_col:
        return {"local_rpf_score": 0, "priority": "Low", "components": {}, "error": "Missing required columns"}
    
    signal_df = df[(df[drug_col] == drug) & (df[reaction_col] == reaction)]
    
    if signal_df.empty:
        return {"local_rpf_score": 0, "priority": "Low", "components": {}, "error": "No cases found"}
    
    # Get case counts
    case_count = len(signal_df)
    serious_count = 0
    serious_col = next((col for col in ["serious", "seriousness", "serious_flag"] if col in signal_df.columns), None)
    if serious_col:
        serious_mask = signal_df[serious_col].astype(str).str.lower().isin(["1", "yes", "y", "true", "serious"])
        serious_count = serious_mask.sum()
    
    # Compute trends
    drug_trend = None
    reaction_trend = None
    
    if TREND_FUSION_AVAILABLE:
        try:
            trend_signals = compute_local_trend_signals(signal_df)
            drug_trends = trend_signals.get("drug_trends", [])
            reaction_trends = trend_signals.get("reaction_trends", [])
            
            drug_trend = next((t for t in drug_trends if t.get("drug") == drug), None)
            reaction_trend = next((t for t in reaction_trends if t.get("reaction") == reaction), None)
        except Exception:
            pass
    
    # Compute local RPF
    return compute_local_rpf(
        drug_trend=drug_trend,
        reaction_trend=reaction_trend,
        alerts={"high_risk": case_count > 50, "critical": serious_count > 10},
        case_count=case_count,
        serious_count=serious_count,
        disproportionality_score=0.0  # Would need to compute ROR/PRR
    )


def fuse_rpf(
    local_scores: Dict[str, Any],
    ai_context: Optional[Dict[str, Any]] = None,
    cross_signals: Optional[List[Dict[str, Any]]] = None,
    signal_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Fuse local RPF scores with AI-driven narrative reasoning and cross-signal analysis.
    
    Combines:
    - Local quantitative RPF (fast, numeric)
    - AI interpretive RPF (clinical, regulatory context)
    - Cross-signal weighted RPF (portfolio context)
    - Regulatory-impact-weighted RPF
    - Subgroup amplification weighting
    
    Args:
        local_scores: Local RPF score dictionary from compute_local_rpf()
        ai_context: Clinical and regulatory context (optional)
        cross_signals: Related signals across portfolio (optional)
        signal_data: Signal-specific data (drug, reaction, cases, etc.)
        
    Returns:
        Fused RPF dictionary with local + AI interpretation + regulatory recommendations
    """
    local_score = local_scores.get("local_rpf_score", 50)
    local_priority = local_scores.get("priority", "Medium")
    
    # Prepare summary for AI
    fusion_summary = {
        "local_rpf_score": local_score,
        "local_priority": local_priority,
        "local_components": local_scores.get("components", {}),
        "signal_context": signal_data or {},
        "cross_signals_count": len(cross_signals) if cross_signals else 0,
        "cross_signals_summary": [
            {
                "drug": s.get("drug", "Unknown"),
                "reaction": s.get("reaction", "Unknown"),
                "rpf": s.get("rpf_score", s.get("local_rpf_score", 0)),
                "priority": s.get("priority", "Unknown")
            }
            for s in (cross_signals or [])[:5]  # Top 5 related signals
        ] if cross_signals else [],
        "ai_context_available": ai_context is not None
    }
    
    # Generate AI interpretation
    ai_interpretation = None
    ai_regulatory_priority = None
    ai_confidence = None
    
    if LLM_AVAILABLE:
        prompt = f"""
        You are a senior pharmacovigilance risk assessment expert analyzing a safety signal.
        
        Local RPF Analysis:
        {json.dumps(fusion_summary, indent=2, default=str)}
        
        Clinical/Regulatory Context:
        {json.dumps(ai_context or {}, indent=2, default=str)}
        
        Generate a comprehensive, regulator-ready RPF assessment including:
        
        1. **Clinical Seriousness Assessment**
           - Severity of the adverse reaction
           - Impact on patient safety
           - Frequency vs. exposure analysis
        
        2. **Temporal Pattern Strength**
           - Trend acceleration/deceleration
           - Stability of signal over time
           - Time-to-detection assessment
        
        3. **Subgroup Amplification**
           - Population-specific risk elevations
           - Vulnerability patterns
           - Dose-response relationships
        
        4. **Regulatory Impact**
           - Label impact potential (Boxed Warning, Warnings & Precautions, Adverse Reactions)
           - Regulatory reporting requirements
           - Risk Management Plan implications
        
        5. **Signal Confidence Assessment**
           - Probability the signal represents a true safety risk (0-100%)
           - Evidence strength evaluation
           - Potential confounders or alternative explanations
        
        6. **Priority Ranking Justification**
           - Why this signal is High/Medium/Low priority
           - Comparison with portfolio signals
           - Resource allocation rationale
        
        7. **Cross-Signal Context**
           - How this signal relates to other portfolio signals
           - Class effect considerations
           - Cumulative risk assessment
        
        Provide clear, evidence-based reasoning suitable for regulatory documentation.
        """
        
        system_prompt = "You are a senior pharmacovigilance risk assessment expert with deep expertise in regulatory frameworks (FDA, EMA, ICH) and signal evaluation."
        
        try:
            ai_response = call_medical_llm(
                prompt,
                system_prompt,
                task_type="causal_reasoning",
                max_tokens=2000,
                temperature=0.3
            )
            
            ai_interpretation = ai_response
            
            # Extract priority and confidence from AI response (simple extraction)
            if "high priority" in ai_response.lower() or "high-priority" in ai_response.lower():
                ai_regulatory_priority = "High"
            elif "low priority" in ai_response.lower() or "low-priority" in ai_response.lower():
                ai_regulatory_priority = "Low"
            else:
                ai_regulatory_priority = local_priority  # Default to local
            
            # Extract confidence estimate (look for percentages)
            import re
            confidence_matches = re.findall(r'(\d+)%', ai_response)
            if confidence_matches:
                ai_confidence = min(100, max(0, int(confidence_matches[-1])))
            else:
                ai_confidence = None
                
        except Exception:
            pass
    
    # Combine local and AI priorities
    final_priority = local_priority
    if ai_regulatory_priority and ai_regulatory_priority != local_priority:
        # AI can upgrade/downgrade priority
        priority_hierarchy = {"Low": 1, "Medium": 2, "High": 3}
        if priority_hierarchy.get(ai_regulatory_priority, 2) > priority_hierarchy.get(local_priority, 2):
            final_priority = ai_regulatory_priority  # Upgrade if AI suggests higher priority
    
    # Cross-signal weighting (adjust score based on portfolio context)
    adjusted_score = local_score
    cross_signal_adjustment = 0
    
    if cross_signals:
        # If multiple related signals exist, increase priority
        related_signals_count = len([s for s in cross_signals if s.get("rpf_score", 0) >= 50])
        if related_signals_count >= 3:
            cross_signal_adjustment = +5  # Portfolio-wide concern
        elif related_signals_count >= 2:
            cross_signal_adjustment = +3
        
        adjusted_score = min(100, local_score + cross_signal_adjustment)
    
    # Build fused RPF result
    fused_rpf = {
        "local_rpf_score": local_score,
        "adjusted_rpf_score": round(adjusted_score, 1),
        "final_priority": final_priority,
        "local_priority": local_priority,
        "ai_priority": ai_regulatory_priority,
        "ai_confidence": ai_confidence,
        "components": local_scores.get("components", {}),
        "ai_interpretation": ai_interpretation or "AI interpretation not available.",
        "cross_signal_adjustment": cross_signal_adjustment,
        "cross_signals_context": {
            "related_signals_count": len(cross_signals) if cross_signals else 0,
            "portfolio_concern": len(cross_signals) >= 3 if cross_signals else False
        },
        "computation_timestamp": datetime.now().isoformat(),
        "fusion_method": "hybrid_local_ai_cross_signal"
    }
    
    return fused_rpf
