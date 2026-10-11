"""Compatibility wrapper for the ant-colony evidence exploration demo."""
from __future__ import annotations

from .colony import AntColony


class SwarmIntelligence:
    """Run the in-memory colony heuristic; output is not a truth or evidence verdict."""

    def __init__(self, n: int = 100) -> None:
        if isinstance(n, bool) or n < 1:
            raise ValueError("n must be a positive integer")
        self.colony = AntColony(max(1, int(n) // 4))

    def verify(self) -> dict[str, int]:
        """Return the demo's pheromone count, not a verification of semantic truth."""
        return self.colony.run(20)


SwarmIntelligenceV8 = SwarmIntelligence
