"""Fail-closed provenance and integrity checks for the QAC-derived matrix bundle.

These checks verify committed artifacts' byte identity and advertised structure.
They do not reproduce the scientific analysis or validate its statistical model.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
EVAL = ROOT / "APEX44" / "04-evaluation"
OUTPUT = ROOT / "APEX44" / "03-computation" / "output"


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _matrix_facts(path: Path) -> tuple[tuple[int, int], int, set[tuple[int, int]]]:
    """Read a scipy sparse NPZ archive without depending on scipy at test time."""
    with ZipFile(path) as archive:
        assert archive.testzip() is None, f"Corrupt NPZ/ZIP member in {path}"

    with np.load(path, allow_pickle=False) as data:
        required = {"data", "indices", "indptr", "shape", "format"}
        assert required.issubset(data.files), (
            f"{path} is not a supported SciPy sparse NPZ; keys={data.files}"
        )
        shape = tuple(int(x) for x in data["shape"].tolist())
        assert len(shape) == 2, f"Expected a 2-D matrix in {path}, got {shape}"
        fmt_value = data["format"].item()
        fmt = fmt_value.decode("ascii") if isinstance(fmt_value, bytes) else str(fmt_value)
        values = np.asarray(data["data"])
        indices = np.asarray(data["indices"], dtype=np.int64)
        indptr = np.asarray(data["indptr"], dtype=np.int64)
        assert len(values) == len(indices), f"data/indices length mismatch in {path}"

        if fmt == "csr":
            assert len(indptr) == shape[0] + 1, f"Invalid CSR indptr in {path}"
            rows = np.repeat(np.arange(shape[0]), np.diff(indptr))
            cols = indices
        elif fmt == "csc":
            assert len(indptr) == shape[1] + 1, f"Invalid CSC indptr in {path}"
            cols = np.repeat(np.arange(shape[1]), np.diff(indptr))
            rows = indices
        else:
            raise AssertionError(f"Unsupported sparse format {fmt!r} in {path}")

        assert len(rows) == len(values), f"indptr/value count mismatch in {path}"
        assert np.all((rows >= 0) & (rows < shape[0])), f"Row index out of bounds in {path}"
        assert np.all((cols >= 0) & (cols < shape[1])), f"Column index out of bounds in {path}"
        coordinates = set(zip(rows.tolist(), cols.tolist()))
        assert len(coordinates) == len(values), f"Duplicate stored coordinates in {path}"
        return (shape[0], shape[1]), len(values), coordinates


def test_claim_is_not_promoted_without_source_generator_and_replay() -> None:
    report = _json(EVAL / "DRS_real_data.json")
    audit = report["reproducibility_audit"]

    source_candidates = list(ROOT.rglob(report["source"]["file"]))
    assert not source_candidates, (
        "The source appears in the repository; add source-hash verification and a clean replay "
        "before changing the status to supported."
    )
    assert audit["source_available_in_snapshot"] is False
    assert audit["generator_bound_to_outputs"] is False
    assert audit["replay_receipt"] is None
    assert report["status"] == "REVIEW_REQUIRED"
    assert report["evidence_status"] == "PARTIAL_EVIDENCE"
    assert report["promotion_authority"] == "NONE"
    assert audit["status"] == "BLOCKED"
    assert report["historical_comparison"]["verdict"].startswith("NOT_VERIFIED:")


def test_matrix_bundle_matches_reported_shapes_counts_and_hash_prefixes() -> None:
    report = _json(EVAL / "DRS_real_data.json")
    meta = _json(OUTPUT / "W_sig_meta.json")
    n_roots = int(meta["B_shape"][1])
    artifacts = [
        (
            OUTPUT / "B_real_6236x1642.npz",
            tuple(report["B_real"]["shape"]),
            int(report["B_real"]["nnz"]),
            report["B_real"].get("sha16"),
        ),
        (
            OUTPUT / "W_morph_1642x1642.npz",
            (n_roots, n_roots),
            int(report["W_morph"]["nnz"]),
            report["W_morph"].get("sha16"),
        ),
        (
            OUTPUT / "W_sig_1642x1642.npz",
            (n_roots, n_roots),
            int(meta["W_sig_nnz_directed"]),
            None,
        ),
        (
            OUTPUT / "W_fdr_1642x1642.npz",
            (n_roots, n_roots),
            7458,
            None,
        ),
    ]

    observed: dict[str, tuple[tuple[int, int], int, set[tuple[int, int]]]] = {}
    for path, expected_shape, expected_nnz, sha_prefix in artifacts:
        assert path.is_file(), f"Missing matrix artifact: {path}"
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if sha_prefix:
            assert digest.startswith(sha_prefix), (
                f"SHA-256 prefix mismatch for {path.name}: "
                f"recorded={sha_prefix}, actual={digest}"
            )
        shape, nnz, coordinates = _matrix_facts(path)
        assert shape == expected_shape, f"{path.name}: shape {shape}, expected {expected_shape}"
        assert nnz == expected_nnz, f"{path.name}: stored nnz {nnz}, expected {expected_nnz}"
        observed[path.name] = (shape, nnz, coordinates)

    for filename in ("W_sig_1642x1642.npz", "W_fdr_1642x1642.npz"):
        coordinates = observed[filename][2]
        assert not any(row == col for row, col in coordinates), (
            f"{filename} contains diagonal/self edges"
        )
        assert {(col, row) for row, col in coordinates} == coordinates, (
            f"{filename} is not symmetric; undirected-edge counts cannot be inferred as nnz/2"
        )

    roots = json.loads((OUTPUT / "roots_1642.json").read_text(encoding="utf-8"))
    assert len(roots) == n_roots, f"Expected {n_roots} root labels, got {len(roots)}"
    assert len(set(roots)) == len(roots), "Root labels contain duplicates"
    assert meta["B_nnz"] == report["B_real"]["nnz"]
    assert meta["W_morph_nnz"] == report["W_morph"]["nnz"]
    assert meta["W_sig_nnz_undirected"] * 2 == meta["W_sig_nnz_directed"]
    assert report["W_sig_Holm"]["directed"] == meta["W_sig_nnz_directed"]
    assert report["W_fdr_BH"]["directed"] == 7458
    for path, *_ in artifacts:
        print(f"OBSERVED_SHA256 {path.relative_to(ROOT)} {hashlib.sha256(path.read_bytes()).hexdigest()}")
