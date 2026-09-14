from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, ClassVar


VALID_STATUSES = frozenset(
    {
        "PASS",
        "FAIL",
        "INVALID",
        "NONCONVERGED",
        "ABORTED",
        "SUPERSEDED",
    }
)

FAILURE_STATUSES = frozenset(
    {
        "FAIL",
        "INVALID",
        "NONCONVERGED",
        "ABORTED",
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
class ExperimentRecord:
    experiment_id: str
    specification_id: str
    parent_experiment_id: str | None
    source_hash: str
    code_commit: str
    parameters: dict[str, Any]
    seed: int | None
    rng_policy: str
    environment_hash: str
    status: str
    start_time_utc: str
    end_time_utc: str | None
    result_hash: str | None
    failure_reason: str | None = None
    seen_results_before_change: bool = False

    SCHEMA: ClassVar[str] = (
        "scientific-inference-control-plane-experiment-ledger-v0.1"
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.SCHEMA,
            "experiment_id": self.experiment_id,
            "specification_id": self.specification_id,
            "parent_experiment_id": self.parent_experiment_id,
            "source_hash": self.source_hash,
            "code_commit": self.code_commit,
            "parameters": self.parameters,
            "parameters_hash": sha256_canonical(self.parameters),
            "seed": self.seed,
            "rng_policy": self.rng_policy,
            "environment_hash": self.environment_hash,
            "status": self.status,
            "start_time_utc": self.start_time_utc,
            "end_time_utc": self.end_time_utc,
            "result_hash": self.result_hash,
            "failure_reason": self.failure_reason,
            "seen_results_before_change": self.seen_results_before_change,
        }

    def validate(self) -> None:
        if not self.experiment_id:
            raise ValueError("experiment_id_required")

        if not self.specification_id:
            raise ValueError("specification_id_required")

        if not self.source_hash:
            raise ValueError("source_hash_required")

        if not self.code_commit:
            raise ValueError("code_commit_required")

        if self.status not in VALID_STATUSES:
            raise ValueError(
                f"invalid_status:{self.status}"
            )

        if not self.rng_policy:
            raise ValueError("rng_policy_required")

        if not self.environment_hash:
            raise ValueError("environment_hash_required")

        if not self.start_time_utc:
            raise ValueError("start_time_utc_required")

        if self.status == "PASS" and not self.result_hash:
            raise ValueError("pass_requires_result_hash")

        if self.status in FAILURE_STATUSES and not self.failure_reason:
            raise ValueError(
                f"failure_status_requires_reason:{self.status}"
            )

        if (
            self.seen_results_before_change
            and self.parent_experiment_id is None
        ):
            raise ValueError(
                "result_seen_before_change_requires_parent"
            )


class AppendOnlyExperimentLedger:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def _read_records(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []

        records: list[dict[str, Any]] = []

        with self.path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()

                if not stripped:
                    continue

                try:
                    value = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"invalid_json_line:{line_number}"
                    ) from exc

                if not isinstance(value, dict):
                    raise ValueError(
                        f"ledger_record_not_object:{line_number}"
                    )

                records.append(value)

        return records

    def experiment_ids(self) -> set[str]:
        return {
            str(record["experiment_id"])
            for record in self._read_records()
            if "experiment_id" in record
        }

    def contains(self, experiment_id: str) -> bool:
        return experiment_id in self.experiment_ids()

    def append(self, record: ExperimentRecord) -> None:
        record.validate()

        if self.contains(record.experiment_id):
            raise ValueError(
                f"duplicate_experiment_id:{record.experiment_id}"
            )

        self.path.parent.mkdir(parents=True, exist_ok=True)

        with self.path.open(
            "a",
            encoding="utf-8",
            newline="\n",
        ) as handle:
            handle.write(
                canonical_json(record.to_dict())
                + "\n"
            )

    def verify_integrity(self) -> dict[str, Any]:
        records = self._read_records()
        ids = [r.get("experiment_id") for r in records]

        duplicate_ids = sorted(
            {
                x
                for x in ids
                if x is not None and ids.count(x) > 1
            }
        )

        return {
            "record_count": len(records),
            "unique_experiment_count": len(set(ids)),
            "duplicate_experiment_ids": duplicate_ids,
            "append_only_readable": True,
            "valid": not duplicate_ids,
        }


def make_experiment_id(
    specification_id: str,
    source_hash: str,
    code_commit: str,
    parameters: dict[str, Any],
    seed: int | None,
) -> str:
    payload = {
        "specification_id": specification_id,
        "source_hash": source_hash,
        "code_commit": code_commit,
        "parameters": parameters,
        "seed": seed,
    }

    return (
        "EXP-"
        + sha256_canonical(payload)[:24]
    )


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
