import hashlib
from dataclasses import dataclass


@dataclass
class Claim:
    id: str
    text: str
    owner: str
    timestamp: str

    def hash(self) -> str:
        return hashlib.sha256(self.text.encode()).hexdigest()[:16]

    def is_valid(self) -> bool:
        return len(self.text) > 0 and len(self.owner) > 0


@dataclass
class Evidence:
    claim_id: str
    type: str
    data: str
    confidence: float

    def is_strong(self) -> bool:
        return self.confidence >= 0.8

    def verify(self, claim) -> bool:
        return self.claim_id == claim.id and self.confidence > 0.5


def test_claim_creation_valid() -> None:
    c = Claim(id="1", text="العلم نور", owner="Amr", timestamp="2026-07-29")
    assert c.is_valid()


def test_claim_invalid_empty() -> None:
    c = Claim(id="2", text="", owner="", timestamp="2026-07-29")
    assert not c.is_valid()


def test_claim_hash_stable() -> None:
    c = Claim(id="3", text="تفاحة", owner="Amr", timestamp="2026-07-29")
    assert c.hash() == c.hash()


def test_evidence_strong() -> None:
    e = Evidence(claim_id="1", type="invisible", data="watermark", confidence=0.9)
    assert e.is_strong()


def test_evidence_weak() -> None:
    e = Evidence(claim_id="1", type="linguistic", data="weak", confidence=0.3)
    assert not e.is_strong()


def test_evidence_verifies_claim() -> None:
    c = Claim(id="1", text="العلم نور", owner="Amr", timestamp="2026-07-29")
    e = Evidence(claim_id="1", type="semantic", data="proof", confidence=0.85)
    assert e.verify(c)
