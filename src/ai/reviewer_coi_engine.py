"""
Reviewer Conflict-of-Interest Engine (CHUNK B7.1)
Detects and validates reviewer conflicts before assignment.
"""
from typing import Dict, List, Any, Optional


def detect_conflicts(
    signal: Dict[str, Any],
    reviewer: Dict[str, Any],
    reviewer_history: Optional[Dict[str, Any]] = None,
    company_policy: Optional[Dict[str, Any]] = None
) -> List[str]:
    """
    Detect conflicts of interest for a reviewer-signal assignment (CHUNK B7.1).
    
    Args:
        signal: Signal dictionary with drug, reaction, case_id, study_id, etc.
        reviewer: Reviewer profile dictionary
        reviewer_history: Reviewer's historical assignments, authored cases, etc.
        company_policy: Company COI policy limits
        
    Returns:
        List of conflict descriptions (empty if no conflicts)
    """
    conflicts = []
    reviewer_history = reviewer_history or {}
    company_policy = company_policy or {
        "max_open_tasks": 12,
        "max_risk_load": 15,
        "allow_same_study": False,
        "allow_product_overlap": True
    }
    
    reviewer_name = reviewer.get("name", "Unknown")
    
    # 1. Reviewer authored case narratives
    authored_cases = reviewer_history.get("authored_cases", [])
    signal_case_id = signal.get("case_id")
    
    if signal_case_id and signal_case_id in authored_cases:
        conflicts.append(
            f"Reviewer {reviewer_name} authored case narrative for case {signal_case_id}. "
            "Self-review violates independence requirements."
        )
    
    # Check multiple case IDs if present
    case_ids = signal.get("case_ids", [])
    if isinstance(case_ids, list):
        for case_id in case_ids:
            if case_id in authored_cases:
                conflicts.append(
                    f"Reviewer {reviewer_name} authored case narrative for case {case_id}. "
                    "Self-review violates independence requirements."
                )
    
    # 2. Product conflict / Competing product
    product_conflicts = reviewer_history.get("product_conflicts", [])
    signal_drug = signal.get("drug", "")
    
    if signal_drug and signal_drug in product_conflicts:
        conflicts.append(
            f"Drug '{signal_drug}' conflicts with reviewer {reviewer_name}'s portfolio. "
            "Assignment may create competitive bias."
        )
    
    # Check for competing products
    competing_products = reviewer_history.get("competing_products", [])
    if signal_drug and signal_drug in competing_products:
        conflicts.append(
            f"Drug '{signal_drug}' is a competing product to reviewer {reviewer_name}'s portfolio. "
            "Assignment may create competitive bias."
        )
    
    # Check product overlap if not allowed
    if not company_policy.get("allow_product_overlap", True):
        reviewer_products = reviewer_history.get("assigned_products", [])
        if signal_drug and signal_drug in reviewer_products:
            conflicts.append(
                f"Reviewer {reviewer_name} already assigned to product '{signal_drug}'. "
                "Product overlap not allowed per company policy."
            )
    
    # 3. Study conflict
    study_conflicts = reviewer_history.get("study_conflicts", [])
    signal_study_id = signal.get("study_id")
    
    if signal_study_id and signal_study_id in study_conflicts:
        conflicts.append(
            f"Reviewer {reviewer_name} is part of study {signal_study_id}. "
            "Assignment to same study creates conflict of interest."
        )
    
    # Check if reviewer is study investigator
    study_investigators = reviewer_history.get("study_investigators", {})
    if signal_study_id and signal_study_id in study_investigators:
        investigators = study_investigators[signal_study_id]
        if reviewer_name in investigators:
            conflicts.append(
                f"Reviewer {reviewer_name} is an investigator in study {signal_study_id}. "
                "Assignment to own study creates conflict of interest."
            )
    
    # Check same study policy
    if not company_policy.get("allow_same_study", False):
        reviewer_studies = reviewer_history.get("assigned_studies", [])
        if signal_study_id and signal_study_id in reviewer_studies:
            conflicts.append(
                f"Reviewer {reviewer_name} already assigned to study {signal_study_id}. "
                "Same-study assignment not allowed per company policy."
            )
    
    # 4. Workload limit exceeded
    max_open_tasks = company_policy.get("max_open_tasks", 12)
    current_open_tasks = reviewer_history.get("open_tasks", 0)
    
    if current_open_tasks >= max_open_tasks:
        conflicts.append(
            f"Reviewer {reviewer_name} has {current_open_tasks} open tasks (limit: {max_open_tasks}). "
            "Assignment would exceed maximum workload capacity."
        )
    
    # 5. Risk load limit exceeded
    max_risk_load = company_policy.get("max_risk_load", 15)
    current_risk_load = reviewer_history.get("risk_load", 0)
    
    if current_risk_load >= max_risk_load:
        conflicts.append(
            f"Reviewer {reviewer_name} has risk load score {current_risk_load:.1f} (limit: {max_risk_load}). "
            "Assignment would exceed maximum risk load capacity."
        )
    
    # 6. Named in complaint
    complaints = reviewer_history.get("named_in_complaints", [])
    if complaints:
        signal_key = f"{signal_drug}_{signal.get('reaction', '')}"
        if signal_key in complaints:
            conflicts.append(
                f"Reviewer {reviewer_name} was named in a complaint related to this signal. "
                "Assignment may create bias or appearance of conflict."
            )
    
    # 7. Company policy violations
    policy_violations = reviewer_history.get("policy_violations", [])
    for violation in policy_violations:
        if violation.get("applies_to_signal_type") == signal.get("signal_type"):
            conflicts.append(
                f"Reviewer {reviewer_name} has policy restriction: {violation.get('description', 'Unknown violation')}"
            )
    
    # 8. Recent assignment to same drug/reaction
    recent_assignments = reviewer_history.get("recent_assignments", [])
    for assignment in recent_assignments:
        if (assignment.get("drug") == signal_drug and 
            assignment.get("reaction") == signal.get("reaction", "")):
            conflicts.append(
                f"Reviewer {reviewer_name} was recently assigned to same signal ({signal_drug} → {signal.get('reaction', '')}). "
                "Frequent assignment to same signal may create bias."
            )
            break
    
    return conflicts


