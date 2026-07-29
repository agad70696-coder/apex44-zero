from.formal_logic import Rule

class ApexTheorems:
    @staticmethod
    def get_all_theorems() -> list:
        return [
            Rule("T1_NoEvidence_NoClaim", ["NOT_HasEvidence"], "NotVerifiable", "لا دليل = لا ادعاء", "∀c: ¬HasEvidence(c) → ¬Verifiable(c)"),
            Rule("T2_FullVerification", ["HasEvidence", "ValidQuote", "ValidURL"], "Verified", "تحقق كامل", "∀c: HasEvidence(c) ∧ ValidQuote(c) → Verified(c)"),
            Rule("T3_Overconfidence_Motive", ["BiasOverconfidence", "NOT_HasEvidence"], "MotiveStatusSeeking", "6.0 بدون دليل = مكانة", "∀c: Bias(c) ∧ ¬HasEvidence(c) → Motive(c)"),
            Rule("T4_EternityLock", ["Verified", "HasAuditRecord"], "EternityLocked", "موثق = مقفول للأبد", "∀c: Verified(c) ∧ HasAudit(c) → Locked(c)"),
        ]
