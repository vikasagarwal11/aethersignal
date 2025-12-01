"""
Automated DSUR (Development Safety Update Report) and PBRER (Periodic Benefit-Risk Evaluation Report) 
Generator for AetherSignal (CHUNK 6.14)
Generates ICH E2F (DSUR) and ICH E2C(R2) (PBRER) compliant regulatory reports.
"""
import datetime
import json
from typing import Dict, List, Optional, Any
from src.ai.medical_llm import call_medical_llm
from src.ai.risk_prioritization import RiskPrioritizationEngine


class DSURPBRERGenerator:
    """
    DSUR and PBRER Generator (CHUNK 6.14).
    
    Produces regulatory-compliant reports using:
    - ICH E2F (DSUR Guideline)
    - ICH E2C(R2) (PBRER Guideline)
    - Trend Alerts
    - RPF (Risk Prioritization Framework)
    - Subgroup Analysis
    - Lot/Batch Detection
    - Narrative Intelligence
    - LLM-powered interpretation
    """
    
    def __init__(self):
        self.rpf = RiskPrioritizationEngine()

    def _system_prompt(self):
        return """
You are a senior pharmacovigilance and regulatory safety scientist with expertise in:
- ICH E2F (DSUR Guideline)
- ICH E2C(R2) (PBRER Guideline)
- EMA GVP Modules (especially VII, IX, XV)
- CIOMS Working Groups
- FDA post-marketing safety reporting

Generate formal DSUR or PBRER reports using concise, scientific, regulatory language.
"""

    def build_payload(
        self,
        alerts: Dict,
        signals: List[Dict],
        subgroups: Optional[Dict] = None,
        lot_findings: Optional[Dict] = None,
        narrative_highlights: Optional[List] = None,
        meta: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Prepare payload for DSUR/PBRER generation (CHUNK 6.14).
        
        Args:
            alerts: Trend alerts dictionary
            signals: List of signal dictionaries
            subgroups: Subgroup analysis results
            lot_findings: Lot/batch analysis results
            narrative_highlights: Narrative cluster highlights
            meta: Metadata (drug, reaction, period, etc.)
            
        Returns:
            Structured payload for report generation
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
            "meta": meta,
            "signals": signals,
            "rpf_ranked": self.rpf.prioritize(rpf_signals) if rpf_signals else [],
            "trend_alerts": alerts,
            "subgroup_analysis": subgroups or {},
            "lot_analysis": lot_findings or {},
            "narratives": narrative_highlights or [],
        }

    # ---------------------------------------------------------------------
    # DSUR
    # ---------------------------------------------------------------------
    def generate_dsur(self, payload: Dict[str, Any], heavy: bool = False) -> Optional[str]:
        """
        Generate DSUR (Development Safety Update Report) in light or heavy mode (CHUNK 6.14).
        
        Args:
            payload: Structured payload from build_payload()
            heavy: If True, generate full DSUR; if False, generate summary
            
        Returns:
            Generated DSUR content as markdown string, or None if generation fails
        """
        sys_prompt = self._system_prompt()
        
        # Format data for prompt
        trend_alerts_summary = self._format_trend_alerts(payload.get('trend_alerts', {}))
        rpf_summary = self._format_rpf_ranked(payload.get('rpf_ranked', []))
        subgroup_summary = self._format_subgroups(payload.get('subgroup_analysis', {}))
        lot_summary = self._format_lot_findings(payload.get('lot_analysis', {}))
        narrative_summary = self._format_narratives(payload.get('narratives', []))
        
        if not heavy:
            user_prompt = f"""
Create a short DSUR executive summary for:
- Drug: {payload.get('meta', {}).get('drug', 'Multiple Drugs')}
- Reaction: {payload.get('meta', {}).get('reaction', 'Multiple Reactions')}

Include:
1. New safety information
2. Emerging signals
3. Serious unexpected cases
4. Benefit-risk impact
5. Recommended follow-up

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

        # Heavy DSUR
        user_prompt = f"""
Create a **full DSUR (Development Safety Update Report)** according to ICH E2F.

