#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / "release/maintenance/baseline/all_sha256.txt"
OUT = ROOT / "release/maintenance/drift.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def current_files() -> dict[str, str]:
    result: dict[str, str] = {}

    for path in ROOT.rglob("*"):
        if (
            not path.is_file()
            or ".git" in path.parts
            or ".venv" in path.parts
            or path.is_relative_to(ROOT / "release/maintenance/baseline")
        ):
            continue

        rel = str(path.relative_to(ROOT))
        result[rel] = sha256(path)

    return result


def load_baseline() -> dict[str, str]:
    if not BASELINE.exists():
        return {}

    result = {}

    for line in BASELINE.read_text().splitlines():
        digest, path = line.split(maxsplit=1)
        result[path] = digest

    return result


def main() -> int:
    before = load_baseline()
    after = current_files()

    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    changed = sorted(
        p for p in set(before) & set(after)
        if before[p] != after[p]
    )

    report = {
        "added": added,
        "removed": removed,
        "changed": changed,
        "clean": not (added or removed or changed),
    }

    OUT.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(report, indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
