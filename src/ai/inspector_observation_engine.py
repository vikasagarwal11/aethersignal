"""
Inspector Observation Letter Engine (CHUNK 6.22.3)
Generates FDA/EMA/MHRA-style inspection observation letters (Form 483, Major Objections, etc.)
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

try:
    from src.ai.medical_llm import call_medical_llm
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

try:
    from src.ai.trend_alerts import detect_trend_alerts_heavy
    TREND_ALERTS_AVAILABLE = True
except ImportError:
    TREND_ALERTS_AVAILABLE = False

try:
    from src.ai.risk_prioritization import RiskPrioritizationEngine
    RPF_AVAILABLE = True
except ImportError:
    RPF_AVAILABLE = False

try:
    from src.ai.shmi_engine import SHMIEngine
    SHMI_AVAILABLE = True
except ImportError:
    SHMI_AVAILABLE = False

try:
    from src.ai.governance_engine import GovernanceEngine
    GOVERNANCE_AVAILABLE = True
except ImportError:
    GOVERNANCE_AVAILABLE = False


def generate_observation_letter(
    df: Optional[Any] = None,
    question: Optional[str] = None,
    user_answer: Optional[str] = None,
    persona: str = "FDA Clinical Reviewer",
    signal_data: Optional[Dict[str, Any]] = None,
    conversation_history: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Generate FDA/EMA/MHRA-style inspection observation letters.
    
    Args:
        df: Safety data DataFrame (optional, for context)
        question: Inspector question (optional)
        user_answer: User's answer (optional)
        persona: Inspector persona name
        signal_data: Signal-specific data (optional)
        conversation_history: Full conversation history (optional)
        
    Returns:
        Dictionary with observation letter content, deficiencies, and regulatory citations
    """
    # Determine agency from persona
    agency = "FDA"
    letter_type = "Form 483 Observation"
    
    if "EMA" in persona:
        agency = "EMA"
        letter_type = "Major Objection"
    elif "MHRA" in persona:
        agency = "MHRA"
        letter_type = "Inspection Findings"
    elif "PMDA" in persona:
        agency = "PMDA"
        letter_type = "Inspection Report"
    
    # Heavy analysis for regulatory-grade output
    trends = []
    rpf_scores = []
    shmi_score = None
    governance_gaps = []
    
    if TREND_ALERTS_AVAILABLE and df is not None:
        try:
            trends = detect_trend_alerts_heavy(df)
            if isinstance(trends, list):
                trends = trends[:5]
            elif isinstance(trends, dict):
                trends = trends.get("alerts", [])[:5]
        except Exception:
            pass
    
    if RPF_AVAILABLE and signal_data:
        try:
            rpf_engine = RiskPrioritizationEngine()
            rpf_result = rpf_engine.score_signal(signal_data)
            if isinstance(rpf_result, dict):
                rpf_scores = [rpf_result]
        except Exception:
            pass
    
    if SHMI_AVAILABLE and signal_data:
        try:
            shmi_engine = SHMIEngine()
            shmi_result = shmi_engine.compute_shmi(signal_data)
            if isinstance(shmi_result, dict):
                shmi_score = shmi_result.get("shmi_value")
        except Exception:
            pass
    
    if GOVERNANCE_AVAILABLE:
        try:
            gov_engine = GovernanceEngine()
            if signal_data:
                gaps = gov_engine.evaluate_compliance_for_signal(signal_data)
                if isinstance(gaps, list):
                    governance_gaps = [g for g in gaps if g.get("missing", False)][:5]
        except Exception:
            pass
    
    # Analyze deficiencies from conversation history
    deficiencies = _analyze_deficiencies_from_history(conversation_history or [], user_answer)
    
    # Generate formal letter using LLM
    if LLM_AVAILABLE:
        prompt = _build_observation_letter_prompt(
            agency, letter_type, persona, question, user_answer,
            trends, rpf_scores, shmi_score, governance_gaps, deficiencies, signal_data
        )
        system_prompt = f"You are a senior {agency} regulatory inspector preparing an official inspection observation letter."
        
        try:
            letter_content = call_medical_llm(
                prompt,
                system_prompt,
                task_type="general",
                max_tokens=2000,
                temperature=0.2  # Low temperature for formal regulatory writing
            )
            if not letter_content:
                letter_content = _generate_fallback_observation_letter(
                    agency, letter_type, deficiencies, governance_gaps
                )
        except Exception:
            letter_content = _generate_fallback_observation_letter(
                agency, letter_type, deficiencies, governance_gaps
            )
    else:
        letter_content = _generate_fallback_observation_letter(
            agency, letter_type, deficiencies, governance_gaps
        )
    
    # Regulatory citations based on agency
    regulations = _get_regulatory_citations(agency)
    
    observation_letter = {
        "agency": agency,
        "letter_type": letter_type,
        "persona": persona,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "deficiencies": deficiencies,
        "governance_gaps": governance_gaps,
        "content": letter_content,
        "regulations_cited": regulations,
        "severity": _determine_letter_severity(deficiencies),
        "response_required_days": _get_response_timeline(agency, deficiencies),
        "potential_regulatory_impact": _assess_regulatory_impact(agency, deficiencies)
    }
    
    return observation_letter


