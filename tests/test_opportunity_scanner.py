"""Regression tests for opportunity scanner outputs and typed check outcomes."""
import json

import pytest
from pathlib import Path
from IRRE.discovery.opportunity_scanner import OpportunityScanner

EXPECTED_SCAN_COUNT = 3


class SyntheticDNSFailure(OSError):
    """Stable test failure with the expected user-facing message."""

    def __init__(self) -> None:
        super().__init__("synthetic DNS failure")


def test_write_outputs_creates_valid_jsonl_and_report(tmp_path: Path) -> None:
    scanner = OpportunityScanner(output_dir=tmp_path)
    results = {
        "rpc": {"status": "PASS", "opportunity": "DNS resolution succeeded"},
        "jcs": {"status": "FAIL", "opportunity": "JCS marker missing"},
        "nist": {"status": "OPPORTUNITY", "opportunity": "Review date approaching"},
    }
    ledger, report = scanner.write_outputs(results, observed_at="2026-10-11T00:00:00Z")
    rows = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == EXPECTED_SCAN_COUNT
    assert {row["check"] for row in rows} == {"rpc", "jcs", "nist"}
    assert all(row["observed_at"] == "2026-10-11T00:00:00Z" for row in rows)
    assert [row["status"] for row in rows if row["check"] == "jcs"] == ["FAIL"]
    body = report.read_text(encoding="utf-8")
    assert "Checks recorded: **3**" in body
    assert "`FAIL`: 1" in body
    assert "JCS marker missing" in body


def test_write_outputs_replaces_snapshot_without_duplicate_rows(tmp_path: Path) -> None:
    scanner = OpportunityScanner(output_dir=tmp_path)
    scanner.write_outputs({"old": {"status": "PASS", "opportunity": "old"}}, "t1")
    ledger, _ = scanner.write_outputs({"new": {"status": "FAIL", "opportunity": "new"}}, "t2")
    rows = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 1
    assert rows[0]["check"] == "new"
    assert rows[0]["observed_at"] == "t2"


def test_scan_rpc_returns_typed_status_without_network(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "IRRE.discovery.opportunity_scanner.socket.gethostbyname",
        lambda _host: "192.0.2.1",
    )
    assert OpportunityScanner().scan_rpc() == {
        "status": "PASS",
        "opportunity": "RPC hostname resolved via DNS",
    }


def test_scan_rpc_failure_is_not_promoted_to_pass(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_lookup(_host: str) -> str:
        raise SyntheticDNSFailure()
    monkeypatch.setattr("IRRE.discovery.opportunity_scanner.socket.gethostbyname", fail_lookup)
    result = OpportunityScanner().scan_rpc()
    assert result["status"] == "FAIL"
    assert "synthetic DNS failure" in result["opportunity"]
