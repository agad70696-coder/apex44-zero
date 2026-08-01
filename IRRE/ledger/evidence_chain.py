import hashlib, json, time, sqlite3, base64, threading, os
from pathlib import Path
from cryptography.fernet import Fernet

try:
    from rfc3161ng import RemoteTimestamper
    TSA_AVAILABLE = True
except:
    TSA_AVAILABLE = False

DB_FILE = "evidence_chain.db"
ANCHOR_FILE = "evidence_chain.anchor.log"
MAX_DB_SIZE_BYTES = 1 * 1024
MAX_ANCHOR_SIZE_BYTES = 10 * 1024 * 1024

def get_fernet():
    key_b64 = os.getenv("IRRE_ENCRYPTION_KEY")
    if not key_b64:
        key = Fernet.generate_key()
        return Fernet(key), False
    try:
        f = Fernet(key_b64.encode() if len(key_b64)==44 else base64.urlsafe_b64encode(key_b64.encode().ljust(32)[:32]))
        return f, True
    except:
        return Fernet(Fernet.generate_key()), False

FERNET, HAS_KEY = get_fernet()

class EvidenceChain:
    def __init__(self, db_file=DB_FILE):
        self.db_file = Path(db_file)
        self.anchor_file = Path(ANCHOR_FILE)
        self.lock = threading.Lock()
        self.conn = sqlite3.connect(str(self.db_file), check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self._create_table()
        self._load_chain_memory()

    def _enc(self, s: str) -> str:
        if not HAS_KEY:
            return s
        return FERNET.encrypt(s.encode()).decode()

    def _dec(self, s: str) -> str:
        if not HAS_KEY or not s:
            return s
        try:
            if s.startswith("gAAAA"):
                return FERNET.decrypt(s.encode()).decode()
            return s
        except:
            return s

    def _create_table(self):
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS blocks (
            idx INTEGER PRIMARY KEY,
            prev_hash TEXT, ai_hash TEXT, quantum_seal TEXT,
            public_key TEXT, algorithm TEXT,
            timestamp REAL, tsa_token TEXT,
            merkle_root TEXT, block_hash TEXT, metadata TEXT
        )""")
        self.conn.commit()

    def _load_chain_memory(self):
        cur = self.conn.execute("SELECT * FROM blocks ORDER BY idx")
        rows = cur.fetchall()
        if not rows:
            self._create_genesis()

    def _create_genesis(self):
        block = {
            "index": 0, "prev_hash": "0"*64, "ai_hash": "GENESIS",
            "quantum_seal": "GENESIS", "public_key": "GENESIS",
            "algorithm": "GENESIS", "timestamp": time.time(),
            "tsa_token": "GENESIS", "merkle_root": "0"*64,
            "metadata": {"note": "Genesis"}
        }
        block["block_hash"] = self._hash_block(block)
        block["merkle_root"] = block["block_hash"]
        self._insert_block(block)
        self._append_anchor(block["block_hash"])

    def _hash_block(self, b):
        s = f"{b['index']}\x00{b['prev_hash']}\x01{b['ai_hash']}\x00{b['quantum_seal']}\x01{b['public_key']}\x00{b['timestamp']}\x01{b.get('tsa_token','')}\x00{b.get('merkle_root','')}"
        return hashlib.sha3_256(s.encode()).hexdigest()

    def _get_tsa(self, data_str):
        if not TSA_AVAILABLE:
            return None
        try:
            ts = RemoteTimestamper("https://freetsa.org/ts
