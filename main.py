import hashlib, time, json

# 1- التوقيع الرقمي
class ForensicSigner:
    def __init__(self, owner):
        self.owner = owner
        self.private = f"PRIVATE-KEY-{owner}-2026"
        self.public = hashlib.sha3_256(self.private.encode()).hexdigest()

    def sign(self, evidence_hash):
        sig = hashlib.sha3_256(f"{self.private}{evidence_hash}".encode()).hexdigest()
        return {
            "owner": self.owner,
            "hash": evidence_hash,
            "signature": sig,
            "public": self.public,
            "time": time.ctime()
        }

    def verify(self, evidence_hash, signature):
        expected = hashlib.sha3_256(f"{self.private}{evidence_hash}".encode()).hexdigest()
        return expected == signature

# 2- البلوكشين
chain = ["GENESIS"]

def anchor(evidence_hash):
    prev = chain[-1]
    block_hash = hashlib.sha3_256(f"{prev}{evidence_hash}{time.time()}".encode()).hexdigest()
    chain.append(block_hash)
    return block_hash

# 3- التجربة العملية
print("APEX44-ZERO - القرار العلمي")

evidence_hash = hashlib.sha3_256(f"CAR-HACKED-{time.time()}".encode()).hexdigest()
print(f"دليل: {evidence_hash[:20]}...")

officer = ForensicSigner("Amr Gad - Cairo")
signed = officer.sign(evidence_hash)
print(f"توقيع بواسطة: {signed['owner']}")
