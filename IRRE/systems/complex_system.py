from dataclasses import dataclass, field
from typing import Any


@dataclass
class SystemComponent:
    id: str
    type: str
    health: float = 1.0
    dependencies: list[str] = field(default_factory=list)
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class Interaction:
    source: str
    target: str
    interaction_type: str
    strength: float = 1.0
    description: str = ""


class ComplexSystem:
    def __init__(self, name: str = "apex44-zero") -> None:
        self.name = name
        self.components: dict[str, SystemComponent] = {}
        self.interactions: list[Interaction] = []
        self._build_apex_system()

    def _build_apex_system(self) -> None:
        self.add_component(
            "Evidence_Layer", "Evidence", 1.0, properties={"law": "No Evidence = No Claim"}
        )
        self.add_component("Behavioral_Layer", "Agent", 1.0, properties={"detects": "Bias+Motive"})
        self.add_component("Mathematical_Layer", "Theorem", 1.0, properties={"proves": "Theorems"})
        self.add_component(
            "Knowledge_Layer", "Knowledge", 1.0, properties={"understands": "Cairo=Entity"}
        )
        self.add_component("Gate_Layer", "Agent", 1.0, properties={"qac": "44/44"})
        self.add_interaction(
            "Evidence_Layer", "Behavioral_Layer", "feeds", 0.9, "الدليل يغذي النفسي"
        )
        self.add_interaction("Behavioral_Layer", "Mathematical_Layer", "triggers", 0.8)
        self.add_interaction("Mathematical_Layer", "Knowledge_Layer", "updates", 0.9)
        self.add_interaction("Knowledge_Layer", "Evidence_Layer", "reinterprets", 0.7)
        self.add_interaction("Gate_Layer", "Evidence_Layer", "protects", 1.0)

    def add_component(self, cid, ctype, health=1.0, dependencies=None, properties=None) -> None:
        self.components[cid] = SystemComponent(
            cid, ctype, health, dependencies or [], properties or {}
        )

    def add_interaction(self, src, tgt, itype, strength=1.0, desc="") -> None:
        self.interactions.append(Interaction(src, tgt, itype, strength, desc))

    def get_component_health(self, cid):
        return self.components.get(cid, SystemComponent(cid, "Unknown", 0)).health

    def system_health(self):
        if not self.components:
            return 0
        min_h = min(c.health for c in self.components.values())
        avg_h = sum(c.health for c in self.components.values()) / len(self.components)
        return min_h * 0.6 + avg_h * 0.4
