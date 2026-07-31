import hashlib
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.exceptions import InvalidSignature

class ForensicSigner:
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
        sig = self.private_key.sign(
            merkle_root.encode(),
            ec.ECDSA(hashes.SHA256())
        )
        return sig.hex()

    def verify(self, merkle_root: str, sig_hex: str, public_pem: str) -> bool:
        try:
            pub = serialization.load_pem_public_key(public_pem.encode())
            pub.verify(bytes.fromhex(sig_hex), merkle_root.encode(), ec.ECDSA(hashes.SHA256()))
            return True
        except InvalidSignature:
            return False

def merkle_root(h_list):
    cur = h_list[:]
    while len(cur) > 1:
        if len(cur) % 2 == 1:
            cur.append(cur[-1])
        nxt = []
        for i in range(0, len(cur), 2):
            nxt.append(hashlib.sha256((cur[i]+cur[i+1]).encode()).hexdigest())
        cur = nxt
    return cur[0]
