"""
Inspector Report Panel (CHUNK 6.22.x Completion UI)
UI for generating and viewing mock inspection reports with PDF export.
"""
import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime

try:
    from src.ai.inspector_report_generator import MockInspectionReportGenerator, InspectionReport
    from src.ai.company_readiness_scorer import CompanyReadinessScorer, ReadinessScore
    REPORT_GENERATOR_AVAILABLE = True
except ImportError:
    REPORT_GENERATOR_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


def render_inspector_report_panel(
    governance_data: Optional[Dict[str, Any]] = None,
    signals: Optional[List[Dict[str, Any]]] = None,
    inspection_session: Optional[Dict[str, Any]] = None
) -> None:
    """
    Render inspector report generation panel.
    
    Args:
        governance_data: Governance package
        signals: List of signals
        inspection_session: Inspection Q&A session data
    """
    if not REPORT_GENERATOR_AVAILABLE:
        st.error("Inspector report generator not available.")
        return
    
    st.header("📄 Mock Inspection Report Generator")
    st.markdown("Generate FDA/EMA/MHRA-style inspection reports with findings and readiness assessment.")
    
    # Agency selection
    agency = st.selectbox(
        "Regulatory Agency",
        options=["FDA", "EMA", "MHRA", "PMDA"],
        help="Select agency style for the inspection report"
    )
    
    # Generate report
    if st.button("📋 Generate Inspection Report", type="primary"):
        with st.spinner(f"Generating {agency} inspection report..."):
            # Generate report
            generator = MockInspectionReportGenerator(agency=agency)
            report = generator.generate_report(
                governance_data=governance_data or {},
                signals=signals or [],
                inspection_session=inspection_session
            )
            
            # Calculate readiness score
            scorer = CompanyReadinessScorer()
            readiness = scorer.calculate_readiness(
                governance_data=governance_data or {},
                signals=signals or [],
                findings=[f.to_dict() for f in report.findings]
            )
            
            st.session_state.inspection_report = report
            st.session_state.readiness_score = readiness
            st.success(f"Report generated! Readiness Score: {readiness.overall_score:.1f}/100 ({readiness.readiness_level})")
    
    # Display report if available
    if "inspection_report" in st.session_state:
        report = st.session_state.inspection_report
        readiness = st.session_state.get("readiness_score")
        
        # Readiness Score Display
        if readiness:
            st.subheader("🏆 Company Readiness Score")
            
            col1, col2, col3, col4 = st.columns(4)
            
            level_colors = {
                "excellent": "🟢",
                "good": "🟡",
                "fair": "🟠",
                "poor": "🔴"
            }
            
            col1.metric(
                "Overall Score",
                f"{readiness.overall_score:.1f}/100",
                delta=f"{readiness.overall_score - 85:.1f}" if readiness.overall_score > 85 else None
            )
            
            col2.metric("Critical Findings", readiness.critical_findings_count)
            col3.metric("Major Findings", readiness.major_findings_count)
            col4.metric("Minor Findings", readiness.minor_findings_count)
            
            # Component scores
            st.markdown("#### Component Scores")
            
            component_cols = st.columns(6)
            component_cols[0].metric("Data Quality", f"{readiness.data_quality_score:.0f}")
            component_cols[1].metric("Procedures", f"{readiness.procedures_score:.0f}")
            component_cols[2].metric("Timeliness", f"{readiness.timeliness_score:.0f}")
            component_cols[3].metric("Documentation", f"{readiness.documentation_score:.0f}")
            component_cols[4].metric("Governance", f"{readiness.governance_score:.0f}")
            component_cols[5].metric("Evidence", f"{readiness.evidence_strength_score:.0f}")
            
            st.markdown(f"**Readiness Level:** {level_colors.get(readiness.readiness_level, '⚪')} {readiness.readiness_level.upper()}")
        
        st.markdown("---")
        
        # Report Header
        st.subheader(f"{report.report_type}")
        st.write(f"**Agency:** {report.agency}")
        st.write(f"**Inspection Date:** {report.inspection_date}")
        st.write(f"**Company:** {report.company_name}")
        
        st.markdown("---")
        
        # Findings
        st.subheader("🔍 Inspection Findings")
        
        if report.findings:
            for i, finding in enumerate(report.findings, 1):
                severity_colors = {
                    "critical": "🔴",
                    "major": "🟠",
                    "minor": "🟡",
                    "observation": "⚪"
                }
                
                with st.expander(f"{severity_colors.get(finding.severity, '⚪')} Finding {i}: {finding.category.upper()} - {finding.severity.upper()}"):
                    st.write(f"**Description:** {finding.description}")
                    st.write(f"**Regulatory Basis:** {finding.regulatory_basis}")
                    st.write(f"**Evidence:**")
                    for evidence in finding.evidence:
                        st.write(f"- {evidence}")
                    st.write(f"**Recommended Action:** {finding.recommended_action}")
                    st.write(f"**Impact Assessment:** {finding.impact_assessment}")
        else:
            st.success("✅ No findings identified. Excellent compliance!")
        
        st.markdown("---")
        
        # Overall Assessment
        st.subheader("📝 Overall Assessment")
        st.write(report.overall_assessment)
        
        st.markdown("---")
        
        # Recommendations
        if report.recommendations:
            st.subheader("💡 Recommendations")
            for i, rec in enumerate(report.recommendations, 1):
                st.write(f"{i}. {rec}")
        
        st.markdown("---")
        
        # Export Options
        st.subheader("💾 Export Report")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Text export
            report_text = _format_report_text(report)
            st.download_button(
                label="📥 Download Report (TXT)",
                data=report_text,
                file_name=f"inspection_report_{report.agency}_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain"
            )
        
        with col2:
            # PDF export (if available)
            if REPORTLAB_AVAILABLE:
                if st.button("📄 Generate PDF Report"):
                    with st.spinner("Generating PDF..."):
                        pdf_data = _generate_pdf_report(report, readiness)
                        st.download_button(
                            label="📥 Download PDF",
                            data=pdf_data,
                            file_name=f"inspection_report_{report.agency}_{datetime.now().strftime('%Y%m%d')}.pdf",
                            mime="application/pdf"
                        )
            else:
                st.info("PDF generation requires reportlab package")


