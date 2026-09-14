from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path.cwd()
REPORT = REPO / "artifacts/control_plane_v0.1/representation_adjudication.json"

CURRENT_B = REPO / "APEX44/03-computation/output/B_real_6236x1642.npz"
DRS = REPO / "APEX44/04-evaluation/DRS_real_data.json"
QAC = REPO / "PHASE2_CLEAN/source/quranic-corpus-morphology-0.4.txt"


def git(*args: str) -> str:
    r = subprocess.run(
        ["git", *args],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return r.stdout.strip() if r.returncode == 0 else ""


def sha256(path: Path) -> str | None:
    if not path.is_file():
        return None

    h = hashlib.sha256()

    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)

    return h.hexdigest()


def file_info(path: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(REPO).as_posix(),
        "sha256": sha256(path),
        "bytes": path.stat().st_size if path.exists() else None,
        "timestamp_utc": (
            datetime.fromtimestamp(
                path.stat().st_mtime,
                tz=timezone.utc,
            ).isoformat()
            if path.exists()
            else None
        ),
        "in_head": (
            subprocess.run(
                ["git", "cat-file", "-e",
                 f"HEAD:{path.relative_to(REPO).as_posix()}"],
                cwd=REPO,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            ).returncode
            == 0
        ),
    }


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def npz_shape(path: Path) -> list[int] | None:
    if not path.is_file():
        return None

    try:
        import numpy as np
        with np.load(path, allow_pickle=False) as z:
            if "shape" in z.files:
                return [int(x) for x in z["shape"].tolist()]
    except Exception:
        return None

    return None


def search_refs(pattern: str) -> list[str]:
    refs = git(
        "for-each-ref",
        "--format=%(refname)",
        "refs/heads",
        "refs/remotes",
        "refs/tags",
    ).splitlines()

    if not refs:
        return []

    r = subprocess.run(
        ["git", "grep", "-n", "-E", pattern, *refs, "--"],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    return r.stdout.splitlines()[:500]


def main() -> None:
    drs = load_json(DRS)
    source = drs.get("source", {})
    bmeta = drs.get("B_real", {})

    local_qac_sha = sha256(QAC)
    metadata_qac_sha = source.get("sha256")

    qac_conflict = (
        local_qac_sha is not None
        and metadata_qac_sha != local_qac_sha
    )

    b_item = file_info(CURRENT_B)
    b_item["dimensions"] = npz_shape(CURRENT_B)
    b_item["status"] = "UNVERIFIED"

    if (
        CURRENT_B.is_file()
        and bmeta.get("file") == b_item["path"]
        and bmeta.get("shape") == b_item["dimensions"]
    ):
        b_item["status"] = "CANONICAL_CURRENT"

    if (
        isinstance(bmeta.get("sha16"), str)
        and b_item["sha256"]
        and bmeta["sha16"] == b_item["sha256"][: len(bmeta["sha16"])]
    ):
        b_item["sha16_status"] = "EXACT_PREFIX_MATCH"
    else:
        b_item["sha16_status"] = "UNVERIFIED"

    qac_item = file_info(QAC)
    qac_item.update(
        {
            "status": "CONFLICT" if qac_conflict else "VERIFIED",
            "metadata_sha256": metadata_qac_sha,
            "metadata_sha256_length": (
                len(metadata_qac_sha)
                if isinstance(metadata_qac_sha, str)
                else None
            ),
            "metadata_lines": source.get("lines"),
            "metadata_size": source.get("size"),
            "local_lines": (
                sum(1 for _ in QAC.open("rb"))
                if QAC.is_file()
                else None
            ),
            "metadata_content_size_matches": (
                str(QAC.stat().st_size) == str(source.get("size"))
                if QAC.is_file()
                else False
            ),
        }
    )

    target_search = (
        search_refs("128220|128220.?x.?80|80.?concept|80_concept")
    )

    current_search = search_refs("6236.?x.?1642|B_real")

    report = {
        "schema": "scientific-inference-control-plane-representation-adjudication-v0.1-r2",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repository": "agad70696-coder/apex44-zero",
        "branch": git("branch", "--show-current"),
        "commit": git("rev-parse", "HEAD"),
        "labels": [
            "CANONICAL_CURRENT",
            "CANONICAL_TARGET",
            "HISTORICAL",
            "UNVERIFIED",
            "CONFLICT",
        ],
        "current_representation": b_item,
        "qac_source": qac_item,
        "drs_source_metadata": source,
        "drs_b_real_metadata": bmeta,
        "target_128220x80": {
            "status": "UNVERIFIED",
            "evidence_count": len(target_search),
            "git_reference_matches": target_search,
        },
        "current_representation_references": current_search[:200],
        "runtime_exclusions": [
            "__pycache__",
            "*.pyc",
            "*.bak",
            "g2_execution.log",
        ],
        "scientific_verdict": {
            "current_representation": (
                "CANONICAL_CURRENT"
                if b_item["status"] == "CANONICAL_CURRENT"
                else "UNVERIFIED"
            ),
            "target_128220x80": "UNVERIFIED",
            "qac_provenance": (
                "CONFLICT" if qac_conflict else "VERIFIED"
            ),
            "overall": (
                "CONFLICT"
                if qac_conflict
                else (
                    "CANONICAL_CURRENT"
                    if b_item["status"] == "CANONICAL_CURRENT"
                    else "UNVERIFIED"
                )
            ),
        },
        "conflicts": [],
    }

    if qac_conflict:
        report["conflicts"].append(
            {
                "type": "QAC_METADATA_SHA_CONFLICT",
                "source_path": qac_item["path"],
                "local_sha256": local_qac_sha,
                "metadata_sha256": metadata_qac_sha,
                "local_sha256_length": (
                    len(local_qac_sha)
                    if local_qac_sha
                    else None
                ),
                "metadata_sha256_length": (
                    len(metadata_qac_sha)
                    if isinstance(metadata_qac_sha, str)
                    else None
                ),
                "content_size_match": (
                    qac_item["metadata_content_size_matches"]
                ),
                "line_count_match": (
                    qac_item["metadata_lines"]
                    == qac_item["local_lines"]
                ),
                "action": "PRESERVE_AND_BLOCK_PROMOTION",
            }
        )

    REPORT.write_text(
        json.dumps(
            report,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    print("G2.3_REPORT=", REPORT)
    print("CURRENT_STATUS=", report["scientific_verdict"]["current_representation"])
    print("TARGET_128220x80_STATUS=", report["scientific_verdict"]["target_128220x80"])
    print("QAC_PROVENANCE_STATUS=", report["scientific_verdict"]["qac_provenance"])
    print("OVERALL_STATUS=", report["scientific_verdict"]["overall"])
    print("CONFLICT_COUNT=", len(report["conflicts"]))


if __name__ == "__main__":
    main()
