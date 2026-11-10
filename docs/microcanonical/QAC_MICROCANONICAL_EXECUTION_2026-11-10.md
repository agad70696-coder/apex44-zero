# QAC Microcanonical v0.2 — Android execution record
Date: 2026-11-10 (Africa/Cairo)
Worktree: `~/apex44-qac-microcanonical-20261110`
Branch: `research/qac-microcanonical-v0.1`
Base: `cbd879b8745e5df00c40e6da3578e153efcd35b4`

## Artifact and installation evidence

- Release ZIP: 51,803 bytes; SHA-256 `a49754af79b47db1785d21e42a1c43380f9ae71752c78707b3388b56aac52efb`.
- ZIP integrity: PASS; all 17 entries in `MANIFEST.sha256`: PASS.
- Android Termux: Python 3.13.13, NumPy 2.4.4, SciPy 1.18.0.
- `py_compile`: PASS; package pytest: 33/33 PASS (13.08 s); both synthetic smoke runners: exit 0.
- The four production code/test files were copied into this isolated worktree; SHA-256 equality with their staged copies was checked.

## Pinned source replay

- Morphology source SHA-256: `a1d12923815341face765083805d2148ed2d9f5cc3f7d6665219d887675d8c46`.
- Reference pipeline SHA-256: `125c6816f59c2fdbe192bc1b18657efa91b89c28221d272efee79e69933ce59b`.
- Full matrix: 6,236 × 1,642; active matrix: 6,214 × 1,642; NNZ: 44,431.
- Active row degree classes: 39; column degree classes: 173; row/column degree sums both equal 44,431.
- Curveball receipt reports `pipeline_matrix_parity=PASS_SCOPED`; canonical reference fit accepted, maximum row residual 5.19e-11 and column residual 1.12e-9.

## QAC Curveball pilot 1 (small diagnostic)

- Receipt: `artifacts/microcanonical/qac_curveball_pilot_20261110_small.json`.
- Receipt SHA-256: `aa74f13cfbb99fcb92470f0ff70543d1fa94f92f539c30761932aeefa254e2dc`.
- Design: 4 chains; 5,000 initialization proposals + 1,000 burn-in proposals + 50 retained samples × 100 proposals; seeds 20261130–20261133.
- Each chain: 11,000 proposals, 5,296–5,345 changed trades, acceptance rate 0.481–0.486; invariant validations were run every 1,000 proposals and at chain completion.
- Initialization overlap with observed graph: 0.742–0.747; final overlap: 0.531–0.537. These starts are distinct but are not certified overdispersed.
- Retained draws: 200 total, so the configured ESS threshold 400 is unattainable in this run (maximum possible ESS 200).
- Rank-normalized/folded split-Rhat ranged 1.431–2.352; ESS estimates 10.09–22.02; MCSE/SD 0.213–0.315. All diagnostic screens failed.
- Four adjacent-window distance comparisons each had KS-D=1.0. This is a descriptive effect size only; no KS p-values were computed and no stopping authority is granted.
- Decision: `MIXING_NOT_ESTABLISHED`; `NOT_ESTABLISHED` statistical significance; `NOT_COMPUTED` microcanonical tail probabilities; `PROMOTION_AUTHORITY=NONE`.

## Theory and interpretation boundary

The screened Erdős et al. (2018) Theorem 2 and Theorem 3 sufficient conditions do not apply to this QAC degree sequence. This is not proof of slow mixing. The Curveball kernel's fixed-margin stationary target and tested degree invariants do not certify finite-run convergence. No p-values, statistical significance, linguistic interpretation, or theological conclusion follow from this pilot.

## QAC Curveball pilot 2 (extended diagnostic)

