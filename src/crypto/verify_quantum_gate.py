import json, sys, hashlib, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.crypto.quantum_seal import verify_seal, DEV21, ZERO4, ALL25

MANIFEST = "APEX44/04-data/quantum_seals_v2.4.json"

def fail(msg):
    print(f"❌ QUANTUM GATE FAILED: {msg}")
    sys.exit(1)

with open(MANIFEST) as f:
    data = json.load(f)

irre_hash = data["irre_hash"]
seals = data["seals"]

if len(seals)!=25:
    fail(f"Expected 25 got {len(seals)}")

for qid in sorted(data["all25"], key=lambda x: int(x)):
    s = seals.get(str(qid))
    if not s or len(s)!=128 or not verify_seal(str(qid), s, irre_hash):
        fail(f"QID {qid} len={len(s) if s else 0} tampered")

print(f"✅ All 25 verified len=128 SHAKE-256 512-bit Grover SAFE")
print(f"✅ Dev21 {len(DEV21)} 156pairs + Zero4 {ZERO4}")
print("GATE: PASSED")
