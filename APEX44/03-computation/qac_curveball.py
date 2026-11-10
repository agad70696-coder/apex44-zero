#!/usr/bin/env python3
"""Independent Curveball trade kernel for exact-degree QAC randomization.

This is a second microcanonical kernel, not a replacement for the 2-switch
kernel. It preserves all row and column degrees exactly and has the uniform
fixed-degree distribution as its stationary distribution. A finite run still
requires separate mixing diagnostics; neither the kernel nor its stationary
law certifies that a finite sample is calibrated.
"""
from __future__ import annotations

import argparse
import json
import math
import platform
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import scipy

from qac_microcanonical import (
    SCHEMA_VERSION,
    DegreeClasses,
    build_qac_incidence,
    canonical_csr_hash,
    compute_statistics,
    degree_sequence_rapid_mixing_screen,
    fit_degree_class_bicm,
    make_degree_classes,
    mixing_diagnostics,
    rebuild_class_counts,
    sha256_bytes,
    validate_binary_incidence,
)
import scipy.sparse as sp


class DegreePreservingCurveballChain:
    """Lazy Curveball chain over a simple bipartite fixed-degree fiber.

    One proposal holds with probability 1/2. Otherwise an unordered pair of
    rows is selected uniformly. Let A and B be their disjoint sets of unique
    neighbors, after removing their common neighbors. A subset A' of A∪B of
    size |A| is selected uniformly; A' is assigned to the first row and the
    complement to the second. The trade is symmetric: the union and |A| are
    invariant, so the reverse allocation has the same probability.

    Every 2-switch is a possible size-one Curveball trade. Since 2-switches
    connect all simple bipartite realizations of a graphical degree sequence,
    the Curveball state graph is connected as well. The explicit hold gives
    aperiodicity. These facts establish the stationary target, not finite-run
    convergence speed.
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
        if self.n_rows < 2 or self.matrix.nnz == 0:
            raise ValueError("CURVEBALL_REQUIRES_AT_LEAST_TWO_ROWS_AND_ONE_EDGE")
        self.edge_count = int(self.matrix.nnz)
        self.initial_row_degrees = np.asarray(self.matrix.sum(axis=1)).ravel().astype(np.int64)
        self.initial_col_degrees = np.asarray(self.matrix.sum(axis=0)).ravel().astype(np.int64)
        self.classes = classes or make_degree_classes(self.matrix)
        if len(self.classes.row_inverse) != self.n_rows or len(self.classes.col_inverse) != self.n_cols:
            raise ValueError("DEGREE_CLASS_SHAPE_MISMATCH")
        # Full degree-sequence and class-order validation, not shape-only.
        from qac_microcanonical import validate_degree_classes_against_matrix
        validate_degree_classes_against_matrix(self.matrix, self.classes)
        self.row_neighbors = [
            set(self.matrix.indices[self.matrix.indptr[row]:self.matrix.indptr[row + 1]].tolist())
            for row in range(self.n_rows)
        ]
        self.X, self.Y, self.E = rebuild_class_counts(self.matrix, self.classes)
        self.rng = np.random.default_rng(seed)
        self.seed = int(seed)
        self.proposals = 0
        self.accepted_trades = 0
        self.lazy_holds = 0
        self.reject_identical_row_pair = 0
        self.valid_no_change_trades = 0
        self._original_edge_ids = self._edge_ids()

    @property
    def acceptance_rate(self) -> float:
        return self.accepted_trades / self.proposals if self.proposals else 0.0

    def _edge_ids(self) -> set[int]:
        return {
            row * self.n_cols + col
            for row, neighbors in enumerate(self.row_neighbors)
            for col in neighbors
        }

    def edge_overlap_with_original(self) -> float:
        current = self._edge_ids()
        return len(current & self._original_edge_ids) / self.edge_count

    def distance_from_original(self) -> dict[str, float]:
        overlap = self.edge_overlap_with_original()
        turnover = 1.0 - overlap
        hamming = (2.0 * self.edge_count * turnover) / (self.n_rows * self.n_cols)
        return {
            "edge_overlap": float(overlap),
            "edge_turnover_fraction": float(turnover),
            "hamming_distance_fraction": float(hamming),
        }

    def _update_edge_counter(self, row: int, col: int, delta: int) -> None:
        row_class = int(self.classes.row_inverse[row])
        col_class = int(self.classes.col_inverse[col])
        self.X[row_class, col] += delta
        self.Y[row, col_class] += delta
        self.E[row_class, col_class] += delta

    def step(self) -> bool:
        """Apply one Markov proposal; return True iff the graph changed."""
        self.proposals += 1
        if self.rng.random() < 0.5:
            self.lazy_holds += 1
            return False

        first, second = self.rng.choice(self.n_rows, size=2, replace=False)
        i, k = int(first), int(second)
        # Canonicalize the pair order. This does not alter the uniform pair law.
        if i > k:
            i, k = k, i
        ni, nk = self.row_neighbors[i], self.row_neighbors[k]
        common = ni & nk
        left_only = ni - common
        right_only = nk - common
        if not left_only and not right_only:
            self.reject_identical_row_pair += 1
            return False

        union = np.asarray(sorted(left_only | right_only), dtype=np.int64)
        chosen_indices = self.rng.choice(len(union), size=len(left_only), replace=False)
        new_left = set(int(union[index]) for index in chosen_indices)
        new_right = set(int(col) for col in union) - new_left

        left_remove = left_only - new_left
        left_add = new_left - left_only
        right_remove = right_only - new_right
        right_add = new_right - right_only
        if not (left_remove or left_add or right_remove or right_add):
            self.valid_no_change_trades += 1
            return False

        for col in left_remove:
            self._update_edge_counter(i, col, -1)
        for col in left_add:
            self._update_edge_counter(i, col, +1)
        for col in right_remove:
            self._update_edge_counter(k, col, -1)
        for col in right_add:
            self._update_edge_counter(k, col, +1)

        self.row_neighbors[i] = common | new_left
        self.row_neighbors[k] = common | new_right
        self.accepted_trades += 1
        return True

    def advance(self, proposals: int, *, validate_every: int = 0) -> None:
        if proposals < 0 or validate_every < 0:
            raise ValueError("INVALID_CURVEBALL_ADVANCE_CONFIGURATION")
        for step in range(1, proposals + 1):
            self.step()
            if validate_every and step % validate_every == 0:
                self.assert_invariants()
        self.assert_invariants()

    def statistics(self, probabilities: np.ndarray) -> dict[str, float]:
        return compute_statistics(self.X, self.Y, self.E, self.classes, probabilities)

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
            raise ValueError("INVALID_CURVEBALL_CHAIN_SCHEDULE")
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
                    **self.distance_from_original(),
                })
        self.assert_invariants()
        if len(retained) != samples:
            raise RuntimeError("CURVEBALL_RETAINED_SAMPLE_COUNT_MISMATCH")
        return retained

    def to_csr(self) -> sp.csr_matrix:
        rows: list[int] = []
        cols: list[int] = []
        for row, neighbors in enumerate(self.row_neighbors):
            for col in neighbors:
                rows.append(row)
                cols.append(col)
        matrix = sp.coo_matrix(
            (np.ones(len(rows), dtype=np.int8), (rows, cols)),
            shape=(self.n_rows, self.n_cols),
        ).tocsr()
        matrix.sum_duplicates()
        matrix.eliminate_zeros()
        matrix.sort_indices()
        return matrix

    def assert_invariants(self) -> None:
        row_degrees = np.fromiter((len(values) for values in self.row_neighbors), dtype=np.int64)
        if not np.array_equal(row_degrees, self.initial_row_degrees):
            raise RuntimeError("CURVEBALL_ROW_DEGREE_INVARIANT_BROKEN")
        column_degrees = np.zeros(self.n_cols, dtype=np.int64)
        for neighbors in self.row_neighbors:
            if len(neighbors) != len(set(neighbors)):
                raise RuntimeError("CURVEBALL_DUPLICATE_ROW_NEIGHBOR")
            for col in neighbors:
                column_degrees[col] += 1
        if not np.array_equal(column_degrees, self.initial_col_degrees):
            raise RuntimeError("CURVEBALL_COLUMN_DEGREE_INVARIANT_BROKEN")
        if int(row_degrees.sum()) != self.edge_count:
            raise RuntimeError("CURVEBALL_EDGE_COUNT_INVARIANT_BROKEN")
        rebuilt_x, rebuilt_y, rebuilt_e = rebuild_class_counts(self.to_csr(), self.classes)
        if not np.array_equal(rebuilt_x, self.X):
            raise RuntimeError("CURVEBALL_ROOT_COUNTER_INVARIANT_BROKEN")
        if not np.array_equal(rebuilt_y, self.Y):
            raise RuntimeError("CURVEBALL_VERSE_COUNTER_INVARIANT_BROKEN")
        if not np.array_equal(rebuilt_e, self.E):
            raise RuntimeError("CURVEBALL_BLOCK_COUNTER_INVARIANT_BROKEN")


def _two_sample_ks_effect_size(left: np.ndarray, right: np.ndarray) -> float:
    """Return the two-sample empirical-CDF sup distance, without a p-value."""
    a = np.asarray(left, dtype=np.float64)
    b = np.asarray(right, dtype=np.float64)
    if a.ndim != 1 or b.ndim != 1 or a.size == 0 or b.size == 0:
        raise ValueError("KS_EFFECT_SIZE_REQUIRES_NONEMPTY_VECTORS")
    if not np.all(np.isfinite(a)) or not np.all(np.isfinite(b)):
        raise ValueError("KS_EFFECT_SIZE_REQUIRES_FINITE_VALUES")
    support = np.sort(np.concatenate((a, b)))
    cdf_a = np.searchsorted(np.sort(a), support, side="right") / a.size
    cdf_b = np.searchsorted(np.sort(b), support, side="right") / b.size
    return float(np.max(np.abs(cdf_a - cdf_b)))


def curveball_distance_stability_diagnostic(
    chain_traces: list[list[dict[str, float | int]]],
    *,
    window_size: int = 25,
) -> dict[str, Any]:
    """Descriptive adjacent-window KS-D diagnostic; never computes p-values.

    For each chain, compare every adjacent pair of non-overlapping windows of
    Hamming distances from the observed starting graph. The KS D statistic is
    reported only as a distributional effect size. No iid KS p-value or
    automatic stopping decision is produced because samples are serially
    dependent and distance stabilization is not proof of graph stationarity.
    """
    if window_size < 4:
        raise ValueError("CURVEBALL_DISTANCE_WINDOW_TOO_SMALL")
    comparisons: list[dict[str, float | int]] = []
    for chain_index, trace in enumerate(chain_traces):
        if len(trace) < 2 * window_size:
            continue
        distances = np.asarray(
            [float(item["hamming_distance_fraction"]) for item in trace],
            dtype=np.float64,
        )
        if not np.all(np.isfinite(distances)):
            raise ValueError("NONFINITE_CURVEBALL_DISTANCE_TRACE")
        window_count = len(distances) // window_size
        windows = [
            distances[index * window_size:(index + 1) * window_size]
            for index in range(window_count)
        ]
        for earlier_index in range(window_count - 1):
            earlier = windows[earlier_index]
            later = windows[earlier_index + 1]
            comparisons.append({
                "chain_index": chain_index,
                "earlier_window_index": earlier_index,
                "later_window_index": earlier_index + 1,
                "earlier_window_size": int(earlier.size),
                "later_window_size": int(later.size),
                "ks_effect_size_D": _two_sample_ks_effect_size(earlier, later),
            })
    if not comparisons:
        return {
            "status": "INSUFFICIENT_SAMPLES",
            "window_size": window_size,
            "comparisons": [],
            "formal_ks_p_values": "NOT_COMPUTED_DEPENDENT_MCMC",
            "stopping_authority": "NONE",
        }
    values = [float(item["ks_effect_size_D"]) for item in comparisons]
    chain_ids = sorted({int(item["chain_index"]) for item in comparisons})
    return {
        "status": "DESCRIPTIVE_DISTANCE_DISTRIBUTION_STABILITY_ONLY",
        "window_size": window_size,
        "comparisons": comparisons,
        "comparisons_per_chain": {
            str(index): sum(int(item["chain_index"]) == index for item in comparisons)
            for index in chain_ids
        },
        "median_ks_effect_size_D": float(np.median(values)),
        "max_ks_effect_size_D": float(np.max(values)),
        "formal_ks_p_values": "NOT_COMPUTED_DEPENDENT_MCMC",
        "stopping_authority": "NONE",
        "warning": "A stable distance distribution is not proof of stationarity; the distance statistic may stabilize before other graph features mix. D is an effect size only; serial dependence is not converted into an iid KS p-value.",
    }


def run_qac_curveball_chains(
    repo_root: Path,
    *,
    chain_count: int = 4,
    initialization_proposals: int = 50_000,
    burn_in: int = 10_000,
    samples_per_chain: int = 100,
    thin: int = 1_000,
    seed_base: int = 20261130,
    validate_every: int = 10_000,
    distance_window_size: int = 25,
) -> dict[str, Any]:
    if chain_count < 4 or initialization_proposals < 0 or burn_in < 0 or samples_per_chain < 50 or thin < 1:
        raise ValueError("INVALID_CURVEBALL_CONFIRMATORY_CONFIGURATION")
    built = build_qac_incidence(repo_root)
    active_mask = np.asarray(built.incidence.sum(axis=1)).ravel() > 0
    matrix = built.incidence[active_mask, :].tocsr()
    matrix.sort_indices()
    if matrix.shape[0] != len(built.active_verse_keys):
        raise RuntimeError("CURVEBALL_ACTIVE_VERSE_ALIGNMENT_FAILED")
    classes = make_degree_classes(matrix)
    fit = fit_degree_class_bicm(classes)
    if not fit.accepted:
        raise RuntimeError("CURVEBALL_CANONICAL_REFERENCE_FIT_BLOCKED")
    X0, Y0, E0 = rebuild_class_counts(matrix, classes)
    observed = compute_statistics(X0, Y0, E0, classes, fit.probabilities)
    theory_screen = degree_sequence_rapid_mixing_screen(classes)

    active_row_by_source = {
        source_row: active_row
        for active_row, source_row in enumerate(built.active_verse_indices)
    }
    full_degrees = np.asarray(built.incidence.sum(axis=1)).ravel().astype(np.int64)
    full_verse_map = [
        {
            "source_matrix_row": source_row,
            "active_matrix_row": active_row_by_source.get(source_row),
            "surah": int(key[0]),
            "ayah": int(key[1]),
            "degree": int(full_degrees[source_row]),
            "active": source_row in active_row_by_source,
        }
        for source_row, key in enumerate(built.verse_keys)
    ]
    active_verse_map = [item for item in full_verse_map if item["active"]]

    traces: list[list[dict[str, float | int]]] = []
    chain_summaries: list[dict[str, Any]] = []
    initial_states: list[set[int]] = []
    for chain_index in range(chain_count):
        seed = seed_base + chain_index
        chain = DegreePreservingCurveballChain(matrix, classes, seed=seed)
        chain.advance(initialization_proposals, validate_every=validate_every)
        init_state = chain._edge_ids()
        initial_states.append(init_state)
        init_overlap = len(init_state & chain._original_edge_ids) / chain.edge_count
        init_hash = canonical_csr_hash(chain.to_csr())
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
            "initialization_edge_overlap_with_observed": float(init_overlap),
            "initialization_matrix_sha256": init_hash,
            "initial_state_design": "observed_graph_then_independent_seeded_curveball_prefix",
            "overdispersed_initialization_established": False,
            "proposals": chain.proposals,
            "accepted_trades": chain.accepted_trades,
            "lazy_holds": chain.lazy_holds,
            "reject_identical_row_pair": chain.reject_identical_row_pair,
            "valid_no_change_trades": chain.valid_no_change_trades,
            "acceptance_rate": chain.acceptance_rate,
            "final_distance": chain.distance_from_original(),
        })

    pairwise_overlap = []
    for i, left in enumerate(initial_states):
        pairwise_overlap.append([
            len(left & right) / matrix.nnz for right in initial_states
        ])
    diagnostics = mixing_diagnostics(traces)
    distance_stability = curveball_distance_stability_diagnostic(
        traces, window_size=distance_window_size
    )
    statistic_names = (
        "block_deviance", "h_root", "h_verse",
        "h_verse_non_singleton_root_classes", "h_verse_singleton_root_classes",
        "max_root_contribution", "max_verse_contribution",
    )
    return {
        "schema_version": "apex44-qac-curveball-pilot-v0.2",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": {
            "sha256": built.source_sha256,
            "root_order_sha256": built.root_order_sha256,
            "verse_order_sha256": built.verse_order_sha256,
            "matrix_sha256": built.matrix_sha256,
            "active_matrix_sha256": canonical_csr_hash(matrix),
            "row_degree_sequence_sha256": sha256_bytes(np.asarray(classes.row_degrees, dtype="<i8").tobytes()),
            "column_degree_sequence_sha256": sha256_bytes(np.asarray(classes.col_degrees, dtype="<i8").tobytes()),
            "pipeline_sha256": built.pipeline_sha256,
            "full_shape": list(built.incidence.shape),
            "active_shape": list(matrix.shape),
            "nnz": int(matrix.nnz),
            "root_order": list(built.roots),
            "full_verse_id_map": full_verse_map,
            "active_verse_id_map": active_verse_map,
            "pipeline_matrix_parity": "PASS_SCOPED",
        },
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "platform": platform.platform(),
        },
        "kernel": {
            "name": "lazy_curveball_uniform_trade",
            "transition": "hold with probability 1/2; otherwise choose an unordered row pair uniformly and choose a subset of the symmetric difference uniformly with the first row's original unique-neighbor cardinality",
            "stationary_target": "uniform over all simple bipartite matrices with the exact observed row and column degrees",
            "detailed_balance_reason": "The selected row-pair symmetric difference is invariant under reversal, and the subset cardinality is fixed by the first row degree; forward and reverse allocations have equal probability.",
            "irreducibility_reason": "Every valid 2-switch is a possible one-neighbor Curveball trade; the bipartite 2-switch graph connects all realizations of a graphical degree sequence.",
            "aperiodicity_reason": "Explicit probability-1/2 hold.",
            "rapid_mixing_certificate": "NOT_ESTABLISHED",
        },
        "design": {
            "chain_count": chain_count,
            "initialization_proposals_per_chain": initialization_proposals,
            "burn_in_proposals_per_chain": burn_in,
            "samples_per_chain": samples_per_chain,
            "proposals_between_samples": thin,
            "seed_base": seed_base,
            "seeds": [seed_base + i for i in range(chain_count)],
            "overdispersed_initialization_established": False,
        },
        "reference_fit": {
            "accepted": fit.accepted,
            "max_abs_row_residual": fit.max_abs_row_residual,
            "max_abs_column_residual": fit.max_abs_col_residual,
            "probability_shape": list(fit.probabilities.shape),
        },
        "observed_statistics": observed,
        "theory_screen": theory_screen,
        "chains": chain_summaries,
        "initialization_pairwise_edge_overlap": pairwise_overlap,
        "trace": {
            name: [[float(item[name]) for item in chain] for chain in traces]
            for name in statistic_names + ("edge_overlap", "edge_turnover_fraction", "hamming_distance_fraction")
        },
        "mixing_diagnostics": diagnostics,
        "distance_distribution_stability": distance_stability,
        "inference": {
            "microcanonical_tail_probabilities": "NOT_COMPUTED",
            "formal_p_values": "NOT_AUTHORIZED",
            "reason": "Curveball is an alternative uniform-stationary kernel; finite-run convergence is not established by kernel validity or distance stabilization alone.",
        },
        "decision": {
            "source_identity": "PASS_SCOPED",
            "matrix_reconstruction": "PASS_SCOPED",
            "curveball_degree_invariants": "PASS_SCOPED",
            "mixing": diagnostics["status"],
            "distance_stability": distance_stability["status"],
            "statistical_significance": "NOT_ESTABLISHED",
            "linguistic_interpretation": "NOT_ESTABLISHED",
            "promotion_authority": "NONE",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--chains", type=int, default=4)
    parser.add_argument("--initialization-proposals", type=int, default=50_000)
    parser.add_argument("--burn-in", type=int, default=10_000)
    parser.add_argument("--samples", type=int, default=100)
    parser.add_argument("--thin", type=int, default=1_000)
    parser.add_argument("--seed-base", type=int, default=20261130)
    parser.add_argument("--validate-every", type=int, default=10_000)
    parser.add_argument("--distance-window-size", type=int, default=25)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error(f"OUTPUT_PATH_ALREADY_EXISTS: refusing overwrite: {args.output}")
    result = run_qac_curveball_chains(
        args.repo_root,
        chain_count=args.chains,
        initialization_proposals=args.initialization_proposals,
        burn_in=args.burn_in,
        samples_per_chain=args.samples,
        thin=args.thin,
        seed_base=args.seed_base,
        validate_every=args.validate_every,
        distance_window_size=args.distance_window_size,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(args.output),
        "source_sha256": result["source"]["sha256"],
        "active_shape": result["source"]["active_shape"],
        "nnz": result["source"]["nnz"],
        "mixing": result["mixing_diagnostics"]["status"],
        "distance_stability": result["distance_distribution_stability"]["status"],
        "promotion_authority": "NONE",
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
