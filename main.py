from IRRE.ai.ai_evidence import AIModelEvidence
from IRRE.crypto.post_quantum import QuantumSafeEvidence
from IRRE.ledger.evidence_chain import EvidenceChain


def main() -> None:
    print("=== IRRE - apex44-zero | Post-Quantum Evidence ===")

    # 1 - AI Evidence
    ai = AIModelEvidence(
        model_id="apex44-v1",
        prompt="What is the future of AI?",
        output="The future is promising and quantum-resistant",
    )
    print(f"AI Hash: {ai.hash}")

    # 2 - Quantum Safe Seal - 50 years valid
    pq = QuantumSafeEvidence(evidence_id="apex44-v1")
    proof = pq.export_proof(ai.hash)
    print(f"PQ Seal: {proof['quantum_seal']}")
    print(f"Algorithm: {proof['algorithm']}")

    # 3 - Immutable Chain
    ledger = EvidenceChain()
    block = ledger.add(
        ai_hash=ai.hash,
        pq_seal=proof["quantum_seal"],
        metadata={"model_id": "apex44-v1", "proof": proof},
    )

    print(f"Block #{block['index']} Created: {block['block_hash']}")
    print(f"Chain Valid: {ledger.verify()}")

    # Save chain
    with open("evidence_chain.json", "w", encoding="utf-8") as f:
        f.write(ledger.export())

    print("\nDone! Evidence is valid for 50 years and quantum-resistant.")


if __name__ == "__main__":
    main()
