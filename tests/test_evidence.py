from IRRE.ai.ai_evidence import AIModelEvidence
from IRRE.crypto.post_quantum import QuantumSafeEvidence
from IRRE.ledger.evidence_chain import EvidenceChain


def test_full_flow() -> None:
    ai = AIModelEvidence("test-v1", "test prompt", "test output")
    assert ai.verify()
    print("Test 1 - AI Evidence: PASS")

    pq = QuantumSafeEvidence("test-v1")
    proof = pq.export_proof(ai.hash)
    assert pq.verify_seal(ai.hash, proof["quantum_seal"])
    print("Test 2 - PQ Seal: PASS")

    ledger = EvidenceChain()
    ledger.add(ai.hash, proof["quantum_seal"])
    assert ledger.verify()
    print("Test 3 - Chain: PASS")

    ledger.chain[0]["ai_hash"] = "tampered"
    assert not ledger.verify()
    print("Test 4 - Tamper Detection: PASS")

    print("All tests passed - 50 year proof is valid!")


if __name__ == "__main__":
    test_full_flow()
