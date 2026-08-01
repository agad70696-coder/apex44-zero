import os
import sqlite3
import hashlib
import json
import secrets
import threading
from datetime import datetime, timezone
from pathlib import Path

try:
    from cryptography.fernet import Fernet, InvalidToken
    CRYPTO_AVAILABLE = True
except ImportError:
    Fernet = None
    InvalidToken = Exception
    CRYPTO_AVAILABLE = False

ALLOWED_BASE = Path("data").resolve()
ALLOWED_BASE.mkdir(parents=True, exist_ok=True)

def _safe_path(p_str: str) -> Path:
    p = Path(p_str)
    resolved = (ALLOWED_BASE / p.name).resolve() if not p.is_absolute() else p.resolve()
    try:
        resolved.relative_to(ALLOWED_BASE)
    except ValueError:
        resolved = (ALLOWED_BASE / p.name).resolve()
    return resolved

DB_PATH = _safe_path(os.getenv("IRRE_DB_PATH", "evidence_chain.db"))
LOG_PATH = _safe_path(os.getenv("IRRE_ANCHOR_LOG", "evidence_chain.anchor.log"))
MAX_DB_SIZE = 10 * 1024 * 1024
MAX_LOG_SIZE = 50 * 1024
MAX_ENTRY_SIZE = 100 * 1024

class EvidenceChain:
    def __init__(self):
        self._lock = threading.Lock()
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        enc_key = os.getenv("IRRE_ENCRYPTION_KEY")
        self.fernet = None
        if CRYPTO_AVAILABLE and enc_key:
            try:
                self.fernet = Fernet(enc_key.encode())
            except Exception:
                self.fernet = None

        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False, timeout=10.0)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA foreign_keys=ON;")
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS evidence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                hash TEXT NOT NULL UNIQUE,
                prev_hash TEXT,
                data_enc BLOB NOT NULL,
                data_hash TEXT NOT NULL
            )
        """)
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_hash ON evidence(hash);")
        self.conn.commit()

    def _check_limits(self):
        if DB_PATH.exists() and DB_PATH.stat().st_size > MAX_DB_SIZE:
            raise RuntimeError("DB limit exceeded")
        if LOG_PATH.exists() and LOG_PATH.stat().st_size > MAX_LOG_SIZE:
            raise RuntimeError("Log limit exceeded")

    def _hash(self, data: str) -> str:
        return hashlib.sha256(data.encode()).hexdigest()

    def add(self, data: dict) -> str:
        with self._lock:
            self._check_limits()
            if not isinstance(data, dict):
                raise ValueError("data must be dict")
            raw = json.dumps(data, sort_keys=True)
            if len(raw) > MAX_ENTRY_SIZE:
                raise ValueError("Entry too large")

            data_hash = self._hash(raw)
            cur = self.conn.execute("SELECT hash FROM evidence ORDER BY id DESC LIMIT 1")
            row = cur.fetchone()
            prev_hash = row[0] if row else "0"*64

            chain_str = prev_hash + data_hash + datetime.now(timezone.utc).isoformat()
            block_hash = self._hash(chain_str)

            enc = self.fernet.encrypt(raw.encode()) if self.fernet else raw.encode()

            self.conn.execute(
                "INSERT INTO evidence (timestamp, hash, prev_hash, data_enc, data_hash) VALUES (?,?,?,?,?)",
                (datetime.now(timezone.utc).isoformat(), block_hash, prev_hash, enc, data_hash)
            )
            self.conn.commit()
            return block_hash

    def verify_integrity(self) -> bool:
        with self._lock:
            cur = self.conn.execute("SELECT hash, prev_hash, data_enc, data_hash FROM evidence ORDER BY id")
            prev = "0"*64
            for h, ph, enc, dh in cur.fetchall():
                if ph!= prev:
                    return False
                try:
                    raw = self.fernet.decrypt(enc).decode() if self.fernet else enc.decode()
                except Exception:
                    return False
                if self._hash(raw)!= dh:
                    return False
                prev = h
            return True
