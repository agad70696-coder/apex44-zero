#!/usr/bin/env python3
"""Reproduce and verify APEX44's QAC morphology-to-projection analysis.

Default behavior is read-only. Use --write only when intentionally replacing
committed matrix artifacts with the corrected, wide-integer computation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import scipy
import scipy.sparse as sp
from scipy.stats import poisson

ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = ROOT / "PHASE2_CLEAN/source/quranic-corpus-morphology-0.4.txt"
SOURCE_MANIFEST_PATH = ROOT / "PHASE2_CLEAN/source/source_manifest.json"
OUTPUT_DIR = ROOT / "APEX44/03-computation/output"
REPORT_PATH = ROOT / "APEX44/04-evaluation/DRS_real_data.json"
META_PATH = OUTPUT_DIR / "W_sig_meta.json"

EXPECTED_SOURCE_SHA256 = (
    "a1d12923815341face765083805d2148ed2d9f5cc3f7d6665219d887675d8c46"
)
ALPHA = 0.05
ROOT_FEATURE_COUNT = 1642
EXPECTED_B_SHAPE = (6236, ROOT_FEATURE_COUNT)
EXPECTED_B_NNZ = 102210
ARTIFACT_PATHS = {
    "B_real": OUTPUT_DIR / "B_real_6236x1642.npz",
    "W_morph": OUTPUT_DIR / "W_morph_1642x1642.npz",
    "W_sig_Holm": OUTPUT_DIR / "W_sig_1642x1642.npz",
    "W_fdr_BH": OUTPUT_DIR / "W_fdr_1642x1642.npz",
    "roots": OUTPUT_DIR / "roots_1642.json",
}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_and_validate_source() -> tuple[bytes, str, dict[str, Any]]:
    if not SOURCE_PATH.is_file():
        raise FileNotFoundError(f"Required QAC source is missing: {SOURCE_PATH}")
    if not SOURCE_MANIFEST_PATH.is_file():
        raise FileNotFoundError(f"Required source manifest is missing: {SOURCE_MANIFEST_PATH}")

    raw = SOURCE_PATH.read_bytes()
    observed_sha = sha256_bytes(raw)
    if observed_sha != EXPECTED_SOURCE_SHA256:
        raise ValueError(
            "SOURCE_SHA256_MISMATCH: expected "
            f"{EXPECTED_SOURCE_SHA256}, observed {observed_sha}"
        )

    manifest = json.loads(SOURCE_MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.get("sha256") != observed_sha:
        raise ValueError("SOURCE_MANIFEST_SHA256_MISMATCH")
    if manifest.get("bytes") != len(raw):
        raise ValueError("SOURCE_MANIFEST_BYTE_LENGTH_MISMATCH")
    if manifest.get("lines") != len(raw.splitlines()):
        raise ValueError("SOURCE_MANIFEST_LINE_COUNT_MISMATCH")
    if manifest.get("version") != "0.4":
        raise ValueError("UNEXPECTED_QAC_SOURCE_VERSION")

    header = raw[:4096]
    if b"Copyright (C) 2011 Kais Dukes" not in header:
        raise ValueError("SOURCE_COPYRIGHT_BLOCK_MISSING")
    if b"License: GNU General Public License" not in header:
        raise ValueError("SOURCE_LICENSE_NOTICE_MISSING")
    if b"PLEASE DO NOT REMOVE OR CHANGE THIS COPYRIGHT BLOCK" not in header:
        raise ValueError("SOURCE_COPYRIGHT_INSTRUCTIONS_MISSING")

    return raw, observed_sha, manifest


def build_biadjacency(source_text: str) -> tuple[sp.csr_matrix, list[str]]:
    """Build verse × root/lemma binary incidence, preserving the legacy ordering."""
    lines = [
        line.strip()
        for line in source_text.splitlines()
        if line.strip() and not line.startswith("#") and not line.startswith("LOCATION")
    ]
    verse_to_index: dict[tuple[int, int], int] = {}
    triples: list[tuple[int, str]] = []
    location_pattern = __import__("re").compile(r"\(?(\d+):(\d+):\d+:\d+\)?")
    root_pattern = __import__("re").compile(r"ROOT:([^\s|]+)")
    lemma_pattern = __import__("re").compile(r"LEM:([^\s|]+)")

    for line in lines:
        parts = line.split("\t")
        match = location_pattern.search(parts[0])
        if match is None:
            continue
        verse_key = (int(match.group(1)), int(match.group(2)))
        if verse_key not in verse_to_index:
            verse_to_index[verse_key] = len(verse_to_index)
        verse_index = verse_to_index[verse_key]
        features = " ".join(parts[1:])
        root_match = root_pattern.search(features)
        lemma_match = lemma_pattern.search(features)
        if root_match:
            feature = root_match.group(1)
        elif lemma_match:
            feature = lemma_match.group(1)
        else:
            feature = parts[1] if len(parts) > 1 else None
        if feature and feature != "UNK":
            triples.append((verse_index, feature))

    counts = Counter(feature for _, feature in triples)
    roots = [feature for feature, _ in counts.most_common(ROOT_FEATURE_COUNT)]
    feature_to_index = {feature: index for index, feature in enumerate(roots)}

    rows: list[int] = []
    cols: list[int] = []
    for verse_index, feature in triples:
        feature_index = feature_to_index.get(feature)
        if feature_index is not None:
            rows.append(verse_index)
            cols.append(feature_index)

    matrix = sp.coo_matrix(
        (np.ones(len(rows), dtype=np.int8), (rows, cols)),
        shape=(len(verse_to_index), len(roots)),
        dtype=np.int8,
    ).tocsr()
    matrix.sum_duplicates()
    matrix.data = np.ones_like(matrix.data)

    if matrix.shape != EXPECTED_B_SHAPE or matrix.nnz != EXPECTED_B_NNZ:
        raise ValueError(
            "B_MATRIX_CONTRACT_MISMATCH: "
            f"shape={matrix.shape}, nnz={matrix.nnz}; "
            f"expected shape={EXPECTED_B_SHAPE}, nnz={EXPECTED_B_NNZ}"
        )
    if len(set(roots)) != ROOT_FEATURE_COUNT:
        raise ValueError("ROOT_LABELS_NOT_UNIQUE")
    return matrix, roots


def holm_adjust(p_values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return corrected Holm p-values and rejection flags in original pair order."""
    count = len(p_values)
    order = np.argsort(p_values, kind="mergesort")
    sorted_p = p_values[order]
    adjusted_sorted = np.maximum.accumulate(
        sorted_p * (count - np.arange(count, dtype=np.float64))
    )
    adjusted_sorted = np.minimum(adjusted_sorted, 1.0)
    adjusted = np.empty(count, dtype=np.float64)
    adjusted[order] = adjusted_sorted
    return adjusted, adjusted <= ALPHA


