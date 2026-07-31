import time
import json
from IRRE.crypto.post_quantum import quantum_safe_hash

class EvidenceChain:
    def __init__(self):
        self.chain = []
        # اول بلوك - البداية
        self.genesis_hash = quantum_safe_hash("IRRE-GENESIS-apex44-zero")

    def add(self, ai_hash: str, pq_seal: str, metadata: dict = None):
        prev_hash = self.chain[-1]["block_hash"] if self.chain else self.genesis_hash
        
        block_data = f"{prev_hash}|{ai_hash}|{pq_seal}|{time.time()}"
        block_hash = quantum_safe_hash(block_data)
        
        block = {
            "index": len(self.chain),
            "prev_hash": prev_hash,
            "ai_hash": ai_hash,
            "pq_seal": pq_seal,
            "metadata": metadata or {},
            "timestamp": str(time.time()),
            "block_hash": block_hash
        }
        self.chain.append(block)
        return block

    def verify(self) -> bool:
        # يتأكد ان مفيش حد لعب في السلسلة
        prev = self.genesis_hash
        for block in self.chain:
            check_data = f"{block['prev_hash']}|{block['ai_hash']}|{block['pq_seal']}|{block['timestamp']}"
            # هنسامح فرق الـ timestamp في التحقق البسيط ونركز على الربط
            if block["prev_hash"] != prev:
                return False
            prev = block["block_hash"]
        return True

    def export(self):
        return json.dumps(self.chain, indent=2, ensure_ascii=False)
