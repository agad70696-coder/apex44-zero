def test_invisible_watermark() -> None:
    text = "نص أصلي"
    protected = f"{text}\u200b"  # Zero-Width Space
    assert "\u200b" in protected  # العلامة غير المرئية موجودة
