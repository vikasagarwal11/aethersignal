"""
Inspector Simulation Engine (CHUNK 6.22.2)
Multi-turn inspector interrogation with escalation, persona support, and answer scoring.
Simulates FDA/EMA/MHRA/PMDA inspector questioning patterns.
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
    from src.ai.portfolio_risk_propagation import compute_portfolio_risk_propagation
    PORTFOLIO_AVAILABLE = True
except ImportError:
    PORTFOLIO_AVAILABLE = False

try:
    from src.ai.trend_alerts import detect_trend_alerts_light
    TREND_ALERTS_AVAILABLE = True
except ImportError:
    TREND_ALERTS_AVAILABLE = False


INSPECTOR_PERSONAS = [
    {
        "name": "FDA Clinical Reviewer",
        "style": "strict, clinical, evidence-focused",
        "focus": "clinical accuracy, data integrity, statistical rigor",
        "agency": "FDA",
        "regulations": "21 CFR 314.80, 600.80"
    },
    {
        "name": "FDA Pharmacovigilance Inspector",
        "style": "procedural, systematic, compliance-oriented",
        "focus": "SOP compliance, documentation completeness, timeline adherence",
        "agency": "FDA",
        "regulations": "FDA PV Inspection Guide, 21 CFR 314.80"
    },
    {
        "name": "EMA Signal Assessor",
        "style": "evidence-focused, collaborative but thorough",
        "focus": "signal validation, benefit-risk assessment, regulatory reporting",
        "agency": "EMA",
        "regulations": "GVP Module IX, ICH E2C(R2)"
    },
    {
        "name": "MHRA Safety Auditor",
        "style": "methodical, detail-oriented, UK regulatory framework",
        "focus": "regulatory reporting timeliness, signal quality, risk minimization",
        "agency": "MHRA",
        "regulations": "MHRA GVP Guide, EudraVigilance requirements"
    },
    {
        "name": "PMDA Reviewer",
        "style": "thorough, systematic, Japanese regulatory standards",
        "focus": "case quality, signal detection methodology, risk communication",
        "agency": "PMDA",
        "regulations": "PMDA GVP Ordinance, ICH Guidelines"
    }
]

ESCALATION_LEVELS = {
    1: {
        "name": "Clarification",
        "tone": "neutral",
        "type": "information_request"
    },
    2: {
        "name": "Evidence Challenge",
        "tone": "concerned",
        "type": "evidence_gap"
    },
    3: {
        "name": "SOP Compliance Challenge",
        "tone": "formal",
        "type": "compliance_issue"
    },
    4: {
        "name": "Potential Deficiency",
        "tone": "serious",
        "type": "deficiency_warning"
    },
    5: {
        "name": "Official Observation Letter",
        "tone": "formal_deficiency",
        "type": "observation_letter"
    }
}


class InspectorSimulator:
    """
    Multi-turn inspector interrogation engine with escalation logic.
    
    Features:
    - Persona-based questioning
    - Answer scoring (0-100)
    - Escalation levels (1-5)
    - Inspector memory (last 3 answers + metadata)
    - Auto-deficiency letter generation
    """
    
    def __init__(self, persona: str = "FDA Clinical Reviewer"):
        """Initialize inspector simulator with selected persona."""
        self.persona = next(
            (p for p in INSPECTOR_PERSONAS if persona in p["name"]),
            INSPECTOR_PERSONAS[0]
        )
        self.conversation_history: List[Dict[str, Any]] = []
        self.escalation_level = 1
        self.question_count = 0
        
    def generate_inspector_question(
        self,
        df: Optional[Any] = None,
        signal_data: Optional[Dict[str, Any]] = None,
        portfolio_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate an inspector question based on data and conversation history.
        
        Args:
            df: Safety data DataFrame
            signal_data: Signal-specific data
            portfolio_data: Portfolio-level risk data
            
        Returns:
            Dictionary with question, context, and escalation info
        """
        self.question_count += 1
        
        # Build context from data
        context = self._build_context(df, signal_data, portfolio_data)
        
        # Determine question focus based on escalation level
        question_focus = self._determine_question_focus()
        
        # Generate question using LLM
        if LLM_AVAILABLE:
            prompt = self._build_question_prompt(context, question_focus)
            system_prompt = f"You are a {self.persona['name']} conducting a pharmacovigilance inspection."
            try:
                question_text = call_medical_llm(prompt, system_prompt, task_type="general", max_tokens=300)
                if not question_text:
                    question_text = self._generate_fallback_question(question_focus)
            except Exception:
                question_text = self._generate_fallback_question(question_focus)
        else:
            question_text = self._generate_fallback_question(question_focus)
        
        question_data = {
            "question_id": self.question_count,
            "question": question_text,
            "persona": self.persona["name"],
            "escalation_level": self.escalation_level,
            "level_name": ESCALATION_LEVELS[self.escalation_level]["name"],
            "context": context,
            "timestamp": datetime.now().isoformat()
        }
        
        self.conversation_history.append({
            "type": "question",
            "data": question_data
        })
        
        return question_data
    
    def evaluate_answer(
        self,
        answer: str,
        question_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate user's answer and generate follow-up.
        
        Args:
            answer: User's answer text
            question_data: Original question data
            
        Returns:
            Dictionary with score, feedback, and next action
        """
        if not question_data:
            question_data = self.conversation_history[-1].get("data", {}) if self.conversation_history else {}
        
        # Score the answer (0-100)
        score_result = self._score_answer(answer, question_data)
        
        # Determine if escalation is needed
        should_escalate = score_result["score"] < 60 and self.escalation_level < 5
        
        if should_escalate:
            self.escalation_level = min(5, self.escalation_level + 1)
        
        # Generate feedback
        feedback = self._generate_feedback(score_result, question_data)
        
        # Store answer in history
        self.conversation_history.append({
            "type": "answer",
            "data": {
                "answer": answer,
                "score": score_result["score"],
                "timestamp": datetime.now().isoformat()
            }
        })
        
        evaluation = {
            "score": score_result["score"],
            "score_breakdown": score_result["breakdown"],
            "feedback": feedback,
            "escalation_level": self.escalation_level,
            "should_escalate": should_escalate,
            "next_action": self._determine_next_action(score_result["score"])
        }
        
        return evaluation
    
    def generate_observation_letter(
        self,
        signal_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a formal observation letter (Form 483 equivalent).
        
        Args:
            signal_data: Signal data for context
            
        Returns:
            Dictionary with observation letter content
        """
        # Analyze conversation history for deficiencies
        deficiencies = self._analyze_deficiencies()
        
        # Generate formal letter
        if LLM_AVAILABLE:
            prompt = self._build_observation_letter_prompt(deficiencies, signal_data)
            system_prompt = f"You are a {self.persona['name']} writing a formal regulatory observation letter."
            try:
                letter_content = call_medical_llm(prompt, system_prompt, task_type="general", max_tokens=1500)
                if not letter_content:
                    letter_content = self._generate_fallback_observation_letter(deficiencies)
            except Exception:
                letter_content = self._generate_fallback_observation_letter(deficiencies)
        else:
            letter_content = self._generate_fallback_observation_letter(deficiencies)
        
        observation_letter = {
            "agency": self.persona["agency"],
            "letter_type": "Observation Letter" if self.persona["agency"] == "FDA" else "Major Objection",
            "persona": self.persona["name"],
            "deficiencies": deficiencies,
            "content": letter_content,
            "timestamp": datetime.now().isoformat(),
            "regulations_cited": self.persona["regulations"]
        }
        
        return observation_letter
    
    def _build_context(
        self,
        df: Optional[Any] = None,
        signal_data: Optional[Dict[str, Any]] = None,
        portfolio_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build context for question generation."""
        context = {
            "persona": self.persona,
            "escalation_level": self.escalation_level,
            "previous_questions": len([h for h in self.conversation_history if h.get("type") == "question"]),
            "signal_data": signal_data or {},
            "portfolio_data": portfolio_data or {}
        }
        
        # Add trend alerts if available
        if TREND_ALERTS_AVAILABLE and df is not None:
            try:
                alerts = detect_trend_alerts_light(df)
                context["trend_alerts"] = alerts[:5] if alerts else []
            except Exception:
                pass
        
        # Add portfolio risk if available
        if PORTFOLIO_AVAILABLE and df is not None:
            try:
                portfolio = compute_portfolio_risk_propagation(df)
                context["portfolio_rpf"] = portfolio.get("portfolio_rpf", [])[:5]
            except Exception:
                pass
        
        return context
    
    def _determine_question_focus(self) -> str:
        """Determine what aspect to focus on based on escalation level."""
        if self.escalation_level == 1:
            return "basic_clarification"
        elif self.escalation_level == 2:
            return "evidence_gap"
        elif self.escalation_level == 3:
            return "sop_compliance"
        elif self.escalation_level == 4:
            return "potential_deficiency"
        else:
            return "critical_deficiency"
    
    def _build_question_prompt(self, context: Dict[str, Any], focus: str) -> str:
        """Build prompt for LLM to generate inspector question."""
        return f"""
        You are a {context['persona']['name']} conducting a pharmacovigilance inspection.
        Your style is: {context['persona']['style']}
        Your focus is: {context['persona']['focus']}
        
        Current escalation level: {context['escalation_level']} ({ESCALATION_LEVELS[context['escalation_level']]['name']})
        
        Question focus: {focus}
        
        Context:
        - Previous questions asked: {context['previous_questions']}
        - Trend alerts: {context.get('trend_alerts', [])[:3]}
        - Portfolio RPF: {context.get('portfolio_rpf', [])[:3]}
        
        Generate a single, realistic inspector question that:
        1. Matches your persona and regulatory focus
        2. Is appropriate for the escalation level
        3. Is specific and actionable
        4. Could be answered with data/evidence from a safety system
        
        Return ONLY the question text, no preamble or explanation.
        """
    
    def _generate_fallback_question(self, focus: str) -> str:
        """Generate fallback question if LLM unavailable."""
        questions = {
            "basic_clarification": f"As a {self.persona['name']}, can you explain your signal detection methodology for this product?",
            "evidence_gap": f"I notice some gaps in the evidence. Can you provide additional documentation supporting this signal assessment?",
            "sop_compliance": f"Please demonstrate compliance with {self.persona['regulations']} for signal management. Where is this documented?",
            "potential_deficiency": f"I have concerns about {self.persona['focus']}. Can you provide a comprehensive explanation and corrective action plan?",
            "critical_deficiency": f"This appears to be a significant compliance issue. Please provide all relevant documentation and your remediation plan."
        }
        return questions.get(focus, questions["basic_clarification"])
    
    def _score_answer(self, answer: str, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """Score answer on multiple dimensions (0-100)."""
        if LLM_AVAILABLE:
            prompt = f"""
            Evaluate this answer to an inspector question from a {self.persona['name']}:
            
            Question: {question_data.get('question', '')}
            Answer: {answer}
            
            Score the answer (0-100) on:
            1. Clinical accuracy (0-25 points)
            2. Completeness (0-25 points)
            3. Regulatory appropriateness (0-25 points)
            4. Evidence supporting (0-25 points)
            
            Return JSON with:
            - total_score (0-100)
            - clinical_accuracy (0-25)
            - completeness (0-25)
            - regulatory_appropriateness (0-25)
            - evidence_supporting (0-25)
            - feedback (brief explanation)
            """
            system_prompt = f"You are evaluating an answer to an inspector question from a {self.persona['name']}."
            try:
                result = call_medical_llm(prompt, system_prompt, task_type="general", max_tokens=400)
                # Try to parse JSON if returned
                if result and isinstance(result, str):
                    try:
                        parsed = json.loads(result)
                        if isinstance(parsed, dict):
                            return parsed
                    except:
                        pass
            except Exception:
                pass
        
        # Fallback scoring (simple heuristics)
        score = 70  # Default passing score
        breakdown = {
            "clinical_accuracy": 17,
            "completeness": 17,
            "regulatory_appropriateness": 18,
            "evidence_supporting": 18
        }
        
        # Simple checks
        if len(answer) < 50:
            score -= 20
            breakdown["completeness"] -= 10
        
        if "evidence" not in answer.lower() and "document" not in answer.lower():
            score -= 15
            breakdown["evidence_supporting"] -= 10
        
        return {
            "score": max(0, min(100, score)),
            "breakdown": breakdown,
            "feedback": "Answer evaluated. Consider providing more specific evidence and documentation."
        }
    
    def _generate_feedback(self, score_result: Dict[str, Any], question_data: Dict[str, Any]) -> str:
        """Generate feedback on the answer."""
        score = score_result["score"]
        
        if score >= 80:
            return "✓ Excellent answer. The inspector is satisfied with your response."
        elif score >= 60:
            return "⚠ Acceptable answer, but some areas could be strengthened. The inspector may ask follow-up questions."
        elif score >= 40:
            return "⚠️ Weak answer. The inspector is not fully satisfied. Consider providing more detail and evidence."
        else:
            return "❌ Insufficient answer. The inspector is concerned and will escalate this issue."
    
    def _determine_next_action(self, score: float) -> str:
        """Determine next action based on score."""
        if score >= 80:
            return "continue"
        elif score >= 60:
            return "clarify"
        elif score >= 40:
            return "escalate"
        else:
            return "formal_deficiency"
    
    def _analyze_deficiencies(self) -> List[Dict[str, Any]]:
        """Analyze conversation history to identify deficiencies."""
        deficiencies = []
        
        low_scores = [
            h["data"] for h in self.conversation_history
            if h.get("type") == "answer" and h["data"].get("score", 100) < 60
        ]
        
        for answer_data in low_scores:
            deficiencies.append({
                "issue": "Insufficient documentation or justification",
                "severity": "Major" if answer_data.get("score", 0) < 40 else "Minor",
                "context": "Answer to inspector question scored below acceptable threshold"
            })
        
        return deficiencies
    
    def _build_observation_letter_prompt(
        self,
        deficiencies: List[Dict[str, Any]],
        signal_data: Optional[Dict[str, Any]]
    ) -> str:
        """Build prompt for generating observation letter."""
        return f"""
        Generate a formal {self.persona['agency']} observation letter (Form 483 equivalent) based on:
        
        Agency: {self.persona['agency']}
        Persona: {self.persona['name']}
        Regulations: {self.persona['regulations']}
        
        Identified Deficiencies:
        {json.dumps(deficiencies, indent=2)}
        
        Signal Context:
        {json.dumps(signal_data or {}, indent=2)}
        
        Generate a professional, regulatory-compliant observation letter that:
        1. Lists each deficiency clearly
        2. Cites relevant regulations
        3. Requests corrective actions
        4. Sets timelines for response
        5. Maintains formal inspector tone
        
        Structure:
        - Header with agency and date
        - Introduction
        - List of observations/deficiencies
        - Regulatory citations
        - Request for response
        - Closing
        """
    
    def _generate_fallback_observation_letter(self, deficiencies: List[Dict[str, Any]]) -> str:
        """Generate fallback observation letter if LLM unavailable."""
        letter = f"""
        {self.persona['agency']} OBSERVATION LETTER
        
        Date: {datetime.now().strftime('%Y-%m-%d')}
        
        Dear Safety Team,
        
        During our review, the following observations were noted:
        
        """
        
        for i, deficiency in enumerate(deficiencies, 1):
            letter += f"\n{i}. {deficiency.get('issue', 'Compliance issue identified')}\n"
            letter += f"   Severity: {deficiency.get('severity', 'Major')}\n"
        
        letter += f"\n\nPlease provide a response addressing these observations within 30 days.\n"
        letter += f"\nRegulations cited: {self.persona['regulations']}\n"
        
        return letter


def simulate_inspector_question(
    df: Optional[Any] = None,
    persona: str = "FDA Clinical Reviewer",
    signal_data: Optional[Dict[str, Any]] = None,
    portfolio_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Convenience function to generate a single inspector question.
    
    Args:
        df: Safety data DataFrame
        persona: Inspector persona name
        signal_data: Signal-specific data
        portfolio_data: Portfolio-level risk data
        
    Returns:
        Question dictionary
    """
    simulator = InspectorSimulator(persona)
    return simulator.generate_inspector_question(df, signal_data, portfolio_data)


def inspector_followup(
    user_answer: str,
    question_data: Dict[str, Any],
    persona: str = "FDA Clinical Reviewer"
) -> Dict[str, Any]:
    """
    Convenience function to evaluate an answer and get follow-up.
    
    Args:
        user_answer: User's answer text
        question_data: Original question data
        persona: Inspector persona name
        
    Returns:
        Evaluation dictionary with score and feedback
    """
    simulator = InspectorSimulator(persona)
    return simulator.evaluate_answer(user_answer, question_data)

