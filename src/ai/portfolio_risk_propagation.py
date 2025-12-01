"""
Portfolio Risk Propagation Engine (PART 9)
Computes portfolio-level risk propagation by drug class, reaction categories,
co-occurrence patterns, trend alerts, and cross-signal correlation.
"""
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime

try:
    from src.portfolio.portfolio_trends import PortfolioTrendEngine
    PORTFOLIO_TRENDS_AVAILABLE = True
except ImportError:
    PORTFOLIO_TRENDS_AVAILABLE = False

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


def infer_drug_class(drug_name: str) -> str:
    """
    Infer drug class from drug name (simplified - can be enhanced with drug database).
    """
    drug_lower = str(drug_name).lower()
    
    # Simple keyword-based classification
    if any(term in drug_lower for term in ["dupixent", "humira", "adalimumab", "etanercept", "infliximab", "remicade", "enbrel"]):
        return "Biologics - TNF-alpha inhibitors"
    elif any(term in drug_lower for term in ["keytruda", "opdivo", "yervoy", "pembrolizumab", "nivolumab", "ipilimumab"]):
        return "Oncology - Immune checkpoint inhibitors"
    elif any(term in drug_lower for term in ["metformin", "insulin", "glipizide", "semaglutide", "ozempic"]):
        return "Endocrinology - Antidiabetics"
    elif any(term in drug_lower for term in ["aspirin", "warfarin", "heparin", "clopidogrel"]):
        return "Cardiology - Anticoagulants"
    else:
        return "Other"


