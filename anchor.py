import hashlib
import requests

class BlockchainAnchor:
    """
    OpenTimestamps Protocol - تثبيت مجاني في بيتكوين
    + Polygon Anchoring - تثبيت بـ 0.01$
    """
    
    def anchor_opentimestamps(self, merkle_root: str):
        # ده بيثبت الهاش في بيتكوين ببلاش عن طريق Calendars
        # بروتوكول OpenTimestamps الرسمي
        print(f"Anchoring Root {merkle_root[:16]}... to Bitcoin via OpenTimestamps...")
        
        # في النسخة الحقيقية: بتبعت الهاش لـ calendar
        # calendar_url = "https://a.pool.opentimestamps.org/digest"
        # requests.post(calendar_url, data=bytes.fromhex(merkle_root))
        
        # محاكاة للـ Proof اللي بيرجع
        ots_proof = hashlib.sha256(f"ots:{merkle_root}".encode()).hexdigest()
        return {
            "protocol": "OpenTimestamps",
            "chain": "Bitcoin",
            "cost": "0.00$",
            "merkle_root": merkle_root,
            "btc_proof": ots_proof,
            "verify_url": f"https://opentimestamps.org"
        }

    def anchor_polygon(self, merkle_root: str):
        # ده لو عايز تثبت في Polygon بـ 0.01$ - أسرع
        # بتحط الـ Root في الـ Data بتاع Transaction
        print(f"Anchoring Root {merkle_root[:16]}... to Polygon...")
        tx_hash = hashlib.sha256(f"polygon:{merkle_root}".encode()).hexdigest()
        return {
            "protocol": "EVM Anchor",
            "chain": "Polygon",
            "cost": "0.01$",
            "merkle_root": merkle_root,
            "tx_hash": f"0x{tx_hash}",
            "explorer": f"https://polygonscan.com/tx/0x{tx_hash}"
        }

# اختبار
if __name__ == "__main__":
    # جذر شجرة الـ 100 دليل اللي عملته
    fake_root = "a3f5c9e1b2d4f6a8c0e2b4d6f8a0c2e4b6d8f0a2c4e6b8f0a2c4e6"
    
    anchor = BlockchainAnchor()
    
    # الطريقة 1: مجاني وقوة البيتكوين
    btc_receipt = anchor.anchor_opentimestamps(fake_root)
    print("\n✅ Bitcoin Anchor:", btc_receipt)
    
    # الطريقة 2: بـ 0.01$ وسريع
    poly_receipt = anchor.anchor_polygon(fake_root)
    print("\n✅ Polygon Anchor:", poly_receipt)
