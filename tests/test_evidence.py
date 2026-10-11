from IRRE.ai.ai_evidence import AIModelEvidence
from IRRE.crypto.post_quantum import QuantumSafeEvidence
from IRRE.ledger.evidence_chain import EvidenceChain


def test_full_flow() -> None:
    ai = AIModelEvidence("test-v1", "test prompt", "test output")
    assert ai.verify()

    pq = QuantumSafeEvidence("test-v1")
    proof = pq.export_proof(ai.hash)
    assert pq.verify_seal(ai.hash, proof["quantum_seal"])

    ledger = EvidenceChain(crypto=pq)
    block = ledger.add(ai.hash, proof["quantum_seal"], metadata={"model": "test-v1"})
    assert block["index"] == 0
    result = ledger.verify_chain()
    assert result["valid"]
    assert result["records"] == 1
    assert result["pqc_proof_validation"] == "VERIFIED"

    # Mutate persisted payload without updating the recorded digest; verification must fail.
    ledger.conn.execute(
        "UPDATE evidence_chain SET data_json = ? WHERE id = ?",
        ('{"ai_hash":"tampered","metadata":{},"pq_seal":"tampered"}', block["id"]),
    )
    ledger.conn.commit()
    assert not ledger.verify()
    ledger.close()
