"""
AI-Driven CAPA (Corrective and Preventive Actions) Recommendations Engine for AetherSignal (CHUNK 6.15)
Generates regulatory-compliant CAPA recommendations for identified safety signals and risks.
"""
import datetime
from typing import Dict, List, Optional, Any
from src.ai.medical_llm import call_medical_llm


class CAPAEngine:
    """
    CAPA Recommendations Engine (CHUNK 6.15).
    
    Generates Corrective and Preventive Actions for:
    - Identified Signals
    - Emerging Risks
    - Subgroup-specific risks
    - Lot/Batch spikes
    - Trend anomalies
    - Case narratives
    - Regulatory impact
    """
    
    def _system_prompt(self):
        return """
You are a senior pharmacovigilance quality and compliance expert.
You specialize in:

- ICH E2C(R2), E2F
- EMA GVP (Modules I–XI, XV)
- FDA post-marketing safety requirements
- CAPA (Corrective and Preventive Actions)
- Risk minimization measures (RMM)
- Inspection readiness
- PRAC/PSMF processes

Generate compliant, inspection-ready CAPA recommendations.
Use structured, actionable language suitable for regulatory review.
"""

    def generate_capa(
        self,
        payload: Dict[str, Any],
        heavy: bool = False
    ) -> Optional[str]:
        """
        Generate CAPA recommendations (CHUNK 6.15).
        
        Args:
            payload: Structured payload with signal data, trend alerts, RPF scores, etc.
            heavy: If True, generate full CAPA; if False, generate summary
            
        Returns:
            Generated CAPA content as markdown string, or None if generation fails
        """
        sys_prompt = self._system_prompt()
        
        # Format data for prompt
        signal_summary = self._format_signals(payload.get('signals', []))
        trend_alerts_summary = self._format_trend_alerts(payload.get('trend_alerts', {}))
        rpf_summary = self._format_rpf_ranked(payload.get('rpf_ranked', []))
        subgroup_summary = self._format_subgroups(payload.get('subgroup_analysis', {}))
        lot_summary = self._format_lot_findings(payload.get('lot_analysis', {}))
        narrative_summary = self._format_narratives(payload.get('narrative_highlights', []))
        
        if not heavy:
            user_prompt = f"""
Create a concise CAPA summary for the following risk profile:

### Signal Summary
{signal_summary}

### Priority Risks (RPF)
{rpf_summary[:500]}  # First 500 chars

### Trend Alerts
{trend_alerts_summary[:500]}

Provide:
1. Top 3 immediate corrective actions
2. Top 2 preventive actions
3. Key regulatory notifications needed
4. Timeline (1-30-90 days)

Use concise, actionable language.
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
        
        # Heavy CAPA - Full recommendations
        user_prompt = f"""
Create comprehensive CAPA recommendations for the following risk profile:

### Signal Detected
{signal_summary}

### Trend Alerts
{trend_alerts_summary}

### Lot/Batch Findings
{lot_summary}

### RPF Ranking (Prioritized Risks)
{rpf_summary}

### Subgroup Risks
{subgroup_summary}

### Narrative Case Highlights
{narrative_summary}

Generate a complete CAPA recommendation document with:

1. **Root Cause Hypothesis**
   - Analysis of potential underlying causes
   - Data-driven evidence supporting the hypothesis
   - Alternative explanations considered

2. **Corrective Actions (Immediate - Days 1-30)**
   - Immediate actions to address the identified risk
   - Case-level investigations needed
   - Data collection requirements
   - Communication actions

3. **Preventive Actions (Long-term - Days 30-90+)**
   - Systemic improvements
   - Process enhancements
   - Training requirements
   - System updates

4. **Required Regulatory Notifications**
   - Which agencies need to be notified (FDA, EMA, etc.)
   - Timeline for notifications
   - Required documentation
   - Expedited reporting requirements

5. **Risk Minimization Measures (RMM)**
   - Educational materials needed
   - Labeling changes required
   - Healthcare provider communications
   - Patient monitoring programs
   - Risk Management Plans (RMP) updates

6. **Impact on Benefit-Risk Assessment**
   - How this affects overall benefit-risk balance
   - Patient population considerations
   - Alternative treatments assessment
   - Clinical implications

7. **Recommended Timeline**
   - Immediate actions (1-7 days)
   - Short-term actions (7-30 days)
   - Medium-term actions (30-90 days)
   - Long-term actions (90+ days)

