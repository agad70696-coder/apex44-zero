# APEX44 Scientific Control Gate

This gate replaces the old placeholder rows where an observation of \`"pending"\` was incorrectly paired with \`"passed": true\`.

## Scope

The executable contract covers S1, S2, S3, S4, S5, S6, S9, S10, S11, S12, S13, S14, S15, and S16. Existing S7/S8 checks remain separate smoke controls. The report status \`BLOCKED\` is intentional until real, scoped observations and provenance are supplied.

## Important interpretation limits

- The numeric thresholds in \`scientific_control_contract.json\` are proposed operational defaults. They require scientific review and preregistration before a real evaluation; they are not established scientific constants.
- The gate's passing unit tests exercise the evaluator using synthetic fixtures only. They do not mark the project's scientific controls as passed.
- Each observation requires a subject commit SHA, dataset SHA-256, model identifier, structured metrics, and evidence records with source, role, and SHA-256.
- Missing observations or invalid provenance produce \`BLOCKED\`; measured acceptance violations produce \`FAIL\`.
- \`PASS_SCOPED\` never grants production-release authority. This subsystem always emits \`release_promotion_authority: NONE\`.

## Run

From repository root:

\`\`\`sh
python APEX44/04-evaluation/scientific_control_gate.py
\`\`\`

Without an observation file, this writes a blocked report to stdout and exits with code 2 by design. To evaluate a frozen JSON observation document:

\`\`\`sh
python APEX44/04-evaluation/scientific_control_gate.py --observations path/to/observations.json --output path/to/report.json
\`\`\`

Run only the software/evaluator tests (these are not scientific results):

\`\`\`sh
python -m pytest -q APEX44/04-evaluation/tests/test_controls.py APEX44/04-evaluation/tests/test_scientific_control_gate.py
\`\`\`
