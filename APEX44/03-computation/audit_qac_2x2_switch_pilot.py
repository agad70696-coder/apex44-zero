#!/usr/bin/env python3
"""Portable, read-only audit for the archived QAC 2x2-switch pilot."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import scipy
import scipy.sparse as sp

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "APEX44/03-computation/output/B_real_6236x1642.npz"
CORPUS = ROOT / "PHASE2_CLEAN/source/quranic-corpus-morphology-0.4.txt"
SOURCE_MANIFEST = ROOT / "PHASE2_CLEAN/source/source_manifest.json"
PILOT = ROOT / "artifacts/microcanonical/qac_2x2_switch_pilot_20261112.json"
RUNNER = ROOT / "artifacts/microcanonical/qac_2x2_switch_pilot_runner_20261112.py"
TERMUX_AUDIT = ROOT / "artifacts/microcanonical/qac_2x2_switch_pilot_audit_termux_original_20261112.json"
OUTPUT = ROOT / "artifacts/microcanonical/qac_2x2_switch_pilot_audit_20261112.json"

EXPECTED_MATRIX_SHA = "a75fdf4d57bd9448a74607fff9b9ddf31c26e2c3f356eb9fd40d19aa511c8c3a"
EXPECTED_CORPUS_SHA = "a1d12923815341face765083805d2148ed2d9f5cc3f7d6665219d887675d8c46"
EXPECTED_SHAPE = (6236, 1642)
EXPECTED_EDGES = 44431
EXPECTED_C4 = 2427533
EXPECTED_SEEDS = [2026111201, 2026111202, 2026111203, 2026111204]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def c4_from_projection(projection: sp.spmatrix) -> int:
    upper = sp.triu(projection, k=1).tocoo()
    return sum(int(value) * (int(value) - 1) // 2 for value in upper.data)


def require(condition: bool, label: str) -> None:
    if not condition:
        raise RuntimeError("AUDIT_FAILED:" + label)


def main() -> None:
    for path in (SOURCE, CORPUS, SOURCE_MANIFEST, PILOT, RUNNER, TERMUX_AUDIT):
        require(path.is_file(), "MISSING:" + str(path.relative_to(ROOT)))

    matrix_sha = sha256(SOURCE)
    corpus_sha = sha256(CORPUS)
    runner_sha = sha256(RUNNER)
    pilot_sha = sha256(PILOT)
    termux_audit_sha = sha256(TERMUX_AUDIT)

    source_manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    require(matrix_sha == EXPECTED_MATRIX_SHA, "MATRIX_SHA256")
    require(corpus_sha == EXPECTED_CORPUS_SHA, "CORPUS_SHA256")
    require(source_manifest.get("sha256") == corpus_sha, "SOURCE_MANIFEST_SHA256")
    require(source_manifest.get("bytes") == CORPUS.stat().st_size, "SOURCE_MANIFEST_BYTES")

    B8 = sp.load_npz(SOURCE).tocsr()
    B8.sum_duplicates()
    B8.eliminate_zeros()
    B8.sort_indices()
    require(B8.shape == EXPECTED_SHAPE, "MATRIX_SHAPE")
    require(B8.nnz == EXPECTED_EDGES, "MATRIX_NNZ")
    require(bool(np.all(B8.data == 1)), "MATRIX_BINARY")

    B64 = B8.astype(np.int64)
    W64_full = (B64.T @ B64).tocsr()
    W64 = W64_full.copy()
    W64.setdiag(0)
    W64.eliminate_zeros()
    c4_root = c4_from_projection(W64)

    V64_full = (B64 @ B64.T).tocsr()
    c4_verse = c4_from_projection(V64_full)

    # Negative control: reproduce the unsafe int8 multiplication.
    W8 = (B8.T @ B8).tocsr()
    c4_int8 = c4_from_projection(W8)
    int8_negative_cells = int(np.count_nonzero(W8.data < 0))
    int8_vs_int64_cells = int((W8.astype(np.int64) != W64_full).nnz)

    pilot = json.loads(PILOT.read_text(encoding="utf-8"))
    require(pilot.get("schema") == "qac-realdata-fixed-degree-switch-pilot-v1", "PILOT_SCHEMA")
    require(pilot.get("source_matrix_sha256") == matrix_sha, "PILOT_MATRIX_SHA")
    require(pilot.get("source_corpus_sha256") == corpus_sha, "PILOT_CORPUS_SHA")
    require(tuple(pilot.get("shape", [])) == EXPECTED_SHAPE, "PILOT_SHAPE")
    require(pilot.get("nnz") == EXPECTED_EDGES, "PILOT_EDGE_COUNT")
    require(pilot.get("observed_c4") == EXPECTED_C4, "PILOT_OBSERVED_C4")
    require(c4_root == EXPECTED_C4, "ROOT_C4_REPLAY")
    require(c4_verse == EXPECTED_C4, "VERSE_C4_REPLAY")
    require(c4_int8 == 1599245, "INT8_NEGATIVE_CONTROL")
    require(int8_negative_cells == 119, "INT8_NEGATIVE_CELL_COUNT")
    require(int8_vs_int64_cells == 152, "INT8_DIFFERING_CELL_COUNT")

    chains = pilot.get("chains", [])
    require(len(chains) == 4, "CHAIN_COUNT")
    summaries = []
    all_trace_values = []
    all_degree_flags = True

    for expected_seed, chain in zip(EXPECTED_SEEDS, chains):
        require(chain.get("seed") == expected_seed, "CHAIN_SEED")
        require(chain.get("proposals") == 500000, "CHAIN_PROPOSALS")
        require(chain.get("burn_in") == 100000, "CHAIN_BURN_IN")
        accepted = int(chain["accepted"])
        same_pair_reject = int(chain["same_row_col_reject"])
        occupied_reject = int(chain["occupied_cross_reject"])
        require(accepted + same_pair_reject + occupied_reject == 500000, "PROPOSAL_ACCOUNTING")
        require(abs(float(chain["acceptance_rate"]) - accepted / 500000) < 1e-12, "ACCEPTANCE_RATE")

        degree_flag = chain.get("exact_degrees_preserved") is True
        all_degree_flags &= degree_flag
        trace = chain.get("trace", [])
        require(len(trace) == 9, "TRACE_POINT_COUNT")
        trace_c4 = []
        for index, record in enumerate(trace, start=2):
            require(record.get("proposal") == index * 50000, "TRACE_STEP")
            require(record.get("edges") == EXPECTED_EDGES, "TRACE_EDGE_COUNT")
            trace_c4.append(int(record["c4"]))
            all_trace_values.append(int(record["c4"]))

        summaries.append({
            "seed": expected_seed,
            "proposals": 500000,
            "burn_in": 100000,
            "accepted": accepted,
            "same_row_col_reject": same_pair_reject,
            "occupied_cross_reject": occupied_reject,
            "acceptance_rate": float(chain["acceptance_rate"]),
            "trace_points": len(trace),
            "trace_min_c4": min(trace_c4),
            "trace_max_c4": max(trace_c4),
            "trace_final_c4": trace_c4[-1],
            "degree_invariant_recorded_by_runner": degree_flag,
        })

    require(all_degree_flags, "RECORDED_DEGREE_INVARIANTS")
    traces = np.asarray(all_trace_values, dtype=np.float64)
    require(traces.size == 36, "TOTAL_TRACE_POINTS")

    report = {
        "schema": "AA-QAC-2X2-SWITCH-PILOT-AUDIT-0.1",
        "created_on": "2026-11-12",
        "status": "PASS_SCOPED",
        "scope": "Read-only replay of source identity and C4 arithmetic, plus structural validation of the archived four-chain pilot receipt. Does not certify mixing or inferential calibration.",
        "source": {
            "matrix_path": "APEX44/03-computation/output/B_real_6236x1642.npz",
            "matrix_sha256": matrix_sha,
            "matrix_shape": list(B8.shape),
            "matrix_nnz": int(B8.nnz),
            "matrix_binary": True,
            "corpus_path": "PHASE2_CLEAN/source/quranic-corpus-morphology-0.4.txt",
            "corpus_sha256": corpus_sha,
            "source_manifest_sha256": source_manifest.get("sha256"),
        },
        "arithmetic": {
            "c4_root_pair_projection_int64": c4_root,
            "c4_verse_pair_projection_int64": c4_verse,
            "c4_int8_negative_control": c4_int8,
            "int8_negative_overlap_cells": int8_negative_cells,
            "int8_vs_int64_different_cells": int8_vs_int64_cells,
            "accepted_c4": EXPECTED_C4,
            "rejected_int8_c4": "NUMERIC_OVERFLOW",
        },
        "pilot_artifacts": {
            "runner_path": "artifacts/microcanonical/qac_2x2_switch_pilot_runner_20261112.py",
            "runner_sha256": runner_sha,
            "result_path": "artifacts/microcanonical/qac_2x2_switch_pilot_20261112.json",
            "result_sha256": pilot_sha,
            "original_termux_audit_sha256": termux_audit_sha,
            "original_termux_audit_path": "artifacts/microcanonical/qac_2x2_switch_pilot_audit_termux_original_20261112.json",
        },
        "pilot": {
            "chain_count": len(chains),
            "seeds": EXPECTED_SEEDS,
            "proposals_per_chain": 500000,
            "burn_in_per_chain": 100000,
            "retained_c4_snapshots_per_chain": 9,
            "trace_spacing_proposals": 50000,
            "all_chains_record_exact_degree_preservation": all_degree_flags,
            "chains": summaries,
            "trace_summary": {
                "count": int(traces.size),
                "minimum_c4": int(traces.min()),
                "maximum_c4": int(traces.max()),
                "mean_c4": float(traces.mean()),
                "median_c4": float(np.median(traces)),
            },
            "kernel": pilot.get("kernel"),
            "null": pilot.get("null"),
        },
        "limitations": [
            "All four chains use the same observed graph as their initial state; independent seeds do not establish overdispersed initialization.",
            "Only nine C4 snapshots per chain are retained; full trajectories and sampled matrices are not archived.",
            "The audit verifies the runner's recorded degree-invariant flags and proposal accounting; it cannot independently replay every intermediate state because those states were not saved.",
            "Autocorrelation, effective sample size, rank-normalized/folded split-Rhat, burn-in adequacy, and tail convergence remain unestablished.",
            "No Monte Carlo p-value or calibrated inferential tail probability is produced.",
            "This is the degree-preserving microcanonical 2x2-switch experiment. It does not preserve X or Y and is not the Profile Fiber experiment.",
        ],
        "decision": {
            "c4_int8_1599245": "REJECTED_NUMERIC_OVERFLOW",
            "c4_int64_2427533": "PASS_SCOPED",
            "pilot": "DESCRIPTIVE_ONLY",
            "mixing": "NOT_ESTABLISHED",
            "p_value": "NOT_COMPUTED",
            "promotion_authority": "NONE",
        },
        "environment": {
            "numpy": np.__version__,
            "scipy": scipy.__version__,
        },
        "source_modified": False,
        "pilot_result_modified": False,
        "production_modified": False,
    }
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + chr(10), encoding="utf-8")
    print("AUDIT_STATUS=PASS_SCOPED")
    print("MATRIX_SHA256=", matrix_sha)
    print("CORPUS_SHA256=", corpus_sha)
    print("C4_ROOT_INT64=", c4_root)
    print("C4_VERSE_INT64=", c4_verse)
    print("C4_INT8_REJECTED=", c4_int8)
    print("INT8_NEGATIVE_CELLS=", int8_negative_cells)
    print("INT8_DIFFERING_CELLS=", int8_vs_int64_cells)
    print("TRACE_POINTS=", int(traces.size))
    print("TRACE_MIN_MAX=", int(traces.min()), int(traces.max()))
    print("TRACE_MEAN=", float(traces.mean()))
    print("AUDIT_REPORT=", OUTPUT.relative_to(ROOT))
    print("AUDIT_REPORT_SHA256=", sha256(OUTPUT))
    print("PRODUCTION_MODIFIED=False")


if __name__ == "__main__":
    main()
