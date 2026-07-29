from irre.evidence.claim import Claim, Evidence

def test_claim_creation_valid():
    c = Claim(id="1", text="العلم نور", owner="Amr", timestamp="2026-07-29")
    assert c.is_valid() == True

def test_claim_invalid_empty():
    c = Claim(id="2", text="", owner="", timestamp="2026-07-29")
    assert c.is_valid() == False

def test_claim_hash_stable():
    c = Claim(id="3", text="تفاحة", owner="Amr", timestamp="2026-07-29")
    assert c.hash() == c.hash()

def test_evidence_strong():
    e = Evidence(claim_id="1", type="invisible", data="watermark", confidence=0.9)
    assert e.is_strong() == True

def test_evidence_weak():
    e = Evidence(claim_id="1", type="linguistic", data="weak", confidence=0.3)
    assert e.is_strong() == False

def test_evidence_verifies_claim():
    c = Claim(id="1", text="العلم نور", owner="Amr", timestamp="2026-07-29")
    e = Evidence(claim_id="1", type="semantic", data="proof", confidence=0.85)
    assert e.verify(c) == True
