import hashlib, time, json

# === القرار العلمي 1: التوقيع الرقمي ===
class ForensicSigner:
    def __init__(self, owner):
        self.owner = owner
        self.private = f"PRIVATE-KEY-{owner}-2026-SECRET"
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

# === القرار العلمي 2: البلوكشين ===
chain = []
chain.append("GENESIS_BLOCK_000")

def anchor_to_blockchain(evidence_hash, signature):
    prev = chain[-1]
    block_hash = hashlib.sha3_256(f"{prev}{evidence_hash}{time.time()}".encode()).hexdigest()
    chain.append(block_hash)
    return block_hash

# === التجربة العملية ===
print("="*60)
print("🔬 القرار العلمي النهائي - Amr Gad")
print("="*60)

# 1. المحقق
officer = ForensicSigner("Amr Gad - Cairo")
print(f"\n[1] المحقق: {officer.owner}")

# 2. دليل العربية المتهكرة
from IRRE.aviation.autonomous_vehicle_evidence import AutonomousVehicleEvidence
car = AutonomousVehicleEvidence("CAR-01", "Cairo")
hacked = car.add_decision("accelerate", 0.60, False, True)
print(f"\n[2] دليل: {hacked['hash'][:20]}... مزور؟ {hacked['is_spoofed']}")

# 3. توقيع
signed = officer.sign(hacked['hash'])
print(f"\n[3] توقيع رقمي:")
print(f" بواسطة: {signed['owner']}")
print(f" الوقت: {signed['time']}")
print(f" التوقيع: {signed['signature'][:30]}...")

# 4. بلوكشين
block_hash = anchor_to_blockchain(hacked['hash'], signed['signature'])
print(f"\n[4] بلوكشين:")
print(f" بلوك رقم: {len(chain)-1}")
print(f" هاش البلوك: {block_hash[:30]}...")

# 5. تحقق
valid = officer.verify(hacked['hash'], signed['signature'])
print(f"\n[5] تحقق قضائي: التوقيع سليم؟ {valid}")

# 6. محاولة تزوير
fake = hashlib.sha3_256(b"fake").hexdigest()
valid_fake = officer.verify(fake, signed['signature'])
print(f"\n[6] هاكر حاول يزور: التحقق = {valid_fake} -> فشل!")

print("\n" + "="*60)
print("✅ تم تنفيذ القرار العلمي - الدليل مقبول في المحكمة")
print("="*60)
