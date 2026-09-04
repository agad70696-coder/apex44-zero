from __future__ import annotations

import numpy as np


def holm_reference(p_values: list[float], alpha: float = 0.05) -> list[bool]:
    p = np.asarray(p_values, dtype=float)
    order = np.argsort(p)
    sorted_p = p[order]

    reject = np.zeros(len(p), dtype=bool)

    for i, value in enumerate(sorted_p):
        threshold = alpha / (len(p) - i)
        if value <= threshold:
            reject[order[i]] = True
        else:
            break

    return reject.tolist()


def test_holm_known_answer() -> None:
    p = [0.001, 0.01, 0.03, 0.20]
    expected = [True, False, False, False]

    assert holm_reference(p, 0.05) == expected
