import hashlib, json, time
from pathlib import Path

class EvidenceChain:
    def __init__(self, chain_file="evidence_chain.json"):
        self.chain_file = Path(chain_file)
        self.chain = []
        if self.chain_file.exists():
            try:
                self.chain = json.loads(self.chain_file.read_text())
            except: self.chain = []
        if not self.chain:
            self._create_genesis()

    def _create_genesis(self):
        genesis = {
            "index": 0,
            "prev_hash": "0"*64,
            "ai_hash": "GENESIS",
            "quantum_seal": "GENESIS",
            "public_key": "GENESIS",
            "algorithm": "GENESIS",
            "timestamp": time.time(),
            "metadata": {"note": "Genesis Block"}
        }
        genesis["block_hash"] = self._hash_block(genesis)
        self.chain.append(genesis)
        self._save()

    def _hash_block(self, block):
        data = f"{block['index']}{block['prev_hash']}{block['ai_hash']}{block['quantum_seal']}{block['timestamp']}"
        return hashlib.sha3_256(data.encode()).hexdigest()

    def add(self, ai_hash, quantum_seal, metadata, public_key, algorithm):
        prev = self.chain[-1]
        block = {
            "index": len(self.chain),
            "prev_hash": prev["block_hash"],
            "ai_hash": ai_hash,
            "quantum_seal": quantum_seal,
            "public_key": public_key,
            "algorithm": algorithm,
            "timestamp": time.time(),
            "metadata": metadata
        }
        block["block_hash"] = self._hash_block(block)
        self.chain.append(block)
        self._save()
        return block

    def _save(self):
        self.chain_file.write_text(json.dumps(self.chain, indent=2))

    def verify(self):
        for i in range(1, len(self.chain)):
            curr = self.chain[i]
            prev = self.chain[i-1]
            if curr["prev_hash"]!= prev["block_hash"]: return False
            if curr["block_hash"]!= self._hash_block(curr): return False
        return True
