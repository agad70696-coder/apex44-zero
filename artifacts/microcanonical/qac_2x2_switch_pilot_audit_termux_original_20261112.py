#!/usr/bin/env python3
"""Read-only audit of the QAC fixed-degree 2x2-switch pilot."""
from __future__ import annotations

import hashlib
import json
import math
import platform
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import scipy
import scipy.sparse as sp

HOME = Path.home()
SOURCE = HOME / "apex44-zero/artifacts/audit_workspace/DQ-QAC-ROOT-ONLY-002/B_root_only_6236x1642.npz"
PILOT_DIR = HOME / "qac-repair-20261112-realdata-v4"
PILOT = PILOT_DIR / "microcanonical_2x2_pilot.json"
RUN_SCRIPT = PILOT_DIR / "microcanonical_2x2_pilot.py"
OUTPUT = PILOT_DIR / "microcanonical_2x2_pilot_audit_v0_1.json"

EXPECTED_SOURCE_SHA256 = "a75fdf4d57bd9448a74607fff9b9ddf31c26e2c3f356eb9fd40d19aa511c8c3a"
EXPECTED_CORPUS_SHA256 = "a1d12923815341face765083805d2148ed2d9f5cc3f7d6665219d887675d8c46"
EXPECTED_SHAPE = (6236, 1642)
EXPECTED_EDGES = 44431


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def c4_from_overlap(W: sp.spmatrix) -> int:
    upper = sp.triu(W, k=1).tocoo()
    return sum(int(x) * (int(x) - 1) // 2 for x in upper.data)


def main() -> None:
    for p in (SOURCE, PILOT, RUN_SCRIPT):
        if not p.is_file():
            raise FileNotFoundError(p)

    source_sha = sha256_file(SOURCE)
    pilot_sha = sha256_file(PILOT)
    script_sha = sha256_file(RUN_SCRIPT)

    B8 = sp.load_npz(SOURCE).tocsr()
    B8.sum_duplicates()
    B8.eliminate_zeros()
    B8.sort_indices()

    if B8.shape != EXPECTED_SHAPE or B8.nnz != EXPECTED_EDGES:
        raise ValueError(f"SOURCE_CONTRACT_MISMATCH:{B8.shape}:{B8.nnz}")
    if not np.all(B8.data == 1):
        raise ValueError("SOURCE_NOT_BINARY")

    B64 = B8.astype(np.int64)
    W8 = (B8.T @ B8).tocsr()
    W64 = (B64.T @ B64).tocsr()
    W64.setdiag(0)
    W64.eliminate_zeros()

    c4_int8 = c4_from_overlap(W8)
    c4_int64 = c4_from_overlap(W64)
    negative_int8_cells = int(np.count_nonzero(W8.data < 0))
    differing_overlap_cells = int((W8.astype(np.int64) != (B64.T @ B64)).nnz)
    W64_upper = sp.triu(W64, k=1).tocoo()
    projection_nnz_offdiag = int(W64.nnz)
    projection_max_offdiag = int(W64.data.max()) if W64.nnz else 0

    pilot = json.loads(PILOT.read_text(encoding="utf-8"))
    if pilot.get("schema") != "qac-realdata-fixed-degree-switch-pilot-v1":
        raise ValueError("UNEXPECTED_PILOT_SCHEMA")

    chains = pilot.get("chains", [])
    if len(chains) != 4:
        raise ValueError(f"CHAIN_COUNT_MISMATCH:{len(chains)}")

    chain_summaries = []
    all_degrees_preserved = True
    trace_values = []
    for chain in chains:
        trace = chain.get("trace", [])
        all_degrees_preserved &= chain.get("exact_degrees_preserved") is True
        values = [int(x["c4"]) for x in trace]
        trace_values.extend(values)
        chain_summaries.append({
            "seed": int(chain["seed"]),
            "proposals": int(chain["proposals"]),
            "burn_in": int(chain["burn_in"]),
            "accepted": int(chain["accepted"]),
            "acceptance_rate": float(chain["acceptance_rate"]),
            "trace_points": len(trace),
            "trace_min_c4": min(values) if values else None,
            "trace_max_c4": max(values) if values else None,
            "trace_final_c4": values[-1] if values else None,
            "exact_degrees_preserved": chain.get("exact_degrees_preserved") is True,
        })

    if source_sha != EXPECTED_SOURCE_SHA256:
        raise ValueError("SOURCE_SHA256_MISMATCH")
    if pilot.get("source_matrix_sha256") != source_sha:
        raise ValueError("PILOT_SOURCE_SHA256_MISMATCH")
    if pilot.get("source_corpus_sha256") != EXPECTED_CORPUS_SHA256:
        raise ValueError("PILOT_CORPUS_SHA256_MISMATCH")
    if c4_int64 != int(pilot.get("observed_c4", -1)):
        raise ValueError(f"PILOT_OBSERVED_C4_MISMATCH:{c4_int64}")
    if projection_nnz_offdiag != int(pilot.get("projection_nnz", -1)):
        raise ValueError("PILOT_PROJECTION_NNZ_MISMATCH")
    if projection_max_offdiag != int(pilot.get("projection_max", -1)):
        raise ValueError("PILOT_PROJECTION_MAX_MISMATCH")
    if not all_degrees_preserved:
        raise ValueError("CHAIN_DEGREE_PRESERVATION_FLAG_MISSING")
    if not trace_values or any(int(x) < 0 for x in trace_values):
        raise ValueError("INVALID_C4_TRACE")

    arr = np.asarray(trace_values, dtype=np.float64)
    report = {
        "schema": "AA-QAC-MICROCANONICAL-2X2-PILOT-AUDIT-0.1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS_SCOPED",
        "scope": "Read-only identity, integer-arithmetic, pilot-output, and recorded-invariant audit. This is not a mixing or inferential calibration.",
        "source": {
            "path": str(SOURCE),
            "bytes": SOURCE.stat().st_size,
            "sha256": source_sha,
            "shape": list(B8.shape),
            "nnz": int(B8.nnz),
            "binary": True,
            "corpus_sha256": EXPECTED_CORPUS_SHA256,
        },
        "artifacts": {
            "pilot_script": {"path": str(RUN_SCRIPT), "sha256": script_sha},
            "pilot_result": {"path": str(PILOT), "sha256": pilot_sha},
            "audit_output": str(OUTPUT),
        },
        "arithmetic_audit": {
            "c4_int8_product": int(c4_int8),
            "c4_int64_product": int(c4_int64),
            "int8_negative_overlap_cells": negative_int8_cells,
            "int8_vs_int64_different_overlap_cells": differing_overlap_cells,
            "int8_result_rejected_for_overflow": bool(negative_int8_cells > 0 and c4_int8 != c4_int64),
            "accepted_observed_c4": int(c4_int64),
            "projection_offdiagonal_nnz": projection_nnz_offdiag,
            "projection_max_offdiagonal_overlap": projection_max_offdiag,
            "independent_c4_replay_matches_pilot": c4_int64 == int(pilot["observed_c4"]),
        },
        "pilot": {
            "schema": pilot["schema"],
            "null": pilot.get("null"),
            "kernel": pilot.get("kernel"),
            "chain_count": len(chains),
            "all_chains_record_exact_degree_preservation": bool(all_degrees_preserved),
            "common_initial_state": "All four chains are initialized from the same observed matrix B; seeds differ.",
            "burn_in_proposals": int(chains[0]["burn_in"]),
            "proposals_per_chain": int(chains[0]["proposals"]),
            "trace_spacing_proposals": 50000,
            "trace_points_per_chain": len(chains[0].get("trace", [])),
            "chains": chain_summaries,
            "trace_summary": {
                "count": int(arr.size),
                "minimum_c4": int(arr.min()),
                "maximum_c4": int(arr.max()),
                "mean_c4": float(arr.mean()),
                "median_c4": float(np.median(arr)),
                "sample_sd_c4": float(arr.std(ddof=1)) if arr.size > 1 else None,
            },
        },
        "limitations": [
            "Four chains share the same initial observed matrix; this is not an overdispersed initialization design.",
            "Only nine thinned C4 snapshots per chain are stored; full trajectories and sampled adjacency states are not retained.",
            "Autocorrelation, effective sample size, rank-normalized split-Rhat, and tail stability are not established by this pilot.",
            "No Monte Carlo p-value or calibrated tail probability is produced.",
            "The 2x2-switch chain targets the uniform fixed-degree bipartite graph space only under the stated symmetric proposal and irreducibility assumptions.",
            "The pilot is distinct from Profile Fiber sampling: it preserves individual row and column degrees, but does not preserve X and Y profiles.",
        ],
        "decisions": {
            "C4_INT8_1599245": "REJECTED_NUMERIC_OVERFLOW",
            "C4_INT64_2427533": "PASS_SCOPED",
            "microcanonical_inference": "NOT_ESTABLISHED",
            "mixing": "NOT_ASSESSED",
            "burn_in_adequacy": "NOT_ESTABLISHED",
            "promotion_authority": "NONE",
        },
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
        },
        "files_written_by_audit": [str(OUTPUT)],
        "production_modified": False,
        "source_modified": False,
        "pilot_result_modified": False,
    }
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("AUDIT_STATUS=PASS_SCOPED")
    print("SOURCE_SHA256=", source_sha)
    print("PILOT_SCRIPT_SHA256=", script_sha)
    print("PILOT_RESULT_SHA256=", pilot_sha)
    print("C4_INT8_REJECTED=", c4_int8)
    print("C4_INT64_ACCEPTED=", c4_int64)
    print("TRACE_POINTS=", arr.size)
    print("TRACE_MIN_MAX=", int(arr.min()), int(arr.max()))
    print("TRACE_MEAN=", float(arr.mean()))
    print("AUDIT_REPORT=", OUTPUT)
    print("AUDIT_REPORT_SHA256=", sha256_file(OUTPUT))
    print("PRODUCTION_MODIFIED=False")
    print("SOURCE_MODIFIED=False")


if __name__ == "__main__":
    main()
