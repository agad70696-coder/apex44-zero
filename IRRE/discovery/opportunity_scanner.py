"""Collect opportunity checks and persist an auditable per-run snapshot."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import socket
import sys
from collections.abc import Mapping
from typing import Any

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class OpportunityScanner:
    """Run lightweight checks and persist their results without import-time side effects."""

    def __init__(self, output_dir: pathlib.Path | str = "data") -> None:
        self.output_dir = pathlib.Path(output_dir)

    def scan_rpc(self) -> dict[str, str]:
        """Check DNS resolution only; this does not establish RPC endpoint health."""
        try:
            socket.gethostbyname("polygon-amoy.drpc.org")
            return {"status": "PASS", "opportunity": "RPC hostname resolved via DNS"}
        except OSError as exc:
            return {"status": "FAIL", "opportunity": f"RPC hostname DNS lookup failed: {exc}"}

    def scan_jcs(self) -> dict[str, str]:
        try:
            from IRRE.ledger import jcs_canonical
            valid = jcs_canonical.is_jcs()
            return {"status": "PASS" if valid else "FAIL", "opportunity": "JCS check"}
        except Exception as exc:
            return {"status": "FAIL", "opportunity": f"JCS check error: {type(exc).__name__}: {exc}"}

    def scan_tla(self) -> dict[str, str]:
        """Check invariant names are present; this is not a TLC model-checker run."""
        spec_path = PROJECT_ROOT / "specs" / "evidence_chain.tla"
        if not spec_path.is_file():
            return {"status": "FAIL", "opportunity": "TLA+ specification missing"}
        try:
            text = spec_path.read_text(encoding="utf-8")
        except OSError as exc:
            return {"status": "FAIL", "opportunity": f"TLA+ specification unreadable: {exc}"}
        missing = [name for name in ("Inv_Crypto", "Inv_Linkage") if name not in text]
        if missing:
            return {"status": "FAIL", "opportunity": f"TLA+ invariant names missing: {', '.join(missing)}"}
        return {"status": "PASS", "opportunity": "TLA+ invariant names present (static check only)"}

    def scan_nist(self) -> dict[str, str]:
        today = dt.datetime.now(dt.timezone.utc).date()
        days = (dt.date(2030, 12, 31) - today).days
        return {"status": "OPPORTUNITY", "opportunity": f"{days} days until 2030-12-31 review date"}

    @staticmethod
    def _timestamp() -> str:
        return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    def write_outputs(
        self, results: Mapping[str, Mapping[str, Any]], observed_at: str | None = None
    ) -> tuple[pathlib.Path, pathlib.Path]:
        """Write a JSONL snapshot and a matching Markdown report."""
        timestamp = observed_at or self._timestamp()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        records = [
            {
                "observed_at": timestamp,
                "check": str(name),
                "status": str(result.get("status", "UNKNOWN")),
                "opportunity": str(result.get("opportunity", "No detail supplied")),
            }
            for name, result in results.items()
        ]
        ledger_path = self.output_dir / "opportunity_ledger.jsonl"
        report_path = self.output_dir / "opportunity_report.md"

        ledger_tmp = ledger_path.with_suffix(ledger_path.suffix + ".tmp")
        ledger_tmp.write_text(
            "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in records),
            encoding="utf-8",
        )
        ledger_tmp.replace(ledger_path)

        counts: dict[str, int] = {}
        for row in records:
            counts[row["status"]] = counts.get(row["status"], 0) + 1
        lines = [
            "# Opportunity Scan Report",
            "",
            f"- Observed at (UTC): `{timestamp}`",
            f"- Checks recorded: **{len(records)}**",
            "- Status counts: " + (", ".join(f"`{key}`: {value}" for key, value in sorted(counts.items())) or "none"),
            "",
            "## Findings",
            "",
            "| Check | Status | Finding |",
            "| --- | --- | --- |",
        ]
        for row in records:
            detail = row["opportunity"].replace("|", "\\|").replace("\n", " ")
            lines.append(f"| `{row['check']}` | **{row['status']}** | {detail} |")
        lines.extend([
            "",
            "> PASS applies only to the named check. DNS resolution is not an RPC request; "
            "the TLA+ check is static and is not a TLC model-checker run.",
            "",
        ])
        report_tmp = report_path.with_suffix(report_path.suffix + ".tmp")
        report_tmp.write_text("\n".join(lines), encoding="utf-8")
        report_tmp.replace(report_path)
        return ledger_path, report_path

    def run(self) -> dict[str, dict[str, str]]:
        results = {
            "rpc": self.scan_rpc(),
            "jcs": self.scan_jcs(),
            "tla": self.scan_tla(),
            "nist": self.scan_nist(),
        }
        ledger, report = self.write_outputs(results)
        print(json.dumps(results, ensure_ascii=False, sort_keys=True))
        print(f"Wrote scan ledger: {ledger}")
        print(f"Wrote scan report: {report}")
        return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="data", help="Directory for scan output files")
    args = parser.parse_args()
    OpportunityScanner(output_dir=args.output_dir).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
