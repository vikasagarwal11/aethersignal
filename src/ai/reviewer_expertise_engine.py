"""
Reviewer Expertise Matching Engine (CHUNK B8)
Skill-based reviewer assignment with expertise scoring.
"""
import pandas as pd
from typing import Dict, List, Any, Optional


def compute_expertise_score(
    signal: Dict[str, Any],
    reviewer: Dict[str, Any]
) -> float:
    """
    Compute Reviewer Expertise Score (ES) for signal assignment (CHUNK B8.2).
    
    Formula: ES = (Skill match × 0.5) + (Therapeutic-area match × 0.3) + (Historical performance × 0.2)
    
    Args:
        signal: Signal dictionary with required skills, therapeutic area, etc.
        reviewer: Reviewer profile with skills, therapeutic areas, performance metrics
        
    Returns:
        Expertise Score (0.0 - 1.0)
    """
    # 1. Skill overlap (50% weight)
    signal_skills = signal.get("skills_required", [])
    reviewer_skills = reviewer.get("skills", [])
    
    if isinstance(signal_skills, str):
        signal_skills = [s.strip() for s in signal_skills.split(",")]
    if isinstance(reviewer_skills, str):
        reviewer_skills = [s.strip() for s in reviewer_skills.split(",")]
    
    # Normalize to lowercase for matching
    signal_skills_set = {s.lower() for s in signal_skills}
    reviewer_skills_set = {s.lower() for s in reviewer_skills}
    
    if signal_skills_set:
        skill_overlap = len(signal_skills_set & reviewer_skills_set) / len(signal_skills_set)
    else:
        # No specific skills required, assume 0.5 match
        skill_overlap = 0.5
    
    # 2. Therapeutic area match (30% weight)
    signal_ta = signal.get("therapeutic_area", signal.get("indication", "")).lower()
    reviewer_tas = reviewer.get("therapeutic_areas", [])
    
    if isinstance(reviewer_tas, str):
        reviewer_tas = [ta.strip() for ta in reviewer_tas.split(",")]
    
    reviewer_tas_lower = [ta.lower() for ta in reviewer_tas]
    
    ta_match = 1.0 if signal_ta and any(signal_ta in ta or ta in signal_ta for ta in reviewer_tas_lower) else 0.0
    
    # If signal has no explicit TA, try to infer from drug
    if not signal_ta and not reviewer_tas_lower:
        # Default: moderate match if no TA specified
        ta_match = 0.5
    elif signal_ta and not reviewer_tas_lower:
        # Reviewer has no TA specified, neutral
        ta_match = 0.5
    
    # 3. Historical performance (20% weight)
    performance_score = reviewer.get("avg_review_quality", 0.5)
    
    # Ensure performance score is 0-1
    if performance_score > 1.0:
        performance_score = performance_score / 100.0
    
    if performance_score < 0.0:
        performance_score = 0.0
    elif performance_score > 1.0:
        performance_score = 1.0
    
    # If no performance data, use default
    if performance_score == 0.0:
        performance_score = 0.7  # Default: assume good performance
    
    # Calculate Expertise Score
    es = (0.5 * skill_overlap) + (0.3 * ta_match) + (0.2 * performance_score)
    
    return round(es, 3)


def rank_reviewers_by_expertise(
    signal: Dict[str, Any],
    reviewers: List[Dict[str, Any]],
    min_score: float = 0.0
) -> pd.DataFrame:
    """
    Rank reviewers by expertise score for a given signal.
    
    Args:
        signal: Signal dictionary
        reviewers: List of reviewer profiles
        min_score: Minimum expertise score to include
        
    Returns:
        DataFrame with reviewers ranked by expertise score
    """
    rankings = []
    
    for reviewer in reviewers:
        es = compute_expertise_score(signal, reviewer)
        
        if es >= min_score:
            rankings.append({
                "Reviewer": reviewer.get("name", "Unknown"),
                "Expertise Score": es,
                "Skills": ", ".join(reviewer.get("skills", [])) if isinstance(reviewer.get("skills"), list) else str(reviewer.get("skills", "")),
                "Therapeutic Areas": ", ".join(reviewer.get("therapeutic_areas", [])) if isinstance(reviewer.get("therapeutic_areas"), list) else str(reviewer.get("therapeutic_areas", "")),
                "Performance Score": reviewer.get("avg_review_quality", 0.5),
                "Completed Reviews": reviewer.get("completed_reviews", 0),
                "Open Tasks": reviewer.get("current_workload", reviewer.get("open_tasks", 0))
            })
    
    if not rankings:
        return pd.DataFrame(columns=["Reviewer", "Expertise Score", "Skills", "Therapeutic Areas", "Performance Score", "Completed Reviews", "Open Tasks"])
    
    rankings_df = pd.DataFrame(rankings)
    rankings_df = rankings_df.sort_values("Expertise Score", ascending=False)
    
    return rankings_df


