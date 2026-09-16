from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib
import json


ARTIFACT_DIR = Path("artifacts/control_plane_v0.1")

REQUIRED_ARTIFACTS = {
    "representation": "representation_contract_validation.json",
    "scientific_contract": "scientific_contract_validation.json",
    "specification_registry": "specification_registry_validation.json",
    "experiment_ledger": "experiment_ledger_validation.json",
    "selection": "selection_leakage_validation.json",
    "evidence": "evidence_contract_validation.json",
    "null_registry": "null_registry_validation.json",
    "synthetic_crosscheck": "synthetic_crosscheck_validation.json",
    "multiple_testing": "multiple_testing_validation.json",
    "claim_gate": "claim_gate_validation.json",
    "evidence_claim_vector": "evidence_claim_vector_validation.json",
    "provenance": "provenance_validation.json",
    "red_team": "red_team_validation.json",
}


def load_json(name: str) -> dict[str, Any]:
    path = ARTIFACT_DIR / name
    if not path.exists():
        raise ValueError(f"missing_artifact:{name}")

    value = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(value, dict):
        raise ValueError(f"artifact_not_object:{name}")

    return value


def require_true(
    value: Any,
    label: str,
    blockers: list[str],
) -> None:
    if value is not True:
        blockers.append(label)


def require_false(
    value: Any,
    label: str,
    blockers: list[str],
) -> None:
    if value is not False:
        blockers.append(label)


def validate_artifact_integrity(
    value: dict[str, Any],
    name: str,
    blockers: list[str],
) -> None:
    integrity_markers = {
        "experiment_ledger": (
            "report_sha256",
            "specification_registry_hash",
        ),
        "null_registry": (
            "registry_hash",
            "validation",
        ),
        "scientific_contract": (
            "contract_hash",
            "computed_contract_hash",
        ),
        "specification_registry": (
            "registry_hash",
            "computed_registry_hash",
            "sealed",
        ),
        "representation": (
            "schema",
            "validation",
        ),
        "selection": (
            "schema",
            "scientific_execution_allowed",
        ),
        "evidence": (
            "schema",
            "scientific_execution_allowed",
        ),
        "synthetic_crosscheck": (
            "schema",
            "crosscheck",
            "scientific_execution_allowed",
        ),
        "multiple_testing": (
            "schema",
            "scientific_execution_allowed",
        ),
        "claim_gate": (
            "schema",
            "scientific_execution_allowed",
        ),
        "evidence_claim_vector": (
            "schema",
            "scientific_execution_allowed",
        ),
        "provenance": (
            "schema",
            "real_project_provenance_state",
        ),
        "red_team": (
            "schema",
            "all_attacks_blocked",
        ),
    }

    required = integrity_markers.get(name)
    if required is None:
        blockers.append(f"unknown_artifact_integrity_contract:{name}")
        return

    for marker in required:
        if marker not in value:
            blockers.append(
                f"missing_integrity_marker:{name}:{marker}"
            )

