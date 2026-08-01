# apex44-zero - IRRE (Immutable Record for AI Evidence)

Quantum-resistant evidence ledger that proves what an AI model said and seals it for 50+ years.

## Why This Matters

RSA and ECDSA will be broken by Shor's algorithm. This uses Hash-Based Signatures (SHA256 + SHA3-256), same family as NIST PQC SPHINCS+.

## Architecture (9 Steps)

1. Project Structure
2. AI Evidence - ai_evidence.py
3. Post-Quantum Seal - post_quantum.py
4. Evidence Chain - evidence_chain.py
5. Main Orchestrator - main.py
6. Tests - test_evidence.py
7. API Layer - server.py
8. Documentation - this file
9. Final Proof - evidence_chain.json

## Usage

```bash
pip install -r requirements.txt
python main.py
python -m tests.test_evidence
