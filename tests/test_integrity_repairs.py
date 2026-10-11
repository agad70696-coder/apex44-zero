"""Regression tests for modules that previously prevented repository-wide linting."""
from IRRE.knowledge.knowledge_graph import KnowledgeGraph
from IRRE.knowledge.ontology import ApexOntology, Entity, Relation
from IRRE.prediction.predictive_evidence import PredictiveEvidence
from IRRE.swarm.swarm_intelligence import SwarmIntelligence


def test_ontology_graph_is_constructible_and_transitive() -> None:
    ontology = ApexOntology()
    ontology.add_entity(Entity("Africa", type="Continent"))
    ontology.add_relation("مصر", "located_in", "Africa")
    graph = KnowledgeGraph(ontology)
    assert graph.query("القاهرة") is not None
    edges = graph.infer_transitive()
    assert ("القاهرة", "located_in", "Africa") in edges
    assert ontology.relations["located_in"] == Relation("located_in", transitive=True)


def test_prediction_record_hash_detects_mutation() -> None:
    evidence = PredictiveEvidence("model-1", "dataset-sha", "weather")
    record = evidence.add_prediction("heavy rain", 0.8, "medium")
    assert evidence.verify_prediction(record)
    altered = record.copy()
    altered["prediction"] = "clear sky"
    assert not evidence.verify_prediction(altered)


def test_extreme_prediction_is_marked_for_review_not_called_false() -> None:
    evidence = PredictiveEvidence("model-1", "dataset-sha", "market")
    record = evidence.add_prediction("market crash", 1.0, "critical")
    assert record["requires_review"] is True
    assert evidence.verify_prediction(record)


def test_swarm_demo_returns_bounded_result_shape() -> None:
    result = SwarmIntelligence(n=8).verify()
    assert set(result) == {"found"}
    assert isinstance(result["found"], int)
    assert result["found"] >= 0
