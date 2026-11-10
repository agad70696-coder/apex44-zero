from __future__ import annotations

import itertools
import math

import numpy as np
import pytest
import scipy.sparse as sp

from qac_microcanonical import make_degree_classes
from qac_curveball import (
    DegreePreservingCurveballChain,
    curveball_distance_stability_diagnostic,
)


def fixture() -> sp.csr_matrix:
    return sp.csr_matrix(np.array([
        [1, 0, 0, 1, 1, 0],
        [0, 1, 1, 0, 0, 1],
        [1, 1, 0, 0, 1, 0],
        [0, 0, 1, 1, 0, 1],
        [1, 0, 1, 0, 0, 1],
    ], dtype=np.int8))


def matrix_key(matrix: np.ndarray) -> tuple[int, ...]:
    return tuple(np.asarray(matrix, dtype=np.int8).ravel().tolist())


def enumerate_fiber(row_degrees: tuple[int, ...], col_degrees: tuple[int, ...]):
    n_rows, n_cols = len(row_degrees), len(col_degrees)
    states = []
    for flat in itertools.product((0, 1), repeat=n_rows * n_cols):
        matrix = np.asarray(flat, dtype=np.int8).reshape(n_rows, n_cols)
        if tuple(matrix.sum(axis=1)) == row_degrees and tuple(matrix.sum(axis=0)) == col_degrees:
            states.append(matrix)
    return states


def exact_curveball_transition_matrix(states: list[np.ndarray]) -> np.ndarray:
    keys = {matrix_key(state): index for index, state in enumerate(states)}
    n = len(states)
    n_rows = states[0].shape[0]
    transition = np.zeros((n, n), dtype=np.float64)
    row_pairs = list(itertools.combinations(range(n_rows), 2))
    for state_index, state in enumerate(states):
        # Explicit half-hold.
        transition[state_index, state_index] += 0.5
        for i, k in row_pairs:
            left = set(np.flatnonzero(state[i]).tolist())
            right = set(np.flatnonzero(state[k]).tolist())
            common = left & right
            left_only = left - common
            right_only = right - common
            union = sorted(left_only | right_only)
            if not union:
                transition[state_index, state_index] += 0.5 / len(row_pairs)
                continue
            allocations = list(itertools.combinations(union, len(left_only)))
            proposal_mass = 0.5 / len(row_pairs) / len(allocations)
            for chosen in allocations:
                chosen_set = set(chosen)
                candidate = state.copy()
                candidate[i, :] = 0
                candidate[k, :] = 0
                candidate[i, list(common | chosen_set)] = 1
                candidate[k, list(common | (set(union) - chosen_set))] = 1
                target = keys[matrix_key(candidate)]
                transition[state_index, target] += proposal_mass
    return transition


def test_curveball_preserves_exact_row_column_degrees_and_counters():
    matrix = fixture()
    classes = make_degree_classes(matrix)
    chain = DegreePreservingCurveballChain(matrix, classes, seed=20261130)
    chain.advance(5_000, validate_every=250)
    chain.assert_invariants()
    np.testing.assert_array_equal(
        np.asarray(chain.to_csr().sum(axis=1)).ravel(),
        np.asarray(matrix.sum(axis=1)).ravel(),
    )
    np.testing.assert_array_equal(
        np.asarray(chain.to_csr().sum(axis=0)).ravel(),
        np.asarray(matrix.sum(axis=0)).ravel(),
    )
    assert chain.to_csr().nnz == matrix.nnz


def test_curveball_reproducible_for_same_seed():
    matrix = fixture()
    a = DegreePreservingCurveballChain(matrix, seed=77)
    b = DegreePreservingCurveballChain(matrix, seed=77)
    a.advance(1_000)
    b.advance(1_000)
    np.testing.assert_array_equal(a.to_csr().toarray(), b.to_csr().toarray())
    assert a.accepted_trades == b.accepted_trades
    assert a.lazy_holds == b.lazy_holds


def test_curveball_kernel_is_symmetric_on_exhaustive_small_fiber():
    # Three rows and three columns; fiber contains >1 realizations.
    states = enumerate_fiber((1, 1, 2), (1, 1, 2))
    assert len(states) == 5
    transition = exact_curveball_transition_matrix(states)
    np.testing.assert_allclose(transition.sum(axis=1), np.ones(len(states)), atol=1e-12)
    np.testing.assert_allclose(transition, transition.T, atol=1e-12)


def test_curveball_state_graph_is_connected_on_exhaustive_small_fiber():
    states = enumerate_fiber((1, 1, 2), (1, 1, 2))
    transition = exact_curveball_transition_matrix(states)
    adjacency = [set(np.flatnonzero(transition[i] > 0).tolist()) for i in range(len(states))]
    reached = {0}
    frontier = [0]
    while frontier:
        current = frontier.pop()
        for neighbor in adjacency[current] - reached:
            reached.add(neighbor)
            frontier.append(neighbor)
    assert reached == set(range(len(states)))


