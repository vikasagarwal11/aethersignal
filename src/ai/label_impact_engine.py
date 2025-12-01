"""
Label Impact Assessment Engine for AetherSignal (CHUNK 6.19)
Generates regulatory-compliant label change recommendations for SmPC (EMA), USPI (FDA), and CCDS formats.
"""
import datetime
import json
from typing import Dict, List, Optional, Any
from src.ai.medical_llm import call_medical_llm


class LabelImpactEngine:
    """
    Label Impact Assessment Engine (CHUNK 6.19).
    
    Generates regulatory-compliant label change recommendations using:
    - Signal Detection Results
    - Trend Alerts
    - Core Safety Profile (CSP)
    - Risk Prioritization Framework (RPF)
    - Benefit-Risk Assessment
    - Subgroup Analysis
    - Lot/Batch Detection
    - Narrative Intelligence
    - LLM-powered regulatory interpretation
    """
    
    def _system_prompt(self):
        return """
You are an expert in:
- EMA SmPC QRD template (v10+)
- FDA USPI labeling structure and Physician Labeling Rule (PLR)
- CCDS/CCSI authoring standards
- Pharmacovigilance and regulatory science
- Signal → Label impact workflows
- ICH E2C(R2) Section 6 (Label Impact)
- EMA GVP Module IX & XV
- EMA QRD templates

Generate compliant, inspection-ready label change recommendations.
Use formal regulatory language aligned with EMA QRD template and FDA PLR requirements.
Only propose label changes when evidence is strong and sufficient.
"""

    def generate_label_impact(
        self,
        payload: Dict[str, Any],
        heavy: bool = False
    ) -> Optional[str]:
        """
        Generate Label Impact Assessment (CHUNK 6.19).
        
        Args:
            payload: Structured payload with signal data, CSP, RPF scores, etc.
            heavy: If True, generate full assessment; if False, generate summary
            
        Returns:
            Generated label impact content as markdown string, or None if generation fails
        """
        sys_prompt = self._system_prompt()
        
        # Format data for prompt
        signal_summary = self._format_signals(payload.get("signals", []))
        trend_summary = self._format_trend_alerts(payload.get("trend_alerts", {}))
        csp_summary = self._format_csp(payload.get("csp", {}))
        rpf_summary = self._format_rpf_ranked(payload.get("rpf_ranked", []))
        benefit_risk_summary = self._format_benefit_risk(payload.get("benefit_risk", {}))
        subgroup_summary = self._format_subgroups(payload.get("subgroup_analysis", {}))
        lot_summary = self._format_lot_findings(payload.get("lot_analysis", {}))
        
        if not heavy:
            user_prompt = f"""
Assess the need for label changes based on:

### Signals
{signal_summary[:500]}

### Priority Risks (RPF)
{rpf_summary[:500]}

### CSP Summary
{csp_summary[:300]}

Provide:
1. Overall label impact assessment
2. Top 3 recommended label changes
3. Regulatory urgency (immediate, routine, monitoring)
4. Insufficient data warnings (if any)

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
        
        # Heavy mode - Full Label Impact Assessment
        user_prompt = f"""
Assess the need for label changes based on comprehensive safety analysis.

### INPUT DATA

**Signals Detected:**
{signal_summary}

**Trend Alerts:**
{trend_summary}

**Core Safety Profile (CSP):**
{csp_summary}

**Risk Prioritization Framework (RPF):**
{rpf_summary}

**Benefit-Risk Assessment:**
{benefit_risk_summary}

**Subgroup Risks:**
{subgroup_summary}

**Lot/Batch Issues:**
{lot_summary}

### STRUCTURE TO GENERATE

Generate a comprehensive Label Impact Assessment with the following sections:

A. **Executive Summary**
   - Overall label impact assessment
   - Necessity of immediate action (urgent, routine, monitoring)
   - Regulatory urgency classification
   - Key risks requiring label attention
   - Insufficient data warnings (if evidence is weak, state clearly that label update is NOT currently justified and specify what additional data is required)

B. **Proposed Label Changes (EMA SmPC)**

   1. **Section 4.3 Contraindications**
      - New contraindications (if any)
      - Proposed regulatory-compliant wording
      - Evidence supporting contraindication
      - Regulatory justification

   2. **Section 4.4 Warnings and Precautions**
      - New warnings (Important Identified Risks)
      - Updated precautionary statements
      - Proposed QRD-compliant wording
      - Clinical rationale
      - Monitoring recommendations

   3. **Section 4.5 Interactions**
      - New drug-drug interactions
      - Proposed interaction wording
      - Clinical significance
      - Management recommendations

   4. **Section 4.6 Pregnancy/Lactation/Fertility**
      - Pregnancy category updates
      - Lactation safety statements
      - Fertility impact
      - Proposed wording

   5. **Section 4.8 Undesirable Effects (Adverse Reactions)**
      - New adverse reactions to add
      - Frequency updates (very common, common, uncommon, rare, very rare)
      - MedDRA preferred terms
      - SOC (System Organ Class) organization
      - Proposed table updates

   6. **Section 5.1/5.2 Pharmacodynamic/Pharmacokinetic Properties**
      - Mechanistic relevance (if applicable)
      - Safety-related pharmacology updates

C. **Proposed Label Changes (FDA USPI)**

   1. **Boxed Warning (if required)**
      - Determination if boxed warning is warranted
      - Proposed boxed warning text (FDA format)
      - Regulatory justification
      - Evidence threshold assessment

   2. **Warnings and Precautions**
      - New warnings
      - Proposed USPI-style wording
      - Clinical significance
      - Management strategies

   3. **Adverse Reactions**
      - New adverse reactions
      - Frequency categories (≥1%, <1%, etc.)
      - Proposed table format
      - Postmarketing experience updates

   4. **Drug Interactions**
      - Interaction updates
      - USPI-style interaction wording
      - Clinical management

   5. **Use in Specific Populations**
      - Pediatric updates
      - Geriatric updates
      - Renal/hepatic impairment
      - Pregnancy/Lactation
      - Proposed wording