def infer_signal_skills_required(
    signal: Dict[str, Any]
) -> List[str]:
    """
    Infer required skills for a signal based on drug class, reaction type, etc.
    
    Args:
        signal: Signal dictionary
        
    Returns:
        List of required skills
    """
    skills = []
    
    drug = signal.get("drug", "").lower()
    reaction = signal.get("reaction", signal.get("event", "")).lower()
    
    # Drug class skills
    if any(term in drug for term in ["dupixent", "humira", "adalimumab", "etanercept", "infliximab"]):
        skills.extend(["biologics", "immunology"])
    elif any(term in drug for term in ["keytruda", "opdivo", "yervoy", "pembrolizumab", "nivolumab"]):
        skills.extend(["oncology", "immunotherapy"])
    elif any(term in drug for term in ["metformin", "insulin", "glipizide", "semaglutide"]):
        skills.extend(["endocrinology", "cardiometabolic"])
    
    # Reaction-based skills
    if any(term in reaction for term in ["injection", "infusion", "administration"]):
        skills.append("drug administration")
    if any(term in reaction for term in ["cardiac", "heart", "myocardial", "arrhythmia"]):
        skills.append("cardiology")
    if any(term in reaction for term in ["liver", "hepatic", "transaminase"]):
        skills.append("hepatology")
    if any(term in reaction for term in ["kidney", "renal", "nephro"]):
        skills.append("nephrology")
    
    # Remove duplicates and return
    return list(set(skills)) if skills else []


def get_recommended_reviewers(
    signal: Dict[str, Any],
    reviewers: List[Dict[str, Any]],
    top_n: int = 5,
    exclude_conflicts: bool = True
) -> List[Dict[str, Any]]:
    """
    Get top N recommended reviewers for a signal, optionally excluding conflicts.
    
    Args:
        signal: Signal dictionary
        reviewers: List of reviewer profiles
        top_n: Number of top reviewers to return
        exclude_conflicts: Whether to exclude reviewers with conflicts
        
    Returns:
        List of recommended reviewer dictionaries with expertise scores
    """
    # Infer skills if not provided
    if not signal.get("skills_required"):
        signal["skills_required"] = infer_signal_skills_required(signal)
    
    # Rank reviewers
    rankings_df = rank_reviewers_by_expertise(signal, reviewers)
    
    if rankings_df.empty:
        return []
    
    # Optionally filter conflicts
    if exclude_conflicts:
        try:
            from src.ai.reviewer_coi_engine import detect_conflicts
            
            filtered_reviewers = []
            for _, row in rankings_df.iterrows():
                reviewer = next((r for r in reviewers if r.get("name") == row["Reviewer"]), None)
                if reviewer:
                    conflicts = detect_conflicts(signal, reviewer)
                    if not conflicts:  # No conflicts
                        filtered_reviewers.append(row)
            
            if filtered_reviewers:
                rankings_df = pd.DataFrame(filtered_reviewers)
        except ImportError:
            pass  # COI engine not available, skip conflict filtering
    
    # Return top N
    top_reviewers = []
    for _, row in rankings_df.head(top_n).iterrows():
        reviewer = next((r for r in reviewers if r.get("name") == row["Reviewer"]), None)
        if reviewer:
            reviewer_copy = reviewer.copy()
            reviewer_copy["expertise_score"] = row["Expertise Score"]
            top_reviewers.append(reviewer_copy)
    
    return top_reviewers

