from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path.cwd()
REPORT = REPO / "artifacts/control_plane_v0.1/representation_adjudication.json"

CURRENT_B = REPO / "APEX44/03-computation/output/B_real_6236x1642.npz"
DRS = REPO / "APEX44/04-evaluation/DRS_real_data.json"
QAC_LOCAL = REPO / "PHASE2_CLEAN/source/quranic-corpus-morphology-0.4.txt"

TARGET_DIMENSIONS = "128220x80"


def run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None

    digest = hashlib.sha256()

    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)

    return digest.hexdigest()


def file_timestamp(path: Path) -> str | None:
    if not path.exists():
        return None

    return datetime.fromtimestamp(
        path.stat().st_mtime,
        tz=timezone.utc,
    ).isoformat()


def dimensions(path: Path) -> list[int] | None:
    if not path.is_file():
        return None

    try:
        import numpy as np
    except Exception:
        return None

    try:
        with np.load(path, allow_pickle=False) as data:
            if "shape" in data.files:
                value = data["shape"]
                return [int(x) for x in value.tolist()]

            for key in data.files:
                obj = data[key]
                if hasattr(obj, "shape") and len(obj.shape) == 2:
                    return [int(obj.shape[0]), int(obj.shape[1])]
    except Exception:
        return None

    return None


def load_json(path: Path) -> Any:
    if not path.is_file():
        return None

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def git_file_history(path: str) -> list[dict[str, str]]:
    output = run_git(
        "log",
        "--all",
        "--date=iso-strict",
        "--format=%H%x09%aI%x09%s",
        "--",
        path,
    )

    records: list[dict[str, str]] = []

    if not output:
        return records

    for line in output.splitlines():
        parts = line.split("\t", 2)

        if len(parts) != 3:
            continue

        records.append(
            {
                "commit": parts[0],
                "timestamp": parts[1],
                "subject": parts[2],
            }
        )

    return records


def current_branch() -> str:
    return run_git("branch", "--show-current")


def current_commit() -> str:
    return run_git("rev-parse", "HEAD")


