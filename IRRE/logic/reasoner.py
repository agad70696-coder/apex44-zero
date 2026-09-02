from .formal_logic import Fact, KnowledgeBase


class AutomatedReasoner:
    def __init__(self, kb: KnowledgeBase) -> None:
        self.kb = kb
        self.proof_steps: list[str] = []
        self.inferred: list[Fact] = []

    def forward_chain(self, max_iterations: int = 10) -> list[Fact]:
        new_facts = True
        it = 0
        while new_facts and it < max_iterations:
            new_facts = False
            it += 1
            for rule in self.kb.rules:
                subjects = {f.subject for f in self.kb.facts.values()}
                for subject in subjects:
                    all(
                        self.kb.has_fact(p, subject, True)
                        or (
                            p.startswith("NOT_")
                            and not self.kb.has_fact(p.replace("NOT_", ""), subject, True)
                        )
                        for p in rule.premises
                        if not p.startswith("NOT_") or True
                    )
                    # Simplified check for demo
                    premises_ok = True
                    for pre in rule.premises:
                        if pre.startswith("NOT_"):
                            if self.kb.has_fact(pre.replace("NOT_", ""), subject, True):
                                premises_ok = False
                        elif not self.kb.has_fact(pre, subject, True):
                            premises_ok = False
                    if premises_ok:
                        key = f"{rule.conclusion}:{subject}"
                        if key not in self.kb.facts:
                            nf = Fact(rule.conclusion, subject, True, 0.95)
                            self.kb.facts[key] = nf
                            self.inferred.append(nf)
                            self.proof_steps.append(
                                f"Step: {rule.premises} for {subject} → {nf} via {rule.name}"
                            )
                            new_facts = True
        return self.inferred

    def prove_no_evidence_theorem(self, claim_id: str) -> dict:
        has_ev = self.kb.has_fact("HasEvidence", claim_id, True)
        if not has_ev:
            self.kb.add_fact("Verifiable", claim_id, False)
            self.proof_steps.append(
                f"Theorem Proved: ¬HasEvidence({claim_id}) → ¬Verifiable({claim_id}) | QED"
            )
            return {
                "proved": True,
                "verdict": "REJECTED - Mathematically Proven",
                "proof": self.proof_steps,
            }
        return {"proved": False, "verdict": "NEEDS_VERIFICATION", "proof": self.proof_steps}
