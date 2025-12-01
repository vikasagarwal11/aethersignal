"""
Mock Inspection Day Engine (CHUNK 6.22.4)
Full audit simulation with timed steps, multi-inspector switching, escalation, and final report generation.
"""
import random
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

try:
    from src.ai.inspector_simulation import InspectorSimulator
    SIMULATION_AVAILABLE = True
except ImportError:
    SIMULATION_AVAILABLE = False

try:
    from src.ai.inspector_observation_engine import generate_observation_letter
    OBSERVATION_AVAILABLE = True
except ImportError:
    OBSERVATION_AVAILABLE = False

try:
    from src.ai.medical_llm import call_medical_llm
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

try:
    from src.ai.trend_alerts import detect_trend_alerts_light
    TREND_ALERTS_AVAILABLE = True
except ImportError:
    TREND_ALERTS_AVAILABLE = False

try:
    from src.ai.portfolio_risk_propagation import compute_portfolio_risk_propagation
    PORTFOLIO_AVAILABLE = True
except ImportError:
    PORTFOLIO_AVAILABLE = False


MOCK_INSPECTION_STEPS = [
    {
        "step": "Case Processing Verification",
        "focus": "Data integrity, case quality, processing procedures",
        "persona": "FDA Pharmacovigilance Inspector"
    },
    {
        "step": "Signal Detection Rationales",
        "focus": "Signal detection methodology, statistical approaches, validation procedures",
        "persona": "FDA Clinical Reviewer"
    },
    {
        "step": "Trend Alerts Interpretation",
        "focus": "Trend analysis accuracy, alert justification, temporal pattern recognition",
        "persona": "EMA Signal Assessor"
    },
    {
        "step": "Subgroup Risk Evaluation",
        "focus": "Population-specific risk assessment, demographic analysis, vulnerability patterns",
        "persona": "FDA Clinical Reviewer"
    },
    {
        "step": "RPF & Prioritization Justification",
        "focus": "Risk prioritization framework, scoring methodology, prioritization rationale",
        "persona": "EMA Signal Assessor"
    },
    {
        "step": "Governance Completeness Review",
        "focus": "SOP compliance, documentation completeness, timeline adherence, audit trails",
        "persona": "FDA Pharmacovigilance Inspector"
    },
    {
        "step": "Label Impact Assessment Evidence",
        "focus": "Label change recommendations, regulatory justification, impact assessment",
        "persona": "MHRA Safety Auditor"
    },
    {
        "step": "Benefit–Risk Argument",
        "focus": "Benefit-risk methodology, quantitative assessment, regulatory alignment",
        "persona": "EMA Signal Assessor"
    },
    {
        "step": "Final Inspector Summary",
        "focus": "Overall assessment, key findings, regulatory concerns, recommendations",
        "persona": "FDA Pharmacovigilance Inspector"
    }
]


