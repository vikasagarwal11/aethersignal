"""
Company Readiness Scorer (CHUNK 6.22.x Completion)
Calculates comprehensive company inspection readiness score.
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class ReadinessScore:
    """Company inspection readiness score breakdown."""
    overall_score: float  # 0-100
    data_quality_score: float
    procedures_score: float
    timeliness_score: float
    documentation_score: float
    governance_score: float
    evidence_strength_score: float
    
    critical_findings_count: int
    major_findings_count: int
    minor_findings_count: int
    
    readiness_level: str  # "excellent", "good", "fair", "poor"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": self.overall_score,
            "data_quality_score": self.data_quality_score,
            "procedures_score": self.procedures_score,
            "timeliness_score": self.timeliness_score,
            "documentation_score": self.documentation_score,
            "governance_score": self.governance_score,
            "evidence_strength_score": self.evidence_strength_score,
            "critical_findings_count": self.critical_findings_count,
            "major_findings_count": self.major_findings_count,
            "minor_findings_count": self.minor_findings_count,
            "readiness_level": self.readiness_level
        }


class CompanyReadinessScorer:
    """
    Calculates comprehensive company inspection readiness score.
    
    Evaluates:
    - Data quality
    - Procedural compliance
    - Timeliness
    - Documentation completeness
    - Governance maturity
    - Evidence strength
    """
    
    def __init__(self):
        """Initialize readiness scorer."""
        pass
    
    def calculate_readiness(
        self,
        governance_data: Dict[str, Any],
        signals: Optional[List[Dict[str, Any]]] = None,
        findings: Optional[List[Dict[str, Any]]] = None
    ) -> ReadinessScore:
        """
        Calculate comprehensive readiness score.
        
        Args:
            governance_data: Governance package
            signals: List of signals
            findings: Optional inspection findings
            
        Returns:
            ReadinessScore object
        """
        # Calculate component scores
        data_quality = self._score_data_quality(governance_data, signals)
        procedures = self._score_procedures(governance_data)
        timeliness = self._score_timeliness(governance_data)
        documentation = self._score_documentation(governance_data)
        governance = self._score_governance(governance_data)
        evidence = self._score_evidence_strength(governance_data, signals)
        
        # Count findings
        critical_count = len([f for f in (findings or []) if f.get("severity") == "critical"])
        major_count = len([f for f in (findings or []) if f.get("severity") == "major"])
        minor_count = len([f for f in (findings or []) if f.get("severity") == "minor"])
        
        # Calculate weighted overall score
        overall = (
            data_quality * 0.15 +
            procedures * 0.15 +
            timeliness * 0.25 +
            documentation * 0.20 +
            governance * 0.15 +
            evidence * 0.10
        )
        
        # Deduct for findings
        overall -= (critical_count * 10)
        overall -= (major_count * 5)
        overall -= (minor_count * 2)
        
        overall = max(0.0, min(100.0, overall))
        
        # Determine readiness level
        if overall >= 90:
            level = "excellent"
        elif overall >= 75:
            level = "good"
        elif overall >= 60:
            level = "fair"
        else:
            level = "poor"
        
        return ReadinessScore(
            overall_score=overall,
            data_quality_score=data_quality,
            procedures_score=procedures,
            timeliness_score=timeliness,
            documentation_score=documentation,
            governance_score=governance,
            evidence_strength_score=evidence,
            critical_findings_count=critical_count,
            major_findings_count=major_count,
            minor_findings_count=minor_count,
            readiness_level=level
        )
    
    def _score_data_quality(self, governance_data: Dict[str, Any], signals: Optional[List[Dict[str, Any]]]) -> float:
        """Score data quality (0-100)."""
        # Check for data quality issues
        quality_issues = governance_data.get("data_quality_issues", [])
        base_score = 100.0
        
        # Deduct for each issue
        base_score -= len(quality_issues) * 5
        
        # Check signal data completeness
        if signals:
            incomplete_signals = sum(1 for s in signals if not s.get("complete", True))
            base_score -= (incomplete_signals / len(signals)) * 20
        
        return max(0.0, min(100.0, base_score))
    
    def _score_procedures(self, governance_data: Dict[str, Any]) -> float:
        """Score procedural compliance (0-100)."""
        base_score = 100.0
        
        # Check SOP gaps
        sop_gaps = len(governance_data.get("sop_gaps", []))
        base_score -= sop_gaps * 10
        
        # Check procedure compliance
        compliance_rate = governance_data.get("sop_compliance_rate", 100)
        base_score = min(base_score, compliance_rate)
        
        return max(0.0, min(100.0, base_score))
    
    def _score_timeliness(self, governance_data: Dict[str, Any]) -> float:
        """Score timeliness compliance (0-100)."""
        base_score = 100.0
        
        # Check timeline deviations
        deviations = governance_data.get("timeline_deviations", [])
        for deviation in deviations:
            days_late = deviation.get("days_late", 0)
            if days_late > 60:
                base_score -= 15
            elif days_late > 30:
                base_score -= 10
            elif days_late > 0:
                base_score -= 5
        
        # Check on-time rate
        on_time_rate = governance_data.get("on_time_completion_rate", 100)
        base_score = min(base_score, on_time_rate)
        
        return max(0.0, min(100.0, base_score))
    
    def _score_documentation(self, governance_data: Dict[str, Any]) -> float:
        """Score documentation completeness (0-100)."""
        base_score = 100.0
        
        # Check missing documentation
        missing_docs = len(governance_data.get("missing_documentation", []))
        base_score -= missing_docs * 10
        
        # Check documentation completeness rate
        doc_completeness = governance_data.get("documentation_completeness_rate", 100)
        base_score = min(base_score, doc_completeness)
        
        return max(0.0, min(100.0, base_score))
    
    def _score_governance(self, governance_data: Dict[str, Any]) -> float:
        """Score governance maturity (0-100)."""
        base_score = 100.0
        
        # Check governance gaps
        gaps = governance_data.get("governance_gaps", [])
        base_score -= len(gaps) * 8
        
        # Check SHMI score if available
        shmi_score = governance_data.get("shmi_score", 100)
        base_score = min(base_score, shmi_score)
        
        return max(0.0, min(100.0, base_score))
    
    def _score_evidence_strength(self, governance_data: Dict[str, Any], signals: Optional[List[Dict[str, Any]]]) -> float:
        """Score evidence strength (0-100)."""
        base_score = 100.0
        
        # Check signal confidence scores
        if signals:
            avg_confidence = sum(s.get("confidence_score", 50) for s in signals) / len(signals) if signals else 50
            base_score = avg_confidence
        
        return max(0.0, min(100.0, base_score))

