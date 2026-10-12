# APEX44 Scientific Control Gate

This gate replaces the placeholder control rows in which an observation of `"pending"` was incorrectly paired with `"passed": true`.

## Scope

The executable contract covers S1, S2, S3, S4, S5, S6, S9, S10, S11, S12, S13, S14, S15, and S16. Existing S7/S8 checks remain separate software smoke controls. With no real observations supplied, the report deliberately marks the fourteen scientific controls `BLOCKED`.

## Evidence identity and boundaries

Each observation requires a subject commit SHA, dataset SHA-256, model identifier, structured metrics, and evidence records containing a source label, evidence-root-relative file path, role, and SHA-256. The evaluator rereads the referenced file and recomputes SHA-256 over its bytes. Missing files, path escapes, and digest mismatches are `BLOCKED`.

A matching SHA-256 supports byte identity for the bytes read; it does not establish source origin, witness independence, semantic identity, evidentiary admissibility, or truth. Those remain separate review obligations.

## Thresholds and interpretation

The numeric thresholds in `scientific_control_contract.json` are proposed operational defaults. They require scientific review and preregistration before real evaluation; they are not established scientific constants. Synthetic fixtures test the evaluator's mechanics only and do not count as scientific evidence.

Missing observations or invalid provenance produce `BLOCKED`; measured acceptance violations produce `FAIL`. `PASS_SCOPED` never grants production-release authority: the report always emits `release_promotion_authority: NONE`.

## Run

From the repository root, the no-observation run prints a blocked report and exits with code 2 by design:

```sh
python APEX44/04-evaluation/scientific_control_gate.py
```

To evaluate a frozen JSON observation document whose `path` fields point to files under the repository root:

```sh
python APEX44/04-evaluation/scientific_control_gate.py --observations path/to/observations.json --evidence-root . --output path/to/report.json
```

Run the software/evaluator tests (not scientific-results tests):

```sh
python -m pytest -q APEX44/04-evaluation/tests/test_controls.py APEX44/04-evaluation/tests/test_scientific_control_gate.py
```

## Metric implementation notes (follow-up review)

- **S3 — surprisal calibration:** `I(P) = -log2(P)`. Equal probabilities may have equal surprisal values; unequal probabilities must preserve inverse ordering, within the configured numerical tolerance. Formula calibration remains a separate check.
- **S5 — annotation noise:** noise percentages must be actual integers (not Python booleans) in the inclusive range 0–100. Required levels must be present and unique.
- **S6 — representation stability:** rankings are compared with Kendall's tau-b, which adjusts for ties. The registered minimum (currently 0.8) is a proposed operational threshold requiring preregistration review.
- **S9 — generator bias:** evidence must identify an explicit non-negative integer seed or non-empty string seed so the fixture setup can be reproduced.
- **S15 — kill switch:** the observation records `unauthorized_override_rejected`; recording that an authority check merely occurred is insufficient. The positive test confirms rejection, and a negative regression verifies that an observed bypass fails the control.

These rules define evaluator behavior, not scientific truth. Tests use synthetic fixtures and cannot promote any of the fourteen controls without real, scoped observations and admissible evidence.
