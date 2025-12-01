"""
Multi-Signal Inspector Challenge Engine (CHUNK 6.22.5)
Simulates the hardest real FDA/EMA inspection scenarios:
- Multiple signals at once
- Class effect interrogation
- Cross-linking patterns
- Inconsistent rationales
- Cross-signal consistency challenges
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

try:
    from src.ai.inspector_simulation import InspectorSimulator
    SIMULATION_AVAILABLE = True
except ImportError:
    SIMULATION_AVAILABLE = False

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
    from src.ai.risk_prioritization import RiskPrioritizationEngine
    RPF_AVAILABLE = True
except ImportError:
    RPF_AVAILABLE = False


class MultiSignalInspectorChallenge:
    """
    Multi-signal inspector challenge engine.
    
    Features:
    - Cross-signal questioning
    - Class effect interrogation
    - Consistency challenges
    - Rationale discrepancies
    - Priority justification
    """
    
    def __init__(self, signals: List[Dict[str, Any]], persona: str = "FDA Pharmacovigilance Inspector"):
        """
        Initialize multi-signal challenge.
        
        Args:
            signals: List of signal dictionaries with drug, reaction, RPF score, priority, etc.
            persona: Inspector persona to use
        """
        self.signals = signals
        self.persona = persona
        self.inspector = InspectorSimulator(persona) if SIMULATION_AVAILABLE else None
        self.challenge_transcript: List[Dict[str, Any]] = []
        self.current_question_index = 0
    
    def analyze_signal_patterns(self) -> Dict[str, Any]:
        """
        Analyze signals for patterns that inspectors would question.
        
        Returns:
            Dictionary with patterns, inconsistencies, and class effects
        """
        patterns = {
            "class_effects": [],
            "inconsistencies": [],
            "priority_discrepancies": [],
            "timeline_gaps": [],
            "rationale_gaps": []
        }
        
        # Group signals by drug class
        drug_classes = {}
        for signal in self.signals:
            drug = signal.get("drug", "Unknown")
            drug_class = signal.get("drug_class", "Unknown")
            if drug_class not in drug_classes:
                drug_classes[drug_class] = []
            drug_classes[drug_class].append(signal)
        
        # Detect class effects
        for drug_class, class_signals in drug_classes.items():
            if len(class_signals) >= 2:
                reactions = [s.get("reaction", "") for s in class_signals]
                unique_reactions = set(reactions)
                if len(unique_reactions) < len(class_signals):
                    patterns["class_effects"].append({
                        "drug_class": drug_class,
                        "signals": class_signals,
                        "common_reactions": [r for r in reactions if reactions.count(r) > 1],
                        "description": f"Multiple signals in {drug_class} class suggesting potential class effect"
                    })
        
        # Detect priority discrepancies
        priority_scores = {}
        for signal in self.signals:
            priority = signal.get("priority", "Unknown")
            rpf_score = signal.get("rpf_score", 0)
            
            if priority not in priority_scores:
                priority_scores[priority] = []
            priority_scores[priority].append(rpf_score)
        
        # Check for inconsistencies (low RPF but high priority, or vice versa)
        for signal in self.signals:
            priority = signal.get("priority", "Unknown")
            rpf_score = signal.get("rpf_score", 50)
            
            if priority == "High" and rpf_score < 50:
                patterns["priority_discrepancies"].append({
                    "signal": signal,
                    "issue": f"High priority assigned but low RPF score ({rpf_score})",
                    "type": "high_priority_low_rpf"
                })
            elif priority == "Low" and rpf_score > 70:
                patterns["priority_discrepancies"].append({
                    "signal": signal,
                    "issue": f"Low priority assigned but high RPF score ({rpf_score})",
                    "type": "low_priority_high_rpf"
                })
        
        # Detect timeline gaps (signals detected long after first case)
        for signal in self.signals:
            first_case_date = signal.get("first_case_date")
            detection_date = signal.get("detection_date")
            if first_case_date and detection_date:
                # This would require date parsing, simplified here
                patterns["timeline_gaps"].append({
                    "signal": signal,
                    "first_case": first_case_date,
                    "detection": detection_date
                })
        
        return patterns
    
    def generate_cross_signal_questions(self) -> List[str]:
        """
        Generate high-pressure cross-signal inspection questions.
        
        Returns:
            List of inspection questions
        """
        patterns = self.analyze_signal_patterns()
        
        questions = []
        
        # Class effect questions
        if patterns["class_effects"]:
            class_effect = patterns["class_effects"][0]
            questions.append(
                f"You have {len(class_effect['signals'])} signals in the {class_effect['drug_class']} class. "
                f"These signals involve reactions: {', '.join(set(class_effect['common_reactions']))}. "
                f"What is your justification for not treating this as a class effect that requires "
                f"portfolio-wide risk management? Why were these assessed separately rather than together?"
            )
        
        # Priority discrepancy questions
        if patterns["priority_discrepancies"]:
            discrepancy = patterns["priority_discrepancies"][0]
            signal = discrepancy["signal"]
            questions.append(
                f"Signal {signal.get('drug', 'Unknown')} - {signal.get('reaction', 'Unknown')} is "
                f"marked as {signal.get('priority', 'Unknown')} priority, but has an RPF score of "
                f"{signal.get('rpf_score', 0)}. Can you explain this discrepancy? What additional "
                f"factors led to this priority assignment that are not reflected in the RPF score?"
            )
        
        # Cross-signal consistency questions
        if len(self.signals) >= 2:
            high_priority = [s for s in self.signals if s.get("priority") == "High"]
            low_priority = [s for s in self.signals if s.get("priority") == "Low"]
            
            if high_priority and low_priority:
                high_signal = high_priority[0]
                low_signal = low_priority[0]
                
                questions.append(
                    f"You have {high_signal.get('drug', 'Unknown')} - {high_signal.get('reaction', 'Unknown')} "
                    f"marked as High priority ({high_signal.get('rpf_score', 0)} RPF), but "
                    f"{low_signal.get('drug', 'Unknown')} - {low_signal.get('reaction', 'Unknown')} "
                    f"is marked as Low priority ({low_signal.get('rpf_score', 0)} RPF). "
                    f"Can you explain the rationale for this prioritization? What makes one signal "
                    f"more urgent than the other? Were the same assessment criteria applied to both?"
                )
        
        # Why escalation/not escalation questions
        escalated = [s for s in self.signals if s.get("status") in ["Escalated", "Under Assessment", "Validated"]]
        not_escalated = [s for s in self.signals if s.get("status") in ["New", "Open"]]
        
        if escalated and not_escalated:
            questions.append(
                f"You have {len(escalated)} escalated signal(s) and {len(not_escalated)} non-escalated signal(s). "
                f"What criteria did you use to decide which signals to escalate? Can you show me the "
                f"decision rationale for each? Why did signal {escalated[0].get('drug', 'Unknown')} - "
                f"{escalated[0].get('reaction', 'Unknown')} get escalated but signal "
                f"{not_escalated[0].get('drug', 'Unknown')} - {not_escalated[0].get('reaction', 'Unknown')} did not?"
            )
        
        # Use LLM to generate additional questions if available
        if LLM_AVAILABLE and len(questions) < 5:
            try:
                ai_questions = self._generate_ai_cross_signal_questions(patterns)
                questions.extend(ai_questions[:5 - len(questions)])
            except Exception:
                pass
        
        # Fallback questions
        if not questions:
            questions = [
                "How do you ensure consistency in signal assessment across your portfolio?",
                "What is your process for identifying class effects?",
                "How do you prioritize signals when multiple signals require attention simultaneously?",
                "What documentation do you maintain for signal escalation decisions?",
                "How do you handle signals with similar characteristics but different priority assignments?"
            ]
        
        return questions[:5]  # Limit to 5 questions
    
    def _generate_ai_cross_signal_questions(self, patterns: Dict[str, Any]) -> List[str]:
        """Generate AI-powered cross-signal questions."""
        prompt = f"""
        You are an {self.persona} conducting a multi-signal inspection.
        
        Active Signals:
        {json.dumps(self.signals, indent=2, default=str)}
        
        Detected Patterns:
        {json.dumps(patterns, indent=2, default=str)}
        
        Generate 3-5 high-pressure inspection questions that:
        - Challenge cross-signal consistency
        - Question prioritization rationale
        - Probe for class effects
        - Identify discrepancies or gaps
        - Test the sponsor's signal management process
        
        Format each question as a standalone string. Be direct, professional, and regulatory-focused.
        """
        
        system_prompt = f"You are an {self.persona} with expertise in multi-signal assessment and cross-product analysis."
        
        try:
            response = call_medical_llm(
                prompt,
                system_prompt,
                task_type="general",
                max_tokens=800,
                temperature=0.4
            )
            
            # Parse response into list of questions
            questions = []
            for line in response.split("\n"):
                line = line.strip()
                if line and (line.startswith("-") or line.startswith("•") or line.startswith("1.") or line.startswith("2.") or line.startswith("3.") or line.startswith("4.") or line.startswith("5.")):
                    # Remove numbering/bullets
                    question = line.lstrip("-•1234567890. ")
                    if question and len(question) > 20:
                        questions.append(question)
            
            return questions if questions else []
        except Exception:
            return []
    
    def generate_cross_link_followup(
        self,
        answer: str,
        question: str,
        challenge_type: str = "consistency"
    ) -> Dict[str, Any]:
        """
        Generate inspector follow-up that challenges the answer.
        
        Args:
            answer: User's answer
            question: Original question
            challenge_type: Type of challenge (consistency, timeline, evidence, rationale)
            
        Returns:
            Dictionary with follow-up question and escalation level
        """
        if not LLM_AVAILABLE:
            return {
                "followup": f"Your answer requires further clarification. Can you provide more specific evidence?",
                "escalation_level": 2,
                "challenge_type": challenge_type
            }
        
        prompt = f"""
        You are an {self.persona} challenging a sponsor's answer during inspection.
        
        Original Question:
        {question}
        
        Sponsor's Answer:
        {answer}
        
        Active Signals Context:
        {json.dumps(self.signals[:3], indent=2, default=str)}
        
        Challenge Type: {challenge_type}
        
        Generate a follow-up question that:
        - Contradicts or challenges inconsistencies in the answer
        - Points out missing evidence or documentation gaps
        - Questions timelines or decision rationale
        - Asks for specific justification or proof
        - Maintains professional but firm regulatory tone
        
        Be specific and reference the signals or data directly.
        """
        
        system_prompt = f"You are an {self.persona} conducting a thorough inspection with high standards for evidence and consistency."
        
        try:
            followup_text = call_medical_llm(
                prompt,
                system_prompt,
                task_type="general",
                max_tokens=500,
                temperature=0.3
            )
            
            # Determine escalation level based on challenge severity
            escalation_level = 2
            if any(keyword in followup_text.lower() for keyword in ["missing", "incomplete", "inconsistent", "contradiction"]):
                escalation_level = 3
            if any(keyword in followup_text.lower() for keyword in ["critical", "concerning", "deficiency", "violation"]):
                escalation_level = 4
            
            return {
                "followup": followup_text.strip(),
                "escalation_level": escalation_level,
                "challenge_type": challenge_type,
                "timestamp": datetime.now().isoformat()
            }
        except Exception:
            return {
                "followup": "Your answer requires further clarification. Please provide more specific evidence and documentation.",
                "escalation_level": 2,
                "challenge_type": challenge_type
            }
    
    def run_multi_signal_challenge(self) -> Dict[str, Any]:
        """
        Run complete multi-signal challenge session.
        
        Returns:
            Dictionary with questions, patterns, and challenge summary
        """
        patterns = self.analyze_signal_patterns()
        questions = self.generate_cross_signal_questions()
        
        return {
            "persona": self.persona,
            "signal_count": len(self.signals),
            "detected_patterns": patterns,
            "questions": questions,
            "timestamp": datetime.now().isoformat(),
            "challenge_summary": self._generate_challenge_summary(patterns, questions)
        }
    
    def _generate_challenge_summary(self, patterns: Dict[str, Any], questions: List[str]) -> str:
        """Generate summary of challenge focus areas."""
        summary_parts = []
        
        if patterns["class_effects"]:
            summary_parts.append(f"{len(patterns['class_effects'])} potential class effect(s) detected")
        
        if patterns["priority_discrepancies"]:
            summary_parts.append(f"{len(patterns['priority_discrepancies'])} priority discrepancy/ies identified")
        
        if patterns["inconsistencies"]:
            summary_parts.append(f"{len(patterns['inconsistencies'])} inconsistency/ies found")
        
        if summary_parts:
            return "Multi-signal challenge focuses on: " + ", ".join(summary_parts) + "."
        else:
            return "Standard multi-signal consistency review."


def generate_cross_signal_questions(signals: List[Dict[str, Any]], persona: str = "FDA Pharmacovigilance Inspector") -> List[str]:
    """
    Generate cross-signal reasoning questions (convenience function).
    
    Args:
        signals: List of signal dictionaries
        persona: Inspector persona
        
    Returns:
        List of inspection questions
    """
    challenge = MultiSignalInspectorChallenge(signals, persona)
    return challenge.generate_cross_signal_questions()


def generate_cross_link_followups(
    answer: str,
    signals: List[Dict[str, Any]],
    persona: str = "FDA Pharmacovigilance Inspector"
) -> Dict[str, Any]:
    """
    Generate inspector follow-up that challenges the answer (convenience function).
    
    Args:
        answer: User's answer
        signals: List of active signals
        persona: Inspector persona
        
    Returns:
        Dictionary with follow-up question and escalation
    """
    challenge = MultiSignalInspectorChallenge(signals, persona)
    return challenge.generate_cross_link_followup(answer, "", "consistency")
