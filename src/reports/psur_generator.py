"""
PSUR/DSUR Generator (Refactored - No Placeholders)
Automated regulatory report generation with multi-tenant support.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import logging

from .psur_context import PSURContext, OrgProductConfig
from .psur_helpers import (
    load_unified_ae_data_for_period,
    compute_signal_summary,
    compute_literature_summary,
    summarize_trends_for_prompt,
    summarize_alignment_for_prompt
)
from src.org.org_profile_manager import load_org_product_config, get_current_tenant_id
from src.ai.medical_llm import call_medical_llm
from src.executive_dashboard.aggregator import ExecutiveAggregator

logger = logging.getLogger(__name__)


def build_psur_context(
    tenant_id: Optional[str],
    product: str,
    period_start: datetime,
    period_end: datetime
) -> PSURContext:
    """
    Build PSUR context from tenant, product, and period.
    
    Args:
        tenant_id: Organization identifier (if None, uses current user's org)
        product: Product/drug name
        period_start: Report period start
        period_end: Report period end
    
    Returns:
        PSURContext with all required data
    """
    if tenant_id is None:
        tenant_id = get_current_tenant_id()
    
    # Load org config
    org_config = load_org_product_config(tenant_id=tenant_id, product=product)
    
    # Load unified AE data
    unified_ae_data = load_unified_ae_data_for_period(
        period_start=period_start,
        period_end=period_end,
        drug=product,
        tenant_id=tenant_id
    )
    
    # Compute signal summary
    signals_summary = compute_signal_summary(unified_ae_data, drug=product)
    
    # Compute literature summary
    literature_summary = compute_literature_summary(product, period_start, period_end)
    
    # Build context
    ctx = PSURContext(
        tenant_id=tenant_id or "",
        product=product,
        org_config=org_config,
        unified_ae_data=unified_ae_data,
        signals_summary=signals_summary,
        literature_summary=literature_summary,
        period_start=period_start.isoformat(),
        period_end=period_end.isoformat()
    )
    
    # Validate context and log warnings
    warnings = ctx.validate()
    if warnings:
        logger.warning(f"PSUR context validation warnings for {product}: {warnings}")
    
    return ctx


# ============================================================================
# SECTION RENDERERS - ORG-CONFIG DRIVEN ([AUTO+MANUAL])
# ============================================================================

def render_section_marketing_auth(ctx: PSURContext) -> str:
    """Render Section 1: Marketing Authorization Status."""
    cfg = ctx.org_config
    if cfg and cfg.authorization_status:
        lines = [f"Marketing authorization status for {ctx.product}:"]
        for region, status in cfg.authorization_status.items():
            lines.append(f"- {region}: {status}")
        return "\n".join(lines)
    
    return (
        f"Marketing authorization status for {ctx.product} has not yet been configured "
        f"for your organization. You can populate this in the Regulatory Settings page."
    )


def render_section_safety_actions(ctx: PSURContext) -> str:
    """Render Section 2: Safety Actions Taken."""
    cfg = ctx.org_config
    if cfg and cfg.safety_actions:
        lines = ["Safety actions taken during the reporting period:"]
        for action in cfg.safety_actions:
            date = action.get("date", "")
            desc = action.get("description", "")
            lines.append(f"- {date}: {desc}")
        return "\n".join(lines)
    
    return "No organization-specific safety actions have been configured for this period."


def render_section_rmp_changes(ctx: PSURContext) -> str:
    """Render Section 3: RMP Changes."""
    cfg = ctx.org_config
    if cfg and cfg.rmp_changes:
        lines = ["Risk Management Plan (RMP) updates during the reporting period:"]
        for change in cfg.rmp_changes:
            date = change.get("date", "")
            desc = change.get("description", "")
            lines.append(f"- {date}: {desc}")
        return "\n".join(lines)
    
    return (
        "No RMP changes have been configured for this period. If changes occurred, "
        "please update them in the Regulatory Settings."
    )


def render_section_exposure(ctx: PSURContext) -> str:
    """Render Section 4: Estimated Exposure."""
    cfg = ctx.org_config
    
    # Try org config first
    if cfg and cfg.exposure_estimates:
        lines = ["Patient exposure estimates:"]
        for period, estimate in cfg.exposure_estimates.items():
            lines.append(f"- {period}: {estimate}")
        return "\n".join(lines)
    
    # Fallback: Use case counts as proxy
    try:
        df = ctx.unified_ae_data
        if not isinstance(df, pd.DataFrame):
            df = pd.DataFrame()
        
        if not df.empty:
            total_cases = len(df)
            return (
                f"Based on available case reports, {total_cases} adverse event cases were reported "
                f"during the reporting period. Note: This is not a direct measure of patient exposure. "
                f"Please configure exposure estimates in Regulatory Settings for accurate exposure data."
            )
    except Exception as e:
        logger.error(f"Error computing exposure proxy: {e}")
    
    return (
        "Patient exposure estimates have not been configured. Please update your Regulatory Settings "
        "to provide exposure data (e.g., patient-years, prescription counts)."
    )


# ============================================================================
# SECTION RENDERERS - DATA-DRIVEN ([AUTO])
# ============================================================================

def render_section_signals(ctx: PSURContext) -> Dict[str, Any]:
    """Render Section 5: Summary of Signals."""
    signals_summary = ctx.signals_summary
    
    signal_summaries = []
    for signal in signals_summary.get("top_signals", [])[:10]:
        signal_summaries.append({
            "drug": signal.get("drug", ctx.product),
            "reaction": signal.get("reaction", ""),
            "quantum_score": signal.get("quantum_score", 0.0),
            "gri_score": signal.get("gri_score", 0.0),
            "priority": signal.get("priority", "unknown"),
            "frequency": signal.get("frequency", 0),
            "evidence_summary": f"Evidence from {len(signals_summary.get('sources', {}))} sources"
        })
    
    return {
        "title": "Summary of Signals",
        "signals": signal_summaries,
        "total_signals": signals_summary.get("total_signals", 0),
        "total_cases": signals_summary.get("total_cases", 0)
    }


def render_section_trends(ctx: PSURContext) -> str:
    """Render trend analysis section."""
    try:
        df = ctx.unified_ae_data
        if not isinstance(df, pd.DataFrame) or df.empty:
            return "No adverse event reports were available for the selected reporting period."
        
        aggregator = ExecutiveAggregator()
        trends = aggregator.compute_trends(df, period="M")
        
        if trends.empty:
            return "No trend data available for the selected reporting period."
        
        first = trends.iloc[0]
        last = trends.iloc[-1]
        change = int(last["count"] - first["count"])
        direction = "increase" if change > 0 else "decrease" if change < 0 else "no net change"
        
        return (
            f"Across the reporting period ({ctx.period_start} to {ctx.period_end}), reported cases changed from "
            f"{int(first['count'])} in {first['period_str']} to {int(last['count'])} in {last['period_str']}, "
            f"representing a {direction} of {abs(change)} cases."
        )
    except Exception as e:
        logger.error(f"Error rendering trends: {e}")
        return "Trend analysis could not be generated due to data processing error."


def render_section_severity_distribution(ctx: PSURContext) -> str:
    """Render severity distribution section."""
    try:
        df = ctx.unified_ae_data
        if not isinstance(df, pd.DataFrame) or df.empty:
            return "No severity data available."
        
        if "severity_score" not in df.columns:
            return "Severity scoring not available for this dataset."
        
        severe_count = len(df[df["severity_score"] >= 0.7])
        moderate_count = len(df[(df["severity_score"] >= 0.4) & (df["severity_score"] < 0.7)])
        mild_count = len(df[df["severity_score"] < 0.4])
        total = len(df)
        
        return (
            f"Severity distribution across {total} reported cases:\n"
            f"- Severe (score ≥0.7): {severe_count} cases ({severe_count/total*100:.1f}%)\n"
            f"- Moderate (0.4-0.7): {moderate_count} cases ({moderate_count/total*100:.1f}%)\n"
            f"- Mild (<0.4): {mild_count} cases ({mild_count/total*100:.1f}%)"
        )
    except Exception as e:
        logger.error(f"Error rendering severity distribution: {e}")
        return "Severity distribution analysis could not be generated."


# ============================================================================
# SECTION RENDERERS - LLM-GENERATED ([AUTO])
# ============================================================================

def render_section_benefit_risk(ctx: PSURContext) -> str:
    """Render Section 6: Benefit-Risk Assessment."""
    try:
        # Build prompt
        prompt = (
            f"You are a senior pharmacovigilance expert. Write a clear, concise benefit-risk assessment for "
            f"{ctx.product} covering the period {ctx.period_start} to {ctx.period_end}.\n\n"
            f"Use the following information:\n"
            f"- Signals summary: {ctx.signals_summary}\n"
            f"- AE trends: {summarize_trends_for_prompt(ctx.unified_ae_data)}\n"
            f"- Social vs FAERS vs literature alignment: {summarize_alignment_for_prompt(ctx.unified_ae_data)}\n"
        )
        
        if ctx.org_config and ctx.org_config.exposure_estimates:
            prompt += f"- Exposure estimates: {ctx.org_config.exposure_estimates}\n"
        
        system_prompt = (
            "You are a pharmacovigilance expert writing regulatory reports. "
            "Provide clear, evidence-based benefit-risk assessments using formal medical language."
        )
        
        result = call_medical_llm(
            prompt=prompt,
            system_prompt=system_prompt,
            task_type="narrative_analysis",
            max_tokens=1500,
            temperature=0.3
        )
        
        if result:
            return result
        
        # Fallback if LLM fails
        return (
            f"Benefit-risk assessment for {ctx.product} based on available data:\n\n"
            f"During the reporting period, {ctx.signals_summary.get('total_cases', 0)} adverse event cases "
            f"were reported. {ctx.signals_summary.get('total_signals', 0)} distinct signals were identified. "
            f"Please review the signal summary and trend analysis sections for detailed information."
        )
    except Exception as e:
        logger.error(f"Error generating benefit-risk assessment: {e}")
        return (
            "Benefit-risk assessment could not be generated automatically. "
            "Please review the signal summary and trend analysis sections."
        )


def render_section_conclusions(ctx: PSURContext) -> str:
    """Render Section 7: Overall Conclusions."""
    try:
        prompt = (
            f"You are a pharmacovigilance expert. Write overall conclusions and recommendations for "
            f"{ctx.product} based on the following safety data:\n\n"
            f"- Total signals identified: {ctx.signals_summary.get('total_signals', 0)}\n"
            f"- Total cases reported: {ctx.signals_summary.get('total_cases', 0)}\n"
            f"- Top signals: {ctx.signals_summary.get('top_signals', [])[:5]}\n"
            f"- Trends: {summarize_trends_for_prompt(ctx.unified_ae_data)}\n\n"
            f"Provide clear conclusions and actionable recommendations."
        )
        
        system_prompt = (
            "You are a pharmacovigilance expert writing regulatory conclusions. "
            "Provide clear, actionable recommendations based on the safety data."
        )
        
        result = call_medical_llm(
            prompt=prompt,
            system_prompt=system_prompt,
            task_type="narrative_analysis",
            max_tokens=1000,
            temperature=0.3
        )
        
        if result:
            return result
        
        # Fallback
        return (
            f"Based on the safety data reviewed for {ctx.product} during the reporting period, "
            f"{ctx.signals_summary.get('total_signals', 0)} signals were identified from "
            f"{ctx.signals_summary.get('total_cases', 0)} reported cases. "
            f"Continued monitoring is recommended. Please review individual signal assessments for detailed recommendations."
        )
    except Exception as e:
        logger.error(f"Error generating conclusions: {e}")
        return "Conclusions could not be generated automatically. Please review the signal summary section."


# ============================================================================
# ANNEX RENDERERS
# ============================================================================

def render_annex_line_listings(ctx: PSURContext) -> str:
    """Render Annex A: Line Listings."""
    try:
        df = ctx.unified_ae_data
        if not isinstance(df, pd.DataFrame) or df.empty:
            return "No case data available for line listings."
        
        # Limit to top cases
        top_cases = df.head(100)
        
        lines = ["Line listings (top 100 cases):"]
        for idx, row in top_cases.iterrows():
            drug = row.get("drug", ctx.product)
            reaction = row.get("reaction", "Unknown")
            date = row.get("created_date", "Unknown")
            source = row.get("source", "Unknown")
            lines.append(f"- {drug} → {reaction} ({date}, Source: {source})")
        
        return "\n".join(lines)
    except Exception as e:
        logger.error(f"Error rendering line listings: {e}")
        return "Line listings could not be generated."


def render_annex_tabulations(ctx: PSURContext) -> str:
    """Render Annex B: Summary Tabulations."""
    try:
        df = ctx.unified_ae_data
        if not isinstance(df, pd.DataFrame) or df.empty:
            return "No data available for summary tabulations."
        
        lines = ["Summary tabulations:"]
        
        # By reaction
        if "reaction" in df.columns:
            reaction_counts = df["reaction"].value_counts().head(10)
            lines.append("\nTop 10 reactions:")
            for reaction, count in reaction_counts.items():
                lines.append(f"- {reaction}: {count} cases")
        
        # By source
        if "source" in df.columns:
            source_counts = df["source"].value_counts()
            lines.append("\nBy source:")
            for source, count in source_counts.items():
                lines.append(f"- {source}: {count} cases")
        
        # By severity
        if "severity_score" in df.columns:
            severe = len(df[df["severity_score"] >= 0.7])
            moderate = len(df[(df["severity_score"] >= 0.4) & (df["severity_score"] < 0.7)])
            mild = len(df[df["severity_score"] < 0.4])
            lines.append("\nBy severity:")
            lines.append(f"- Severe: {severe} cases")
            lines.append(f"- Moderate: {moderate} cases")
            lines.append(f"- Mild: {mild} cases")
        
        return "\n".join(lines)
    except Exception as e:
        logger.error(f"Error rendering tabulations: {e}")
        return "Summary tabulations could not be generated."


def render_annex_literature(ctx: PSURContext) -> str:
    """Render Annex C: Literature Reports."""
    lit_summary = ctx.literature_summary
    
    if lit_summary and lit_summary.get("total_citations", 0) > 0:
        lines = [f"Literature reports ({lit_summary.get('total_citations', 0)} citations):"]
        for paper in lit_summary.get("key_papers", [])[:10]:
            lines.append(f"- {paper}")
        return "\n".join(lines)
    
    return (
        "Literature reports: No literature citations were retrieved for this reporting period. "
        "Literature integration is being enhanced."
    )


def render_annex_exposure_tables(ctx: PSURContext) -> str:
    """Render Annex D: Exposure Tables."""
    cfg = ctx.org_config
    
    if cfg and cfg.exposure_estimates:
        lines = ["Exposure tables:"]
        for period, estimate in cfg.exposure_estimates.items():
            lines.append(f"- {period}: {estimate}")
        return "\n".join(lines)
    
    return (
        "Exposure tables: Patient exposure data has not been configured. "
        "Please update your Regulatory Settings to provide exposure estimates."
    )


# ============================================================================
# MAIN GENERATOR CLASSES
# ============================================================================

class PSURGenerator:
    """
    Generates Periodic Safety Update Reports (PSUR).
    """
    
    def __init__(self):
        """Initialize PSUR generator."""
        pass
    
    def generate_psur(
        self,
        drug: str,
        period_start: datetime,
        period_end: datetime,
        tenant_id: Optional[str] = None,
        data_sources: Optional[Dict[str, Any]] = None  # Kept for backward compatibility
    ) -> Dict[str, Any]:
        """
        Generate complete PSUR.
        
        Args:
            drug: Drug name
            period_start: Report period start
            period_end: Report period end
            tenant_id: Optional tenant ID (if None, uses current user's org)
            data_sources: Optional data sources dict (for backward compatibility)
        
        Returns:
            Complete PSUR document structure
        """
        # Build context (validation happens inside build_psur_context)
        ctx = build_psur_context(tenant_id, drug, period_start, period_end)
        
        psur = {
            "drug": drug,
            "report_period": {
                "start": period_start.isoformat(),
                "end": period_end.isoformat()
            },
            "generated_at": datetime.now().isoformat(),
            "sections": {}
        }
        
        # Generate sections
        psur["sections"]["section_1"] = {
            "title": "Worldwide Marketing Authorization Status",
            "content": render_section_marketing_auth(ctx)
        }
        
        psur["sections"]["section_2"] = {
            "title": "Actions Taken for Safety Reasons",
            "content": render_section_safety_actions(ctx)
        }
        
        psur["sections"]["section_3"] = {
            "title": "Changes to Risk Management Plan",
            "content": render_section_rmp_changes(ctx)
        }
        
        psur["sections"]["section_4"] = {
            "title": "Estimated Exposure",
            "content": render_section_exposure(ctx)
        }
        
        psur["sections"]["section_5"] = render_section_signals(ctx)
        
        psur["sections"]["section_6"] = {
            "title": "Discussion on Benefit-Risk",
            "content": render_section_benefit_risk(ctx)
        }
        
        psur["sections"]["section_7"] = {
            "title": "Conclusions",
            "content": render_section_conclusions(ctx)
        }
        
        # Generate annexes
        psur["annexes"] = {
            "annex_a": render_annex_line_listings(ctx),
            "annex_b": render_annex_tabulations(ctx),
            "annex_c": render_annex_literature(ctx),
            "annex_d": render_annex_exposure_tables(ctx)
        }
        
        return psur


class DSURGenerator:
    """
    Generates Development Safety Update Reports (DSUR).
    """
    
    def __init__(self):
        """Initialize DSUR generator."""
        pass
    
    def generate_dsur(
        self,
        drug: str,
        period_start: datetime,
        period_end: datetime,
        tenant_id: Optional[str] = None,
        data_sources: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate complete DSUR.
        
        Args:
            drug: Drug name
            period_start: Report period start
            period_end: Report period end
            tenant_id: Optional tenant ID
            data_sources: Optional data sources dict
        
        Returns:
            Complete DSUR document structure
        """
        ctx = build_psur_context(tenant_id, drug, period_start, period_end)
        
        dsur = {
            "drug": drug,
            "report_period": {
                "start": period_start.isoformat(),
                "end": period_end.isoformat()
            },
            "generated_at": datetime.now().isoformat(),
            "sections": {}
        }
        
        # Section 1: Introduction
        dsur["sections"]["section_1"] = {
            "title": "Introduction",
            "content": f"Development Safety Update Report for {drug}"
        }
        
        # Section 2: Development Status
        cfg = ctx.org_config
        if cfg and cfg.clinical_program:
            lines = ["Worldwide Development Status:"]
            for program in cfg.clinical_program:
                study_id = program.get("study_id", "")
                phase = program.get("phase", "")
                status = program.get("status", "")
                lines.append(f"- {study_id}: {phase} ({status})")
            content = "\n".join(lines)
        else:
            content = (
                "Clinical development status has not been configured. "
                "Please update your Regulatory Settings to provide clinical program information."
            )
        
        dsur["sections"]["section_2"] = {
            "title": "Worldwide Development Status",
            "content": content
        }
        
        # Section 3: Safety Information
        safety_info = (
            f"Safety information from real-world data:\n\n"
            f"- Total cases: {ctx.signals_summary.get('total_cases', 0)}\n"
            f"- Total signals: {ctx.signals_summary.get('total_signals', 0)}\n"
            f"- Source breakdown: {ctx.signals_summary.get('sources', {})}\n\n"
            f"Note: Clinical trial SAE data should be integrated separately."
        )
        
        dsur["sections"]["section_3"] = {
            "title": "Safety Information",
            "content": safety_info
        }
        
        # Section 4: Risk Summary
        risk_summary = render_section_signals(ctx)
        dsur["sections"]["section_4"] = {
            "title": "Interval Summary of Risks",
            "content": f"Identified risks: {risk_summary.get('total_signals', 0)} signals identified. See signal summary for details."
        }
        
        # Section 5: Benefit-Risk
        dsur["sections"]["section_5"] = {
            "title": "Integrated Benefit-Risk Evaluation",
            "content": render_section_benefit_risk(ctx)
        }
        
        return dsur


class SignalReportGenerator:
    """
    Generates Signal Evaluation Reports (SER).
    """
    
    def __init__(self):
        """Initialize signal report generator."""
        pass
    
    def generate_signal_report(
        self,
        drug: str,
        reaction: str,
        signal_data: Dict[str, Any],
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate signal evaluation report.
        
        Args:
            drug: Drug name
            reaction: Reaction name
            signal_data: Signal analysis data
            tenant_id: Optional tenant ID
        
        Returns:
            Complete signal report structure
        """
        # Build context (use last 90 days for signal report)
        period_end = datetime.now()
        period_start = datetime.now() - timedelta(days=90)
        ctx = build_psur_context(tenant_id, drug, period_start, period_end)
        
        # Filter data for this specific signal
        try:
            df = ctx.unified_ae_data
            if isinstance(df, pd.DataFrame) and not df.empty:
                signal_df = df[
                    (df["drug"].str.contains(drug, case=False, na=False)) &
                    (df["reaction"].str.contains(reaction, case=False, na=False))
                ]
            else:
                signal_df = pd.DataFrame()
        except Exception:
            signal_df = pd.DataFrame()
        
        return {
            "signal_id": signal_data.get("signal_id", "unknown"),
            "drug": drug,
            "reaction": reaction,
            "generated_at": datetime.now().isoformat(),
            "summary": self._generate_summary(drug, reaction, signal_data),
            "evidence": self._generate_evidence_section(signal_data),
            "analysis": self._generate_analysis_section(signal_data, signal_df),
            "conclusions": self._generate_conclusions(signal_data, signal_df),
            "recommendations": self._generate_recommendations(signal_data)
        }
    
    def _generate_summary(
        self,
        drug: str,
        reaction: str,
        signal_data: Dict[str, Any]
    ) -> str:
        """Generate signal summary."""
        quantum_score = signal_data.get("quantum_score", 0.0)
        gri_score = signal_data.get("gri_score", 0.0)
        priority = signal_data.get("priority_category", "unknown")
        
        return (
            f"Signal: {drug} → {reaction}\n"
            f"Quantum Score: {quantum_score:.2f}\n"
            f"Global Risk Index: {gri_score:.2f} ({priority.title()})\n"
            f"Evidence from {len(signal_data.get('sources', []))} sources"
        )
    
    def _generate_evidence_section(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate evidence section."""
        return {
            "faers": signal_data.get("faers_count", 0),
            "social": signal_data.get("social_count", 0),
            "literature": signal_data.get("literature_count", 0),
            "clinical_trials": signal_data.get("clinical_count", 0)
        }
    
    def _generate_analysis_section(
        self,
        signal_data: Dict[str, Any],
        signal_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """Generate analysis section."""
        trend_text = "Trend analysis unavailable."
        severity_text = "Severity distribution unavailable."
        
        if not signal_df.empty:
            # Trend analysis
            try:
                aggregator = ExecutiveAggregator()
                trends = aggregator.compute_trends(signal_df, period="M")
                if not trends.empty:
                    first = trends.iloc[0]
                    last = trends.iloc[-1]
                    change = int(last["count"] - first["count"])
                    direction = "increasing" if change > 0 else "decreasing" if change < 0 else "stable"
                    trend_text = f"Trend: {direction} ({change} cases change over period)"
            except Exception:
                pass
            
            # Severity distribution
            try:
                if "severity_score" in signal_df.columns:
                    severe = len(signal_df[signal_df["severity_score"] >= 0.7])
                    total = len(signal_df)
                    severity_text = f"Severity: {severe}/{total} cases classified as severe (≥0.7)"
            except Exception:
                pass
        
        return {
            "trend_analysis": trend_text,
            "severity_distribution": severity_text,
            "mechanistic_plausibility": signal_data.get("mechanistic_score", 0.0)
        }
    
    def _generate_conclusions(
        self,
        signal_data: Dict[str, Any],
        signal_df: pd.DataFrame
    ) -> str:
        """Generate conclusions."""
        try:
            prompt = (
                f"Write signal evaluation conclusions for {signal_data.get('drug', 'drug')} → "
                f"{signal_data.get('reaction', 'reaction')} signal:\n\n"
                f"- Quantum Score: {signal_data.get('quantum_score', 0.0)}\n"
                f"- Priority: {signal_data.get('priority_category', 'unknown')}\n"
                f"- Evidence sources: {signal_data.get('sources', [])}\n"
                f"- Total cases: {len(signal_df) if not signal_df.empty else 0}\n\n"
                f"Provide clear conclusions and next steps."
            )
            
            system_prompt = "You are a pharmacovigilance expert evaluating safety signals."
            
            result = call_medical_llm(
                prompt=prompt,
                system_prompt=system_prompt,
                task_type="narrative_analysis",
                max_tokens=800,
                temperature=0.3
            )
            
            if result:
                return result
        except Exception as e:
            logger.error(f"Error generating signal conclusions: {e}")
        
        # Fallback
        priority = signal_data.get("priority_category", "unknown")
        return (
            f"Signal evaluation for {signal_data.get('drug', 'drug')} → {signal_data.get('reaction', 'reaction')}: "
            f"Priority level: {priority}. Continued monitoring recommended. "
            f"Review individual case details for further assessment."
        )
    
    def _generate_recommendations(self, signal_data: Dict[str, Any]) -> List[str]:
        """Generate recommendations."""
        action = signal_data.get("recommended_action", "monitor_only")
        
        recommendations = []
        if action == "regulatory_submission":
            recommendations.append("Prepare regulatory submission")
            recommendations.append("Update Risk Management Plan")
        elif action == "label_update_recommended":
            recommendations.append("Consider label update")
        else:
            recommendations.append("Continue monitoring")
        
        return recommendations

