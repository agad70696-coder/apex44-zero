from fastapi import FastAPI
from pydantic import BaseModel
from IRRE.ai.ai_evidence import AIModelEvidence
from IRRE.crypto.post_quantum import QuantumSafeEvidence
from IRRE.ledger.evidence_chain import EvidenceChain
from IRRE.ledger.blockchain_anchor import BlockchainAnchor

app = FastAPI(title="apex44-zero IRRE V4 - PQC + Merkle + Anchor + Blockchain")
ledger = EvidenceChain()
chain_anchor = BlockchainAnchor()

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
        ai.hash,
        proof["quantum_seal"],
        {"model_id": req.model_id},
        proof["public_key"],
        proof["algorithm"]
    )
    bc = chain_anchor.anchor(block["merkle_root"])
    return {
        "ai_hash": ai.hash,
        "block_hash": block["block_hash"],
        "merkle_root": block["merkle_root"],
        "tsa": block["tsa_token"][:20] if block["tsa_token"] else "LOCAL",
        "blockchain": bc,
        "verified": ledger.verify(),
        "status": "Evidence anchored for 2076"
    }

@app.get("/verify")
def verify():
    return {
        "valid": ledger.verify(),
        "length": ledger.get_len(),
        "protection": ["SQLite-WAL", "Merkle-Tree", "Anchor-Log", "TSA-rfc3161", "Blockchain-Polygon"]
    }

@app.get("/")
def root():
    return {"status": "apex44-zero - Real IRRE - Ready for Court"}
