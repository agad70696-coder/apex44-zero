# Method references — APEX44 / QAC Microcanonical v0.2

1. **Carstens, Corrie Jacobien & Kleer, Pieter (2018).** *Speeding up Switch Markov Chains for Sampling Bipartite Graphs with Given Degree Sequence.* APPROX/RANDOM 2018, LIPIcs 116, 36:1–36:18. DOI: https://doi.org/10.4230/LIPIcs.APPROX-RANDOM.2018.36

   Relevance: formal comparison between switch and Curveball Markov chains. Their result is that Curveball is rapidly mixing whenever the corresponding switch chain is rapidly mixing. This is conditional on a switch-chain rapid-mixing result applying to the degree sequence; it is not a standalone QAC mixing certificate.

2. **Erdős, Péter L.; Mezei, Tamás Róbert; Miklós, István; Soltész, Dániel (2018).** *Efficiently sampling the realizations of bounded, irregular degree sequences of bipartite and directed graphs.* PLOS ONE 13(8), e0201995. DOI: https://doi.org/10.1371/journal.pone.0201995

   Relevance: exact fixed-degree state space, connectivity of bipartite realizations under 2-switches, uniform stationary law for the lazy symmetric switch chain, and two sufficient rapid-mixing conditions screened in this project. The full Theorem 3 statement gives the inclusive `<=` inequality; the abstract summarizes it with `<`. The test and implementation use the full theorem statement. This boundary issue does not alter the recorded QAC result because its left side greatly exceeds its right side.

3. **Godard, Karl & Neal, Zachary P. (2022).** *fastball: A fast algorithm to randomly sample bipartite graphs with fixed degree sequences.* Journal of Complex Networks 10(6), cnac049. DOI: https://doi.org/10.1093/comnet/cnac049

   Relevance: Curveball is described as an established fixed-degree sampler; Fastball is a separate proposed algorithm with improved asymptotic complexity and a C++ performance demonstration. Fastball is not implemented in this release.

4. **Neal, Zachary P. (2025).** *A stopping rule for randomly sampling bipartite networks with fixed degree sequences.* Social Networks 80, 59–64. DOI: https://doi.org/10.1016/j.socnet.2024.09.001

   Relevance: proposes a stopping diagnostic based on stabilization of the distribution of distances between sampled networks and the observed network. This package reports only adjacent-window KS D effect sizes and no p-values or automatic stopping authority. The published empirical performance does not establish validity for every large, irregular degree sequence.

5. **Vehtari, Aki et al. (2021).** *Rank-normalization, folding, and localization: An improved R-hat for assessing convergence of MCMC.* Bayesian Analysis 16(2), 667–718. DOI: https://doi.org/10.1214/20-BA1221

   Relevance: motivates rank-normalized and folded split-Rhat. The implementation is a transparent screening approximation; the confirmatory analysis should validate diagnostics against reference implementations.

6. **Stan Development Team.** *Stan Reference Manual — Effective sample size.* https://mc-stan.org/docs/reference-manual/analysis.html#effective-sample-size

   Relevance: autocorrelation-aware effective sample size and Geyer-style paired autocorrelation sequences. The code uses a screening approximation, not a full reproduction of every Stan diagnostic.
