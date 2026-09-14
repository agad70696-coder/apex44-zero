from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
import hashlib
import json
from pathlib import Path
from copy import deepcopy


@dataclass(frozen=True)
class AttackCase:
    attack_id: str
    description: str
    expected_block: str


def canonical(value: Mapping[str, Any]) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def record_hash(record: Mapping[str, Any]) -> str:
    payload = canonical(record).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def verify_hashed_record(record: Mapping[str, Any]) -> None:
    declared = record.get("record_hash")
    if not isinstance(declared, str):
        raise ValueError("missing_record_hash")

    body = dict(record)
    body.pop("record_hash", None)

    actual = record_hash(body)
    if declared != actual:
        raise ValueError("record_hash_mismatch")


def verify_no_unsupported_promotion(record: Mapping[str, Any]) -> None:
    if record.get("decision") != "PROMOTE":
        return

    vector = record.get("evidence_vector")
    if not isinstance(vector, Mapping):
        raise ValueError("promotion_without_evidence_vector")

    if vector.get("claim_support_authorized") is not True:
        raise ValueError("promotion_without_support_authorization")

    count = vector.get("independent_support_count", 0)
    if not isinstance(count, int) or count < 1:
        raise ValueError("promotion_without_independent_support")

    if record.get("provenance_status") != "VERIFIED":
        raise ValueError("promotion_with_unverified_provenance")

    if record.get("representation_status") != "VERIFIED":
        raise ValueError("promotion_with_unverified_representation")


def verify_conflict_preservation(record: Mapping[str, Any]) -> None:
    if record.get("contradiction_present") is True:
        if record.get("contradiction_preserved") is not True:
            raise ValueError("contradiction_deleted")


def verify_no_scalar_replacement(record: Mapping[str, Any]) -> None:
    vector = record.get("evidence_vector")
    if not isinstance(vector, Mapping):
        return

    if "evidence_score" in vector or "support_score" in vector:
        raise ValueError("scalar_evidence_replacement_detected")


def verify_claim_identity_binding(
    record: Mapping[str, Any],
    expected_claim_id: str,
) -> None:
    if record.get("claim_id") != expected_claim_id:
        raise ValueError("claim_identity_mismatch")


def build_attack_cases() -> list[AttackCase]:
    return [
        AttackCase(
            "RT-001",
            "Promote computation-only claim",
            "promotion_without_support_authorization",
        ),
        AttackCase(
            "RT-002",
            "Promote with zero independent support",
            "promotion_without_independent_support",
        ),
        AttackCase(
            "RT-003",
            "Promote with provenance conflict",
            "promotion_with_unverified_provenance",
        ),
        AttackCase(
            "RT-004",
            "Promote with representation blocked",
            "promotion_with_unverified_representation",
        ),
        AttackCase(
            "RT-005",
            "Delete contradiction before promotion",
            "contradiction_deleted",
        ),
        AttackCase(
            "RT-006",
            "Replace evidence vector with scalar score",
            "scalar_evidence_replacement_detected",
        ),
        AttackCase(
            "RT-007",
            "Swap claim identity",
            "claim_identity_mismatch",
        ),
        AttackCase(
            "RT-008",
            "Tamper with hashed governance record",
            "record_hash_mismatch",
        ),
    ]


