import os, time, threading, re
from collections import defaultdict
from fastapi import FastAPI, Depends, HTTPException, Request, BackgroundTasks
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field, validator
from IRRE.ai.ai_evidence import AIModelEvidence
from IRRE.crypto.post_quantum import QuantumSafeEvidence
from IRRE.ledger.evidence_chain import EvidenceChain
from IRRE.ledger.blockchain_anchor import BlockchainAnchor

API_KEY = os.getenv("IRRE_API_KEY")
if not API_KEY:
    raise RuntimeError("CRITICAL: IRRE_API_KEY env var not set. Example: export IRRE_API_KEY='your-strong-key'")

if len(API_KEY) < 16:
    raise RuntimeError("CRITICAL: IRRE_API_KEY too weak, min 16 chars")

app = FastAPI(title="apex44-zero IRRE V6 - Critical Fixed")

api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)
ledger = EvidenceChain()
chain_anchor = BlockchainAnchor()

MODEL_ID_REGEX = r"^[a-zA-Z0-9_-]{1,100}$"

class RateLimiter:
    def __init__(self, max_requests=20, window=60):
        self.max_requests = max_requests
        self.window = window
        self.requests = defaultdict(list)
        self.lock = threading.Lock()
    def is_allowed(self, client_ip: str):
        with self.lock:
            now = time.time()
            reqs = [t for t in self.requests[client_ip] if now - t < self.window]
            self.requests[client_ip] = reqs
            if len(reqs) >= self.max_requests:
                return False
            reqs.append(now)
            self.requests[client_ip] = reqs
            return True

limiter = RateLimiter(max_requests=20, window=60)

def verify_api_key(api_key: str = Depends(api_key_header)):
    if not api_key or api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key. Use X-API-KEY header")
    return api_key

def rate_limit_check(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    if not limiter.is_allowed(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded: 20 req/min")
    return client_ip

class EvidenceRequest(BaseModel):
    model_id: str = Field(..., pattern=MODEL_ID_REGEX)
    prompt: str = Field(..., min_length=1, max_length=10000)
    output: str = Field(..., min_length=1, max_length=10000)

    @validator('model_id')
    def validate_model_id(cls, v):
        if not re.fullmatch(MODEL_ID_REGEX, v):
            raise ValueError('Invalid model_id')
        return v

def do_blockchain_anchor(merkle_root: str):
    try:
        chain_anchor.anchor(merkle_root)
    except:
        pass

@app.post("/create_evidence")
def create_evidence(
    req: EvidenceRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key),
    client_ip: str = Depends(rate_limit_check)
):
    if len(req.prompt.encode('utf-8')) > 10240 or len(req.output.encode('utf-8')) > 10240:
        raise HTTPException(status_code=413, detail="Payload too large: max 10KB per field")
    ai = AIModelEvidence(req.model_id, req.prompt, req.output)
    crypto = QuantumSafeEvidence(req.model_id)
    proof = crypto.export_proof(ai.hash)
    block = ledger.add(ai.hash, proof["quantum_seal"], {"model_id": req.model_id}, proof["public_key"], proof["algorithm"])
    background_tasks.add_task(do_blockchain_anchor, block["merkle_root"])
    return {
        "ai_hash": ai.hash,
        "block_hash": block["block_hash"],
        "merkle_root": block["merkle_root"],
        "verified": ledger.verify(),
        "status": "secured-critical-fixed"
    }

@app.get("/verify")
def verify(api_key: str = Depends(verify_api_key), client_ip: str = Depends(rate_limit_check)):
    return {
        "valid": ledger.verify(),
        "length": ledger.get_len(),
        "protection": ["PathTraversal-Fixed", "NoDefaultKey", "PQC-Enforced", "Thread-Lock", "API-Key", "RateLimit", "Validation"]
    }

@app.get("/")
def root():
    return {"status": "apex44-zero V6 - Critical Fixed"}
