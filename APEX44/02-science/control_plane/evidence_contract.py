from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


SCHEMA_ID = (
    "scientific-inference-control-plane-evidence-contract-v0.1"
)

EPISTEMIC_LAYERS = (
    "OBSERVED",
    "ANNOTATED",
    "DERIVED",
    "INFERRED",
    "GENERALIZED",
    "COMPRESSED",
)

CLAIM_SUPPORT_STATUSES = frozenset(
    {
        "NOT_ASSESSED",
        "UNSUPPORTED",
        "CONDITIONAL",
        "SUPPORTED",
        "REFUTED",
        "CONFLICTED",
        "BLOCKED",
    }
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
class EvidenceRecord:
    evidence_id: str
    epistemic_layer: str
    source: dict[str, Any]
    observation: dict[str, Any]
    derivation: dict[str, Any]
    independence: dict[str, Any]
    provenance: dict[str, Any]
    falsification: dict[str, Any]
    claim_support_status: str

    def validate(self) -> None:
        if not self.evidence_id:
            raise ValueError("evidence_id_required")

        if self.epistemic_layer not in EPISTEMIC_LAYERS:
            raise ValueError(
                f"invalid_epistemic_layer:{self.epistemic_layer}"
            )

        if not isinstance(self.source, dict):
            raise ValueError("source_object_required")

        source_hash = self.source.get("sha256")

        if (
            not isinstance(source_hash, str)
            or len(source_hash) != 64
            or any(c not in "0123456789abcdef" for c in source_hash)
        ):
            raise ValueError("source_sha256_invalid")

        if not isinstance(self.observation, dict):
            raise ValueError("observation_object_required")

        if not isinstance(self.derivation, dict):
            raise ValueError("derivation_object_required")

        if not isinstance(self.independence, dict):
            raise ValueError("independence_object_required")

        if not isinstance(self.provenance, dict):
            raise ValueError("provenance_object_required")

        if not isinstance(self.falsification, dict):
            raise ValueError("falsification_object_required")

        if self.claim_support_status not in CLAIM_SUPPORT_STATUSES:
            raise ValueError(
                "invalid_claim_support_status:"
                + self.claim_support_status
            )

        if (
            self.claim_support_status == "SUPPORTED"
            and self.epistemic_layer
            not in {
                "ANNOTATED",
                "DERIVED",
                "INFERRED",
                "GENERALIZED",
            }
        ):
            raise ValueError(
                "unsupported_layer_for_supported_claim"
            )

        if (
            self.epistemic_layer == "OBSERVED"
            and self.claim_support_status == "SUPPORTED"
        ):
            raise ValueError(
                "raw_observation_cannot_directly_support_claim"
            )

    def to_dict(self) -> dict[str, Any]:
        self.validate()

        return {
            "schema": SCHEMA_ID,
            "evidence_id": self.evidence_id,
            "epistemic_layer": self.epistemic_layer,
            "source": self.source,
            "observation": self.observation,
            "derivation": self.derivation,
            "independence": self.independence,
            "provenance": self.provenance,
            "falsification": self.falsification,
            "claim_support_status": self.claim_support_status,
        }


def evidence_hash(record: dict[str, Any]) -> str:
    payload = dict(record)
    payload.pop("evidence_hash", None)
    return sha256_canonical(payload)


def validate_record(record: dict[str, Any]) -> None:
    if not isinstance(record, dict):
        raise ValueError("record_must_be_object")

    if record.get("schema") != SCHEMA_ID:
        raise ValueError("invalid_schema")

    evidence = EvidenceRecord(
        evidence_id=record.get("evidence_id", ""),
        epistemic_layer=record.get(
            "epistemic_layer",
            "",
        ),
        source=record.get("source", {}),
        observation=record.get(
            "observation",
            {},
        ),
        derivation=record.get(
            "derivation",
            {},
        ),
        independence=record.get(
            "independence",
            {},
        ),
        provenance=record.get(
            "provenance",
            {},
        ),
        falsification=record.get(
            "falsification",
            {},
        ),
        claim_support_status=record.get(
            "claim_support_status",
            "",
        ),
    )

    evidence.validate()


def assess_claim_support(
    record: EvidenceRecord,
) -> dict[str, Any]:
    record.validate()

    reasons: list[str] = []
    status = record.claim_support_status

    if not record.provenance.get(
        "complete",
        False,
    ):
        reasons.append("provenance_incomplete")

    if not record.independence.get(
        "assessed",
        False,
    ):
        reasons.append("independence_not_assessed")

    if not record.falsification.get(
        "performed",
        False,
    ):
        reasons.append("falsification_not_performed")

    if reasons and status == "SUPPORTED":
        status = "CONDITIONAL"

    if record.epistemic_layer == "OBSERVED":
        status = (
            "BLOCKED"
            if status == "SUPPORTED"
            else status
        )
        reasons.append(
            "observation_is_not_independent_claim_support"
        )

    return {
        "evidence_id": record.evidence_id,
        "epistemic_layer": record.epistemic_layer,
        "claim_support_status": status,
        "reasons": sorted(set(reasons)),
        "claim_authorization": (
            status == "SUPPORTED"
            and not reasons
        ),
    }


def run_self_audit() -> dict[str, Any]:
    observed = EvidenceRecord(
        evidence_id="EVID-OBSERVED-001",
        epistemic_layer="OBSERVED",
        source={
            "path": "source.txt",
            "sha256": "0" * 64,
        },
        observation={
            "fact": "raw observed value",
        },
        derivation={},
        independence={
            "assessed": True,
        },
        provenance={
            "complete": True,
        },
        falsification={
            "performed": True,
        },
        claim_support_status="NOT_ASSESSED",
    )

    derived = EvidenceRecord(
        evidence_id="EVID-DERIVED-001",
        epistemic_layer="DERIVED",
        source={
            "path": "derived.json",
            "sha256": "1" * 64,
        },
        observation={
            "source_artifact": "EVID-OBSERVED-001",
        },
        derivation={
            "method": "deterministic_derivation",
        },
        independence={
            "assessed": True,
        },
        provenance={
            "complete": True,
        },
        falsification={
            "performed": True,
        },
        claim_support_status="SUPPORTED",
    )

    observed_result = assess_claim_support(observed)
    derived_result = assess_claim_support(derived)

    raw_support_block = False

    try:
        EvidenceRecord(
            evidence_id="EVID-ILLEGAL-001",
            epistemic_layer="OBSERVED",
            source={
                "path": "source.txt",
                "sha256": "2" * 64,
            },
            observation={},
            derivation={},
            independence={
                "assessed": True,
            },
            provenance={
                "complete": True,
            },
            falsification={
                "performed": True,
            },
            claim_support_status="SUPPORTED",
        ).validate()
    except ValueError as exc:
        raw_support_block = (
            str(exc)
            == "raw_observation_cannot_directly_support_claim"
        )

    return {
        "observed": observed_result,
        "derived": derived_result,
        "raw_observation_support_blocked": raw_support_block,
        "valid": (
            observed_result["claim_authorization"] is False
            and derived_result["claim_authorization"] is True
            and raw_support_block is True
        ),
    }
