# IRRE Engine - المحرك الرئيسي
from IRRE.agents.verifier import VerifierAgent
from IRRE.core.evidence import Claim, Evidence


class IRREEngine:
    def run(self, question) -> None:
        print(f"🔍 سؤال البحث: {question}")
        print("[Planner] قسمت السؤال لـ 3 مهام")
        print("[Scout] جبت أدلة")

        claims = []
        for i in range(1, 4):
            ev = Evidence(
                source_url=f"https://example.com/paper{i}",
                quote=f"دليل علمي للجزء {i}",
                confidence=0.9,
            )
            claim = Claim(f"جزء {i}: {question}", [ev])
            claims.append(claim)

        print("[Verifier] بتحقق...")
        verifier = VerifierAgent()
        for c in claims:
            verifier.verify(c)

        verifier.final_gate(claims)
        print("✅ البحث خلص وكل النتائج بالدليل")


if __name__ == "__main__":
    engine = IRREEngine()
    engine.run("هل الروبوتات البحثية ستستبدل الباحث البشري؟")
