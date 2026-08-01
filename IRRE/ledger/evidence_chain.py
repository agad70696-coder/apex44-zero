import hashlib, json, time, sqlite3, base64, threading
from pathlib import Path

try:
    from rfc3161ng import RemoteTimestamper
    TSA_AVAILABLE = True
except:
    TSA_AVAILABLE = False

DB_FILE = "evidence_chain.db"
ANCHOR_FILE = "evidence_chain.anchor.log"
MAX_DB_SIZE_BYTES = 1 * 1024 * 1024 * 1024
MAX_ANCHOR_SIZE_BYTES = 10 * 1024 * 1024

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
        (b["index"], b["prev_hash"], b["ai_hash"], b["quantum_seal"],
         b["public_key"], b["algorithm"], b["timestamp"], b["tsa_token"],
         b["merkle_root"], b["block_hash"], json.dumps(b["metadata"])))
        self.conn.commit()

    def _append_anchor(self, block_hash):
        if self.anchor_file.exists() and self.anchor_file.stat().st_size > MAX_ANCHOR_SIZE_BYTES:
            backup = self.anchor_file.with_suffix(".log.1")
            if backup.exists():
                backup.unlink()
            self.anchor_file.rename(backup)
        with open(self.anchor_file, "a") as f:
            f.write(block_hash + "\n")

    def _check_disk_limit(self):
        if self.db_file.exists() and self.db_file.stat().st_size > MAX_DB_SIZE_BYTES:
            raise RuntimeError("Evidence DB reached max size 1GB - rotation required")

    def add(self, ai_hash, quantum_seal, metadata, public_key, algorithm):
        with self.lock:
            self._check_disk_limit()
            prev = self.conn.execute("SELECT * FROM blocks ORDER BY idx DESC LIMIT 1").fetchone()
            prev_hash = prev[9] if prev else "0"*64
            prev_merkle = prev[8] if prev else "0"*64
            idx = (prev[0] + 1) if prev else 0
            ts = time.time()
            tsa = self._get_tsa(f"{prev_hash}{ai_hash}{ts}")
            temp_hash = hashlib.sha3_256(f"{idx}{prev_hash}{ai_hash}{quantum_seal}{ts}".encode()).hexdigest()
            merkle_root = hashlib.sha3_256(f"{prev_merkle}{temp_hash}".encode()).hexdigest()
            block = {
                "index": idx, "prev_hash": prev_hash, "ai_hash": ai_hash,
                "quantum_seal": quantum_seal, "public_key": public_key,
                "algorithm": algorithm, "timestamp": ts, "tsa_token": tsa or "LOCAL",
                "merkle_root": merkle_root, "metadata": metadata
            }
            block["block_hash"] = self._hash_block(block)
            self._insert_block(block)
            self._append_anchor(block["block_hash"])
            return block

    def verify(self):
        cur = self.conn.execute("SELECT * FROM blocks ORDER BY idx")
        rows = cur.fetchall()
        if not rows:
            return False
        if self.anchor_file.exists():
            anchors = [l.strip() for l in self.anchor_file.read_text().splitlines() if l.strip()]
            if len(anchors)!= len(rows):
                return False
            if anchors[-1]!= rows[-1][9]:
                return False
        for i in range(1, len(rows)):
            curr, prev = rows[i], rows[i-1]
            if curr[1]!= prev[9]:
                return False
            b = {"index": curr[0], "prev_hash": curr[1], "ai_hash": curr[2],
                 "quantum_seal": curr[3], "public_key": curr[4], "timestamp": curr[6],
                 "tsa_token": curr[7], "merkle_root": curr[8], "metadata": {}}
            if self._hash_block(b)!= curr[9]:
                return False
        return True

    def get_len(self):
        cur = self.conn.execute("SELECT COUNT(*) FROM blocks")
        return cur.fetchone()[0]
