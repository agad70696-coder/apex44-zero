import hashlib
import time


def soft_hash(data: str) -> str:
    return hashlib.sha3_256(data.encode()).hexdigest()

class SoftRobotEvidence:
    """
    روبوت لين من سيليكون - بيمسك قلب مريض أثناء العملية
    لازم نثبت انه ما ضغطش زيادة وموت المريض
    """
    def __init__(self, robot_id: str, material: str):
        self.robot_id = robot_id
        self.material = material  # silicone, hydrogel
        self.base_hash = soft_hash(f"{robot_id}{material}{time.time()}")
        self.grips = []

    def add_grip(self, pressure_kpa: float, target: str):
        # الضغط الآمن للأنسجة البشرية < 15 kPa
        # لو روبوت لين ضغط 50 kPa على قلب = ثقب القلب
        is_crushing = pressure_kpa > 15.0 and target in ["heart", "brain", "liver"]

        entry = {
            "pressure": pressure_kpa,
            "target": target,
            "hash": soft_hash(f"{self.robot_id}{pressure_kpa}{target}{time.time()}"),
            "is_crushing": is_crushing
        }
        self.grips.append(entry)
        return entry

    def is_grip_safe(self) -> bool:
        return not any(g["is_crushing"] for g in self.grips)
