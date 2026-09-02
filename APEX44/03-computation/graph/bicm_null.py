"""
BiCM: Bipartite Configuration Model
- Generates ensemble preserving degree sequences
- Projection-aware null = projection of BiCM-generated bipartite networks
- Statistically-validated projection: link if shared neighbors significant
"""


def bicm_projection_null(bipartite_graph, n_samples=10000) -> None:
    # 1. Preserve degrees L and Gamma as ensemble expectations
    # 2. Generate n_samples BiCM networks
    # 3. Project each
    # 4. Compute co-occurrence distribution
    # 5. Return p-values for each edge in 80-node graph
    pass


def specification_curve(normalizations=None, metrics=None, taus=None) -> None:
    # هل البنية تبقى عبر كل المواصفات أم تنهار؟
    # الطفرة الحقيقية تبقى عبر المنحنى
    pass
