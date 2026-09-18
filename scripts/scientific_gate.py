#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "schemas" / "scientific_release_policy.json"
REPORT = ROOT / "release" / "reports" / "scientific_gate_report.json"


class GateFailure(Exception):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise GateFailure(f"MISSING: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise GateFailure(f"INVALID_JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise GateFailure(f"JSON_OBJECT_REQUIRED: {path}")
    return value


def git_head() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def run() -> int:
    policy = load_json(POLICY)

    results: list[dict[str, Any]] = []

    def record(gate: str, passed: bool, detail: str) -> None:
        results.append(
            {
                "gate": gate,
                "status": "PASS" if passed else "FAIL",
                "detail": detail,
            }
        )

    # G0
    try:
        git = git_head()
        if not git:
            raise GateFailure("empty git HEAD")
        record("G0", True, f"git_head={git}")
    except Exception as exc:
        record("G0", False, str(exc))

    # G1
    try:
        audit_path = ROOT / "APEX44/00-governance/audit_trail.json"
        audit = load_json(audit_path)

        required = [
            "biadj_hash",
            "n_rows",
            "n_cols",
            "E",
            "seed",
            "R",
        ]

        missing = [key for key in required if key not in audit]
        if missing:
            raise GateFailure(f"missing audit keys: {missing}")

        record("G1", True, "audit schema present")
    except Exception as exc:
        record("G1", False, str(exc))

    # G2
    try:
        matrix = ROOT / "APEX44/00-governance/biadj.npy"
        if not matrix.exists():
            raise GateFailure(f"missing matrix: {matrix}")

        import numpy as np

        b = np.load(matrix, allow_pickle=False)

        if b.ndim != 2:
            raise GateFailure(f"matrix ndim={b.ndim}, expected 2")

        if not np.isin(b, [0, 1]).all():
            raise GateFailure("matrix is not binary")

        record("G2", True, f"shape={b.shape}, edges={int(b.sum())}")
    except Exception as exc:
        record("G2", False, str(exc))

    # G3
    try:
        audit = load_json(ROOT / "APEX44/00-governance/audit_trail.json")

        err = audit.get("err_final")

        if not finite(err):
            raise GateFailure("err_final missing or non-finite")

        if float(err) > 1e-8:
            raise GateFailure(f"err_final={err} > 1e-8")

        record("G3", True, f"err_final={err}")
    except Exception as exc:
        record("G3", False, str(exc))

    # G4
    try:
        audit = load_json(ROOT / "APEX44/00-governance/audit_trail.json")

        declared_r = int(audit["R"])
        required_r = int(policy["null_ensemble"]["R"])

        if declared_r != required_r:
            raise GateFailure(
                f"declared R={declared_r}, required R={required_r}"
            )

        # Must have an explicit executed-R field.
        executed_r = audit.get("executed_R")
        if executed_r is None:
            raise GateFailure("executed_R missing")

        if int(executed_r) != required_r:
            raise GateFailure(
                f"executed R={executed_r}, required R={required_r}"
            )

        record("G4", True, f"R={required_r}")
    except Exception as exc:
        record("G4", False, str(exc))

    # G5
    try:
        pvalues_path = ROOT / "APEX44/00-governance/pvalues.json"
        pvalues = load_json(pvalues_path)

        values = pvalues.get("p_values")
        if not isinstance(values, list) or not values:
            raise GateFailure("p_values missing or empty")

        for p in values:
            if not finite(p) or not 0.0 <= float(p) <= 1.0:
                raise GateFailure(f"invalid p-value: {p}")

        if "holm" not in pvalues or "bh" not in pvalues:
            raise GateFailure("missing multiple-testing results")

        record("G5", True, f"n_pvalues={len(values)}")
    except Exception as exc:
        record("G5", False, str(exc))

    # G6
    try:
        backbone = ROOT / "APEX44/00-governance/validated_backbone.json"
        data = load_json(backbone)

        if "backbone_edges" not in data:
            raise GateFailure("backbone_edges missing")

        record(
            "G6",
            True,
            f"backbone_edges={data['backbone_edges']}",
        )
    except Exception as exc:
        record("G6", False, str(exc))

    # G7
    try:
        reproduction = ROOT / "release/manifests/reproduction.json"
        data = load_json(reproduction)

        if data.get("identical") is not True:
            raise GateFailure("reproduction identical != true")

        if not data.get("run_a_hash") or not data.get("run_b_hash"):
            raise GateFailure("missing reproduction hashes")

        record("G7", True, "dual reproduction recorded")
    except Exception as exc:
        record("G7", False, str(exc))

    # G8
    try:
        manifest = ROOT / "release/manifests/analysis_manifest.json"
        data = load_json(manifest)

        files = data.get("files")
        if not isinstance(files, list) or not files:
            raise GateFailure("manifest files missing")

        mismatches = []
        for entry in files:
            path = ROOT / entry["path"]
            expected = entry["sha256"]
            actual = sha256_file(path)
            if actual != expected:
                mismatches.append(
                    f"{entry['path']}: {actual} != {expected}"
                )

        if mismatches:
            raise GateFailure("; ".join(mismatches))

        record("G8", True, f"manifested_files={len(files)}")
    except Exception as exc:
        record("G8", False, str(exc))

    # G9
    try:
        if os.getenv("GITHUB_ACTIONS") != "true":
            raise GateFailure("not running under GitHub Actions")

        sha = os.getenv("GITHUB_SHA")
        if not sha:
            raise GateFailure("GITHUB_SHA missing")

        record("G9", True, f"github_sha={sha}")
    except Exception as exc:
        record("G9", False, str(exc))

    passed = all(item["status"] == "PASS" for item in results)

    report = {
        "protocol": policy["protocol"],
        "policy_version": policy["version"],
        "git_head": git_head(),
        "decision": "PASS" if passed else "FAIL",
        "fail_closed": True,
        "gates": results,
    }

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    for item in results:
        print(f"{item['gate']} {item['status']} — {item['detail']}")

    print(f"FINAL DECISION: {report['decision']}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(run())
