"""
AI Reviewer Assignment v2 (CHUNK B5)
Enhanced workload-aware, expertise-based reviewer assignment system.
"""
import pandas as pd
from typing import Dict, List, Any, Optional
import json

try:
    from .medical_llm import call_medical_llm
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False


def assign_reviewer_v2(
    signal: Dict[str, Any],
    reviewers_df: pd.DataFrame,
    lifecycle_stage: str,
    severity: str,
    therapeutic_area: Optional[str] = None,
    due_date: Optional[str] = None,
    medical_llm = None
) -> Dict[str, Any]:
    """
    Enhanced, workload-aware reviewer assignment engine.
    
    Args:
        signal: Signal dictionary
        reviewers_df: DataFrame with reviewer information (columns: name, expertise, open_reviews, etc.)
        lifecycle_stage: Current lifecycle stage
        severity: Signal severity (low/medium/high/critical)
        therapeutic_area: Therapeutic area tag
        due_date: Due date string
        medical_llm: LLM instance for AI layer
        
    Returns:
        Dictionary with reviewer assignment and rationale
    """
    if reviewers_df is None or reviewers_df.empty:
        return {
            "reviewer": "Unassigned",
            "rationale": "No reviewers available in system."
        }
    
    # -----------------------
    # RULE LAYER (fast)
    # -----------------------
    
    # Calculate expertise match
    if therapeutic_area:
        reviewers_df = reviewers_df.copy()
        reviewers_df["expertise_match"] = reviewers_df.get("expertise", pd.Series()).apply(
            lambda x: therapeutic_area.lower() in str(x).lower() if pd.notna(x) else False
        )
    else:
        reviewers_df = reviewers_df.copy()
        reviewers_df["expertise_match"] = False
    
    # Calculate workload score (inverse of open reviews)
    reviewers_df["workload_score"] = 1.0 / (reviewers_df.get("open_reviews", pd.Series([1])).fillna(1) + 1)
    
    # Severity weight
    severity_weight = {
        "high": 1.0,
        "critical": 1.0,
        "medium": 0.7,
        "low": 0.4
    }.get(severity.lower(), 0.5)
    
    # Risk-adjusted capacity
    reviewers_df["risk_adjusted_capacity"] = reviewers_df["workload_score"] * severity_weight
    
    # Prioritize: expertise match first, then risk-adjusted capacity
    if "expertise_match" in reviewers_df.columns and reviewers_df["expertise_match"].any():
        # Sort by expertise match (True first), then risk-adjusted capacity (descending)
        candidates = reviewers_df.sort_values(
            ["expertise_match", "risk_adjusted_capacity"],
            ascending=[False, False]
        )
    else:
        # No expertise match, sort by risk-adjusted capacity
        candidates = reviewers_df.sort_values("risk_adjusted_capacity", ascending=False)
    
    candidate = candidates.iloc[0]
    
    # -----------------------
    # AI LAYER (contextual)
    # -----------------------
    
    ai_rationale = None
    
    if LLM_AVAILABLE and medical_llm:
        try:
            ai_prompt = f"""
You are an expert in pharmacovigilance reviewer assignment.

Signal:
- Drug: {signal.get('drug', 'Unknown')}
- Reaction: {signal.get('reaction', signal.get('event', 'Unknown'))}
- Priority: {signal.get('priority', 'Unknown')}

Candidate Reviewer:
- Name: {candidate.get('name', 'Unknown')}
- Expertise: {candidate.get('expertise', 'Not specified')}
- Open Reviews: {candidate.get('open_reviews', 0)}
- Workload Score: {candidate.get('workload_score', 0):.2f}

Lifecycle Stage: {lifecycle_stage}
Severity: {severity}
Therapeutic Area: {therapeutic_area or 'Not specified'}
Due Date: {due_date or 'Not specified'}

Explain if this candidate is ideal for reviewing this signal.

Respond in JSON format:
{{
    "reviewer": "reviewer name",
    "rationale": "brief explanation of assignment rationale"
}}
"""
            
            system_prompt = "You are a pharmacovigilance operations manager assigning reviewers based on expertise, workload, and signal characteristics."
            
            ai_response = call_medical_llm(
                prompt=ai_prompt,
                system_prompt=system_prompt,
                task_type="general",
                max_tokens=200,
                temperature=0.3
            )
            
            if ai_response:
                try:
                    # Try to parse JSON
                    response_clean = ai_response.strip()
                    if response_clean.startswith("```json"):
                        response_clean = response_clean[7:]
                    elif response_clean.startswith("```"):
                        response_clean = response_clean[3:]
                    if response_clean.endswith("```"):
                        response_clean = response_clean[:-3]
                    response_clean = response_clean.strip()
                    
                    ai_result = json.loads(response_clean)
                    reviewer_name = ai_result.get("reviewer", candidate.get("name", "Unknown"))
                    ai_rationale = ai_result.get("rationale", "AI rationale unavailable.")
                    
                    return {
                        "reviewer": reviewer_name,
                        "rationale": ai_rationale,
                        "expertise_match": candidate.get("expertise_match", False),
                        "workload_score": candidate.get("workload_score", 0)
                    }
                except (json.JSONDecodeError, ValueError):
                    ai_rationale = ai_response[:200] if len(ai_response) > 200 else ai_response
        except Exception:
            pass
    
    # Fallback to rule-based assignment
    reviewer_name = candidate.get("name", "Unassigned")
    rule_rationale = f"Assigned based on workload ({candidate.get('workload_score', 0):.2f})"
    if candidate.get("expertise_match", False):
        rule_rationale += f" and expertise match in {therapeutic_area}"
    
    return {
        "reviewer": reviewer_name,
        "rationale": ai_rationale or rule_rationale,
        "expertise_match": candidate.get("expertise_match", False),
        "workload_score": candidate.get("workload_score", 0)
    }

