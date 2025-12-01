"""
Signal Lifecycle Timeline Model (CHUNK H1.9 Part 1)
Unified timeline data structure shared by client-side (Pyodide) and server-side processing.
Core foundation for signal lifecycle tracking, governance, inspector simulation, and regulatory reporting.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any
import json


@dataclass
class TimelineEvent:
    """
    A single event in the signal lifecycle timeline.
    
    Represents any significant milestone in signal processing:
    - Triage events
    - Assessment events
    - Evaluation events
    - Decision events
    - CAPA events
    - Label update events
    - Close events
    """
    name: str  # Event name (e.g., "Signal Triage", "Assessment Complete")
    timestamp: Optional[datetime] = None  # When the event occurred
    source: Optional[str] = None  # Source system/user (e.g., "auto-detected", "reviewer:john@example.com")
    details: Optional[Dict[str, Any]] = field(default_factory=dict)  # Event-specific details
    confidence: float = 1.0  # Confidence score (0.0-1.0) for auto-detected events
    sla_target_days: Optional[int] = None  # SLA target in days from previous event
    sla_met: Optional[bool] = None  # Whether SLA was met
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "name": self.name,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "source": self.source,
            "details": self.details,
            "confidence": self.confidence,
            "sla_target_days": self.sla_target_days,
            "sla_met": self.sla_met
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TimelineEvent":
        """Create TimelineEvent from dictionary."""
        timestamp = None
        if data.get("timestamp"):
            if isinstance(data["timestamp"], str):
                timestamp = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
            elif isinstance(data["timestamp"], datetime):
                timestamp = data["timestamp"]
        
        return cls(
            name=data.get("name", ""),
            timestamp=timestamp,
            source=data.get("source"),
            details=data.get("details", {}),
            confidence=data.get("confidence", 1.0),
            sla_target_days=data.get("sla_target_days"),
            sla_met=data.get("sla_met")
        )


@dataclass
class SignalLifecycleTimeline:
    """
    Unified lifecycle timeline structure shared by client + server.
    
    This is the core data model that tracks a signal's complete lifecycle from
    initial detection through assessment, decision, CAPA, label updates, and closure.
    
    Used by:
    - Trend Alerts Engine
    - Signal Governance Dashboard
    - Inspector Simulation
    - Risk Prioritization Framework (RPF)
    - Benefit-Risk Assessment
    - CAPA Recommendations
    - Label Impact Assessment
    - DSUR/PBRER Generation
    - Timeliness Monitoring
    - SOP Compliance
    - Audit Defense Binder
    - Duplicate Signal Detection
    - Portfolio Trend Integration
    """
    
    signal_id: str
    drug_name: str
    reaction_name: str
    
    # Core lifecycle events
    triage_event: Optional[TimelineEvent] = None  # Initial signal triage
    assessment_event: Optional[TimelineEvent] = None  # Signal assessment started
    evaluation_event: Optional[TimelineEvent] = None  # Evaluation completed
    decision_event: Optional[TimelineEvent] = None  # Decision made (validated/closed/etc.)
    capa_event: Optional[TimelineEvent] = None  # CAPA actions initiated
    label_event: Optional[TimelineEvent] = None  # Label update completed
    close_event: Optional[TimelineEvent] = None  # Signal closed
    
    # Supporting evidence
    trend_alerts: List[Dict[str, Any]] = field(default_factory=list)  # Trend alert findings
    subgroup_findings: List[Dict[str, Any]] = field(default_factory=list)  # Subgroup analysis
    clustering_findings: List[Dict[str, Any]] = field(default_factory=list)  # Case clustering results
    benefit_risk_summary: Optional[Dict[str, Any]] = None  # Benefit-risk assessment
    governance_flags: List[Dict[str, Any]] = field(default_factory=list)  # Governance findings
    sop_findings: List[Dict[str, Any]] = field(default_factory=list)  # SOP compliance findings
    inspector_risks: List[Dict[str, Any]] = field(default_factory=list)  # Inspector-identified risks
    
    # Timeliness & quality metrics
    sla_violations: List[Dict[str, Any]] = field(default_factory=list)  # SLA violations
    missing_artifacts: List[str] = field(default_factory=list)  # Missing required artifacts
    lifecycle_score: Optional[float] = None  # Overall lifecycle health score (0-100)
    
    # Confidence & risk indicators
    signal_confidence_score: Optional[float] = None  # Signal confidence (0-100)
    signal_priority_score: Optional[float] = None  # Signal priority score (0-100)
    
    # Hybrid compute flags
    summarized: bool = False  # Whether this is a summarized (light) version
    full_server_analysis_complete: bool = False  # Whether full server analysis is done
    
    # Additional metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    version: int = 1  # Timeline version for tracking changes
    
    def __post_init__(self):
        """Initialize timestamps if not provided."""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    def as_dict(self) -> Dict[str, Any]:
        """Convert entire timeline to a serializable dictionary."""
        return {
            "signal_id": self.signal_id,
            "drug_name": self.drug_name,
            "reaction_name": self.reaction_name,
            "triage_event": self._event_to_dict(self.triage_event),
            "assessment_event": self._event_to_dict(self.assessment_event),
            "evaluation_event": self._event_to_dict(self.evaluation_event),
            "decision_event": self._event_to_dict(self.decision_event),
            "capa_event": self._event_to_dict(self.capa_event),
            "label_event": self._event_to_dict(self.label_event),
            "close_event": self._event_to_dict(self.close_event),
            "trend_alerts": self.trend_alerts,
            "subgroup_findings": self.subgroup_findings,
            "clustering_findings": self.clustering_findings,
            "benefit_risk_summary": self.benefit_risk_summary,
            "governance_flags": self.governance_flags,
            "sop_findings": self.sop_findings,
            "inspector_risks": self.inspector_risks,
            "sla_violations": self.sla_violations,
            "missing_artifacts": self.missing_artifacts,
            "lifecycle_score": self.lifecycle_score,
            "signal_confidence_score": self.signal_confidence_score,
            "signal_priority_score": self.signal_priority_score,
            "summarized": self.summarized,
            "full_server_analysis_complete": self.full_server_analysis_complete,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "version": self.version
        }
    
    @staticmethod
    def _event_to_dict(event: Optional[TimelineEvent]) -> Optional[Dict[str, Any]]:
        """Convert TimelineEvent to dictionary."""
        if not event:
            return None
        return event.to_dict()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SignalLifecycleTimeline":
        """Create SignalLifecycleTimeline from dictionary."""
        # Parse timestamps
        created_at = None
        if data.get("created_at"):
            if isinstance(data["created_at"], str):
                created_at = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
            elif isinstance(data["created_at"], datetime):
                created_at = data["created_at"]
        
        updated_at = None
        if data.get("updated_at"):
            if isinstance(data["updated_at"], str):
                updated_at = datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))
            elif isinstance(data["updated_at"], datetime):
                updated_at = data["updated_at"]
        
        # Parse events
        triage_event = TimelineEvent.from_dict(data["triage_event"]) if data.get("triage_event") else None
        assessment_event = TimelineEvent.from_dict(data["assessment_event"]) if data.get("assessment_event") else None
        evaluation_event = TimelineEvent.from_dict(data["evaluation_event"]) if data.get("evaluation_event") else None
        decision_event = TimelineEvent.from_dict(data["decision_event"]) if data.get("decision_event") else None
        capa_event = TimelineEvent.from_dict(data["capa_event"]) if data.get("capa_event") else None
        label_event = TimelineEvent.from_dict(data["label_event"]) if data.get("label_event") else None
        close_event = TimelineEvent.from_dict(data["close_event"]) if data.get("close_event") else None
        
        return cls(
            signal_id=data.get("signal_id", ""),
            drug_name=data.get("drug_name", ""),
            reaction_name=data.get("reaction_name", ""),
            triage_event=triage_event,
            assessment_event=assessment_event,
            evaluation_event=evaluation_event,
            decision_event=decision_event,
            capa_event=capa_event,
            label_event=label_event,
            close_event=close_event,
            trend_alerts=data.get("trend_alerts", []),
            subgroup_findings=data.get("subgroup_findings", []),
            clustering_findings=data.get("clustering_findings", []),
            benefit_risk_summary=data.get("benefit_risk_summary"),
            governance_flags=data.get("governance_flags", []),
            sop_findings=data.get("sop_findings", []),
            inspector_risks=data.get("inspector_risks", []),
            sla_violations=data.get("sla_violations", []),
            missing_artifacts=data.get("missing_artifacts", []),
            lifecycle_score=data.get("lifecycle_score"),
            signal_confidence_score=data.get("signal_confidence_score"),
            signal_priority_score=data.get("signal_priority_score"),
            summarized=data.get("summarized", False),
            full_server_analysis_complete=data.get("full_server_analysis_complete", False),
            created_at=created_at,
            updated_at=updated_at,
            version=data.get("version", 1)
        )
    
    def to_json(self) -> str:
        """Serialize timeline to JSON string."""
        return json.dumps(self.as_dict(), default=str, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> "SignalLifecycleTimeline":
        """Deserialize timeline from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def get_event_sequence(self) -> List[TimelineEvent]:
        """
        Get all events in chronological order.
        
        Returns:
            List of TimelineEvent objects sorted by timestamp
        """
        events = []
        
        if self.triage_event:
            events.append(self.triage_event)
        if self.assessment_event:
            events.append(self.assessment_event)
        if self.evaluation_event:
            events.append(self.evaluation_event)
        if self.decision_event:
            events.append(self.decision_event)
        if self.capa_event:
            events.append(self.capa_event)
        if self.label_event:
            events.append(self.label_event)
        if self.close_event:
            events.append(self.close_event)
        
        # Sort by timestamp (None timestamps go to end)
        events.sort(key=lambda e: e.timestamp if e.timestamp else datetime.max)
        
        return events
    
    def get_lifecycle_stage(self) -> str:
        """
        Determine current lifecycle stage based on events.
        
        Returns:
            Current stage: "New", "Triage", "Assessment", "Evaluation", "Decision", "CAPA", "Label", "Closed"
        """
        if self.close_event:
            return "Closed"
        if self.label_event:
            return "Label Update"
        if self.capa_event:
            return "CAPA"
        if self.decision_event:
            return "Decision"
        if self.evaluation_event:
            return "Evaluation"
        if self.assessment_event:
            return "Assessment"
        if self.triage_event:
            return "Triage"
        return "New"
    
    def update_timestamp(self):
        """Update the updated_at timestamp to now."""
        self.updated_at = datetime.now()
        self.version += 1

