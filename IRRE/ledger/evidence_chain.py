import sqlite3, hashlib, json, threading, re
from datetime import datetime, timezone
from pathlib import Path
from IRRE.pqc.hybrid_crypto import HybridCryptoV8
from IRRE.pqc.pqc_signer import PQCSignerV8

BASE_DIR = Path("data").resolve()
BASE_DIR.mkdir(parents=True, exist_ok=True)

def _safe_db_path(p: str) -> Path:
    return (BASE_DIR / Path(p).name).resolve()

def _valid_hash(h: str) -> bool:
    return bool(re.fullmatch(r"[a-fA-F0-9]{64}", h))

class PersistentForensicChain:
    def __init__(self, db_path="forensic_chain.db"):
        self._lock = threading.Lock()
        self.db_path = _safe_db_path(db_path)
        self.crypto = HybridCryptoV8()
        self.signer = PQCSignerV8()
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False, timeout=10.0)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.create_chain()

    def create_chain(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS evidence_chain (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp_utc TEXT NOT NULL,
                evidence_hash TEXT NOT NULL,
                chained_hash TEXT NOT NULL UNIQUE,
                prev_hash TEXT NOT NULL,
                data_json BLOB NOT NULL,
                signature BLOB NOT NULL
            )
        """)
        self.conn.commit()
        cur = self.conn.execute("SELECT COUNT(*) FROM evidence_chain")
        if cur.fetchone()[0] == 0:
            gh = hashlib.sha256(b"APEX-GENESIS-V8-PQC").hexdigest()
            enc = self.crypto.encrypt(b"{}")
            sig = self.signer.sign(gh)
            self.conn.execute(
                "INSERT INTO evidence_chain (timestamp_utc, evidence_hash, chained_hash, prev_hash, data_json, signature) VALUES (?,?,?,?,?,?)",
                (datetime.now(timezone.utc).isoformat(), gh, gh, "0"*64, enc, sig)
            )
            self.conn.commit()

    def add_evidence(self, evidence_hash, data):
        with self._lock:
            if not _valid_hash(evidence_hash): raise ValueError("Invalid hash")
            raw = json.dumps(data, sort_keys=True)
            if len(raw) > 100*1024: raise ValueError("Payload too large")
            cur = self.conn.execute("SELECT chained_hash FROM evidence_chain ORDER BY id DESC LIMIT 1")
            prev = cur.fetchone()
            prev_hash = prev[0] if prev else "0"*64
            chained = hashlib.sha256(f"{prev_hash}{evidence_hash}".encode()).hexdigest()
            enc_data = self.crypto.encrypt(raw.encode())
            sig = self.signer.sign(chained)
            self.conn.execute(
                "INSERT INTO evidence_chain (timestamp_utc, evidence_hash, chained_hash, prev_hash, data_json, signature) VALUES (?,?,?,?,?,?)",
                (datetime.now(timezone.utc).isoformat(), evidence_hash, chained, prev_hash, enc_data, sig)
            )
            self.conn.commit()
            return chained

    def verify_chain(self) -> bool:
        with self._lock:
            prev = "0"*64
            for ch, ph in self.conn.execute("SELECT chained_hash, prev_hash FROM evidence_chain ORDER BY id"):
                if ph!= prev and prev!= "0"*64: return False
                prev = ch
            return True
