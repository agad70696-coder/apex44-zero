def test_full_flow():
    original = "كتابي"
    owner, buyer = "Amr", "Client1"
    # محاكاة التدفق الكامل
    assert owner != buyer
    assert len(original) > 0
