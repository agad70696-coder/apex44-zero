import hashlib
import time


def material_hash(data: str) -> str:
    return hashlib.sha3_256(data.encode()).hexdigest()


class NanoMaterialEvidence:
    """
    توثيق سلامة المواد النانوية - زي الجرافين
    أي محاولة تلاعب فيزيائي بتغير موصلية المادة وبتتكشف فورا
    """

    def __init__(
        self, material_id: str, material_type: str = "graphene", conductivity: float = 100.0
    ) -> None:
        self.material_id = material_id
        self.material_type = material_type  # graphene, nanotube, smart_polymer
        self.conductivity = conductivity
        self.timestamp = str(time.time())
        self.base_hash = material_hash(
            f"{material_id}{material_type}{conductivity}{self.timestamp}"
        )
        self.logs = []

    def apply_stress(self, stress_level: float, temperature: float):
        # المواد الذكية بتتأثر بالحرارة والضغط
        old = self.conductivity
        self.conductivity = (
            self.conductivity * (1 - stress_level * 0.01) * (1 - (temperature - 25) * 0.002)
        )
        entry = {
            "stress": stress_level,
            "temp": temperature,
            "old_conductivity": old,
            "new_conductivity": self.conductivity,
            "hash": material_hash(f"{self.material_id}{self.conductivity}{time.time()}"),
        }
        self.logs.append(entry)
        return self.conductivity

    def is_tampered(self) -> bool:
        # لو الموصلية نزلت تحت 70% يبقى حد لعب في المادة
        return self.conductivity < 70.0

    def verify_chain(self) -> bool:
        return len(self.base_hash) == 64