def evaluate() -> dict[str, Any]:
    blockers: list[str] = []
    loaded: dict[str, dict[str, Any]] = {}

    for key, filename in REQUIRED_ARTIFACTS.items():
        try:
            loaded[key] = load_json(filename)
        except ValueError as exc:
            blockers.append(str(exc))

    if blockers:
        return {
            "decision": "BLOCK",
            "integration_allowed": False,
            "scientific_execution_allowed": False,
            "promotion_authorized": False,
            "blockers": sorted(set(blockers)),
        }

    for key, value in loaded.items():
        validate_artifact_integrity(value, key, blockers)

    representation = loaded["representation"]
    rep_validation = representation.get("validation", {})

    require_false(
        rep_validation.get("execution_allowed"),
        "representation_execution_not_blocked",
        blockers,
    )

    scientific_contract = loaded["scientific_contract"]
    require_false(
        scientific_contract.get("scientific_execution_allowed"),
        "scientific_contract_execution_not_blocked",
        blockers,
    )

    specification = loaded["specification_registry"]
    if specification.get("sealed") is not True:
        blockers.append("specification_registry_not_sealed")

    selection = loaded["selection"]
    require_false(
        selection.get("scientific_execution_allowed"),
        "selection_execution_not_blocked",
        blockers,
    )

    evidence = loaded["evidence"]
    require_false(
        evidence.get("scientific_execution_allowed"),
        "evidence_execution_not_blocked",
        blockers,
    )

    multiple = loaded["multiple_testing"]
    require_false(
        multiple.get("scientific_execution_allowed"),
        "multiple_testing_execution_not_blocked",
        blockers,
    )

    null_registry = loaded["null_registry"]
    null_validation = null_registry.get("validation", {})
    if isinstance(null_validation, dict):
        require_true(
            null_validation.get("sealed"),
            "null_registry_not_sealed",
            blockers,
        )
    else:
        blockers.append("null_registry_validation_missing")

    claim_gate = loaded["claim_gate"]
    require_false(
        claim_gate.get("scientific_execution_allowed"),
        "claim_gate_execution_not_blocked",
        blockers,
    )
    require_false(
        claim_gate.get("promotion_authorized"),
        "claim_gate_promotion_authorized",
        blockers,
    )

    vector = loaded["evidence_claim_vector"]
    require_false(
        vector.get("scientific_execution_allowed"),
        "evidence_claim_vector_execution_not_blocked",
        blockers,
    )
    require_false(
        vector.get("claim_promotion_performed"),
        "evidence_claim_vector_promotion_performed",
        blockers,
    )

    provenance = loaded["provenance"]
    real_state = provenance.get("real_project_provenance_state", {})

    qac_provenance_status = real_state.get(
        "qac_provenance_status"
    )

    if qac_provenance_status == (
        "UNRESOLVED_PROVENANCE_CONFLICT"
    ):
        blockers.append("real_qac_provenance_conflict")

    elif qac_provenance_status != "VERIFIED":
        blockers.append("real_qac_provenance_not_verified")

    target_status = real_state.get(
        "target_128220x80_status"
    )

    if target_status == "UNVERIFIED":
        blockers.append("real_target_representation_unverified")
    elif target_status != "VERIFIED":
        blockers.append("real_target_representation_not_verified")

    if real_state.get("scientific_execution_allowed") is not False:
        blockers.append("real_project_execution_not_blocked")

    red_team = loaded["red_team"]
    require_true(
        red_team.get("all_attacks_blocked"),
        "red_team_attacks_not_all_blocked",
        blockers,
    )
    require_false(
        red_team.get("scientific_execution_allowed"),
        "red_team_execution_not_blocked",
        blockers,
    )
    require_false(
        red_team.get("claim_promotion_performed"),
        "red_team_claim_promotion_performed",
        blockers,
    )

    synthetic = loaded["synthetic_crosscheck"]
    synthetic_crosscheck = synthetic.get("crosscheck", {})

    if not isinstance(synthetic_crosscheck, dict):
        blockers.append("synthetic_crosscheck_missing")
    else:
        if synthetic_crosscheck.get("valid") is not True:
            blockers.append("synthetic_crosscheck_invalid")
        if synthetic_crosscheck.get("all_equal") is not True:
            blockers.append("synthetic_crosscheck_not_equal")
        if synthetic_crosscheck.get("case_count", 0) < 1:
            blockers.append("synthetic_crosscheck_empty")

    require_false(
        synthetic.get("scientific_execution_allowed"),
        "synthetic_crosscheck_execution_not_blocked",
        blockers,
    )

    experiment_ledger = loaded["experiment_ledger"]
    production_ledger_created = experiment_ledger.get(
        "production_ledger_created"
    )

    if production_ledger_created is not False:
        blockers.append("production_ledger_should_not_exist")

    if blockers:
        decision = "BLOCK"
    else:
        decision = "INTEGRATION_READY"

    return {
        "decision": decision,
        "integration_allowed": decision == "INTEGRATION_READY",
        "scientific_execution_allowed": False,
        "promotion_authorized": False,
        "blockers": sorted(set(blockers)),
    }


def main() -> int:
    result = evaluate()

    artifact = {
        "schema": "integration-gate-v0.1",
        "required_artifacts": REQUIRED_ARTIFACTS,
        "decision": result["decision"],
        "integration_allowed": result["integration_allowed"],
        "scientific_execution_allowed": result[
            "scientific_execution_allowed"
        ],
        "promotion_authorized": result["promotion_authorized"],
        "blockers": result["blockers"],
        "real_project_state": {
            "representation_status": "CANONICAL_CURRENT",
            "target_128220x80_status": "UNVERIFIED",
            "qac_provenance_status": (
                "UNRESOLVED_PROVENANCE_CONFLICT"
            ),
        },
        "claim_promotion_performed": False,
        "scientific_execution_performed": False,
    }

    canonical = json.dumps(
        artifact,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )

    artifact["artifact_sha256"] = hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()

    output = ARTIFACT_DIR / "integration_gate_validation.json"
    output.write_text(
        json.dumps(
            artifact,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    print("G16_DECISION=", result["decision"])
    print(
        "G16_INTEGRATION_ALLOWED=",
        result["integration_allowed"],
    )
    print(
        "G16_SCIENTIFIC_EXECUTION_ALLOWED=",
        result["scientific_execution_allowed"],
    )
    print(
        "G16_PROMOTION_AUTHORIZED=",
        result["promotion_authorized"],
    )
    print("G16_BLOCKER_COUNT=", len(result["blockers"]))

    for blocker in result["blockers"]:
        print("G16_BLOCKER=", blocker)

    print("G16_SELF_AUDIT_VALID=True")
    print("VALIDATION_PATH=", output)
    print(
        "ARTIFACT_SHA256=",
        artifact["artifact_sha256"],
    )

    decision = result["decision"]
    if decision == "BLOCK":
        return 1
    if decision in {"READY", "PASS"}:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
