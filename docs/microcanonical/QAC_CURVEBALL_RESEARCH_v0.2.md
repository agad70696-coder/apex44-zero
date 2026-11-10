# QAC Microcanonical v0.2 — Curveball research and design record

## 1. Research question

Can a second, faster-moving fixed-degree Markov kernel generate useful samples from the same microcanonical fiber as the 2-switch chain, while preserving every verse degree, every root degree, the binary constraint, and the edge count exactly?

The Curveball implementation is an alternative transition kernel over the same state space. It is not a new null hypothesis and does not change the target distribution.

## 2. State space and target

Let `B` be a simple binary bipartite incidence matrix. The fiber is

`Omega(r,c) = {B in {0,1}^{n x m}: B 1 = r and B^T 1 = c}`.

The target is the uniform law on `Omega(r,c)`. This is also the exact conditional distribution of a canonical independent-edge BiCM after conditioning on the complete observed row- and column-degree sequences: the BiCM likelihood is proportional to a factor depending only on those degrees, so it is constant throughout the fixed-margin fiber.

## 3. Lazy Curveball transition

At each proposal:

1. Hold with probability `1/2`.
2. Otherwise choose an unordered pair of distinct rows uniformly.
3. Let `C` be their common neighbors, `A` the first row's unique neighbors, and `D` the second row's unique neighbors. `A` and `D` are disjoint.
4. Let `U = A union D`. Choose a subset `A_new` uniformly from all subsets of `U` with cardinality `|A|`.
5. Assign `C union A_new` to the first row and `C union (U \ A_new)` to the second row.

### Exact invariants

- Each selected row retains its degree because `|A_new| = |A|` and the second row receives `|D|` unique neighbors.
- Each column degree is preserved because every column in `U` remains attached to exactly one of the selected rows; common neighbors remain attached to both.
- No duplicate edge can be created because each row receives a set, and the unique-neighbor allocation is a partition of `U`.
- All unselected rows are unchanged.

### Detailed balance

For a fixed selected row pair, the symmetric difference `U` and first-row allocation size `|A|` are invariants under reversal. A particular allocation has probability

`1 / binom(|U|, |A|)`

in both directions. The row-pair selection probability and the non-hold probability are also identical in both directions. Therefore every off-diagonal transition is symmetric. The uniform distribution on the fiber is stationary.

Every valid 2-switch is a special Curveball trade: choose a new first-row set by replacing one unique neighbor with one unique neighbor from the second row. Since 2-switches connect all simple bipartite realizations of a graphical degree sequence, the Curveball state graph is connected. The explicit half-hold makes the chain aperiodic.

These arguments establish the stationary target and irreducibility/aperiodicity. They do **not** provide a useful finite-run mixing-time bound for QAC.

## 4. Why add Curveball, and why not declare it solved

Carstens and Kleer (2018) establish a theoretical comparison: the Curveball chain is rapidly mixing whenever the corresponding switch chain is rapidly mixing. Their result does not create a rapid-mixing certificate for a degree sequence for which no applicable switch-chain theorem has been established. The published paper explicitly notes that rapid-mixing results are sequence-dependent. The QAC degree summary currently available does not satisfy the two screened sufficient conditions from Erdős et al. (2018):

- `Delta = 1,879`, whereas `sqrt(E/2) = 149.04865` for `E=44,431`.
- With column bounds `c1=1, c2=1,879` and row bounds `d1=1, d2=48`, Theorem 3 has left side `86,342` and right side `4,335`; its condition does not hold.

The full theorem statement gives the inclusive `<=` inequality in Theorem 3. The paper abstract uses a strict `<` in its prose summary; the implementation follows the full theorem statement. This boundary distinction does not affect QAC because `86,342` is far above `4,335`.

Failure of a sufficient condition is **not** evidence of slow mixing. It only means those two theorems do not certify rapid mixing for this degree sequence. Curveball may still mix adequately in practice, but that requires evidence specific to this state space and the statistics of interest.

