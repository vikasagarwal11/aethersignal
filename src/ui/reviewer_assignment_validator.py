"""
Reviewer Assignment Validator UI (CHUNK B7.3)
UI components for validating reviewer assignments with COI checking.
"""
import streamlit as st
from typing import Dict, List, Any, Optional
import pandas as pd

try:
    from src.ai.reviewer_coi_engine import validate_assignment, get_reviewer_history
    COI_ENGINE_AVAILABLE = True
except ImportError:
    COI_ENGINE_AVAILABLE = False


def render_assignment_validator(
    signal: Dict[str, Any],
    reviewers: List[Dict[str, Any]],
    reviewer_histories: Optional[Dict[str, Dict[str, Any]]] = None,
    company_policy: Optional[Dict[str, Any]] = None,
    signals_list: Optional[List[Dict[str, Any]]] = None,
    cases_list: Optional[List[Dict[str, Any]]] = None
) -> Optional[str]:
    """
    Render reviewer assignment validator with COI checking (CHUNK B7.3).
    
    Args:
        signal: Signal dictionary to assign
        reviewers: List of reviewer profile dictionaries
        reviewer_histories: Optional pre-computed reviewer histories
        company_policy: Company COI policy
        signals_list: All signals (for building history)
        cases_list: All cases (for building history)
        
    Returns:
        Selected reviewer name if valid assignment, None otherwise
    """
    if not COI_ENGINE_AVAILABLE:
        st.error("Conflict-of-Interest engine not available. Please install required dependencies.")
        return None
    
    st.markdown("### 👤 Assign Reviewer")
    
    signal_drug = signal.get("drug", "Unknown")
    signal_reaction = signal.get("reaction") or signal.get("event", "Unknown")
    signal_key = f"{signal_drug} → {signal_reaction}"
    
    st.info(f"**Signal:** {signal_key}")
    
    # Reviewer selection
    reviewer_names = [r.get("name", "Unknown") for r in reviewers]
    
    if not reviewer_names:
        st.warning("No reviewers available for assignment.")
        return None
    
    selected_reviewer_name = st.selectbox(
        "Select Reviewer:",
        options=reviewer_names,
        help="Select a reviewer to validate assignment"
    )
    
    # Find selected reviewer
    selected_reviewer = next((r for r in reviewers if r.get("name") == selected_reviewer_name), None)
    
    if not selected_reviewer:
        return None
    
    # Get or build reviewer history
    reviewer_histories = reviewer_histories or {}
    
    if selected_reviewer_name not in reviewer_histories:
        # Build history on-the-fly
        reviewer_history = get_reviewer_history(
            reviewer_name=selected_reviewer_name,
            signals=signals_list,
            cases=cases_list
        )
    else:
        reviewer_history = reviewer_histories[selected_reviewer_name]
    
    # Default company policy
    company_policy = company_policy or {
        "max_open_tasks": 12,
        "max_risk_load": 15,
        "allow_same_study": False,
        "allow_product_overlap": True
    }
    
    # Validate assignment
    validation_result = validate_assignment(
        signal=signal,
        reviewer=selected_reviewer,
        reviewer_history=reviewer_history,
        company_policy=company_policy
    )
    
    # Display validation result
    st.markdown("---")
    
    if validation_result["valid"]:
        st.success("✅ **Assignment Valid** — No conflicts detected.")
        st.info("This reviewer assignment complies with all conflict-of-interest policies.")
        
        # Show assignment details
        with st.expander("📋 Assignment Details", expanded=False):
            st.json({
                "reviewer": selected_reviewer_name,
                "signal": signal_key,
                "reviewer_expertise": selected_reviewer.get("expertise", "Not specified"),
                "current_workload": reviewer_history.get("open_tasks", 0),
                "current_risk_load": reviewer_history.get("risk_load", 0)
            })
        
        # Confirm button
        if st.button("✅ Confirm Assignment", type="primary", key="confirm_assignment"):
            return selected_reviewer_name
        
        return None
    else:
        st.error("❌ **Assignment Blocked** — Conflicts detected:")
        
        conflicts = validation_result["conflicts"]
        
        for i, conflict in enumerate(conflicts, 1):
            st.write(f"**{i}.** {conflict}")
        
        st.warning("⚠️ This assignment cannot be completed due to conflict-of-interest violations. Please select a different reviewer.")
        
        # Show reviewer details
        with st.expander("📋 Reviewer Details", expanded=False):
            st.json({
                "reviewer": selected_reviewer_name,
                "current_workload": reviewer_history.get("open_tasks", 0),
                "current_risk_load": reviewer_history.get("risk_load", 0),
                "assigned_products": reviewer_history.get("assigned_products", []),
                "authored_cases": len(reviewer_history.get("authored_cases", []))
            })
        
        return None


def render_bulk_assignment_validator(
    signals: List[Dict[str, Any]],
    reviewers: List[Dict[str, Any]],
    company_policy: Optional[Dict[str, Any]] = None
) -> pd.DataFrame:
    """
    Render bulk assignment validation for multiple signals.
    
    Args:
        signals: List of signals to validate
        reviewers: List of reviewer profiles
        company_policy: Company COI policy
        
    Returns:
        DataFrame with validation results
    """
    if not COI_ENGINE_AVAILABLE:
        st.error("Conflict-of-Interest engine not available.")
        return pd.DataFrame()
    
    st.markdown("### 🔍 Bulk Assignment Validation")
    
    validation_results = []
    
    with st.spinner("Validating assignments..."):
        for signal in signals:
            signal_drug = signal.get("drug", "Unknown")
            signal_reaction = signal.get("reaction") or signal.get("event", "Unknown")
            signal_key = f"{signal_drug} → {signal_reaction}"
            
            current_reviewer = signal.get("owner") or signal.get("reviewer") or signal.get("assigned_reviewer")
            
            if current_reviewer:
                # Find reviewer
                reviewer = next((r for r in reviewers if r.get("name") == current_reviewer), None)
                
                if reviewer:
                    # Build history (simplified for bulk)
                    reviewer_history = get_reviewer_history(
                        reviewer_name=current_reviewer,
                        signals=signals,
                        cases=None
                    )
                    
                    # Validate
                    result = validate_assignment(
                        signal=signal,
                        reviewer=reviewer,
                        reviewer_history=reviewer_history,
                        company_policy=company_policy
                    )
                    
                    validation_results.append({
                        "Signal": signal_key,
                        "Assigned Reviewer": current_reviewer,
                        "Valid": "✅ Yes" if result["valid"] else "❌ No",
                        "Conflicts": len(result["conflicts"]),
                        "Conflict Details": "; ".join(result["conflicts"][:2])  # First 2 conflicts
                    })
    
    if validation_results:
        results_df = pd.DataFrame(validation_results)
        st.dataframe(results_df, use_container_width=True, hide_index=True)
        return results_df
    else:
        st.info("No assignments to validate.")
        return pd.DataFrame()

