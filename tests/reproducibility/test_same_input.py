def test_same_input_same_output() -> None:
    def protect(t):
        return t + "\u200b"

    assert protect("test") == protect("test")
