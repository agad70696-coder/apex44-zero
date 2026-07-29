from typing import List, Tuple, Optional
from.ontology import ApexOntology, Entity

class KnowledgeGraph:
    def __init__(self, ontology: ApexOntology = None):
        self.ontology = ontology or ApexOntology()
        self.inferred_edges: List[Tuple[str, str, str]] = []

    def query(self, name: str) -> Optional[Entity]:
        return self.ontology.get_entity(name)

    def traverse(self, start: str, relation: str, depth: int = 3) -> List[str]:
        visited = set()
        result = []
        stack = [(start, 0)]
        while stack:
            cur, d = stack.pop()
            if cur in visited or d > depth:
                continue
            visited.add(cur)
            if cur!= start:
                result.append(cur)
            ent = self.query(cur)
            if ent and relation in ent.relations:
                for tgt in ent.relations[relation]:
                    if tgt not in visited:
                        stack.append((tgt, d+1))
        return result

    def infer_transitive(self):
        self.inferred_edges = []
        for rel_name, rel_def in self.ontology.relations.items():
            if not rel_def.transitive:
                continue
            for ename, ent in self.ontology.entities.items():
                if rel_name not in ent.relations:
                    continue
                for mid in ent.relations[rel_name]:
                    mid_ent = self.query(mid)
                    if not mid_ent or rel_name not in mid_ent.relations:
                        continue
                    for tgt in mid_ent.relations[rel_name]:
                        if rel_name not in ent.relations or tgt not in ent.relations[rel_name]:
                            ent.add_relation(rel_name, tgt)
                            self.inferred_edges.append((ename, rel_name, tgt))
        return self.inferred_edges

    def explain(self, name: str) -> str:
        ent = self.query(name)
        if not ent:
            return f"'{name}' not found"
        lines = [f"🧠 {ent.name} is not just a word:", f" Type: {ent.type}"]
        for rel, tgts in ent.relations.items():
            lines.append(f" {rel} → {', '.join(tgts)}")
        path = self.traverse(name, "located_in", 5)
        if path:
            lines.append(f" Inferred: {name} located_in {', '.join(path)}")
        return "\n".join(lines)
