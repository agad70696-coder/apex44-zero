"""Semantic-query facade over the local knowledge graph."""
from __future__ import annotations

from typing import Any

from .knowledge_graph import KnowledgeGraph
from .ontology import ApexOntology


class SemanticEngine:
    def __init__(self) -> None:
        self.ontology = ApexOntology()
        self.kg = KnowledgeGraph(self.ontology)
        self.kg.infer_transitive()

    def understand(self, term: str) -> dict[str, Any]:
        entity = self.kg.query(term)
        if entity is None:
            return {"found": False, "explanation": f"'{term}' is not present in the configured ontology"}
        return {
            "found": True,
            "type": entity.type,
            "explanation": self.kg.explain(term),
        }

    def answer_what_is(self, term: str) -> str:
        result = self.understand(term)
        return str(result.get("explanation", "Not found"))

    def infer_new_knowledge(self, term: str) -> list[str]:
        return [
            f"{source} {relation} {target} [INFERRED]"
            for source, relation, target in self.kg.inferred_edges
            if source == term
        ]


SemanticEngineV8 = SemanticEngine


if __name__ == "__main__":
    engine = SemanticEngine()
    print(engine.answer_what_is("القاهرة"))
    print(engine.infer_new_knowledge("القاهرة"))
