from __future__ import annotations

import itertools
import sys

import numpy as np
import pytest
import scipy.sparse as sp

from qac_microcanonical import (
    DegreeClasses,
    DegreePreservingSwitchChain,
    compute_statistics,
    degree_sequence_rapid_mixing_screen,
    ess_initial_positive_sequence,
    fit_degree_class_bicm,
    make_degree_classes,
    mixing_diagnostics,
    main,
    rebuild_class_counts,
    split_rhat,
    validate_binary_incidence,
    validate_degree_classes_against_matrix,
)


def fixture() -> sp.csr_matrix:
    return sp.csr_matrix(np.array([
        [1, 0, 0, 0, 1, 1, 0],
        [1, 0, 1, 0, 1, 1, 0],
        [0, 1, 0, 0, 1, 1, 1],
        [1, 0, 0, 0, 0, 1, 0],
        [0, 0, 0, 0, 0, 0, 1],
        [0, 0, 0, 0, 1, 0, 1],
        [0, 0, 0, 0, 0, 1, 1],
        [0, 0, 0, 1, 0, 0, 1],
    ], dtype=np.int8))


def test_binary_input_validation_rejects_nonbinary_values():
    with pytest.raises(ValueError, match="INCIDENCE_MUST_BE_FINITE_BINARY"):
        validate_binary_incidence(sp.csr_matrix([[1.0, 2.0], [0.0, 1.0]]))


def test_binary_input_validation_rejects_duplicate_coordinates():
    matrix = sp.coo_matrix((np.array([1, 1]), (np.array([0, 0]), np.array([1, 1]))), shape=(2, 2))
    with pytest.raises(ValueError, match="DUPLICATE_INCIDENCE_COORDINATE"):
        validate_binary_incidence(matrix)


def test_fit_matches_all_degree_margins():
    matrix = fixture()
    classes = make_degree_classes(matrix)
    fitted = fit_degree_class_bicm(classes)
    assert fitted.accepted
    assert fitted.max_abs_row_residual < 1e-8
    assert fitted.max_abs_col_residual < 1e-8
    assert np.all((fitted.probabilities > 0) & (fitted.probabilities < 1))


def test_analytic_jacobian_matches_central_difference():
    # Recreate the reduced equations to check the same analytic derivative.
    classes = make_degree_classes(fixture())
    rv = classes.row_values.astype(float)
    cv = classes.col_values.astype(float)
    rc = classes.row_counts.astype(float)
    cc = classes.col_counts.astype(float)
    nr, nc = len(rv), len(cv)
    parameter_count = nr + nc - 1
    edge_count = float(np.dot(rv, rc))
    beta0 = np.log(cv)
    alpha0 = np.log(rv / edge_count)
    gauge = float(beta0[-1])
    theta = np.concatenate((alpha0 + gauge, (beta0 - gauge)[:-1]))

    def probs(t):
        beta = np.concatenate((t[nr:], np.zeros(1)))
        return 1 / (1 + np.exp(-(t[:nr, None] + beta[None, :])))

    def fun(t):
        p = probs(t)
        return np.concatenate((p @ cc - rv, rc @ p[:, :-1] - cv[:-1]))

    def jac(t):
        p = probs(t)
        w = p * (1 - p)
        out = np.zeros((parameter_count, parameter_count))
        out[:nr, :nr] = np.diag(w @ cc)
        out[:nr, nr:] = w[:, :-1] * cc[:-1][None, :]
        out[nr:, :nr] = (rc[:, None] * w[:, :-1]).T
        out[nr:, nr:] = np.diag(rc @ w[:, :-1])
        return out

    analytic = jac(theta)
    numeric = np.zeros_like(analytic)
    step = 1e-6
    for j in range(parameter_count):
        delta = np.zeros(parameter_count)
        delta[j] = step
        numeric[:, j] = (fun(theta + delta) - fun(theta - delta)) / (2 * step)
    np.testing.assert_allclose(analytic, numeric, rtol=1e-6, atol=1e-7)


