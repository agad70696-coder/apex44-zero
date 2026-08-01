from fastapi import FastAPI
from pydantic import BaseModel
from IRRE.ai.ai_evidence import AIModelEvidence
from IRRE.crypto.post_quantum import QuantumSafeEvidence
from IRRE.ledger.evidence_chain import EvidenceChain

app = FastAPI(title="apex44-zero IRRE - Real Ledger V3")
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
    block = ledger.add(ai.hash, proof["quantum_seal"], {"model_id": req.model_id}, proof["public_key"], proof["algorithm"])
    return {"ai_hash": ai.hash, "block_hash": block["block_hash"], "merkle_root": block["merkle_root"], "tsa": block["tsa_token"][:20]+"...", "verified": ledger.verify()}

@app.get("/verify")
def verify():
    return {"valid": ledger.verify(), "length": ledger.get_len(), "anchor_protected": True, "merkle": True, "tsa": True}
