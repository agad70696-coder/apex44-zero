"""Typed, minimal ontology used by the IRRE knowledge graph.

These structures represent an explicit in-memory graph. A transitive relation declaration is
a rule available to the graph engine, not evidence that any particular inferred fact is true.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Relation:
    name: str
    transitive: bool = False


@dataclass
class Entity:
    name: str
    type: str = "Entity"
    relations: dict[str, list[str]] = field(default_factory=dict)

    def add_relation(self, relation: str, target: str) -> None:
        """Record a directed relation without duplicating the same target."""
        if not relation or not target:
            raise ValueError("relation and target must be non-empty")
        targets = self.relations.setdefault(relation, [])
        if target not in targets:
            targets.append(target)


class ApexOntology:
    """Mutable ontology containing entities and typed relation declarations."""

    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.relations: dict[str, Relation] = {
            "located_in": Relation("located_in", transitive=True),
            "proves": Relation("proves", transitive=False),
        }
        self.add_entity(Entity("مصر", type="Country"))
        self.add_entity(Entity("القاهرة", type="City"))
        self.add_entity(Entity("Evidence", type="KnowledgeEntity"))
        self.add_entity(Entity("Claim", type="KnowledgeEntity"))
        self.add_relation("القاهرة", "located_in", "مصر")
        self.add_relation("Evidence", "proves", "Claim")

    def add_entity(self, entity: Entity) -> None:
        if not isinstance(entity, Entity):
            raise TypeError("entity must be an Entity instance")
        if not entity.name:
            raise ValueError("entity name must not be empty")
        self.entities[entity.name] = entity

    def add_relation(self, source: str, relation: str, target: str) -> None:
        if source not in self.entities:
            raise KeyError(f"Unknown source entity: {source}")
        if target not in self.entities:
            raise KeyError(f"Unknown target entity: {target}")
        if relation not in self.relations:
            self.relations[relation] = Relation(relation)
        self.entities[source].add_relation(relation, target)

    def get_entity(self, name: str) -> Entity | None:
        return self.entities.get(name)


# Compatibility name used by earlier IRRE modules.
OntologyV8 = ApexOntology
