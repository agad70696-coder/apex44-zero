
from IRRE.ai.ai_evidence import AIModelEvidence
from IRRE.crypto.post_quantum import QuantumSafeEvidence
from IRRE.ledger.evidence_chain import EvidenceChain

def test_full_flow():
    ai = AIModelEvidence("test-v1", "test prompt", "test output")
    assert ai.verify() == True
    print("Test 1 - AI Evidence: PASS")

    pq = QuantumSafeEvidence("test-v1")
    proof = pq.export_proof(ai.hash)
    assert pq.verify_seal(ai.hash, proof["quantum_seal"]) == True
    print("Test 2 - PQ Seal: PASS")

    ledger = EvidenceChain()
    block = ledger.add(ai.hash, proof["quantum_seal"])
    assert ledger.verify() == True
    print("Test 3 - Chain: PASS")

    ledger.chain[0]["ai_hash"] = "tampered"
    assert ledger.verify() == False
    print("Test 4 - Tamper Detection: PASS")

    print("All tests passed - 50 year proof is valid!")

if __name__ == "__main__":
    test_full_flow()
