from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


REQUIRED_FIELDS = (
    "observation",
    "annotation",
    "derivation",
    "inference",
    "generalization",
    "compression",
    "independence",
    "provenance",
    "falsification",
    "claim_support_authorized",
    "independent_support_count",
    "contradiction_present",
    "contradiction_preserved",
)

BOOLEAN_FIELDS = (
    "observation",
    "annotation",
    "derivation",
    "inference",
    "generalization",
    "compression",
    "independence",
    "provenance",
    "falsification",
    "claim_support_authorized",
    "contradiction_present",
    "contradiction_preserved",
)


@dataclass(frozen=True)
class EvidenceClaimVector:
    claim_id: str
    values: Mapping[str, Any]

    def validate(self) -> None:
        if not isinstance(self.claim_id, str) or not self.claim_id:
            raise ValueError("invalid_claim_id")

        keys = set(self.values)

        missing = [field for field in REQUIRED_FIELDS if field not in keys]
        if missing:
            raise ValueError(
                "missing_vector_fields:" + ",".join(sorted(missing))
            )

        allowed = set(REQUIRED_FIELDS)
        extra = sorted(keys - allowed)
        if extra:
            raise ValueError(
                "unexpected_vector_fields:" + ",".join(extra)
            )

        for field in BOOLEAN_FIELDS:
            if type(self.values[field]) is not bool:
                raise ValueError(f"non_boolean_field:{field}")

        support_count = self.values["independent_support_count"]
        if type(support_count) is not int or support_count < 0:
            raise ValueError("invalid_independent_support_count")

        if (
            self.values["contradiction_present"]
            and not self.values["contradiction_preserved"]
        ):
            raise ValueError("contradiction_not_preserved")

        if (
            self.values["claim_support_authorized"]
            and self.values["independent_support_count"] < 1
        ):
            raise ValueError("authorized_without_independent_support")

    def as_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "claim_id": self.claim_id,
            **dict(self.values),
        }


def build_vector(
    claim_id: str,
    *,
    observation: bool,
    annotation: bool,
    derivation: bool,
    inference: bool,
    generalization: bool,
    compression: bool,
    independence: bool,
    provenance: bool,
    falsification: bool,
    claim_support_authorized: bool,
    independent_support_count: int,
    contradiction_present: bool,
    contradiction_preserved: bool,
) -> EvidenceClaimVector:
    return EvidenceClaimVector(
        claim_id=claim_id,
        values={
            "observation": observation,
            "annotation": annotation,
            "derivation": derivation,
            "inference": inference,
            "generalization": generalization,
            "compression": compression,
            "independence": independence,
            "provenance": provenance,
            "falsification": falsification,
            "claim_support_authorized": claim_support_authorized,
            "independent_support_count": independent_support_count,
            "contradiction_present": contradiction_present,
            "contradiction_preserved": contradiction_preserved,
        },
    )


def validate_vector(vector: EvidenceClaimVector) -> dict[str, Any]:
    vector.validate()
    return {
        "valid": True,
        "claim_id": vector.claim_id,
        "dimensions": list(REQUIRED_FIELDS),
        "scalar_evidence_score_present": False,
        "contradiction_preserved": bool(
            vector.values["contradiction_preserved"]
        ),
    }