def path_exists_in_head(path: str) -> bool:
    result = subprocess.run(
        ["git", "cat-file", "-e", f"HEAD:{path}"],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return result.returncode == 0


def search_git_history(pattern: str) -> list[str]:
    refs = run_git(
        "for-each-ref",
        "--format=%(refname)",
        "refs/heads",
        "refs/remotes",
        "refs/tags",
    ).splitlines()

    if not refs:
        return []

    result = subprocess.run(
        [
            "git",
            "grep",
            "-n",
            "-E",
            pattern,
            *refs,
            "--",
        ],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    lines = result.stdout.splitlines()

    return lines[:500]


def search_local_files(pattern: str) -> list[str]:
    result = subprocess.run(
        [
            "grep",
            "-RInE",
            "--exclude-dir=.git",
            "--exclude='*.pyc'",
            pattern,
            "APEX44",
            "docs",
            "tests",
            "scripts",
        ],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    return result.stdout.splitlines()[:500]


def find_candidate_files() -> list[str]:
    candidates: set[str] = set()

    roots = [
        REPO / "APEX44",
        REPO / "artifacts",
        REPO / "docs",
        REPO / "tests",
        REPO / "scripts",
        REPO / "PHASE2_CLEAN",
    ]

    patterns = (
        "*128220*",
        "*80*concept*",
        "*80_concept*",
        "*6236x1642*",
        "*B_real*",
        "*representation*",
        "*phase2*",
        "*Phase2*",
    )

    for root in roots:
        if not root.exists():
            continue

        for pattern in patterns:
            for path in root.rglob(pattern):
                if path.is_file():
                    candidates.add(path.relative_to(REPO).as_posix())

    return sorted(candidates)


def classify_current_b(
    path: Path,
    drs_data: Any,
) -> str:
    if not path.is_file():
        return "UNVERIFIED"

    if isinstance(drs_data, dict):
        b_real = drs_data.get("B_real")

        if isinstance(b_real, dict):
            expected_file = b_real.get("file")

            if expected_file == path.relative_to(REPO).as_posix():
                return "CANONICAL_CURRENT"

    return "UNVERIFIED"


def main() -> None:
    report: dict[str, Any] = {
        "schema": "scientific-inference-control-plane-representation-adjudication-v0.1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repository": "agad70696-coder/apex44-zero",
        "branch": current_branch(),
        "commit": current_commit(),
        "labels": [
            "CANONICAL_CURRENT",
            "CANONICAL_TARGET",
            "HISTORICAL",
            "UNVERIFIED",
            "CONFLICT",
        ],
        "items": [],
        "representation_conflicts": [],
        "search": {},
    }

    drs_data = load_json(DRS)

    if CURRENT_B.exists():
        current_item: dict[str, Any] = {
            "path": CURRENT_B.relative_to(REPO).as_posix(),
            "status": classify_current_b(CURRENT_B, drs_data),
            "sha256": sha256_file(CURRENT_B),
            "git_blob_sha1": run_git("hash-object", str(CURRENT_B)),
            "commit": current_commit(),
            "dimensions": dimensions(CURRENT_B),
            "source": None,
            "producer": None,
            "timestamp": file_timestamp(CURRENT_B),
            "in_head": path_exists_in_head(
                CURRENT_B.relative_to(REPO).as_posix()
            ),
        }

        if isinstance(drs_data, dict):
            source = drs_data.get("source")

            if isinstance(source, dict):
                current_item["source"] = source

            b_real = drs_data.get("B_real")

            if isinstance(b_real, dict):
                current_item["producer"] = {
                    key: b_real.get(key)
                    for key in (
                        "producer",
                        "method",
                        "script",
                        "source",
                        "shape",
                        "nnz",
                        "density",
                    )
                    if key in b_real
                }

                expected_shape = b_real.get("shape")

                if (
                    expected_shape is not None
                    and current_item["dimensions"] is not None
                    and list(expected_shape)
                    != current_item["dimensions"]
                ):
                    current_item["status"] = "CONFLICT"

                    report["representation_conflicts"].append(
                        {
                            "type": "CURRENT_B_SHAPE_MISMATCH",
                            "path": current_item["path"],
                            "metadata_shape": expected_shape,
                            "actual_shape": current_item["dimensions"],
                        }
                    )

        report["items"].append(current_item)
    else:
        report["items"].append(
            {
                "path": "APEX44/03-computation/output/B_real_6236x1642.npz",
                "status": "UNVERIFIED",
                "reason": "FILE_NOT_FOUND",
            }
        )

    qac_item: dict[str, Any] = {
        "path": QAC_LOCAL.relative_to(REPO).as_posix(),
        "status": "UNVERIFIED",
        "sha256": sha256_file(QAC_LOCAL),
        "git_blob_sha1": run_git("hash-object", str(QAC_LOCAL)),
        "commit_history": git_file_history(
            QAC_LOCAL.relative_to(REPO).as_posix()
        ),
        "timestamp": file_timestamp(QAC_LOCAL),
        "in_head": path_exists_in_head(
            QAC_LOCAL.relative_to(REPO).as_posix()
        ),
    }

    if isinstance(drs_data, dict):
        source = drs_data.get("source")

        if isinstance(source, dict):
            metadata_sha = source.get("sha256")
            metadata_lines = source.get("lines")
            metadata_size = source.get("size")

            qac_item["metadata_sha256"] = metadata_sha
            qac_item["metadata_lines"] = metadata_lines
            qac_item["metadata_size"] = metadata_size

            if metadata_sha == qac_item["sha256"]:
                qac_item["status"] = "VERIFIED"
            else:
                qac_item["status"] = "CONFLICT"

                report["representation_conflicts"].append(
                    {
                        "type": "QAC_SHA_MISMATCH",
                        "path": qac_item["path"],
                        "local_sha256": qac_item["sha256"],
                        "metadata_sha256": metadata_sha,
                        "metadata_sha256_length": (
                            len(metadata_sha)
                            if isinstance(metadata_sha, str)
                            else None
                        ),
                    }
                )

    report["items"].append(qac_item)

    candidate_paths = find_candidate_files()

    for candidate in candidate_paths:
        if candidate in {
            CURRENT_B.relative_to(REPO).as_posix(),
            QAC_LOCAL.relative_to(REPO).as_posix(),
        }:
            continue

        candidate_path = REPO / candidate

        history = git_file_history(candidate)

        item: dict[str, Any] = {
            "path": candidate,
            "status": "UNVERIFIED",
            "sha256": sha256_file(candidate_path),
            "git_blob_sha1": run_git("hash-object", candidate),
            "commit": current_commit(),
            "dimensions": dimensions(candidate_path),
            "source": None,
            "producer": None,
            "timestamp": file_timestamp(candidate_path),
            "in_head": path_exists_in_head(candidate),
            "history_count": len(history),
            "history": history[:20],
        }

        lower = candidate.lower()

        if (
            item["dimensions"] == [128220, 80]
            or "128220" in lower
            or "80_concept" in lower
            or "80concept" in lower
        ):
            item["status"] = "UNVERIFIED"

            if item["dimensions"] == [128220, 80]:
                item["status"] = "CANONICAL_TARGET"

        if history and item["status"] == "UNVERIFIED":
            item["status"] = "HISTORICAL"

        report["items"].append(item)

    report["search"] = {
        "git_128220_80": search_git_history(
            "128220|128220.?x.?80|80.?concept|80_concept"
        ),
        "git_phase2": search_git_history(
            "Phase.?2|PHASE2_CLEAN|phase2"
        ),
        "git_current_representation": search_git_history(
            "6236.?x.?1642|B_real"
        ),
        "local_128220_80": search_local_files(
            "128220|128220.?x.?80|80.?concept|80_concept"
        ),
        "local_phase2": search_local_files(
            "Phase.?2|PHASE2_CLEAN|phase2"
        ),
    }

    statuses = {item["status"] for item in report["items"]}

    target_mentions = (
        len(report["search"]["git_128220_80"])
        + len(report["search"]["local_128220_80"])
    )

    if target_mentions == 0:
        report["target_128220x80_status"] = "UNVERIFIED"
    else:
        report["target_128220x80_status"] = "UNVERIFIED"

    if "CONFLICT" in statuses or report["representation_conflicts"]:
        report["overall_status"] = "CONFLICT"
    elif any(
        item["status"] == "CANONICAL_CURRENT"
        for item in report["items"]
    ):
        report["overall_status"] = "CANONICAL_CURRENT"
    else:
        report["overall_status"] = "UNVERIFIED"

    REPORT.parent.mkdir(parents=True, exist_ok=True)

    REPORT.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    print("G2_REPORT=", REPORT)
    print("G2_OVERALL_STATUS=", report["overall_status"])
    print("TARGET_128220x80_STATUS=", report["target_128220x80_status"])

    print()
    print("ITEM_STATUSES")

    for item in report["items"]:
        print(
            item.get("status"),
            item.get("path"),
            item.get("dimensions"),
            item.get("sha256"),
            sep=" | ",
        )

    print()
    print("CONFLICT_COUNT=", len(report["representation_conflicts"]))

    for conflict in report["representation_conflicts"]:
        print(
            "CONFLICT",
            conflict.get("type"),
            conflict.get("path"),
            sep=" | ",
        )


if __name__ == "__main__":
    main()
