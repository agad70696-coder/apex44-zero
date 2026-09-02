import hashlib
import time


def auto_hash(data: str) -> str:
    return hashlib.sha3_256(data.encode()).hexdigest()

class AutonomousRobotEvidence:
    """
    روبوت مستقل بذكاء اصطناعي بياخد قرار لوحده
    لازم نوثق كل قرار عشان لو قتل حد نعرف ليه
    """
    def __init__(self, robot_id: str, mission: str):
        self.robot_id = robot_id
        self.mission = mission
        self.base_hash = auto_hash(f"{robot_id}{mission}{time.time()}")
        self.decisions = []

    def add_decision(self, decision: str, confidence: float, human_override: bool):
        # لو ثقة الروبوت < 60% ومفيش تدخل بشري = قرار خطير
        is_risky = confidence < 0.6 and not human_override

        entry = {
            "decision": decision,
            "confidence": confidence,
            "human_override": human_override,
            "hash": auto_hash(f"{self.robot_id}{decision}{confidence}{time.time()}"),
            "is_risky": is_risky
        }
        self.decisions.append(entry)
        return entry

    def is_mission_compliant(self) -> bool:
        return not any(d["is_risky"] for d in self.decisions)
