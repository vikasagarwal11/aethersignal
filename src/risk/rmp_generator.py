"""
RMP (Risk Management Plan) Generator (Phase 3F.5.3)
Generates regulatory-ready RMP reports.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class RMPGenerator:
    """
    Generates Risk Management Plan (RMP) reports.
    """
    
    def __init__(self):
        """Initialize RMP generator."""
        pass
    
    def generate_rmp_section(
        self,
        drug: str,
        reaction: str,
        gri_result: Dict[str, Any],
        mechanism_result: Optional[Dict[str, Any]] = None,
        label_gaps: Optional[Dict[str, Any]] = None,
        literature_summary: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate RMP section for a drug-reaction pair.
        
        Args:
            drug: Drug name
            reaction: Reaction name
            gri_result: Global Risk Index result
            mechanism_result: Optional mechanism analysis result
            label_gaps: Optional label gap analysis
            literature_summary: Optional literature summary
        
        Returns:
            Dictionary with RMP section content
        """
        rmp_section = {
            "drug": drug,
            "reaction": reaction,
            "generated_at": datetime.now().isoformat(),
            "summary": self._generate_summary(drug, reaction, gri_result),
            "epidemiological_stats": self._generate_epidemiological_stats(gri_result),
            "mechanistic_justification": self._generate_mechanistic_justification(mechanism_result),
            "literature_support": literature_summary or "Literature review pending",
            "label_comparison": self._generate_label_comparison(label_gaps),
            "clinical_evidence": self._generate_clinical_evidence(gri_result),
            "geographic_breakdown": self._generate_geographic_breakdown(gri_result),
            "recommended_actions": self._generate_recommended_actions(gri_result),
            "monitoring_plan": self._generate_monitoring_plan(gri_result),
            "mitigation_plan": self._generate_mitigation_plan(gri_result)
        }
        
        return rmp_section
    
    def _generate_summary(
        self,
        drug: str,
        reaction: str,
        gri_result: Dict[str, Any]
    ) -> str:
        """Generate risk summary."""
        gri_score = gri_result.get("gri_score", 0.0)
        priority = gri_result.get("priority_category", "unknown")
        total_cases = gri_result.get("total_cases", 0)
        
        return (
            f"Risk Summary: {drug} → {reaction}\n"
            f"Global Risk Index: {gri_score:.2f} ({priority.title()})\n"
            f"Total Cases: {total_cases}\n"
            f"Recommended Action: {gri_result.get('recommended_action', 'monitor').replace('_', ' ').title()}"
        )
    
    def _generate_epidemiological_stats(self, gri_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate epidemiological statistics."""
        return {
            "total_cases": gri_result.get("total_cases", 0),
            "sources": gri_result.get("sources", []),
            "source_count": len(gri_result.get("sources", [])),
            "components": gri_result.get("components", {})
        }
    
    def _generate_mechanistic_justification(
        self,
        mechanism_result: Optional[Dict[str, Any]]
    ) -> str:
        """Generate mechanistic justification."""
        if not mechanism_result:
            return "Mechanistic analysis pending"
        
        chain = mechanism_result.get("chain", [])
        plausibility = mechanism_result.get("plausibility_score", 0.0)
        
        if chain:
            chain_text = "\n".join(f"- {step}" for step in chain)
            return f"Mechanistic Plausibility: {plausibility:.2f}\n\nMechanistic Chain:\n{chain_text}"
        else:
            return f"Mechanistic Plausibility: {plausibility:.2f}\n\nMechanistic chain analysis pending"
    
    def _generate_label_comparison(
        self,
        label_gaps: Optional[Dict[str, Any]]
    ) -> str:
        """Generate label comparison."""
        if not label_gaps:
            return "Label comparison analysis pending"
        
        gap_score = label_gaps.get("gap_score", 0.0)
        return f"Label Gap Score: {gap_score:.2f}\n\nDetailed label comparison pending"
    
    def _generate_clinical_evidence(self, gri_result: Dict[str, Any]) -> str:
        """Generate clinical evidence summary."""
        components = gri_result.get("components", {})
        clinical_score = components.get("clinical_evidence", 0.0)
        
        return f"Clinical Evidence Alignment Score: {clinical_score:.2f}"
    
    def _generate_geographic_breakdown(self, gri_result: Dict[str, Any]) -> str:
        """Generate geographic breakdown."""
        sources = gri_result.get("sources", [])
        return f"Sources reporting: {', '.join(sources) if sources else 'Multiple sources'}"
    
    def _generate_recommended_actions(self, gri_result: Dict[str, Any]) -> List[str]:
        """Generate recommended actions."""
        action = gri_result.get("recommended_action", "monitor_only")
        priority = gri_result.get("priority_category", "low")
        
        actions = []
        
        if action == "public_health_alert":
            actions.append("Immediate public health notification required")
            actions.append("Regulatory authority notification")
        elif action == "regulatory_submission":
            actions.append("Prepare regulatory submission (PSUR/PBRER)")
            actions.append("Update Risk Management Plan")
        elif action == "label_update_recommended":
            actions.append("Review label update requirements")
            actions.append("Prepare label change proposal")
        elif action == "trigger_medical_review":
            actions.append("Medical review required")
            actions.append("Case-by-case assessment")
        elif action == "enhanced_surveillance":
            actions.append("Enhanced monitoring recommended")
            actions.append("Quarterly review")
        else:
            actions.append("Continue routine monitoring")
        
        return actions
    
    def _generate_monitoring_plan(self, gri_result: Dict[str, Any]) -> str:
        """Generate monitoring plan."""
        priority = gri_result.get("priority_category", "low")
        
        if priority == "critical":
            return "Daily monitoring, weekly review, immediate escalation protocol"
        elif priority == "high":
            return "Weekly monitoring, monthly review, quarterly assessment"
        elif priority == "moderate":
            return "Monthly monitoring, quarterly review"
        else:
            return "Routine monitoring, annual review"
    
    def _generate_mitigation_plan(self, gri_result: Dict[str, Any]) -> str:
        """Generate mitigation plan."""
        action = gri_result.get("recommended_action", "monitor_only")
        
        if action in ["public_health_alert", "regulatory_submission"]:
            return "Immediate risk mitigation measures required. Consider label update, patient communication, healthcare provider notification."
        elif action == "label_update_recommended":
            return "Consider label update to include reaction. Patient monitoring recommended."
        elif action == "trigger_medical_review":
            return "Medical review to assess causality. Enhanced patient monitoring."
        else:
            return "Standard monitoring and surveillance"