def main() -> int:
    base_vector = {
        "observation": True,
        "annotation": True,
        "derivation": True,
        "inference": False,
        "generalization": False,
        "compression": False,
        "independence": True,
        "provenance": True,
        "falsification": True,
        "claim_support_authorized": True,
        "independent_support_count": 1,
    }

    base = {
        "claim_id": "CLAIM-G15-001",
        "decision": "PROMOTE",
        "provenance_status": "VERIFIED",
        "representation_status": "VERIFIED",
        "contradiction_present": False,
        "contradiction_preserved": True,
        "evidence_vector": dict(base_vector),
    }

    results: dict[str, str] = {}

    attack = deepcopy(base)
    attack["evidence_vector"]["claim_support_authorized"] = False
    try:
        verify_no_unsupported_promotion(attack)
    except ValueError as exc:
        assert str(exc) == "promotion_without_support_authorization"
        results["RT-001"] = "BLOCKED"
    else:
        results["RT-001"] = "ESCAPED"

    attack = deepcopy(base)
    attack["evidence_vector"] = dict(base_vector)
    attack["evidence_vector"]["independent_support_count"] = 0
    try:
        verify_no_unsupported_promotion(attack)
    except ValueError as exc:
        assert str(exc) == "promotion_without_independent_support"
        results["RT-002"] = "BLOCKED"
    else:
        results["RT-002"] = "ESCAPED"

    attack = deepcopy(base)
    attack["provenance_status"] = "UNRESOLVED_PROVENANCE_CONFLICT"
    try:
        verify_no_unsupported_promotion(attack)
    except ValueError as exc:
        assert str(exc) == "promotion_with_unverified_provenance"
        results["RT-003"] = "BLOCKED"
    else:
        results["RT-003"] = "ESCAPED"

    attack = deepcopy(base)
    attack["representation_status"] = "BLOCKED"
    try:
        verify_no_unsupported_promotion(attack)
    except ValueError as exc:
        assert str(exc) == "promotion_with_unverified_representation"
        results["RT-004"] = "BLOCKED"
    else:
        results["RT-004"] = "ESCAPED"

    attack = deepcopy(base)
    attack["contradiction_present"] = True
    attack["contradiction_preserved"] = False
    try:
        verify_conflict_preservation(attack)
    except ValueError as exc:
        assert str(exc) == "contradiction_deleted"
        results["RT-005"] = "BLOCKED"
    else:
        results["RT-005"] = "ESCAPED"

    attack = deepcopy(base)
    attack["evidence_vector"] = {
        "support_score": 0.99,
    }
    try:
        verify_no_scalar_replacement(attack)
    except ValueError as exc:
        assert str(exc) == "scalar_evidence_replacement_detected"
        results["RT-006"] = "BLOCKED"
    else:
        results["RT-006"] = "ESCAPED"

    attack = deepcopy(base)
    try:
        verify_claim_identity_binding(attack, "CLAIM-G15-EXPECTED")
    except ValueError as exc:
        assert str(exc) == "claim_identity_mismatch"
        results["RT-007"] = "BLOCKED"
    else:
        results["RT-007"] = "ESCAPED"

    original = deepcopy(base)
    original["record_hash"] = record_hash(original)

    tampered = dict(original)
    tampered["decision"] = "BLOCK"

    try:
        verify_hashed_record(tampered)
    except ValueError as exc:
        assert str(exc) == "record_hash_mismatch"
        results["RT-008"] = "BLOCKED"
    else:
        results["RT-008"] = "ESCAPED"

    assert all(
        value == "BLOCKED"
        for value in results.values()
    ), results

    cases = build_attack_cases()

    artifact = {
        "schema": "red-team-v0.1",
        "attacks": [
            {
                "attack_id": case.attack_id,
                "description": case.description,
                "expected_block": case.expected_block,
                "observed": results[case.attack_id],
            }
            for case in cases
        ],
        "all_attacks_blocked": True,
        "scientific_execution_allowed": False,
        "claim_promotion_performed": False,
        "real_project_state": {
            "representation_status": "CANONICAL_CURRENT",
            "target_128220x80_status": "UNVERIFIED",
            "qac_provenance_status": "UNRESOLVED_PROVENANCE_CONFLICT",
        },
    }

    payload = canonical(artifact).encode("utf-8")
    artifact["artifact_sha256"] = hashlib.sha256(payload).hexdigest()

    output = (
        Path("artifacts/control_plane_v0.1")
        / "red_team_validation.json"
    )

    output.write_text(
        json.dumps(
            artifact,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    print("TEST_RT001_COMPUTATION_ONLY_BLOCK=PASS")
    print("TEST_RT002_ZERO_INDEPENDENT_SUPPORT_BLOCK=PASS")
    print("TEST_RT003_PROVENANCE_CONFLICT_BLOCK=PASS")
    print("TEST_RT004_REPRESENTATION_BLOCKED_PROMOTION=PASS")
    print("TEST_RT005_CONTRADICTION_DELETION_BLOCK=PASS")
    print("TEST_RT006_SCALAR_REPLACEMENT_BLOCK=PASS")
    print("TEST_RT007_CLAIM_IDENTITY_BINDING=PASS")
    print("TEST_RT008_HASH_TAMPER_BLOCK=PASS")
    print("G15_SELF_AUDIT_VALID=True")
    print("VALIDATION_PATH=", output)
    print("ARTIFACT_SHA256=", artifact["artifact_sha256"])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
