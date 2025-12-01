"""
Governance PDF Generator (CHUNK 6.21.1 - Part 13)
Generates regulatory-ready PDF documents for signal governance files.
"""
import datetime
from typing import Dict, Any, Optional
from pathlib import Path

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib import colors
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from .signal_file_generator import SignalFileGenerator


class GovernancePDFGenerator:
    """
    Builds a regulatory-ready PDF containing:
    - Signal File
    - Compliance Checklist
    - Reviewer Assignments
    - Oversight Metrics
    - Risk Assessment (RPF)
    - Trend Alerts Summary
    """

    def __init__(self, dataset: Dict[str, Any]):
        """
        Initialize the PDF Generator.
        
        Args:
            dataset: Dictionary containing signals and data
        """
        if not REPORTLAB_AVAILABLE:
            raise ImportError(
                "reportlab is required for PDF generation. "
                "Install it with: pip install reportlab"
            )
        
        self.dataset = dataset
        self.signal_file = SignalFileGenerator(dataset)
        self.styles = getSampleStyleSheet()
        
        # Create custom styles
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles for the PDF."""
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=12,
        ))
        self.styles.add(ParagraphStyle(
            name='BodyText',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=14,
        ))

    def generate_pdf(self, signal_id: str, output_path: str) -> str:
        """
        Generate complete PDF for a signal.
        
        Args:
            signal_id: Signal identifier
            output_path: Output file path
            
        Returns:
            Path to generated PDF
        """
        story = []
        
        # Generate signal file data
        signal_data = self.signal_file.generate_signal_file(signal_id)
        
        if "error" in signal_data:
            raise ValueError(f"Signal not found: {signal_data.get('error')}")
        
        # Title page
        story.append(Paragraph(
            "<b>Signal Governance Report</b>",
            self.styles["Title"]
        ))
        story.append(Spacer(1, 12))
        story.append(Paragraph(
            f"Generated at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}",
            self.styles["Normal"]
        ))
        story.append(Spacer(1, 12))
        
        # Signal Overview
        story.append(Paragraph("<b>1. Signal Overview</b>", self.styles["CustomHeading"]))
        overview = signal_data.get("overview", {})
        evidence = signal_data.get("evidence_package", {})
        
        overview_items = [
            ("Drug", evidence.get("drug", overview.get("drug", "Unknown"))),
            ("Reaction", evidence.get("reaction", overview.get("reaction", "Unknown"))),
            ("Cases", str(evidence.get("cases", overview.get("cases", 0)))),
            ("Serious Cases", str(evidence.get("serious_cases", overview.get("serious_cases", 0)))),
            ("Fatal Cases", str(evidence.get("fatal_cases", overview.get("fatal_cases", 0)))),
            ("Lifecycle", evidence.get("lifecycle", overview.get("lifecycle", "Unknown"))),
            ("Detected On", evidence.get("detected_on", overview.get("detected_on", "Unknown"))),
        ]
        
        for key, value in overview_items:
            story.append(Paragraph(f"<b>{key}:</b> {value}", self.styles["BodyText"]))
        
        story.append(Spacer(1, 12))
        story.append(PageBreak())
        
        # Trend Alerts Summary
        story.append(Paragraph("<b>2. Trend Alerts Summary</b>", self.styles["CustomHeading"]))
        trends = signal_data.get("trends", {})
        
        alerts = trends.get("alerts", [])
        if alerts:
            for alert in alerts[:10]:  # Limit to first 10
                if isinstance(alert, dict):
                    title = alert.get("title", alert.get("summary", "Alert"))
                    severity = alert.get("severity", "info")
                    summary = alert.get("summary", "")
                    story.append(Paragraph(
                        f"<b>{severity.upper()}: {title}</b><br/>{summary}",
                        self.styles["BodyText"]
                    ))
                    story.append(Spacer(1, 6))
        else:
            story.append(Paragraph("No significant alerts detected.", self.styles["BodyText"]))
        
        story.append(Spacer(1, 12))
        story.append(PageBreak())
        
        # Compliance Checklist
        story.append(Paragraph("<b>3. Compliance Checklist (GVP / FDA / MHRA)</b>", self.styles["CustomHeading"]))
        compliance = signal_data.get("compliance", {})
        checklist = compliance.get("checklist", [])
        
        if checklist:
            table_data = [["Requirement", "Category", "Regulation", "Status"]]
            
            for item in checklist:
                requirement = item.get("text", "")
                category = item.get("category", "")
                regulation = item.get("regulation", "")
                completed = item.get("completed", False)
                status = "✓ Passed" if completed else "✗ Gap"
                
                table_data.append([requirement, category, regulation, status])
            
            table = Table(table_data, colWidths=[3*inch, 1.5*inch, 1.5*inch, 1*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#3B82F6")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            story.append(table)
            
            # Compliance score
            score = compliance.get("score", 0)
            story.append(Spacer(1, 12))
            story.append(Paragraph(
                f"<b>Overall Compliance Score: {score:.1f}/100</b>",
                self.styles["BodyText"]
            ))
        else:
            story.append(Paragraph("No compliance checklist available.", self.styles["BodyText"]))
        
        story.append(Spacer(1, 12))
        story.append(PageBreak())
        
        # Risk Profile
        story.append(Paragraph("<b>4. Risk Assessment (RPF)</b>", self.styles["CustomHeading"]))
        risk_profile = signal_data.get("risk_profile", {})
        
        risk_items = [
            ("RPF Score", str(risk_profile.get("rpf_score", 0))),
            ("Risk Level", str(risk_profile.get("risk_level", "Low"))),
        ]
        
        sub_scores = risk_profile.get("sub_scores", {})
        if sub_scores:
            story.append(Paragraph("<b>Sub-Scores:</b>", self.styles["BodyText"]))
            for key, value in sub_scores.items():
                story.append(Paragraph(
                    f"  • {key.replace('_', ' ').title()}: {value:.2f}",
                    self.styles["BodyText"]
                ))
        
        for key, value in risk_items:
            story.append(Paragraph(f"<b>{key}:</b> {value}", self.styles["BodyText"]))
        
        story.append(Spacer(1, 12))
        story.append(PageBreak())
        
        # Reviewer Assignment
        story.append(Paragraph("<b>5. Reviewer Assignment</b>", self.styles["CustomHeading"]))
        reviewer = signal_data.get("reviewer_assignment", {})
        
        reviewer_name = reviewer.get("reviewer", "Unassigned")
        story.append(Paragraph(f"<b>Assigned Reviewer:</b> {reviewer_name}", self.styles["BodyText"]))
        
        reasons = reviewer.get("reason", [])
        if isinstance(reasons, list) and reasons:
            story.append(Paragraph("<b>Assignment Reasons:</b>", self.styles["BodyText"]))
            for reason in reasons:
                story.append(Paragraph(f"  • {reason}", self.styles["BodyText"]))
        elif isinstance(reasons, str):
            story.append(Paragraph(f"<b>Reason:</b> {reasons}", self.styles["BodyText"]))
        
        workload_status = reviewer.get("workload_status", "unknown")
        story.append(Paragraph(f"<b>Workload Status:</b> {workload_status}", self.styles["BodyText"]))
        
        story.append(Spacer(1, 12))
        story.append(PageBreak())
        
        # Follow-Up Plan
        story.append(Paragraph("<b>6. Follow-Up Plan</b>", self.styles["CustomHeading"]))
        followup = signal_data.get("followup_plan", {})
        
        steps = followup.get("steps", [])
        if isinstance(steps, list):
            for step in steps:
                story.append(Paragraph(f"• {step}", self.styles["BodyText"]))
        else:
            story.append(Paragraph(str(steps), self.styles["BodyText"]))
        
        priority = followup.get("priority", "Medium")
        timeline = followup.get("timeline", "")
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"<b>Priority:</b> {priority}", self.styles["BodyText"]))
        if timeline:
            story.append(Paragraph(f"<b>Timeline:</b> {timeline}", self.styles["BodyText"]))
        
        story.append(Spacer(1, 12))
        story.append(PageBreak())
        
        # AI Summary
        story.append(Paragraph("<b>7. AI Summary (Regulatory Style)</b>", self.styles["CustomHeading"]))
        ai_summary = signal_data.get("ai_summary", "No summary available.")
        story.append(Paragraph(ai_summary, self.styles["BodyText"]))
        story.append(Spacer(1, 16))
        
        # Build the PDF
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        doc.build(story)
        
        return output_path

