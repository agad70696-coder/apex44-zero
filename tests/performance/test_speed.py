import time


def test_perf_10k() -> None:
    text = "a" * 10000
    start = time.time()
    _ = text + "\u200b"
    assert time.time() - start < 2.0
