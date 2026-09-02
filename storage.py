import hashlib
import json
import re
import sqlite3
import threading
from datetime import UTC, datetime
from pathlib import Path

from IRRE.pqc.hybrid_crypto import HybridCryptoV8

BASE_DIR = Path("data").resolve()
BASE_DIR.mkdir(parents=True, exist_ok=True)


def _safe_db_path(p: str) -> Path:
    return (BASE_DIR / Path(p).name).resolve()


def _valid_hash(h: str) -> bool:
    return bool(re.fullmatch(r"[a-fA-F0-9]{64}", h))


class PersistentForensicChain:
    def __init__(self, db_path="forensic_chain.db") -> None:
        self._lock = threading.Lock()
        self.db_path = _safe_db_path(db_path)
        self.crypto = HybridCryptoV8()
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False, timeout=10.0)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.create_chain()

    def create_chain(self) -> None:
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS evidence_chain (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp_utc TEXT NOT NULL,
                evidence_hash TEXT NOT NULL,
                chained_hash TEXT NOT NULL UNIQUE,
                prev_hash TEXT NOT NULL,
                data_json BLOB NOT NULL
            )
        """)
        self.conn.commit()
        cur = self.conn.execute("SELECT COUNT(*) FROM evidence_chain")
        if cur.fetchone()[0] == 0:
            gh = hashlib.sha256(b"APEX-GENESIS-V8-PQC").hexdigest()
            enc = self.crypto.encrypt(b"{}")
            self.conn.execute(
                "INSERT INTO evidence_chain (timestamp_utc, evidence_hash, chained_hash, prev_hash, data_json) VALUES (?,?,?,?,?)",
                (datetime.now(UTC).isoformat(), gh, gh, "0" * 64, enc),
            )
            self.conn.commit()

    def add_evidence(self, evidence_hash, data):
        with self._lock:
            if not _valid_hash(evidence_hash):
                raise ValueError("Bad hash")
            raw = json.dumps(data, sort_keys=True)
            cur = self.conn.execute(
                "SELECT chained_hash FROM evidence_chain ORDER BY id DESC LIMIT 1"
            )
            prev = cur.fetchone()
            prev_hash = prev[0] if prev else "0" * 64
            chained = hashlib.sha256(f"{prev_hash}{evidence_hash}".encode()).hexdigest()
            enc_data = self.crypto.encrypt(raw.encode())
            self.conn.execute(
                "INSERT INTO evidence_chain (timestamp_utc, evidence_hash, chained_hash, prev_hash, data_json) VALUES (?,?,?,?,?)",
                (
                    datetime.now(UTC).isoformat(),
                    evidence_hash,
                    chained,
                    prev_hash,
                    enc_data,
                ),
            )
            self.conn.commit()
            return chained