def test_switch_preserves_all_row_and_column_degrees():
    matrix = fixture()
    chain = DegreePreservingSwitchChain(matrix, seed=12345)
    for _ in range(20000):
        chain.step()
    chain.assert_invariants()
    result = chain.to_csr()
    np.testing.assert_array_equal(np.asarray(result.sum(axis=1)).ravel(), np.asarray(matrix.sum(axis=1)).ravel())
    np.testing.assert_array_equal(np.asarray(result.sum(axis=0)).ravel(), np.asarray(matrix.sum(axis=0)).ravel())
    assert result.nnz == matrix.nnz
    assert (result.data == 1).all()


def test_same_seed_reproduces_exact_chain_state():
    matrix = fixture()
    left = DegreePreservingSwitchChain(matrix, seed=444)
    right = DegreePreservingSwitchChain(matrix, seed=444)
    for _ in range(10000):
        left.step()
        right.step()
    assert (left.to_csr() != right.to_csr()).nnz == 0
    assert left.accepted == right.accepted


def test_incremental_class_counters_match_full_rebuild():
    matrix = fixture()
    classes = make_degree_classes(matrix)
    chain = DegreePreservingSwitchChain(matrix, classes, seed=991)
    for _ in range(12000):
        chain.step()
    chain.assert_invariants()
    x, y, e = rebuild_class_counts(chain.to_csr(), classes)
    np.testing.assert_array_equal(chain.X, x)
    np.testing.assert_array_equal(chain.Y, y)
    np.testing.assert_array_equal(chain.E, e)


def test_switch_chain_is_symmetric_and_connected_on_small_degree_fiber():
    # Enumerate all 3x3 binary matrices with margins (2,2,2)/(2,2,2).
    states = []
    for bits in itertools.product((0, 1), repeat=9):
        candidate = np.asarray(bits, dtype=np.int8).reshape(3, 3)
        if np.all(candidate.sum(axis=0) == 2) and np.all(candidate.sum(axis=1) == 2):
            states.append(candidate)
    assert len(states) > 1

    def state_key(a):
        return tuple(a.ravel().tolist())

    transition_counts = {}
    for state in states:
        src = state_key(state)
        counts = {}
        for i, k in itertools.combinations(range(3), 2):
            for j, ell in itertools.combinations(range(3), 2):
                diagonal_a = (state[i, j], state[k, ell], state[i, ell], state[k, j])
                if diagonal_a in ((1, 1, 0, 0), (0, 0, 1, 1)):
                    target = state.copy()
                    target[i, j] = 1 - target[i, j]
                    target[k, ell] = 1 - target[k, ell]
                    target[i, ell] = 1 - target[i, ell]
                    target[k, j] = 1 - target[k, j]
                    dst = state_key(target)
                    counts[dst] = counts.get(dst, 0) + 1
        transition_counts[src] = counts

    # Every valid 2-switch has its reverse; multiplicities must match.
    for src, destinations in transition_counts.items():
        for dst, count in destinations.items():
            assert transition_counts[dst].get(src, 0) == count

    # The state graph must be connected for this realizable bipartite sequence.
    start = state_key(states[0])
    seen = {start}
    queue = [start]
    while queue:
        src = queue.pop()
        for dst in transition_counts[src]:
            if dst not in seen:
                seen.add(dst)
                queue.append(dst)
    assert seen == {state_key(state) for state in states}


def test_statistics_are_finite_nonnegative_and_singleton_split_reconciles():
    matrix = fixture()
    classes = make_degree_classes(matrix)
    fitted = fit_degree_class_bicm(classes)
    x, y, e = rebuild_class_counts(matrix, classes)
    stats = compute_statistics(x, y, e, classes, fitted.probabilities)
    assert all(np.isfinite(value) and value >= 0 for value in stats.values())
    assert stats["h_verse"] == pytest.approx(
        stats["h_verse_singleton_root_classes"] + stats["h_verse_non_singleton_root_classes"],
        abs=1e-9,
    )


