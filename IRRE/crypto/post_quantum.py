"""SPHINCS+ evidence signing adapter.

PySPX 0.5.0 is an older binding used here for reproducible CI coverage. Its successful
execution is not, by itself, a production security certification. Keep this adapter
fail-closed: do not substitute a classical or HMAC signature when the PQ library is absent.
"""
from __future__ import annotations

import base64
import importlib
import os
import re
from pathlib import Path

SPHINCS_MODULE = None
SPHINCS_IMPORT_ERRORS: list[str] = []
for module_name in ("pyspx.shake_128f", "pyspx.shake256_128f"):
    try:
        SPHINCS_MODULE = importlib.import_module(module_name)
        break
    except ImportError as exc:
        SPHINCS_IMPORT_ERRORS.append(f"{module_name}: {exc}")

PQC_AVAILABLE = SPHINCS_MODULE is not None
sphincs = SPHINCS_MODULE
ALGO = "SPHINCS+-SHAKE-128f (PySPX binding)" if PQC_AVAILABLE else "UNAVAILABLE"


def _sanitize_model_id(model_id: str) -> str:
    if not isinstance(model_id, str) or not re.fullmatch(r"[a-zA-Z0-9_-]{1,100}", model_id):
        raise ValueError("Invalid model_id: allowed a-zA-Z0-9_- length 1-100")
    return model_id


def _message(ai_hash: str) -> bytes:
    if not isinstance(ai_hash, str) or not ai_hash:
        raise ValueError("ai_hash must be a non-empty string")
    if len(ai_hash) == 64 and re.fullmatch(r"[a-fA-F0-9]{64}", ai_hash):
        return bytes.fromhex(ai_hash)
    return ai_hash.encode("utf-8")


class QuantumSafeEvidence:
    """Store a local SPHINCS+ key pair and export/verify signatures."""

    def __init__(self, model_id: str, keys_dir: str | Path = "keys") -> None:
        self.model_id = _sanitize_model_id(model_id)
        self.keys_dir = Path(keys_dir).resolve()
        self.keys_dir.mkdir(parents=True, exist_ok=True)
        self.sk_path = (self.keys_dir / f"{self.model_id}_sk.key").resolve()
        self.pk_path = (self.keys_dir / f"{self.model_id}_pk.key").resolve()
        if self.keys_dir not in self.sk_path.parents or self.keys_dir not in self.pk_path.parents:
            raise ValueError("Path traversal blocked")
        if not PQC_AVAILABLE:
            raise RuntimeError(
                "PQC library missing - install the pinned PySPX binding; no fallback signer is used"
            )
        self._load_or_generate()

    def _load_or_generate(self) -> None:
        if self.sk_path.exists() and self.pk_path.exists():
            self.sk = base64.b64decode(self.sk_path.read_text(encoding="ascii"), validate=True)
            self.pk = base64.b64decode(self.pk_path.read_text(encoding="ascii"), validate=True)
            return
        self.generate_keypair()

    def generate_keypair(self) -> tuple[bytes, bytes]:
        """Generate keys using the binding-provided seed size and store them locally."""
        if not PQC_AVAILABLE or sphincs is None:
            raise RuntimeError("PQC library unavailable")
        seed_size = int(getattr(sphincs, "crypto_sign_SEEDBYTES", 96))
        pk, sk = sphincs.generate_keypair(os.urandom(seed_size))
        self.pk, self.sk = pk, sk
        # Best-effort restrictive file permissions on Unix-like platforms.
        self.sk_path.write_text(base64.b64encode(sk).decode("ascii"), encoding="ascii")
        try:
            self.sk_path.chmod(0o600)
        except OSError:
            pass
        self.pk_path.write_text(base64.b64encode(pk).decode("ascii"), encoding="ascii")
        try:
            self.pk_path.chmod(0o644)
        except OSError:
            pass
        return pk, sk

    def export_proof(self, ai_hash: str) -> dict[str, object]:
        message = _message(ai_hash)
        signature = sphincs.sign(message, self.sk)
        return {
            "quantum_seal": base64.b64encode(signature).decode("ascii"),
            "public_key": base64.b64encode(self.pk).decode("ascii"),
            "algorithm": ALGO,
            "pqc_available": True,
        }

    def verify_proof(
        self, ai_hash: str, signature_b64: str, public_key_b64: str | None = None
    ) -> bool:
        if not PQC_AVAILABLE or sphincs is None:
            return False
        try:
            public_key = (
                base64.b64decode(public_key_b64, validate=True)
                if public_key_b64
                else self.pk
            )
            signature = base64.b64decode(signature_b64, validate=True)
            return bool(sphincs.verify(_message(ai_hash), signature, public_key))
        except (ValueError, TypeError, UnicodeError):
            return False

    def verify_seal(self, ai_hash: str, signature_b64: str, public_key_b64: str | None = None) -> bool:
        """Compatibility alias for older callers."""
        return self.verify_proof(ai_hash, signature_b64, public_key_b64)
