# Scientific Evidence Schema

## 1. Purpose

This document defines the minimum structured representation required for
scientific evidence inside Scientific Kernel.

The schema exists to preserve provenance, reproducibility, uncertainty,
contradiction handling, and traceability between evidence and scientific
claims.

---

## 2. Evidence Object

Each evidence record should contain, where applicable:

- evidence_id
- source_id
- source_type
- source_location
- acquisition_date
- data_version
- observation
- measurement
- unit
- preprocessing
- methodology
- assumptions
- uncertainty
- confidence
- provenance
- supporting_references
- contradictory_references
- related_claims
- status
- created_at
- updated_at

---

## 3. Evidence Identity

`evidence_id` must uniquely identify an evidence record.

Identifiers must remain stable across revisions unless the underlying
evidence itself changes.

A modification to the interpretation of evidence must not silently replace
the original evidence record.

---

## 4. Provenance

Every evidence record must preserve sufficient provenance to answer:

1. Where did the evidence originate?
2. How was it acquired?
3. When was it acquired?
4. Which version was used?
5. What transformations were applied?
6. Which methodology produced the derived representation?

---

## 5. Observation vs Interpretation

The system must explicitly distinguish:

### Observation

What was directly observed, measured, retrieved, or recorded.

### Interpretation

What is inferred or concluded from the observation.

Interpretation must never be stored as though it were raw observation.

---

## 6. Uncertainty

Evidence may contain uncertainty.

The system should support:

- measurement uncertainty;
- sampling uncertainty;
- methodological uncertainty;
- model uncertainty;
- missing information;
- confidence intervals where applicable;
- qualitative uncertainty when numerical uncertainty is unavailable.

Absence of a numerical uncertainty value does not imply certainty.

---

## 7. Contradictory Evidence

Evidence that conflicts with another record must remain represented.

Contradictions should be explicitly linked rather than silently resolved.

A contradiction may result from:

- different measurements;
- different populations;
- different methodologies;
- different definitions;
- different time periods;
- data quality problems;
- genuine scientific disagreement.

---

## 8. Claims

Scientific claims must reference the evidence supporting them.

A claim may also reference:

- contradictory evidence;
- assumptions;
- derivations;
- computational tests;
- independent validation.

A claim without sufficient evidence must not be classified as validated.

---

## 9. Status Model

Evidence and claims should use explicit status values.

Recommended evidence statuses:

- raw
- structured
- validated
- disputed
- superseded
- rejected

Recommended claim statuses:

- proposed
- supported
- computationally_validated
- empirically_validated
- disputed
- rejected
- inconclusive
- open_problem

---

## 10. Versioning

Evidence records must be versionable.

Changes must preserve:

- previous version;
- change reason;
- changed fields;
- responsible process;
- timestamp;
- validation result.

Historical versions must remain recoverable.

---

## 11. Reproducibility Requirement

A derived result should be reproducible from:

- evidence identifiers;
- evidence versions;
- methodology version;
- algorithm version;
- parameters;
- execution environment;
- test results.

---

## 12. Minimum Quality Gate

An evidence record should not be considered complete unless the system
can determine, where applicable:

- identity;
- provenance;
- source;
- observation;
- methodology;
- version;
- uncertainty;
- validation status.

Missing information must be represented explicitly rather than fabricated.

---

## 13. Scientific Integrity Rule

Scientific Kernel must never manufacture missing evidence,
provenance, measurements, references, or validation results.

Unknown information must remain unknown.

---

## 14. Future Extensions

The schema may later be extended for:

- multimodal evidence;
- statistical distributions;
- causal relationships;
- temporal evidence;
- graph relationships;
- machine-learning features;
- formal proofs;
- computational experiments;
- benchmark results.

Extensions must remain backward-compatible where scientifically possible.

---

## 15. Schema Status

Status: Draft / Foundational

This schema is a versioned research artifact and may be revised when
stronger methodological requirements or evidence become available.
