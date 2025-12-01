"""
Local CAPA Generator (CHUNK 7.11)
Browser-based Corrective & Preventive Actions generator.

Works offline to generate CAPA recommendations based on:
- Deviations
- Alerts
- Timeline violations
- Root cause analysis
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json


@dataclass
class CAPAAction:
    """Represents a CAPA action item."""
    action_type: str  # "corrective" or "preventive"
    description: str
    priority: str  # "high", "medium", "low"
    responsible: str
    due_date: str
    status: str  # "open", "in_progress", "completed"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_type": self.action_type,
            "description": self.description,
            "priority": self.priority,
            "responsible": self.responsible,
            "due_date": self.due_date,
            "status": self.status
        }


@dataclass
class CAPARecommendation:
    """Complete CAPA recommendation package."""
    issue_description: str
    root_cause_analysis: str
    corrective_actions: List[CAPAAction]
    preventive_actions: List[CAPAAction]
    severity: str
    impact: str
    timeline: str
    regulatory_justification: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "issue_description": self.issue_description,
            "root_cause_analysis": self.root_cause_analysis,
            "corrective_actions": [a.to_dict() for a in self.corrective_actions],
            "preventive_actions": [a.to_dict() for a in self.preventive_actions],
            "severity": self.severity,
            "impact": self.impact,
            "timeline": self.timeline,
            "regulatory_justification": self.regulatory_justification
        }


class LocalCAPAEngine:
    """
    Local CAPA generator for browser-based processing.
    
    Generates regulatory-compliant CAPA recommendations without server dependencies.
    """
    
    def __init__(self):
        """Initialize local CAPA engine."""
        pass
    
    def generate_capa(
        self,
        issue_type: str,
        description: str,
        deviations: Optional[List[Dict[str, Any]]] = None,
        alerts: Optional[List[Dict[str, Any]]] = None,
        timeline_violations: Optional[List[Dict[str, Any]]] = None
    ) -> CAPARecommendation:
        """
        Generate CAPA recommendation.
        
        Args:
            issue_type: Type of issue (e.g., "signal_delay", "missing_documentation")
            description: Description of the issue
            deviations: List of deviations
            alerts: List of alerts
            timeline_violations: List of timeline violations
            
        Returns:
            CAPARecommendation object
        """
        # Root cause analysis (5-Why approach)
        root_causes = self._perform_root_cause_analysis(issue_type, description, deviations, alerts, timeline_violations)
        
        # Generate corrective actions
        corrective_actions = self._generate_corrective_actions(root_causes, issue_type)
        
        # Generate preventive actions
        preventive_actions = self._generate_preventive_actions(root_causes, issue_type)
        
        # Determine severity and impact
        severity = self._determine_severity(deviations, alerts, timeline_violations)
        impact = self._determine_impact(issue_type, severity)
        
        # Generate timeline
        timeline = self._generate_timeline(severity, corrective_actions)
        
        # Regulatory justification
        regulatory_justification = self._generate_regulatory_justification(issue_type, severity)
        
        return CAPARecommendation(
            issue_description=description,
            root_cause_analysis=root_causes,
            corrective_actions=corrective_actions,
            preventive_actions=preventive_actions,
            severity=severity,
            impact=impact,
            timeline=timeline,
            regulatory_justification=regulatory_justification
        )
    
    def _perform_root_cause_analysis(
        self,
        issue_type: str,
        description: str,
        deviations: Optional[List[Dict[str, Any]]],
        alerts: Optional[List[Dict[str, Any]]],
        timeline_violations: Optional[List[Dict[str, Any]]]
    ) -> str:
        """Perform root cause analysis using 5-Why approach."""
        analysis = f"Root Cause Analysis for: {issue_type}\n\n"
        
        # Identify contributing factors
        factors = []
        
        if deviations:
            factors.append(f"- {len(deviations)} deviation(s) identified")
        
        if alerts:
            factors.append(f"- {len(alerts)} alert(s) raised")
        
        if timeline_violations:
            factors.append(f"- {len(timeline_violations)} timeline violation(s) detected")
        
        analysis += "Contributing Factors:\n" + "\n".join(factors) + "\n\n"
        
        # 5-Why path
        why_path = self._build_why_path(issue_type)
        analysis += "5-Why Analysis Path:\n" + why_path
        
        return analysis
    
    def _build_why_path(self, issue_type: str) -> str:
        """Build 5-Why analysis path."""
        templates = {
            "signal_delay": """1. Why was the signal delayed? → Missing automated alerts
2. Why were alerts missing? → Trend detection not configured
3. Why was trend detection not configured? → Process documentation incomplete
4. Why was documentation incomplete? → Training not provided
5. Why was training not provided? → Resource allocation issue""",
            
            "missing_documentation": """1. Why is documentation missing? → Process not followed
