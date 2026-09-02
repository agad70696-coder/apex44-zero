import os
import sqlite3
import threading
import time
from pathlib import Path

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field, validator

from IRRE.ai.ai_evidence import AIModelEvidence
from IRRE.crypto.post_quantum import QuantumSafeEvidence
from IRRE.ledger.blockchain_anchor import BlockchainAnchor
from IRRE.ledger.evidence_chain import EvidenceChain

API_KEY = os.getenv("IRRE_API_KEY")
if not API_KEY:
    raise RuntimeError("CRITICAL: IRRE_API_KEY env var not set")
if len(API_KEY) < 16:
    raise RuntimeError("CRITICAL: IRRE_API_KEY too weak")

DB_RATE = Path("rate_limit.db")

app = FastAPI(title="apex44-zero IRRE V7 - Fully Locked")
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)
ledger = EvidenceChain()
chain_anchor = BlockchainAnchor()
MODEL_ID_REGEX = r"^[a-zA-Z0-9_-]{1,100}$"

class PersistentRateLimiter:
    def __init__(self, max_requests=20, window=60):
        self.max_requests = max_requests
        self.window = window
        self.lock = threading.Lock()
        self.conn = sqlite3.connect(str(DB_RATE), check_same_thread=False)
        self.conn.execute("CREATE TABLE IF NOT EXISTS rates (ip TEXT, ts REAL)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_ip_ts ON rates(ip, ts)")
        self.conn.commit()
    def is_allowed(self, client_ip: str):
        with self.lock:
            now = time.time()
            cutoff = now - self.window
            self.conn.execute("DELETE FROM rates WHERE ts <?", (cutoff,))
            cur = self.conn.execute("SELECT COUNT(*) FROM rates WHERE ip=?", (client_ip,))
            count = cur.fetchone()[0]
            if count >= self.max_requests:
                self.conn.commit()
                return False
            self.conn.execute("INSERT INTO rates VALUES (?,?)", (client_ip, now))
            self.conn.commit()
            return True

limiter = PersistentRateLimiter(max_requests=20, window=60)

def verify_api_key(api_key: str = Depends(api_key_header)):
    if not api_key or api_key!= API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return api_key

def rate_limit_check(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    if not limiter.is_allowed(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit 20/min - persistent")
    return client_ip

class EvidenceRequest(BaseModel):
    model_id: str = Field(..., pattern=MODEL_ID_REGEX)
    prompt: str = Field(..., min_length=1, max_length=10000)
    output: str = Field(..., min_length=1, max_length=10000)
    @validator('model_id')
    def validate_model_id(cls, v):
        if not __import__('re').fullmatch(MODEL_ID_REGEX, v):
            raise ValueError('Invalid model_id')
        return v

def do_blockchain_anchor(merkle_root: str):
    try:
        chain_anchor.anchor(merkle_root)
    except:
        pass

@app.post("/create_evidence")
def create_evidence(req: EvidenceRequest, background_tasks: BackgroundTasks, api_key: str = Depends(verify_api_key), client_ip: str = Depends(rate_limit_check)):
    if len(req.prompt.encode('utf-8')) > 10240 or len(req.output.encode('utf-8')) > 10240:
        raise HTTPException(status_code=413, detail="Payload too large max 10KB")
    ai = AIModelEvidence(req.model_id, req.prompt, req.output)
    crypto = QuantumSafeEvidence(req.model_id)
    proof = crypto.export_proof(ai.hash)
    block = ledger.add(ai.hash, proof["quantum_seal"], {"model_id": req.model_id}, proof["public_key"], proof["algorithm"])
    background_tasks.add_task(do_blockchain_anchor, block["merkle_root"])
    return {"ai_hash": ai.hash, "block_hash": block["block_hash"], "merkle_root": block["merkle_root"], "verified": ledger.verify(), "status": "fully-locked-v7"}

@app.get("/verify")
def verify(api_key: str = Depends(verify_api_key), client_ip: str = Depends(rate_limit_check)):
    return {"valid": ledger.verify(), "length": ledger.get_len(), "protection": ["Persistent-RateLimit", "NoDefaultKey", "PQC-Enforced", "Encrypted-At-Rest", "Thread-Lock", "DiskLimit"]}

@app.get("/")
def root():
    return {"status": "apex44-zero V7 Fully Locked"}
