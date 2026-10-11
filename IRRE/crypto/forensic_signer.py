"""Development fallback signer for forensic package integrity.

Ed25519 is a classical signature scheme, not a post-quantum signature. The private key
is generated in memory and is lost when this process exits. Production deployments must
use the configured hardware secure element and an independently managed key lifecycle.
"""
from __future__ import annotations

import base64
import re

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

_VALID_DIGEST = re.compile(r"^(?:[a-fA-F0-9]{64}|[a-fA-F0-9]{128})$")


class ForensicSigner:
    """Ephemeral Ed25519 signer used only as a development fallback."""

    def __init__(self) -> None:
        self._private_key = Ed25519PrivateKey.generate()

    @staticmethod
    def _message(digest: str) -> bytes:
        if not isinstance(digest, str) or not _VALID_DIGEST.fullmatch(digest):
            raise ValueError("Expected a 64- or 128-character hexadecimal digest")
        return digest.lower().encode("ascii")

    def sign(self, digest: str) -> str:
        """Sign a hex digest and return a Base64-encoded signature."""
        signature = self._private_key.sign(self._message(digest))
        return base64.b64encode(signature).decode("ascii")

    def get_public_pem(self) -> str:
        """Export the public key in SubjectPublicKeyInfo PEM format."""
        public_key = self._private_key.public_key()
        return public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("ascii")

    def verify(self, digest: str, signature_b64: str, public_pem: str) -> bool:
        """Verify using only the supplied public key; malformed data returns False."""
        try:
            message = self._message(digest)
            signature = base64.b64decode(signature_b64, validate=True)
            public_key = serialization.load_pem_public_key(public_pem.encode("ascii"))
            if not isinstance(public_key, Ed25519PublicKey):
                return False
            public_key.verify(signature, message)
            return True
        except (ValueError, TypeError, UnicodeError, InvalidSignature):
            return False
