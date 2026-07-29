from typing import Dict, List, Any
from.ontology import ApexOntology
from.knowledge_graph import KnowledgeGraph

class SemanticEngine:
    def __init__(self):
        self.ontology = ApexOntology()
        self.kg = KnowledgeGraph(self.ontology)
        self.kg.infer_transitive()

    def understand(self, term: str) -> Dict[str, Any]:
        ent = self.kg.query(term)
        if not ent:
            return {"found": False, "explanation": f"'{term}' is just a word"}
        return {"found": True, "type": ent.type, "explanation": self.kg.explain(term)}

    def answer_what_is(self, term: str) -> str:
        u = self.understand(term)
        return u.get("explanation", "Not found")

    def infer_new_knowledge(self, term: str) -> List[str]:
        return [f"{s} {r} {t} [INFERRED]" for s,r,t in self.kg.inferred_edges if s==term]

if __name__ == "__main__":
    eng = SemanticEngine()
    print(eng.answer_what_is("القاهرة"))
    print(eng.infer_new_knowledge("القاهرة"))
