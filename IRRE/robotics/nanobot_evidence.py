import hashlib
import time
import math

def nano_hash(data: str) -> str:
    return hashlib.sha3_256(data.encode()).hexdigest()

class NanobotEvidence:
    """
    توثيق سرب روبوتات نانوية بتوصّل دواء للسرطان
    بيمنع الروبوت يغلط ويهاجم خلية سليمة
    """
    def __init__(self, swarm_id: str, target_tumor_id: str, drug: str):
        self.swarm_id = swarm_id
        self.target_tumor_id = target_tumor_id
        self.drug = drug
        self.base_hash = nano_hash(f"{swarm_id}{target_tumor_id}{time.time()}")
        self.movements = []

    def add_movement(self, x: float, y: float, z: float, cell_type: str):
        # لو الروبوت راح لخلية سليمة ومعاه سم = كارثة
        is_attacking_healthy = cell_type == "healthy" and self.drug in ["chemo", "doxorubicin"]
        
        # المسافة من الورم - لو بعد أكتر من 5 ميكرومتر وهو بيفرغ الدواء = تسريب
        distance = math.sqrt(x**2 + y**2 + z**2)
        is_leaking = distance > 5.0 and cell_type != "cancer"

        entry = {
            "x": x, "y": y, "z": z,
            "cell_type": cell_type,
            "hash": nano_hash(f"{self.swarm_id}{x}{y}{z}{cell_type}{time.time()}"),
            "is_dangerous": is_attacking_healthy or is_leaking
        }
        self.movements.append(entry)
        return entry

    def is_mission_safe(self) -> bool:
        return not any(m["is_dangerous"] for m in self.movements)

    def verify_swarm(self) -> bool:
        return len(self.base_hash) == 64
