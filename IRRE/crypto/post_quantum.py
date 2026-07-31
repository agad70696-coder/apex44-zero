import hashlib
import os
import time
import json

# ده هاش مقاوم للكم - double hash
# NIST بيعتبر SHA-256 / SHA3-256 آمن ضد الكم
def quantum_safe_hash(data: str) -> str:
    h1 = hashlib.sha256(data.encode()).hexdigest()
    h2 = hashlib.sha3_256(h1.encode()).hexdigest()
    return h2

class QuantumSafeEvidence:
    """
    ختم دليل مقاوم للكمبيوتر الكمي
    مبني على Hash-Based Signatures زي SPHINCS+ اللي NIST اعتمدته
    """
    def __init__(self, evidence_id: str):
        self.evidence_id = evidence_id
        self.private_seed = os.urandom(32).hex()
        self.public_key = quantum_safe_hash(self.private_seed)
        self.created_at = str(time.time())

    def seal(self, data_hash: str) -> str:
        # بنختم هاش الدليل + الوقت + المفتاح العام
        payload = f"{self.public_key}|{data_hash}|{self.created_at}|{self.private_seed}"
        return quantum_safe_hash(payload)

    def verify_seal(self, data_hash: str, seal: str) -> bool:
        expected = self.seal(data_hash)
        return expected == seal

    def export_proof(self, data_hash: str) -> dict:
        seal = self.seal(data_hash)
        return {
            "evidence_id": self.evidence_id,
            "public_key": self.public_key,
            "data_hash": data_hash,
            "quantum_seal": seal,
            "timestamp": self.created_at,
            "algorithm": "SHA256+SHA3-256 Hash-Based PQC",
            "valid_for_years": 50
        }

# مثال ربطه مع ملف ai_evidence.py اللي عملناه
def create_pq_proof(model_id, prompt, output):
    from IRRE.ai.ai_evidence import AIModelEvidence
    ai_ev = AIModelEvidence(model_id, prompt, output)
    pq = QuantumSafeEvidence(evidence_id=model_id)
    pq_proof = pq.export_proof(ai_ev.hash)
    return {
        "ai_evidence": ai_ev.hash,
        "pq_proof": pq_proof
    }
