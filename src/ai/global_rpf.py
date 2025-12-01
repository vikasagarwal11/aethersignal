"""
Global Portfolio-Level RPF Fusion Engine (CHUNK 7.4.6)
Computes RPF for every signal in portfolio, normalizes scores, identifies cross-drug amplifiers,
and creates enterprise-level portfolio heatmaps and risk prioritization.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

try:
    from src.ai.hybrid_rpf_fusion import compute_local_rpf, compute_local_rpf_from_df, fuse_rpf
    HYBRID_RPF_AVAILABLE = True
except ImportError:
    HYBRID_RPF_AVAILABLE = False

try:
    from src.ai.risk_prioritization import RiskPrioritizationEngine
    RPF_AVAILABLE = True
except ImportError:
    RPF_AVAILABLE = False

try:
    from src.ai.medical_llm import call_medical_llm
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

try:
    from src.ai.portfolio_risk_propagation import compute_portfolio_risk_propagation
    PORTFOLIO_AVAILABLE = True
except ImportError:
    PORTFOLIO_AVAILABLE = False


def compute_portfolio_rpf(
    signals: List[Dict[str, Any]],
    df: Optional[Any] = None,
    include_ai_fusion: bool = True
) -> Dict[str, Any]:
    """
    Compute RPF for every signal in portfolio and create portfolio-level prioritization.
    
    Args:
        signals: List of signal dictionaries (each with drug, reaction, case data)
        df: Safety data DataFrame (optional, for extracting trends)
        include_ai_fusion: Whether to include AI-powered fusion (default: True)
        
    Returns:
        Dictionary with portfolio RPF results, normalized scores, cross-drug amplifiers, heatmap data
    """
    if not signals:
        return {
            "signals": [],
            "portfolio_summary": {},
            "heatmap_data": [],
            "cross_drug_amplifiers": [],
            "risk_of_missing": {}
        }
    
    portfolio_results = []
    
    # Compute RPF for each signal
    for i, signal in enumerate(signals):
        drug = signal.get("drug", signal.get("drug_name", "Unknown"))
        reaction = signal.get("reaction", signal.get("reaction_pt", signal.get("event", "Unknown")))
        
        # Extract signal-specific data
        drug_trend = signal.get("drug_trend", {})
        reaction_trend = signal.get("reaction_trend", {})
        alerts = signal.get("alerts", {})
        case_count = signal.get("case_count", signal.get("cases", signal.get("count", 0)))
        serious_count = signal.get("serious_count", signal.get("serious_cases", 0))
        disproportionality_score = signal.get("disproportionality_score", signal.get("ror", signal.get("prr", 0)))
        
        # Compute local RPF
        local_rpf = None
        if HYBRID_RPF_AVAILABLE:
            try:
                if df is not None:
                    local_rpf = compute_local_rpf_from_df(df, drug, reaction)
                else:
                    local_rpf = compute_local_rpf(
                        drug_trend=drug_trend,
                        reaction_trend=reaction_trend,
                        alerts=alerts,
                        case_count=case_count,
                        serious_count=serious_count,
                        disproportionality_score=disproportionality_score
                    )
            except Exception:
                pass
        
        if not local_rpf:
            # Fallback to basic RPF
            local_rpf = {
                "local_rpf_score": signal.get("rpf_score", 50),
                "priority": signal.get("priority", "Medium"),
                "components": {}
            }
        
        # AI fusion (optional)
        fused_rpf = local_rpf
        if include_ai_fusion and HYBRID_RPF_AVAILABLE:
            try:
                ai_context = signal.get("evidence_summary", signal.get("summary", {}))
                cross_signals = [s for s in signals if s.get("drug") != drug][:5]  # Top 5 other signals
                
                fused_rpf = fuse_rpf(
                    local_scores=local_rpf,
                    ai_context=ai_context,
                    cross_signals=cross_signals,
                    signal_data=signal
                )
            except Exception:
                pass
        
        # Build result entry
        result_entry = {
            "signal_id": signal.get("id", signal.get("signal_id", f"signal_{i}")),
            "drug": drug,
            "reaction": reaction,
            "local_rpf_score": local_rpf.get("local_rpf_score", 0),
            "fused_rpf_score": fused_rpf.get("adjusted_rpf_score", fused_rpf.get("local_rpf_score", 0)),
            "final_priority": fused_rpf.get("final_priority", local_rpf.get("priority", "Medium")),
            "case_count": case_count,
            "serious_count": serious_count,
            "components": local_rpf.get("components", {}),
            "ai_interpretation": fused_rpf.get("ai_interpretation", "") if isinstance(fused_rpf, dict) else "",
            "drug_class": signal.get("drug_class", "Unknown"),
            "reaction_soc": signal.get("reaction_soc", signal.get("soc", "Unknown"))
        }
        
        portfolio_results.append(result_entry)
    
    # Normalize RPF scores across portfolio
    normalized_results = _normalize_portfolio_rpf(portfolio_results)
    
    # Identify cross-drug amplifiers (class effects)
    cross_drug_amplifiers = _identify_cross_drug_amplifiers(normalized_results)
    
    # Compute risk of missing signal
    risk_of_missing = _compute_risk_of_missing(normalized_results)
    
    # Generate portfolio summary
    portfolio_summary = _generate_portfolio_summary(normalized_results, cross_drug_amplifiers)
    
    # Create heatmap data
    heatmap_data = _create_rpf_heatmap_data(normalized_results)
    
    return {
        "signals": normalized_results,
        "portfolio_summary": portfolio_summary,
        "heatmap_data": heatmap_data,
        "cross_drug_amplifiers": cross_drug_amplifiers,
        "risk_of_missing": risk_of_missing,
        "computation_timestamp": datetime.now().isoformat()
    }


def _normalize_portfolio_rpf(signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize RPF scores across portfolio for fair comparison."""
    if not signals:
        return signals
    
    # Extract scores
    scores = [s.get("fused_rpf_score", s.get("local_rpf_score", 0)) for s in signals]
    max_score = max(scores) if scores else 100
    min_score = min(scores) if scores else 0
    
    # Normalize to 0-100 scale if needed
    if max_score > 100 or min_score < 0:
        score_range = max_score - min_score
        for signal in signals:
            score = signal.get("fused_rpf_score", signal.get("local_rpf_score", 0))
            if score_range > 0:
                normalized = ((score - min_score) / score_range) * 100
            else:
                normalized = score
            signal["normalized_rpf_score"] = round(normalized, 1)
    else:
        # Already in 0-100 range
        for signal in signals:
            signal["normalized_rpf_score"] = signal.get("fused_rpf_score", signal.get("local_rpf_score", 0))
    
    # Rank signals by normalized score
    signals.sort(key=lambda x: x.get("normalized_rpf_score", 0), reverse=True)
    
    # Add rank
    for i, signal in enumerate(signals):
        signal["portfolio_rank"] = i + 1
    
    return signals