def compute_portfolio_risk_propagation(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes portfolio-level risk propagation by:
    - Drug class
    - Reaction categories
    - Co-occurrence patterns
    - Trend alerts
    - Cross-signal correlation
    
    Args:
        df: Normalized safety data DataFrame
        
    Returns:
        Dictionary with portfolio risk propagation results
    """
    if df is None or df.empty:
        return {
            "trends": {},
            "drug_classes": [],
            "reaction_clusters": [],
            "cross_signal_links": [],
            "portfolio_rpf": [],
            "class_effects": []
        }
    
    # Ensure required columns exist
    required_cols = []
    drug_col = None
    reaction_col = None
    case_col = None
    
    # Try to find drug column
    for col in ["drug_normalized", "drug_name", "drug", "drug_concept_name"]:
        if col in df.columns:
            drug_col = col
            required_cols.append(col)
            break
    
    # Try to find reaction column
    for col in ["reaction_normalized", "reaction_pt", "reaction", "pt"]:
        if col in df.columns:
            reaction_col = col
            required_cols.append(col)
            break
    
    # Try to find case ID column
    for col in ["primaryid", "caseid", "case_id", "id"]:
        if col in df.columns:
            case_col = col
            required_cols.append(col)
            break
    
    if not all([drug_col, reaction_col, case_col]):
        return {
            "trends": {},
            "drug_classes": [],
            "reaction_clusters": [],
            "cross_signal_links": [],
            "portfolio_rpf": [],
            "class_effects": []
        }
    
    # Step 1: Drug Class Inference
    df["drug_class"] = df[drug_col].apply(infer_drug_class)
    
    drug_classes = (
        df.groupby([drug_col, "drug_class"])[case_col]
        .count()
        .reset_index()
        .rename(columns={case_col: "case_count"})
    )
    
    # Step 2: Reaction Category Clustering (SOC-level if available)
    soc_col = None
    for col in ["soc", "soc_name", "system_organ_class"]:
        if col in df.columns:
            soc_col = col
            break
    
    if soc_col:
        reactions = (
            df.groupby([reaction_col, soc_col])[case_col]
            .count()
            .reset_index()
            .rename(columns={case_col: "case_count"})
        )
    else:
        # Fallback: just reaction counts
        reactions = (
            df.groupby(reaction_col)[case_col]
            .count()
            .reset_index()
            .rename(columns={case_col: "case_count"})
        )
        reactions["soc"] = "Unknown"
    
    # Step 3: Cross-Signal Links (drug + reaction)
    cross_links = (
        df.groupby([drug_col, reaction_col])[case_col]
        .count()
        .reset_index()
        .rename(columns={case_col: "count"})
        .sort_values("count", ascending=False)
    )
    
    # Step 4: Portfolio-level RPF (weighted by case count)
    portfolio_rpf = []
    
    if RPF_AVAILABLE:
        try:
            rpf_engine = RiskPrioritizationEngine()
            
            # Compute RPF per drug
            for drug in df[drug_col].unique():
                drug_df = df[df[drug_col] == drug]
                
                # Create a minimal signal dict for RPF computation
                signal_data = {
                    "drug": drug,
                    "cases": len(drug_df),
                    "serious_cases": len(drug_df[drug_df.get("seriousness", pd.Series()).str.contains("Yes", case=False, na=False)]) if "seriousness" in drug_df.columns else 0
                }
                
                try:
                    rpf_result = rpf_engine.score_signal(signal_data)
                    portfolio_rpf.append({
                        "drug_name": drug,
                        "rpf_score": rpf_result.get("rpf_score", 0.0) if isinstance(rpf_result, dict) else 0.0,
                        "case_count": len(drug_df)
                    })
                except Exception:
                    # Fallback: simple case count-based score
                    portfolio_rpf.append({
                        "drug_name": drug,
                        "rpf_score": min(100, len(drug_df) * 0.1),
                        "case_count": len(drug_df)
                    })
        except Exception:
            # Fallback: case count-based RPF
            drug_counts = df.groupby(drug_col)[case_col].count().reset_index()
            drug_counts.columns = [drug_col, "case_count"]
            drug_counts["rpf_score"] = drug_counts["case_count"].apply(lambda x: min(100, x * 0.1))
            drug_counts = drug_counts.rename(columns={drug_col: "drug_name"})
            portfolio_rpf = drug_counts.to_dict("records")
    else:
        # Simple fallback RPF
        drug_counts = df.groupby(drug_col)[case_col].count().reset_index()
        drug_counts.columns = [drug_col, "case_count"]
        drug_counts["rpf_score"] = drug_counts["case_count"].apply(lambda x: min(100, x * 0.1))
        drug_counts = drug_counts.rename(columns={drug_col: "drug_name"})
        portfolio_rpf = drug_counts.to_dict("records")
    
    # Step 5: Portfolio Trends
    trends = {}
    if PORTFOLIO_TRENDS_AVAILABLE:
        try:
            trend_engine = PortfolioTrendEngine()
            trends = trend_engine.compute_cross_product_trends(df)
        except Exception:
            trends = {}
    elif TREND_ALERTS_AVAILABLE:
        try:
            alerts = detect_trend_alerts_light(df)
            trends = {"portfolio_alerts": alerts or []}
        except Exception:
            trends = {}
    
    # Step 6: Class-Effect Detection
    class_effects = []
    if "drug_class" in df.columns:
        class_grouped = df.groupby(["drug_class", reaction_col])[case_col].count().reset_index()
        class_grouped.columns = ["drug_class", "reaction", "case_count"]
        
        # Find reactions that appear in multiple drugs of same class
        for drug_class in class_grouped["drug_class"].unique():
            class_reactions = class_grouped[class_grouped["drug_class"] == drug_class]
            class_reactions = class_reactions.sort_values("case_count", ascending=False)
            
            if len(class_reactions) > 0:
                class_effects.append({
                    "drug_class": drug_class,
                    "top_reaction": class_reactions.iloc[0]["reaction"] if len(class_reactions) > 0 else None,
                    "total_cases": class_reactions["case_count"].sum(),
                    "unique_reactions": len(class_reactions)
                })
    
    return {
        "trends": trends,
        "drug_classes": drug_classes.to_dict("records"),
        "reaction_clusters": reactions.to_dict("records"),
        "cross_signal_links": cross_links.to_dict("records"),
        "portfolio_rpf": portfolio_rpf,
        "class_effects": class_effects
    }

