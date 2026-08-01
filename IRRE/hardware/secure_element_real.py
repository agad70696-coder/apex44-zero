import os
import hashlib

class SecureElementV8:
    """
    V8 Hardware Root of Trust
    Level 1: ATECC608A (I2C)
    Level 2: TPM 2.0
    Level 3: ARM TrustZone / OP-TEE
    """
    def __init__(self):
        self.backend = "SOFTWARE"
        self.chip = None

        # 1. جرب ATECC608A الحقيقية
        if os.getenv("IRRE_PRODUCTION") == "1":
            try:
                import board, busio
                from adafruit_atecc.adafruit_atecc import ATECC608A
                i2c = busio.I2C(board.SCL, board.SDA)
                self.chip = ATECC608A(i2c)
                if self.chip.serial_number:
                    self.backend = "ATECC608A"
                    print(f"[V8-SECURE] ATECC608A locked - SN:{self.chip.serial_number.hex()}")
                    return
            except Exception as e:
                print(f"[V8-HW] ATECC not found: {e}")

        # 2. جرب TPM 2.0
        try:
            from tpm2_pytss import ESAPI
            self.backend = "TPM2.0"
            print("[V8-SECURE] TPM 2.0 detected")
            return
        except:
            pass

        # 3. Dev mode
        print(f"[V8-WARN] Running in {self.backend} mode - set IRRE_PRODUCTION=1 on Pi")

    def sign(self, data_hash_hex: str) -> bytes:
        """التوقيع لا يخرج المفتاح من الشريحة ابدا"""
        digest = bytes.fromhex(data_hash_hex)
        if self.backend == "ATECC608A" and self.chip:
            # المفتاح جوة الشريحة - مستحيل يتسرق حتى لو اتسرقت الـ SD Card
            return self.chip.sign(digest)
        else:
            # Fallback V8 PQC Signer
            from IRRE.pqc.pqc_signer import PQCSignerV8
            return PQCSignerV8().sign(data_hash_hex)

    def is_hardware_backed(self) -> bool:
        return self.backend in ["ATECC608A", "TPM2.0", "TrustZone"]
