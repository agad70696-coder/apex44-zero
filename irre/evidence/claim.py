from dataclasses import dataclass
import hashlib

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
