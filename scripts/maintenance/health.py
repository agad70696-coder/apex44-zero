#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "release/maintenance/health.json"


def run(cmd: list[str]) -> tuple[int, str]:
    p = subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return p.returncode, p.stdout.strip()


def main() -> int:
    sha_rc, sha = run(["git", "rev-parse", "HEAD"])
    status_rc, status = run(["git", "status", "--porcelain"])
    branch_rc, branch = run(["git", "branch", "--show-current"])

    data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "commit": sha if sha_rc == 0 else None,
        "branch": branch if branch_rc == 0 else None,
        "working_tree_clean": status_rc == 0 and status == "",
        "git_status": status.splitlines(),
        "python": sys.version,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(data, indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
