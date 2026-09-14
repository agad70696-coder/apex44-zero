from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


SCHEMA_ID = (
    "scientific-inference-control-plane-specification-registry-v0.1"
)

VALID_SPECIFICATION_STATUSES = frozenset(
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


def specification_hash(specification: dict[str, Any]) -> str:
    return sha256_canonical(specification)


def validate_specification(
    specification: dict[str, Any],
) -> None:
    required = (
        "specification_id",
        "contract_id",
        "contract_hash",
        "question",
        "hypothesis",
        "estimand",
        "unit",
        "representation",
        "null_policy",
        "selection_policy",
        "multiple_testing_policy",
        "confirmation_policy",
        "claim_policy",
        "status",
    )

    for key in required:
        if key not in specification:
            raise ValueError(
                f"specification_field_required:{key}"
            )

    for key in (
        "specification_id",
        "contract_id",
        "question",
        "hypothesis",
        "estimand",
        "unit",
    ):
        value = specification[key]
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"specification_string_required:{key}"
            )

    contract_hash = specification["contract_hash"]

    if (
        not isinstance(contract_hash, str)
        or len(contract_hash) != 64
        or any(c not in "0123456789abcdef" for c in contract_hash)
    ):
        raise ValueError("specification_contract_hash_invalid")

    if specification["status"] not in VALID_SPECIFICATION_STATUSES:
        raise ValueError(
            f"invalid_specification_status:{specification['status']}"
        )

    for key in (
        "representation",
        "null_policy",
        "selection_policy",
        "multiple_testing_policy",
        "confirmation_policy",
        "claim_policy",
    ):
        if not isinstance(specification[key], dict):
            raise ValueError(
                f"specification_object_required:{key}"
            )


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
            raise ValueError(f"{key}_required")

    if not isinstance(registry.get("sealed"), bool):
        raise ValueError("sealed_boolean_required")

    specifications = registry.get("specifications")

    if not isinstance(specifications, list):
        raise ValueError("specifications_array_required")

    ids = []

    for specification in specifications:
        if not isinstance(specification, dict):
            raise ValueError(
                "specification_must_be_object"
            )

        validate_specification(specification)
        ids.append(specification["specification_id"])

    duplicates = sorted(
        {
            value
            for value in ids
            if ids.count(value) > 1
        }
    )

    if duplicates:
        raise ValueError(
            "duplicate_specification_ids:"
            + ",".join(duplicates)
        )

    computed_hash = registry_hash(registry)
    supplied_hash = registry.get("registry_hash")

    if require_hash and not supplied_hash:
        raise ValueError("registry_hash_required")

    if supplied_hash is not None and supplied_hash != computed_hash:
        raise ValueError("registry_hash_mismatch")

    return {
        "valid": True,
        "specification_count": len(specifications),
        "sealed": registry["sealed"],
        "computed_registry_hash": computed_hash,
        "duplicate_specification_ids": duplicates,
    }


def load_registry(path: str | Path) -> dict[str, Any]:
    value = json.loads(
        Path(path).read_text(encoding="utf-8")
    )

    if not isinstance(value, dict):
        raise ValueError("registry_must_be_object")

    return value


def validate_file(
    path: str | Path,
    *,
    require_hash: bool = True,
) -> dict[str, Any]:
    registry = load_registry(path)
    result = validate_registry(
        registry,
        require_hash=require_hash,
    )
    result["path"] = str(path)
    return result
