import numpy as np
from ai.medical_llm import MedicalLLM

class BenefitRiskEngine:

    def __init__(self):
        self.llm = MedicalLLM()

    def _system_prompt(self):
        return """
You are an expert in:
- EMA Benefit–Risk Methodologies
- PRAC Frameworks
- FDA Benefit–Risk Assessment Guidance
- ICH E2C(R2) PBRER benefit–risk sections

Generate structured, compliant benefit–risk outputs.
"""

    def compute_scores(self, benefit_data, risk_data):
        """
        benefit_data = [{ "name": "efficacy", "value": 0.76, "weight": 0.5 }, ...]
        risk_data     = [{ "name": "risk_bad", "value": 0.3, "weight": 0.7 }, ...]

        value = effect magnitude (0 to 1)
        weight = importance (0 to 1)
        """
        benefit_score = np.sum([b["value"] * b["weight"] for b in benefit_data])
        risk_score    = np.sum([r["value"] * r["weight"] for r in risk_data])
        bri = benefit_score - risk_score

        return {
            "benefit_score": float(benefit_score),
            "risk_score": float(risk_score),
            "benefit_risk_index": float(bri)
        }

    def generate_narrative(self, benefit_data, risk_data, bri):
        user_prompt = f"""
Data:
Benefits: {benefit_data}
Risks: {risk_data}
BRI Score: {bri}

Generate:

1. Executive Summary (2-3 lines)
2. Key Benefits (list)
3. Key Risks (list)
4. Benefit–Risk Interpretation
5. Recommended Regulatory Position
6. Suggested Next Steps

Style: ICH E2C(R2), EMA PRAC wording.
"""

        return self.llm.generate(self._system_prompt(), user_prompt)

    def evaluate(self, benefit_data, risk_data):
        scores = self.compute_scores(benefit_data, risk_data)
        narrative = self.generate_narrative(
            benefit_data, risk_data, scores["benefit_risk_index"]
        )
        return { "scores": scores, "narrative": narrative }
