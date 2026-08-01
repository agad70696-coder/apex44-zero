from fastapi import FastAPI
from pydantic import BaseModel
from IRRE.ai.ai_evidence import AIModelEvidence
from IRRE.crypto.post_quantum import QuantumSafeEvidence
from IRRE.ledger.evidence_chain import EvidenceChain

app = FastAPI(title="apex44-zero IRRE API")
ledger = EvidenceChain()

class EvidenceRequest(BaseModel):
    model_id: str
    prompt: str
    output: str

@app.post("/create_evidence")
def create_evidence(req: EvidenceRequest):
    ai = AIModelEvidence(req.model_id, req.prompt, req.output)
    pq = QuantumSafeEvidence(req.model_id)
    proof = pq.export_proof(ai.hash)
    block = ledger.add(ai.hash, proof["quantum_seal"], {"model_id": req.model_id})
    return {
        "ai_hash": ai.hash,
        "quantum_seal": proof["quantum_seal"],
        "block_hash": block["block_hash"],
        "block_index": block["index"]
    }

@app.get("/verify")
def verify_chain():
    return {"valid": ledger.verify(), "length": len(ledger.chain)}

@app.get("/")
def root():
    return {"status": "IRRE API running - 50 year quantum proof"}
