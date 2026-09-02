from typing import Any

from .complex_system import ComplexSystem
from .emergence import EmergenceDetector


class SystemPredictor:
    def __init__(self, system: ComplexSystem = None):
        self.system = system or ComplexSystem()
        self.detector = EmergenceDetector(self.system)

    def what_if_remove_component(self, cid: str) -> dict[str, Any]:
        if cid not in self.system.components:
            return {"error": "not found"}
        orig_h = self.system.system_health()
        removed = self.system.components[cid]
        orig_comp_h = removed.health
        removed.health = 0
        affected = []
        for comp_id, comp in self.system.components.items():
            if comp_id == cid:
                continue
            for inter in self.system.interactions:
                if inter.source == cid and inter.target == comp_id:
                    old = comp.health
                    comp.health = max(0, comp.health - inter.strength * 0.5)
                    if comp.health < old:
                        affected.append({"component": comp_id, "old": old, "new": comp.health, "via": inter.interaction_type})
        new_h = self.system.system_health()
        removed.health = orig_comp_h
        for aff in affected:
            self.system.components[aff["component"]].health = aff["old"]
        return {"scenario": f"Remove {cid}", "original_health": orig_h, "predicted_health": new_h, "drop": orig_h-new_h, "cascade_size": len(affected), "affected": affected, "prediction": f"Removing {cid} drops health by {orig_h-new_h:.2f} and affects {len(affected)} - Butterfly Effect!"}

    def what_if_add_bias(self, rate: float = 0.8):
        orig = self.system.get_component_health("Behavioral_Layer")
        new_h = orig * (1 - rate * 0.7)
        self.system.components["Behavioral_Layer"].health = new_h
        sys_h = self.system.system_health()
        self.system.components["Behavioral_Layer"].health = orig
        return {"scenario": f"Bias {rate*100:.0f}%", "system_health_after": sys_h, "prediction": f"{rate*100:.0f}% bias → System {sys_h:.2f}"}
