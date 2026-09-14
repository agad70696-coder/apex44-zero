from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


SCHEMA_ID = (
    "scientific-inference-control-plane-representation-contract-v0.1"
)

VALID_REPRESENTATION_STATUSES = frozenset(
    {
        "CANONICAL_CURRENT",
        "VERIFIED_TARGET",
        "UNVERIFIED",
        "CONFLICT",
        "BLOCKED",
    }
)

VALID_PROVENANCE_STATUSES = frozenset(
    {
        "VERIFIED",
        "UNRESOLVED_PROVENANCE_CONFLICT",
        "UNKNOWN",
    }
)

VALID_TARGET_STATUSES = frozenset(
    {
        "CURRENT",
        "VERIFIED_TARGET",
        "UNVERIFIED_TARGET",
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


@dataclass(frozen=True)
class RepresentationContract:
    representation_id: str
    path: str
    dimensions: tuple[int, ...]
    representation_status: str
    source_sha256: str
    representation_sha256: str
    source_metadata: dict[str, Any]
    provenance_status: str
    target_status: str
    lock: bool
    execution_allowed: bool

    def validate(self) -> None:
        if not self.representation_id:
            raise ValueError("representation_id_required")

        if not self.path:
            raise ValueError("representation_path_required")

        if (
            not self.dimensions
            or not all(
                isinstance(x, int) and x > 0
                for x in self.dimensions
            )
        ):
            raise ValueError("representation_dimensions_invalid")

        if (
            self.representation_status
            not in VALID_REPRESENTATION_STATUSES
        ):
            raise ValueError(
                "invalid_representation_status:"
                + self.representation_status
            )

        if (
            len(self.source_sha256) != 64
            or any(
                c not in "0123456789abcdef"
                for c in self.source_sha256
            )
        ):
            raise ValueError("source_sha256_invalid")

        if (
            len(self.representation_sha256) != 64
            or any(
                c not in "0123456789abcdef"
                for c in self.representation_sha256
            )
        ):
            raise ValueError("representation_sha256_invalid")

        if not isinstance(self.source_metadata, dict):
            raise ValueError("source_metadata_required")

        if self.provenance_status not in VALID_PROVENANCE_STATUSES:
            raise ValueError(
                "invalid_provenance_status:"
                + self.provenance_status
            )

        if self.target_status not in VALID_TARGET_STATUSES:
            raise ValueError(
                "invalid_target_status:"
                + self.target_status
            )

        if not isinstance(self.lock, bool):
            raise ValueError("lock_boolean_required")

        if not isinstance(self.execution_allowed, bool):
            raise ValueError(
                "execution_allowed_boolean_required"
            )

        if (
            self.provenance_status
            == "UNRESOLVED_PROVENANCE_CONFLICT"
        ):
            if self.execution_allowed:
                raise ValueError(
                    "provenance_conflict_cannot_allow_execution"
                )

        if (
            self.representation_status
            in {
                "UNVERIFIED",
                "CONFLICT",
                "BLOCKED",
            }
            and self.execution_allowed
        ):
            raise ValueError(
                "unverified_or_blocked_representation_cannot_allow_execution"
            )

        if (
            self.target_status == "UNVERIFIED_TARGET"
            and self.execution_allowed
        ):
            raise ValueError(
                "unverified_target_cannot_allow_execution"
            )

        if self.execution_allowed and not self.lock:
            raise ValueError(
                "execution_requires_locked_representation"
            )

        if (
            self.execution_allowed
            and self.representation_status
            not in {
                "CANONICAL_CURRENT",
                "VERIFIED_TARGET",
            }
        ):
            raise ValueError(
                "execution_requires_verified_representation"
            )

    def to_dict(self) -> dict[str, Any]:
        self.validate()

        return {
            "schema": SCHEMA_ID,
            "representation_id": self.representation_id,
            "path": self.path,
            "dimensions": list(self.dimensions),
            "representation_status": self.representation_status,
            "source_sha256": self.source_sha256,
            "representation_sha256": self.representation_sha256,
            "source_metadata": self.source_metadata,
            "provenance_status": self.provenance_status,
            "target_status": self.target_status,
            "lock": self.lock,
            "execution_allowed": self.execution_allowed,
        }


def validate_contract(
    contract: dict[str, Any],
    *,
    require_hash: bool = True,
) -> dict[str, Any]:
    if not isinstance(contract, dict):
        raise ValueError("contract_must_be_object")

    if contract.get("schema") != SCHEMA_ID:
        raise ValueError("invalid_schema")

    required = (
        "representation_id",
        "path",
        "dimensions",
        "representation_status",
        "source_sha256",
        "representation_sha256",
        "source_metadata",
        "provenance_status",
        "target_status",
        "lock",
        "execution_allowed",
    )

    for key in required:
        if key not in contract:
            raise ValueError(
                f"contract_field_required:{key}"
            )

    object_value = RepresentationContract(
        representation_id=contract["representation_id"],
        path=contract["path"],
        dimensions=tuple(contract["dimensions"]),
        representation_status=contract[
            "representation_status"
        ],
        source_sha256=contract["source_sha256"],
        representation_sha256=contract[
            "representation_sha256"
        ],
        source_metadata=contract["source_metadata"],
        provenance_status=contract[
            "provenance_status"
        ],
        target_status=contract["target_status"],
        lock=contract["lock"],
        execution_allowed=contract[
            "execution_allowed"
        ],
    )

    object_value.validate()

    computed_hash = contract_hash(contract)
    supplied_hash = contract.get("contract_hash")

    if require_hash and not supplied_hash:
        raise ValueError("contract_hash_required")

    if supplied_hash is not None:
        if supplied_hash != computed_hash:
            raise ValueError("contract_hash_mismatch")

    return {
        "valid": True,
        "computed_contract_hash": computed_hash,
        "execution_allowed": object_value.execution_allowed,
        "representation_status": (
            object_value.representation_status
        ),
        "provenance_status": (
            object_value.provenance_status
        ),
        "target_status": object_value.target_status,
    }


def run_self_audit() -> dict[str, Any]:
    current_blocked = RepresentationContract(
        representation_id="REP-CURRENT-001",
        path=(
            "APEX44/03-computation/output/"
            "B_real_6236x1642.npz"
        ),
        dimensions=(6236, 1642),
        representation_status="CANONICAL_CURRENT",
        source_sha256="0" * 64,
        representation_sha256="1" * 64,
        source_metadata={
            "source": "QAC",
            "provenance_note": (
                "metadata digest conflict preserved"
            ),
        },
        provenance_status=(
            "UNRESOLVED_PROVENANCE_CONFLICT"
        ),
        target_status="CURRENT",
        lock=True,
        execution_allowed=False,
    )

    current_blocked.validate()

    target_blocked = RepresentationContract(
        representation_id="REP-TARGET-001",
        path="UNVERIFIED_TARGET",
        dimensions=(128220, 80),
        representation_status="UNVERIFIED",
        source_sha256="2" * 64,
        representation_sha256="3" * 64,
        source_metadata={
            "target": "128220x80",
            "verification": "not_established",
        },
        provenance_status="UNKNOWN",
        target_status="UNVERIFIED_TARGET",
        lock=False,
        execution_allowed=False,
    )

    target_blocked.validate()

    illegal = RepresentationContract(
        representation_id="REP-ILLEGAL-001",
        path="UNVERIFIED_TARGET",
        dimensions=(128220, 80),
        representation_status="UNVERIFIED",
        source_sha256="4" * 64,
        representation_sha256="5" * 64,
        source_metadata={},
        provenance_status="UNKNOWN",
        target_status="UNVERIFIED_TARGET",
        lock=True,
        execution_allowed=True,
    )

    execution_blocked = False

    try:
        illegal.validate()
    except ValueError as exc:
        execution_blocked = True
        execution_error = str(exc)
    else:
        execution_error = None

    return {
        "current_conflict_preserved": (
            current_blocked.execution_allowed is False
        ),
        "unverified_target_blocked": (
            target_blocked.execution_allowed is False
        ),
        "illegal_execution_blocked": execution_blocked,
        "illegal_execution_error": execution_error,
        "valid": (
            current_blocked.execution_allowed is False
            and target_blocked.execution_allowed is False
            and execution_blocked is True
        ),
    }
