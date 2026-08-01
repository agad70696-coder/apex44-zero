import os, sqlite3, hashlib, json, secrets, threading
from datetime import datetime, timezone
from pathlib import Path

try:
    from cryptography.fernet import Fernet
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

DB_PATH = Path("evidence_chain.db")
LOG_PATH = Path("evidence_chain.anchor.log")
MAX_DB_SIZE = 1 * 1024 * 1024
MAX_LOG_SIZE = 10 * 1024 * 1024

class EvidenceChain:
    def __init__(self):
        self._lock = threading.Lock()
        enc_key = os.getenv("IRRE_ENCRYPTION_KEY")
        if CRYPTO_AVAILABLE and enc_key:
            self.fernet = Fernet(enc_key.encode() if isinstance(enc_key, str) else enc_key)
        else:
            self.fernet = None
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("CREATE TABLE IF NOT EXISTS chain (id INTEGER PRIMARY KEY, ts TEXT, ai_hash TEXT, quantum_seal TEXT, meta TEXT, pubkey TEXT, block_hash TEXT, merkle_root TEXT, tsa_token TEXT, algo TEXT)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_block ON chain(block_hash)")
        self.conn.commit()

    def _check_limits(self):
        if DB_PATH.exists() and DB_PATH.stat().st_size > MAX_DB_SIZE:
            raise RuntimeError("Evidence DB exceeded 1GB")
        if LOG_PATH.exists() and LOG_PATH.stat().st_size > MAX_LOG_SIZE:
            LOG_PATH.write_text(LOG_PATH.read_text()[-500000:], encoding='utf-8')

    def _enc(self, data: str) -> str:
        if not data:
            return data
        if self.fernet:
            return self.fernet.encrypt(data.encode()).decode()
        return data

    def _dec(self, data: str) -> str:
        if not data:
            return data
        if self.fernet:
            try:
                return self.fernet.decrypt(data.encode()).decode()
            except:
                return data
        return data

    def _merkle(self, left: str, right: str) -> str:
        return hashlib.sha256(b"\x01" + left.encode() + b"\x00" + right.encode()).hexdigest()

    def _hash_block(self, ts, ai_hash, seal, meta, pubkey):
        payload = f"{ts}{ai_hash}{seal}{json.dumps(meta, sort_keys=True)}{pubkey}".encode()
        return hashlib.sha256(payload).hexdigest()

    def add(self, ai_hash, quantum_seal, meta, public_key, algo="SPHINCS+"):
        with self._lock:
            self._check_limits()
            ts = datetime.now(timezone.utc).isoformat()
            seal_enc = self._enc(quantum_seal)
            pub_enc = self._enc(public_key)
            tsa_enc = self._enc(f"TSA-{secrets.token_hex(16)}")
            last = self.conn.execute("SELECT block_hash, merkle_root FROM chain ORDER BY id DESC LIMIT 1").fetchone()
            if last:
                prev_hash, prev_root = last
                merkle_root = self._merkle(prev_root, ai_hash)
            else:
                prev_hash = "0"*64
                merkle_root = hashlib.sha256(b"\x00" + ai_hash.encode()).hexdigest()
            block_hash = self._hash_block(ts, ai_hash, quantum_seal, meta, public_key)
            self.conn.execute("INSERT INTO chain (ts, ai_hash, quantum_seal, meta, pubkey, block_hash, merkle_root, tsa_token, algo) VALUES (?,?,?,?,?,?,?,?,?)",
                (ts, ai_hash, seal_enc, json.dumps(meta), pub_enc, block_hash, merkle_root, tsa_enc, algo))
            self.conn.commit()
            try:
                with open(LOG_PATH, "a", encoding="utf-8") as f:
                    f.write(f"{ts}|{block_hash}|{merkle_root}\n")
            except:
                pass
            return {"block_hash": block_hash, "merkle_root": merkle_root, "ts": ts}

    def verify(self):
        with self._lock:
            rows = self.conn.execute("SELECT ts, ai_hash, quantum_seal, meta, pubkey, block_hash, merkle_root FROM chain ORDER BY id").fetchall()
            if not rows:
                return True
            prev_root = None
            for r in rows:
                ts, ai_hash, seal_enc, meta_json, pub_enc, block_hash, merkle_root = r
                seal = self._dec(seal_enc)
                pub = self._dec(pub_enc)
                meta = json.loads(meta_json)
                calc = self._hash_block(ts, ai_hash, seal, meta, pub)
                if calc!= block_hash:
                    return False
                if prev_root is None:
                    exp = hashlib.sha256(b"\x00" + ai_hash.encode()).hexdigest()
                else:
                    exp = self._merkle(prev_root, ai_hash)
                if exp!= merkle_root:
                    return False
                prev_root = merkle_root
            return True

    def get_len(self):
        with self._lock:
            return self.conn.execute("SELECT COUNT(*) FROM chain").fetchone()[0]
