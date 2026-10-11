"""Knowledge graph operations over explicitly declared ontology relations."""
from __future__ import annotations

from .ontology import ApexOntology, Entity


class KnowledgeGraph:
    def __init__(self, ontology: ApexOntology | None = None) -> None:
        self.ontology = ontology or ApexOntology()
        self.inferred_edges: list[tuple[str, str, str]] = []

    def query(self, name: str) -> Entity | None:
        return self.ontology.get_entity(name)

    def traverse(self, start: str, relation: str, depth: int = 3) -> list[str]:
        if depth < 0:
            raise ValueError("depth must not be negative")
        visited: set[str] = set()
        result: list[str] = []
        stack = [(start, 0)]
        while stack:
            current, distance = stack.pop()
            if current in visited or distance > depth:
                continue
            visited.add(current)
            if current != start:
                result.append(current)
            entity = self.query(current)
            if entity is not None and relation in entity.relations:
                for target in entity.relations[relation]:
                    if target not in visited:
                        stack.append((target, distance + 1))
        return result

    def infer_transitive(self) -> list[tuple[str, str, str]]:
        """Add graph closure edges for declared transitive relations."""
        self.inferred_edges = []
        for relation_name, relation_definition in self.ontology.relations.items():
            if not relation_definition.transitive:
                continue
            # Work from a snapshot so newly inferred edges cannot create an unbounded loop.
            original_edges = [
                (entity_name, target)
                for entity_name, entity in self.ontology.entities.items()
                for target in entity.relations.get(relation_name, [])
            ]
            additions: list[tuple[str, str]] = []
            for source, middle in original_edges:
                middle_entity = self.query(middle)
                if middle_entity is None:
                    continue
                for target in middle_entity.relations.get(relation_name, []):
                    source_entity = self.query(source)
                    if source_entity is not None and target not in source_entity.relations.get(relation_name, []):
                        additions.append((source, target))
            for source, target in additions:
                source_entity = self.query(source)
                if source_entity is None:
                    continue
                source_entity.add_relation(relation_name, target)
                self.inferred_edges.append((source, relation_name, target))
        return self.inferred_edges

    def explain(self, name: str) -> str:
        entity = self.query(name)
        if entity is None:
            return f"'{name}' not found"
        lines = [f"{entity.name} is an entity:", f" Type: {entity.type}"]
        for relation, targets in entity.relations.items():
            lines.append(f" {relation} -> {', '.join(targets)}")
        path = self.traverse(name, "located_in", 5)
        if path:
            lines.append(f" Inferred path: {name} located_in {', '.join(path)}")
        return "\n".join(lines)


KnowledgeGraphV8 = KnowledgeGraph
