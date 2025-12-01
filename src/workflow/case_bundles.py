"""
Case Bundles Engine (Phase 3H.1)
Groups related AE evidence from all sources into reviewable bundles.
"""

import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)


class CaseBundle:
    """
    Represents a case bundle - a group of related AE evidence.
    """
    
    def __init__(
        self,
        bundle_id: str,
        drug: str,
        reaction: str,
        created_by: str = "system"
    ):
        """
        Initialize case bundle.
        
        Args:
            bundle_id: Unique bundle ID
            drug: Drug name
            reaction: Reaction name
            created_by: Creator (user or system)
        """
        self.bundle_id = bundle_id
        self.drug = drug
        self.reaction = reaction
        self.created_by = created_by
        self.created_at = datetime.now()
        self.status = "draft"  # draft, in_review, approved, rejected, needs_more_data
        self.evidence: List[Dict[str, Any]] = []
        self.tasks: List[Dict[str, Any]] = []
        self.reviews: List[Dict[str, Any]] = []
        self.audit_log: List[Dict[str, Any]] = []
        self.summary: Optional[str] = None
        self.quantum_score: Optional[float] = None
        self.gri_score: Optional[float] = None
    
    def add_evidence(self, evidence: Dict[str, Any]):
        """Add evidence to bundle."""
        evidence["added_at"] = datetime.now().isoformat()
        self.evidence.append(evidence)
        self._log_action("evidence_added", {"evidence_id": evidence.get("id")})
    
    def add_task(self, task: Dict[str, Any]):
        """Add task to bundle."""
        task["created_at"] = datetime.now().isoformat()
        task["status"] = "not_started"
        self.tasks.append(task)
        self._log_action("task_created", {"task_id": task.get("id")})
    
    def update_status(self, new_status: str, updated_by: str, reason: Optional[str] = None):
        """Update bundle status."""
        old_status = self.status
        self.status = new_status
        self._log_action(
            "status_updated",
            {
                "old_status": old_status,
                "new_status": new_status,
                "updated_by": updated_by,
                "reason": reason
            }
        )
    
    def add_review(self, review: Dict[str, Any]):
        """Add review to bundle."""
        review["reviewed_at"] = datetime.now().isoformat()
        self.reviews.append(review)
        self._log_action("review_added", {"reviewer": review.get("reviewer")})
    
    def _log_action(self, action: str, metadata: Dict[str, Any]):
        """Log action to audit trail."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "metadata": metadata
        }
        self.audit_log.append(log_entry)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert bundle to dictionary."""
        return {
            "bundle_id": self.bundle_id,
            "drug": self.drug,
            "reaction": self.reaction,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "status": self.status,
            "evidence_count": len(self.evidence),
            "task_count": len(self.tasks),
            "review_count": len(self.reviews),
            "quantum_score": self.quantum_score,
            "gri_score": self.gri_score,
            "summary": self.summary
        }


class CaseBundlesEngine:
    """
    Engine for creating and managing case bundles.
    """
    
    def __init__(self):
        """Initialize case bundles engine."""
        self.bundles: Dict[str, CaseBundle] = {}
    
    def create_bundle(
        self,
        drug: str,
        reaction: str,
        evidence_df: pd.DataFrame,
        created_by: str = "system"
    ) -> CaseBundle:
        """
        Create a new case bundle from evidence.
        
        Args:
            drug: Drug name
            reaction: Reaction name
            evidence_df: DataFrame with AE evidence
            created_by: Creator identifier
        
        Returns:
            CaseBundle instance
        """
        bundle_id = str(uuid.uuid4())
        bundle = CaseBundle(bundle_id, drug, reaction, created_by)
        
        # Add evidence from DataFrame
        for _, row in evidence_df.iterrows():
            evidence = {
                "id": row.get("ae_id", str(uuid.uuid4())),
                "source": row.get("source", "unknown"),
                "text": row.get("text", row.get("full_text", ""))[:500],
                "timestamp": row.get("timestamp") or row.get("event_date"),
                "severity": row.get("severity") or row.get("reaction_severity_score"),
                "confidence": row.get("confidence"),
                "quantum_score": row.get("quantum_score")
            }
            bundle.add_evidence(evidence)
        
        # Calculate summary scores
        if "quantum_score" in evidence_df.columns:
            bundle.quantum_score = evidence_df["quantum_score"].mean()
        
        # Auto-create default tasks
        bundle = self._create_default_tasks(bundle)
        
        # Store bundle
        self.bundles[bundle_id] = bundle
        
        return bundle
    
    def _create_default_tasks(self, bundle: CaseBundle) -> CaseBundle:
        """Create default tasks for bundle."""
        default_tasks = [
            {
                "id": str(uuid.uuid4()),
                "title": "Review Social Evidence",
                "type": "review",
                "priority": "medium",
                "assigned_to": None
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Check Literature Support",
                "type": "research",
                "priority": "medium",
                "assigned_to": None
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Run Mechanism Validation",
                "type": "analysis",
                "priority": "high",
                "assigned_to": None
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Assess Label Impact",
                "type": "regulatory",
                "priority": "high",
                "assigned_to": None
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Write Safety Narrative",
                "type": "documentation",
                "priority": "medium",
                "assigned_to": None
            }
        ]
        
        for task in default_tasks:
            bundle.add_task(task)
        
        return bundle
    
    def get_bundle(self, bundle_id: str) -> Optional[CaseBundle]:
        """Get bundle by ID."""
        return self.bundles.get(bundle_id)
    
    def list_bundles(
        self,
        status: Optional[str] = None,
        drug: Optional[str] = None,
        limit: int = 100
    ) -> List[CaseBundle]:
        """List bundles with filters."""
        bundles = list(self.bundles.values())
        
        if status:
            bundles = [b for b in bundles if b.status == status]
        
        if drug:
            bundles = [b for b in bundles if drug.lower() in b.drug.lower()]
        
        # Sort by created_at (newest first)
        bundles.sort(key=lambda b: b.created_at, reverse=True)
        
        return bundles[:limit]
    
    def auto_create_bundles_from_signals(
        self,
        prioritized_signals: List[Dict[str, Any]],
        evidence_df: pd.DataFrame,
        threshold: float = 0.65
    ) -> List[CaseBundle]:
        """
        Auto-create bundles from prioritized signals.
        
        Args:
            prioritized_signals: List of signals with GRI scores
            evidence_df: DataFrame with all AE evidence
            threshold: Minimum GRI score to create bundle
        
        Returns:
            List of created bundles
        """
        created_bundles = []
        
        for signal in prioritized_signals:
            gri_score = signal.get("gri_score", 0.0)
            
            if gri_score >= threshold:
                drug = signal.get("drug")
                reaction = signal.get("reaction")
                
                # Filter evidence for this drug-reaction pair
                bundle_evidence = evidence_df[
                    (evidence_df["drug"].str.contains(drug, case=False, na=False)) &
                    (evidence_df["reaction"] == reaction)
                ]
                
                if not bundle_evidence.empty:
                    bundle = self.create_bundle(
                        drug, reaction, bundle_evidence, created_by="system"
                    )
                    bundle.gri_score = gri_score
                    bundle.quantum_score = signal.get("quantum_score")
                    created_bundles.append(bundle)
        
        return created_bundles

