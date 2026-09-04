# APEX44-ZERO - Audited 2026-09-04
Branch: research/g0-g10-gate e9b7c2e - VALID JSON

Built with love on Termux in Edfu, Aswan - Egypt

## Reproducibility - QAC 6236x80
- biadj_hash: 0be169fa1f1b66c2
- BiCM: solve_tool(method=newton, tolerance=1e-8)
- newton_steps=160, err_final=9.84e-09
- Ensemble: R=10000, seed=44, entropy depends on size

## Statistics - Truth-in-labeling fix
- Holm-Bonferroni step-down alpha/(m-i+1)
- NOT Bonferroni alpha/m
- p=[0.001,0.01,0.03,0.20] => [True,True,False,False]
- Bonferroni <= Holm <= BH

## Integrity - Tamper-Evident
- Canonical JSON RFC8785 sort_keys=True separators=,: 
- self_hash=SHA256(canonical)
- genesis prev_hash=null
- verify_chain() recomputes
- Limitation: tamper-evident, not tamper-proof

## PQC - NIST SP 800-208
- ML-DSA FIPS 204 core
- SLH-DSA FIPS 205 + LMS-W4-SHA256 RFC8554
- Hash-based security only

## Evidence
- evidence_chain.json VALID JSON
- python -m json.tool passes
- chain_head eb5558211f9514f2

## GATE
./scripts/quality-gate-strict.sh
