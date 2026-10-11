# Audit: commit 84ba90e805d8427c4be57b965046353849b8720b

Date of review: 2026-10-11

## Scope and decision

This review covers the committed QAC-derived matrix bundle and the claims attached to it. The four NPZ outputs and JSON summaries are present, but the repository snapshot does not close the provenance chain needed to promote the results as independently reproduced real-data evidence.

Current disposition: REVIEW_REQUIRED; evidence status PARTIAL_EVIDENCE; promotion authority NONE.

## Findings

1. **Source closure is missing.** DRS_real_data.json refers to quranic-corpus-morphology-0.4.txt and records a SHA-256, line count, and byte-size claim, but the source file is not in the inspected repository tree. Its bytes and source digest cannot be recomputed from this snapshot.
2. **No checked-in producer reproduces the committed matrix.** apply_to_qac.py discovers qac_batch*.py files and extracts regex matches from their source text; its fallback fabricates placeholder observations, and build_biadj adds edges to empty rows and columns. It does not parse the named QAC morphology text. bicm_10k_ensemble.py has a hard-coded 5x4 example under __main__. Neither binds its outputs to the committed 6236x1642 matrix.
3. **Method equivalence is not established.** The result metadata describes an analytic Chung-Lu/Poisson-tail calculation with Holm correction, whereas the candidate implementation performs sampled BiCM operations. No committed replay record shows that the listed method produced the published arrays.
4. **Artifact identity is only partially recorded.** The report has short SHA-256 prefixes for two artifacts and no complete digest inventory binding all four arrays, labels, source, and producer together.
5. **CI failure on main is independent.** Self-Evolve run #156 (run ID 38136630526) stopped at the test step because pytest was not installed (No module named pytest). The open repair PR already installs pytest; this audit is being added to that PR rather than changing main directly.

## Repairs

- Downgraded the real-data claim to REVIEW_REQUIRED, with PARTIAL_EVIDENCE and promotion_authority=NONE.
- Replaced the historical comparison's affirmative verdict with NOT_VERIFIED; the counts remain reported outputs, not independently reproduced findings.
- Added reproducibility limitations to both result metadata files without changing the binary arrays or inventing replacement numerical results.
- Added regression checks for source/replay closure, NPZ byte identity where checksums are recorded, dimensions, stored entry counts, symmetry of the two significance masks, and root-label uniqueness.

## Requirements for scientific promotion

Supply the unmodified QAC morphology v0.4 source or an auditable acquisition receipt; check in a deterministic producer that reads that exact source and records its full SHA-256; record full SHA-256 hashes for every output; run it in a clean environment; and attach a replay receipt binding source, code, parameters, seed, and outputs. Statistical assumptions and family-wise/FDR calculations must then be re-evaluated from the executable producer. Until then, retain these arrays as analysis artifacts but keep their real-data and historical-comparison claims review-only.
