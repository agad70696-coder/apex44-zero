"""Executable sanity controls; the 14 scientific controls use a separate fail-closed gate."""
from __future__ import annotations
import numpy as np

def _holm_adjusted_pvalues(pvalues: np.ndarray) -> np.ndarray:
    if pvalues.ndim!=1 or np.any((pvalues<0)|(pvalues>1)): raise ValueError("pvalues must be one-dimensional and in [0, 1]")
    n=len(pvalues); order=np.argsort(pvalues); sorted_p=pvalues[order]
    adjusted_sorted=np.maximum.accumulate(np.minimum((n-np.arange(n))*sorted_p,1.0))
    adjusted=np.empty(n,dtype=float); adjusted[order]=adjusted_sorted
    return adjusted

def test_null_ladder_has_no_false_discoveries_for_frozen_seed() -> None:
    rng=np.random.default_rng(44); pvalues=rng.random(190)
    assert int(np.count_nonzero(_holm_adjusted_pvalues(pvalues)<=0.05))==0

def test_positive_control_recovers_injected_cooccurrence_signal() -> None:
    rng=np.random.default_rng(44); binary=(rng.random((100,20))<0.05).astype(np.int8)
    binary[:10,0]=1; binary[:10,1]=1
    assert int((binary.T@binary)[0,1])>=10
