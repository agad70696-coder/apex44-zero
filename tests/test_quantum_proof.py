from IRRE.quantum.quantum_proof import QuantumProof


def test_quantum_proof_creation() -> None:
    proof = QuantumProof("secret data")
    assert proof.verify("secret data")
    assert proof.is_quantum_safe()


def test_quantum_tamper() -> None:
    proof = QuantumProof("secret")
    assert not proof.verify("hacked")
