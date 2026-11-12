# QAC fixed-degree 2x2-switch pilot — 2026-11-12

## Purpose and relation to existing work

This record adds a four-chain fixed-degree 2x2-switch diagnostic to the existing QAC Microcanonical v0.2 research branch. It is distinct from the 2026-11-10 Curveball pilots and from Profile Fiber sampling. The present experiment fixes the complete observed row- and column-degree sequences only; it does not preserve the per-node X and Y profiles.

## Pinned data identity

The matrix already present in this research worktree at:

APEX44/03-computation/output/B_real_6236x1642.npz

was independently hashed and matches the Root-only matrix used by the Termux execution:

- Matrix SHA-256: a75fdf4d57bd9448a74607fff9b9ddf31c26e2c3f356eb9fd40d19aa511c8c3a
- Shape: 6,236 × 1,642
- Binary edges: 44,431
- Corpus SHA-256: a1d12923815341face765083805d2148ed2d9f5cc3f7d6665219d887675d8c46
- Corpus bytes: 6,309,503

No second copy of the matrix or corpus is included. The pinned research-branch matrix is the input reference.

## C4 arithmetic correction

The observed number of 4-cycles is 2,427,533, calculated after promoting the incidence matrix to int64 before multiplication. Three computations agree:

1. Root-pair overlap projection using int64.
2. Verse-pair overlap projection using int64.
3. Rebuilding the matrix from row-neighbor sets and recomputing using int64.

The earlier value 1,599,245 came from an int8 sparse multiplication and is rejected as numeric overflow. The int8 product produced 119 negative overlap cells and 152 stored overlap cells that differed from the int64 product.

The definition used is the sum, over unordered root pairs, of choose(common verses, 2), equivalently the same sum over unordered verse pairs.

## Pilot design

- Kernel: select two distinct edge slots uniformly; exchange their column endpoints if both cross-edges are absent; otherwise remain at the current state.
- Chains: 4.
- Seeds: 2026111201, 2026111202, 2026111203, 2026111204.
- Proposals per chain: 500,000.
- Burn-in proposals: 100,000.
- C4 recorded every 50,000 proposals from proposal 100,000 through 500,000.
- All chains initialized from the same observed matrix. Independent random streams do not establish overdispersed initialization.

Each proposal is accounted for as an accepted switch, a same-row/column rejection, or an occupied-cross-edge rejection. The runner checks exact row and column degree preservation at chain completion.

## Results

| Seed | Accepted | Acceptance rate | Final recorded C4 |
|---:|---:|---:|---:|
| 2026111201 | 432,387 | 86.4774% | 1,891,193 |
| 2026111202 | 432,403 | 86.4806% | 1,910,525 |
| 2026111203 | 432,318 | 86.4636% | 1,848,066 |
| 2026111204 | 432,611 | 86.5222% | 1,895,223 |

Across 36 recorded C4 snapshots:
- Minimum: 1,838,445
- Maximum: 1,915,830
- Mean: 1,885,248.11

All four pilot receipts record exact preservation of the observed row and column degrees. The portable audit independently verifies the matrix and corpus hashes, the C4 arithmetic, proposal accounting, trace schedule, and the degree-invariant flags recorded by the runner.

## Kernel and interpretation boundary

The proposal is symmetric: selecting two distinct edge slots has the same probability in either direction, and a valid switch has a unique reverse switch using the same two slots. Invalid proposals are self-loops. For this fixed degree sequence, every state has a positive self-loop probability because at least one row has degree greater than one, so selecting two edges incident to that same row leaves the state unchanged. The standard connectivity of simple bipartite degree-sequence realizations by 2-switches supplies irreducibility; together these facts identify the uniform fixed-degree target and aperiodicity.

These kernel properties do not certify finite-run mixing. The pilot retained only nine C4 snapshots per chain and all chains started from the same observed state. It does not establish autocorrelation, ESS, rank-normalized/folded split-Rhat, burn-in adequacy, tail convergence, or calibrated Monte Carlo p-values.

A lower C4 trace than the observed C4 is descriptive, not a significance result. No inferential tail probability is reported.

## Decision

- Source identity: PASS_SCOPED
- int64 C4 replay: PASS_SCOPED
- int8 C4 value 1,599,245: REJECTED_NUMERIC_OVERFLOW
- Pilot execution record: PASS_SCOPED
- Mixing: NOT_ESTABLISHED
- Inferential p-value: NOT_COMPUTED
- Promotion authority: NONE

This result does not replace or upgrade the 2026-11-10 Curveball diagnostics, whose mixing screens failed. It is an additional fixed-degree 2-switch pilot only.

## Reproduction and audit artifacts

- artifacts/microcanonical/qac_2x2_switch_pilot_20261112.json
- artifacts/microcanonical/qac_2x2_switch_pilot_runner_20261112.py — exact Termux execution source, retained unchanged; its original path assumptions are specific to the recorded phone environment.
- artifacts/microcanonical/qac_2x2_switch_pilot_audit_termux_original_20261112.json
- artifacts/microcanonical/qac_2x2_switch_pilot_audit_termux_original_20261112.py — exact original Termux audit source.
- APEX44/03-computation/audit_qac_2x2_switch_pilot.py — portable read-only verifier for this repository layout.
- artifacts/microcanonical/qac_2x2_switch_pilot_audit_20261112.json — portable verifier output.

Run the portable verifier from the repository root:

python APEX44/03-computation/audit_qac_2x2_switch_pilot.py

The verifier writes only the versioned audit JSON under artifacts/microcanonical. It does not modify the matrix, corpus, original pilot result, production files, or main branch.

## Governance

This addition is isolated on research/qac-microcanonical-2x2-pilot-20261112, based on the already-published QAC Microcanonical research branch. It is not merged into main, and it does not grant promotion authority.

Checksum manifest: docs/microcanonical/QAC_2X2_SWITCH_PILOT_SHA256_2026-11-12.txt
