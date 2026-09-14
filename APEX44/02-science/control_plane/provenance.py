from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence
import hashlib
import json


SHA256_LENGTH = 64


@dataclass(frozen=True)
class ProvenanceRecord:
    artifact_id: str
    artifact_type: str
    content_sha256: str
    source_ids: tuple[str, ...]
    dependency_ids: tuple[str, ...]
    transformation: str
    role: str
    independence_group: str
    status: str

    def validate(self) -> None:
        if not self.artifact_id:
            raise ValueError("invalid_artifact_id")

        if len(self.content_sha256) != SHA256_LENGTH:
            raise ValueError("invalid_sha256_length")

        try:
            int(self.content_sha256, 16)
        except ValueError as exc:
            raise ValueError("invalid_sha256") from exc

        if len(set(self.source_ids)) != len(self.source_ids):
            raise ValueError("duplicate_source_ids")

        if len(set(self.dependency_ids)) != len(self.dependency_ids):
            raise ValueError("duplicate_dependency_ids")

        if not self.transformation:
            raise ValueError("missing_transformation")

        if not self.role:
            raise ValueError("missing_role")

        if not self.independence_group:
            raise ValueError("missing_independence_group")

        if not self.status:
            raise ValueError("missing_status")

    def as_dict(self) -> dict[str, object]:
        self.validate()
        return {
            "artifact_id": self.artifact_id,
            "artifact_type": self.artifact_type,
            "content_sha256": self.content_sha256,
            "source_ids": list(self.source_ids),
            "dependency_ids": list(self.dependency_ids),
            "transformation": self.transformation,
            "role": self.role,
            "independence_group": self.independence_group,
            "status": self.status,
        }


def canonical_json(value: Mapping[str, object]) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def record_hash(record: ProvenanceRecord) -> str:
    payload = canonical_json(record.as_dict()).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_graph(records: Sequence[ProvenanceRecord]) -> None:
    indexed = {}

    for record in records:
        record.validate()
        if record.artifact_id in indexed:
            raise ValueError("duplicate_artifact_id")
        indexed[record.artifact_id] = record

    for record in records:
        for dep in record.dependency_ids:
            if dep not in indexed:
                raise ValueError(
                    f"missing_dependency:{record.artifact_id}:{dep}"
                )

        for source in record.source_ids:
            if source not in indexed:
                raise ValueError(
                    f"missing_source:{record.artifact_id}:{source}"
                )

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node_id: str) -> None:
        if node_id in visiting:
            raise ValueError(f"provenance_cycle:{node_id}")
        if node_id in visited:
            return

        visiting.add(node_id)
        node = indexed[node_id]

        for dep in node.dependency_ids:
            visit(dep)

        for source in node.source_ids:
            visit(source)

        visiting.remove(node_id)
        visited.add(node_id)

    for node_id in indexed:
        visit(node_id)


def compare_declared_hash(
    expected_sha256: str,
    actual_sha256: str,
) -> bool:
    return (
        isinstance(expected_sha256, str)
        and isinstance(actual_sha256, str)
        and expected_sha256 == actual_sha256
        and len(actual_sha256) == SHA256_LENGTH
    )


def same_independence_group(
    left: ProvenanceRecord,
    right: ProvenanceRecord,
) -> bool:
    return left.independence_group == right.independence_group
