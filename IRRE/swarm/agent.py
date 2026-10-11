"""Small, inspectable ant-colony primitives for evidence-path exploration.

Pheromones here are in-memory heuristic suggestions. They are not evidence that a claim is
true and do not provide independent corroboration.
"""
from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass
class AuditRecord:
    ant_id: str
    source: str
    target: str
    action: str


@dataclass
class Pheromone:
    source: str
    target: str
    strength: float
    audit_record: AuditRecord


class BaseAnt:
    """Select a path using observed pheromones or an explicit random-exploration fallback."""

    def __init__(self, ant_id: str, role: str, location: str) -> None:
        if not ant_id or not role or not location:
            raise ValueError("ant_id, role, and location must be non-empty")
        self.ant_id = ant_id
        self.role = role
        self.location = location

    def act(self, pheromones: list[Pheromone], locations: list[str]) -> Pheromone | None:
        candidates = [location for location in locations if location != self.location]
        if not candidates:
            return None

        relevant = [
            pheromone
            for pheromone in pheromones
            if pheromone.target in candidates and pheromone.strength > 0.05
        ]
        if relevant:
            selected = max(relevant, key=lambda item: item.strength)
            target = selected.target
            action = "follow-pheromone"
            strength = min(1.0, max(0.1, selected.strength * 0.9))
        else:
            target = random.choice(candidates)
            action = "random-exploration"
            strength = 0.5

        source = self.location
        self.location = target
        audit = AuditRecord(self.ant_id, source, target, action)
        return Pheromone(source, target, strength, audit)