D. **CCDS / CCSI Updates**
   - Global core safety information changes
   - Exact wording suggestions (harmonized global format)
   - Risk classification justification
   - Section-by-section CCDS updates
   - Version control considerations

E. **Regulatory Justification**
   - Why each update is required
   - Supporting evidence summary
   - Regulatory precedent (if applicable)
   - Expected EMA/FDA reaction
   - Risk if company does NOT update label (regulatory scrutiny, liability, patient safety)
   - Timeline considerations (expedited vs routine)

F. **Impact Assessment Ranking**
   - High Impact: Requires immediate label update (urgent safety concerns)
   - Medium Impact: Recommended update within next periodic review cycle
   - Low Impact: Monitor and consider in future updates
   - No Impact: Insufficient evidence for label change at this time

G. **Reviewer Notes for QPPV & Safety Review Committee (SRC)**
   - Points requiring QPPV review
   - Items for SRC discussion
   - Medical judgment considerations
   - Regulatory strategy recommendations
   - Implementation timeline suggestions
   - Stakeholder communication needs

H. **Insufficient Data Warnings**
   - Clearly identify any proposed changes where evidence is weak
   - Specify what additional data is required
   - State when label update is NOT currently justified
   - Provide data collection recommendations

Format as markdown with clear sections. Use formal regulatory language.
Ensure all proposed wording aligns with EMA QRD template and FDA PLR requirements.
If evidence is insufficient for a label change, state this clearly rather than proposing changes.
"""
        try:
            response = call_medical_llm(
                prompt=user_prompt,
                system_prompt=sys_prompt,
                task_type="regulatory_writing",
                max_tokens=6000,
                temperature=0.3
            )
            return response
        except Exception:
            return None

    def build_payload(
        self,
        alerts: Dict,
        signals: List[Dict],
        csp: Optional[Dict] = None,
        rpf_ranked: Optional[List[Dict]] = None,
        subgroups: Optional[Dict] = None,
        lot_findings: Optional[Dict] = None,
        narrative_highlights: Optional[List] = None,
        meta: Optional[Dict] = None,
        benefit_risk: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Build payload for label impact assessment generation (CHUNK 6.19).
        
        Args:
            alerts: Trend alerts dictionary
            signals: List of signal dictionaries
            csp: Core Safety Profile data
            rpf_ranked: RPF-ranked signals list
            subgroups: Subgroup analysis results
            lot_findings: Lot/batch analysis results
            narrative_highlights: Narrative cluster highlights
            meta: Metadata (drug, reaction, etc.)
            benefit_risk: Benefit-risk assessment data
            
        Returns:
            Structured payload for label impact generation
        """
        return {
            "generated_on": datetime.datetime.utcnow().isoformat(),
            "meta": meta or {},
            "signals": signals,
            "rpf_ranked": rpf_ranked or [],
            "trend_alerts": alerts,
            "csp": csp or {},
            "subgroup_analysis": subgroups or {},
            "lot_analysis": lot_findings or {},
            "narrative_highlights": narrative_highlights or [],
            "benefit_risk": benefit_risk or {},
        }
    
    def _format_signals(self, signals: List[Dict]) -> str:
        """Format signals for label impact prompt."""
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
        """Format trend alerts for label impact prompt."""
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
        
        return "\n".join(parts) if parts else "No trend alerts detected."
    
    def _format_csp(self, csp: Dict) -> str:
        """Format CSP data for label impact prompt."""
        if not csp:
            return "Core Safety Profile not available."
        
        if isinstance(csp, dict):
            content = csp.get("content", "")
            if content:
                # Extract key sections from CSP
                return f"CSP Content Summary:\n{content[:1000]}..."
            else:
                return "CSP data present but content not available."
        elif isinstance(csp, str):
            return f"CSP Content:\n{csp[:1000]}..."
        else:
            return "CSP data format not recognized."
    
    def _format_rpf_ranked(self, rpf_ranked: List[Dict]) -> str:
        """Format RPF-ranked signals for label impact prompt."""
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
        
        return "\n".join(parts)
    
    def _format_benefit_risk(self, benefit_risk: Dict) -> str:
        """Format benefit-risk assessment for label impact prompt."""
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
    
    def _format_subgroups(self, subgroups: Dict) -> str:
        """Format subgroup analysis for label impact prompt."""
        if not subgroups:
            return "No subgroup-specific risks identified."
        
        parts = ["Subgroup Risk Patterns:"]
        for key, value in list(subgroups.items())[:8]:
            if isinstance(value, dict):
                parts.append(f"- {key}: {value.get('top_group', 'N/A')} ({value.get('top_value', 0)} cases)")
            else:
                parts.append(f"- {key}: {value}")
        
        return "\n".join(parts)
    
    def _format_lot_findings(self, lot_findings: Dict) -> str:
        """Format lot/batch findings for label impact prompt."""
        if not lot_findings:
            return "No lot/batch anomalies detected."
        
        parts = ["Lot/Batch Quality Concerns:"]
        if isinstance(lot_findings, list):
            for lot in lot_findings[:8]:
                parts.append(f"- Lot {lot.get('lot_number', 'N/A')}: {lot.get('count', 0)} cases (spike: {lot.get('spike_ratio', 0):.2f}×)")
        elif isinstance(lot_findings, dict):
            for key, value in list(lot_findings.items())[:8]:
                parts.append(f"- {key}: {value}")
        
        return "\n".join(parts)

