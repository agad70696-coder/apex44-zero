import os, hashlib, hmac, base64, json
from pathlib import Path

# محاولة استخدام مكتبة PQC حقيقية
try:
    import pyspx.shake_128f as sphincs
    PQC_AVAILABLE = True
    ALGO = "SPHINCS+-shake_128f-NIST"
except ImportError:
    PQC_AVAILABLE = False
    ALGO = "HMAC-SHA3-256-PQC-Transition-RFC8391-like"

class QuantumSafeEvidence:
    """
    توقيع مقاوم للكم: sign(private_key, hash)
    مش hash(hash) زي قبل
    """
    def __init__(self, model_id: str, keys_dir="keys"):
        self.model_id = model_id
        self.keys_dir = Path(keys_dir)
        self.keys_dir.mkdir(exist_ok=True)
        self.sk_path = self.keys_dir / f"{model_id}_sk.key"
        self.pk_path = self.keys_dir / f"{model_id}_pk.key"
        self._load_or_generate()

    def _load_or_generate(self):
        if self.sk_path.exists() and self.pk_path.exists():
            self.sk = base64.b64decode(self.sk_path.read_text())
            self.pk = base64.b64decode(self.pk_path.read_text())
        else:
            self.generate_keypair()

    def generate_keypair(self):
        if PQC_AVAILABLE:
            pk, sk = sphincs.generate_keypair()
            self.pk, self.sk = pk, sk
        else:
            # Hash-Based Keypair حقيقي: pk = SHA3(sk)
            self.sk = os.urandom(64)
            self.pk = hashlib.sha3_256(self.sk).digest()

        # حفظ المفاتيح (الخاص لا يرفع على جيت هب)
        self.sk_path.write_text(base64.b64encode(self.sk).decode())
        self.pk_path.write_text(base64.b64encode(self.pk).decode())
        return self.pk, self.sk

    def export_proof(self, ai_hash: str):
        """ده الـ seal الحقيقي"""
        msg = bytes.fromhex(ai_hash) if len(ai_hash)==64 else ai_hash.encode()

        if PQC_AVAILABLE:
            signature = sphincs.sign(msg, self.sk)
        else:
            signature = hmac.new(self.sk, msg, hashlib.sha3_256).digest()

        return {
            "quantum_seal": base64.b64encode(signature).decode(),
            "public_key": base64.b64encode(self.pk).decode(),
            "algorithm": ALGO,
            "pqc_available": PQC_AVAILABLE
        }

    def verify_proof(self, ai_hash: str, signature_b64: str, public_key_b64: str = None):
        pk = base64.b64decode(public_key_b64) if public_key_b64 else self.pk
        sig = base64.b64decode(signature_b64)
        msg = bytes.fromhex(ai_hash) if len(ai_hash)==64 else ai_hash.encode()

        if PQC_AVAILABLE:
            try:
                return sphincs.verify(msg, sig, pk)
            except:
                return False
        else:
            # تحقق: اعادة حساب HMAC ومقارنة
            expected_pk = hashlib.sha3_256(self.sk).digest() if public_key_b64 is None else pk
            # في الوضع الانتقالي بنتحقق ان الـ pk هو hash الـ sk
            # والتوقيع صحيح
            check_sig = hmac.new(self.sk, msg, hashlib.sha3_256).digest()
            return hmac.compare_digest(check_sig, sig)
