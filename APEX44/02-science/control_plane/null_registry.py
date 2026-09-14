from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


SCHEMA_ID = (
    "scientific-inference-control-plane-null-registry-v0.1"
)

VALID_VISIBILITY = frozenset(
    {
        "NOT_SEEN",
        "PRE_REGISTERED_ONLY",
    }
)

VALID_STATUS = frozenset(
    {
        "REGISTERED",
        "SEALED",
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


def registry_hash(registry: dict[str, Any]) -> str:
    payload = dict(registry)
    payload.pop("registry_hash", None)
    return sha256_canonical(payload)


def null_hash(null_model: dict[str, Any]) -> str:
    return sha256_canonical(null_model)


@dataclass(frozen=True)
class NullModel:
    null_id: str
    family: str
    description: str
    preserves: tuple[str, ...]
    destroys: tuple[str, ...]
    parameters: dict[str, Any]
    selection_policy: dict[str, Any]
    result_visibility: str
    status: str

    def validate(self) -> None:
        if not self.null_id:
            raise ValueError("null_id_required")

        if not self.family:
            raise ValueError("null_family_required")

        if not self.description:
            raise ValueError("null_description_required")

        if not self.preserves:
            raise ValueError("null_preserves_required")

        if not self.destroys:
            raise ValueError("null_destroys_required")

        if not isinstance(self.parameters, dict):
            raise ValueError("null_parameters_required")

        if not isinstance(self.selection_policy, dict):
            raise ValueError(
                "null_selection_policy_required"
            )

        if self.result_visibility not in VALID_VISIBILITY:
            raise ValueError(
                "invalid_null_result_visibility:"
                + self.result_visibility
            )

        if self.status not in VALID_STATUS:
            raise ValueError(
                "invalid_null_status:"
                + self.status
            )

        if (
            self.result_visibility == "NOT_SEEN"
            and self.selection_policy.get(
                "result_inspection_allowed",
                False,
            )
        ):
            raise ValueError(
                "not_seen_null_cannot_allow_result_inspection"
            )

    def to_dict(self) -> dict[str, Any]:
        self.validate()

        return {
            "null_id": self.null_id,
            "family": self.family,
            "description": self.description,
            "preserves": list(self.preserves),
            "destroys": list(self.destroys),
            "parameters": self.parameters,
            "selection_policy": self.selection_policy,
            "result_visibility": self.result_visibility,
            "status": self.status,
        }


def validate_registry(
    registry: dict[str, Any],
    *,
    require_hash: bool = True,
) -> dict[str, Any]:
    if not isinstance(registry, dict):
        raise ValueError("registry_must_be_object")

    if registry.get("schema") != SCHEMA_ID:
        raise ValueError("invalid_registry_schema")

    for key in (
        "registry_id",
        "registry_version",
    ):
        value = registry.get(key)

        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"{key}_required"
            )

    if not isinstance(registry.get("sealed"), bool):
        raise ValueError("sealed_boolean_required")

    null_models = registry.get("null_models")

    if not isinstance(null_models, list):
        raise ValueError("null_models_array_required")

    ids: list[str] = []

    for value in null_models:
        if not isinstance(value, dict):
            raise ValueError(
                "null_model_must_be_object"
            )

        model = NullModel(
            null_id=value.get("null_id", ""),
            family=value.get("family", ""),
            description=value.get("description", ""),
            preserves=tuple(
                value.get("preserves", [])
            ),
            destroys=tuple(
                value.get("destroys", [])
            ),
            parameters=value.get(
                "parameters",
                {},
            ),
            selection_policy=value.get(
                "selection_policy",
                {},
            ),
            result_visibility=value.get(
                "result_visibility",
                "",
            ),
            status=value.get(
                "status",
                "",
            ),
        )

        model.validate()
        ids.append(model.null_id)

    duplicates = sorted(
        {
            value
            for value in ids
            if ids.count(value) > 1
        }
    )

    if duplicates:
        raise ValueError(
            "duplicate_null_ids:"
            + ",".join(duplicates)
        )

    computed_hash = registry_hash(registry)
    supplied_hash = registry.get(
        "registry_hash"
    )

    if require_hash and not supplied_hash:
        raise ValueError(
            "registry_hash_required"
        )

    if supplied_hash is not None:
        if supplied_hash != computed_hash:
            raise ValueError(
                "registry_hash_mismatch"
            )

    if (
        registry["sealed"]
        and any(
            value.get("status") == "REGISTERED"
            for value in null_models
        )
    ):
        raise ValueError(
            "sealed_registry_contains_unsealed_null"
        )

    return {
        "valid": True,
        "null_model_count": len(
            null_models
        ),
        "sealed": registry["sealed"],
        "computed_registry_hash": computed_hash,
        "duplicate_null_ids": duplicates,
    }
