#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "config/self_maintenance_policy.json"


def classify(files: list[str]) -> str:
    text = " ".join(files).lower()

    critical = [
        "null_model",
        "bicm",
        "pvalue",
        "p_value",
        "backbone",
        "crypt",
        "observed",
        "biadj",
        "release_policy",
    ]

    high = [
        "dataset",
        "qac",
        "quran",
        "token",
        "normal",
        "statistics",
    ]

    if any(x in text for x in critical):
        return "CRITICAL"

    if any(x in text for x in high):
        return "HIGH"

    return "LOW"


def main() -> int:
    policy = json.loads(POLICY.read_text())

    files = sys.argv[1:]

    risk = classify(files)

    allowed = risk == "LOW"

    result = {
        "risk": risk,
        "files": files,
        "auto_fix_allowed": allowed,
        "human_review_required": risk in {"HIGH", "CRITICAL"},
        "policy_version": policy["version"],
    }

    print(json.dumps(result, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
