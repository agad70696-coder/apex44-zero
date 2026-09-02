import json

from anchor import BitcoinAnchor
from main import ForensicSigner


def verify_for_court() -> bool | None:
    print("=== APEX-44 ZERO - Court Verification ===")
    print("Loading court package...")

    try:
        # This file will be given to the court
        with open("court_package.json") as f:
            package = json.load(f)

        merkle_root = package["merkle_root"]
        signature = package["signature"]
        public_pem = package["public_key_pem"]
        anchor_data = package["bitcoin_anchor"]

        print(f"\n1. Merkle Root: {merkle_root[:20]}...")
        print(f"2. Signature: {signature[:20]}...")

        # Step 1: Verify ECDSA Signature
        signer = ForensicSigner()
        is_sig_valid = signer.verify(merkle_root, signature, public_pem)

        print("\n--- Signature Check ---")
        if is_sig_valid:
            print("✅ SIGNATURE VALID - Signed by officer's private key")
        else:
            print("❌ SIGNATURE INVALID - TAMPERED!")
            return False

        # Step 2: Verify Bitcoin Anchor
        anchor = BitcoinAnchor()
        is_anchor_valid = anchor.verify_anchor(merkle_root, anchor_data)

        print("\n--- Bitcoin Anchor Check ---")
        print(f"Timestamp UTC: {anchor_data['timestamp_utc']}")
        if is_anchor_valid:
            print("✅ BITCOIN ANCHOR VALID - Timestamp proven on Bitcoin")
        else:
            print("❌ ANCHOR INVALID - Timestamp tampered!")
            return False

        print("\n===============================")
        print("FINAL VERDICT: ✅ EVIDENCE IS VALID")
        print("This evidence is admissible in court.")
        print("===============================")
        return True

    except FileNotFoundError:
        print("❌ court_package.json not found!")
        print("Make sure you run main.py + anchor.py first to generate it.")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    verify_for_court()
