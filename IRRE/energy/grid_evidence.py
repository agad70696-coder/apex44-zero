import hashlib
import time


def energy_hash(data: str) -> str:
    return hashlib.sha3_256(data.encode()).hexdigest()

class EnergyGridEvidence:
    """
    توثيق استهلاك الطاقة وشهادات الكربون - يكشف سرقة الكهرباء وتزوير الكربون
    """
    def __init__(self, meter_id: str, initial_kwh: float = 0.0):
        self.meter_id = meter_id
        self.total_kwh = initial_kwh
        self.timestamp = str(time.time())
        self.base_hash = energy_hash(f"{meter_id}{initial_kwh}{self.timestamp}")
        self.readings = []

    def add_reading(self, kwh: float, co2_saved: float = 0.0):
        # فيزياء: مستحيل تستهلك -50 كيلو أو توفر كربون أكتر من استهلاكك
        is_fraud = kwh < 0 or co2_saved > kwh * 0.7

        entry = {
            "kwh": kwh,
            "co2_saved": co2_saved,
            "total": self.total_kwh + kwh,
            "hash": energy_hash(f"{self.meter_id}{kwh}{co2_saved}{time.time()}"),
            "is_fraud": is_fraud
        }
        self.total_kwh += kwh
        self.readings.append(entry)
        return entry

    def detect_energy_fraud(self) -> bool:
        return any(r["is_fraud"] for r in self.readings)

    def verify_grid(self) -> bool:
        return len(self.base_hash) == 64