class MockInspectionDay:
    """
    Full mock inspection day simulation.
    
    Features:
    - Timed inspection steps
    - Multi-inspector personas (switches between FDA/EMA/MHRA)
    - Escalation based on answer quality
    - Comprehensive transcript tracking
    - Final inspection report generation
    """
    
    def __init__(self, df: Optional[Any] = None, signal_data: Optional[Dict[str, Any]] = None):
        """Initialize mock inspection day."""
        self.df = df
        self.signal_data = signal_data or {}
        self.steps = MOCK_INSPECTION_STEPS.copy()
        self.current_step_index = 0
        self.transcript: List[Dict[str, Any]] = []
        self.inspectors_used: List[str] = []
        self.total_score = 0.0
        self.step_scores: List[float] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
    
    def start_inspection(self) -> Dict[str, Any]:
        """Start the mock inspection."""
        self.start_time = datetime.now()
        self.current_step_index = 0
        
        # Shuffle steps for variability (except first and last)
        middle_steps = self.steps[1:-1]
        random.shuffle(middle_steps)
        self.steps = [self.steps[0]] + middle_steps + [self.steps[-1]]
        
        # Generate first question
        first_step = self.steps[0]
        inspector = InspectorSimulator(first_step["persona"])
        question_data = inspector.generate_inspector_question(
            df=self.df,
            signal_data=self.signal_data
        )
        
        return {
            "inspection_started": True,
            "current_step": 0,
            "total_steps": len(self.steps) - 1,  # Exclude final summary
            "step_name": first_step["step"],
            "question": question_data.get("question", ""),
            "persona": first_step["persona"],
            "focus": first_step["focus"],
            "start_time": self.start_time.isoformat()
        }
    
    def process_step_answer(
        self,
        step_index: int,
        answer: str,
        time_taken_seconds: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Process answer for a specific step and move to next step.
        
        Args:
            step_index: Current step index (0-based)
            answer: User's answer
            time_taken_seconds: Time taken to answer (optional, for scoring)
            
        Returns:
            Dictionary with evaluation and next step information
        """
        if step_index >= len(self.steps) - 1:
            return {"error": "Inspection already completed"}
        
        current_step = self.steps[step_index]
        inspector = InspectorSimulator(current_step["persona"])
        
        # Get question from transcript or generate it
        question_text = None
        if self.transcript and len(self.transcript) > step_index:
            question_text = self.transcript[step_index].get("question", "")
        
        if not question_text:
            # Generate question for this step
            question_data = inspector.generate_inspector_question(
                df=self.df,
                signal_data=self.signal_data
            )
            question_text = question_data.get("question", "")
        
        # Evaluate answer
        evaluation = inspector.evaluate_answer(answer, {"question": question_text})
        
        # Record in transcript
        transcript_entry = {
            "step_index": step_index,
            "step_name": current_step["step"],
            "persona": current_step["persona"],
            "focus": current_step["focus"],
            "question": question_text,
            "answer": answer,
            "score": evaluation.get("score", 0),
            "feedback": evaluation.get("feedback", ""),
            "escalation_level": evaluation.get("escalation_level", 1),
            "timestamp": datetime.now().isoformat(),
            "time_taken_seconds": time_taken_seconds
        }
        
        # Store or update transcript entry
        if len(self.transcript) > step_index:
            self.transcript[step_index] = transcript_entry
        else:
            self.transcript.append(transcript_entry)
        
        # Update scores
        score = evaluation.get("score", 0)
        self.step_scores.append(score)
        self.total_score = sum(self.step_scores) / len(self.step_scores) if self.step_scores else 0
        
        # Track inspectors used
        if current_step["persona"] not in self.inspectors_used:
            self.inspectors_used.append(current_step["persona"])
        
        # Move to next step
        next_step_index = step_index + 1
        next_question = None
        next_step_info = None
        
        if next_step_index < len(self.steps) - 1:
            next_step = self.steps[next_step_index]
            next_inspector = InspectorSimulator(next_step["persona"])
            next_question_data = next_inspector.generate_inspector_question(
                df=self.df,
                signal_data=self.signal_data
            )
            next_question = next_question_data.get("question", "")
            next_step_info = {
                "step_index": next_step_index,
                "step_name": next_step["step"],
                "persona": next_step["persona"],
                "focus": next_step["focus"]
            }
        
        return {
            "current_step_evaluation": evaluation,
            "transcript_entry": transcript_entry,
            "overall_score": self.total_score,
            "next_step": next_step_info,
            "next_question": next_question,
            "inspection_complete": next_step_index >= len(self.steps) - 1
        }
    
    def generate_final_report(self) -> Dict[str, Any]:
        """
        Generate final inspection report (Form 483 / Major Objection equivalent).
        
        Returns:
            Dictionary with complete inspection report
        """
        if not self.transcript:
            return {"error": "No inspection transcript available"}
        
        self.end_time = datetime.now()
        duration_minutes = (self.end_time - self.start_time).total_seconds() / 60 if self.start_time else 0
        
        # Analyze transcript for deficiencies
        deficiencies = []
        major_observations = []
        minor_observations = []
        
        for entry in self.transcript:
            score = entry.get("score", 100)
            step_name = entry.get("step_name", "Unknown Step")
            
            if score < 40:
                major_observations.append({
                    "step": step_name,
                    "issue": entry.get("feedback", "Significant deficiency identified"),
                    "score": score
                })
                deficiencies.append({
                    "severity": "Major",
                    "step": step_name,
                    "issue": entry.get("feedback", ""),
                    "evidence": f"Answer scored {score}/100"
                })
            elif score < 60:
                minor_observations.append({
                    "step": step_name,
                    "issue": entry.get("feedback", "Minor deficiency identified"),
                    "score": score
                })
                deficiencies.append({
                    "severity": "Minor",
                    "step": step_name,
                    "issue": entry.get("feedback", ""),
                    "evidence": f"Answer scored {score}/100"
                })
        
        # Generate observation letter
        primary_persona = self.inspectors_used[0] if self.inspectors_used else "FDA Clinical Reviewer"
        observation_letter = None
        
        try:
            observation_letter = generate_observation_letter(
                df=self.df,
                persona=primary_persona,
                signal_data=self.signal_data,
                conversation_history=self.transcript
            )
        except Exception:
            pass
        
        # Generate comprehensive report using LLM
        report_content = None
        if LLM_AVAILABLE:
            prompt = self._build_final_report_prompt(
                transcript=self.transcript,
                deficiencies=deficiencies,
                major_observations=major_observations,
                minor_observations=minor_observations,
                overall_score=self.total_score,
                duration_minutes=duration_minutes
            )
            system_prompt = f"You are a senior {primary_persona} preparing a comprehensive inspection summary report."
            
            try:
                report_content = call_medical_llm(
                    prompt,
                    system_prompt,
                    task_type="general",
                    max_tokens=2500,
                    temperature=0.2
                )
            except Exception:
                pass
        
        if not report_content:
            report_content = self._generate_fallback_report(
                deficiencies, major_observations, minor_observations,
                self.total_score, duration_minutes
            )
        
        return {
            "inspection_date": self.start_time.strftime("%Y-%m-%d") if self.start_time else datetime.now().strftime("%Y-%m-%d"),
            "inspection_duration_minutes": round(duration_minutes, 1),
            "inspectors": self.inspectors_used,
            "total_steps": len(self.transcript),
            "overall_score": round(self.total_score, 1),
            "step_scores": [round(s, 1) for s in self.step_scores],
            "major_observations_count": len(major_observations),
            "minor_observations_count": len(minor_observations),
            "deficiencies": deficiencies,
            "major_observations": major_observations,
            "minor_observations": minor_observations,
            "observation_letter": observation_letter,
            "full_report": report_content,
            "regulatory_impact": self._assess_regulatory_impact(deficiencies),
            "recommended_actions": self._generate_recommended_actions(deficiencies, self.total_score),
            "transcript": self.transcript
        }
    
    def _build_final_report_prompt(
        self,
        transcript: List[Dict],
        deficiencies: List[Dict],
        major_observations: List[Dict],
        minor_observations: List[Dict],
        overall_score: float,
        duration_minutes: float
    ) -> str:
        """Build prompt for final inspection report generation."""
        return f"""
        Generate a comprehensive regulatory inspection summary report based on a mock inspection simulation.
        
        Inspection Overview:
        - Duration: {duration_minutes:.1f} minutes
        - Total Steps: {len(transcript)}
        - Overall Performance Score: {overall_score:.1f}/100
        
        Inspection Steps Completed:
        {json.dumps([{"step": t.get("step_name"), "score": t.get("score"), "persona": t.get("persona")} for t in transcript], indent=2)}
        
        Deficiencies Identified:
        Major Observations ({len(major_observations)}): {json.dumps(major_observations, indent=2)}
        Minor Observations ({len(minor_observations)}): {json.dumps(minor_observations, indent=2)}
        
        Full Transcript:
        {json.dumps(transcript, indent=2, default=str)}
        
        Generate a professional, regulator-ready inspection summary report with the following structure:
        
        1. **Executive Summary**
           - Inspection overview
           - Overall assessment
           - Key findings summary
        
        2. **Inspection Scope & Methodology**
           - Steps covered
           - Inspectors involved
           - Areas examined
        
        3. **Major Observations**
           - List each major finding
           - Regulatory basis
           - Evidence
           - Required actions
        
        4. **Minor Observations**
           - List minor findings
           - Recommendations
        
        5. **Overall Assessment**
           - Performance evaluation
           - Compliance status
           - Strengths identified
           - Areas for improvement
        
        6. **Regulatory Impact**
           - Potential regulatory consequences
           - Required CAPA actions
           - Timeline expectations
        
        7. **Recommendations**
           - Immediate actions
           - Short-term improvements
           - Long-term enhancements
        
        8. **Conclusion**
           - Summary
           - Next steps
           - Response requirements
        
        Maintain formal, professional tone suitable for regulatory documentation.
        """
    
    def _generate_fallback_report(
        self,
        deficiencies: List[Dict],
        major_observations: List[Dict],
        minor_observations: List[Dict],
        overall_score: float,
        duration_minutes: float
    ) -> str:
        """Generate fallback report if LLM unavailable."""
        report = f"""
        MOCK INSPECTION SUMMARY REPORT
        
        Date: {datetime.now().strftime('%Y-%m-%d')}
        Duration: {duration_minutes:.1f} minutes
        Overall Score: {overall_score:.1f}/100
        
        EXECUTIVE SUMMARY
        {'='*50}
        This mock inspection assessed pharmacovigilance processes and compliance.
        Overall performance score: {overall_score:.1f}/100.
        
        """
        
        if major_observations:
            report += f"\nMAJOR OBSERVATIONS ({len(major_observations)})\n{'-'*50}\n"
            for i, obs in enumerate(major_observations, 1):
                report += f"\n{i}. {obs.get('step', 'Unknown Step')}\n"
                report += f"   Issue: {obs.get('issue', 'Major deficiency identified')}\n"
                report += f"   Score: {obs.get('score', 0)}/100\n"
        
        if minor_observations:
            report += f"\nMINOR OBSERVATIONS ({len(minor_observations)})\n{'-'*50}\n"
            for i, obs in enumerate(minor_observations, 1):
                report += f"\n{i}. {obs.get('step', 'Unknown Step')}\n"
                report += f"   Issue: {obs.get('issue', 'Minor deficiency identified')}\n"
        
        report += f"\n\nRECOMMENDATIONS\n{'-'*50}\n"
        report += "1. Address all major observations within 30 days\n"
        report += "2. Provide corrective action plans for identified deficiencies\n"
        report += "3. Enhance documentation and evidence-based justifications\n"
        report += "4. Strengthen SOP compliance and audit trail maintenance\n"
        
        return report
    
    def _assess_regulatory_impact(self, deficiencies: List[Dict]) -> str:
        """Assess potential regulatory impact based on deficiencies."""
        major_count = len([d for d in deficiencies if d.get("severity") == "Major"])
        
        if major_count >= 3:
            return "Critical - Potential FDA Warning Letter or EMA Major Objection if not addressed promptly"
        elif major_count >= 1:
            return "Major - Enhanced regulatory monitoring and potential compliance action if deficiencies persist"
        elif len(deficiencies) > 0:
            return "Minor - Standard regulatory follow-up required"
        else:
            return "No significant regulatory concerns identified"
    
    def _generate_recommended_actions(
        self,
        deficiencies: List[Dict],
        overall_score: float
    ) -> List[str]:
        """Generate recommended corrective actions."""
        actions = []
        
        if overall_score < 60:
            actions.append("Immediate review and enhancement of pharmacovigilance processes")
            actions.append("Comprehensive documentation audit and gap remediation")
            actions.append("Staff training on regulatory requirements and SOP compliance")
        
        major_deficiencies = [d for d in deficiencies if d.get("severity") == "Major"]
        if major_deficiencies:
            actions.append(f"Address {len(major_deficiencies)} major observation(s) within 30 days")
            actions.append("Develop and implement comprehensive CAPA plan")
            actions.append("Provide regulatory response with evidence and timelines")
        
        if overall_score >= 80:
            actions.append("Continue maintaining current standards and documentation practices")
        elif overall_score >= 60:
            actions.append("Focus on strengthening areas with minor observations")
            actions.append("Enhance documentation completeness and regulatory justification")
        
        return actions


def run_mock_inspection(
    df: Optional[Any] = None,
    signal_data: Optional[Dict[str, Any]] = None
) -> MockInspectionDay:
    """
    Start a new mock inspection day session.
    
    Args:
        df: Safety data DataFrame (optional)
        signal_data: Signal-specific data (optional)
        
    Returns:
        MockInspectionDay instance ready to start inspection
    """
    return MockInspectionDay(df=df, signal_data=signal_data)


def compile_mock_inspection_report(
    inspection: MockInspectionDay
) -> Dict[str, Any]:
    """
    Compile final inspection report from mock inspection day.
    
    Args:
        inspection: MockInspectionDay instance with completed transcript
        
    Returns:
        Complete inspection report dictionary
    """
    return inspection.generate_final_report()
