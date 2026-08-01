from fastapi import FastAPI
from pydantic import BaseModel
from IRRE.ai.ai_evidence import AIModelEvidence
from IRRE.crypto.post_quantum import QuantumSafeEvidence
from IRRE.ledger.evidence_chain import EvidenceChain

app = FastAPI(title="apex44-zero IRRE API - PQC Real")
ledger = EvidenceChain()

class EvidenceRequest(BaseModel):
    model_id: str
    prompt: str
    output: str

@app.post("/create_evidence")
def create_evidence(req: EvidenceRequest):
    ai = AIModelEvidence(req.model_id, req.prompt, req.output)
    crypto = QuantumSafeEvidence(req.model_id)
    proof = crypto.export_proof(ai.hash)
    block = ledger.add(
        ai_hash=ai.hash,
        quantum_seal=proof["quantum_seal"],
        public_key=proof["public_key"],
        algorithm=proof["algorithm"],
        metadata={"model_id": req.model_id}
    )
    return {
        "ai_hash": ai.hash,
        "quantum_seal": proof["quantum_seal"],
        "public_key": proof["public_key"],
        "algorithm": proof["algorithm"],
        "block_hash": block["block_hash"],
        "verified": ledger.verify()
    }

@app.get("/verify")
def verify_chain():
    return {"valid": ledger.verify(), "length": len(ledger.chain), "pqc": True}

@app.get("/")
def root():
    return {"status": "IRRE API - Real PQC sign(sk, hash) - Ready for 2076"}
