"""
IRRE - Behavioral Agent
يفهم ليه الإنسان قال الادعاء، مش بس هل هو صح
"""


try:
    from IRRE.agents.verifier import VerifierAgent
    from IRRE.core.evidence import Claim
    from IRRE.psychology.behavioral_logic import BehavioralAnalyzer, BehavioralLaw
except ImportError:
    from behavioral_logic import BehavioralAnalyzer, BehavioralLaw
    class VerifierAgent:
        def final_gate(self, claim) -> dict:
            return {"pass": len(claim.evidences) > 0}
    class Claim:
        def __init__(self, text, evidences):
            self.text = text
            self.evidences = evidences

class BehavioralAgent:
    def __init__(self):
        self.verifier = VerifierAgent()
        self.behavioral_law = BehavioralLaw()
        self.analyzer = BehavioralAnalyzer()

    def audit_claim(self, claim) -> dict:
        behavioral_result = self.behavioral_law.final_behavioral_gate(claim)
        factual_pass = behavioral_result["factual_pass"]
        bias = behavioral_result["behavioral_analysis"]["bias"].value
        motive = behavioral_result["behavioral_analysis"]["motive"].value

        if not factual_pass and bias == "overconfidence_bias":
            verdict = "REJECTED - Overconfidence without evidence"
            human_explanation = "الإنسان يدعي 6.0 ليثبت ذاته، لكن لا يوجد دليل."
        elif factual_pass and motive == "truth_seeking":
            verdict = "VERIFIED - Factual + Truth-seeking"
            human_explanation = "الادعاء مدعوم بدليل ورغبة في الحقيقة."
        elif not factual_pass:
            verdict = "REJECTED - No Evidence"
            human_explanation = "لا يوجد دليل. No Evidence = No Claim"
        else:
            verdict = "VERIFIED"
            human_explanation = "تم التحقق."

        return {
            "claim_text": claim.text,
            "factual_pass": factual_pass,
            "bias": bias,
            "motive": motive,
            "verdict": verdict,
            "human_explanation": human_explanation,
            "full_audit": behavioral_result["audit_message"] + f" | {verdict}",
            "is_explainable": True
        }

if __name__ == "__main__":
    print("🧠 BehavioralAgent - Self Test")
    class FakeClaim:
        def __init__(self, text, evidences):
            self.text = text
            self.evidences = evidences

    agent = BehavioralAgent()
    claim1 = FakeClaim("مشروعي 6.0 ثوري عالمي فريد", [])
    result1 = agent.audit_claim(claim1)
    print(f"Test 1: {result1['full_audit']}")
    print(f"Human: {result1['human_explanation']}")
    print("🔒 BehavioralAgent Locked")
