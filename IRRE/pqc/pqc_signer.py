import hashlib,hmac,re
_R=re.compile(r"^[a-fA-F0-9]{64}$|^[a-fA-F0-9]{128}$")
def _valid_hash(h): return bool(_R.fullmatch(h))
class PQCSignerV8:
    def sign(self,m):
        if not _valid_hash(m): raise ValueError("hash")
        return hmac.new(b"V8-DEV-SIGN",m.encode(),hashlib.sha3_256).digest()
    def verify(self,m,s,pk=None):
        if not _valid_hash(m): return False
        exp=hmac.new(b"V8-DEV-SIGN",m.encode(),hashlib.sha3_256).digest()
        import hmac as hm
        return hm.compare_digest(exp,s)