def test_root_and_verse_deviance_decompositions_hold():
    matrix = fixture()
    classes = make_degree_classes(matrix)
    fitted = fit_degree_class_bicm(classes)
    x, y, e = rebuild_class_counts(matrix, classes)
    stats = compute_statistics(x, y, e, classes, fitted.probabilities)
    trials = classes.row_counts[:, None] * classes.col_counts[None, :]
    block_rate = e / trials
    root_rate = x / classes.row_counts[:, None]
    verse_rate = y / classes.col_counts[None, :]
    p_root = fitted.probabilities[:, classes.col_inverse]
    p_verse = fitted.probabilities[classes.row_inverse, :]
    from scipy.special import xlogy
    d_root = float((2 * (xlogy(x, root_rate / p_root) + xlogy(classes.row_counts[:, None] - x, (1-root_rate)/(1-p_root)))).sum())
    d_verse = float((2 * (xlogy(y, verse_rate / p_verse) + xlogy(classes.col_counts[None, :] - y, (1-verse_rate)/(1-p_verse)))).sum())
    assert d_root - stats["block_deviance"] == pytest.approx(stats["h_root"], abs=1e-8)
    assert d_verse - stats["block_deviance"] == pytest.approx(stats["h_verse"], abs=1e-8)


def test_schedule_returns_exact_retained_sample_count():
    matrix = fixture()
    classes = make_degree_classes(matrix)
    fitted = fit_degree_class_bicm(classes)
    chain = DegreePreservingSwitchChain(matrix, classes, seed=98)
    records = chain.run_schedule(
        burn_in=100, samples=12, thin=25, probabilities=fitted.probabilities, validate_every=50
    )
    assert len(records) == 12
    assert records[-1]["step"] == 400
    chain.assert_invariants()


def test_mix_diagnostics_do_not_pass_short_or_unmixed_traces():
    traces = [[{"block_deviance": float(i), "h_root": float(i), "h_verse": float(i),
                "h_verse_non_singleton_root_classes": float(i),
                "max_root_contribution": float(i), "max_verse_contribution": float(i),
                "edge_overlap": 1.0 - i / 100.0} for i in range(10)] for _ in range(4)]
    result = mixing_diagnostics(traces)
    assert result["status"] == "INSUFFICIENT_RETAINED_SAMPLES"
    assert np.isfinite(split_rhat(np.random.default_rng(1).normal(size=(4, 100))))
    assert 0 < ess_initial_positive_sequence(np.random.default_rng(2).normal(size=(4, 100))) <= 400


def test_explicit_laziness_prevents_period_two_perfect_matching_chain():
    matching = sp.csr_matrix(np.array([[1, 0], [0, 1]], dtype=np.int8))
    chain = DegreePreservingSwitchChain(matching, seed=5150)
    initial = chain.to_csr().copy()
    for _ in range(500):
        chain.step()
    assert chain.lazy_holds > 0
    assert chain.proposals == 500
    chain.assert_invariants()
    assert chain.to_csr().shape == initial.shape


def test_bicm_fit_rejects_isolates_and_boundary_sequences():
    isolated = sp.csr_matrix(np.array([[1, 0], [0, 0], [0, 1]], dtype=np.int8))
    with pytest.raises(ValueError, match="BICM_FIT_REQUIRES_ISOLATES_REMOVED"):
        fit_degree_class_bicm(make_degree_classes(isolated))
    boundary = sp.csr_matrix(np.array([[1, 1], [1, 0]], dtype=np.int8))
    with pytest.raises(ValueError, match="BICM_DEGREE_SEQUENCE_ON_FEASIBILITY_BOUNDARY"):
        fit_degree_class_bicm(make_degree_classes(boundary))


def test_rank_normalized_rhat_flags_between_chain_shift():
    rng = np.random.default_rng(20261110)
    aligned = rng.normal(size=(4, 200))
    shifted = aligned.copy()
    shifted[2:] += 2.0
    assert split_rhat(aligned) < 1.1
    assert split_rhat(shifted) > 1.1


