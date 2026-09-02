"""
APEX44 Core Engine
Author: Amr Gad

القلب الرئيسي للمشروع.
يقوم بربط جميع الوحدات معًا.
"""

from apex44.ai.reasoner import Reasoner
from apex44.ai.verifier import Verifier


class ApexEngine:
    """المحرك الرئيسي."""

    def __init__(self) -> None:
        self.reasoner = Reasoner()
        self.verifier = Verifier()

    def analyze(self, claim: str):
        """
        تحليل مطالبة.
        """

        reasoning = self.reasoner.analyze(claim)
        verification = self.verifier.verify(claim)

        return {
            "claim": claim,
            "reasoning": reasoning,
            "verification": verification,
        }
