from dataclasses import dataclass
import hashlib
@dataclass(frozen=True)
class Evidence:
    id: str; claim_id: str; source_url: str; quote: str; sha256_quote: str
    def is_valid(self):
        assert self.source_url.startswith(("http://","https://"))
        assert len(self.quote) > 50
        assert hashlib.sha256(self.quote.encode()).hexdigest() == self.sha256_quote
        return True