def bh_adjust(p_values: np.ndarray) -> tuple[float | None, np.ndarray]:
    """Return the canonical BH cutoff and rejection flags, including ties at cutoff."""
    count = len(p_values)
    order = np.argsort(p_values, kind="mergesort")
    sorted_p = p_values[order]
    thresholds = ALPHA * np.arange(1, count + 1, dtype=np.float64) / count
    passing = np.flatnonzero(sorted_p <= thresholds)
    if len(passing) == 0:
        return None, np.zeros(count, dtype=bool)
    cutoff = float(sorted_p[passing[-1]])
    return cutoff, p_values <= cutoff


def symmetric_weighted_mask(
    rows: np.ndarray,
    cols: np.ndarray,
    observations: np.ndarray,
    rejected: np.ndarray,
    shape: tuple[int, int],
) -> sp.csr_matrix:
    """Create a symmetric, integer-weighted projection from rejected positive edges."""
    keep = rejected & (observations > 0)
    selected_rows = rows[keep]
    selected_cols = cols[keep]
    values = observations[keep].astype(np.int64, copy=False)
    both_rows = np.concatenate((selected_rows, selected_cols))
    both_cols = np.concatenate((selected_cols, selected_rows))
    both_values = np.concatenate((values, values))
    result = sp.coo_matrix(
        (both_values, (both_rows, both_cols)), shape=shape, dtype=np.int64
    ).tocsr()
    result.setdiag(0)
    result.eliminate_zeros()
    return result


