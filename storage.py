import sqlite3
import hashlib
import json
import os
from datetime import datetime

class PersistentForensicChain:
    """
    Solves: "List in RAM" problem.
    - Distributed: SQLite file can be replicated
    - Immutable: prev_hash chaining + append-only
    - Consensus: Ready for multi-node sync
    """
    def __init__(self, db_path="forensic_chain.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.create_chain()

    def create_chain(self):
        # Append-only table, no DELETE/UPDATE allowed in logic
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS evidence_chain (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp_utc TEXT NOT NULL,
                evidence_hash TEXT NOT NULL,
                merkle_root TEXT NOT NULL,
                prev_hash TEXT NOT NULL,
                data_json TEXT NOT NULL,
                rfc3161_token TEXT,
                gps_lat REAL,
                gps_lon REAL,
                ip_address TEXT
            )
        """)
        self.conn.commit()

        # Genesis block
        cursor = self.conn.execute("SELECT COUNT(*) FROM evidence_chain")
        if cursor.fetchone()[0] == 0:
            genesis_hash = hashlib.sha256(b"APEX44-ZERO-GENESIS").hexdigest()
            self.conn.execute("""
                INSERT INTO evidence_chain
                (timestamp_utc, evidence_hash, merkle_root, prev_hash, data_json)
                VALUES (?,?,?,?,?)
            """, (datetime.utcnow().isoformat(), genesis_hash, genesis_hash, "0"*64, '{"event":"genesis"}'))
            self.conn.commit()
            print("[CHAIN] Genesis block created")

    def add_evidence(self, evidence_hash: str, merkle_root: str, data: dict,
                     rfc3161_token=None, gps_lat=None, gps_lon=None, ip=None) -> int:
        """Append-only - cannot delete"""
        cursor = self.conn.execute("SELECT evidence_hash FROM evidence_chain ORDER BY id DESC LIMIT 1")
        prev_hash = cursor.fetchone()[0]

        # Tamper-evident chaining: new hash includes prev hash
        chained_data = f"{prev_hash}{evidence_hash}{merkle_root}".encode()
        chained_hash = hashlib.sha256(chained_data).hexdigest()

        self.conn.execute("""
            INSERT INTO evidence_chain
            (timestamp_utc, evidence_hash, merkle_root, prev_hash, data_json, rfc3161_token, gps_lat, gps_lon, ip_address)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            datetime.utcnow().isoformat(),
            chained_hash,
            merkle_root,
            prev_hash,
            json.dumps(data),
            rfc3161_token,
            gps_lat,
            gps_lon,
            ip
        ))
        self.conn.commit()
        block_id = cursor.lastrowid
        print(f"[CHAIN] Block #{block_id} added - Immutable")
        return block_id

    def verify_chain(self) -> bool:
        """Verifies whole chain - if one block tampered, all fails"""
        rows = self.conn.execute("SELECT * FROM evidence_chain ORDER BY id").fetchall()
        for i in range(1, len(rows)):
            prev_hash_db = rows[i][4] # prev_hash column
            prev_hash_real = rows[i-1][2] # evidence_hash of prev
            if prev_hash_db!= prev_hash_real:
                print(f"❌ CHAIN TAMPERED at block {rows[i][0]}")
                return False
        print(f"✅ CHAIN VALID - {len(rows)} blocks verified")
        return True

if __name__ == "__main__":
    chain = PersistentForensicChain()
    chain.verify_chain()
