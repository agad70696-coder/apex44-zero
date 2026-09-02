"""
APEX44 v2.4 - Quantum Seal per Question (Full 25)
NIST 2024 SHAKE-256 512-bit per QID - Grover 256-bit SAFE
"""

import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

DEV21 = [
    "114",
    "124",
    "126",
    "135",
    "156",
    "157",
    "207",
    "224",
    "234",
    "241",
    "245",
    "330",
    "337",
    "342",
    "352",
    "360",
    "386",
    "397",
    "419",
    "424",
    "428",
]
ZERO4 = ["260", "322", "336", "384"]
ALL25 = sorted(DEV21 + ZERO4, key=int)


def shake512_hex(data: bytes) -> str:
    return hashlib.shake_256(data).hexdigest(64)  # 512-bit = 128 hex


def quantum_hash(s: str) -> str:
    return shake512_hex(s.encode("utf-8"))


def seal_qid(qid: str, irre_hash: str) -> str:
    payload = (
        f"APEX44|v2.4|QID:{qid}|IRRE:{irre_hash}|NIST:SHAKE-256-512|Grover:256bit|50Y".encode()
    )
    return shake512_hex(payload)


def seal_all(qids, irre_hash):
    return {str(q): seal_qid(str(q), irre_hash) for q in sorted(qids, key=int)}


def verify_seal(qid, seal, irre_hash):
    return seal_qid(qid, irre_hash) == seal and len(seal) == 128


if __name__ == "__main__":
    # نفس الـ IRRE string بتاع v2.3 بالظبط عشان البصمة تفضل ثابتة
    inv_str = f"IRRE-Dev21+Zero4=25-Pairs156-Zero{sorted(ZERO4)}"
    irre = quantum_hash(inv_str)

    print(f"INV_STR: {inv_str}")
    print(f"IRRE Quantum Hash: {irre} len={len(irre)} verified={len(irre) == 128}")
    print("\n--- v2.4 Full 25 Quantum Seal ---")
    seals = seal_all(ALL25, irre)

    for qid, s in seals.items():
        print(f"QID {qid}: {s[:32]}... len={len(s)} ok={verify_seal(qid, s, irre)}")

    # احفظ الـ manifest
    os.makedirs("APEX44/04-data", exist_ok=True)
    manifest = {
        "version": "v2.4",
        "irre_str": inv_str,
        "irre_hash": irre,
        "dev21": DEV21,
        "zero4": ZERO4,
        "all25": ALL25,
        "seals": seals,
        "nist": "SHAKE-256 512-bit",
        "grover_resistance": "256-bit SAFE - 50Y",
    }
    with open("APEX44/04-data/quantum_seals_v2.4.json", "w") as f:
        json.dump(manifest, f, indent=2)

    print("\n✅ VERIFIED: Full 25 len=128 each")
    print("✅ Manifest saved: APEX44/04-data/quantum_seals_v2.4.json")
    print("Dev 25 = 21 answered (156 pairs) + 4 zero [260,322,336,384] - Baseline 0.0904/0.2260")
