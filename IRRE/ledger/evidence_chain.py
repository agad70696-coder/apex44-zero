"""SQLite-backed append-only evidence hash chain.

The structural hash-chain check is distinct from cryptographic signature verification. If
no signer or PQ verifier is configured, the result reports that absence rather than
promoting it to a signature-validation success.
"""
from __future__ import annotations

import base64
import hashlib
import json
import re
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

GENESIS_HASH = "0" * 128


def quantum_hash(data: str | bytes) -> str:
    raw = data.encode("utf-8") if isinstance(data, str) else data
    return hashlib.shake_256(raw).hexdigest(64)


_64 = re.compile(r"^[a-fA-F0-9]{64}$")
_128 = re.compile(r"^[a-fA-F0-9]{128}$")


def _valid_hash(value: str) -> bool:
    return isinstance(value, str) and bool(_64.fullmatch(value) or _128.fullmatch(value))


class EvidenceChain:
    """Append evidence to SQLite and verify its data hashes and predecessor links."""

    def __init__(
        self,
        db: str | Path = ":memory:",
        crypto: Any = None,
        signer: Any = None,
    ) -> None:
        self.db = str(db)
        if self.db != ":memory:":
            Path(self.db).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
        self.crypto = crypto
        self.signer = signer
        self.conn = sqlite3.connect(self.db, check_same_thread=False)
        self.conn.execute(
            """CREATE TABLE IF NOT EXISTS evidence_chain (
                id INTEGER PRIMARY KEY,
                timestamp_utc TEXT NOT NULL,
                evidence_hash TEXT NOT NULL,
                chained_hash TEXT NOT NULL,
                prev_hash TEXT NOT NULL,
                data_json TEXT NOT NULL,
                signature TEXT NOT NULL DEFAULT ''
            )"""
        )
        self.conn.commit()

    @staticmethod
    def _canonical_json(value: Any) -> str:
        return json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
        )

    def _sign(self, chained_hash: str) -> str:
        if self.signer is None:
            return ""
        signature = self.signer.sign(chained_hash)
        if isinstance(signature, bytes):
            return "b64:" + base64.b64encode(signature).decode("ascii")
        if isinstance(signature, str):
            if hasattr(self.signer, "get_public_pem"):
                return "ed25519-b64:" + signature
            return "text:" + signature
        raise TypeError("signer.sign() must return bytes or str")

    def add(
        self,
        ai_hash: str,
        pq_seal: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Append a record and return the stored block metadata."""
        if not _valid_hash(ai_hash):
            raise ValueError("ai_hash must be a 64- or 128-character hexadecimal hash")
        if not isinstance(pq_seal, str) or not pq_seal.strip():
            raise ValueError("pq_seal must be a non-empty string")
        if metadata is not None and not isinstance(metadata, dict):
            raise TypeError("metadata must be a dictionary when supplied")

        payload = {
            "ai_hash": ai_hash.lower(),
            "pq_seal": pq_seal,
            "metadata": metadata or {},
        }
        data_json = self._canonical_json(payload)
        evidence_hash = quantum_hash(data_json)
        timestamp = datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")

        # Serialize concurrent writers so prev_hash and the inserted link stay consistent.
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            last = self.conn.execute(
                "SELECT chained_hash FROM evidence_chain ORDER BY id DESC LIMIT 1"
            ).fetchone()
            prev_hash = last[0] if last else GENESIS_HASH
            chained_hash = quantum_hash(prev_hash + evidence_hash)
            signature = self._sign(chained_hash)
            cursor = self.conn.execute(
                """INSERT INTO evidence_chain
                   (timestamp_utc, evidence_hash, chained_hash, prev_hash, data_json, signature)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (timestamp, evidence_hash, chained_hash, prev_hash, data_json, signature),
            )
            record_id = int(cursor.lastrowid)
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

        return {
            "index": record_id - 1,
            "id": record_id,
            "timestamp_utc": timestamp,
            "ai_hash": payload["ai_hash"],
            "pq_seal": pq_seal,
            "metadata": payload["metadata"],
            "evidence_hash": evidence_hash,
            "prev_hash": prev_hash,
            "block_hash": chained_hash,
            "signature": signature,
        }

    def _verify_signature(self, chained_hash: str, signature: str) -> bool:
        if self.signer is None or not signature:
            return False
        try:
            if signature.startswith("ed25519-b64:") and hasattr(self.signer, "get_public_pem"):
                return bool(
                    self.signer.verify(
                        chained_hash,
                        signature.removeprefix("ed25519-b64:"),
                        self.signer.get_public_pem(),
                    )
                )
            if signature.startswith("b64:"):
                raw = base64.b64decode(signature.removeprefix("b64:"), validate=True)
                return bool(self.signer.verify(chained_hash, raw))
            return False
        except (ValueError, TypeError, UnicodeError, base64.binascii.Error):
            return False

    def verify_chain(self) -> dict[str, Any]:
        rows = self.conn.execute(
            """SELECT id, evidence_hash, chained_hash, prev_hash, data_json, signature
               FROM evidence_chain ORDER BY id"""
        ).fetchall()
        previous = GENESIS_HASH
        signature_checks = 0
        for record_id, evidence_hash, chained_hash, prev_hash, data_json, signature in rows:
            if prev_hash != previous:
                return {"valid": False, "records": len(rows), "break_at": record_id,
                        "reason": "previous-hash mismatch"}
            try:
                payload = json.loads(data_json)
            except (ValueError, TypeError):
                return {"valid": False, "records": len(rows), "break_at": record_id,
                        "reason": "invalid payload JSON"}
            if quantum_hash(data_json) != evidence_hash:
                return {"valid": False, "records": len(rows), "break_at": record_id,
                        "reason": "payload hash mismatch"}
            if quantum_hash(prev_hash + evidence_hash) != chained_hash:
                return {"valid": False, "records": len(rows), "break_at": record_id,
                        "reason": "chain hash mismatch"}

            if self.crypto is not None:
                verifier = getattr(self.crypto, "verify_seal", None)
                if callable(verifier):
                    try:
                        crypto_ok = bool(verifier(payload["ai_hash"], payload["pq_seal"]))
                    except Exception:
                        crypto_ok = False
                    if not crypto_ok:
                        return {"valid": False, "records": len(rows), "break_at": record_id,
                                "reason": "proof verification failed"}
            if self.signer is not None:
                signature_checks += 1
                if not self._verify_signature(chained_hash, signature):
                    return {"valid": False, "records": len(rows), "break_at": record_id,
                            "reason": "record signature verification failed"}
            previous = chained_hash

        return {
            "valid": True,
            "records": len(rows),
            "integrity": "VERIFIED",
            "signature_validation": (
                "VERIFIED" if self.signer is not None and signature_checks == len(rows)
                else "NOT_CONFIGURED"
            ),
            "pqc_proof_validation": (
                "VERIFIED" if self.crypto is not None and callable(getattr(self.crypto, "verify_seal", None))
                else "NOT_CONFIGURED"
            ),
        }

    def verify(self) -> bool:
        """Compatibility wrapper: true means chain integrity and configured checks passed."""
        return bool(self.verify_chain().get("valid", False))

    def export(self) -> str:
        rows = self.conn.execute(
            """SELECT id, timestamp_utc, evidence_hash, chained_hash, prev_hash, data_json, signature
               FROM evidence_chain ORDER BY id"""
        ).fetchall()
        records = []
        for record in rows:
            record_id, timestamp, ev_hash, chain_hash, prev_hash, data_json, signature = record
            records.append({
                "id": record_id,
                "timestamp_utc": timestamp,
                "evidence_hash": ev_hash,
                "block_hash": chain_hash,
                "prev_hash": prev_hash,
                "data": json.loads(data_json),
                "signature": signature,
            })
        return self._canonical_json({"records": records, "verification": self.verify_chain()})

    def close(self) -> None:
        self.conn.close()
