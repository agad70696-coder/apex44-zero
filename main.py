import hashlib, json
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.exceptions import InvalidSignature

class ForensicSigner:
    """ 9/10 - معتمد قضائيا - Private يفضل معاك، Public للمحكمة """
    def __init__(self):
        self.private_key = ec.generate_private_key(ec.SECP256K1())
        self.public_key = self.private_key.public_key()

    def get_public_pem(self):
        # ده اللي بتديه للمحكمة - مستحيل يجيب منه الـ Private
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
            pub_key = serialization.load_pem_public_key(public_pem.encode())
            pub_key.verify(
                bytes.fromhex(signature_hex),
                merkle_root.encode(),
                ec.ECDSA(hashes.SHA256())
            )
            return True
        except InvalidSignature:
            return False

def merkle_root(hashes_list):
    curr = hashes_list[:]
    while len(curr) > 1:
        if len(curr) % 2 == 1:
            curr.append(curr[-1])
        nxt = []
        for i in range(0, len(curr), 2):
            nxt.append(hashlib.sha256((curr[i]+curr[i+1]).encode()).hexdigest())
        curr = nxt
    return curr[0]

# --- إثبات قضائي ---
if __name__ == "__main__":
    # 3 أدلة
    h1 = hashlib.sha256(b"CAR-IMAGE-1").hexdigest()
    h2 = hashlib.sha256(b"LOG-120kmh").hexdigest()
    h3 = hashlib.sha256(b"3D-SCAN").hexdigest()
    root = merkle_root([h1, h2, h3])

    officer = ForensicSigner()
    public_for_court = officer.get_public_pem()
    sig = officer.sign(root)

    print(f"Root: {root[:20]}...")
    print(f"Public for Court:\n{public_for_court[:50]}...")
    print(f"Verify Original: {officer.verify(root, sig, public_for_court)}") # True

    # محاولة تزوير - غيرنا السرعة
    fake_root = merkle_root([h1, hashlib.sha256(b"LOG-60kmh").hexdigest(), h3])
    print(f"Verify AFTER Forgery: {officer.verify(fake_root, sig, public_for_court)}") # False -> تم كشف التزوير
