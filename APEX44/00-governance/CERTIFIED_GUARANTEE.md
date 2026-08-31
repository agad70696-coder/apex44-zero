# CERTIFIED GUARANTEE v1.0 - ISO 25010 + ASVS L2 + SLSA L3 + SSDF

Construction valid but inference not yet:
The 80-node graph is computationally valid as an observed representation, but its topology is not yet inferentially calibrated

Rule: No result becomes claim stronger than weakest Gate
Gate0: Provenance W3C PROV + OpenLineage + SLSA/in-toto + SHA256 + git SHA + uv.lock
Gate1-4: Same IDs, Same Normalization, Same Estimand, Same Edge Definition
Gate5: Projection-Aware Null Ensemble (10k bipartite configuration model)
Gate6: Holm/BH correction
Gate7: Specification Curve (RAW vs NORM, cosine/jaccard/PMI)
Gate8: Adversarial Reproduction + Sigstore Rekor

Quality Model ISO 25010:2023 - 9 characteristics must be measured
Security ASVS L2 + SSDF + SLSA L3 + signed commits + protected branches
Engineering: Google mandatory code review for all commits
