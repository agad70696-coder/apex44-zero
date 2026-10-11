# Forensic audit and correction of commit 84ba90e805d8427c4be57b965046353849b8720b

Review and corrected replay: 2026-10-11.

## Decision

The original commit's reported significance masks were not safe to rely on. The earlier audit was incomplete because it did not identify integer overflow in the projection. This repair corrects the computation, includes the exact QAC morphology v0.4 source as an unmodified file, and adds a source-to-output reproduction command and blocking CI checks.

Current disposition: REPRODUCED_SCOPED for source-to-array reproduction; overall scientific claim remains REVIEW_REQUIRED; promotion authority remains NONE.

## Confirmed source identity

The exact source file was recovered from the existing local project workspace at PHASE2_CLEAN/source/quranic-corpus-morphology-0.4.txt. Its raw SHA-256 matches the source hash already recorded in the original result report:

a1d12923815341face765083805d2148ed2d9f5cc3f7d6665219d887675d8c46

Its raw size is 6,309,503 bytes and its line count is 128,276. The file was added to the repair branch byte-for-byte, preserving the copyright/license block and CRLF line endings. A source manifest records version, byte length, line count, and digest. This closes the input's byte-identity gap in the repository snapshot; it does not independently authenticate upstream custody.

## Critical computational defect: int8 overflow

The previous projection calculation multiplied an int8 incidence matrix directly. Counts over the signed 8-bit range overflowed. Inspection of the pre-repair matrix found 1,580 negative stored entries and a maximum of 127, which is impossible for a co-occurrence count. The old projection had 318,274 stored entries; the corrected int64 projection has 318,278 stored entries and maximum common-verse count 2,567. A total of 2,108 matrix coordinates differ, and two undirected pairs had been erased by wraparound to zero.

The incidence matrix remains binary int8 for storage efficiency, but is promoted to int64 before multiplication. The corrected projection is symmetric, nonnegative, and has a zero diagonal.

## Corrected statistical calculation

The prior counts 616 (Holm) and 3729 (BH/FDR) came from the overflowed matrix and a multiple-testing family restricted to observed nonzero edges. They are explicitly invalidated. The corrected analysis tests the full family of 1,347,261 unordered root/lemma pairs, including zero-observation pairs with p-value 1. The expected count uses a degree-based Poisson-tail approximation and is not an exact sampled BiCM null.

Corrected counts: Holm 542 undirected pairs; Benjamini-Hochberg 1,685 undirected pairs. The historical figure of 1,816 has not been recreated under a source-bound comparable method; the verdict remains NOT_VERIFIED.

## Reproducibility and tests

Read-only verification from the repository root:

python APEX44/03-computation/reproduce_qac_analysis.py --verify

To intentionally regenerate matrices and metadata:

python APEX44/03-computation/reproduce_qac_analysis.py --write

The runner verifies the source hash and source manifest, rebuilds the incidence matrix from the raw corpus, performs the projection using wide integers, recalculates both correction procedures across the full pair family, and semantically compares every matrix and root label with the stored files. Full SHA-256 values for committed outputs are recorded in both report metadata files. These hashes establish byte identity of stored artifacts, not mathematical validity or upstream provenance by themselves.

The repair also adds a regression test showing int8 overflow on a 300-common-neighbor synthetic fixture and a blocking quality-gate step that executes the targeted tests and the full source-to-output replay. Local result: PASS_SCOPED_REPRODUCTION; targeted tests: pass.

## Boundaries

Reproducing a result from a fixed corpus establishes computational reproducibility, not the validity of the degree-based Poisson approximation, root/lemma feature selection, linguistic interpretation, or comparison with a historical number. Those remain review-required. No promotion authority is granted.
