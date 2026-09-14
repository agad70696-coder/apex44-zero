from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


SCHEMA_ID = (
    "scientific-inference-control-plane-claim-gate-v0.1"
)


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def sha256_canonical(value: Any) -> str:
    return hashlib.sha256(
        canonical_json(value).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class ClaimInput:
    claim_id: str
    claim_text: str
    evidence_vector: dict[str, Any]
    provenance_status: str
    representation_status: str
    selection_status: str
    multiple_testing_status: str
    falsification_status: str
    computation_status: str

    def validate(self) -> None:
        if not self.claim_id:
            raise ValueError(
                "claim_id_required"
            )

        if not self.claim_text:
            raise ValueError(
                "claim_text_required"
            )

        if not isinstance(
            self.evidence_vector,
            dict,
        ):
            raise ValueError(
                "evidence_vector_required"
            )

        if self.computation_status == "SUCCESS":
            return


def evaluate_claim(
    claim: ClaimInput,
) -> dict[str, Any]:
    claim.validate()

    blockers: list[str] = []
    warnings: list[str] = []

    required_vector_fields = (
        "observation",
        "derivation",
        "independence",
        "provenance",
        "falsification",
        "claim_support_authorized",
        "independent_support_count",
    )

    for field in required_vector_fields:
        if field not in claim.evidence_vector:
            blockers.append(
                f"evidence_vector_missing:{field}"
            )

    claim_support_authorized = claim.evidence_vector.get(
        "claim_support_authorized",
        False,
    )

    if claim_support_authorized is not True:
        blockers.append(
            "claim_support_authorization_missing"
        )

    independent_support_count = claim.evidence_vector.get(
        "independent_support_count",
        0,
    )

    if (
        not isinstance(
            independent_support_count,
            int,
        )
        or independent_support_count < 1
    ):
        blockers.append(
            "independent_support_required"
        )

    if (
        claim.provenance_status
        != "VERIFIED"
    ):
        blockers.append(
            "provenance_not_verified"
        )

    if claim.representation_status != "VERIFIED":
        blockers.append(
            "representation_not_verified"
        )

    if claim.selection_status != "PASS":
        blockers.append(
            "selection_control_not_pass"
        )

    if (
        claim.multiple_testing_status
        != "PASS"
    ):
        blockers.append(
            "multiple_testing_not_pass"
        )

    if claim.falsification_status != "PASS":
        blockers.append(
            "falsification_not_pass"
        )

    if claim.computation_status == "SUCCESS":
        warnings.append(
            "computation_success_is_not_claim_support"
        )

    if claim.computation_status != "SUCCESS":
        blockers.append(
            "computation_not_successful"
        )

    if blockers:
        decision = "BLOCK"
    else:
        decision = "PROMOTE"

    return {
        "schema": SCHEMA_ID,
        "claim_id": claim.claim_id,
        "claim_text": claim.claim_text,
        "blockers": sorted(set(blockers)),
        "warnings": sorted(set(warnings)),
        "decision": decision,
        "promotion_authorized": (
            decision == "PROMOTE"
        ),
    }


def gate_hash(
    result: dict[str, Any],
) -> str:
    payload = dict(result)
    payload.pop("gate_hash", None)
    return sha256_canonical(payload)


def validate_gate_record(
    record: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise ValueError(
            "gate_record_must_be_object"
        )

    if record.get("schema") != SCHEMA_ID:
        raise ValueError(
            "invalid_schema"
        )

    supplied_hash = record.get(
        "gate_hash"
    )

    if not isinstance(
        supplied_hash,
        str,
    ):
        raise ValueError(
            "gate_hash_required"
        )

    expected_hash = gate_hash(record)

    if supplied_hash != expected_hash:
        raise ValueError(
            "gate_hash_mismatch"
        )

    if record.get("decision") == "PROMOTE":
        if not record.get(
            "promotion_authorized",
            False,
        ):
            raise ValueError(
                "promote_without_authorization"
            )

    return {
        "valid": True,
        "gate_hash": expected_hash,
        "decision": record["decision"],
    }


def run_self_audit() -> dict[str, Any]:
    computation_only = ClaimInput(
        claim_id="CLAIM-G12-COMPUTATION-ONLY",
        claim_text=(
            "A successful computation establishes scientific support."
        ),
        evidence_vector={
            "observation": True,
            "derivation": True,
            "independence": True,
            "provenance": True,
            "falsification": True,
        },
        provenance_status="VERIFIED",
        representation_status="VERIFIED",
        selection_status="PASS",
        multiple_testing_status="PASS",
        falsification_status="PASS",
        computation_status="SUCCESS",
    )

    result = evaluate_claim(
        computation_only
    )

    computation_only_blocked = (
        result["decision"] == "PROMOTE"
    )

    real_current_conflict = ClaimInput(
        claim_id="CLAIM-G12-REAL-CURRENT",
        claim_text=(
            "The current QAC-backed representation is ready "
            "for scientific claim promotion."
        ),
        evidence_vector={
            "observation": True,
            "derivation": True,
            "independence": True,
            "provenance": True,
            "falsification": True,
        },
        provenance_status=(
            "UNRESOLVED_PROVENANCE_CONFLICT"
        ),
        representation_status="BLOCKED",
        selection_status="PASS",
        multiple_testing_status="PASS",
        falsification_status="PASS",
        computation_status="SUCCESS",
    )

    real_result = evaluate_claim(
        real_current_conflict
    )

    real_blocked = (
        real_result["decision"] == "BLOCK"
    )

    return {
        "computation_only": result,
        "real_current_conflict": real_result,
        "computation_only_blocked": (
            not computation_only_blocked
        ),
        "real_current_conflict_blocked": (
            real_blocked
        ),
        "valid": (
            not computation_only_blocked
            and real_blocked
        ),
    }
