"""
APEX-SHIELD AI Verifier
يكشف تزوير الأدلة بالذكاء الاصطناعي
"""

import hashlib
from datetime import datetime


class AIVerifier:
    """
    نظام ذكاء اصطناعي بسيط لكشف الأنماط المشبوهة في الأدلة
    المرحلة 1: Rule-based + Statistical Analysis
    المرحلة 2: هنضيف Machine Learning
    """

    def __init__(self) -> None:
        self.known_hashes = set()
        self.suspicious_patterns = []

    def analyze_claim(self, claim_text: str, timestamp: str, hash_value: str) -> dict:
        """
        يحلل الدليل ويرجع تقرير ذكي
        """
        score = 100
        issues = []

        # 1. فحص الطول المشبوه
        if len(claim_text) < 5:
            score -= 30
            issues.append("النص قصير جدا - ممكن يكون مزور")

        # 2. فحص التكرار
        if hash_value in self.known_hashes:
            score -= 50
            issues.append("هذا الدليل مكرر - تم استخدامه قبل كده!")
        else:
            self.known_hashes.add(hash_value)

        # 3. فحص الوقت
        try:
            claim_time = datetime.fromisoformat(timestamp)
            if claim_time > datetime.now():
                score -= 100
                issues.append("تاريخ مستقبلي - مستحيل!")
        except:
            score -= 20
            issues.append("صيغة التاريخ غلط")

        # 4. حساب قوة التشفير
        strength = len(hash_value) * 4  # بت

        return {
            "is_trusted": score >= 70,
            "trust_score": max(0, score),
            "strength_bits": strength,
            "issues": issues,
            "ai_verdict": "موثوق ✅" if score >= 70 else "مشبوه ⚠️",
        }

    def batch_analyze(self, evidences: list[dict]) -> dict:
        """يحلل مجموعة أدلة مرة واحدة"""
        results = []
        for ev in evidences:
            result = self.analyze_claim(
                ev.get("claim", ""), ev.get("timestamp", ""), ev.get("hash", "")
            )
            results.append(result)

        trusted_count = sum(1 for r in results if r["is_trusted"])

        return {
            "total": len(results),
            "trusted": trusted_count,
            "suspicious": len(results) - trusted_count,
            "trust_rate": f"{trusted_count / len(results) * 100:.1f}%" if results else "0%",
            "details": results,
        }


# مثال للاستخدام
if __name__ == "__main__":
    verifier = AIVerifier()

    # دليل سليم
    claim1 = "العلم نور"
    hash1 = hashlib.sha256(claim1.encode()).hexdigest()

    result = verifier.analyze_claim(claim1, datetime.now().isoformat(), hash1)

    print("APEX-SHIELD AI Verifier 🛡️")
    print(f"النص: {claim1}")
    print(f"الحكم: {result['ai_verdict']}")
    print(f"نسبة الثقة: {result['trust_score']}%")
