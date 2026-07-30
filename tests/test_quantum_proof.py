from IRRE.quantum.quantum_proof import QuantumProof

def test_quantum_proof_creation():
    proof = QuantumProof("secret data")
    assert proof.verify("secret data") == True
    assert proof.is_quantum_safe() == True

def test_quantum_tamper():
    proof = QuantumProof("secret")
    assert proof.verify("hacked") == False