8. **Inspection Readiness Preparation**
   - Documentation to prepare
   - Quality records needed
   - Audit trail requirements
   - Evidence of actions taken
   - Response to potential inspector questions

Format as markdown with clear sections and actionable items.
Use regulatory-appropriate language.
"""
        try:
            response = call_medical_llm(
                prompt=user_prompt,
                system_prompt=sys_prompt,
                task_type="regulatory_writing",
                max_tokens=3500,
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
    ) -> Dict[str, Any]:
        """
        Build payload for CAPA generation (CHUNK 6.15).
        
        Args:
            alerts: Trend alerts dictionary
            signals: List of signal dictionaries
            rpf_ranked: RPF-ranked signals list
            subgroups: Subgroup analysis results
            lot_findings: Lot/batch analysis results
            narrative_highlights: Narrative cluster highlights
            meta: Metadata (drug, reaction, etc.)
            
        Returns:
            Structured payload for CAPA generation
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
        }
    
    def _format_signals(self, signals: List[Dict]) -> str:
        """Format signals for CAPA prompt."""
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
        """Format trend alerts for CAPA prompt."""
        if not alerts:
            return "No trend alerts detected."
        
        parts = []
        if alerts.get("alerts"):
            parts.append(f"High-Priority Alerts: {len(alerts['alerts'])}")
            for alert in alerts["alerts"][:5]:
                parts.append(f"- {alert.get('title', alert.get('message', 'Unknown'))}: {alert.get('summary', '')}")
        
        if alerts.get("emerging_signals"):
            parts.append(f"\nEmerging Signals: {len(alerts['emerging_signals'])}")
            for signal in alerts["emerging_signals"][:5]:
                parts.append(f"- {signal.get('drug', 'Unknown')} → {signal.get('reaction', 'Unknown')}")
        
        return "\n".join(parts) if parts else "No trend alerts detected."
    
    def _format_rpf_ranked(self, rpf_ranked: List[Dict]) -> str:
        """Format RPF-ranked signals for CAPA prompt."""
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
        """Format subgroup analysis for CAPA prompt."""
        if not subgroups:
            return "No subgroup-specific risks identified."
        
        parts = ["Subgroup Risk Patterns:"]
        for key, value in list(subgroups.items())[:5]:
            if isinstance(value, dict):
                parts.append(f"- {key}: {value.get('top_group', 'N/A')} ({value.get('top_value', 0)} cases)")
                if value.get('anomaly_score', 1) > 2:
                    parts.append(f"  ⚠️ Anomaly detected (score: {value.get('anomaly_score', 0):.2f})")
            else:
                parts.append(f"- {key}: {value}")
        
        return "\n".join(parts)
    
    def _format_lot_findings(self, lot_findings: Dict) -> str:
        """Format lot/batch findings for CAPA prompt."""
        if not lot_findings:
            return "No lot/batch anomalies detected."
        
        parts = ["Lot/Batch Quality Concerns:"]
        if isinstance(lot_findings, list):
            for lot in lot_findings[:5]:
                parts.append(f"- Lot {lot.get('lot_number', 'N/A')}: {lot.get('count', 0)} cases")
                parts.append(f"  Spike ratio: {lot.get('spike_ratio', 0):.2f}×")
                parts.append(f"  Serious cases: {lot.get('serious_count', 0)}")
        elif isinstance(lot_findings, dict):
            for key, value in list(lot_findings.items())[:5]:
                parts.append(f"- {key}: {value}")
        
        return "\n".join(parts)
    
    def _format_narratives(self, narratives: List) -> str:
        """Format narrative highlights for CAPA prompt."""
        if not narratives:
            return "No narrative patterns identified."
        
        parts = ["Case Narrative Patterns:"]
        for idx, narrative in enumerate(narratives[:5], 1):
            if isinstance(narrative, dict):
                summary = narrative.get("summary", {})
                if summary:
                    parts.append(f"{idx}. {summary.get('cluster_label', 'Unknown')}")
                    parts.append(f"   {summary.get('one_sentence_summary', '')}")
                    if summary.get("clinical_risk"):
                        parts.append(f"   Clinical Risk: {summary['clinical_risk']}")
                else:
                    parts.append(f"{idx}. {narrative.get('text', str(narrative))[:200]}")
            else:
                parts.append(f"{idx}. {str(narrative)[:200]}")
        
        return "\n".join(parts)
