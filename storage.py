import sqlite3
import hashlib
import json
import os
import threading
import ipaddress
import re
from datetime import datetime, timezone
from pathlib import Path

try:
    from cryptography.fernet import Fernet, InvalidToken
    CRYPTO_AVAILABLE = True
except ImportError:
    Fernet = None
    CRYPTO_AVAILABLE = False

BASE_DIR = Path("data").resolve()
BASE_DIR.mkdir(parents=True, exist_ok=True)
MAX_DB_SIZE = 10 * 1024 * 1024
MAX_ENTRY_SIZE = 100 * 1024

def _safe_db_path(p: str) -> Path:
    path = Path(p)
    # امنع Path Traversal
    safe = (BASE_DIR / path.name).resolve()
    try:
        safe.relative_to(BASE_DIR)
    except ValueError:
        safe = (BASE_DIR / "forensic_chain.db").resolve()
    return safe

def _valid_hash(h: str) -> bool:
    return bool(re.fullmatch(r"[a-fA-F0-9]{64}", h))

class PersistentForensicChain:
    def __init__(self, db_path="forensic_chain.db"):
        self._lock = threading.Lock()
        self.db_path = _safe_db_path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        enc_key = os.getenv("IRRE_ENCRYPTION_KEY")
        self.fernet = None
        if CRYPTO_AVAILABLE and enc_key:
            try:
                self.fernet = Fernet(enc_key.encode())
            except Exception:
                self.fernet = None

        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False, timeout=10.0)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA foreign_keys=ON;")
        self.create_chain()

    def _check_limits(self):
        if self.db_path.exists() and self.db_path.stat().st_size > MAX_DB_SIZE:
            raise RuntimeError("DB size limit - DoS protection")

    def _encrypt(self, text: str) -> bytes:
        b = text.encode()
        return self.fernet.encrypt(b) if self.fernet else b

    def _decrypt(self, token: bytes) -> str:
        try:
            return self.fernet.decrypt(token).decode() if self.fernet else token.decode()
        except Exception:
            raise ValueError("Decryption failed - tampered data")

    def create_chain(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS evidence_chain (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp_utc TEXT NOT NULL,
                evidence_hash TEXT NOT NULL,
                chained_hash TEXT NOT NULL UNIQUE,
                merkle_root TEXT NOT NULL,
                prev_hash TEXT NOT NULL,
                data_json BLOB NOT NULL,
                rfc3161_token BLOB,
                gps_lat REAL,
                gps_lon REAL,
                ip_address TEXT
            )
        """)
        self.conn.commit()
        # Genesis block
        cur = self.conn.execute("SELECT COUNT(*) FROM evidence_chain")
        if cur.fetchone()[0] == 0:
            genesis_hash = hashlib.sha256(b"APEX-GENESIS-V7").hexdigest()
            self.conn.execute(
                "INSERT INTO evidence_chain (timestamp_utc, evidence_hash, chained_hash, merkle_root, prev_hash, data_json, rfc3161_token, gps_lat, gps_lon, ip_address) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (datetime.now(timezone.utc).isoformat(), genesis_hash, genesis_hash, genesis_hash, "0"*64, self._encrypt("{}"), None, None, None, None)
            )
            self.conn.commit()

    def add_evidence(self, evidence_hash, data, merkle_root=None, rfc3161_token=None, gps_lat=None, gps_lon=None, ip=None):
        with self._lock:
            self._check_limits()
            if not _valid_hash(evidence_hash):
                raise ValueError("Invalid evidence_hash format")

            raw_json = json.dumps(data, sort_keys=True)
            if len(raw_json) > MAX_ENTRY_SIZE:
                raise ValueError("Entry too large")

            if gps_lat is not None and not (-90 <= float(gps_lat) <= 90):
                raise ValueError("Invalid lat")
            if gps_lon is not None and not (-180 <= float(gps_lon) <= 180):
                raise ValueError("Invalid lon")
            if ip:
                ipaddress.ip_address(ip)

            cur = self.conn.execute("SELECT chained_hash FROM evidence_chain ORDER BY id DESC LIMIT 1")
            row = cur.fetchone()
            prev_hash = row[0] if row else "0"*64

            chained_data = f"{prev_hash}{evidence_hash}{merkle_root or ''}"
            chained_hash = hashlib.sha256(chained_data.encode()).hexdigest()
            merkle_root = merkle_root or chained_hash

            enc_data = self._encrypt(raw_json)
            enc_token = self._encrypt(rfc3161_token) if rfc3161_token else None

            self.conn.execute(
                "INSERT INTO evidence_chain (timestamp_utc, evidence_hash, chained_hash, merkle_root, prev_hash, data_json, rfc3161_token, gps_lat, gps_lon, ip_address) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (datetime.now(timezone.utc).isoformat(), evidence_hash, chained_hash, merkle_root, prev_hash, enc_data, enc_token, gps_lat, gps_lon, ip)
            )
            self.conn.commit()
            return self.conn.execute("SELECT last_insert_rowid()").fetchone()
