from IRRE.ai.ai_evidence import AIModelEvidence
from IRRE.crypto.post_quantum import QuantumSafeEvidence
from IRRE.ledger.evidence_chain import EvidenceChain

def main():
    print("=== IRRE - apex44-zero | Post-Quantum Evidence ===")
    
    # 1- دليل الـ AI
    ai = AIModelEvidence(
        model_id="apex44-v1",
        prompt="ما هو مستقبل الذكاء الاصطناعي؟",
        output="المستقبل واعد ومقاوم للكم"
    )
    print(f"AI Hash: {ai.hash}")

    # 2- ختم مقاوم للكمبيوتر الكمي - 50 سنة
    pq = QuantumSafeEvidence(evidence_id="apex44-v1")
    proof = pq.export_proof(ai.hash)
    print(f"PQ Seal: {proof['quantum_seal']}")
    print(f"Algorithm: {proof['algorithm']}")

    # 3- حطه في السلسلة الغير قابلة للتزوير
    ledger = EvidenceChain()
    block = ledger.add(
        ai_hash=ai.hash, 
        pq_seal=proof["quantum_seal"], 
        metadata={"model_id": "apex44-v1", "proof": proof}
    )
    
    print(f"Block #{block['index']} Created: {block['block_hash']}")
    print(f"Chain Valid: {ledger.verify()}")
    
    # احفظ السلسلة
    with open("evidence_chain.json", "w", encoding="utf-8") as f:
        f.write(ledger.export())
    
    print("\nتمام! الدليل بقى صالح 50 سنة ومقاوم للكم.")

if __name__ == "__main__":
    main()
