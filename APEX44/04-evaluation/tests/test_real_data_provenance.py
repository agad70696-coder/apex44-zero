"""Regression tests for QAC provenance and projection integer overflow."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import scipy.sparse as sp

ROOT = Path(__file__).resolve().parents[3]
RUNNER_PATH = ROOT / "APEX44/03-computation/reproduce_qac_analysis.py"
SPEC = importlib.util.spec_from_file_location("apex44_qac_reproduction", RUNNER_PATH)
assert SPEC is not None and SPEC.loader is not None
runner = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = runner
SPEC.loader.exec_module(runner)

SOURCE = ROOT / "PHASE2_CLEAN/source/quranic-corpus-morphology-0.4.txt"
SOURCE_MANIFEST = ROOT / "PHASE2_CLEAN/source/source_manifest.json"
OUTPUT = ROOT / "APEX44/03-computation/output"
REPORT_PATH = ROOT / "APEX44/04-evaluation/DRS_real_data.json"
META_PATH = OUTPUT / "W_sig_meta.json"


def test_source_manifest_binds_verbatim_qac_v04_bytes() -> None:
    raw = SOURCE.read_bytes()
    manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    digest = hashlib.sha256(raw).hexdigest()
    assert digest == runner.EXPECTED_SOURCE_SHA256
    assert digest == manifest["sha256"]
    assert len(raw) == manifest["bytes"] == 6_309_503
    assert len(raw.splitlines()) == manifest["lines"] == 128_276
    assert b"Copyright (C) 2011 Kais Dukes" in raw[:4096]
    assert b"License: GNU General Public License" in raw[:4096]
    assert b"PLEASE DO NOT REMOVE OR CHANGE THIS COPYRIGHT BLOCK" in raw[:4096]


def test_int8_projection_overflow_regression_is_killed() -> None:
    toy = sp.csr_matrix(np.ones((300, 2), dtype=np.int8))
    legacy_product = (toy.T @ toy).toarray()
    corrected_product = (toy.astype(np.int64).T @ toy.astype(np.int64)).toarray()
    assert int(legacy_product[0, 1]) != 300
    assert int(corrected_product[0, 1]) == 300
    assert corrected_product.dtype == np.int64


def test_committed_corrected_projection_is_wide_nonnegative_and_manifest_bound() -> None:
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    meta = json.loads(META_PATH.read_text(encoding="utf-8"))
    projection = sp.load_npz(OUTPUT / "W_morph_1642x1642.npz").tocsr()
    incidence = sp.load_npz(OUTPUT / "B_real_6236x1642.npz").tocsr()
    roots = json.loads((OUTPUT / "roots_1642.json").read_text(encoding="utf-8"))
    assert incidence.shape == (6236, 1642)
    assert incidence.nnz == 44_431
    assert len(roots) == 1642 and len(set(roots)) == 1642
    assert report["feature_extraction"]["primary_layer"] == "ROOT"
    assert report["feature_extraction"]["typed_feature_layers_pooled"] is False
    assert meta["feature_layer"] == "ROOT-only"
    assert projection.shape == (1642, 1642)
    assert projection.dtype == np.dtype(np.int64)
    assert projection.nnz == report["W_morph"]["nnz"] == meta["W_morph_nnz"]
    assert int(projection.data.min()) > 0
    assert int(projection.data.max()) == report["W_morph"]["max_common_verses"]
    assert (projection != projection.T).nnz == 0
    assert np.count_nonzero(projection.diagonal()) == 0
    assert report["status"] == "REVIEW_REQUIRED"
    assert report["evidence_status"] == "REPRODUCED_SCOPED"
    assert report["promotion_authority"] == "NONE"
    hashes = report["artifact_sha256"]
    assert hashes == meta["artifact_sha256"]
    for relative, digest in hashes.items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest
