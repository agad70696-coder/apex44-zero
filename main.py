import hashlib, time
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes

class ForensicSigner:
    def __init__(self, owner):
        self.owner = owner
        self.key = ec.generate_private_key(ec.SECP256K1())
        self.pub = self.key.public_key()
    def sign(self, data):
        sig = self.key.sign(data.encode(), ec.ECDSA(hashes.SHA256()))
        return sig.hex()
    def verify(self, data, sig_hex):
        try:
            self.pub.verify(bytes.fromhex(sig_hex), data.encode(), ec.ECDSA(hashes.SHA256()))
            return True
        except:
            return False

def merkle_root(h_list):
    curr = h_list[:]
    while len(curr) > 1:
        if len(curr) % 2 == 1:
            curr.append(curr[-1])
        nxt = []
        for i in range(0, len(curr), 2):
            nxt.append(hashlib.sha256((curr[i]+curr[i+1]).encode()).hexdigest())
        curr = nxt
    return curr[0]

# تجربة
h1 = hashlib.sha256(b"CAR-LOG-1").hexdigest()
h2 = hashlib.sha256(b"3D-PRINT-2").hexdigest()
h3 = hashlib.sha256(b"CAR-LOG-3").hexdigest()
root = merkle_root([h1,h2,h3])
signer = ForensicSigner("Amr Gad")
sig = signer.sign(root)
print("Merkle Root:", root[:20])
print("ECDSA Signature Valid:", signer.verify(root, sig))
