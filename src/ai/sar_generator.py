"""
Automated Safety Assessment Report (SAR) Generator for AetherSignal (CHUNK 6.13)
Generates FDA/EMA-style regulatory-compliant safety assessment reports.
"""
import datetime
import json
from typing import Dict, List, Optional, Any
from src.ai.medical_llm import call_medical_llm
from src.ai.risk_prioritization import RiskPrioritizationEngine


class SARGenerator:
    """
    Safety Assessment Report (SAR) Generator (CHUNK 6.13).
    
    Produces regulatory-compliant SAR documents using:
    - Trend Alerts
    - RPF (Risk Prioritization Framework)
    - Subgroup Analysis
    - Lot/Batch Detection
    - Narrative Intelligence
    - LLM-powered interpretation
    """
    
    def __init__(self):
        self.rpf = RiskPrioritizationEngine()

    def build_sar_payload(
        self,
        alerts: Dict,
        signals: List[Dict],
        subgroups: Optional[Dict] = None,
        lot_findings: Optional[Dict] = None,
        narrative_highlights: Optional[List] = None,
        meta: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Collects all analytical components into a structured payload (CHUNK 6.13).
        
        Args:
            alerts: Trend alerts dictionary
            signals: List of signal dictionaries
            subgroups: Subgroup analysis results
            lot_findings: Lot/batch analysis results
            narrative_highlights: Narrative cluster highlights
            meta: Metadata (drug, reaction, etc.)
            
        Returns:
            Structured payload for SAR generation
        """
        meta = meta or {}
        
        # Extract signals for RPF if not already provided
        rpf_signals = signals
        if alerts and not signals:
            # Extract signals from alerts
            rpf_signals = self.rpf.extract_signals_from_alerts(
                alerts.get("alerts", []) + alerts.get("emerging_signals", []),
                None  # df not needed if signals already extracted
            )
        
        return {
            "generated_on": datetime.datetime.utcnow().isoformat(),
            "drug": meta.get("drug", "Multiple Drugs"),
            "reaction": meta.get("reaction", "Multiple Reactions"),
            "signals": signals,
            "rpf_ranked": self.rpf.prioritize(rpf_signals) if rpf_signals else [],
            "trend_alerts": alerts,
            "subgroup_analysis": subgroups or {},
            "lot_analysis": lot_findings or {},
            "narrative_highlights": narrative_highlights or [],
            "meta": meta
        }

    def _build_system_prompt(self):
        return """
You are a pharmacovigilance safety scientist with deep expertise in:
- FDA FAERS
- EMA EudraVigilance
- WHO UMC VigiBase
- GVP Module IX (Signal Management)
- CIOMS VIII SAR Framework
- PRAC decision frameworks

Your task is to produce a *regulatory-compliant SAR (Safety Assessment Report)*.
Use formal scientific language. Be concise but complete.
"""

    def generate_sar(self, payload: Dict[str, Any], heavy: bool = False) -> Optional[str]:
        """
        Generate Safety Assessment Report (SAR) in light or heavy mode (CHUNK 6.13).
        
        Args:
            payload: Structured payload from build_sar_payload()
            heavy: If True, generate full SAR; if False, generate summary
            
        Returns:
            Generated SAR content as markdown string, or None if generation fails
        """
        system_prompt = self._build_system_prompt()
        
        # Light mode → short summary
        if not heavy:
            user_prompt = f"""
Create a **1-page Safety Assessment Summary** for:

Drug: {payload.get('drug', 'Multiple Drugs')}
Reaction: {payload.get('reaction', 'Multiple Reactions')}

Summaries needed:
1. Key findings
2. Trend overview
3. Seriousness and clinical impact
4. Top RPF-ranked risks
5. Recommended next steps

Use concise, professional language suitable for regulatory review.
            """
            
            try:
                response = call_medical_llm(
                    prompt=user_prompt,
                    system_prompt=system_prompt,
                    task_type="regulatory_writing",
                    max_tokens=800,
                    temperature=0.3
                )
                return response
            except Exception:
                return None
        
        # Heavy mode → full SAR
        # Format payload data for prompt
        trend_alerts_summary = self._format_trend_alerts(payload.get('trend_alerts', {}))
        rpf_summary = self._format_rpf_ranked(payload.get('rpf_ranked', []))
        subgroup_summary = self._format_subgroups(payload.get('subgroup_analysis', {}))
        lot_summary = self._format_lot_findings(payload.get('lot_analysis', {}))
        narrative_summary = self._format_narratives(payload.get('narrative_highlights', []))
        
        user_prompt = f"""
Create a **full Safety Assessment Report (SAR)** using the following data.

---

### Trend Alerts
{trend_alerts_summary}

### Prioritized Signals (RPF)
{rpf_summary}

### Subgroup Analysis
{subgroup_summary}

### Lot / Batch Findings
{lot_summary}

### Narrative Case Highlights
{narrative_summary}

---

Structure the SAR exactly as follows:

# 1. Executive Summary
# 2. Background & Clinical Context
# 3. Data Sources & Methodology
# 4. Signal Description
# 5. Trend Analysis
# 6. Subgroup & Stratified Findings
# 7. Lot/Batch Investigation
# 8. Narrative Case Review
# 9. RPF Risk Assessment & Justification
# 10. Regulatory Interpretation (EMA/FDA)
# 11. Recommended Actions
# 12. Conclusion

Be detailed. Use clinical language.
Provide evidence-based reasoning.
Format as markdown with proper headings.
            """
        
        try:
            response = call_medical_llm(
                prompt=user_prompt,
                system_prompt=system_prompt,
                task_type="regulatory_writing",
                max_tokens=3000,
                temperature=0.3
            )
            return response
        except Exception:
            return None
    
    def _format_trend_alerts(self, alerts: Dict) -> str:
        """Format trend alerts for SAR prompt."""
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
        """Format RPF-ranked signals for SAR prompt."""
        if not rpf_ranked:
            return "No signals prioritized."
        
        parts = [f"Top {min(10, len(rpf_ranked))} Prioritized Signals:"]
        for idx, entry in enumerate(rpf_ranked[:10], 1):
            signal = entry.get("signal", {})
            rpf_score = entry.get("rpf_score", 0)
            risk_level = entry.get("risk_level", "Unknown")
            drug = signal.get("drug", "Unknown")
            reaction = signal.get("reaction", "Unknown")
            parts.append(f"{idx}. {risk_level}: {drug} → {reaction} (RPF Score: {rpf_score:.1f})")
        
        return "\n".join(parts)
    
    def _format_subgroups(self, subgroups: Dict) -> str:
        """Format subgroup analysis for SAR prompt."""
        if not subgroups:
            return "No subgroup analysis available."
        
        parts = ["Subgroup Findings:"]
        for key, value in list(subgroups.items())[:5]:
            if isinstance(value, dict):
                parts.append(f"- {key}: {value.get('top_group', 'N/A')} ({value.get('top_value', 0)} cases)")
            else:
                parts.append(f"- {key}: {value}")
        
        return "\n".join(parts)
    
    def _format_lot_findings(self, lot_findings: Dict) -> str:
        """Format lot/batch findings for SAR prompt."""
        if not lot_findings:
            return "No lot/batch anomalies detected."
        
        parts = ["Lot/Batch Findings:"]
        if isinstance(lot_findings, list):
            for lot in lot_findings[:5]:
                parts.append(f"- Lot {lot.get('lot_number', 'N/A')}: {lot.get('count', 0)} cases (spike ratio: {lot.get('spike_ratio', 0):.2f}×)")
        elif isinstance(lot_findings, dict):
            for key, value in list(lot_findings.items())[:5]:
                parts.append(f"- {key}: {value}")
        
        return "\n".join(parts)
    
    def _format_narratives(self, narratives: List) -> str:
        """Format narrative highlights for SAR prompt."""
        if not narratives:
            return "No narrative highlights available."
        
        parts = ["Narrative Case Highlights:"]
        for idx, narrative in enumerate(narratives[:5], 1):
            if isinstance(narrative, dict):
                summary = narrative.get("summary", {})
                if summary:
                    parts.append(f"{idx}. {summary.get('cluster_label', 'Unknown')}: {summary.get('one_sentence_summary', '')}")
                else:
                    parts.append(f"{idx}. {narrative.get('text', str(narrative))[:200]}")
            else:
                parts.append(f"{idx}. {str(narrative)[:200]}")
        
        return "\n".join(parts)
