from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


SCHEMA_ID = (
    "scientific-inference-control-plane-multiple-testing-v0.1"
)

VALID_PROCEDURES = frozenset(
    {
        "HOLM",
        "BH",
    }
)

VALID_VISIBILITY = frozenset(
    {
        "NOT_SEEN",
        "SEEN_AFTER_LOCK",
        "SEEN_BEFORE_LOCK",
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


def specification_hash(
    specification: dict[str, Any],
) -> str:
    payload = dict(specification)
    payload.pop("specification_hash", None)
    return sha256_canonical(payload)


@dataclass(frozen=True)
class MultipleTestingSpecification:
    specification_id: str
    family_id: str
    family_definition: str
    hypotheses: tuple[str, ...]
    alpha: float
    procedure: str
    result_visibility: str
    locked: bool
    execution_allowed: bool

    def validate(self) -> None:
        if not self.specification_id:
            raise ValueError(
                "specification_id_required"
            )

        if not self.family_id:
            raise ValueError(
                "family_id_required"
            )

        if not self.family_definition:
            raise ValueError(
                "family_definition_required"
            )

        if not self.hypotheses:
            raise ValueError(
                "hypotheses_required"
            )

        if not (
            isinstance(self.alpha, (int, float))
            and 0 < self.alpha < 1
        ):
            raise ValueError(
                "alpha_out_of_range"
            )

        if self.procedure not in VALID_PROCEDURES:
            raise ValueError(
                f"invalid_procedure:{self.procedure}"
            )

        if self.result_visibility not in VALID_VISIBILITY:
            raise ValueError(
                "invalid_result_visibility:"
                + self.result_visibility
            )

        if not isinstance(self.locked, bool):
            raise ValueError(
                "locked_boolean_required"
            )

        if not isinstance(
            self.execution_allowed,
            bool,
        ):
            raise ValueError(
                "execution_allowed_boolean_required"
            )

        if (
            self.result_visibility
            == "SEEN_BEFORE_LOCK"
        ):
            if self.execution_allowed:
                raise ValueError(
                    "result_seen_before_lock_cannot_execute"
                )

        if (
            self.execution_allowed
            and not self.locked
        ):
            raise ValueError(
                "execution_requires_locked_multiple_testing_spec"
            )

        if (
            self.execution_allowed
            and self.result_visibility
            != "NOT_SEEN"
        ):
            raise ValueError(
                "execution_requires_unseen_results"
            )

    def to_dict(self) -> dict[str, Any]:
        self.validate()

        return {
            "schema": SCHEMA_ID,
            "specification_id": self.specification_id,
            "family_id": self.family_id,
            "family_definition": self.family_definition,
            "hypotheses": list(self.hypotheses),
            "alpha": self.alpha,
            "procedure": self.procedure,
            "result_visibility": self.result_visibility,
            "locked": self.locked,
            "execution_allowed": self.execution_allowed,
        }


def adjust_holm(
    p_values: list[float],
) -> list[float]:
    n = len(p_values)

    if n == 0:
        return []

    for value in p_values:
        if not 0 <= value <= 1:
            raise ValueError(
                "p_value_out_of_range"
            )

    indexed = sorted(
        enumerate(p_values),
        key=lambda item: (
            item[1],
            item[0],
        ),
    )

    adjusted_sorted: list[float] = [
        0.0
    ] * n

    running_max = 0.0

    for rank, (index, value) in enumerate(
        indexed,
        start=1,
    ):
        adjusted = min(
            1.0,
            (n - rank + 1) * value,
        )
        running_max = max(
            running_max,
            adjusted,
        )
        adjusted_sorted[index] = running_max

    return adjusted_sorted


def adjust_bh(
    p_values: list[float],
) -> list[float]:
    n = len(p_values)

    if n == 0:
        return []

    for value in p_values:
        if not 0 <= value <= 1:
            raise ValueError(
                "p_value_out_of_range"
            )

    indexed = sorted(
        enumerate(p_values),
        key=lambda item: (
            item[1],
            item[0],
        ),
    )

    adjusted_sorted: list[float] = [
        0.0
    ] * n

    running_min = 1.0

    for rank in range(
        n,
        0,
        -1,
    ):
        index, value = indexed[rank - 1]

        adjusted = min(
            1.0,
            value * n / rank,
        )

        running_min = min(
            running_min,
            adjusted,
        )

        adjusted_sorted[index] = running_min

    return adjusted_sorted


def reject_mask(
    adjusted_p_values: list[float],
    alpha: float,
) -> list[bool]:
    if not (
        isinstance(alpha, (int, float))
        and 0 < alpha < 1
    ):
        raise ValueError(
            "alpha_out_of_range"
        )

    return [
        value <= alpha
        for value in adjusted_p_values
    ]


def validate_specification(
    specification: dict[str, Any],
    *,
    require_hash: bool = True,
) -> dict[str, Any]:
    if not isinstance(
        specification,
        dict,
    ):
        raise ValueError(
            "specification_must_be_object"
        )

    if specification.get("schema") != SCHEMA_ID:
        raise ValueError(
            "invalid_schema"
        )

    object_value = MultipleTestingSpecification(
        specification_id=specification.get(
            "specification_id",
            "",
        ),
        family_id=specification.get(
            "family_id",
            "",
        ),
        family_definition=specification.get(
            "family_definition",
            "",
        ),
        hypotheses=tuple(
            specification.get(
                "hypotheses",
                [],
            )
        ),
        alpha=specification.get(
            "alpha",
            0,
        ),
        procedure=specification.get(
            "procedure",
            "",
        ),
        result_visibility=specification.get(
            "result_visibility",
            "",
        ),
        locked=specification.get(
            "locked",
            False,
        ),
        execution_allowed=specification.get(
            "execution_allowed",
            False,
        ),
    )

    object_value.validate()

    computed_hash = specification_hash(
        specification
    )

    supplied_hash = specification.get(
        "specification_hash"
    )

    if require_hash and not supplied_hash:
        raise ValueError(
            "specification_hash_required"
        )

    if supplied_hash is not None:
        if supplied_hash != computed_hash:
            raise ValueError(
                "specification_hash_mismatch"
            )

    return {
        "valid": True,
        "specification_hash": computed_hash,
        "execution_allowed": (
            object_value.execution_allowed
        ),
    }


def run_self_audit() -> dict[str, Any]:
    p_values = [
        0.001,
        0.01,
        0.03,
        0.20,
        0.80,
    ]

    holm = adjust_holm(p_values)
    bh = adjust_bh(p_values)

    expected_holm = [
        0.005,
        0.04,
        0.09,
        0.40,
        0.80,
    ]

    expected_bh = [
        0.005,
        0.025,
        0.05,
        0.25,
        0.80,
    ]

    deterministic_holm = all(
        abs(a - b) <= 1e-12
        for a, b in zip(
            holm,
            expected_holm,
        )
    )

    deterministic_bh = all(
        abs(a - b) <= 1e-12
        for a, b in zip(
            bh,
            expected_bh,
        )
    )

    spec = MultipleTestingSpecification(
        specification_id="SIC-MT-V0.1-001",
        family_id="FAMILY-SYNTHETIC-001",
        family_definition=(
            "All five synthetic hypotheses in this controlled "
            "test family."
        ),
        hypotheses=(
            "H1",
            "H2",
            "H3",
            "H4",
            "H5",
        ),
        alpha=0.05,
        procedure="HOLM",
        result_visibility="NOT_SEEN",
        locked=True,
        execution_allowed=True,
    )

    spec.validate()

    pre_result_change_blocked = MultipleTestingSpecification(
        specification_id="SIC-MT-V0.1-002",
        family_id="FAMILY-SYNTHETIC-001",
        family_definition="Same family",
        hypotheses=("H1", "H2"),
        alpha=0.05,
        procedure="BH",
        result_visibility="SEEN_BEFORE_LOCK",
        locked=False,
        execution_allowed=True,
    )

    blocked = False

    try:
        pre_result_change_blocked.validate()
    except ValueError as exc:
        blocked = (
            str(exc)
            == "result_seen_before_lock_cannot_execute"
        )

    return {
        "holm": holm,
        "bh": bh,
        "holm_expected": expected_holm,
        "bh_expected": expected_bh,
        "holm_deterministic": deterministic_holm,
        "bh_deterministic": deterministic_bh,
        "pre_result_change_blocked": blocked,
        "valid": (
            deterministic_holm
            and deterministic_bh
            and blocked
        ),
    }
