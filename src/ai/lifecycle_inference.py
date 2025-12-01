"""
Automatic Lifecycle Stage Inference (CHUNK B4)
Hybrid rule-based + AI approach to detect signal lifecycle stage.
"""
from typing import Dict, List, Any, Optional
import json

try:
    from .medical_llm import call_medical_llm
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False


def infer_lifecycle_stage(
    trend_alerts: Optional[List[Dict[str, Any]]] = None,
    rpf_scores: Optional[Dict[str, Any]] = None,
    confidence_scores: Optional[Dict[str, Any]] = None,
    label_impact_scores: Optional[Dict[str, Any]] = None,
    capa_findings: Optional[Dict[str, Any]] = None,
    governance_gaps: Optional[Dict[str, Any]] = None,
    summary: Optional[Dict[str, Any]] = None,
    medical_llm = None
) -> Dict[str, Any]:
    """
    Hybrid rule + AI approach to infer lifecycle stage.
    
    Returns:
        Dictionary with stage, evidence, and AI rationale
    """
    trend_alerts = trend_alerts or []
    rpf_scores = rpf_scores or {}
    confidence_scores = confidence_scores or {}
    label_impact_scores = label_impact_scores or {}
    capa_findings = capa_findings or {}
    governance_gaps = governance_gaps or {}
    summary = summary or {}
    
    # ---------
    # RULE LAYER
    # ---------
    rule_stage = "Triage"
    rule_evidence = "Initial signal detection phase."
    
    if len(trend_alerts) == 0:
        rule_stage = "Triage (No notable trends detected)"
        rule_evidence = "No statistical or clinical anomalies detected."
    else:
        top_alert = trend_alerts[0] if trend_alerts else {}
        if isinstance(top_alert, dict):
            severity = top_alert.get("severity", "info")
            confidence = confidence_scores.get("overall_confidence") or confidence_scores.get("score", 0)
            confidence_normalized = float(confidence) / 100.0 if confidence > 1 else float(confidence) if confidence else 0
            
            if severity in ["high", "critical", "warning"]:
                if confidence_normalized < 0.4:
                    rule_stage = "Signal Under Assessment"
                    rule_evidence = "High-severity alert with low confidence score. Requires deeper investigation."
                else:
                    rule_stage = "Signal Evaluation"
                    rule_evidence = "High-severity alert with moderate to high confidence. Under evaluation."
            else:
                rule_stage = "Signal Validation"
                rule_evidence = "Low/moderate anomalies present. Validation phase."
    
    # CAPA triggers mid/late stage
    open_major = capa_findings.get("open_major", 0) or capa_findings.get("urgent_capa_count", 0)
    if open_major > 0:
        rule_stage = "Corrective/Preventive Action (CAPA)"
        rule_evidence = f"Major CAPA items remain open ({open_major}). Corrective actions in progress."
    
    # Label impact → late stage
    should_update = label_impact_scores.get("should_update_label", False)
    if should_update:
        rule_stage = "Recommendation"
        rule_evidence = "Potential label impact identified. Recommendation phase for regulatory submission."
    
    # High RPF score → evaluation/recommendation
    rpf_score = rpf_scores.get("rpf_score") or rpf_scores.get("qsp_score", 0)
    if rpf_score and float(rpf_score) >= 70:
        if rule_stage == "Triage":
            rule_stage = "Signal Evaluation"
            rule_evidence = "High RPF score indicates significant risk requiring evaluation."
    
    # ---------
    # AI LAYER (if LLM available)
    # ---------
    ai_rationale = None
    
    if LLM_AVAILABLE and medical_llm:
        try:
            ai_prompt = f"""
You are a pharmacovigilance lifecycle expert. Based on the following data, determine the most accurate signal lifecycle stage.

Trend Alerts: {len(trend_alerts)} alerts
RPF Scores: {rpf_scores}
Confidence Scores: {confidence_scores}
Label Impact: {label_impact_scores}
CAPA: {capa_findings}
Governance Gaps: {governance_gaps}

Current rule-based stage: {rule_stage}
Rule evidence: {rule_evidence}

Respond in JSON format with:
- stage: The lifecycle stage (Triage, Validation, Assessment, Evaluation, Recommendation, CAPA, Closed)
- rationale: Brief explanation of why this stage is appropriate

JSON Response:
"""
            
            system_prompt = "You are a pharmacovigilance lifecycle expert determining signal management stages according to EMA GVP Module IX and CIOMS VIII guidelines."
            
            ai_response = call_medical_llm(
                prompt=ai_prompt,
                system_prompt=system_prompt,
                task_type="general",
                max_tokens=300,
                temperature=0.3
            )
            
            if ai_response:
                # Try to parse JSON from response
                try:
                    # Clean up response to extract JSON
                    response_clean = ai_response.strip()
                    if response_clean.startswith("```json"):
                        response_clean = response_clean[7:]
                    elif response_clean.startswith("```"):
                        response_clean = response_clean[3:]
                    if response_clean.endswith("```"):
                        response_clean = response_clean[:-3]
                    response_clean = response_clean.strip()
                    
                    ai_result = json.loads(response_clean)
                    rule_stage = ai_result.get("stage", rule_stage)
                    ai_rationale = ai_result.get("rationale", "AI rationale unavailable.")
                except (json.JSONDecodeError, ValueError):
                    # Fallback: use rule-based stage, extract rationale from text
                    ai_rationale = ai_response[:200] if len(ai_response) > 200 else ai_response
        except Exception:
            # Fallback to rule-based if AI fails
            pass
    
    return {
        "stage": rule_stage,
        "evidence": rule_evidence,
        "ai_rationale": ai_rationale or "AI rationale unavailable. Using rule-based inference."
    }