def _format_report_text(report: InspectionReport) -> str:
    """Format report as plain text."""
    lines = [
        f"{report.report_type}",
        f"AGENCY: {report.agency}",
        f"INSPECTION DATE: {report.inspection_date}",
        f"COMPANY: {report.company_name}",
        "",
        "=" * 80,
        "",
        "FINDINGS:",
        ""
    ]
    
    for i, finding in enumerate(report.findings, 1):
        lines.append(f"Finding {i} ({finding.severity.upper()}):")
        lines.append(f"  Category: {finding.category}")
        lines.append(f"  Description: {finding.description}")
        lines.append(f"  Regulatory Basis: {finding.regulatory_basis}")
        lines.append(f"  Evidence: {'; '.join(finding.evidence)}")
        lines.append(f"  Recommended Action: {finding.recommended_action}")
        lines.append("")
    
    lines.extend([
        "=" * 80,
        "",
        "OVERALL ASSESSMENT:",
        report.overall_assessment,
        "",
        "RECOMMENDATIONS:",
        ""
    ])
    
    for i, rec in enumerate(report.recommendations, 1):
        lines.append(f"{i}. {rec}")
    
    return "\n".join(lines)


def _generate_pdf_report(report: InspectionReport, readiness: Optional[ReadinessScore]) -> bytes:
    """Generate PDF report (requires reportlab)."""
    from io import BytesIO
    
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, height - 72, report.report_type)
    
    # Header info
    y = height - 100
    c.setFont("Helvetica", 12)
    c.drawString(72, y, f"Agency: {report.agency}")
    y -= 20
    c.drawString(72, y, f"Inspection Date: {report.inspection_date}")
    y -= 20
    c.drawString(72, y, f"Company: {report.company_name}")
    
    # Readiness score
    if readiness:
        y -= 30
        c.setFont("Helvetica-Bold", 14)
        c.drawString(72, y, f"Company Readiness Score: {readiness.overall_score:.1f}/100")
        y -= 20
        c.setFont("Helvetica", 10)
        c.drawString(72, y, f"Level: {readiness.readiness_level.upper()}")
    
    # Findings
    y -= 40
    c.setFont("Helvetica-Bold", 14)
    c.drawString(72, y, "Findings:")
    y -= 20
    
    c.setFont("Helvetica", 10)
    for finding in report.findings[:10]:  # Limit to 10 for PDF
        if y < 100:
            c.showPage()
            y = height - 72
        
        c.drawString(72, y, f"Finding {finding.finding_id}: {finding.description[:60]}...")
        y -= 15
    
    c.save()
    buffer.seek(0)
    return buffer.read()