def _analyze_deficiencies_from_history(
    conversation_history: List[Dict[str, Any]],
    user_answer: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Analyze conversation history to identify deficiencies."""
    deficiencies = []
    
    # Check for low-scoring answers
    for entry in conversation_history:
        if entry.get("type") == "answer":
            answer_data = entry.get("data", {})
            score = answer_data.get("score", 100)
            
            if score < 60:
                deficiencies.append({
                    "issue": "Insufficient documentation or justification provided",
                    "severity": "Major" if score < 40 else "Minor",
                    "evidence": f"Answer scored {score}/100 on regulatory evaluation",
                    "recommendation": "Provide comprehensive documentation and evidence-based justification"
                })
    
    # Check for missing critical information
    if user_answer:
        answer_lower = user_answer.lower()
        missing_items = []
        
        if "evidence" not in answer_lower and "document" not in answer_lower:
            missing_items.append("Supporting evidence and documentation")
        
        if "sop" not in answer_lower and "procedure" not in answer_lower:
            missing_items.append("SOP compliance demonstration")
        
        if "timeline" not in answer_lower and "schedule" not in answer_lower:
            missing_items.append("Timeline and schedule information")
        
        if missing_items:
            deficiencies.append({
                "issue": f"Missing critical information: {', '.join(missing_items)}",
                "severity": "Minor",
                "recommendation": "Provide complete information addressing all regulatory requirements"
            })
    
    return deficiencies


def _build_observation_letter_prompt(
    agency: str,
    letter_type: str,
    persona: str,
    question: Optional[str],
    user_answer: Optional[str],
    trends: List[Any],
    rpf_scores: List[Any],
    shmi_score: Optional[float],
    governance_gaps: List[Dict],
    deficiencies: List[Dict],
    signal_data: Optional[Dict]
) -> str:
    """Build prompt for LLM to generate observation letter."""
    return f"""
    Generate a formal {agency} {letter_type} based on the following inspection findings:
    
    Inspector Persona: {persona}
    Inspection Date: {datetime.now().strftime('%Y-%m-%d')}
    
    Context:
    - Inspector Question: {question or 'Not provided'}
    - User Response: {user_answer or 'Not provided'}
    
    Findings:
    
    1. Identified Deficiencies:
    {json.dumps(deficiencies, indent=2) if deficiencies else 'None identified'}
    
    2. Governance Gaps:
    {json.dumps(governance_gaps, indent=2) if governance_gaps else 'None identified'}
    
    3. Data Analysis Summary:
    - Trend Alerts: {len(trends)} alerts detected
    - RPF Scores: {len(rpf_scores)} signals scored
    - Signal Health Index: {shmi_score if shmi_score else 'Not available'}
    
    4. Signal Context:
    {json.dumps(signal_data, indent=2, default=str) if signal_data else 'Not provided'}
    
    Generate a professional, regulatory-compliant {letter_type} with the following structure:
    
    1. **Header**: Agency name, letter type, date, inspection reference
    
    2. **Introduction**: Brief context of the inspection
    
    3. **Observations/Findings**: 
       - List each deficiency clearly
       - Cite specific regulatory requirements
       - Include evidence references
       
    4. **Regulatory Basis**: 
       - Cite relevant regulations ({_get_regulatory_citations(agency)})
       - Explain non-compliance implications
       
    5. **Required Corrective Actions**:
       - Specific actions required
       - Documentation requests
       - Timeline expectations
       
    6. **Response Requirements**:
       - Response deadline
       - Required format
       - Contact information
       
    7. **Potential Regulatory Impact**:
       - Assessment of severity
       - Potential consequences if not addressed
       
    8. **Closing**: Formal closing with inspector signature
    
    Maintain formal, professional tone appropriate for {agency} regulatory communications.
    """


def _generate_fallback_observation_letter(
    agency: str,
    letter_type: str,
    deficiencies: List[Dict],
    governance_gaps: List[Dict]
) -> str:
    """Generate fallback observation letter if LLM unavailable."""
    letter = f"""
{agency.upper()} {letter_type.upper()}

Date: {datetime.now().strftime('%Y-%m-%d')}
Inspection Reference: INSP-{datetime.now().strftime('%Y%m%d')}

Dear Safety Team,

During our recent pharmacovigilance inspection, the following observations were noted:

"""
    
    for i, deficiency in enumerate(deficiencies, 1):
        letter += f"\nObservation {i}:\n"
        letter += f"Finding: {deficiency.get('issue', 'Compliance issue identified')}\n"
        letter += f"Severity: {deficiency.get('severity', 'Major')}\n"
        if deficiency.get('recommendation'):
            letter += f"Recommendation: {deficiency['recommendation']}\n"
    
    if governance_gaps:
        letter += "\n\nGovernance Gaps Identified:\n"
        for gap in governance_gaps[:5]:
            letter += f"- {gap.get('item', 'Missing documentation')}\n"
    
    letter += f"\n\nRegulations Cited: {_get_regulatory_citations(agency)}\n"
    letter += "\nPlease provide a response addressing these observations within 30 days.\n"
    letter += "\nSincerely,\n"
    letter += f"{agency} Inspection Team"
    
    return letter


def _get_regulatory_citations(agency: str) -> str:
    """Get regulatory citations based on agency."""
    citations = {
        "FDA": "21 CFR 314.80, 21 CFR 600.80, FDA PV Inspection Guide",
        "EMA": "GVP Module IX, ICH E2C(R2), Directive 2001/83/EC",
        "MHRA": "MHRA GVP Guide, EudraVigilance requirements, UK Good Practice Guide",
        "PMDA": "PMDA GVP Ordinance, ICH Guidelines, Pharmaceutical Affairs Act"
    }
    return citations.get(agency, "Relevant pharmacovigilance regulations")


def _determine_letter_severity(deficiencies: List[Dict]) -> str:
    """Determine overall severity of observation letter."""
    if not deficiencies:
        return "Informational"
    
    major_count = sum(1 for d in deficiencies if d.get("severity") == "Major")
    
    if major_count >= 3:
        return "Critical"
    elif major_count >= 1:
        return "Major"
    else:
        return "Minor"


def _get_response_timeline(agency: str, deficiencies: List[Dict]) -> int:
    """Get required response timeline in days."""
    severity = _determine_letter_severity(deficiencies)
    
    timelines = {
        "FDA": {"Critical": 15, "Major": 30, "Minor": 45},
        "EMA": {"Critical": 10, "Major": 30, "Minor": 60},
        "MHRA": {"Critical": 14, "Major": 30, "Minor": 60},
        "PMDA": {"Critical": 14, "Major": 30, "Minor": 45}
    }
    
    agency_timelines = timelines.get(agency, {"Critical": 15, "Major": 30, "Minor": 45})
    return agency_timelines.get(severity, 30)


def _assess_regulatory_impact(agency: str, deficiencies: List[Dict]) -> str:
    """Assess potential regulatory impact."""
    severity = _determine_letter_severity(deficiencies)
    
    impacts = {
        "Critical": f"Potential {agency} Warning Letter or Marketing Authorization suspension if not addressed promptly",
        "Major": f"Potential {agency} compliance action or enhanced monitoring if deficiencies persist",
        "Minor": f"Standard {agency} follow-up; no immediate regulatory action expected if addressed"
    }
    
    return impacts.get(severity, "Standard regulatory follow-up required")
