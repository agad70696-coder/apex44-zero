import base64
import re
from pathlib import Path

try:
    import pyspx.shake_128f as sphincs
    PQC_AVAILABLE = True
    ALGO = "SPHINCS+-shake_128f-NIST"
except ImportError:
    PQC_AVAILABLE = False
    ALGO = "HMAC-SHA3-256-PQC-Transition"

MODEL_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,100}$")

def _sanitize_model_id(model_id: str) -> str:
    if not MODEL_ID_PATTERN.fullmatch(model_id):
        raise ValueError("Invalid model_id: allowed a-zA-Z0-9_- length 1-100")
    return model_id

class QuantumSafeEvidence:
    def __init__(self, model_id: str, keys_dir="keys"):
        self.model_id = _sanitize_model_id(model_id)
        self.keys_dir = Path(keys_dir).resolve()
        self.keys_dir.mkdir(parents=True, exist_ok=True)
        self.sk_path = (self.keys_dir / f"{self.model_id}_sk.key").resolve()
        self.pk_path = (self.keys_dir / f"{self.model_id}_pk.key").resolve()
        if self.keys_dir not in self.sk_path.parents or self.keys_dir not in self.pk_path.parents:
            raise ValueError("Path traversal blocked")
        self._load_or_generate()

    def _load_or_generate(self):
        if self.sk_path.exists() and self.pk_path.exists():
            self.sk = base64.b64decode(self.sk_path.read_text())
            self.pk = base64.b64decode(self.pk_path.read_text())
        else:
            self.generate_keypair()

    def generate_keypair(self):
        if not PQC_AVAILABLE:
            raise RuntimeError("PQC library missing - production requires pyspx SPHINCS+")
        pk, sk = sphincs.generate_keypair()
        self.pk, self.sk = pk, sk
        self.sk_path.write_text(base64.b64encode(self.sk).decode())
        self.pk_path.write_text(base64.b64encode(self.pk).decode())
        return self.pk, self.sk

    def export_proof(self, ai_hash: str):
        msg = bytes.fromhex(ai_hash) if len(ai_hash)==64 else ai_hash.encode()
        signature = sphincs.sign(msg, self.sk)
        return {
            "quantum_seal": base64.b64encode(signature).decode(),
            "public_key": base64.b64encode(self.pk).decode(),
            "algorithm": ALGO,
            "pqc_available": True
        }

    def verify_proof(self, ai_hash: str, signature_b64: str, public_key_b64: str = None):
        pk = base64.b64decode(public_key_b64) if public_key_b64 else self.pk
        sig = base64.b64decode(signature_b64)
        msg = bytes.fromhex(ai_hash) if len(ai_hash)==64 else ai_hash.encode()
        try:
            return sphincs.verify(msg, sig, pk)
        except:
            return False
