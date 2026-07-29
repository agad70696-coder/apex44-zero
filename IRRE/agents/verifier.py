# Verifier - أهم روبوت في IRRE
# وظيفته: يرفض أي ادعاء بدون دليل
from IRRE.core.evidence import Claim

class VerifierAgent:
    def verify(self, claim: Claim):
        ok = claim.verify()
        if not ok:
            print(f"❌ REJECTED: {claim.text}")
            return False
        print(f"✅ VERIFIED: {claim.text}")
        return True

    def final_gate(self, claims):
        all_ok = all(c.status == "verified" for c in claims)
        if all_ok:
            print("🔒 IRRE GATE PASSED - For Eternity Locked")
            return True
        else:
            print("🔴 IRRE GATE FAILED - Evidence missing")
            return False