def _identify_cross_drug_amplifiers(signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Identify cross-drug amplifiers (class effects) across portfolio."""
    amplifiers = []
    
    # Group by drug class
    class_signals = {}
    for signal in signals:
        drug_class = signal.get("drug_class", "Unknown")
        if drug_class not in class_signals:
            class_signals[drug_class] = []
        class_signals[drug_class].append(signal)
    
    # Identify classes with multiple high-RPF signals
    for drug_class, class_signals_list in class_signals.items():
        if len(class_signals_list) >= 2:
            high_rpf_signals = [
                s for s in class_signals_list
                if s.get("normalized_rpf_score", 0) >= 60
            ]
            
            if len(high_rpf_signals) >= 2:
                # Class effect detected
                avg_rpf = sum(s.get("normalized_rpf_score", 0) for s in high_rpf_signals) / len(high_rpf_signals)
                
                amplifiers.append({
                    "drug_class": drug_class,
                    "signal_count": len(high_rpf_signals),
                    "avg_rpf_score": round(avg_rpf, 1),
                    "max_rpf_score": max(s.get("normalized_rpf_score", 0) for s in high_rpf_signals),
                    "signals": [
                        {
                            "drug": s.get("drug"),
                            "reaction": s.get("reaction"),
                            "rpf_score": s.get("normalized_rpf_score", 0)
                        }
                        for s in high_rpf_signals[:5]
                    ],
                    "risk_level": "High" if avg_rpf >= 70 else "Medium",
                    "description": f"Class effect detected in {drug_class} with {len(high_rpf_signals)} high-RPF signals"
                })
    
    return amplifiers


def _compute_risk_of_missing(signals: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute risk of missing important signals."""
    high_priority = [s for s in signals if s.get("final_priority") == "High"]
    medium_priority = [s for s in signals if s.get("final_priority") == "Medium"]
    low_priority = [s for s in signals if s.get("final_priority") == "Low"]
    
    high_rpf_but_low_priority = [
        s for s in signals
        if s.get("normalized_rpf_score", 0) >= 70 and s.get("final_priority") != "High"
    ]
    
    return {
        "high_priority_count": len(high_priority),
        "medium_priority_count": len(medium_priority),
        "low_priority_count": len(low_priority),
        "potential_missed_signals": len(high_rpf_but_low_priority),
        "missed_signals_list": [
            {
                "drug": s.get("drug"),
                "reaction": s.get("reaction"),
                "rpf_score": s.get("normalized_rpf_score", 0),
                "current_priority": s.get("final_priority")
            }
            for s in high_rpf_but_low_priority
        ],
        "risk_score": min(100, len(high_rpf_but_low_priority) * 20 + len(high_priority) * 5)
    }


def _generate_portfolio_summary(
    signals: List[Dict[str, Any]],
    cross_drug_amplifiers: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Generate portfolio-level summary."""
    total_signals = len(signals)
    
    if not signals:
        return {
            "total_signals": 0,
            "high_priority_count": 0,
            "medium_priority_count": 0,
            "low_priority_count": 0,
            "avg_rpf_score": 0,
            "class_effects_detected": 0
        }
    
    high_priority = len([s for s in signals if s.get("final_priority") == "High"])
    medium_priority = len([s for s in signals if s.get("final_priority") == "Medium"])
    low_priority = len([s for s in signals if s.get("final_priority") == "Low"])
    
    avg_rpf = sum(s.get("normalized_rpf_score", 0) for s in signals) / total_signals if total_signals > 0 else 0
    
    return {
        "total_signals": total_signals,
        "high_priority_count": high_priority,
        "medium_priority_count": medium_priority,
        "low_priority_count": low_priority,
        "avg_rpf_score": round(avg_rpf, 1),
        "max_rpf_score": max(s.get("normalized_rpf_score", 0) for s in signals) if signals else 0,
        "min_rpf_score": min(s.get("normalized_rpf_score", 0) for s in signals) if signals else 0,
        "class_effects_detected": len(cross_drug_amplifiers),
        "top_5_signals": [
            {
                "drug": s.get("drug"),
                "reaction": s.get("reaction"),
                "rpf_score": s.get("normalized_rpf_score", 0),
                "priority": s.get("final_priority")
            }
            for s in signals[:5]
        ]
    }


def _create_rpf_heatmap_data(signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Create heatmap data structure for portfolio visualization."""
    heatmap_data = []
    
    for signal in signals:
        rpf_score = signal.get("normalized_rpf_score", 0)
        priority = signal.get("final_priority", "Medium")
        
        # Determine heatmap color level
        if rpf_score >= 70:
            risk_level = "High"
            color_level = 3
        elif rpf_score >= 50:
            risk_level = "Medium"
            color_level = 2
        else:
            risk_level = "Low"
            color_level = 1
        
        heatmap_data.append({
            "drug": signal.get("drug", "Unknown"),
            "reaction": signal.get("reaction", "Unknown"),
            "drug_class": signal.get("drug_class", "Unknown"),
            "rpf_score": rpf_score,
            "priority": priority,
            "risk_level": risk_level,
            "color_level": color_level,
            "case_count": signal.get("case_count", 0),
            "serious_count": signal.get("serious_count", 0),
            "portfolio_rank": signal.get("portfolio_rank", 0)
        })
    
    return heatmap_data
