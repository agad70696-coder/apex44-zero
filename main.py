from IRRE.ai.ai_evidence import AIModelEvidence
from IRRE.crypto.forensic_signer import ForensicSigner
from IRRE.crypto.post_quantum import QuantumSafeEvidence
from IRRE.ledger.evidence_chain import EvidenceChain


def main() -> None:
    print("=== IRRE - apex44-zero | Post-Quantum Evidence ===")

    ai = AIModelEvidence(
        model_id="apex44-v1",
        prompt="What is the future of AI?",
        output="The future is promising and quantum-resistant",
    )
    print(f"AI Hash: {ai.hash}")

    pq = QuantumSafeEvidence(model_id="apex44-v1")
    proof = pq.export_proof(ai.hash)
    print(f"PQC Seal: {proof['quantum_seal']}")
    print(f"Algorithm: {proof['algorithm']}")

    ledger = EvidenceChain(crypto=pq, signer=ForensicSigner())
    block = ledger.add(
        ai_hash=ai.hash,
        pq_seal=str(proof["quantum_seal"]),
        metadata={"model_id": "apex44-v1", "proof": proof},
    )
    print(f"Block #{block['index']} Created: {block['block_hash']}")
    print(f"Chain Valid: {ledger.verify()}")

    with open("evidence_chain.json", "w", encoding="utf-8") as stream:
        stream.write(ledger.export())
    ledger.close()
    print("\nDone! Evidence chain export saved to evidence_chain.json.")


if __name__ == "__main__":
    main()
