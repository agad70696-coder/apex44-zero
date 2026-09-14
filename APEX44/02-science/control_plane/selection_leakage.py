from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


SCHEMA_ID = (
    "scientific-inference-control-plane-selection-leakage-v0.1"
)

RESULT_VISIBILITY_STATES = frozenset(
    {
        "NOT_SEEN",
        "SEEN_AFTER_SELECTION_LOCK",
        "SEEN_BEFORE_SELECTION",
        "UNKNOWN",
    }
)

DECISION_STATUSES = frozenset(
    {
        "ALLOWED",
        "BLOCKED",
        "INCONCLUSIVE",
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
class SelectionDecision:
    specification_id: str
    selection_stage: str
    selection_rules: tuple[str, ...]
    result_visibility: str
    observed_result_hash: str | None

    def validate(self) -> None:
        if not self.specification_id:
            raise ValueError("specification_id_required")

        if not self.selection_stage:
            raise ValueError("selection_stage_required")

        if not self.selection_rules:
            raise ValueError("selection_rules_required")

        if self.result_visibility not in RESULT_VISIBILITY_STATES:
            raise ValueError(
                f"invalid_result_visibility:{self.result_visibility}"
            )

        if self.result_visibility == "SEEN_BEFORE_SELECTION":
            raise ValueError(
                "selection_leakage_result_seen_before_selection"
            )

        if (
            self.result_visibility == "UNKNOWN"
            and self.observed_result_hash is not None
        ):
            raise ValueError(
                "unknown_visibility_cannot_have_observed_result"
            )

        if (
            self.result_visibility == "NOT_SEEN"
            and self.observed_result_hash is not None
        ):
            raise ValueError(
                "not_seen_cannot_have_observed_result"
            )

    def to_dict(self) -> dict[str, Any]:
        self.validate()

        return {
            "schema": SCHEMA_ID,
            "specification_id": self.specification_id,
            "selection_stage": self.selection_stage,
            "selection_rules": list(self.selection_rules),
            "result_visibility": self.result_visibility,
            "observed_result_hash": self.observed_result_hash,
        }


def evaluate_selection(
    decision: SelectionDecision,
) -> dict[str, Any]:
    violations: list[str] = []

    try:
        decision.validate()
    except ValueError as exc:
        violations.append(str(exc))

    if decision.result_visibility == "SEEN_BEFORE_SELECTION":
        violations.append(
            "result_observed_before_selection_lock"
        )

    if decision.result_visibility == "UNKNOWN":
        violations.append(
            "result_visibility_unknown"
        )

    if violations:
        status = "BLOCKED"
    elif decision.result_visibility == "SEEN_AFTER_SELECTION_LOCK":
        status = "ALLOWED"
    elif decision.result_visibility == "NOT_SEEN":
        status = "ALLOWED"
    else:
        status = "INCONCLUSIVE"

    payload = {
        "schema": SCHEMA_ID,
        "specification_id": decision.specification_id,
        "selection_stage": decision.selection_stage,
        "selection_rules": list(decision.selection_rules),
        "result_visibility": decision.result_visibility,
        "observed_result_hash": decision.observed_result_hash,
        "decision_status": status,
        "violations": sorted(set(violations)),
    }

    payload["decision_hash"] = sha256_canonical(payload)

    return payload


def validate_record(record: dict[str, Any]) -> None:
    if not isinstance(record, dict):
        raise ValueError("record_must_be_object")

    if record.get("schema") != SCHEMA_ID:
        raise ValueError("invalid_schema")

    required = (
        "specification_id",
        "selection_stage",
        "selection_rules",
        "result_visibility",
        "observed_result_hash",
        "decision_hash",
        "decision_status",
        "violations",
    )

    for key in required:
        if key not in record:
            raise ValueError(
                f"record_field_required:{key}"
            )

    if record["decision_status"] not in DECISION_STATUSES:
        raise ValueError(
            f"invalid_decision_status:{record['decision_status']}"
        )

    payload = dict(record)
    supplied_hash = payload.pop("decision_hash")

    computed_hash = sha256_canonical(payload)

    if supplied_hash != computed_hash:
        raise ValueError("decision_hash_mismatch")


def run_self_audit() -> dict[str, Any]:
    cases = [
        SelectionDecision(
            specification_id="SIC-SPEC-V0.1-001",
            selection_stage="specification_selection",
            selection_rules=(
                "selection_rules_registered_before_execution",
            ),
            result_visibility="NOT_SEEN",
            observed_result_hash=None,
        ),
        SelectionDecision(
            specification_id="SIC-SPEC-V0.1-001",
            selection_stage="post_lock_confirmation",
            selection_rules=(
                "specification_locked_before_result_inspection",
            ),
            result_visibility="SEEN_AFTER_SELECTION_LOCK",
            observed_result_hash="a" * 64,
        ),
    ]

    evaluated = [
        evaluate_selection(case)
        for case in cases
    ]

    leakage_case = {
        "specification_id": "SIC-SPEC-V0.1-001",
        "selection_stage": "specification_selection",
        "selection_rules": [
            "selection_rules_registered_before_execution"
        ],
        "result_visibility": "SEEN_BEFORE_SELECTION",
        "observed_result_hash": "b" * 64,
    }

    blocked = evaluate_selection(
        SelectionDecision(
            specification_id=leakage_case["specification_id"],
            selection_stage=leakage_case["selection_stage"],
            selection_rules=tuple(
                leakage_case["selection_rules"]
            ),
            result_visibility=leakage_case[
                "result_visibility"
            ],
            observed_result_hash=leakage_case[
                "observed_result_hash"
            ],
        )
    )

    return {
        "allowed_cases": evaluated,
        "blocked_case": blocked,
        "valid": (
            evaluated[0]["decision_status"] == "ALLOWED"
            and evaluated[1]["decision_status"] == "ALLOWED"
            and blocked["decision_status"] == "BLOCKED"
        ),
    }
