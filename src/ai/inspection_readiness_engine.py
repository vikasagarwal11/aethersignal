"""
Inspection Readiness & Audit Defense Automation Engine for AetherSignal (CHUNK 6.16)
Generates regulatory-compliant inspection evidence packages and audit defense documentation.
"""
import datetime
from typing import Dict, List, Optional, Any
from src.ai.medical_llm import call_medical_llm


class InspectionReadinessEngine:
    """
    Inspection Readiness Engine (CHUNK 6.16).
    
    Generates regulatory inspection-ready documentation for:
    - EMA GVP Module XV (Signal Management)
    - FDA post-marketing PV inspections (21 CFR Part 314.80)
    - MHRA signal audits
    - PMDA post-marketing surveillance
    - PRAC/PSMF audit defense
    """
    
    def _system_prompt(self):
        return """
You are an expert in:
- EMA GVP Modules I–XI, especially Module XV (Signal Management)
- FDA post-marketing PV inspections (21 CFR Part 314.80)
- MHRA signal audit requirements
- PMDA post-marketing surveillance
- Inspection readiness and audit defense
- 21 CFR Part 11 compliance
- System validation requirements

Generate robust, compliant inspection documentation.
Use formal regulatory language suitable for agency review.
"""

    def generate_evidence_pack(
        self,
        payload: Dict[str, Any],
        audit_trail: Optional[List[Dict]] = None,
        heavy: bool = False
    ) -> Optional[str]:
        """
        Generate inspection readiness evidence package (CHUNK 6.16).
        
        Args:
            payload: Structured payload with all analytical data
            audit_trail: List of audit log entries
            heavy: If True, generate full evidence pack; if False, generate summary
            
        Returns:
            Generated evidence pack content as markdown string, or None if generation fails
        """
        sys_prompt = self._system_prompt()
        
        # Format data for prompt
        dataset_info = self._format_dataset_info(payload.get("meta", {}))
        signal_summary = self._format_signals(payload.get("signals", []))
        trend_summary = self._format_trend_alerts(payload.get("trend_alerts", {}))
        rpf_summary = self._format_rpf_ranked(payload.get("rpf_ranked", []))
        subgroup_summary = self._format_subgroups(payload.get("subgroup_analysis", {}))
        lot_summary = self._format_lot_findings(payload.get("lot_analysis", {}))
        audit_summary = self._format_audit_trail(audit_trail or [])
        
        if not heavy:
            user_prompt = f"""
Create a concise inspection readiness summary for:

### Dataset Information
{dataset_info}

### Detected Signals
{signal_summary[:500]}

### Priority Signals (RPF)
{rpf_summary[:500]}

Provide:
1. Overview of signal detection approach
2. Key findings summary
3. Top 3 regulatory considerations
4. Evidence available for review

Use concise, regulatory-appropriate language.
"""
            try:
                response = call_medical_llm(
                    prompt=user_prompt,
                    system_prompt=sys_prompt,
                    task_type="regulatory_writing",
                    max_tokens=1000,
                    temperature=0.3
                )
                return response
            except Exception:
                return None
        
        # Heavy mode - Full evidence pack
        user_prompt = f"""
Create a comprehensive inspection readiness evidence package aligned with FDA/EMA requirements.

### Dataset & Data Lineage
{dataset_info}

### Signal Detection Methodology
- Disproportionality analysis (PRR, ROR, IC)
- Trend detection algorithms
- Subgroup analysis methods
- Lot/batch spike detection
- Risk Prioritization Framework (RPF)
- Narrative clustering approach

### Detected Signals & Evaluation
{signal_summary}

### Trend Analyses
{trend_summary}

### Subgroup Analyses
{subgroup_summary}

### Lot/Batch Analyses
{lot_summary}

### RPF Prioritization Decisions
{rpf_summary}

### Audit Trail Summary
{audit_summary}

Generate a complete evidence package with:

1. **Introduction & Scope**
   - Purpose of the evidence package
   - Regulatory context (FDA/EMA/MHRA)
   - Assessment period

2. **Safety Dataset Description**
   - Data source and lineage
   - Data quality measures
   - Processing methodology
   - Validation steps

3. **Signal Management Approach**
   - Signal detection strategy
   - Statistical methods used
   - Thresholds and criteria
   - Algorithm validation

4. **Disproportionality Methods**
   - PRR/ROR/IC calculations
   - Confidence intervals
   - Method justification
   - Reference data sources

5. **Trend Detection Methods**
   - Temporal analysis approach
   - Change-point detection
   - Baseline comparisons
   - Statistical significance criteria

6. **Signal Assessment Output**
   - All detected signals
   - Evaluation rationale
   - Prioritization logic
   - Decision timeline

7. **Subgroup Assessment**
   - Stratified analyses performed
   - Demographic considerations
   - Statistical testing methods
   - Findings and interpretation

8. **Lot/Batch Assessment**
   - Quality monitoring approach
   - Spike detection methods
   - Investigation procedures
   - Action taken

9. **RPF — Prioritization Decisions**
   - Risk scoring methodology
   - Weight assignment rationale
   - Priority ranking logic
   - Decision justification

10. **CAPA Actions**
    - Corrective actions taken
    - Preventive measures implemented
    - Regulatory notifications made
    - Timeline and evidence

11. **Reviewer Rationale Logs**
    - Assessment decisions
    - Clinical judgment
    - Regulatory considerations
    - Documentation trail

12. **Audit Trail Summary**
    - System activities logged
    - User actions recorded
    - Data access history
    - Report generation logs
    - 21 CFR Part 11 compliance notes

13. **System Validation Notes**
    - Algorithm validation status
    - System qualification
    - Data integrity measures
    - Change control documentation

Format as markdown with clear sections. Use formal regulatory language.
Ensure all evidence is traceable and defensible.
"""
        try:
            response = call_medical_llm(
                prompt=user_prompt,
                system_prompt=sys_prompt,
                task_type="regulatory_writing",
                max_tokens=5000,
                temperature=0.3
            )
            return response
        except Exception:
            return None

    def generate_inspector_questions(
        self,
        signal_context: Dict[str, Any],
        agency: str = "FDA"
    ) -> Optional[str]:
        """
        Generate realistic inspector questions (CHUNK 6.16).
        
        Args:
            signal_context: Context about detected signals
            agency: Regulatory agency ("FDA", "EMA", "MHRA", "PMDA")
            
        Returns:
            Generated questions as markdown string, or None if generation fails
        """
        sys_prompt = self._system_prompt()
        
        # Format signal context
        signal_summary = self._format_signals(signal_context.get("signals", []))
        rpf_summary = self._format_rpf_ranked(signal_context.get("rpf_ranked", []))
        
        user_prompt = f"""
Simulate {agency} inspector questions for this safety signal assessment.

### Signal Context
{signal_summary}

### Prioritized Signals
{rpf_summary[:500]}

Create 10 highly realistic auditor questions that a {agency} inspector would ask during a pharmacovigilance inspection. 

Focus on:
- Signal detection methodology
- Statistical justification
- Decision-making process
- Documentation completeness
- Regulatory compliance
- Data integrity
- Reviewer rationale
- Action taken and timeline

Format as a numbered list with detailed, specific questions.
"""
        try:
            response = call_medical_llm(
                prompt=user_prompt,
                system_prompt=sys_prompt,
                task_type="regulatory_writing",
                max_tokens=1500,
                temperature=0.4  # Slightly higher for variety in questions
            )
            return response
        except Exception:
            return None

    def build_payload(
        self,
        alerts: Dict,
        signals: List[Dict],
        rpf_ranked: Optional[List[Dict]] = None,
        subgroups: Optional[Dict] = None,
        lot_findings: Optional[Dict] = None,
        narrative_highlights: Optional[List] = None,
        meta: Optional[Dict] = None,
        capa_data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Build payload for inspection readiness generation (CHUNK 6.16).
        
        Args:
            alerts: Trend alerts dictionary
            signals: List of signal dictionaries
            rpf_ranked: RPF-ranked signals list
            subgroups: Subgroup analysis results
            lot_findings: Lot/batch analysis results
            narrative_highlights: Narrative cluster highlights
            meta: Metadata (drug, reaction, etc.)
            capa_data: CAPA recommendations data
            
        Returns:
            Structured payload for evidence pack generation
        """
        return {
            "generated_on": datetime.datetime.utcnow().isoformat(),
            "meta": meta or {},
            "signals": signals,
            "rpf_ranked": rpf_ranked or [],
            "trend_alerts": alerts,
            "subgroup_analysis": subgroups or {},
            "lot_analysis": lot_findings or {},
            "narrative_highlights": narrative_highlights or [],
            "capa_data": capa_data,
        }
    
    def _format_dataset_info(self, meta: Dict) -> str:
        """Format dataset information for evidence pack."""
        if not meta:
            return "Dataset information not available."
        
        parts = ["Dataset Information:"]
        parts.append(f"- Drug: {meta.get('drug', 'Multiple Drugs')}")
        parts.append(f"- Reaction: {meta.get('reaction', 'Multiple Reactions')}")
        total_cases = meta.get('total_cases', 'Unknown')
        if isinstance(total_cases, (int, float)):
            parts.append(f"- Total Cases: {total_cases:,}")
        else:
            parts.append(f"- Total Cases: {total_cases}")
        parts.append(f"- Assessment Period: {meta.get('period', 'Not specified')}")
        
        return "\n".join(parts)
    
    def _format_signals(self, signals: List[Dict]) -> str:
        """Format signals for evidence pack."""
        if not signals:
            return "No specific signals identified."
        
        parts = [f"Identified Signals ({len(signals)}):"]
        for idx, signal in enumerate(signals[:10], 1):
            drug = signal.get("drug", "Unknown")
            reaction = signal.get("reaction", "Unknown")
            parts.append(f"{idx}. {drug} → {reaction}")
            if signal.get("ror"):
                parts.append(f"   ROR: {signal.get('ror', 0):.2f}")
            if signal.get("case_count"):
                parts.append(f"   Cases: {signal.get('case_count', 0)}")
        
        return "\n".join(parts)
    
    def _format_trend_alerts(self, alerts: Dict) -> str:
        """Format trend alerts for evidence pack."""
        if not alerts:
            return "No trend alerts detected."
        
        parts = []
        if alerts.get("alerts"):
            parts.append(f"High-Priority Alerts: {len(alerts['alerts'])}")
            for alert in alerts["alerts"][:5]:
                parts.append(f"- {alert.get('title', alert.get('message', 'Unknown'))}: {alert.get('summary', '')}")
        
        return "\n".join(parts) if parts else "No trend alerts detected."
    
    def _format_rpf_ranked(self, rpf_ranked: List[Dict]) -> str:
        """Format RPF-ranked signals for evidence pack."""
        if not rpf_ranked:
            return "No signals prioritized."
        
        parts = [f"Prioritized Signals (Top {min(10, len(rpf_ranked))}):"]
        for idx, entry in enumerate(rpf_ranked[:10], 1):
            signal = entry.get("signal", {})
            rpf_score = entry.get("rpf_score", 0)
            risk_level = entry.get("risk_level", "Unknown")
            drug = signal.get("drug", "Unknown")
            reaction = signal.get("reaction", "Unknown")
            parts.append(f"{idx}. {risk_level}: {drug} → {reaction} (RPF Score: {rpf_score:.1f})")
        
        return "\n".join(parts)
    
    def _format_subgroups(self, subgroups: Dict) -> str:
        """Format subgroup analysis for evidence pack."""
        if not subgroups:
            return "No subgroup-specific risks identified."
        
        parts = ["Subgroup Risk Patterns:"]
        for key, value in list(subgroups.items())[:5]:
            if isinstance(value, dict):
                parts.append(f"- {key}: {value.get('top_group', 'N/A')} ({value.get('top_value', 0)} cases)")
            else:
                parts.append(f"- {key}: {value}")
        
        return "\n".join(parts)
    
    def _format_lot_findings(self, lot_findings: Dict) -> str:
        """Format lot/batch findings for evidence pack."""
        if not lot_findings:
            return "No lot/batch anomalies detected."
        
        parts = ["Lot/Batch Quality Concerns:"]
        if isinstance(lot_findings, list):
            for lot in lot_findings[:5]:
                parts.append(f"- Lot {lot.get('lot_number', 'N/A')}: {lot.get('count', 0)} cases (spike: {lot.get('spike_ratio', 0):.2f}×)")
        elif isinstance(lot_findings, dict):
            for key, value in list(lot_findings.items())[:5]:
                parts.append(f"- {key}: {value}")
        
        return "\n".join(parts)
    
    def _format_audit_trail(self, audit_trail: List[Dict]) -> str:
        """Format audit trail for evidence pack."""
        if not audit_trail:
            return "Audit trail data not available. System activities should be logged for inspection readiness."
        
        parts = [f"Audit Trail Summary ({len(audit_trail)} entries):"]
        
        # Group by event type
        event_counts = {}
        for entry in audit_trail:
            event_type = entry.get("event", "unknown")
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        parts.append("\nEvent Summary:")
        for event_type, count in sorted(event_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            parts.append(f"- {event_type}: {count} occurrences")
        
        parts.append("\nRecent Activities:")
        for entry in audit_trail[-10:]:
            timestamp = entry.get("timestamp", "Unknown")
            event = entry.get("event", "Unknown")
            parts.append(f"- {timestamp}: {event}")
        
        return "\n".join(parts)
