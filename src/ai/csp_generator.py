"""
Core Safety Profile (CSP) Generator for AetherSignal (CHUNK 6.18)
Generates regulatory-compliant Core Safety Profiles aligned with EMA RMP Annex 1, ICH E2C(R2), and CCDS standards.
"""
import datetime
import json
from typing import Dict, List, Optional, Any
from src.ai.medical_llm import call_medical_llm


class CSPGenerator:
    """
    Core Safety Profile (CSP) Generator (CHUNK 6.18).
    
    Generates regulatory-compliant CSP documents using:
    - Signal Detection Results
    - Trend Alerts
    - RPF (Risk Prioritization Framework)
    - Subgroup Analysis
    - Lot/Batch Detection
    - Benefit-Risk Assessment
    - Narrative Intelligence
    - LLM-powered classification and wording
    """
    
    def _system_prompt(self):
        return """
You are a senior pharmacovigilance and regulatory expert specializing in:
- EMA RMP Annex 1 (Safety Specification)
- ICH E2C(R2) PBRER guidelines
- Company Core Safety Information (CCSI)
- CCDS / CSP best practice
- Labeling (SmPC/USPI)

Generate inspection-ready, regulatory-compliant safety specification content.
Use formal regulatory language aligned with EMA GVP Module V Annex 1 style.
"""

    def generate_csp(
        self,
        payload: Dict[str, Any],
        heavy: bool = False
    ) -> Optional[str]:
        """
        Generate Core Safety Profile (CSP) (CHUNK 6.18).
        
        Args:
            payload: Structured payload with signal data, trend alerts, RPF scores, etc.
            heavy: If True, generate full CSP; if False, generate summary
            
        Returns:
            Generated CSP content as markdown string, or None if generation fails
        """
        sys_prompt = self._system_prompt()
        
        # Format data for prompt
        signal_summary = self._format_signals(payload.get("signals", []))
        trend_summary = self._format_trend_alerts(payload.get("trend_alerts", {}))
        rpf_summary = self._format_rpf_ranked(payload.get("rpf_ranked", []))
        subgroup_summary = self._format_subgroups(payload.get("subgroup_analysis", {}))
        lot_summary = self._format_lot_findings(payload.get("lot_analysis", {}))
        benefit_risk_summary = self._format_benefit_risk(payload.get("benefit_risk", {}))
        
        if not heavy:
            user_prompt = f"""
Create a concise Core Safety Profile summary for:

### Detected Signals
{signal_summary[:500]}

### Priority Risks (RPF)
{rpf_summary[:500]}

### Trend Alerts
{trend_summary[:500]}

Provide:
1. Important Identified Risks (top 3)
2. Important Potential Risks (top 2)
3. Missing Information (top 3 gaps)
4. Other Medically Important Conditions

Use concise, regulatory-appropriate language.
"""
            try:
                response = call_medical_llm(
                    prompt=user_prompt,
                    system_prompt=sys_prompt,
                    task_type="regulatory_writing",
                    max_tokens=1500,
                    temperature=0.3
                )
                return response
            except Exception:
                return None
        
        # Heavy mode - Full CSP
        user_prompt = f"""
Create a complete Core Safety Profile (CSP) using EMA RMP Annex 1 structure.

### INPUT DATA

**Signals Detected:**
{signal_summary}

**Trend Alerts:**
{trend_summary}

**Subgroup Risks:**
{subgroup_summary}

**Lot/Batch Issues:**
{lot_summary}

**RPF Prioritization:**
{rpf_summary}

**Benefit-Risk Summary:**
{benefit_risk_summary}

### STRUCTURE TO GENERATE

Generate a comprehensive CSP with the following sections:

1. **Important Identified Risks**
   - List each identified risk with clear regulatory-style descriptions
   - Clinical impact and severity
   - Evidence supporting identification (case counts, disproportionality, trends)
   - Incidence and frequency where available
   - At-risk populations
   - Temporal patterns if relevant

2. **Important Potential Risks**
   - Emerging or suspected risks with insufficient evidence
   - Evidence uncertainty and rationale for "potential" classification
   - Suggested monitoring requirements
   - Risk factors or predisposing conditions
   - Class effects or theoretical concerns

3. **Missing Information**
   - Gaps in safety knowledge
   - Populations with limited data (pediatrics, elderly, pregnancy, etc.)
   - Required further studies or surveillance
   - Duration of treatment limitations
   - Special populations requiring additional monitoring

4. **Other Medically Important Conditions**
   - Class effects requiring surveillance
   - Rare AEs requiring special attention
   - Conditions of uncertain significance
   - Monitoring recommendations

5. **Scientific Rationale for Classification**
   - Why each risk belongs in each category
   - Evidence hierarchy considerations
   - Regulatory precedent if applicable
   - Decision rationale for borderline cases

6. **Recommended CCDS Wording**
   - Safety-related label updates
   - Warning/precaution language (Section 4.4 SmPC style)
   - Adverse reaction table updates (Section 4.8 SmPC style)
   - Contraindications (Section 4.3 SmPC style)
   - Special populations (Section 4.6 SmPC style)

7. **Summary Table**
   - Compact CSP table for RMP/CCDS inclusion
   - Risk category, Description, Evidence Level, Monitoring Status

8. **Version History and Change Log**
   - Version number and date
   - Changes from previous version
   - Rationale for updates

Format as markdown with clear sections. Ensure phrasing matches EMA GVP Module V Annex 1 style.
Use formal regulatory language suitable for submission to health authorities.
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

    def build_payload(
        self,
        alerts: Dict,
        signals: List[Dict],
        rpf_ranked: Optional[List[Dict]] = None,
        subgroups: Optional[Dict] = None,
        lot_findings: Optional[Dict] = None,
        narrative_highlights: Optional[List] = None,
        meta: Optional[Dict] = None,
        benefit_risk: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Build payload for CSP generation (CHUNK 6.18).
        
        Args:
            alerts: Trend alerts dictionary
            signals: List of signal dictionaries
            rpf_ranked: RPF-ranked signals list
            subgroups: Subgroup analysis results
            lot_findings: Lot/batch analysis results
            narrative_highlights: Narrative cluster highlights
            meta: Metadata (drug, reaction, etc.)
            benefit_risk: Benefit-risk assessment data
            
        Returns:
            Structured payload for CSP generation
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
            "benefit_risk": benefit_risk or {},
        }
    
    def _format_signals(self, signals: List[Dict]) -> str:
        """Format signals for CSP prompt."""
        if not signals:
            return "No specific signals identified."
        
        parts = [f"Identified Signals ({len(signals)}):"]
        for idx, signal in enumerate(signals[:15], 1):
            drug = signal.get("drug", "Unknown")
            reaction = signal.get("reaction", "Unknown")
            parts.append(f"{idx}. {drug} → {reaction}")
            if signal.get("ror"):
                parts.append(f"   ROR: {signal.get('ror', 0):.2f}")
            if signal.get("prr"):
                parts.append(f"   PRR: {signal.get('prr', 0):.2f}")
            if signal.get("case_count"):
                parts.append(f"   Cases: {signal.get('case_count', 0)}")
            if signal.get("serious_count"):
                parts.append(f"   Serious Cases: {signal.get('serious_count', 0)}")
        
        return "\n".join(parts)
    
    def _format_trend_alerts(self, alerts: Dict) -> str:
        """Format trend alerts for CSP prompt."""
        if not alerts:
            return "No trend alerts detected."
        
        parts = []
        if alerts.get("alerts"):
            parts.append(f"High-Priority Trend Alerts: {len(alerts['alerts'])}")
            for alert in alerts["alerts"][:10]:
                title = alert.get('title', alert.get('message', 'Unknown'))
                summary = alert.get('summary', '')
                severity = alert.get('severity', 'info')
                parts.append(f"- [{severity.upper()}] {title}: {summary}")
        
        if alerts.get("emerging_signals"):
            parts.append(f"\nEmerging Signals: {len(alerts['emerging_signals'])}")
            for signal in alerts["emerging_signals"][:10]:
                parts.append(f"- {signal.get('drug', 'Unknown')} → {signal.get('reaction', 'Unknown')}")
        
        return "\n".join(parts) if parts else "No trend alerts detected."
    
    def _format_rpf_ranked(self, rpf_ranked: List[Dict]) -> str:
        """Format RPF-ranked signals for CSP prompt."""
        if not rpf_ranked:
            return "No signals prioritized."
        
        parts = [f"Prioritized Signals (Top {min(15, len(rpf_ranked))}):"]
        for idx, entry in enumerate(rpf_ranked[:15], 1):
            signal = entry.get("signal", {})
            rpf_score = entry.get("rpf_score", 0)
            risk_level = entry.get("risk_level", "Unknown")
            drug = signal.get("drug", "Unknown")
            reaction = signal.get("reaction", "Unknown")
            parts.append(f"{idx}. {risk_level}: {drug} → {reaction} (RPF Score: {rpf_score:.1f})")
            # Include pillar breakdown if available
            if entry.get("pillar_scores"):
                parts.append(f"   Pillars: Disprop={entry['pillar_scores'].get('disproportionality', 0):.1f}, "
                           f"Serious={entry['pillar_scores'].get('seriousness', 0):.1f}, "
                           f"Trend={entry['pillar_scores'].get('trend', 0):.1f}")
        
        return "\n".join(parts)
    
    def _format_subgroups(self, subgroups: Dict) -> str:
        """Format subgroup analysis for CSP prompt."""
        if not subgroups:
            return "No subgroup-specific risks identified."
        
        parts = ["Subgroup Risk Patterns:"]
        for key, value in list(subgroups.items())[:8]:
            if isinstance(value, dict):
                top_group = value.get('top_group', 'N/A')
                top_value = value.get('top_value', 0)
                anomaly_score = value.get('anomaly_score', 1)
                parts.append(f"- {key}: {top_group} ({top_value} cases)")
                if anomaly_score > 2:
                    parts.append(f"  ⚠️ Significant anomaly detected (score: {anomaly_score:.2f})")
            else:
                parts.append(f"- {key}: {value}")
        
        return "\n".join(parts)
    
    def _format_lot_findings(self, lot_findings: Dict) -> str:
        """Format lot/batch findings for CSP prompt."""
        if not lot_findings:
            return "No lot/batch anomalies detected."
        
        parts = ["Lot/Batch Quality Concerns:"]
        if isinstance(lot_findings, list):
            for lot in lot_findings[:8]:
                parts.append(f"- Lot {lot.get('lot_number', 'N/A')}: {lot.get('count', 0)} cases")
                parts.append(f"  Spike ratio: {lot.get('spike_ratio', 0):.2f}×, "
                           f"Serious: {lot.get('serious_count', 0)}")
        elif isinstance(lot_findings, dict):
            for key, value in list(lot_findings.items())[:8]:
                parts.append(f"- {key}: {value}")
        
        return "\n".join(parts)
    
    def _format_benefit_risk(self, benefit_risk: Dict) -> str:
        """Format benefit-risk assessment for CSP prompt."""
        if not benefit_risk:
            return "Benefit-risk assessment not available."
        
        parts = ["Benefit-Risk Assessment:"]
        
        if benefit_risk.get("scores"):
            scores = benefit_risk["scores"]
            parts.append(f"- Benefit Score: {scores.get('benefit_score', 'N/A')}")
            parts.append(f"- Risk Score: {scores.get('risk_score', 'N/A')}")
            parts.append(f"- Benefit-Risk Index: {scores.get('benefit_risk_index', 'N/A')}")
        
        if benefit_risk.get("narrative"):
            parts.append(f"\nSummary: {benefit_risk['narrative'][:300]}...")
        
        return "\n".join(parts)

