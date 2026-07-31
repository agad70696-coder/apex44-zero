from apex44.domain.models import Claim, Evidence


class AIVerifier:
    """
    Rule-based verifier for claims and evidence.
    """

    def analyze_claim(self, claim: Claim, evidence: Evidence) -> dict:
        score = evidence.confidence

        if not claim.is_valid():
            return {
                "status": "invalid",
                "score": 0.0,
                "message": "Invalid claim.",
            }

        if evidence.verify(claim):
            verdict = "verified"
        elif score >= 0.5:
            verdict = "partially_verified"
        else:
            verdict = "rejected"

        return {
            "status": verdict,
            "score": score,
            "claim_hash": claim.hash(),
        }
