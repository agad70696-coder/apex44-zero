"""Gate-mechanics tests only; synthetic fixtures are not scientific evidence."""
from __future__ import annotations
import copy,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
import scientific_control_gate as gate  # noqa: E402
CONTRACT=json.loads((ROOT/"scientific_control_contract.json").read_text(encoding="utf-8"))

def evidence(cid: str)->list[dict[str,str]]:
    return [{"source":f"synthetic-fixture://{cid}","role":"unit-test-only","sha256":hashlib.sha256(f"TEST:{cid}".encode()).hexdigest()}]

def fixture()->dict:
    m={
      "S1":{"constraint_density":0.12,"choice_cardinality":5},
      "S2":{"constraint_density":0.82,"choice_cardinality":2},
      "S3":{"probabilities":[0.125,0.25,0.5,1.0],"surprisal_bits":[3.0,2.0,1.0,0.0]},
      "S4":{"matched_score_pairs":[{"short_score":0.4,"padded_score":0.41},{"short_score":0.6,"padded_score":0.59},{"short_score":0.2,"padded_score":0.21}]},
      "S5":{"baseline_score":0.5,"perturbation_curve":[{"noise_percent":0,"score":0.5},{"noise_percent":5,"score":0.53},{"noise_percent":10,"score":0.55},{"noise_percent":20,"score":0.57}]},
      "S6":{"scores_by_representation":{"ROOT":{"a":0.1,"b":0.4,"c":0.7,"d":0.9},"LEMMA":{"a":0.12,"b":0.42,"c":0.68,"d":0.91},"POS":{"a":0.09,"b":0.38,"c":0.71,"d":0.88},"SYNTAX":{"a":0.11,"b":0.43,"c":0.69,"d":0.92}}},
      "S9":{"artifact_fixture_id":"synthetic-artifact-01","generator_seed":44,"injected_artifact_detected":True,"clean_control_false_positive_rate":0.02},
      "S10":{"leakage_injected_detected":True,"promotion_allowed_on_leaked_fixture":False,"clean_fixture_not_flagged":True},
      "S11":{"legal_transform_results":[{"transform_id":"unicode-normalization","scope_preserved":True},{"transform_id":"whitespace-normalization","scope_preserved":True}],"illegal_transform_results":[{"transform_id":"split-leakage","rejected":True},{"transform_id":"scope-expansion","rejected":True}]},
      "S12":{"candidate_score":0.82,"strongest_baseline_score":0.75,"adjusted_p_value":0.02},
      "S13":{"hidden_constraints":[{"constraint_id":"candidate-1","status":"CANDIDATE","provenance_ref":"synthetic-fixture://S13"}],"unverified_promoted_as_fact":False},
      "S14":{"annotation_variant_scores":{"A":0.50,"B":0.54,"C":0.52},"claim_promoted":False},
      "S15":{"critical_failure_injected":True,"promotion_blocked":True,"override_authority_checked":True},
      "S16":{"failure_detected":True,"failure_type":"PROVENANCE","location":"fixture/input.json:4","evidence_ref":"synthetic-fixture://S16","reproduction_command":"python -m pytest"}
    }
    return {"schema_version":"apex44-scientific-observations-v1","evaluation_id":"synthetic-mechanics-test-only","subject":{"commit_sha":"a"*40,"dataset_sha256":"b"*64,"model_id":"synthetic-test-only"},"observations":[{"control_id":k,"metrics":v,"evidence":evidence(k)} for k,v in m.items()]}

def test_contract_has_fourteen_unique_scientific_controls() -> None:
    ids=[x["id"] for x in CONTRACT["controls"]]
    assert len(ids)==14 and len(set(ids))==14
    assert set(ids)=={"S1","S2","S3","S4","S5","S6","S9","S10","S11","S12","S13","S14","S15","S16"}

def test_missing_evidence_is_blocked_not_passed() -> None:
    r=gate.evaluate({},CONTRACT)
    assert r["scientific_control_gate_status"]=="BLOCKED"
    assert r["summary"]=={"PASS":0,"FAIL":0,"BLOCKED":14}
    assert r["release_promotion_authority"]=="NONE"

def test_synthetic_fixtures_exercise_all_gate_branches() -> None:
    r=gate.evaluate(fixture(),CONTRACT)
    assert r["scientific_control_gate_status"]=="PASS_SCOPED"
    assert r["summary"]=={"PASS":14,"FAIL":0,"BLOCKED":0}
    assert r["release_promotion_authority"]=="NONE"
    assert "proposed operational thresholds" in r["interpretation_boundary"]

def test_leakage_control_fails_if_leaked_fixture_can_be_promoted() -> None:
    d=fixture(); next(x for x in d["observations"] if x["control_id"]=="S10")["metrics"]["promotion_allowed_on_leaked_fixture"]=True
    r=gate.evaluate(d,CONTRACT); x=next(x for x in r["controls"] if x["control_id"]=="S10")
    assert x["status"]=="FAIL" and r["scientific_control_gate_status"]=="BLOCKED"

def test_surprisal_formula_mismatch_fails() -> None:
    d=fixture(); next(x for x in d["observations"] if x["control_id"]=="S3")["metrics"]["surprisal_bits"][1]=99.0
    r=gate.evaluate(d,CONTRACT); x=next(x for x in r["controls"] if x["control_id"]=="S3")
    assert x["status"]=="FAIL" and x["reason"]=="CALIBRATION_MISMATCH"

def test_missing_source_evidence_blocks_a_passing_observation() -> None:
    d=fixture(); next(x for x in d["observations"] if x["control_id"]=="S15")["evidence"]=[]
    r=gate.evaluate(d,CONTRACT); x=next(x for x in r["controls"] if x["control_id"]=="S15")
    assert x["status"]=="BLOCKED" and x["reason"]=="EVIDENCE_MISSING"

def test_annotation_disagreement_blocks_claim_promotion() -> None:
    d=fixture(); m=next(x for x in d["observations"] if x["control_id"]=="S14")["metrics"]
    m["annotation_variant_scores"]={"A":0.1,"B":0.9}; m["claim_promoted"]=True
    r=gate.evaluate(d,CONTRACT); assert next(x for x in r["controls"] if x["control_id"]=="S14")["status"]=="FAIL"

def test_duplicate_observation_is_blocked() -> None:
    d=fixture(); d["observations"].append(copy.deepcopy(d["observations"][0]))
    x=next(x for x in gate.evaluate(d,CONTRACT)["controls"] if x["control_id"]=="S1")
    assert x["status"]=="BLOCKED" and x["reason"]=="DUPLICATE_CONTROL_OBSERVATION"
