def test_old_watermark_still_detected() -> None:
    old_protected = "نص قديم\u200b"
    assert "\u200b" in old_protected
