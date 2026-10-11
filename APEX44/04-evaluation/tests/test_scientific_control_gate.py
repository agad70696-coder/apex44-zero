"""Gate-mechanics tests only; synthetic fixtures are not scientific evidence."""
from __future__ import annotations
import copy
import hashlib
import json
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import scientific_control_gate as gate  # noqa: E402
CONTRACT = json.loads((ROOT / "scientific_control_contract.json").read_text(encoding="utf-8"))

def evidence(control_id: str, root: Path) -> list[dict[str, str]]:
    raw = f"synthetic evaluator fixture only:{control_id}".encode()
    relative = Path("synthetic-evidence") / f"{control_id}.bin"
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    return [{"source": f"synthetic-fixture://{control_id}", "path": relative.as_posix(), "role": "unit-test-only", "sha256": hashlib.sha256(raw).hexdigest()}]

def fixture(root: Path) -> dict:
    metrics = {
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
    return {"schema_version":"apex44-scientific-observations-v1","evaluation_id":"synthetic-mechanics-test-only","subject":{"commit_sha":"a"*40,"dataset_sha256":"b"*64,"model_id":"synthetic-test-only"},"observations":[{"control_id":cid,"metrics":values,"evidence":evidence(cid,root)} for cid,values in metrics.items()]}

def test_contract_has_fourteen_unique_controls() -> None:
    ids = [item["id"] for item in CONTRACT["controls"]]
    assert len(ids) == 14 and len(set(ids)) == 14
    assert set(ids) == {"S1","S2","S3","S4","S5","S6","S9","S10","S11","S12","S13","S14","S15","S16"}

def test_missing_observations_are_blocked() -> None:
    report = gate.evaluate({}, CONTRACT)
    assert report["scientific_control_gate_status"] == "BLOCKED"
    assert report["summary"] == {"PASS":0,"FAIL":0,"BLOCKED":14}
    assert all(row["reason"] == "OBSERVATION_MISSING" for row in report["controls"])
    assert report["release_promotion_authority"] == "NONE"

def test_synthetic_fixture_exercises_all_evaluators(tmp_path: Path) -> None:
    report = gate.evaluate(fixture(tmp_path), CONTRACT, evidence_root=tmp_path)
    assert report["scientific_control_gate_status"] == "PASS_SCOPED"
    assert report["summary"] == {"PASS":14,"FAIL":0,"BLOCKED":0}
    assert report["release_promotion_authority"] == "NONE"
    assert "does not prove origin" in report["interpretation_boundary"]

def test_leaked_fixture_cannot_be_promoted(tmp_path: Path) -> None:
    document = fixture(tmp_path)
    next(item for item in document["observations"] if item["control_id"] == "S10")["metrics"]["promotion_allowed_on_leaked_fixture"] = True
    report = gate.evaluate(document, CONTRACT, evidence_root=tmp_path)
    control = next(item for item in report["controls"] if item["control_id"] == "S10")
    assert control["status"] == "FAIL" and report["scientific_control_gate_status"] == "BLOCKED"

def test_surprisal_formula_mismatch_fails(tmp_path: Path) -> None:
    document = fixture(tmp_path)
    next(item for item in document["observations"] if item["control_id"] == "S3")["metrics"]["surprisal_bits"][1] = 99.0
    report = gate.evaluate(document, CONTRACT, evidence_root=tmp_path)
    control = next(item for item in report["controls"] if item["control_id"] == "S3")
    assert control["status"] == "FAIL" and control["reason"] == "CALIBRATION_MISMATCH"

def test_missing_evidence_blocks_otherwise_passing_observation(tmp_path: Path) -> None:
    document = fixture(tmp_path)
    next(item for item in document["observations"] if item["control_id"] == "S15")["evidence"] = []
    report = gate.evaluate(document, CONTRACT, evidence_root=tmp_path)
    control = next(item for item in report["controls"] if item["control_id"] == "S15")
    assert control["status"] == "BLOCKED" and control["reason"] == "EVIDENCE_MISSING"

def test_large_annotation_disagreement_cannot_be_promoted(tmp_path: Path) -> None:
    document = fixture(tmp_path)
    metrics = next(item for item in document["observations"] if item["control_id"] == "S14")["metrics"]
    metrics["annotation_variant_scores"] = {"A":0.1,"B":0.9}
    metrics["claim_promoted"] = True
    report = gate.evaluate(document, CONTRACT, evidence_root=tmp_path)
    assert next(item for item in report["controls"] if item["control_id"] == "S14")["status"] == "FAIL"

def test_duplicate_observation_is_blocked(tmp_path: Path) -> None:
    document = fixture(tmp_path)
    document["observations"].append(copy.deepcopy(document["observations"][0]))
    control = next(item for item in gate.evaluate(document, CONTRACT, evidence_root=tmp_path)["controls"] if item["control_id"] == "S1")
    assert control["status"] == "BLOCKED" and control["reason"] == "DUPLICATE_CONTROL_OBSERVATION"

def test_digest_mismatch_blocks_claimed_evidence(tmp_path: Path) -> None:
    document = fixture(tmp_path)
    item = next(row for row in document["observations"] if row["control_id"] == "S3")["evidence"][0]
    (tmp_path / item["path"]).write_bytes(b"tampered bytes")
    control = next(row for row in gate.evaluate(document, CONTRACT, evidence_root=tmp_path)["controls"] if row["control_id"] == "S3")
    assert control["status"] == "BLOCKED" and control["reason"] == "EVIDENCE_ITEM_0_SHA256_MISMATCH"

def test_missing_file_blocks_claimed_evidence(tmp_path: Path) -> None:
    document = fixture(tmp_path)
    item = next(row for row in document["observations"] if row["control_id"] == "S3")["evidence"][0]
    (tmp_path / item["path"]).unlink()
    control = next(row for row in gate.evaluate(document, CONTRACT, evidence_root=tmp_path)["controls"] if row["control_id"] == "S3")
    assert control["status"] == "BLOCKED" and control["reason"] == "EVIDENCE_ITEM_0_FILE_MISSING"

def test_evidence_path_traversal_is_blocked(tmp_path: Path) -> None:
    document = fixture(tmp_path)
    item = next(row for row in document["observations"] if row["control_id"] == "S3")["evidence"][0]
    item["path"] = "../../outside.bin"
    control = next(row for row in gate.evaluate(document, CONTRACT, evidence_root=tmp_path)["controls"] if row["control_id"] == "S3")
    assert control["status"] == "BLOCKED" and control["reason"] == "EVIDENCE_ITEM_0_PATH_INVALID"

def test_symlink_escape_is_blocked(tmp_path: Path) -> None:
    document = fixture(tmp_path)
    item = next(row for row in document["observations"] if row["control_id"] == "S3")["evidence"][0]
    outside = tmp_path.parent / "outside-evidence.bin"
    outside.write_bytes(b"outside root")
    link = tmp_path / item["path"]
    link.unlink()
    link.symlink_to(outside)
    control = next(row for row in gate.evaluate(document, CONTRACT, evidence_root=tmp_path)["controls"] if row["control_id"] == "S3")
    assert control["status"] == "BLOCKED" and control["reason"] == "EVIDENCE_ITEM_0_PATH_OUTSIDE_ROOT"

def test_blocked_snapshot_matches_evaluator_output() -> None:
    snapshot = json.loads((ROOT / "tests" / "control_results.json").read_text(encoding="utf-8"))
    assert snapshot == gate.evaluate({}, CONTRACT)
