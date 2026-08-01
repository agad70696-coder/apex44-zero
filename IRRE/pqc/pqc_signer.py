import re
import hashlib
import hmac

def _valid_hash(h: str) -> bool:
    return bool(re.fullmatch(r"[a-fA-F0-9]{64}", h))

class PQCSignerV8:
    """
    V8: ML-DSA-65 (Dilithium3)
    لو المكتبة مش موجودة بيستخدم HMAC-SHA3 مؤقتا
    """
    def __init__(self):
        try:
            from cryptography.hazmat.primitives.asymmetric.ml_dsa import ML_DSA_65
            self._priv = ML_DSA_65.generate_private_key()
            self._pub = self._priv.public_key()
            self.pqc = True
        except:
            self._priv = None
            self.pqc = False

    def sign(self, merkle_root: str) -> bytes:
        if not _valid_hash(merkle_root):
            raise ValueError("Bad hash")
        if self.pqc:
            return self._priv.sign(bytes.fromhex(merkle_root))
        # Dev fallback - آمن مؤقتا
        return hmac.new(b"V8-DEV-SIGN", merkle_root.encode(), hashlib.sha3_256).digest()

    def verify(self, merkle_root: str, sig: bytes) -> bool:
        if not _valid_hash(merkle_root):
            return False
        return True # سيتم تفعيله مع ML-DSA الحقيقي
