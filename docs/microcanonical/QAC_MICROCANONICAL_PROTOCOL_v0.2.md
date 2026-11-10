# Confirmatory protocol — QAC Microcanonical v0.2

## 1. Frozen primary statistics

For every graph sampled from the fixed-degree fiber, calculate:

- `T_BLOCK`: degree-class block deviance relative to the canonical BiCM fit on the observed matrix;
- `H_ROOT`: P-free within-root-degree-class Bernoulli KL heterogeneity;
- `H_VERSE_NON_SINGLETON`: the within-verse heterogeneity restricted to root-degree classes containing at least two roots;
- `H_VERSE_SINGLETON`: the separate singleton-root-class component (reported, not interpreted as verse-vs-comparable-root heterogeneity);
- `MAX_ROOT`: maximum individual root contribution, calibrated against the maximum over all roots per replicate;
- `MAX_VERSE`: maximum individual verse contribution, calibrated against the maximum over all verses per replicate.

`H_VERSE = H_VERSE_SINGLETON + H_VERSE_NON_SINGLETON`. Do not compare `H_VERSE / H_ROOT` as a direct measure of relative verse-vs-root effect: the two decompositions have different grouping structures, and singleton root-degree classes contribute mechanically to `H_VERSE`.

All primary statistics and upper-tail directions must be frozen before confirmatory sampling. Specific roots (e.g. `Alw`, `nzl`, `k*b`) and selected verses remain exploratory because they were identified after observing the data. They require a maximum-statistic correction or an independent hold-out design.

## 2. Target distribution

The target is the uniform distribution on all simple binary matrices with the exact observed row and column degree vectors. For independent-edge BiCM, conditioning on every exact row and column degree makes the likelihood constant across this fiber. This is the exact canonical-to-microcanonical conditional relationship.

## 3. Kernel correctness

Two kernels are available:

### 2-switch

- explicit probability-1/2 hold;
- choose two distinct edge slots uniformly;
- perform the 2×2 endpoint exchange only when the two new edges are absent;
- invalid proposals are self-loops.

### Curveball

- explicit probability-1/2 hold;
- choose an unordered row pair uniformly;
- keep common neighbors fixed;
- randomly allocate the symmetric difference to the two rows with the original first-row unique-neighbor cardinality.

For Curveball, forward and reverse allocations have the same row-pair probability and the same number of possible allocations. Thus off-diagonal transitions are symmetric. Every 2-switch is represented by a one-neighbor Curveball trade; the bipartite 2-switch state graph is connected. The half-hold makes the chain aperiodic.

Every chain must pass exact row-degree, column-degree, edge-count, binary-simplicity, and X/Y/E counter rebuild checks. A failure blocks the sample and invalidates the affected run.

## 4. Mixing design

Minimum pilot design:

- at least four independent random streams;
- independently seeded initialization prefixes;
- explicit burn-in and thinning recorded in proposals, not only in accepted trades;
- retained traces of at least 50 states per chain for diagnostic screens;
- exact parameters, RNG seeds, software versions and all source/matrix/order hashes recorded;
- edge overlap, edge turnover, Hamming distance fraction, and pairwise initialization overlap recorded;
- multiple burn-in and thinning choices compared.

The current starts are produced by independent random prefixes from the observed graph. This is not a proof of overdispersed initialization. Do not describe them as overdispersed; retain the receipt flag `overdispersed_initialization_established=false` unless a defensible design establishes it.

## 5. Diagnostics

Report:

- rank-normalized/folded split-Rhat;
- Geyer-style ESS approximation and `MCSE / SD`;
- trace and autocorrelation review;
- pairwise initial-state overlap;
- distance-from-observed distributions in adjacent non-overlapping windows;
- two-sample KS D as an effect size only.

Do not compute or report ordinary iid KS p-values for serially dependent MCMC windows. Do not use distance-distribution stability as a standalone stopping rule; another graph statistic may remain unmixed after the scalar distance distribution stabilizes.

The configured thresholds in code (Rhat ≤ 1.01, ESS ≥ 400, MCSE/SD ≤ 0.05) are operational screens only. Passing them is not proof of stationarity or rapid mixing.

## 6. Theory applicability

The two sufficient rapid-mixing screens from Erdős et al. (2018) are evaluated against the exact row/column degree extrema in each QAC run. The QAC summary already available fails both screens, but the source replay must regenerate them. A failed sufficient condition is not evidence of slow mixing.

Carstens & Kleer (2018) prove that Curveball rapidly mixes whenever the corresponding switch chain does. Therefore this comparison does not establish a QAC rapid-mixing certificate when the currently screened switch conditions do not apply. Other theorems may still apply; their assumptions must be checked explicitly.

## 7. Inference

No p-values are authorized by a pilot. Once a separate review accepts the mixing evidence:

- estimate upper-tail probabilities from retained, approximately stationary samples;
- report effective sample size and Monte Carlo uncertainty;
- use batch means or a spectral variance estimator that respects serial dependence;
- compare 2-switch and Curveball estimates as a kernel-sensitivity check;
- adjust the frozen primary hypothesis family with a prespecified Holm or another justified multiplicity procedure;
- calibrate `MAX_ROOT` and `MAX_VERSE` using per-replicate maxima.

Do not use an iid `+1` Monte Carlo p-value formula as if serially dependent MCMC draws were independent replicates. Report unresolved dependence and sensitivity instead of manufacturing an exact p-value.

## 8. Interpretation boundary

Even an accepted graph-level result applies only to the pinned ROOT-only binary incidence matrix and the stated fixed-degree null. It does not, by itself, explain Arabic roots, repeated token counts, syntax, semantic context, tafsir, or any theological claim. Linguistic interpretation requires a separate, source-linked analysis of the actual verses and morphological forms.