def test_curveball_has_explicit_lazy_holds():
    chain = DegreePreservingCurveballChain(fixture(), seed=12)
    chain.advance(1000)
    assert chain.proposals == 1000
    assert chain.lazy_holds > 0
    assert chain.lazy_holds / chain.proposals > 0.35


def test_curveball_distance_decomposition_matches_hamming_distance():
    matrix = fixture()
    chain = DegreePreservingCurveballChain(matrix, seed=102)
    chain.advance(300)
    current = chain.to_csr().toarray().astype(bool)
    original = matrix.toarray().astype(bool)
    expected = float(np.count_nonzero(current != original) / current.size)
    observed = chain.distance_from_original()
    assert math.isclose(observed["hamming_distance_fraction"], expected, rel_tol=0.0, abs_tol=1e-15)
    assert math.isclose(
        observed["edge_turnover_fraction"],
        1.0 - observed["edge_overlap"],
        rel_tol=0.0,
        abs_tol=1e-15,
    )


def test_distance_stability_reports_effect_size_without_invalid_iid_p_value():
    traces = []
    for base in (0.2, 0.25, 0.3, 0.35):
        traces.append([
            {"hamming_distance_fraction": base + 0.001 * ((i % 5) - 2)}
            for i in range(80)
        ])
    result = curveball_distance_stability_diagnostic(traces, window_size=20)
    assert result["status"] == "DESCRIPTIVE_DISTANCE_DISTRIBUTION_STABILITY_ONLY"
    assert result["formal_ks_p_values"] == "NOT_COMPUTED_DEPENDENT_MCMC"
    assert result["stopping_authority"] == "NONE"
    assert result["max_ks_effect_size_D"] == 0.0


def test_distance_stability_requires_sufficient_samples():
    traces = [[{"hamming_distance_fraction": 0.1}] * 10 for _ in range(4)]
    result = curveball_distance_stability_diagnostic(traces, window_size=25)
    assert result["status"] == "INSUFFICIENT_SAMPLES"
    assert result["formal_ks_p_values"] == "NOT_COMPUTED_DEPENDENT_MCMC"


def test_curveball_rejects_mismatched_degree_class_metadata():
    matrix = fixture()
    classes = make_degree_classes(matrix)
    altered = matrix.copy().tolil()
    altered[0, 0] = 0
    altered[0, 2] = 1
    other = altered.tocsr()
    # If row/column margins change, the passed class metadata must be rejected.
    with pytest.raises(ValueError):
        DegreePreservingCurveballChain(other, classes, seed=1)


def test_manual_ks_effect_size_matches_empirical_cdf_definition():
    from qac_curveball import _two_sample_ks_effect_size

    # Empirical CDFs differ by exactly 1/2 on this two-point example.
    assert math.isclose(
        _two_sample_ks_effect_size(np.array([0.0, 1.0]), np.array([1.0, 2.0])),
        0.5,
        rel_tol=0.0,
        abs_tol=1e-15,
    )


def test_distance_stability_compares_all_adjacent_complete_windows():
    traces = [[
        {"hamming_distance_fraction": float(index % 7) / 10.0}
        for index in range(100)
    ] for _ in range(4)]
    result = curveball_distance_stability_diagnostic(traces, window_size=20)
    assert result["comparisons_per_chain"] == {"0": 4, "1": 4, "2": 4, "3": 4}
    assert len(result["comparisons"]) == 16
    assert result["formal_ks_p_values"] == "NOT_COMPUTED_DEPENDENT_MCMC"
    assert result["stopping_authority"] == "NONE"


def test_curveball_handles_empty_unique_side_as_valid_self_loop():
    matrix = sp.csr_matrix(np.array([
        [1, 1, 0, 0],
        [1, 1, 1, 0],
        [0, 0, 0, 1],
    ], dtype=np.int8))
    chain = DegreePreservingCurveballChain(matrix, seed=7001)
    before = chain.to_csr().toarray().copy()
    # With seed chosen to make the test deterministic, advance until a
    # row-pair with one empty unique side is proposed or the bounded loop ends.
    for _ in range(500):
        chain.step()
    chain.assert_invariants()
    assert chain.to_csr().nnz == matrix.nnz
    assert np.array_equal(
        np.asarray(chain.to_csr().sum(axis=1)).ravel(),
        np.asarray(matrix.sum(axis=1)).ravel(),
    )
    assert np.array_equal(
        np.asarray(chain.to_csr().sum(axis=0)).ravel(),
        np.asarray(matrix.sum(axis=0)).ravel(),
    )
