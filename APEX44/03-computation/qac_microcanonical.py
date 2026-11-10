#!/usr/bin/env python3
"""APEX44/QAC microcanonical switch sampler (research implementation).

The Markov kernel uses symmetric 2x2 switches on a simple bipartite graph.
It preserves every row and column degree exactly. A valid kernel is not the
same as a mixed chain: the module reports diagnostics and never silently
promotes finite-run samples to calibrated p-values.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import importlib.util
import math
import platform
import re
import sys
import time
from collections import Counter, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import scipy
import scipy.sparse as sp
from scipy.optimize import root
from scipy.special import expit, ndtri, rel_entr, xlogy
from scipy.stats import rankdata

SCHEMA_VERSION = "apex44-qac-microcanonical-v0.1.1"
EXPECTED_QAC_SHA256 = "a1d12923815341face765083805d2148ed2d9f5cc3f7d6665219d887675d8c46"
EXPECTED_QAC_SHAPE = (6236, 1642)
EXPECTED_QAC_NNZ = 44431
DEFAULT_DEGREE_RESIDUAL_LIMIT = 1e-3


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_csr_hash(matrix: sp.spmatrix) -> str:
    value = sp.csr_matrix(matrix, dtype=np.int8)
    value.sum_duplicates()
    value.eliminate_zeros()
    value.sort_indices()
    digest = hashlib.sha256()
    digest.update(np.asarray(value.shape, dtype="<i8").tobytes())
    digest.update(np.asarray(value.indptr, dtype="<i8").tobytes())
    digest.update(np.asarray(value.indices, dtype="<i8").tobytes())
    digest.update(np.asarray(value.data, dtype="i1").tobytes())
    return digest.hexdigest()


def validate_binary_incidence(matrix: sp.spmatrix) -> sp.csr_matrix:
    """Canonicalize a sparse incidence matrix, rejecting duplicates/non-binary data."""
    if not sp.issparse(matrix):
        raise TypeError("INCIDENCE_MUST_BE_SPARSE")
    coo = sp.coo_matrix(matrix, dtype=np.float64)
    if coo.nnz:
        if not np.isfinite(coo.data).all() or not np.isin(coo.data, (0.0, 1.0)).all():
            raise ValueError("INCIDENCE_MUST_BE_FINITE_BINARY")
        coordinates = np.column_stack((coo.row, coo.col))
        if len(np.unique(coordinates, axis=0)) != len(coordinates):
            raise ValueError("DUPLICATE_INCIDENCE_COORDINATE")
    result = coo.tocsr().astype(np.int8)
    result.sum_duplicates()
    result.eliminate_zeros()
    result.sort_indices()
    return result


@dataclass(frozen=True)
class DegreeClasses:
    row_values: np.ndarray
    row_inverse: np.ndarray
    row_counts: np.ndarray
    col_values: np.ndarray
    col_inverse: np.ndarray
    col_counts: np.ndarray
    row_degrees: np.ndarray
    col_degrees: np.ndarray


def make_degree_classes(matrix: sp.spmatrix) -> DegreeClasses:
    value = validate_binary_incidence(matrix)
    row_degrees = np.asarray(value.sum(axis=1)).ravel().astype(np.int64)
    col_degrees = np.asarray(value.sum(axis=0)).ravel().astype(np.int64)
    row_values, row_inverse, row_counts = np.unique(
        row_degrees, return_inverse=True, return_counts=True
    )
    col_values, col_inverse, col_counts = np.unique(
        col_degrees, return_inverse=True, return_counts=True
    )
    return DegreeClasses(
        row_values=row_values.astype(np.int64),
        row_inverse=row_inverse.astype(np.int64),
        row_counts=row_counts.astype(np.int64),
        col_values=col_values.astype(np.int64),
        col_inverse=col_inverse.astype(np.int64),
        col_counts=col_counts.astype(np.int64),
        row_degrees=row_degrees,
        col_degrees=col_degrees,
    )


def validate_degree_classes_against_matrix(
    matrix: sp.spmatrix, classes: DegreeClasses
) -> None:
    """Reject degree-class metadata that does not describe this exact matrix."""
    value = validate_binary_incidence(matrix)
    row_degrees = np.asarray(value.sum(axis=1)).ravel().astype(np.int64)
    col_degrees = np.asarray(value.sum(axis=0)).ravel().astype(np.int64)
    if classes.row_degrees.shape != row_degrees.shape or classes.col_degrees.shape != col_degrees.shape:
        raise ValueError("DEGREE_CLASS_DEGREE_VECTOR_SHAPE_MISMATCH")
    if not np.array_equal(classes.row_degrees, row_degrees):
        raise ValueError("DEGREE_CLASS_ROW_SEQUENCE_MISMATCH")
    if not np.array_equal(classes.col_degrees, col_degrees):
        raise ValueError("DEGREE_CLASS_COLUMN_SEQUENCE_MISMATCH")
    if classes.row_inverse.shape != row_degrees.shape or classes.col_inverse.shape != col_degrees.shape:
        raise ValueError("DEGREE_CLASS_INDEX_SHAPE_MISMATCH")
    if (
        classes.row_inverse.size
        and (classes.row_inverse.min() < 0 or classes.row_inverse.max() >= len(classes.row_values))
    ):
        raise ValueError("DEGREE_CLASS_ROW_INDEX_OUT_OF_RANGE")
    if (
        classes.col_inverse.size
        and (classes.col_inverse.min() < 0 or classes.col_inverse.max() >= len(classes.col_values))
    ):
        raise ValueError("DEGREE_CLASS_COLUMN_INDEX_OUT_OF_RANGE")
    if not np.array_equal(classes.row_values[classes.row_inverse], row_degrees):
        raise ValueError("DEGREE_CLASS_ROW_MAPPING_MISMATCH")
    if not np.array_equal(classes.col_values[classes.col_inverse], col_degrees):
        raise ValueError("DEGREE_CLASS_COLUMN_MAPPING_MISMATCH")
    if not np.array_equal(np.bincount(classes.row_inverse, minlength=len(classes.row_values)), classes.row_counts):
        raise ValueError("DEGREE_CLASS_ROW_COUNTS_MISMATCH")
    if not np.array_equal(np.bincount(classes.col_inverse, minlength=len(classes.col_values)), classes.col_counts):
        raise ValueError("DEGREE_CLASS_COLUMN_COUNTS_MISMATCH")


def degree_sequence_rapid_mixing_screen(classes: DegreeClasses) -> dict[str, Any]:
    """Check two published sufficient-condition screens for bipartite switch mixing.

    A failed sufficient condition means only that this theorem does not certify
    rapid mixing for the sequence. It is not evidence that the chain mixes
    slowly. The screen follows Theorems 2 and 3 of Erdős et al. (2018), PLOS ONE
    13(8), e0201995, DOI 10.1371/journal.pone.0201995.
    """
    row = np.asarray(classes.row_degrees, dtype=np.int64)
    col = np.asarray(classes.col_degrees, dtype=np.int64)
    if row.size == 0 or col.size == 0:
        raise ValueError("EMPTY_BIPARTITE_DEGREE_SEQUENCE")
    if np.any(row <= 0) or np.any(col <= 0):
        return {
            "status": "NOT_APPLICABLE_ISOLATES_PRESENT",
            "rapid_mixing_certified": False,
            "interpretation": "Sufficient-condition screen was not evaluated with isolated vertices present.",
        }
    edge_count_row = int(row.sum())
    edge_count_col = int(col.sum())
    if edge_count_row != edge_count_col:
        raise ValueError("BIPARTITE_DEGREE_SUM_MISMATCH")
    n_rows, n_cols = int(row.size), int(col.size)
    delta = int(max(row.max(), col.max()))

    theorem2_bound = math.sqrt(edge_count_row / 2.0)
    theorem2_applicable = bool(2 <= delta <= theorem2_bound)

    # Theorem 3 notation: c-bounds apply to vertices in V (columns/roots),
    # d-bounds apply to vertices in U (rows/verses).
    c1, c2 = int(col.min()), int(col.max())
    d1, d2 = int(row.min()), int(row.max())
    theorem3_bounds_valid = bool(c2 < n_rows and d2 < n_cols)
    theorem3_lhs = int((c2 - c1 - 1) * (d2 - d1 - 1))
    theorem3_rhs = int(max(c1 * (n_cols - d2), d1 * (n_rows - c2)))
    theorem3_applicable = bool(theorem3_bounds_valid and theorem3_lhs <= theorem3_rhs)

    if edge_count_row >= 2 and n_rows >= 2 and n_cols >= 2:
        edge_selector_probability = 1.0 / (edge_count_row * (edge_count_row - 1))
        vertex_selector_probability = 1.0 / (
            2.0 * math.comb(n_rows, 2) * math.comb(n_cols, 2)
        )
        kernel_rate_ratio = edge_selector_probability / vertex_selector_probability
    else:
        edge_selector_probability = None
        vertex_selector_probability = None
        kernel_rate_ratio = None

    return {
        "status": "AT_LEAST_ONE_SUFFICIENT_CONDITION_APPLIES" if theorem2_applicable or theorem3_applicable else "NO_SCREENED_RAPID_MIXING_THEOREM_APPLIES",
        "rapid_mixing_certified_by_screened_results": bool(theorem2_applicable or theorem3_applicable),
        "theorem_2": {
            "reference": "Erdos et al. 2018, PLOS ONE 13(8), e0201995, Theorem 2",
            "condition": "2 <= Delta <= sqrt(|E|/2)",
            "delta_max_degree": delta,
            "edge_count": edge_count_row,
            "upper_bound": theorem2_bound,
            "applicable": theorem2_applicable,
        },
        "kernel_rate_comparison": {
            "reference_kernel": "Erdos et al. 2018 Theorem 2/3 chain: lazy half-hold, then uniform choice of a row-pair and column-pair",
            "implemented_kernel": "lazy half-hold, then uniform choice of two distinct edge slots",
            "reference_switch_probability": vertex_selector_probability,
            "implemented_switch_probability": edge_selector_probability,
            "implemented_to_reference_off_diagonal_rate_ratio": kernel_rate_ratio,
            "scope": "For each valid 2-switch the move probabilities are state-independent constants; the kernels differ by a scalar factor on off-diagonal moves and a compensating self-loop. This reports the discrete-time rate comparison; it does not itself certify mixing for a sequence outside the theorem hypotheses.",
        },
        "theorem_3": {
            "reference": "Erdos et al. 2018, PLOS ONE 13(8), e0201995, Theorem 3",
            "column_degree_bounds_c1_c2": [c1, c2],
            "row_degree_bounds_d1_d2": [d1, d2],
            "vertex_side_bounds_valid": theorem3_bounds_valid,
            "inequality_lhs": theorem3_lhs,
            "inequality_rhs": theorem3_rhs,
            "condition": "(c2-c1-1)*(d2-d1-1) <= max(c1*(n_cols-d2), d1*(n_rows-c2))",
            "applicable": theorem3_applicable,
        },
        "interpretation": (
            "Applicable sufficient condition: theorem can certify rapid mixing under its stated assumptions."
            if theorem2_applicable or theorem3_applicable
            else "No screened sufficient theorem certifies rapid mixing for this degree sequence. This does NOT establish slow mixing; empirical convergence diagnostics and/or other theory remain necessary."
        ),
    }


@dataclass(frozen=True)
class BiCMFit:
    probabilities: np.ndarray
    max_abs_row_residual: float
    max_abs_col_residual: float
    optimizer_success: bool
    optimizer_message: str
    function_evaluations: int
    parameter_count: int
    accepted: bool


def fit_degree_class_bicm(
    classes: DegreeClasses,
    *,
    xtol: float = 1e-10,
    maxfev: int = 5000,
    residual_limit: float = DEFAULT_DEGREE_RESIDUAL_LIMIT,
) -> BiCMFit:
    """Fit canonical BiCM in equal-degree class coordinates with analytic Jacobian.

    Isolates may be present in DegreeClasses, but they are excluded from the
    positive-degree fit and assigned no probability class. The active network
    must be nonempty and strictly interior (no degree at the opposite-side
    cardinality boundary).
    """
    if xtol <= 0 or maxfev < 1 or residual_limit <= 0:
        raise ValueError("INVALID_BICM_SOLVER_CONFIGURATION")
    if np.any(classes.row_values <= 0) or np.any(classes.col_values <= 0):
        raise ValueError("BICM_FIT_REQUIRES_ISOLATES_REMOVED")
    rv = classes.row_values.astype(np.float64)
    cv = classes.col_values.astype(np.float64)
    rc = classes.row_counts.astype(np.float64)
    cc = classes.col_counts.astype(np.float64)
    active_rows = int(classes.row_degrees.size)
    active_cols = int(classes.col_degrees.size)
    if np.any(rv >= active_cols) or np.any(cv >= active_rows):
        raise ValueError("BICM_DEGREE_SEQUENCE_ON_FEASIBILITY_BOUNDARY")
    edge_count = float(np.dot(rv, rc))
    if not math.isclose(edge_count, float(np.dot(cv, cc)), rel_tol=0.0, abs_tol=0.0):
        raise ValueError("BICM_DEGREE_SUM_MISMATCH")
    n_rows, n_cols = len(rv), len(cv)
    parameter_count = n_rows + n_cols - 1
    if parameter_count > 1200:
        raise ValueError(f"BICM_CLASS_DIMENSION_TOO_LARGE:{parameter_count}")

    # Fix final column-class log-fitness to zero to remove the additive gauge.
    beta0 = np.log(cv)
    alpha0 = np.log(rv / edge_count)
    gauge = float(beta0[-1])
    initial = np.concatenate((alpha0 + gauge, (beta0 - gauge)[:-1]))

    def probabilities(theta: np.ndarray) -> np.ndarray:
        alpha = theta[:n_rows]
        beta = np.concatenate((theta[n_rows:], np.zeros(1)))
        return expit(alpha[:, None] + beta[None, :])

    def equations(theta: np.ndarray) -> np.ndarray:
        p = probabilities(theta)
        row_residuals = p @ cc - rv
        col_residuals = rc @ p[:, :-1] - cv[:-1]
        return np.concatenate((row_residuals, col_residuals))

    def jacobian(theta: np.ndarray) -> np.ndarray:
        p = probabilities(theta)
        weights = p * (1.0 - p)
        jac = np.zeros((parameter_count, parameter_count), dtype=np.float64)
        jac[:n_rows, :n_rows] = np.diag(weights @ cc)
        jac[:n_rows, n_rows:] = weights[:, :-1] * cc[:-1][None, :]
        jac[n_rows:, :n_rows] = (rc[:, None] * weights[:, :-1]).T
        jac[n_rows:, n_rows:] = np.diag(rc @ weights[:, :-1])
        return jac

    result = root(
        equations,
        initial,
        jac=jacobian,
        method="hybr",
        options={"xtol": xtol, "maxfev": maxfev},
    )
    finite = bool(np.all(np.isfinite(result.x)))
    if finite:
        p_active = probabilities(result.x)
        row_residuals = p_active @ cc - rv
        col_residuals = rc @ p_active - cv
        finite = bool(
            np.isfinite(p_active).all()
            and np.isfinite(row_residuals).all()
            and np.isfinite(col_residuals).all()
        )
    else:
        p_active = np.full((n_rows, n_cols), np.nan)
        row_residuals = np.full(n_rows, np.nan)
        col_residuals = np.full(n_cols, np.nan)
    row_error = float(np.max(np.abs(row_residuals))) if finite else math.inf
    col_error = float(np.max(np.abs(col_residuals))) if finite else math.inf
    accepted = bool(
        result.success
        and finite
        and np.all(p_active > 0.0)
        and np.all(p_active < 1.0)
        and max(row_error, col_error) <= residual_limit
    )
    return BiCMFit(
        probabilities=p_active,
        max_abs_row_residual=row_error,
        max_abs_col_residual=col_error,
        optimizer_success=bool(result.success),
        optimizer_message=str(result.message),
        function_evaluations=int(result.nfev),
        parameter_count=parameter_count,
        accepted=accepted,
    )


def _binomial_deviance(observed: np.ndarray, trials: np.ndarray, probability: np.ndarray) -> float:
    x = np.asarray(observed, dtype=np.float64)
    n = np.broadcast_to(np.asarray(trials, dtype=np.float64), x.shape)
    p = np.broadcast_to(np.asarray(probability, dtype=np.float64), x.shape)
    if np.any((x < 0) | (x > n)) or np.any((p <= 0) | (p >= 1)):
        raise ValueError("INVALID_BINOMIAL_DEVIANCE_INPUT")
    expected = n * p
    expected_complement = n * (1.0 - p)
    value = float(
        2.0
        * (
            xlogy(x, x / expected)
            + xlogy(n - x, (n - x) / expected_complement)
        ).sum()
    )
    if value < -1e-10:
        raise FloatingPointError(f"NEGATIVE_BINOMIAL_DEVIANCE:{value}")
    return max(0.0, value)


def rebuild_class_counts(
    matrix: sp.spmatrix, classes: DegreeClasses
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    value = validate_binary_incidence(matrix)
    validate_degree_classes_against_matrix(value, classes)
    coo = value.tocoo(copy=False)
    X = np.zeros((len(classes.row_values), value.shape[1]), dtype=np.int64)
    Y = np.zeros((value.shape[0], len(classes.col_values)), dtype=np.int64)
    E = np.zeros((len(classes.row_values), len(classes.col_values)), dtype=np.int64)
    np.add.at(X, (classes.row_inverse[coo.row], coo.col), 1)
    np.add.at(Y, (coo.row, classes.col_inverse[coo.col]), 1)
    np.add.at(E, (classes.row_inverse[coo.row], classes.col_inverse[coo.col]), 1)
    return X, Y, E


def identity_contributions(
    X: np.ndarray, Y: np.ndarray, E: np.ndarray, classes: DegreeClasses
) -> tuple[np.ndarray, np.ndarray]:
    """Return per-root and per-verse direct KL contributions (without BiCM P)."""
    row_counts = classes.row_counts.astype(np.float64)
    col_counts = classes.col_counts.astype(np.float64)
    trials = row_counts[:, None] * col_counts[None, :]
    block_rate = E.astype(np.float64) / trials
    root_rate = X.astype(np.float64) / row_counts[:, None]
    verse_rate = Y.astype(np.float64) / col_counts[None, :]
    root_reference = block_rate[:, classes.col_inverse]
    verse_reference = block_rate[classes.row_inverse, :]
    root_cells = 2.0 * row_counts[:, None] * (
        rel_entr(root_rate, root_reference)
        + rel_entr(1.0 - root_rate, 1.0 - root_reference)
    )
    verse_cells = 2.0 * col_counts[None, :] * (
        rel_entr(verse_rate, verse_reference)
        + rel_entr(1.0 - verse_rate, 1.0 - verse_reference)
    )
    if not np.isfinite(root_cells).all() or not np.isfinite(verse_cells).all():
        raise FloatingPointError("NONFINITE_HETEROGENEITY_STATISTIC")
    return root_cells.sum(axis=0), verse_cells.sum(axis=1)


def compute_statistics(
    X: np.ndarray,
    Y: np.ndarray,
    E: np.ndarray,
    classes: DegreeClasses,
    bicm_probabilities: np.ndarray,
) -> dict[str, float]:
    """Compute block deviance and direct P-free heterogeneity statistics."""
    row_counts = classes.row_counts.astype(np.float64)
    col_counts = classes.col_counts.astype(np.float64)
    trials = row_counts[:, None] * col_counts[None, :]
    block_rate = E.astype(np.float64) / trials
    root_rate = X.astype(np.float64) / row_counts[:, None]
    verse_rate = Y.astype(np.float64) / col_counts[None, :]
    root_reference = block_rate[:, classes.col_inverse]
    verse_reference = block_rate[classes.row_inverse, :]
    root_cells = 2.0 * row_counts[:, None] * (
        rel_entr(root_rate, root_reference)
        + rel_entr(1.0 - root_rate, 1.0 - root_reference)
    )
    verse_cells = 2.0 * col_counts[None, :] * (
        rel_entr(verse_rate, verse_reference)
        + rel_entr(1.0 - verse_rate, 1.0 - verse_reference)
    )
    if not np.isfinite(root_cells).all() or not np.isfinite(verse_cells).all():
        raise FloatingPointError("NONFINITE_HETEROGENEITY_STATISTIC")
    root_identity = root_cells.sum(axis=0)
    verse_identity = verse_cells.sum(axis=1)
    non_singleton = classes.col_counts > 1
    return {
        "block_deviance": _binomial_deviance(E, trials, bicm_probabilities),
        "h_root": float(root_cells.sum()),
        "h_verse": float(verse_cells.sum()),
        "h_verse_non_singleton_root_classes": float(verse_cells[:, non_singleton].sum()),
        "h_verse_singleton_root_classes": float(verse_cells[:, ~non_singleton].sum()),
        "max_root_contribution": float(root_identity.max(initial=0.0)),
        "max_verse_contribution": float(verse_identity.max(initial=0.0)),
    }


class DegreePreservingSwitchChain:
    """Lazy, symmetric 2x2 switch chain for a simple bipartite graph.

    Proposal: choose two distinct edge slots uniformly, then cross-switch the
    endpoints if the rows/columns differ and neither proposed edge exists.
    All invalid proposals are self-loops. A switch and its inverse have the
    same proposal probability, so detailed balance holds for the uniform
    distribution. The 2-switch graph of realizations of a bipartite degree
    sequence is connected. An explicit 1/2 lazy hold guarantees aperiodicity
    for every valid degree sequence; finite-run mixing remains separate.
    """

    def __init__(
        self,
        incidence: sp.spmatrix,
        classes: DegreeClasses | None = None,
        *,
        seed: int,
    ) -> None:
        self.matrix = validate_binary_incidence(incidence)
        self.n_rows, self.n_cols = self.matrix.shape
        if self.matrix.nnz < 2:
            raise ValueError("SWITCH_CHAIN_REQUIRES_AT_LEAST_TWO_EDGES")
        coo = self.matrix.tocoo(copy=False)
        self.rows = coo.row.astype(np.int64, copy=True)
        self.cols = coo.col.astype(np.int64, copy=True)
        self.edge_count = int(self.matrix.nnz)
        self.initial_row_degrees = np.asarray(self.matrix.sum(axis=1)).ravel().astype(np.int64)
        self.initial_col_degrees = np.asarray(self.matrix.sum(axis=0)).ravel().astype(np.int64)
        self.classes = classes or make_degree_classes(self.matrix)
        validate_degree_classes_against_matrix(self.matrix, self.classes)
        self.row_neighbors = [
            set(self.matrix.indices[self.matrix.indptr[i] : self.matrix.indptr[i + 1]].tolist())
            for i in range(self.n_rows)
        ]
        self.X, self.Y, self.E = rebuild_class_counts(self.matrix, self.classes)
        self.rng = np.random.default_rng(seed)
        self.seed = int(seed)
        self.proposals = 0
        self.accepted = 0
        self.lazy_holds = 0
        self.reject_same_row = 0
        self.reject_same_column = 0
        self.reject_occupied_cross_edge = 0
        self._original_edge_ids = set((self.rows * self.n_cols + self.cols).tolist())

    @property
    def acceptance_rate(self) -> float:
        return self.accepted / self.proposals if self.proposals else 0.0

    def step(self) -> bool:
        """Make one proposal; return whether the graph changed."""
        self.proposals += 1
        # Explicit laziness gives every state a self-loop probability >= 1/2,
        # including degree sequences such as a perfect matching where every
        # edge-pair switch might otherwise be accepted.
        if self.rng.random() < 0.5:
            self.lazy_holds += 1
            return False
        p = int(self.rng.integers(self.edge_count))
        q = int(self.rng.integers(self.edge_count - 1))
        if q >= p:
            q += 1
        i, k = int(self.rows[p]), int(self.rows[q])
        j, ell = int(self.cols[p]), int(self.cols[q])

        if i == k:
            self.reject_same_row += 1
            return False
        if j == ell:
            self.reject_same_column += 1
            return False
        if ell in self.row_neighbors[i] or j in self.row_neighbors[k]:
            self.reject_occupied_cross_edge += 1
            return False

        ai = int(self.classes.row_inverse[i])
        ak = int(self.classes.row_inverse[k])
        bj = int(self.classes.col_inverse[j])
        bell = int(self.classes.col_inverse[ell])

        self.row_neighbors[i].remove(j)
        self.row_neighbors[i].add(ell)
        self.row_neighbors[k].remove(ell)
        self.row_neighbors[k].add(j)
        self.cols[p], self.cols[q] = ell, j

        self.X[ai, j] -= 1
        self.X[ai, ell] += 1
        self.X[ak, ell] -= 1
        self.X[ak, j] += 1
        self.Y[i, bj] -= 1
        self.Y[i, bell] += 1
        self.Y[k, bell] -= 1
        self.Y[k, bj] += 1
        self.E[ai, bj] -= 1
        self.E[ai, bell] += 1
        self.E[ak, bell] -= 1
        self.E[ak, bj] += 1
        self.accepted += 1
        return True

    def edge_overlap_with_original(self) -> float:
        current = set((self.rows * self.n_cols + self.cols).tolist())
        return len(current & self._original_edge_ids) / self.edge_count

    def statistics(self, probabilities: np.ndarray) -> dict[str, float]:
        return compute_statistics(self.X, self.Y, self.E, self.classes, probabilities)

    def advance(self, proposals: int, *, validate_every: int = 0) -> None:
        """Advance without retaining samples; useful for independent chain starts."""
        if proposals < 0 or validate_every < 0:
            raise ValueError("INVALID_ADVANCE_CONFIGURATION")
        for local_step in range(1, proposals + 1):
            self.step()
            if validate_every and local_step % validate_every == 0:
                self.assert_invariants()
        self.assert_invariants()

    def run_schedule(
        self,
        *,
        burn_in: int,
        samples: int,
        thin: int,
        probabilities: np.ndarray,
        validate_every: int = 0,
    ) -> list[dict[str, float | int]]:
        if burn_in < 0 or samples < 1 or thin < 1 or validate_every < 0:
            raise ValueError("INVALID_CHAIN_SCHEDULE")
        retained: list[dict[str, float | int]] = []
        total = burn_in + samples * thin
        for local_step in range(1, total + 1):
            self.step()
            if validate_every and local_step % validate_every == 0:
                self.assert_invariants()
            if local_step > burn_in and (local_step - burn_in) % thin == 0:
                retained.append({
                    "step": self.proposals,
                    **self.statistics(probabilities),
                    "edge_overlap": self.edge_overlap_with_original(),
                })
        self.assert_invariants()
        if len(retained) != samples:
            raise RuntimeError("RETAINED_SAMPLE_COUNT_MISMATCH")
        return retained

    def to_csr(self) -> sp.csr_matrix:
        value = sp.coo_matrix(
            (np.ones(self.edge_count, dtype=np.int8), (self.rows, self.cols)),
            shape=(self.n_rows, self.n_cols),
        ).tocsr()
        value.sum_duplicates()
        value.eliminate_zeros()
        value.sort_indices()
        return value

    def assert_invariants(self) -> None:
        if not np.array_equal(np.bincount(self.rows, minlength=self.n_rows), self.initial_row_degrees):
            raise RuntimeError("ROW_DEGREE_INVARIANT_BROKEN")
        if not np.array_equal(np.bincount(self.cols, minlength=self.n_cols), self.initial_col_degrees):
            raise RuntimeError("COLUMN_DEGREE_INVARIANT_BROKEN")
        edge_ids = self.rows * self.n_cols + self.cols
        if len(np.unique(edge_ids)) != self.edge_count:
            raise RuntimeError("DUPLICATE_EDGE_INVARIANT_BROKEN")
        rebuilt_x, rebuilt_y, rebuilt_e = rebuild_class_counts(self.to_csr(), self.classes)
        if not np.array_equal(rebuilt_x, self.X):
            raise RuntimeError("ROOT_CLASS_COUNTER_INVARIANT_BROKEN")
        if not np.array_equal(rebuilt_y, self.Y):
            raise RuntimeError("VERSE_CLASS_COUNTER_INVARIANT_BROKEN")
        if not np.array_equal(rebuilt_e, self.E):
            raise RuntimeError("BLOCK_COUNTER_INVARIANT_BROKEN")
        rebuilt_matrix = self.to_csr()
        for row, neighbors in enumerate(self.row_neighbors):
            start, end = rebuilt_matrix.indptr[row], rebuilt_matrix.indptr[row + 1]
            actual = set(rebuilt_matrix.indices[start:end].tolist())
            if actual != neighbors:
                raise RuntimeError("ROW_NEIGHBOR_INDEX_INVARIANT_BROKEN")


def _basic_rhat(values: np.ndarray) -> float:
    m, n = values.shape
    within = float(values.var(axis=1, ddof=1).mean())
    if within == 0.0:
        return 1.0 if np.all(values == values.flat[0]) else math.inf
    between = n * float(values.mean(axis=1).var(ddof=1))
    variance_hat = ((n - 1) / n) * within + between / n
    return float(math.sqrt(max(variance_hat / within, 0.0)))


def split_rhat(chains: np.ndarray) -> float:
    """Rank-normalized and folded split-Rhat (Vehtari-style screening form)."""
    values = np.asarray(chains, dtype=np.float64)
    if values.ndim != 2 or values.shape[0] < 2 or values.shape[1] < 8:
        return math.inf
    half = values.shape[1] // 2
    split = np.concatenate((values[:, :half], values[:, -half:]), axis=0)
    if not np.isfinite(split).all():
        return math.inf

    def rank_normalize(data: np.ndarray) -> np.ndarray:
        flat = data.ravel()
        ranks = rankdata(flat, method="average")
        transformed = ndtri((ranks - 0.375) / (len(flat) + 0.25))
        return transformed.reshape(data.shape)

    ranked = rank_normalize(split)
    folded = rank_normalize(np.abs(split - np.median(split)))
    return max(_basic_rhat(ranked), _basic_rhat(folded))


def ess_initial_positive_sequence(chains: np.ndarray, max_lag: int = 1000) -> float:
    """Geyer-style paired initial-positive/monotone sequence ESS approximation."""
    values = np.asarray(chains, dtype=np.float64)
    if values.ndim != 2 or values.shape[0] < 2 or values.shape[1] < 4:
        return 0.0
    m, n = values.shape
    centered = values - values.mean(axis=1, keepdims=True)
    variances = np.mean(centered * centered, axis=1)
    if np.all(variances == 0.0):
        return float(m * n)
    if np.any(variances == 0.0):
        return 0.0
    limit = min(n - 1, max_lag)
    rho = np.ones(limit + 1, dtype=np.float64)
    for lag in range(1, limit + 1):
        autocorrelation = np.mean(centered[:, :-lag] * centered[:, lag:], axis=1) / variances
        rho[lag] = float(np.mean(autocorrelation))
    pair_sums: list[float] = []
    for lag in range(0, limit, 2):
        pair = float(rho[lag] + rho[lag + 1])
        if pair <= 0.0:
            break
        if pair_sums:
            pair = min(pair, pair_sums[-1])
        pair_sums.append(pair)
    tau = max(1.0, -1.0 + 2.0 * sum(pair_sums))
    return float(min(m * n, (m * n) / tau))


def mixing_diagnostics(
    chain_records: list[list[dict[str, float | int]]],
    *,
    rhat_max: float = 1.01,
    ess_min: float = 400.0,
    mcse_over_sd_max: float = 0.05,
) -> dict[str, Any]:
    if len(chain_records) < 2 or not chain_records:
        return {"status": "INSUFFICIENT_CHAINS", "statistics": {}}
    common = min(len(record) for record in chain_records)
    if common < 50:
        return {"status": "INSUFFICIENT_RETAINED_SAMPLES", "samples_per_chain": common, "minimum_per_chain": 50, "statistics": {}}
    names = (
        "block_deviance", "h_root", "h_verse",
        "h_verse_non_singleton_root_classes",
        "h_verse_singleton_root_classes",
        "max_root_contribution", "max_verse_contribution", "edge_overlap",
    )
    summary: dict[str, Any] = {}
    passed = True
    total_retained_draws = len(chain_records) * common
    for name in names:
        array = np.asarray([[float(item[name]) for item in row[:common]] for row in chain_records])
        rhat = split_rhat(array)
        ess = ess_initial_positive_sequence(array)
        pooled_sd = float(array.std(ddof=1))
        mcse = pooled_sd / math.sqrt(ess) if ess > 0 else math.inf
        relative_mcse = mcse / pooled_sd if pooled_sd > 0 else (0.0 if math.isfinite(mcse) else math.inf)
        ok = math.isfinite(rhat) and rhat <= rhat_max and ess >= ess_min and relative_mcse <= mcse_over_sd_max
        passed = passed and ok
        summary[name] = {
            "split_rhat_rank_normalized_folded": rhat,
            "ess_initial_positive_sequence": ess,
            "pooled_sd": pooled_sd,
            "mcse": mcse,
            "mcse_over_sd": relative_mcse,
            "screen_pass": bool(ok),
        }
    return {
        "status": "SCREEN_PASS_NOT_PROOF" if passed else "MIXING_NOT_ESTABLISHED",
        "chain_count": len(chain_records),
        "samples_per_chain": common,
        "total_retained_draws": total_retained_draws,
        "ess_threshold_attainable_at_absolute_independence": bool(total_retained_draws >= ess_min),
        "max_possible_ess": total_retained_draws,
        "thresholds": {
            "split_rhat_rank_normalized_folded_max": rhat_max,
            "ess_min": ess_min,
            "mcse_over_sd_max": mcse_over_sd_max,
        },
        "statistics": summary,
        "warning": "These finite-chain diagnostics do not prove stationarity, rapid mixing, or a calibrated test.",
    }


@dataclass(frozen=True)
class QACBuild:
    incidence: sp.csr_matrix
    roots: tuple[str, ...]
    verse_keys: tuple[tuple[int, int], ...]
    active_verse_keys: tuple[tuple[int, int], ...]
    active_verse_indices: tuple[int, ...]
    source_sha256: str
    root_order_sha256: str
    verse_order_sha256: str
    matrix_sha256: str
    pipeline_sha256: str


def build_qac_incidence(
    repo_root: Path,
    *,
    expected_source_sha256: str = EXPECTED_QAC_SHA256,
    source_relative_path: str = "PHASE2_CLEAN/source/quranic-corpus-morphology-0.4.txt",
) -> QACBuild:
    """Rebuild ROOT-only QAC matrix, retain (surah,ayah), verify reference parity."""
    source_path = repo_root / source_relative_path
    pipeline_path = repo_root / "APEX44/03-computation/reproduce_qac_analysis.py"
    if not source_path.is_file() or not pipeline_path.is_file():
        raise FileNotFoundError("QAC_SOURCE_OR_REFERENCE_PIPELINE_MISSING")
    raw = source_path.read_bytes()
    source_sha = sha256_bytes(raw)
    if source_sha != expected_source_sha256:
        raise ValueError(f"QAC_SOURCE_SHA256_MISMATCH:{source_sha}")
    source_text = raw.decode("utf-8")
    normalized_lines = [line.strip() for line in source_text.splitlines()]
    lines = [
        line for line in normalized_lines
        if line and not line.startswith("#") and not line.startswith("LOCATION")
    ]
    location_pattern = re.compile(r"\(?(\d+):(\d+):\d+:\d+\)?")
    root_pattern = re.compile(r"ROOT:([^\s|]+)")
    verse_to_index: dict[tuple[int, int], int] = {}
    triples: list[tuple[int, str]] = []
    for line in lines:
        parts = line.split("\t")
        match = location_pattern.search(parts[0])
        if match is None:
            continue
        verse_key = (int(match.group(1)), int(match.group(2)))
        if verse_key not in verse_to_index:
            verse_to_index[verse_key] = len(verse_to_index)
        feature_match = root_pattern.search(" ".join(parts[1:]))
        if feature_match:
            feature = feature_match.group(1)
            if feature and feature != "UNK":
                triples.append((verse_to_index[verse_key], feature))
    counts = Counter(feature for _, feature in triples)
    roots = tuple(feature for feature, _ in counts.most_common(1642))
    root_to_index = {feature: i for i, feature in enumerate(roots)}
    rows: list[int] = []
    cols: list[int] = []
    for row, feature in triples:
        col = root_to_index.get(feature)
        if col is not None:
            rows.append(row)
            cols.append(col)
    matrix = sp.coo_matrix(
        (np.ones(len(rows), dtype=np.int8), (rows, cols)),
        shape=(len(verse_to_index), len(roots)),
    ).tocsr()
    matrix.sum_duplicates()
    matrix.data[:] = 1
    matrix.eliminate_zeros()
    matrix.sort_indices()
    if matrix.shape != EXPECTED_QAC_SHAPE or matrix.nnz != EXPECTED_QAC_NNZ:
        raise ValueError(f"QAC_MATRIX_CONTRACT_MISMATCH:{matrix.shape}:{matrix.nnz}")

    sys.path.insert(0, str(pipeline_path.parent.resolve()))
    import reproduce_qac_analysis as reference
    if Path(reference.__file__).resolve() != pipeline_path.resolve():
        raise RuntimeError("REFERENCE_PIPELINE_IMPORT_PATH_MISMATCH")
    ref_raw, ref_sha, _ = reference.read_and_validate_source()
    ref_matrix, ref_roots = reference.build_biadjacency(ref_raw.decode("utf-8"))
    ref_matrix = validate_binary_incidence(ref_matrix)
    if ref_sha != source_sha or tuple(ref_roots) != roots or (ref_matrix != matrix).nnz:
        raise ValueError("QAC_REFERENCE_PIPELINE_RECONCILIATION_FAILED")

    all_verse_keys = tuple(verse_to_index.keys())
    active_mask = np.asarray(matrix.sum(axis=1)).ravel() > 0
    active_indices = tuple(int(i) for i in np.flatnonzero(active_mask))
    active_keys = tuple(all_verse_keys[i] for i in active_indices)
    root_blob = json.dumps(roots, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    verse_blob = json.dumps(all_verse_keys, separators=(",", ":")).encode("utf-8")
    return QACBuild(
        incidence=matrix,
        roots=roots,
        verse_keys=all_verse_keys,
        active_verse_keys=active_keys,
        active_verse_indices=active_indices,
        source_sha256=source_sha,
        root_order_sha256=sha256_bytes(root_blob),
        verse_order_sha256=sha256_bytes(verse_blob),
        matrix_sha256=canonical_csr_hash(matrix),
        pipeline_sha256=sha256_file(pipeline_path),
    )


def run_qac_chains(
    repo_root: Path,
    *,
    chain_count: int = 4,
    burn_in: int = 10_000,
    samples_per_chain: int = 100,
    thin: int = 1_000,
    seed_base: int = 20261120,
    validate_every: int = 10_000,
    initialization_proposals: int = 50_000,
) -> dict[str, Any]:
    if chain_count < 4 or samples_per_chain < 50 or burn_in < 0 or thin < 1 or initialization_proposals < 0:
        raise ValueError("INVALID_CONFIRMATORY_CHAIN_CONFIGURATION")
    built = build_qac_incidence(repo_root)
    active_mask = np.asarray(built.incidence.sum(axis=1)).ravel() > 0
    matrix = built.incidence[active_mask, :].tocsr()
    matrix.sort_indices()
    if matrix.shape[0] != len(built.active_verse_keys):
        raise RuntimeError("ACTIVE_VERSE_ID_ALIGNMENT_FAILED")
    classes = make_degree_classes(matrix)
    fit = fit_degree_class_bicm(classes)
    theory_screen = degree_sequence_rapid_mixing_screen(classes)
    if not fit.accepted:
        raise RuntimeError(f"BICM_REFERENCE_FIT_BLOCKED:{fit.max_abs_row_residual}:{fit.max_abs_col_residual}")
    X0, Y0, E0 = rebuild_class_counts(matrix, classes)
    observed = compute_statistics(X0, Y0, E0, classes, fit.probabilities)
    active_row_by_source = {
        source_row: active_row
        for active_row, source_row in enumerate(built.active_verse_indices)
    }
    full_row_degrees = np.asarray(built.incidence.sum(axis=1)).ravel().astype(np.int64)
    full_verse_map = [
        {
            "source_matrix_row": source_row,
            "active_matrix_row": active_row_by_source.get(source_row),
            "surah": int(verse_key[0]),
            "ayah": int(verse_key[1]),
            "degree": int(full_row_degrees[source_row]),
            "active": source_row in active_row_by_source,
        }
        for source_row, verse_key in enumerate(built.verse_keys)
    ]
    active_verse_map = [row for row in full_verse_map if row["active"]]
    full_verse_map_sha = sha256_bytes(
        json.dumps(full_verse_map, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    )
    active_verse_map_sha = sha256_bytes(
        json.dumps(active_verse_map, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    )
    root_contrib, verse_contrib = identity_contributions(X0, Y0, E0, classes)
    top_root_indices = np.argsort(root_contrib)[::-1][:20]
    top_verse_indices = np.argsort(verse_contrib)[::-1][:20]
    observed_top_roots = [
        {
            "root_index": int(j),
            "root": built.roots[int(j)],
            "degree": int(classes.col_degrees[int(j)]),
            "degree_class_size": int(classes.col_counts[classes.col_inverse[int(j)]]),
            "h_root_contribution": float(root_contrib[int(j)]),
        }
        for j in top_root_indices
    ]
    observed_top_verses = [
        {
            **active_verse_map[int(i)],
            "degree": int(classes.row_degrees[int(i)]),
            "h_verse_contribution": float(verse_contrib[int(i)]),
        }
        for i in top_verse_indices
    ]
    row_degree_sha = sha256_bytes(np.asarray(classes.row_degrees, dtype="<i8").tobytes())
    col_degree_sha = sha256_bytes(np.asarray(classes.col_degrees, dtype="<i8").tobytes())
    active_matrix_sha = canonical_csr_hash(matrix)
    probability_sha = sha256_bytes(np.asarray(fit.probabilities, dtype="<f8").tobytes())

    traces: list[list[dict[str, float | int]]] = []
    chain_summaries: list[dict[str, Any]] = []
    initialization_edge_sets: list[set[int]] = []
    for index in range(chain_count):
        seed = seed_base + index
        chain = DegreePreservingSwitchChain(matrix, classes, seed=seed)
        chain.advance(initialization_proposals, validate_every=validate_every)
        initialization_overlap = chain.edge_overlap_with_original()
        initialized_matrix = chain.to_csr()
        initialization_edge_sets.append(
            set((chain.rows * chain.n_cols + chain.cols).tolist())
        )
        initialization_matrix_sha = canonical_csr_hash(initialized_matrix)
        retained = chain.run_schedule(
            burn_in=burn_in,
            samples=samples_per_chain,
            thin=thin,
            probabilities=fit.probabilities,
            validate_every=validate_every,
        )
        traces.append(retained)
        chain_summaries.append({
            "seed": seed,
            "initialization_proposals": initialization_proposals,
            "edge_overlap_after_initialization": initialization_overlap,
            "initialization_matrix_sha256": initialization_matrix_sha,
            "initial_state_design": "observed_graph_then_independent_seeded_switch_prefix",
            "proposals": chain.proposals,
            "accepted": chain.accepted,
            "acceptance_rate": chain.acceptance_rate,
            "explicit_lazy_holds": chain.lazy_holds,
            "reject_same_row": chain.reject_same_row,
            "reject_same_column": chain.reject_same_column,
            "reject_occupied_cross_edge": chain.reject_occupied_cross_edge,
            "final_edge_overlap_with_observed": retained[-1]["edge_overlap"],
        })

    diagnostics = mixing_diagnostics(traces)
    initialization_pairwise_overlap = []
    for i in range(len(initialization_edge_sets)):
        row_overlap = []
        for j in range(len(initialization_edge_sets)):
            row_overlap.append(
                len(initialization_edge_sets[i] & initialization_edge_sets[j]) / matrix.nnz
            )
        initialization_pairwise_overlap.append(row_overlap)
    statistic_names = (
        "block_deviance", "h_root", "h_verse",
        "h_verse_non_singleton_root_classes",
        "h_verse_singleton_root_classes",
        "max_root_contribution", "max_verse_contribution",
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": {
            "relative_path": "PHASE2_CLEAN/source/quranic-corpus-morphology-0.4.txt",
            "sha256": built.source_sha256,
            "root_order_sha256": built.root_order_sha256,
            "verse_order_sha256": built.verse_order_sha256,
            "matrix_sha256": built.matrix_sha256,
            "active_matrix_sha256": active_matrix_sha,
            "row_degree_sequence_sha256": row_degree_sha,
            "column_degree_sequence_sha256": col_degree_sha,
            "root_order": list(built.roots),
            "full_verse_id_map": full_verse_map,
            "active_verse_id_map": active_verse_map,
            "full_verse_id_map_sha256": full_verse_map_sha,
            "active_verse_id_map_sha256": active_verse_map_sha,
            "full_shape": list(built.incidence.shape),
            "active_shape": list(matrix.shape),
            "nnz": int(matrix.nnz),
            "active_verse_keys": len(built.active_verse_keys),
            "pipeline_sha256": built.pipeline_sha256,
            "pipeline_matrix_parity": "PASS_SCOPED",
        },
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "platform": platform.platform(),
        },
        "design": {
            "kernel": "lazy half-hold; otherwise uniform ordered pair of distinct edge slots and fixed 2x2 cross-switch; invalid proposals are self-loops",
            "initialization": "Each chain starts from the same observed graph and uses an independent seeded switch prefix. Pairwise prefix-state overlap is reported; this is not a proof of overdispersed initialization.",
            "target": "uniform distribution over the simple bipartite graph fiber with exact observed row and column degrees",
            "chains": chain_count,
            "independent_initialization_proposals_per_chain": initialization_proposals,
            "burn_in_proposals_per_chain": burn_in,
            "samples_per_chain": samples_per_chain,
            "proposals_between_samples": thin,
            "seed_base": seed_base,
            "seeds": [seed_base + i for i in range(chain_count)],
            "validate_every": validate_every,
        },
        "reference_fit": {
            "accepted": fit.accepted,
            "optimizer_success": fit.optimizer_success,
            "max_abs_row_residual": fit.max_abs_row_residual,
            "max_abs_column_residual": fit.max_abs_col_residual,
            "optimizer_evaluations": fit.function_evaluations,
            "parameter_count": fit.parameter_count,
            "probability_shape": list(fit.probabilities.shape),
            "probability_sha256": probability_sha,
            "status": "PASS_SCOPED_NUMERICAL_FIT",
        },
        "observed_statistics": {name: observed[name] for name in statistic_names},
        "observed_top_root_contributions": observed_top_roots,
        "observed_top_verse_contributions": observed_top_verses,
        "initialization_diagnostics": {
            "start_state": "common_observed_graph",
            "independent_random_streams": True,
            "pairwise_edge_overlap_matrix": initialization_pairwise_overlap,
            "distinct_initialization_hash_count": len({item["initialization_matrix_sha256"] for item in chain_summaries}),
            "overdispersed_initialization_established": False,
        },
        "switch_mixing_theory_screen": theory_screen,
        "chains": chain_summaries,
        "trace": {
            name: [[float(item[name]) for item in chain] for chain in traces]
            for name in statistic_names + ("edge_overlap",)
        },
        "mixing_diagnostics": diagnostics,
        "inference": {
            "microcanonical_tail_probabilities": "NOT_COMPUTED",
            "formal_p_values": "NOT_AUTHORIZED",
            "reason": "A finite switch run is not accepted as calibrated until mixing diagnostics and confirmatory protocol pass.",
        },
        "decision": {
            "source_identity": "PASS_SCOPED",
            "matrix_reconstruction": "PASS_SCOPED",
            "switch_invariants": "PASS_SCOPED",
            "mixing": diagnostics["status"],
            "statistical_significance": "NOT_ESTABLISHED",
            "linguistic_interpretation": "NOT_ESTABLISHED",
            "promotion_authority": "NONE",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--chains", type=int, default=4)
    parser.add_argument("--burn-in", type=int, default=10_000)
    parser.add_argument("--samples", type=int, default=100)
    parser.add_argument("--thin", type=int, default=1_000)
    parser.add_argument("--seed-base", type=int, default=20261120)
    parser.add_argument("--validate-every", type=int, default=10_000)
    parser.add_argument("--initialization-proposals", type=int, default=50_000)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error(f"OUTPUT_PATH_ALREADY_EXISTS (refusing to overwrite): {args.output}")
    result = run_qac_chains(
        args.repo_root,
        chain_count=args.chains,
        burn_in=args.burn_in,
        samples_per_chain=args.samples,
        thin=args.thin,
        seed_base=args.seed_base,
        validate_every=args.validate_every,
        initialization_proposals=args.initialization_proposals,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(args.output),
        "source_sha256": result["source"]["sha256"],
        "active_shape": result["source"]["active_shape"],
        "nnz": result["source"]["nnz"],
        "mixing": result["mixing_diagnostics"]["status"],
        "promotion_authority": "NONE",
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