2. Why was process not followed? → Process unclear or inaccessible
3. Why is process unclear? → Documentation not updated
4. Why was documentation not updated? → No review process
5. Why is there no review process? → Governance gap identified""",
            
            "timeline_violation": """1. Why was timeline violated? → Review not completed on time
2. Why was review delayed? → Resource constraints
3. Why resource constraints? → Workload not balanced
4. Why workload not balanced? → Assignment process inefficient
5. Why inefficient assignment? → Need automated assignment system"""
        }
        
        return templates.get(issue_type, "Root cause analysis requires detailed investigation.")
    
    def _generate_corrective_actions(self, root_causes: str, issue_type: str) -> List[CAPAAction]:
        """Generate corrective actions."""
        actions = []
        
        if "signal_delay" in issue_type.lower():
            actions.append(CAPAAction(
                action_type="corrective",
                description="Configure automated trend alerts for all active signals",
                priority="high",
                responsible="Safety Systems Administrator",
                due_date=self._calculate_due_date(7),
                status="open"
            ))
            actions.append(CAPAAction(
                action_type="corrective",
                description="Immediately review all delayed signals and complete assessments",
                priority="high",
                responsible="Signal Management Team",
                due_date=self._calculate_due_date(14),
                status="open"
            ))
        
        if "documentation" in issue_type.lower():
            actions.append(CAPAAction(
                action_type="corrective",
                description="Complete missing documentation for all open signals",
                priority="medium",
                responsible="Signal Reviewers",
                due_date=self._calculate_due_date(21),
                status="open"
            ))
        
        if "timeline" in issue_type.lower():
            actions.append(CAPAAction(
                action_type="corrective",
                description="Reassign overdue reviews to available reviewers",
                priority="high",
                responsible="Governance Manager",
                due_date=self._calculate_due_date(3),
                status="open"
            ))
        
        return actions
    
    def _generate_preventive_actions(self, root_causes: str, issue_type: str) -> List[CAPAAction]:
        """Generate preventive actions."""
        actions = []
        
        actions.append(CAPAAction(
            action_type="preventive",
            description="Implement automated workflow notifications for timeline tracking",
            priority="medium",
            responsible="IT/Systems Team",
            due_date=self._calculate_due_date(60),
            status="open"
        ))
        
        actions.append(CAPAAction(
            action_type="preventive",
            description="Establish regular review process for signal management procedures",
            priority="medium",
            responsible="Quality Assurance",
            due_date=self._calculate_due_date(30),
            status="open"
        ))
        
        return actions
    
    def _determine_severity(
        self,
        deviations: Optional[List[Dict[str, Any]]],
        alerts: Optional[List[Dict[str, Any]]],
        timeline_violations: Optional[List[Dict[str, Any]]]
    ) -> str:
        """Determine severity level."""
        violation_count = (
            (len(deviations) if deviations else 0) +
            (len(alerts) if alerts else 0) +
            (len(timeline_violations) if timeline_violations else 0)
        )
        
        if violation_count >= 5:
            return "high"
        elif violation_count >= 2:
            return "medium"
        else:
            return "low"
    
    def _determine_impact(self, issue_type: str, severity: str) -> str:
        """Determine impact description."""
        if severity == "high":
            return "Regulatory compliance at risk. Potential inspection findings. Immediate action required."
        elif severity == "medium":
            return "Process efficiency and quality impacted. Corrective action needed within 30 days."
        else:
            return "Minor process deviation. Preventive action recommended."
    
    def _generate_timeline(self, severity: str, corrective_actions: List[CAPAAction]) -> str:
        """Generate timeline for CAPA completion."""
        if severity == "high":
            return "Immediate action required. Critical items due within 7 days. Full resolution within 30 days."
        elif severity == "medium":
            return "Corrective actions due within 14-30 days. Preventive actions within 60 days."
        else:
            return "Corrective actions within 30 days. Preventive actions within 90 days."
    
    def _generate_regulatory_justification(self, issue_type: str, severity: str) -> str:
        """Generate regulatory justification."""
        justifications = {
            "high": "FDA 21 CFR 314.80 and EMA GVP Module IX require timely signal detection and assessment. Delays may result in regulatory findings.",
            "medium": "ICH E2C(R2) and GVP Module VI specify requirements for signal management documentation and timelines.",
            "low": "Best practices recommend preventive actions to maintain process quality and regulatory readiness."
        }
        
        return justifications.get(severity, "Regulatory compliance requires appropriate corrective and preventive actions.")
    
    def _calculate_due_date(self, days_from_now: int) -> str:
        """Calculate due date."""
        due = datetime.now() + timedelta(days=days_from_now)
        return due.strftime("%Y-%m-%d")

