from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


SCHEMA_ID = (
    "scientific-inference-control-plane-scientific-contract-v0.1"
)

ALLOWED_REPRESENTATION_STATUSES = frozenset(
    {
        "CANONICAL_CURRENT",
        "VERIFIED_TARGET",
        "UNVERIFIED",
        "CONFLICT",
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


def contract_hash(contract: dict[str, Any]) -> str:
    payload = dict(contract)
    payload.pop("contract_hash", None)
    return sha256_canonical(payload)


def _require_string(data: dict[str, Any], key: str) -> None:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key}_required")


def validate_contract(
    contract: dict[str, Any],
    *,
    require_hash: bool = True,
) -> dict[str, Any]:
    if not isinstance(contract, dict):
        raise ValueError("contract_must_be_object")

    if contract.get("schema") != SCHEMA_ID:
        raise ValueError("invalid_schema")

    for key in (
        "contract_id",
        "question",
        "hypothesis",
        "estimand",
        "unit",
    ):
        _require_string(contract, key)

    source_manifest = contract.get("source_manifest")
    if not isinstance(source_manifest, dict):
        raise ValueError("source_manifest_required")

    _require_string(source_manifest, "path")
    source_hash = source_manifest.get("sha256")
    if (
        not isinstance(source_hash, str)
        or len(source_hash) != 64
        or any(c not in "0123456789abcdef" for c in source_hash)
    ):
        raise ValueError("source_manifest_sha256_invalid")

    representation = contract.get("representation")
    if not isinstance(representation, dict):
        raise ValueError("representation_required")

    for key in (
        "path",
        "status",
        "source_hash",
        "B_hash",
    ):
        _require_string(representation, key)

    dimensions = representation.get("dimensions")
    if (
        not isinstance(dimensions, list)
        or not dimensions
        or not all(
            isinstance(x, int) and x > 0
            for x in dimensions
        )
    ):
        raise ValueError("representation_dimensions_invalid")

    if representation["status"] not in ALLOWED_REPRESENTATION_STATUSES:
        raise ValueError(
            f"invalid_representation_status:{representation['status']}"
        )

    if not isinstance(representation.get("lock"), bool):
        raise ValueError("representation_lock_required")

    allowed = contract.get("allowed_specifications")
    if (
        not isinstance(allowed, list)
        or not allowed
        or not all(
            isinstance(x, str) and x.strip()
            for x in allowed
        )
    ):
        raise ValueError("allowed_specifications_required")

    forbidden = contract.get("forbidden_adaptive_changes")
    if not isinstance(forbidden, list):
        raise ValueError("forbidden_adaptive_changes_required")

    confirmation = contract.get("confirmation_policy")
    if not isinstance(confirmation, dict):
        raise ValueError("confirmation_policy_required")

    claim_policy = contract.get("claim_policy")
    if not isinstance(claim_policy, dict):
        raise ValueError("claim_policy_required")

    scientific_execution_allowed = True

    if representation["status"] in {
        "CONFLICT",
        "BLOCKED",
    }:
        scientific_execution_allowed = False

    if (
        representation["status"] == "UNVERIFIED"
        and representation.get("lock") is not True
    ):
        scientific_execution_allowed = False

    if contract.get("qac_provenance_status") == (
        "UNRESOLVED_PROVENANCE_CONFLICT"
    ):
        scientific_execution_allowed = False

    computed_hash = contract_hash(contract)

    supplied_hash = contract.get("contract_hash")

    if require_hash and not supplied_hash:
        raise ValueError("contract_hash_required")

    if supplied_hash is not None:
        if supplied_hash != computed_hash:
            raise ValueError("contract_hash_mismatch")

    return {
        "valid": True,
        "scientific_execution_allowed": scientific_execution_allowed,
        "promotion_allowed": False,
        "computed_contract_hash": computed_hash,
        "representation_status": representation["status"],
        "qac_provenance_status": contract.get(
            "qac_provenance_status"
        ),
    }


def load_contract(path: str | Path) -> dict[str, Any]:
    value = json.loads(
        Path(path).read_text(encoding="utf-8")
    )
    if not isinstance(value, dict):
        raise ValueError("contract_must_be_object")
    return value


def validate_file(
    path: str | Path,
    *,
    require_hash: bool = True,
) -> dict[str, Any]:
    contract = load_contract(path)
    result = validate_contract(
        contract,
        require_hash=require_hash,
    )
    result["path"] = str(path)
    return result