- Receipt: `artifacts/microcanonical/qac_curveball_pilot_20261110_extended.json`.
- Receipt SHA-256: `5ecf598c3a352f6156d3780e0aa39eb468f2373347352d736afea5a16203405e`; 2,344,504 bytes; process exit 0.
- Design: 4 chains; 10,000 independent seeded initialization proposals + 5,000 burn-in proposals + 150 retained samples × 100 proposals per chain; 30,000 proposals per chain, 120,000 total; seeds 20261230–20261233.
- Each chain: 14,483–14,674 changed trades; acceptance rate 0.4828–0.4891; 14,905–15,085 explicit lazy holds; 421–448 valid no-change trades. Periodic invariant checks every 1,000 proposals completed without error.
- Initialization overlap with observed graph: 0.5556–0.5687; pairwise chain-initialization edge overlap: 0.3340–0.3433. The receipt deliberately retains `overdispersed_initialization_established=false`; low pairwise overlap alone is not a proof of overdispersion.
- Final overlap with observed graph: 0.2196–0.2301; edge turnover: 0.7699–0.7804. Hamming distance fraction: 0.00670–0.00680. The sampler materially changes edges while retaining margins; this is not evidence of convergence by itself.
- 600 retained draws make the ESS threshold 400 attainable, but the observed ESS estimates were only 10.17–32.82. Rank-normalized/folded split-Rhat ranged 1.327–2.292; MCSE/SD ranged 0.175–0.314. All 8 monitored statistics failed all operational screens (`Rhat≤1.01`, `ESS≥400`, `MCSE/SD≤0.05`).
- 20 adjacent-window distance comparisons (5 per chain, window size 25) all had KS-D=1.0. This is descriptive only; no KS p-values were computed; `stopping_authority=NONE`.
- Related switch-chain screen: Theorem 2 fails (`Δ=1879` versus upper bound `149.05`); Theorem 3 fails (`lhs=86342` versus `rhs=4335`). The associated lazy 2-switch kernel-rate ratio is 26,348.87, but the screened sufficient theorem hypotheses are not met. Neither result proves slow mixing.
- Decision unchanged: `MIXING_NOT_ESTABLISHED`; `NOT_ESTABLISHED` statistical significance; `NOT_COMPUTED` microcanonical tail probabilities; linguistic interpretation `NOT_ESTABLISHED`; `PROMOTION_AUTHORITY=NONE`.

The extended run strengthens the diagnostic evidence that finite-run convergence has not been established; it does not justify interpreting QAC root/verse contributions as statistically significant or promoting any linguistic finding.

## Repository safety

All implementation and pilot artifacts are confined to the isolated research branch. The original `~/apex44-zero` worktree was not modified, and `main` was not modified.

### Subsequent publication audit (2026-11-10)

The original execution run did not itself verify remote publication. A subsequent local/remote audit confirmed:

- Repository: `agad70696-coder/apex44-zero`.
- Published branch: `research/qac-microcanonical-v0.1`.
- Execution commit: `7b2382c5153107b937f14beeff79b14f1a59cc20`, based on remote `main` commit `cbd879b8745e5df00c40e6da3578e153efcd35b4`.
- GitHub comparison at audit time: 1 commit ahead, 0 behind, 13 changed files.
- Local isolated branch HEAD and `origin/research/qac-microcanonical-v0.1` resolved to the same commit; the isolated worktree had zero tracked or untracked changes.
- `git diff --check origin/main...HEAD` passed.
- The original worktree remained on its separate branch with its pre-existing modifications; no cleanup, reset, or checkout was performed there.

This verifies publication of the research branch and its execution artifacts only. It does not certify statistical mixing, authorize inferential claims, constitute independent review, or imply merge into `main`. Pull-request and review state are tracked separately in GitHub.

### Scope clarification for the theorem screen

The receipt field `switch_mixing_theory_screen` evaluates sufficient conditions for the associated lazy 2-switch chain (including its rate comparison), not the Curveball proposal law. It is included only as the related-chain screen relevant to the Curveball rapid-mixing theorem transfer. The screen's failure is not evidence that Curveball mixes slowly; it means the cited sufficient result does not certify the associated chain for this sequence, so no rapid-mixing conclusion transfers from it.

## Permanent-tree verification

After copying into the permanent paths, `py_compile` passed and pytest was rerun from the isolated repository root against `APEX44/04-evaluation/tests/test_qac_microcanonical.py` and `test_qac_curveball.py`: 33/33 passed in 16.57 s (`EXIT_CODE=0`). `git diff --check`: PASS. The staging directory is retained outside the repository; the permanent code/tests and two QAC pilot receipts remain in the isolated branch.
