from typing import Dict, Any, List
from.complex_system import ComplexSystem

class EmergenceDetector:
    def __init__(self, system: ComplexSystem):
        self.system = system

    def detect_trustworthiness(self) -> Dict[str, Any]:
        h = self.system.system_health()
        if h > 0.9:
            level = "HIGHLY_TRUSTWORTHY"
        elif h > 0.7:
            level = "TRUSTWORTHY"
        else:
            level = "UNTRUSTWORTHY"
        return {"emergent_property": "Trustworthiness", "level": level, "system_health": h, "formula": "Trust = Emergence(5 Layers)"}

    def detect_cascade_risk(self) -> Dict[str, Any]:
        min_h = min(c.health for c in self.system.components.values())
        avg_str = sum(i.strength for i in self.system.interactions) / len(self.system.interactions) if self.system.interactions else 0
        risk = (1 - min_h) * avg_str
        weakest = min(self.system.components.values(), key=lambda c: c.health).id
        return {"risk_score": risk, "weakest_link": weakest, "risk_level": "CRITICAL" if risk>0.7 else "LOW"}