Include mandatory DSUR sections:

1. Executive Summary  
2. Worldwide Marketing Approval Status  
3. Summary of Important Risks  
4. Significant Findings from Clinical Trials  
5. Findings from Non-Interventional Studies  
6. Overall Safety Evaluation  
7. Signal and Risk Evaluation  
8. Literature Review  
9. Summary of Safety Changes  
10. Benefit-Risk Assessment  
11. Sponsor Actions Taken or Proposed  
12. Conclusion

Use the following data:

### Trend Alerts
{trend_alerts_summary}

### RPF Ranking
{rpf_summary}

### Subgroup Analysis
{subgroup_summary}

### Lot/Batch Findings
{lot_summary}

### Narratives
{narrative_summary}

Format as markdown with proper headings. Use formal regulatory language.
"""
        try:
            response = call_medical_llm(
                prompt=user_prompt,
                system_prompt=sys_prompt,
                task_type="regulatory_writing",
                max_tokens=4000,
                temperature=0.3
            )
            return response
        except Exception:
            return None

    # ---------------------------------------------------------------------
    # PBRER
    # ---------------------------------------------------------------------
    def generate_pbrer(self, payload: Dict[str, Any], heavy: bool = False) -> Optional[str]:
        """
        Generate PBRER (Periodic Benefit-Risk Evaluation Report) in light or heavy mode (CHUNK 6.14).
        
        Args:
            payload: Structured payload from build_payload()
            heavy: If True, generate full PBRER; if False, generate summary
            
        Returns:
            Generated PBRER content as markdown string, or None if generation fails
        """
        sys_prompt = self._system_prompt()
        
        # Format data for prompt
        trend_alerts_summary = self._format_trend_alerts(payload.get('trend_alerts', {}))
        rpf_summary = self._format_rpf_ranked(payload.get('rpf_ranked', []))
        subgroup_summary = self._format_subgroups(payload.get('subgroup_analysis', {}))
        lot_summary = self._format_lot_findings(payload.get('lot_analysis', {}))
        narrative_summary = self._format_narratives(payload.get('narratives', []))
        
        if not heavy:
            user_prompt = f"""
Create a PBRER summary for:
- Drug: {payload.get('meta', {}).get('drug', 'Multiple Drugs')}
- Reaction: {payload.get('meta', {}).get('reaction', 'Multiple Reactions')}

Include:
1. New safety concerns
2. RPF-ranked risks
3. Cumulative safety information
4. Benefit-risk balance
5. Key actions to consider

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

        # Heavy PBRER
        user_prompt = f"""
Create a **full PBRER (Periodic Benefit-Risk Evaluation Report)** according to ICH E2C(R2).

Include:

1. Introduction  
2. Worldwide Marketing Approval Status  
3. Actions taken for Safety Reasons  
4. Changes to Reference Safety Information  
5. Estimated Patient Exposure  
6. Data in Summary Tabulations  
7. Summaries of Significant New Safety Information  
8. Signal and Risk Evaluation  
9. Benefit-Risk Evaluation  
10. Integrated Benefit-Risk Assessment  
11. Conclusions and Actions

Using the following data:

### Trend Alerts
{trend_alerts_summary}

### RPF Ranking
{rpf_summary}

### Subgroup Analysis
{subgroup_summary}

### Lot/Batch Findings
{lot_summary}

### Narratives
{narrative_summary}

Format as markdown with proper headings. Use formal regulatory language.
"""
        try:
            response = call_medical_llm(
                prompt=user_prompt,
                system_prompt=sys_prompt,
                task_type="regulatory_writing",
                max_tokens=4000,
                temperature=0.3
            )
            return response
        except Exception:
            return None
    
    def _format_trend_alerts(self, alerts: Dict) -> str:
        """Format trend alerts for report prompt."""
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
        """Format RPF-ranked signals for report prompt."""
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
        """Format subgroup analysis for report prompt."""
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
        """Format lot/batch findings for report prompt."""
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
        """Format narrative highlights for report prompt."""
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
