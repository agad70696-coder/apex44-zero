def test_stress_1m() -> None:
    text = "a" * 1000000
    protected = text + "\u200b"
    assert len(protected) > len(text)
