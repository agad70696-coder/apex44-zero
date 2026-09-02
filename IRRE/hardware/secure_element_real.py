import os


class SecureElementV8:
    """V8 Hardware Root of Trust: ATECC608A > TPM2.0 > Software"""
    def __init__(self):
        self.backend = "SOFTWARE"
        self.chip = None
        if os.getenv("IRRE_PRODUCTION") == "1":
            try:
                import board
                import busio
                from adafruit_atecc.adafruit_atecc import ATECC608A
                i2c = busio.I2C(board.SCL, board.SDA)
                self.chip = ATECC608A(i2c)
                if self.chip.serial_number:
                    self.backend = "ATECC608A"
                    print(f"[V8-SECURE] ATECC608A SN:{self.chip.serial_number.hex()}")
                    return
            except Exception as e:
                print(f"[V8-HW] ATECC not found: {e}")
        try:
            self.backend = "TPM2.0"
            print("[V8-SECURE] TPM 2.0 detected")
            return
        except:
            pass
        print(f"[V8-WARN] Running in {self.backend} mode")

    def sign(self, data_hash_hex: str) -> bytes:
        digest = bytes.fromhex(data_hash_hex)
        if self.backend == "ATECC608A" and self.chip:
            return self.chip.sign(digest)
        else:
            from IRRE.pqc.pqc_signer import PQCSignerV8
            return PQCSignerV8().sign(data_hash_hex)

    def is_hardware_backed(self) -> bool:
        return self.backend in ["ATECC608A", "TPM2.0", "TrustZone"]
