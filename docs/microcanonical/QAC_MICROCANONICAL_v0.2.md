# APEX44 / QAC — Microcanonical sampling toolkit v0.2

## Release scope

This release contains two independent Markov kernels for the same fixed-degree bipartite state space:

1. `qac_microcanonical.py`: lazy 2-switch sampling (v0.1.1 kernel).
2. `qac_curveball.py`: lazy Curveball row-pair trades (new experimental v0.2 kernel).

Both preserve every row and column degree exactly. Their common stationary target is the uniform distribution over simple bipartite matrices with the observed exact margins. Neither kernel provides a finite-run mixing certificate for the QAC degree sequence.

## Statistical boundary

The toolkit separates:

- kernel correctness and exact degree invariants;
- finite-run mixing diagnostics;
- inferential calibration.

A successful invariant test proves only that a transition preserved the degree sequence and binary structure. Detailed balance and state-space connectivity establish the stationary target. They do not prove that finite samples approximate it closely enough for tail-probability inference.

The diagnostics report rank-normalized/folded split-Rhat, Geyer-style ESS, MCSE/SD, edge turnover, and a descriptive adjacent-window KS-D effect size for distances from the observed graph. The KS-D diagnostic produces no p-value and has no automatic stopping authority. Formal microcanonical p-values are not computed.

## Kernel choices

### 2-switch

Each proposal holds with probability 1/2. Otherwise, two edge slots are selected and their endpoints are crossed if the resulting simple bipartite graph is valid. Invalid proposals are self-loops.

### Curveball

Each proposal holds with probability 1/2. Otherwise, an unordered pair of rows is selected. Common neighbors stay in both rows; the symmetric difference is randomly partitioned between the two rows while preserving the first row's original unique-neighbor cardinality. This can perform multiple edge reallocations in one trade.

The Curveball transition is symmetric because the selected row pair, symmetric-difference union, and allocation cardinality are unchanged by reversing the trade. Every 2-switch is a possible Curveball trade, so the standard bipartite 2-switch connectivity result gives connectivity of the Curveball state graph.

See `CURVEBALL_RESEARCH.md` for the derivation and the limits of published rapid-mixing results.

## Run the Curveball QAC pilot

Run from a clean repository worktree where the pinned source and reference pipeline are present:

```bash
python APEX44/03-computation/qac_curveball.py \
  --repo-root . \
  --chains 4 \
  --initialization-proposals 50000 \
  --burn-in 10000 \
  --samples 100 \
  --thin 1000 \
  --seed-base 20261130 \
  --output artifacts/microcanonical/qac_curveball_pilot.json
```

The CLI refuses to overwrite an existing receipt. Use a new versioned output path for each run. Each chain starts from the observed graph followed by an independent seeded Curveball prefix. This creates different valid initial states but does **not** prove that those starts are overdispersed across the state space; the receipt records pairwise overlap and sets `overdispersed_initialization_established=false`.

## Run the tests

From this package directory:

```bash
python -m py_compile qac_microcanonical.py qac_curveball.py \
  test_qac_microcanonical.py test_qac_curveball.py \
  create_synthetic_smoke.py create_curveball_synthetic_smoke.py
python -m pytest -q
python create_curveball_synthetic_smoke.py
```

The synthetic receipt is a small-fixture kernel test. It is not QAC evidence and does not authorize statistical inference.

## QAC identity controls

The QAC builder pins the morphology source SHA-256, reconstructs only `ROOT:` features, checks exact parity with `reproduce_qac_analysis.build_biadjacency`, and retains surah/ayah identifiers, original row indices, active row indices, ordered root labels, and independent hashes for these mappings and matrices.

The full QAC source replay is not represented by the synthetic build tests. It must be performed in the target Termux worktree before this package can be considered deployed or reproducible on-device.

## Research limits

- The two screened Erdős et al. sufficient conditions do not certify rapid mixing for the previously reported QAC degree extrema. This is not evidence that the kernels mix slowly.
- Carstens & Kleer show a rapid-mixing comparison from switch to Curveball when the switch chain is rapidly mixing; this does not grant a QAC certificate when the screened switch hypotheses are not met.
- Neal's distance-distribution stopping idea is used only for descriptive KS-D comparisons. Serial dependence invalidates treating the windows as iid samples for an ordinary KS p-value.
- Fastball is cited as a future optimization candidate but is not implemented in this release.
- The graph represents ROOT-only binary verse presence. It does not represent repeated occurrences within a verse, token order, morphology beyond the selected roots, or semantic interpretation.

## Release files

- `qac_microcanonical.py`: 2-switch kernel, QAC build, shared statistics and diagnostics.
- `qac_curveball.py`: alternative Curveball kernel and QAC pilot runner.
- `test_qac_microcanonical.py`, `test_qac_curveball.py`: regression and exact small-fiber checks.
- `CURVEBALL_RESEARCH.md`: detailed derivation and evidence boundaries.
- `PROTOCOL.md`: confirmatory sampling and inference protocol.
- `EXECUTION_STATUS.md`: exact status of build-container, phone, and GitHub work.
