from typing import Any

from .cultural_context import EgyptianCulturalContext
from .semantic_nlp import DeepSemanticAnalyzer


class LinguisticLogic:
    def __init__(self) -> None:
        self.cultural = EgyptianCulturalContext()
        self.semantic = DeepSemanticAnalyzer()

    def to_formal_logic(self, text: str) -> dict[str, Any]:
        analysis = self.semantic.analyze(text)
        intent = analysis["intent"]
        if intent == "build_request":
            formal = f"∃x: BuildRequest(x) ∧ Urgency(HIGH) ∧ Lang(EG) ∧ Term('{text}')"
        elif intent == "location_query":
            formal = "∃f: File(f) ∧ Index(3) ∧ Query(Location(f))"
        elif intent == "philosophical_example":
            formal = "Entity(Cairo,City) ∧ located_in(Cairo,Egypt) ∧ ¬Equal(Cairo,String)"
        elif intent == "status_claim":
            formal = "Claim(c) ∧ Cap(6.0) ∧ Ev(0) → Bias(overconfidence)"
        else:
            formal = analysis["formal_logic"]
        return {
            "original": text,
            "formal_logic": formal,
            "preserved_intent": analysis["social_meaning"],
            "translation": self.translate_preserving_intent(text),
        }

    def translate_preserving_intent(self, text: str) -> str:
        m = {
            "ابنى": "Build it now - full layer immediately (Egyptian urgent trust)",
            "فين 3": "Where is file 3? Built 2, missing third",
            "القاهرة مش كلمة": "Cairo is not a word, it's entity inside Egypt",
            "مشروعي 6.0 ثوري": "My project 6.0 revolutionary (status claim without evidence)",
        }
        return m.get(text, f"'{text}' → intent preserved")

    def full_report(self, text: str) -> str:
        a = self.semantic.analyze(text)
        l = self.to_formal_logic(text)
        return f"📝 '{text}':\n Social: {a['social_meaning']}\n Intent: {a['intent']}\n Bias: {a['bias_detected']}\n Formal: {l['formal_logic']}\n Translation: {l['translation']}"
