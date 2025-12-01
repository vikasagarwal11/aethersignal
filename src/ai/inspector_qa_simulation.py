"""
Inspector Q&A Simulation Engine (CHUNK 6.21.1 - Part 24)
Full inspector interview simulation with FDA/EMA/MHRA/PMDA styles.
"""
import datetime
from typing import Dict, List, Any, Optional
from enum import Enum

try:
    from .medical_llm import call_medical_llm
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False


class InspectorStyle(Enum):
    """Inspector style/enforcement agency."""
    FDA = "fda"
    EMA = "ema"
    MHRA = "mhra"
    PMDA = "pmda"
    GENERAL = "general"


class InspectorQASimulation:
    """
    Simulates regulatory inspector interviews for signal governance systems.
    
    Supports multiple inspector styles (FDA, EMA, MHRA, PMDA) and generates:
    - Rapid-fire Q&A sessions
    - Evidence-linked responses
    - SOP citations
    - Mock inspection reports
    - Reviewer logging
    """

    def __init__(self, style: InspectorStyle = InspectorStyle.GENERAL):
        """
        Initialize the Inspector Q&A Simulation.
        
        Args:
            style: Inspector style/enforcement agency
        """
        self.style = style

    def generate_inspector_questions(self, signals: List[Dict[str, Any]],
                                    governance_package: Optional[Dict[str, Any]] = None,
                                    num_questions: int = 10) -> List[Dict[str, Any]]:
        """
        Generate realistic inspector questions based on signals and governance data.
        
        Args:
            signals: List of signal dictionaries
            governance_package: Complete governance package
            num_questions: Number of questions to generate
            
        Returns:
            List of question dictionaries with answers
        """
        if not signals:
            return []
        
        # Build context for question generation
        context = self._build_inspection_context(signals, governance_package)
        
        # Generate questions using LLM
        questions = []
        
        for i in range(num_questions):
            question_data = self._generate_single_question(context, i, num_questions)
            if question_data:
                questions.append(question_data)
        
        return questions

    def _build_inspection_context(self, signals: List[Dict[str, Any]],
                                  governance_package: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Build context for inspector question generation."""
        high_priority = [s for s in signals if s.get("priority") in ["High", "high", "Critical", "critical"]]
        overdue = [s for s in signals if s.get("timeline_status", {}).get("assessment_status") in ["Moderate Delay", "Severe Delay"]]
        
        return {
            "total_signals": len(signals),
            "high_priority_signals": len(high_priority),
            "overdue_signals": len(overdue),
            "signals": signals[:5],  # Top 5 for context
            "governance_package": governance_package or {}
        }

    def _generate_single_question(self, context: Dict[str, Any],
                                  question_index: int,
                                  total_questions: int) -> Optional[Dict[str, Any]]:
        """Generate a single inspector question with answer."""
        if not LLM_AVAILABLE:
            # Fallback: generate template questions
            templates = [
                "How do you ensure signal detection processes meet GVP Module IX requirements?",
                "What is your timeline for assessing high-priority signals?",
                "How do you validate signals before escalation?",
                "What documentation supports your signal assessment decisions?",
                "How do you handle overdue signal assessments?",
                "What is your process for reviewer assignment?",
                "How do you ensure SOP compliance in signal management?",
                "What evidence supports this signal prioritization?",
                "How do you track signal lifecycle progression?",
                "What CAPA actions have been taken for this signal?"
            ]
            
            if question_index < len(templates):
                return {
                    "question": templates[question_index],
                    "answer": "This would be answered based on governance package data.",
                    "evidence_references": [],
                    "sop_citations": []
                }
            return None
        
        style_name = self.style.value.upper()
        
        prompt = f"""
You are a {style_name} pharmacovigilance inspector conducting a signal governance inspection.

Inspection Context:
- Total signals in portfolio: {context.get('total_signals', 0)}
- High-priority signals: {context.get('high_priority_signals', 0)}
- Overdue assessments: {context.get('overdue_signals', 0)}

Question {question_index + 1} of {total_questions}

Generate a realistic inspector question that would be asked during a {style_name} inspection.

Focus on one of these areas:
1. Signal detection and validation processes
2. Timeline compliance and governance
3. Reviewer assignments and workload
4. Documentation completeness
5. SOP adherence
6. Risk prioritization methodology
7. CAPA actions
8. Benefit-risk assessment
9. Label impact evaluation
10. Audit trail integrity

Provide:
1. A clear, direct inspector question
2. A suggested answer based on best practices
3. Key evidence references that should be cited
4. Relevant SOP citations

Format as JSON:
{{
    "question": "Inspector question text",
    "suggested_answer": "Recommended answer text",
    "evidence_references": ["List of evidence items"],
    "sop_citations": ["List of relevant SOPs"],
    "focus_area": "Signal detection / Timeline compliance / etc."
}}
"""
        
        try:
            system_prompt = f"You are a {style_name} pharmacovigilance inspector conducting regulatory inspections of signal governance systems."
            response = call_medical_llm(
                prompt=prompt,
                system_prompt=system_prompt,
                task_type="general",
                max_tokens=800,
                temperature=0.4
            )
            
            if response:
                # Try to parse JSON from response
                import json
                response_clean = response.strip()
                if response_clean.startswith("```json"):
                    response_clean = response_clean[7:]
                elif response_clean.startswith("```"):
                    response_clean = response_clean[3:]
                if response_clean.endswith("```"):
                    response_clean = response_clean[:-3]
                response_clean = response_clean.strip()
                
                try:
                    return json.loads(response_clean)
                except:
                    # Fallback: create structure from text
                    return {
                        "question": response_clean.split("\n")[0] if response_clean else "Inspector question",
                        "suggested_answer": response_clean,
                        "evidence_references": [],
                        "sop_citations": [],
                        "focus_area": "General"
                    }
        except Exception as e:
            pass
        
        return None

    def simulate_inspection_session(self, signals: List[Dict[str, Any]],
                                   governance_package: Optional[Dict[str, Any]] = None,
                                   num_questions: int = 15) -> Dict[str, Any]:
        """
        Simulate a complete inspection Q&A session.
        
        Args:
            signals: List of signal dictionaries
            governance_package: Complete governance package
            num_questions: Number of questions in session
            
        Returns:
            Complete inspection session dictionary
        """
        questions = self.generate_inspector_questions(signals, governance_package, num_questions)
        
        # Generate session summary
        summary = self._generate_session_summary(questions, signals, governance_package)
        
        return {
            "session_id": f"insp_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "style": self.style.value,
            "questions": questions,
            "summary": summary,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "total_questions": len(questions),
            "signals_reviewed": len(signals)
        }

    def _generate_session_summary(self, questions: List[Dict[str, Any]],
                                 signals: List[Dict[str, Any]],
                                 governance_package: Optional[Dict[str, Any]]) -> str:
        """Generate summary of inspection session."""
        if not LLM_AVAILABLE:
            return f"Inspection session completed with {len(questions)} questions covering {len(signals)} signals."
        
        prompt = f"""
You are summarizing a {self.style.value.upper()} pharmacovigilance inspection session.

Session Details:
- Questions asked: {len(questions)}
- Signals reviewed: {len(signals)}
- Inspector style: {self.style.value.upper()}

Generate a professional inspection session summary covering:
1. Overall assessment
2. Key areas examined
3. Notable findings (if any)
4. Compliance observations
5. Recommendations

Format as a professional regulatory inspection summary.
"""
        
        try:
            system_prompt = f"You are summarizing a {self.style.value.upper()} pharmacovigilance inspection session."
            return call_medical_llm(
                prompt=prompt,
                system_prompt=system_prompt,
                task_type="general",
                max_tokens=1000,
                temperature=0.3
            ) or "Inspection session summary unavailable."
        except Exception as e:
            return f"Inspection session completed. Summary generation error: {str(e)}"

    def generate_mock_inspection_report(self, inspection_session: Dict[str, Any],
                                       signals: List[Dict[str, Any]],
                                       governance_package: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate a full written mock inspection report.
        
        Args:
            inspection_session: Inspection session data
            signals: List of signal dictionaries
            governance_package: Complete governance package
            
        Returns:
            Complete mock inspection report dictionary
        """
        if not LLM_AVAILABLE:
            # Fallback report structure
            return {
                "report_title": f"{self.style.value.upper()} Signal Governance Inspection Report",
                "date": datetime.datetime.utcnow().isoformat(),
                "executive_summary": f"Inspection covered {len(signals)} signals with {inspection_session.get('total_questions', 0)} questions.",
                "findings": [],
                "recommendations": [],
                "questions_answers": inspection_session.get("questions", [])
            }
        
        style_name = self.style.value.upper()
        
        prompt = f"""
You are a {style_name} inspector writing a formal inspection report.

Inspection Session:
- Date: {inspection_session.get('timestamp', '')}
- Questions: {inspection_session.get('total_questions', 0)}
- Signals reviewed: {len(signals)}

Questions Asked:
{chr(10).join([f"{i+1}. {q.get('question', '')}" for i, q in enumerate(inspection_session.get('questions', [])[:10])])}

Generate a complete {style_name}-style inspection report with:
1. Executive Summary
2. Inspection Scope and Methodology
3. Findings (organized by area: signal detection, governance, documentation, compliance)
4. Evidence Review
5. Compliance Assessment
6. Recommendations
7. Conclusion

Format as a professional regulatory inspection report suitable for regulatory submission.
"""
        
        try:
            system_prompt = f"You are a {style_name} pharmacovigilance inspector writing a formal inspection report for signal governance systems."
            report_text = call_medical_llm(
                prompt=prompt,
                system_prompt=system_prompt,
                task_type="general",
                max_tokens=2000,
                temperature=0.3
            )
            
            return {
                "report_title": f"{style_name} Signal Governance Inspection Report",
                "date": datetime.datetime.utcnow().isoformat(),
                "inspector_style": style_name,
                "executive_summary": report_text[:500] if report_text else "",
                "full_report": report_text or "",
                "findings": self._extract_findings(signals, governance_package),
                "recommendations": self._extract_recommendations(signals, governance_package),
                "questions_answers": inspection_session.get("questions", []),
                "evidence_references": self._collect_evidence_references(signals, governance_package),
                "sop_citations": self._collect_sop_citations(governance_package)
            }
        except Exception as e:
            return {
                "report_title": f"{style_name} Signal Governance Inspection Report",
                "date": datetime.datetime.utcnow().isoformat(),
                "error": str(e),
                "questions_answers": inspection_session.get("questions", [])
            }

    def _extract_findings(self, signals: List[Dict[str, Any]],
                         governance_package: Optional[Dict[str, Any]]) -> List[str]:
        """Extract inspection findings from signals and governance data."""
        findings = []
        
        # Check for overdue signals
        overdue = [s for s in signals if s.get("timeline_status", {}).get("assessment_status") in ["Moderate Delay", "Severe Delay"]]
        if overdue:
            findings.append(f"{len(overdue)} signal(s) have overdue assessments requiring attention.")
        
        # Check compliance scores
        if governance_package:
            compliance = governance_package.get("compliance", {})
            score = compliance.get("score", 100)
            if score < 70:
                findings.append(f"Overall compliance score is {score:.1f}/100, indicating areas for improvement.")
        
        # Check for missing documentation
        if governance_package:
            gaps = governance_package.get("compliance", {}).get("gaps", [])
            if gaps:
                findings.append(f"{len(gaps)} compliance gap(s) identified in documentation.")
        
        return findings

    def _extract_recommendations(self, signals: List[Dict[str, Any]],
                                governance_package: Optional[Dict[str, Any]]) -> List[str]:
        """Extract recommendations from signals and governance data."""
        recommendations = []
        
        # High-priority signals
        high_priority = [s for s in signals if s.get("priority") in ["High", "high", "Critical", "critical"]]
        if high_priority:
            recommendations.append(f"Prioritize review of {len(high_priority)} high-priority signal(s).")
        
        # Overdue assessments
        overdue = [s for s in signals if s.get("timeline_status", {}).get("assessment_status") in ["Moderate Delay", "Severe Delay"]]
        if overdue:
            recommendations.append(f"Expedite assessment of {len(overdue)} overdue signal(s) to meet regulatory timelines.")
        
        # Compliance gaps
        if governance_package:
            gaps = governance_package.get("compliance", {}).get("gaps", [])
            if gaps:
                recommendations.append(f"Address {len(gaps)} identified compliance gap(s) to improve inspection readiness.")
        
        return recommendations

    def _collect_evidence_references(self, signals: List[Dict[str, Any]],
                                    governance_package: Optional[Dict[str, Any]]) -> List[str]:
        """Collect evidence references for inspection report."""
        references = []
        
        for signal in signals[:10]:  # Top 10
            drug = signal.get("drug", "Unknown")
            reaction = signal.get("reaction", "Unknown")
            references.append(f"Signal file: {drug} - {reaction}")
        
        if governance_package:
            if governance_package.get("trends"):
                references.append("Trend alerts analysis")
            if governance_package.get("risk_profile"):
                references.append("Risk Prioritization Framework assessment")
            if governance_package.get("compliance"):
                references.append("Compliance checklist")
        
        return references

    def _collect_sop_citations(self, governance_package: Optional[Dict[str, Any]]) -> List[str]:
        """Collect SOP citations from governance package."""
        citations = []
        
        if governance_package:
            sop_findings = governance_package.get("sop_findings", {})
            if isinstance(sop_findings, dict):
                citations.extend(sop_findings.keys())
        
        # Add default SOPs
        default_sops = [
            "SOP-SIG-001: Signal Detection",
            "SOP-SIG-002: Signal Assessment",
            "SOP-QA-004: Documentation Standards"
        ]
        citations.extend(default_sops)
        
        return list(set(citations))  # Remove duplicates

