"""
Review Workflows (Phase 3H.3)
Three-tier review lifecycle for case bundles.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
import logging

from .case_bundles import CaseBundle

logger = logging.getLogger(__name__)


class ReviewWorkflow:
    """
    Manages review workflow for case bundles.
    """
    
    # Workflow states
    STATES = ["draft", "peer_review", "final_review", "approved", "rejected", "needs_more_data"]
    
    def __init__(self):
        """Initialize review workflow."""
        pass
    
    def start_peer_review(
        self,
        bundle: CaseBundle,
        reviewer1: str,
        reviewer2: str
    ) -> Dict[str, Any]:
        """
        Start peer review process.
        
        Args:
            bundle: Case bundle
            reviewer1: First reviewer
            reviewer2: Second reviewer
        
        Returns:
            Review workflow status
        """
        bundle.update_status("peer_review", "system", "Peer review initiated")
        
        # Create review assignments
        review1 = {
            "id": str(uuid.uuid4()),
            "reviewer": reviewer1,
            "role": "safety_scientist",
            "status": "pending",
            "assigned_at": datetime.now().isoformat()
        }
        
        review2 = {
            "id": str(uuid.uuid4()),
            "reviewer": reviewer2,
            "role": "mechanism_specialist",
            "status": "pending",
            "assigned_at": datetime.now().isoformat()
        }
        
        bundle.add_review(review1)
        bundle.add_review(review2)
        
        return {
            "status": "peer_review",
            "reviewers": [reviewer1, reviewer2],
            "required_approvals": 2
        }
    
    def submit_review(
        self,
        bundle: CaseBundle,
        reviewer: str,
        decision: str,  # approve, reject, request_changes
        comments: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Submit a review decision.
        
        Args:
            bundle: Case bundle
            reviewer: Reviewer identifier
            decision: Review decision
            comments: Optional comments
        
        Returns:
            Review submission result
        """
        # Find reviewer's review
        for review in bundle.reviews:
            if review.get("reviewer") == reviewer:
                review["decision"] = decision
                review["comments"] = comments
                review["reviewed_at"] = datetime.now().isoformat()
                review["status"] = "completed"
                break
        
        # Check if all reviews complete
        completed_reviews = [r for r in bundle.reviews if r.get("status") == "completed"]
        
        if len(completed_reviews) >= 2:
            # Check decisions
            decisions = [r.get("decision") for r in completed_reviews]
            
            if all(d == "approve" for d in decisions):
                # Move to final review
                bundle.update_status("final_review", reviewer, "All peer reviews approved")
                return {"status": "final_review", "message": "Ready for final review"}
            elif any(d == "reject" for d in decisions):
                bundle.update_status("rejected", reviewer, "Rejected in peer review")
                return {"status": "rejected", "message": "Bundle rejected"}
            else:
                bundle.update_status("needs_more_data", reviewer, "Changes requested")
                return {"status": "needs_more_data", "message": "Changes requested"}
        
        return {"status": "peer_review", "message": "Waiting for additional reviews"}
    
    def final_approval(
        self,
        bundle: CaseBundle,
        approver: str,
        decision: str,
        comments: Optional[str] = None
    ):
        """
        Final approval/rejection.
        
        Args:
            bundle: Case bundle
            approver: Approver identifier
            decision: approve or reject
            comments: Optional comments
        """
        if decision == "approve":
            bundle.update_status("approved", approver, comments or "Final approval")
            # Lock bundle (read-only except for addenda)
            bundle.status = "approved"
        else:
            bundle.update_status("rejected", approver, comments or "Final rejection")
    
    def get_workflow_status(self, bundle: CaseBundle) -> Dict[str, Any]:
        """Get current workflow status."""
        return {
            "current_state": bundle.status,
            "reviews_completed": len([r for r in bundle.reviews if r.get("status") == "completed"]),
            "reviews_required": 2 if bundle.status == "peer_review" else 1,
            "can_advance": self._can_advance(bundle)
        }
    
    def _can_advance(self, bundle: CaseBundle) -> bool:
        """Check if bundle can advance to next state."""
        if bundle.status == "draft":
            return True
        elif bundle.status == "peer_review":
            completed = len([r for r in bundle.reviews if r.get("status") == "completed"])
            return completed >= 2
        elif bundle.status == "final_review":
            return True
        else:
            return False

