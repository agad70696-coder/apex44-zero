import hashlib, json, time, sqlite3, base64, threading
from pathlib import Path

try:
    from rfc3161ng import RemoteTimestamper
    TSA_AVAILABLE = True
except:
    TSA_AVAILABLE = False

DB_FILE = "evidence_chain.db"
ANCHOR_FILE = "evidence_chain.anchor.log"

class EvidenceChain:
    def __init__(self, db_file=DB_FILE):
        self.db_file = Path(db_file)
        self.anchor_file = Path(ANCHOR_FILE)
        self.lock = threading.Lock()
        self.conn = sqlite3.connect(str(self.db_file), check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self._create_table()
        self._load_chain_memory()

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
        else:
            self.chain = []
            for r in rows:
                self.chain.append({
                    "index": r[0], "prev_hash": r[1], "ai_hash": r[2],
                    "quantum_seal": r[3], "public_key": r[4], "algorithm": r[5],
                    "timestamp": r[6], "tsa_token": r[7], "merkle_root": r[8],
                    "block_hash": r[9], "metadata": json.loads(r[10])
                })

    def _create_genesis(self):
        genesis_hash = "0"*64
        block = {
            "index": 0, "prev_hash": "0"*64, "ai_hash": "GENESIS",
            "quantum_seal": "GENESIS", "public_key": "GENESIS",
            "algorithm": "GENESIS", "timestamp": time.time(),
            "tsa_token": "GENESIS", "merkle_root": genesis_hash,
            "metadata": {"note": "Genesis"}
        }
        block["block_hash"] = self._hash_block(block)
        block["merkle_root"] = block["block_hash"]
        self._insert_block(block)
        self._append_anchor(block["block_hash"])
        self.chain = [block]

    def _hash_block(self, b):
        s = f"{b['index']}{b['prev_hash']}{b['ai_hash']}{b['quantum_seal']}{b['public_key']}{b['timestamp']}{b.get('tsa_token','')}{b.get('merkle_root','')}"
        return hashlib.sha3_256(s.encode()).hexdigest()

    def _get_tsa(self, data_str):
        if not TSA_AVAILABLE:
            return None
        try:
            ts = RemoteTimestamper("https://freetsa.org/tsr", hashname="sha256")
            token = ts.timestamp(data=data_str.encode())
            return base64.b64encode(token).decode()[:256]
        except:
            return None

    def _insert_block(self, b):
        self.conn.execute("INSERT INTO blocks VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (b
