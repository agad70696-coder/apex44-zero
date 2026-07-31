import hashlib
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.exceptions import InvalidSignature

class ForensicSigner:
    # :التوقيع الجنائي فصل
    def __init__(self):
        # نفس منحنى البيتكوين
        self.private_key = ec.generate_private_key(ec.SECP256K1())
        self.public_key = self.private_key.public_key()

    def get_public_pem(self):
        # ده اللي بتديه للمحكمة
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()

    def sign(self, merkle_root: str) -> str:
        signature = self.private_key.sign(
            merkle_root.encode(),
            ec.ECDSA(hashes.SHA256())
        )
        return signature.hex()

    def verify(self, merkle_root: str, signature_hex: str, public_pem: str) -> bool:
        try:
            public_key = serialization.load_pem_public_key(public_pem.encode())
            public_key.verify(
                bytes.fromhex(signature_hex),
                merkle_root.encode(),
                ec.ECDSA(hashes.SHA256())
            )
            return True
        except InvalidSignature:
            return False