## 5. Distance-distribution stability diagnostic

For each retained state, the implementation records:

- edge overlap: `|E_obs intersect E_sample| / E`;
- edge turnover: `1 - edge_overlap`;
- Hamming fraction over all matrix positions: `2 E (1 - edge_overlap) / (n_rows n_cols)`.

The edge-turnover measure is more interpretable on a sparse matrix; Hamming fraction is retained for direct matrix comparison, but its denominator is the full set of possible positions and may make changes look numerically small.

Following the idea explored by Neal (2025), the implementation compares empirical distributions of distances from the observed graph in adjacent, non-overlapping trace windows. It reports the two-sample KS `D` effect size only. It never reports a KS p-value, and it never treats distance stability as an automatic stopping rule. MCMC draws are serially dependent, and a distance distribution can stabilize before other graph features have mixed.

Neal's published stopping-rule study reports useful empirical performance on its studied cases, but that result is not a theorem for arbitrary large irregular degree sequences. It is used here as an additional diagnostic, not as a calibration authority.

## 6. QAC-specific safeguards

`run_qac_curveball_chains()`:

- rebuilds the pinned morphology source from `ROOT:` features only;
- requires exact parity with the legacy reference pipeline's matrix and ordered-root list;
- retains `(surah, ayah)` identifiers, source row indices, and active row indices;
- hashes source, matrix, active matrix, root order, verse order, and degree sequences;
- checks exact row/column degrees and X/Y/E class counters during the run;
- uses at least four independent random streams;
- records the overlap between each independently prefixed state and the observed network and the pairwise overlap between those states;
- explicitly records that these prefix-generated states are **not proven overdispersed**;
- refuses to overwrite an existing output receipt.

## 7. Diagnostics and inferential boundary

The run records rank-normalized/folded split-Rhat, a Geyer-style ESS approximation, and `MCSE / SD` for the predeclared statistics. The configured thresholds are engineering screens only. Passing them is not proof of stationarity. A confirmatory design should include trace review, sensitivity to initialization, burn-in and thinning, comparison of independent kernels, and a dependence-aware uncertainty estimate.

No formal microcanonical p-values are calculated by this version. No iid `+1` Monte Carlo formula is applied to correlated MCMC draws. No linguistic, semantic, tafsir, or miraculous-numerical claim is authorized by the graph-level result.

## 8. Future alternatives

Fastball (Godard & Neal, 2022) is a separate implementation with a published algorithmic improvement over Curveball and a C++ performance demonstration. It is not implemented here. It should be introduced as another independently tested kernel, not silently substituted for Curveball.

## References

- Carstens, C. J. & Kleer, P. (2018). *Speeding up Switch Markov Chains for Sampling Bipartite Graphs with Given Degree Sequence*. LIPIcs 116, 36:1–36:18. DOI: 10.4230/LIPIcs.APPROX-RANDOM.2018.36.
- Erdős, P. L., Mezei, T. R., Miklós, I. & Soltész, D. (2018). *Efficiently sampling the realizations of bounded, irregular degree sequences of bipartite and directed graphs*. PLOS ONE 13(8), e0201995. DOI: 10.1371/journal.pone.0201995.
- Godard, K. & Neal, Z. P. (2022). *fastball: A fast algorithm to randomly sample bipartite graphs with fixed degree sequences*. Journal of Complex Networks 10(6), cnac049. DOI: 10.1093/comnet/cnac049.
- Neal, Z. P. (2025). *A stopping rule for randomly sampling bipartite networks with fixed degree sequences*. Social Networks 80, 59–64. DOI: 10.1016/j.socnet.2024.09.001.
- Vehtari, A. et al. (2021). *Rank-normalization, folding, and localization: An improved R-hat for assessing convergence of MCMC*. Bayesian Analysis 16(2), 667–718. DOI: 10.1214/20-BA1221.
- Stan Development Team. *Stan Reference Manual: Effective sample size*. https://mc-stan.org/docs/reference-manual/analysis.html#effective-sample-size
