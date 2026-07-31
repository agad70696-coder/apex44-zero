from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend

class ForensicSigner:
    def load_from_atecc608a(self, slot=0):
        try:
            import board, busio
            from adafruit_atecc.adafruit_atecc import ATECC608A
            i2c = busio.I2C(board.SCL, board.SDA)
            atecc = ATECC608A(i2c, address=0x60)
            return atecc
        except:
            try:
                with open("secure_element.key", "rb") as f:
                    private_key = serialization.load_pem_private_key(f.read(), password=None, backend=default_backend())
                    return private_key
            except FileNotFoundError:
                private_key = ec.generate_private_key(ec.SECP256K1(), default_backend())
                pem = private_key.private_bytes(encoding=serialization.Encoding.PEM, format=serialization.PrivateFormat.PKCS8, encryption_algorithm=serialization.NoEncryption())
                with open("secure_element.key", "wb") as f:
                    f.write(pem)
                return private_key

    def __init__(self):
        self.secure_element = self.load_from_atecc608a(slot=0)

    def sign(self, data: bytes) -> bytes:
        if hasattr(self.secure_element, 'sign'):
            return self.secure_element.sign(data)
        else:
            return self.secure_element.sign(data, ec.ECDSA(hashes.SHA256()))
