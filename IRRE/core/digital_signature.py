import hashlib
import time
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

class DigitalSigner:
    """
    توقيع رقمي: كل دليل لازم يتوقع بمفتاح خاص
    زي ختم النسر بتاعك، مستحيل حد يزوره
    """
    def __init__(self, owner_id: str):
        self.owner_id = owner_id
        # توليد مفتاح خاص (زي كلمة سر مستحيل تتوقع)
        self.private_key = ed25519.Ed25519PrivateKey.generate()
        self.public_key = self.private_key.public_key()

    def sign_evidence(self, evidence_hash: str) -> dict:
        # بنوقع على الهاش نفسه
        signature = self.private_key.sign(evidence_hash.encode())
        return {
            "owner": self.owner_id,
            "evidence_hash": evidence_hash,
            "signature": signature.hex(),
            "public_key": self.public_key.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw
            ).hex(),
            "timestamp": time.time()
        }

    def verify_signature(self, evidence_hash: str, signature_hex: str, public_key_hex: str) -> bool:
        try:
            pub_key = ed25519.Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key_hex))
            pub_key.verify(bytes.fromhex(signature_hex), evidence_hash.encode())
            return True
        except:
            return False

# مثال سريع
if __name__ == "__main__":
    signer = DigitalSigner("Amr-Gad-Cairo-Police")
    h = hashlib.sha3_256(b"car hacked").hexdigest()
    signed = signer.sign_evidence(h)
    print(f"توقيع: {signed['signature'][:20]}...")
    print(f"تحقق: {signer.verify_signature(h, signed['signature'], signed['public_key'])}")