def validate_assignment(
    signal: Dict[str, Any],
    reviewer: Dict[str, Any],
    reviewer_history: Optional[Dict[str, Any]] = None,
    company_policy: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Validate reviewer assignment for conflicts (CHUNK B7.2).
    
    Args:
        signal: Signal dictionary
        reviewer: Reviewer profile dictionary
        reviewer_history: Reviewer's historical data
        company_policy: Company COI policy
        
    Returns:
        Dictionary with validation result and conflicts
    """
    conflicts = detect_conflicts(
        signal=signal,
        reviewer=reviewer,
        reviewer_history=reviewer_history,
        company_policy=company_policy
    )
    
    return {
        "valid": len(conflicts) == 0,
        "conflicts": conflicts,
        "reviewer_name": reviewer.get("name", "Unknown"),
        "signal_key": f"{signal.get('drug', 'Unknown')} → {signal.get('reaction', signal.get('event', 'Unknown'))}"
    }


def get_reviewer_history(
    reviewer_name: str,
    signals: Optional[List[Dict[str, Any]]] = None,
    cases: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Build reviewer history from available data.
    
    Args:
        reviewer_name: Reviewer name
        signals: List of all signals (to find assigned signals)
        cases: List of all cases (to find authored cases)
        
    Returns:
        Reviewer history dictionary
    """
    history = {
        "name": reviewer_name,
        "authored_cases": [],
        "product_conflicts": [],
        "competing_products": [],
        "assigned_products": [],
        "study_conflicts": [],
        "study_investigators": {},
        "assigned_studies": [],
        "open_tasks": 0,
        "risk_load": 0,
        "named_in_complaints": [],
        "policy_violations": [],
        "recent_assignments": []
    }
    
    # Extract from signals
    if signals:
        for signal in signals:
            owner = signal.get("owner") or signal.get("reviewer") or signal.get("assigned_reviewer", "")
            if owner == reviewer_name:
                history["open_tasks"] += 1
                
                # Track assigned products
                drug = signal.get("drug")
                if drug and drug not in history["assigned_products"]:
                    history["assigned_products"].append(drug)
                
                # Track assigned studies
                study_id = signal.get("study_id")
                if study_id and study_id not in history["assigned_studies"]:
                    history["assigned_studies"].append(study_id)
                
                # Track recent assignments
                history["recent_assignments"].append({
                    "drug": drug,
                    "reaction": signal.get("reaction") or signal.get("event"),
                    "assigned_date": signal.get("assigned_date")
                })
    
    # Extract from cases (if available)
    if cases:
        for case in cases:
            # Check if reviewer authored the case narrative
            narrative_author = case.get("narrative_author") or case.get("reporter_name")
            if narrative_author == reviewer_name:
                case_id = case.get("case_id") or case.get("id")
                if case_id:
                    history["authored_cases"].append(case_id)
    
    return history