def test_nontrivial_verse_heterogeneity_and_singleton_split_are_exposed():
    matrix = fixture()
    classes = make_degree_classes(matrix)
    fitted = fit_degree_class_bicm(classes)
    x, y, e = rebuild_class_counts(matrix, classes)
    stats = compute_statistics(x, y, e, classes, fitted.probabilities)
    assert stats["h_verse"] > 0
    assert stats["h_verse_non_singleton_root_classes"] > 0
    assert stats["h_verse_singleton_root_classes"] > 0


def test_degree_classes_are_rejected_when_reused_for_another_matrix():
    original = fixture()
    classes = make_degree_classes(original)
    altered = original.copy().tolil()
    altered[0, 0] = 0
    altered[0, 1] = 1
    altered = altered.tocsr()
    with pytest.raises(ValueError, match="DEGREE_CLASS_COLUMN_SEQUENCE_MISMATCH"):
        validate_degree_classes_against_matrix(altered, classes)
    with pytest.raises(ValueError, match="DEGREE_CLASS_COLUMN_SEQUENCE_MISMATCH"):
        DegreePreservingSwitchChain(altered, classes, seed=7)


def test_bipartite_rapid_mixing_theorem_screen_reports_non_applicability():
    # Construct matching degree margins with QAC's known dimensions, edge total,
    # and extreme degrees. This is a theorem-condition screen fixture, not a
    # replacement for rebuilding the actual QAC matrix.
    row = np.ones(6214, dtype=np.int64)
    row[:813] = 48
    row[813] += 6
    col = np.ones(1642, dtype=np.int64)
    col[:22] = 1879
    col[22] = 1474
    assert int(row.sum()) == int(col.sum()) == 44431
    rv, ri, rc = np.unique(row, return_inverse=True, return_counts=True)
    cv, ci, cc = np.unique(col, return_inverse=True, return_counts=True)
    classes = DegreeClasses(
        row_values=rv, row_inverse=ri, row_counts=rc,
        col_values=cv, col_inverse=ci, col_counts=cc,
        row_degrees=row, col_degrees=col,
    )
    result = degree_sequence_rapid_mixing_screen(classes)
    assert result["theorem_2"]["applicable"] is False
    assert result["theorem_2"]["upper_bound"] == pytest.approx(np.sqrt(44431 / 2))
    assert result["theorem_3"]["inequality_lhs"] == 86342
    assert result["theorem_3"]["inequality_rhs"] == 4335
    assert result["theorem_3"]["applicable"] is False
    assert result["kernel_rate_comparison"]["implemented_to_reference_off_diagonal_rate_ratio"] == pytest.approx(26348.8666494312)
    assert result["rapid_mixing_certified_by_screened_results"] is False
    assert "does NOT establish slow mixing" in result["interpretation"]


def test_theorem_3_inclusive_boundary_is_treated_as_applicable():
    # For a 2x2 perfect matching, Theorem 3 has lhs == rhs == 1.
    matrix = sp.csr_matrix(np.eye(2, dtype=np.int8))
    result = degree_sequence_rapid_mixing_screen(make_degree_classes(matrix))
    assert result["theorem_3"]["inequality_lhs"] == 1
    assert result["theorem_3"]["inequality_rhs"] == 1
    assert result["theorem_3"]["applicable"] is True
    assert result["rapid_mixing_certified_by_screened_results"] is True


def test_theory_screen_reports_exact_kernel_rate_ratio():
    matrix = fixture()
    result = degree_sequence_rapid_mixing_screen(make_degree_classes(matrix))
    ratio = result["kernel_rate_comparison"]["implemented_to_reference_off_diagonal_rate_ratio"]
    assert ratio > 0
    assert result["kernel_rate_comparison"]["scope"].startswith("For each valid 2-switch")


def test_cli_refuses_to_overwrite_existing_output(tmp_path, monkeypatch):
    output = tmp_path / "existing_receipt.json"
    output.write_text("preserve-me", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["qac_microcanonical", "--output", str(output)])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 2
    assert output.read_text(encoding="utf-8") == "preserve-me"