def compute_bundle() -> dict[str, Any]:
    """Compute the incidence, wide-integer projection and full-family corrected masks."""
    raw, source_sha, source_manifest = read_and_validate_source()
    source_text = raw.decode("utf-8")
    incidence, roots = build_biadjacency(source_text)

    # CRITICAL: int8 matrix multiplication wraps counts >127 and can turn
    # positive edges negative or erase counts divisible by 256. Promote first.
    incidence_wide = incidence.astype(np.int64)
    projection = (incidence_wide.T @ incidence_wide).tocsr()
    projection.setdiag(0)
    projection.eliminate_zeros()
    if projection.dtype != np.dtype(np.int64):
        raise ValueError(f"PROJECTION_DTYPE_MISMATCH: {projection.dtype}")
    if projection.nnz and int(projection.data.min()) < 0:
        raise ValueError("NEGATIVE_PROJECTION_COUNT")
    if np.count_nonzero(projection.diagonal()):
        raise ValueError("PROJECTION_DIAGONAL_NOT_ZERO")
    if (projection != projection.T).nnz:
        raise ValueError("PROJECTION_NOT_SYMMETRIC")

    row_degrees = np.asarray(incidence.sum(axis=1)).ravel().astype(np.float64)
    col_degrees = np.asarray(incidence.sum(axis=0)).ravel().astype(np.float64)
    edge_count = float(row_degrees.sum())
    row_degree_square_sum = float(np.square(row_degrees).sum())
    root_count = incidence.shape[1]

    # Test the entire prespecified family of unordered root pairs. A pair with
    # zero observed co-occurrence has upper-tail p=1; it remains in the family.
    pair_rows, pair_cols = np.triu_indices(root_count, k=1)
    observed_dense = projection.toarray()
    observations = observed_dense[pair_rows, pair_cols].astype(np.int64, copy=False)
    expected = (
        col_degrees[pair_rows]
        * col_degrees[pair_cols]
        * row_degree_square_sum
        / (edge_count * edge_count)
    )
    expected = np.maximum(expected, 1e-12)
    p_values = poisson.sf(observations.astype(np.float64) - 1.0, expected)
    if not np.all(np.isfinite(p_values)) or np.any((p_values < 0) | (p_values > 1)):
        raise ValueError("INVALID_P_VALUES")

    p_holm, reject_holm = holm_adjust(p_values)
    bh_cutoff, reject_bh = bh_adjust(p_values)
    if np.any(reject_holm & (observations == 0)) or np.any(
        reject_bh & (observations == 0)
    ):
        raise ValueError("ZERO_COUNT_EDGE_REJECTED")

    mask_holm = symmetric_weighted_mask(
        pair_rows, pair_cols, observations, reject_holm, projection.shape
    )
    mask_bh = symmetric_weighted_mask(
        pair_rows, pair_cols, observations, reject_bh, projection.shape
    )

    selected = np.flatnonzero(reject_holm & (observations > 0))
    selected = selected[
        np.argsort(-observations[selected], kind="mergesort")[:20]
    ]
    top_20 = [
        {
            "a": roots[int(pair_rows[index])],
            "b": roots[int(pair_cols[index])],
            "observed": int(observations[index]),
            "expected_poisson_mean": float(expected[index]),
            "p_raw": float(p_values[index]),
            "p_holm_adjusted": float(p_holm[index]),
        }
        for index in selected
    ]

    stats: dict[str, Any] = {
        "B_shape": list(incidence.shape),
        "B_nnz": int(incidence.nnz),
        "B_density": float(incidence.nnz / (incidence.shape[0] * incidence.shape[1])),
        "W_morph_shape": list(projection.shape),
        "W_morph_nnz": int(projection.nnz),
        "W_morph_max_common_verses": int(projection.data.max()) if projection.nnz else 0,
        "W_sig_nnz_undirected": int(mask_holm.nnz // 2),
        "W_sig_nnz_directed": int(mask_holm.nnz),
        "W_fdr_nnz_undirected": int(mask_bh.nnz // 2),
        "W_fdr_nnz_directed": int(mask_bh.nnz),
        "E": int(edge_count),
        "S2": int(row_degree_square_sum),
        "tested_hypotheses": int(len(p_values)),
        "nonzero_projection_pairs": int(np.count_nonzero(observations)),
        "zero_projection_pairs": int(np.count_nonzero(observations == 0)),
        "alpha": ALPHA,
        "bh_cutoff": bh_cutoff,
        "top_20_holm": top_20,
        "source_sha256": source_sha,
        "source_bytes": len(raw),
        "source_lines": len(raw.splitlines()),
        "legacy_projection_dtype": "int8",
        "legacy_projection_negative_entries": 1580,
        "legacy_projection_nnz": 318274,
        "corrected_projection_dtype": "int64",
        "changed_projection_coordinates_vs_legacy": 2108,
        "lost_undirected_pairs_due_to_int8_wraparound": 2,
    }
    return {
        "source_sha256": source_sha,
        "source_manifest": source_manifest,
        "incidence": incidence,
        "roots": roots,
        "projection": projection,
        "W_sig": mask_holm,
        "W_fdr": mask_bh,
        "stats": stats,
    }


def json_write(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def artifact_hashes() -> dict[str, str]:
    return {
        relative: sha256_file(ROOT / relative)
        for relative in (
            "APEX44/03-computation/output/B_real_6236x1642.npz",
            "APEX44/03-computation/output/W_morph_1642x1642.npz",
            "APEX44/03-computation/output/W_sig_1642x1642.npz",
            "APEX44/03-computation/output/W_fdr_1642x1642.npz",
            "APEX44/03-computation/output/roots_1642.json",
        )
    }


def write_bundle(bundle: dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    sp.save_npz(ARTIFACT_PATHS["B_real"], bundle["incidence"])
    sp.save_npz(ARTIFACT_PATHS["W_morph"], bundle["projection"])
    sp.save_npz(ARTIFACT_PATHS["W_sig_Holm"], bundle["W_sig"])
    sp.save_npz(ARTIFACT_PATHS["W_fdr_BH"], bundle["W_fdr"])
    ARTIFACT_PATHS["roots"].write_text(
        json.dumps(bundle["roots"], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    stats = bundle["stats"]
    hashes = artifact_hashes()
    method = (
        "Degree-based bipartite projection: lambda_ij = d_i*d_j*sum_v(k_v^2)/E^2; "
        "Poisson upper-tail approximation; Holm FWER alpha=0.05 and BH FDR alpha=0.05. "
        "This is an approximation, not an exact sampled BiCM null."
    )
    meta = {
        "schema_version": "apex44-qac-projection-reproduction-v1",
        "source_sha256": bundle["source_sha256"],
        "producer": "APEX44/03-computation/reproduce_qac_analysis.py",
        "numeric_dtype": "int64 for projection and significance matrices",
        "B_shape": stats["B_shape"],
        "B_nnz": stats["B_nnz"],
        "W_morph_nnz": stats["W_morph_nnz"],
        "W_morph_max_common_verses": stats["W_morph_max_common_verses"],
        "W_sig_nnz_undirected": stats["W_sig_nnz_undirected"],
        "W_sig_nnz_directed": stats["W_sig_nnz_directed"],
        "W_fdr_nnz_undirected": stats["W_fdr_nnz_undirected"],
        "W_fdr_nnz_directed": stats["W_fdr_nnz_directed"],
        "method": method,
        "multiple_testing_family": (
            "all unordered pairs among the 1642 retained root/lemma labels, including "
            "zero-observation pairs with upper-tail p=1"
        ),
        "E": stats["E"],
        "S2": stats["S2"],
        "tested_hypotheses": stats["tested_hypotheses"],
        "nonzero_projection_pairs": stats["nonzero_projection_pairs"],
        "zero_projection_pairs": stats["zero_projection_pairs"],
        "alpha": ALPHA,
        "bh_cutoff": stats["bh_cutoff"],
        "top_20": stats["top_20_holm"],
        "artifact_sha256": hashes,
        "reproducibility_status": "PASS_SCOPED",
        "interpretation_boundary": (
            "Successful replay establishes source-to-array reproducibility, not the validity "
            "of the degree-based Poisson approximation, annotation ontology, or historical claim."
        ),
    }
    json_write(META_PATH, meta)

    report: dict[str, Any] = {}
    if REPORT_PATH.exists():
        report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    source_manifest = bundle["source_manifest"]
    report["source"] = {
        "file": SOURCE_PATH.name,
        "sha256": bundle["source_sha256"],
        "lines": stats["source_lines"],
        "size": str(stats["source_bytes"]),
        "bytes": stats["source_bytes"],
        "version": "0.4",
        "license_notice": source_manifest["license_notice"],
        "origin_url": source_manifest["origin_url"],
    }
    report["B_real"] = {
        "shape": stats["B_shape"],
        "nnz": stats["B_nnz"],
        "density": stats["B_density"],
        "file": ARTIFACT_PATHS["B_real"].relative_to(ROOT).as_posix(),
    }
    report["W_morph"] = {
        "shape": stats["W_morph_shape"],
        "nnz": stats["W_morph_nnz"],
        "dtype": "int64",
        "max_common_verses": stats["W_morph_max_common_verses"],
        "file": ARTIFACT_PATHS["W_morph"].relative_to(ROOT).as_posix(),
    }
    report["W_sig_Holm"] = {
        "undirected": stats["W_sig_nnz_undirected"],
        "directed": stats["W_sig_nnz_directed"],
        "alpha": ALPHA,
        "tested_hypotheses": stats["tested_hypotheses"],
        "family": "all unordered root pairs, including pairs with zero observed co-occurrence",
        "method": method,
        "file": ARTIFACT_PATHS["W_sig_Holm"].relative_to(ROOT).as_posix(),
    }
    report["W_fdr_BH"] = {
        "undirected": stats["W_fdr_nnz_undirected"],
        "directed": stats["W_fdr_nnz_directed"],
        "alpha": ALPHA,
        "tested_hypotheses": stats["tested_hypotheses"],
        "family": "all unordered root pairs, including pairs with zero observed co-occurrence",
        "method": "Benjamini-Hochberg FDR alpha=0.05 over the full pair family",
        "file": ARTIFACT_PATHS["W_fdr_BH"].relative_to(ROOT).as_posix(),
    }
    historical = report.get("historical_comparison", {})
    report["historical_comparison"] = {
        "historical_claim": historical.get("historical_claim", 1816),
        "legacy_overflow_holm": 616,
        "legacy_overflow_fdr": 3729,
        "corrected_all_pairs_holm": stats["W_sig_nnz_undirected"],
        "corrected_all_pairs_fdr": stats["W_fdr_nnz_undirected"],
        "verdict": (
            "NOT_VERIFIED: the historical 1816 figure has not been recreated under a "
            "source-bound comparable method. Previous 616/3729 counts are invalidated because "
            "the prior projection used int8 arithmetic and corrected only the nonzero-edge family."
        ),
    }
    report["top_10_Holm"] = stats["top_20_holm"][:10]
    report["computation_audit"] = {
        "status": "CORRECTED",
        "defect": "integer overflow in int8 projection multiplication",
        "legacy_projection_dtype": "int8",
        "legacy_negative_projection_entries": stats["legacy_projection_negative_entries"],
        "legacy_projection_nnz": stats["legacy_projection_nnz"],
        "corrected_projection_dtype": "int64",
        "corrected_projection_nnz": stats["W_morph_nnz"],
        "corrected_projection_max": stats["W_morph_max_common_verses"],
        "changed_coordinates_vs_legacy": stats["changed_projection_coordinates_vs_legacy"],
        "undirected_pairs_previously_lost_to_zero_wraparound": (
            stats["lost_undirected_pairs_due_to_int8_wraparound"]
        ),
        "multiple_testing_family_changed": True,
        "legacy_counts_valid": False,
    }
    report["artifact_sha256"] = hashes
    report["reproducibility_audit"] = {
        "status": "PASS_SCOPED",
        "reason": "SOURCE_BOUND_REPLAY_AND_WIDE_INTEGER_PROJECTION",
        "source_available_in_snapshot": True,
        "source_sha256_verified": bundle["source_sha256"],
        "producer": "APEX44/03-computation/reproduce_qac_analysis.py",
        "producer_sha256": sha256_file(Path(__file__).resolve()),
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
        },
        "artifact_sha256": hashes,
        "replay_receipt": (
            "Generated and semantically compared all four sparse matrices and root labels; "
            "see test_real_data_provenance.py and CI replay step."
        ),
    }
    report["status"] = "REVIEW_REQUIRED"
    report["evidence_status"] = "REPRODUCED_SCOPED"
    report["promotion_authority"] = "NONE"
    json_write(REPORT_PATH, report)


def verify_bundle() -> dict[str, Any]:
    bundle = compute_bundle()
    missing = [str(path) for path in ARTIFACT_PATHS.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("MISSING_OUTPUT_ARTIFACTS: " + ", ".join(missing))

    expected_matrices = {
        "B_real": bundle["incidence"],
        "W_morph": bundle["projection"],
        "W_sig_Holm": bundle["W_sig"],
        "W_fdr_BH": bundle["W_fdr"],
    }
    for key, expected in expected_matrices.items():
        actual = sp.load_npz(ARTIFACT_PATHS[key]).tocsr()
        expected = expected.tocsr()
        if actual.shape != expected.shape or (actual != expected).nnz:
            raise ValueError(
                f"REPLAY_MATRIX_MISMATCH:{key}: "
                f"expected shape={expected.shape}, nnz={expected.nnz}; "
                f"actual shape={actual.shape}, nnz={actual.nnz}"
            )
        if key != "B_real" and actual.dtype != np.dtype(np.int64):
            raise ValueError(f"PROJECTION_DTYPE_MISMATCH:{key}:{actual.dtype}")

    stored_roots = json.loads(ARTIFACT_PATHS["roots"].read_text(encoding="utf-8"))
    if stored_roots != bundle["roots"]:
        raise ValueError("ROOT_LABEL_REPLAY_MISMATCH")

    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    meta = json.loads(META_PATH.read_text(encoding="utf-8"))
    hashes = artifact_hashes()
    if report.get("artifact_sha256") != hashes or meta.get("artifact_sha256") != hashes:
        raise ValueError("ARTIFACT_SHA256_MANIFEST_MISMATCH")
    if report.get("status") != "REVIEW_REQUIRED":
        raise ValueError("SCIENTIFIC_CLAIM_STATUS_MUST_REMAIN_REVIEW_REQUIRED")
    if report.get("evidence_status") != "REPRODUCED_SCOPED":
        raise ValueError("EVIDENCE_STATUS_MISMATCH")
    if report.get("promotion_authority") != "NONE":
        raise ValueError("PROMOTION_AUTHORITY_MUST_REMAIN_NONE")

    stats = bundle["stats"]
    expected_report_counts = (
        report["W_morph"]["nnz"] == stats["W_morph_nnz"],
        report["W_sig_Holm"]["undirected"] == stats["W_sig_nnz_undirected"],
        report["W_fdr_BH"]["undirected"] == stats["W_fdr_nnz_undirected"],
        meta["tested_hypotheses"] == stats["tested_hypotheses"],
        meta["source_sha256"] == bundle["source_sha256"],
    )
    if not all(expected_report_counts):
        raise ValueError("REPLAY_REPORT_METRICS_MISMATCH")

    return {
        "status": "PASS_SCOPED_REPRODUCTION",
        "source_sha256": bundle["source_sha256"],
        "B_shape": stats["B_shape"],
        "B_nnz": stats["B_nnz"],
        "W_morph_nnz": stats["W_morph_nnz"],
        "W_morph_dtype": str(bundle["projection"].dtype),
        "W_morph_max_common_verses": stats["W_morph_max_common_verses"],
        "tested_hypotheses": stats["tested_hypotheses"],
        "nonzero_projection_pairs": stats["nonzero_projection_pairs"],
        "W_sig_Holm_undirected": stats["W_sig_nnz_undirected"],
        "W_fdr_BH_undirected": stats["W_fdr_nnz_undirected"],
        "artifact_sha256_verified": len(hashes),
        "promotion_authority": "NONE",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--verify", action="store_true", help="Read-only clean replay and comparison")
    action.add_argument("--write", action="store_true", help="Replace output matrices and reports")
    args = parser.parse_args()

    if args.write:
        bundle = compute_bundle()
        write_bundle(bundle)
    receipt = verify_bundle()
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
