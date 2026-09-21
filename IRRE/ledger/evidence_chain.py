import hashlib
import json
import sqlite3
from datetime import datetime, timezone


def quantum_hash(data):
    payload = data.encode() if isinstance(data, str) else data
    return hashlib.shake_256(payload).hexdigest(64)


def _valid_hash(value):
    if not isinstance(value, str):
        return False
    if len(value) not in (64, 128):
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


class EvidenceChain:
    """
    SQLite-backed evidence chain.

    Compatibility contract preserved for existing callers:
      EvidenceChain()
      ledger.add(ai_hash, pq_seal, metadata=...)
      ledger.verify()
      ledger.chain[0]["ai_hash"]

    The constructor also accepts the newer dependency-injection arguments:
      EvidenceChain(db, crypto, signer)
    """

    def __init__(
        self,
        db=":memory:",
        crypto=None,
        signer=None,
    ) -> None:
        self.db = db
        self.crypto = crypto
        self.signer = signer

        self.conn = sqlite3.connect(
            db,
            check_same_thread=False,
        )

        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS evidence_chain (
                id INTEGER PRIMARY KEY,
                timestamp_utc TEXT,
                evidence_hash TEXT,
                chained_hash TEXT,
                prev_hash TEXT,
                data_json TEXT,
                signature TEXT
            )
            """
        )

        self.conn.commit()
        self.chain = []
        self._load_chain()

    def _load_chain(self):
        rows = self.conn.execute(
            """
            SELECT
                id,
                timestamp_utc,
                evidence_hash,
                chained_hash,
                prev_hash,
                data_json,
                signature
            FROM evidence_chain
            ORDER BY id
            """
        ).fetchall()

        for (
            row_id,
            timestamp_utc,
            evidence_hash,
            chained_hash,
            prev_hash,
            data_json,
            signature,
        ) in rows:
            try:
                decoded = json.loads(data_json) if data_json else {}
            except (TypeError, ValueError):
                decoded = {}

            metadata = decoded.get("metadata", {})
            if not isinstance(metadata, dict):
                metadata = {}

            self.chain.append(
                {
                    "index": row_id - 1,
                    "ai_hash": evidence_hash,
                    "pq_seal": signature,
                    "metadata": metadata,
                    "prev_hash": prev_hash,
                    "block_hash": chained_hash,
                    "timestamp_utc": timestamp_utc,
                }
            )

    def add(self, ai_hash, pq_seal, metadata=None):
        if not _valid_hash(ai_hash):
            raise ValueError("ai_hash must be a 64- or 128-hex-character hash")

        if not isinstance(pq_seal, str) or not pq_seal:
            raise ValueError("pq_seal must be a non-empty string")

        if metadata is None:
            metadata = {}

        if not isinstance(metadata, dict):
            raise TypeError("metadata must be a dict")

        prev_hash = (
            self.chain[-1]["block_hash"]
            if self.chain
            else "0" * 128
        )

        block_hash = quantum_hash(f"{prev_hash}{ai_hash}")
        timestamp_utc = datetime.now(timezone.utc).isoformat()

        block = {
            "index": len(self.chain),
            "ai_hash": ai_hash,
            "pq_seal": pq_seal,
            "metadata": metadata,
            "prev_hash": prev_hash,
            "block_hash": block_hash,
            "timestamp_utc": timestamp_utc,
        }

        self.chain.append(block)

        data_json = json.dumps(
            {"metadata": metadata},
            sort_keys=True,
            ensure_ascii=False,
        )

        self.conn.execute(
            """
            INSERT INTO evidence_chain (
                timestamp_utc,
                evidence_hash,
                chained_hash,
                prev_hash,
                data_json,
                signature
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                timestamp_utc,
                ai_hash,
                block_hash,
                prev_hash,
                data_json,
                pq_seal,
            ),
        )

        self.conn.commit()
        return block

    def verify(self):
        previous_hash = "0" * 128

        for index, block in enumerate(self.chain):
            if not isinstance(block, dict):
                return False

            ai_hash = block.get("ai_hash")
            block_hash = block.get("block_hash")
            prev_hash = block.get("prev_hash")
            pq_seal = block.get("pq_seal")

            if not _valid_hash(ai_hash):
                return False

            if not _valid_hash(block_hash):
                return False

            if prev_hash != previous_hash:
                return False

            if not isinstance(pq_seal, str) or not pq_seal:
                return False

            expected_hash = quantum_hash(
                f"{previous_hash}{ai_hash}"
            )

            if block_hash != expected_hash:
                return False

            if block.get("index") != index:
                return False

            previous_hash = block_hash

        return True

    def verify_chain(self):
        return {"valid": self.verify()}

    def export(self):
        return json.dumps(
            self.chain,
            sort_keys=True,
            ensure_ascii=False,
            indent=2,
        )
