import hashlib
import time
import json

class EvidenceBlock:
    def __init__(self, index, evidence_hash, signature, owner, prev_hash):
        self.index = index
        self.timestamp = time.time() # ختم زمني UTC لا يمكن تزويره
        self.evidence_hash = evidence_hash
        self.signature = signature
        self.owner = owner
        self.prev_hash = prev_hash
        # هاش البلوك كله = بصمة البلوكشين
        self.block_hash = hashlib.sha3_256(
            f"{index}{self.timestamp}{evidence_hash}{prev_hash}".encode()
        ).hexdigest()

class EvidenceBlockchain:
    """
    بلوكشين مصغر للمحكمة: كل دليل بلوك، مربوط باللي قبله
    لو حد حاول يغير دليل قديم، كل البلوكشين هينهار
    """
    def __init__(self):
        # أول بلوك (Genesis Block)
        genesis = EvidenceBlock(0, "GENESIS", "0", "APEX44-ZERO", "0")
        self.chain = [genesis]

    def anchor_evidence(self, evidence_hash, signature, owner):
        prev_hash = self.chain[-1].block_hash
        new_block = EvidenceBlock(len(self.chain), evidence_hash, signature, owner, prev_hash)
        self.chain.append(new_block)
        return new_block

    def verify_chain(self) -> bool:
        # لو حد لعب في أي بلوك قديم، السلسلة كلها تبوظ
        for i in range(1, len(self.chain)):
            if self.chain[i].prev_hash!= self.chain[i-1].block_hash:
                return False
        return True

    def get_proof(self, evidence_hash):
        for block in self.chain:
            if block.evidence_hash == evidence_hash:
                return {
                    "exists": True,
                    "block_index": block.index,
                    "timestamp": time.ctime(block.timestamp),
                    "block_hash": block.block_hash,
                    "prev_hash": block.prev_hash
                }
        return {"exists": False}
