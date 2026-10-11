# Follow-up audit: isolate ROOT features and preserve representation typing

Date: 2026-10-11. Parent correction: c6ad72149b2e31b24da95a9fdb4a8ab1779c0a44.

## New semantic defect found and repaired

After repairing int8 arithmetic, a second inspection found the previous incidence builder pooled three different feature types into one column universe:
- 49,968 records with explicit ROOT features;
- 24,640 records that had no ROOT but fell back to LEM;
- 53,611 records that had neither and fell back to the surface/token field.

The resulting output was labelled as a root matrix even though the columns were semantically heterogeneous. The number of unique raw surface fallback values was only 151, which made the mixing visible in high-frequency columns such as conjunctions, particles, and determiners. This is a feature-type/ontology error, independent from the integer-overflow defect.

The primary graph now admits only explicit ROOT values. LEM, POS and surface/token values are not substituted into missing ROOT fields. The source is still preserved byte-for-byte and source-bound.

## Root-only corrected result

- Incidence B: [6236, 1642], 44,431 nonzero verse-root relations.
- Root labels: 1,642 unique explicit ROOT values.
- Projection: int64, 148,370 stored directed entries, maximum common-verse count 514.
- Tested family: 1,347,261 unordered pairs, including zero-observation pairs.
- Holm: 245 undirected pairs.
- Benjamini-Hochberg: 660 undirected pairs.

The intermediate mixed-feature/int64 analysis (542 Holm and 1,685 BH pairs) is retained only as an invalidated audit comparison. The previous mixed-feature/int8 analysis (616 and 3,729) is also invalidated. Neither number should be used as a root-only scientific result.

## Reproduction and release boundary

The runner APEX44/03-computation/reproduce_qac_analysis.py now parses explicit ROOT fields only, promotes the incidence matrix to int64 before multiplication, tests the full pair family, and semantically compares all output matrices and root labels. The blocking quality gate runs both the targeted tests and the clean replay.

Current status: REPRODUCED_SCOPED for root-only source-to-array reproduction; overall scientific claim REVIEW_REQUIRED; promotion authority NONE. The degree-based Poisson-tail expectation remains an approximation, not an exact sampled BiCM null. The historical figure of 1,816 has not been recreated under a comparable source-bound method.
