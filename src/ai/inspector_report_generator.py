"""
Mock Inspection Report Generator (CHUNK 6.22.x Completion)
Generates FDA/EMA/MHRA-style mock inspection reports with findings and annotations.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class InspectionFinding:
    """Represents an inspection finding."""
    finding_id: str
    severity: str  # "critical", "major", "minor", "observation"
    category: str  # "data_quality", "procedures", "timeliness", "documentation"
    description: str
    regulatory_basis: str
    evidence: List[str]
    recommended_action: str
    impact_assessment: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class InspectionReport:
    """Complete mock inspection report."""
    report_type: str  # "FDA 483", "EMA Inspection Report", "MHRA Findings"
    agency: str
    inspection_date: str
    company_name: str
    findings: List[InspectionFinding]
    overall_assessment: str
    readiness_score: float  # 0-100
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_type": self.report_type,
            "agency": self.agency,
            "inspection_date": self.inspection_date,
            "company_name": self.company_name,
            "findings": [f.to_dict() for f in self.findings],
            "overall_assessment": self.overall_assessment,
            "readiness_score": self.readiness_score,
            "recommendations": self.recommendations
        }


class MockInspectionReportGenerator:
    """
    Generates mock regulatory inspection reports.
    
    Creates FDA 483-style, EMA Inspection Report, or MHRA Findings documents
    with realistic findings based on signal governance data.
    """
    
    def __init__(self, agency: str = "FDA"):
        """
        Initialize report generator.
        
        Args:
            agency: Regulatory agency ("FDA", "EMA", "MHRA", "PMDA")
        """
        self.agency = agency.upper()
        self.report_templates = {
            "FDA": {
                "type": "FDA Form 483",
                "template": self._fda_483_template
            },
            "EMA": {
                "type": "EMA Inspection Report",
                "template": self._ema_template
            },
            "MHRA": {
                "type": "MHRA Inspection Findings",
                "template": self._mhra_template
            },
            "PMDA": {
                "type": "PMDA Inspection Report",
                "template": self._pmda_template
            }
        }
    
    def generate_report(
        self,
        governance_data: Dict[str, Any],
        signals: Optional[List[Dict[str, Any]]] = None,
        inspection_session: Optional[Dict[str, Any]] = None
    ) -> InspectionReport:
        """
        Generate complete mock inspection report.
        
        Args:
            governance_data: Governance package with compliance data
            signals: List of signals under review
            inspection_session: Optional inspection Q&A session data
            
        Returns:
            Complete InspectionReport object
        """
        # Analyze governance data to identify findings
        findings = self._identify_findings(governance_data, signals, inspection_session)
        
        # Calculate readiness score
        readiness_score = self._calculate_readiness_score(findings, governance_data)
        
        # Generate overall assessment
        overall_assessment = self._generate_assessment(findings, readiness_score)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(findings)
        
        # Get template
        template = self.report_templates.get(self.agency, self.report_templates["FDA"])
        
        return InspectionReport(
            report_type=template["type"],
            agency=self.agency,
            inspection_date=datetime.now().strftime("%Y-%m-%d"),
            company_name=governance_data.get("company_name", "Company Name"),
            findings=findings,
            overall_assessment=overall_assessment,
            readiness_score=readiness_score,
            recommendations=recommendations
        )
    
    def _identify_findings(
        self,
        governance_data: Dict[str, Any],
        signals: Optional[List[Dict[str, Any]]],
        inspection_session: Optional[Dict[str, Any]]
    ) -> List[InspectionFinding]:
        """Identify inspection findings from governance data."""
        findings = []
        
        # Check for timeline violations
        timeline_deviations = governance_data.get("timeline_deviations", [])
        for deviation in timeline_deviations[:5]:  # Top 5
            findings.append(InspectionFinding(
                finding_id=f"FINDING-{len(findings)+1:03d}",
                severity="major" if deviation.get("days_late", 0) > 30 else "minor",
                category="timeliness",
                description=f"Signal assessment delayed by {deviation.get('days_late', 0)} days beyond regulatory timeline",
                regulatory_basis="FDA 21 CFR 314.80 requires timely signal assessment within 30 days",
                evidence=[f"Signal: {deviation.get('signal_name', 'Unknown')}", f"Due date: {deviation.get('due_date', 'N/A')}"],
                recommended_action="Implement automated timeline tracking and escalation process",
                impact_assessment="Moderate - delays in signal assessment may impact patient safety"
            ))
        
        # Check for missing documentation
        missing_docs = governance_data.get("missing_documentation", [])
        for doc in missing_docs[:3]:  # Top 3
            findings.append(InspectionFinding(
                finding_id=f"FINDING-{len(findings)+1:03d}",
                severity="major",
                category="documentation",
                description=f"Missing required documentation: {doc.get('document_type', 'Unknown')}",
                regulatory_basis="GVP Module IX requires complete signal evaluation documentation",
                evidence=[f"Signal: {doc.get('signal_name', 'Unknown')}", f"Missing: {doc.get('document_type', 'N/A')}"],
                recommended_action="Complete missing documentation and establish review process",
                impact_assessment="High - incomplete documentation may result in regulatory action"
            ))
        
        # Check SOP compliance gaps
        sop_gaps = governance_data.get("sop_gaps", [])
        for gap in sop_gaps[:3]:  # Top 3
            findings.append(InspectionFinding(
                finding_id=f"FINDING-{len(findings)+1:03d}",
                severity="minor",
                category="procedures",
                description=f"SOP compliance gap: {gap.get('gap_description', 'Unknown')}",
                regulatory_basis="FDA requires documented procedures for signal management",
                evidence=[f"Area: {gap.get('area', 'Unknown')}", f"Gap: {gap.get('gap_description', 'N/A')}"],
                recommended_action="Update SOPs and provide training to ensure compliance",
                impact_assessment="Low - procedural gap, not a safety issue"
            ))
        
        return findings
    
    def _calculate_readiness_score(
        self,
        findings: List[InspectionFinding],
        governance_data: Dict[str, Any]
    ) -> float:
        """Calculate company readiness score (0-100)."""
        base_score = 100.0
        
        # Deduct for findings
        for finding in findings:
            if finding.severity == "critical":
                base_score -= 20
            elif finding.severity == "major":
                base_score -= 10
            elif finding.severity == "minor":
                base_score -= 5
            else:
                base_score -= 2
        
        # Deduct for governance gaps
        timeline_violations = len(governance_data.get("timeline_deviations", []))
        base_score -= min(30, timeline_violations * 5)
        
        missing_docs = len(governance_data.get("missing_documentation", []))
        base_score -= min(20, missing_docs * 5)
        
        # Ensure score is between 0 and 100
        return max(0.0, min(100.0, base_score))
    
    def _generate_assessment(self, findings: List[InspectionFinding], readiness_score: float) -> str:
        """Generate overall assessment narrative."""
        critical_count = sum(1 for f in findings if f.severity == "critical")
        major_count = sum(1 for f in findings if f.severity == "major")
        
        if readiness_score >= 90:
            assessment = f"Inspection readiness is excellent. Overall score: {readiness_score:.1f}/100. "
            assessment += f"Minor observations noted ({len(findings)} findings). System demonstrates strong regulatory compliance."
        elif readiness_score >= 70:
            assessment = f"Inspection readiness is good. Overall score: {readiness_score:.1f}/100. "
            assessment += f"Some areas require improvement ({major_count} major, {len(findings) - major_count} minor findings). "
            assessment += "Addressing identified gaps will strengthen compliance posture."
        else:
            assessment = f"Inspection readiness needs improvement. Overall score: {readiness_score:.1f}/100. "
            assessment += f"Significant findings identified ({critical_count} critical, {major_count} major findings). "
            assessment += "Immediate corrective action recommended to address compliance gaps."
        
        return assessment
    
    def _generate_recommendations(self, findings: List[InspectionFinding]) -> List[str]:
        """Generate recommendations based on findings."""
        recommendations = []
        
        # Group by category
        categories = {}
        for finding in findings:
            cat = finding.category
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(finding)
        
        # Generate recommendations per category
        if "timeliness" in categories:
            recommendations.append("Implement automated timeline tracking with escalation alerts for overdue assessments")
        
        if "documentation" in categories:
            recommendations.append("Establish comprehensive documentation checklist and review process for all signals")
        
        if "procedures" in categories:
            recommendations.append("Review and update SOPs to ensure alignment with regulatory requirements")
        
        if "data_quality" in categories:
            recommendations.append("Implement data quality validation checks and automated error detection")
        
        return recommendations
    
    def _fda_483_template(self, report: InspectionReport) -> str:
        """Generate FDA 483-style report text."""
        lines = [
            f"FORM FDA 483",
            f"INSPECTIONAL OBSERVATIONS",
            "",
            f"INSPECTION DATE: {report.inspection_date}",
            f"COMPANY: {report.company_name}",
            "",
            "OBSERVATIONS:",
            ""
        ]
        
        for finding in report.findings:
            lines.append(f"1. {finding.description}")
            lines.append(f"   Regulatory Basis: {finding.regulatory_basis}")
            lines.append(f"   Evidence: {'; '.join(finding.evidence[:2])}")
            lines.append("")
        
        lines.append("END OF OBSERVATIONS")
        return "\n".join(lines)
    
    def _ema_template(self, report: InspectionReport) -> str:
        """Generate EMA-style report text."""
        lines = [
            f"EMA INSPECTION REPORT",
            f"Date: {report.inspection_date}",
            f"Company: {report.company_name}",
            "",
            "FINDINGS:",
            ""
        ]
        
        for finding in report.findings:
            lines.append(f"Finding {finding.finding_id}: {finding.description}")
            lines.append(f"Severity: {finding.severity.upper()}")
            lines.append(f"Category: {finding.category}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _mhra_template(self, report: InspectionReport) -> str:
        """Generate MHRA-style report text."""
        return self._ema_template(report)  # Similar format
    
    def _pmda_template(self, report: InspectionReport) -> str:
        """Generate PMDA-style report text."""
        return self._ema_template(report)  # Similar format

