import hashlib
import time


def sense_hash(data: str) -> str:
    return hashlib.sha3_256(data.encode()).hexdigest()


class QuantumSensingEvidence:
    """
    مستشعر كمي بيقيس جاذبية أو مجال مغناطيسي بدقة ذرية
    لو حد لعب في المستشعر = يزور قراءات زلازل أو غواصات نووية
    """

    def __init__(self, sensor_id: str, location: str) -> None:
        self.sensor_id = sensor_id
        self.location = location
        self.base_hash = sense_hash(f"{sensor_id}{location}{time.time()}")
        self.readings = []

    def add_reading(self, value: float, sensitivity: float):
        # المستشعر الكمي حساسيته لا تقل أبدا
        # لو الحساسية قلت فجأة = حد خرب المستشعر
        is_tampered = sensitivity < 0.9  # أقل من 90% = تلاعب

        entry = {
            "value": value,
            "sensitivity": sensitivity,
            "hash": sense_hash(f"{self.sensor_id}{value}{sensitivity}{time.time()}"),
            "is_tampered": is_tampered,
        }
        self.readings.append(entry)
        return entry

    def is_sensor_intact(self) -> bool:
        return not any(r["is_tampered"] for r in self.readings)
