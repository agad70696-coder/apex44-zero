"""
IRRE - Applied Psychology & Behavioral Logic
No Evidence + No Motive = No Understanding
"""
from dataclasses import dataclass
from typing import List, Dict
from enum import Enum
import re

try:
    from IRRE.core.evidence import Evidence, Claim
except ImportError:
    class Evidence:
        def __init__(self, source_url: str, quote: str, confidence: float):
            self.source_url = source_url
            self.quote = quote
            self.confidence = confidence
        def is_valid(self):
            return self.source_url.startswith("http") and len(self.quote) > 10
    class Claim:
        def __init__(self, text: str, evidences: List):
            self.text = text
            self.evidences = evidences

class BiasType(str, Enum):
    NONE = "none"
    OVERCONFIDENCE = "overconfidence_bias"
    AUTHORITY = "authority_bias"
    SOCIAL_PROOF = "social_proof"
    STATUS_SEEKING = "status_seeking"

class MotiveType(str, Enum):
    TRUTH_SEEKING = "truth_seeking"
    STATUS_SEEKING = "status_seeking"
    FEAR_AVOIDANCE = "fear_avoidance"
    UNKNOWN = "unknown"

@dataclass
class BehavioralEvidence(Evidence):
    motive: MotiveType = MotiveType.UNKNOWN
    bias_type: BiasType = BiasType.NONE
    social_context: str = ""
    
    def is_psychologically_valid(self) -> bool:
        return self.is_valid() and self.motive != MotiveType.UNKNOWN and len(self.social_context) > 5

class BehavioralAnalyzer:
    BIAS_PATTERNS = {
        BiasType.OVERCONFIDENCE: [r"6\.0", r"ثوري", r"عالمي.*فريد", r"revolutionary"],
        BiasType.AUTHORITY: [r"أنا.*خبير", r"as an expert"],
        BiasType.SOCIAL_PROOF: [r"الكل.*يقول", r"everyone knows"],
    }
    MOTIVE_KEYWORDS = {
        MotiveType.STATUS_SEEKING: ["أنا", "مشروعي العالمي", "my project"],
        MotiveType.TRUTH_SEEKING: ["دليل", "مصدر", "evidence", "audit"],
    }

    def detect_bias(self, text: str) -> BiasType:
        for bias, patterns in self.BIAS_PATTERNS.items():
            for p in patterns:
                if re.search(p, text.lower()):
                    return bias
        return BiasType.NONE

    def infer_motive(self, text: str) -> MotiveType:
        for motive, kws in self.MOTIVE_KEYWORDS.items():
            if any(kw.lower() in text.lower() for kw in kws):
                return motive
        return MotiveType.UNKNOWN

    def analyze(self, claim_text: str) -> Dict:
        bias = self.detect_bias(claim_text)
        motive = self.infer_motive(claim_text)
        explanation = f"Bias={bias.value}, Motive={motive.value}. "
        if bias == BiasType.OVERCONFIDENCE:
            explanation += "Inflates capability without evidence."
        return {"bias": bias, "motive": motive, "explanation": explanation}

class BehavioralLaw:
    def __init__(self):
        self.analyzer = BehavioralAnalyzer()

    def final_behavioral_gate(self, claim: Claim) -> Dict:
        has_evidence = len(claim.evidences) > 0
        factual_pass = all(e.is_valid() for e in claim.evidences) if has_evidence else False
        analysis = self.analyzer.analyze(claim.text)
        return {
            "factual_pass": factual_pass,
            "behavioral_analysis": analysis,
            "final_pass": factual_pass,
            "audit_message": f"Factual: {'✅' if factual_pass else '❌'} | Bias: {analysis['bias'].value} | Motive: {analysis['motive'].value}"
        }
