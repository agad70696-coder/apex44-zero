"""
APEX-44 v4.0 - Point 2: Deontic Logic Ethical Engine
Science: Von Wright 1951 Deontic Logic (Obligatory, Permitted, Forbidden)
"""
from enum import Enum
from datetime import datetime

class DeonticOperator(Enum):
    OBLIGATORY = "واجب"  # O
    PERMITTED = "مسموح"  # P
    FORBIDDEN = "ممنوع"  # F

class EthicalEngineV2:
    """
    محرك قانوني يمنع النظام يتحول لأداة ظلم
    """

    def __init__(self):
        # قاعدة القوانين القانونية
        self.laws = [
            {
                "id": "LAW-01",
                "condition": lambda ctx: ctx.get("action") == "forge_evidence",
                "operator": DeonticOperator.FORBIDDEN,
                "reason": "تزوير الأدلة جريمة - مادة 112 عقوبات"
            },
            {
                "id": "LAW-02",
                "condition": lambda ctx: ctx.get("contains_minor") == True and ctx.get("action") == "publish",
                "operator": DeonticOperator.FORBIDDEN,
                "reason": "نشر بيانات قاصر ممنوع - قانون الطفل"
            },
            {
                "id": "LAW-03",
                "condition": lambda ctx: ctx.get("action") == "verify",
                "operator": DeonticOperator.OBLIGATORY,
                "reason": "يجب تسجيل كل عملية تحقق في سجل غير قابل للمسح"
            },
            {
                "id": "LAW-04",
                "condition": lambda ctx: ctx.get("owner") == ctx.get("user") and ctx.get("action") == "watermark",
                "operator": DeonticOperator.PERMITTED,
                "reason": "مسموح توثيق ملكيتك الخاصة"
            },
            {
                "id": "LAW-05",
                "condition": lambda ctx: ctx.get("owner") != ctx.get("user") and ctx.get("action") == "remove_watermark",
                "operator": DeonticOperator.FORBIDDEN,
                "reason": "إزالة علامة ملكية الغير سرقة أدبية - مادة 181"
            },
            {
                "id": "LAW-06",
                "condition": lambda ctx: ctx.get("coercion") == True,
                "operator": DeonticOperator.FORBIDDEN,
                "reason": "الاستخدام تحت إكراه أو تهديد مرفوض"
            }
        ]

    def evaluate(self, context: dict) -> dict:
        """
        context = {
          "action": "watermark" / "verify" / "remove_watermark" / "forge_evidence",
          "owner": "amr",
          "user": "amr",
          "contains_minor": False,
          "coercion": False
        }
        """
        violations = []
        obligations = []

        for law in self.laws:
            if law["condition"](context):
                if law["operator"] == DeonticOperator.FORBIDDEN:
                    violations.append(law)
                elif law["operator"] == DeonticOperator.OBLIGATORY:
                    obligations.append(law)

        if violations:
            return {
                "decision": "FORBIDDEN",
                "allowed": False,
                "violations": violations,
                "timestamp": datetime.utcnow().isoformat(),
                "meaning": f"النظام رفض تنفيذ {context.get('action')} لأنه ممنوع قانوناً"
            }

        return {
            "decision": "PERMITTED",
            "allowed": True,
            "obligations": obligations,
            "timestamp": datetime.utcnow().isoformat(),
            "meaning": "مسموح قانوناً مع وجوب التسجيل"
        }

# اختبار سريع
if __name__ == "__main__":
    engine = EthicalEngineV2()
    # محاولة تزوير
    print(engine.evaluate({"action": "forge_evidence"}))
    # محاولة عادية
    print(engine.evaluate({"action": "watermark", "owner": "amr", "user": "amr"}))
