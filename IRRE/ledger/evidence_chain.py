import hashlib
import re
import sqlite3


def quantum_hash(d):
    return hashlib.shake_256(d.encode() if isinstance(d, str) else d).hexdigest(64)


_64 = re.compile(r"^[a-fA-F0-9]{64}$")
_128 = re.compile(r"^[a-fA-F0-9]{128}$")


def _valid_hash(h):
    return bool(_64.fullmatch(h) or _128.fullmatch(h))


class EvidenceChain:
    def __init__(self, db, crypto, signer) -> None:
        self.conn = sqlite3.connect(db, check_same_thread=False)
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS evidence_chain (id INTEGER PRIMARY KEY,timestamp_utc TEXT,evidence_hash TEXT,chained_hash TEXT,prev_hash TEXT,data_json TEXT,signature TEXT)"
        )

    def verify_chain(self):
        cur = self.conn.cursor()
        rows = cur.execute(
            "SELECT id,evidence_hash,chained_hash,prev_hash FROM evidence_chain ORDER BY id"
        ).fetchall()
        if not rows:
            return {"valid": True}
        pc = None
        for idx, (_rid, ev, ch, ph) in enumerate(rows):
            if idx > 0 and ph != pc:
                return {"valid": False}
            if quantum_hash(f"{ph}{ev}") != ch:
                return {"valid": False}
            pc = ch
        return {"valid": True}
