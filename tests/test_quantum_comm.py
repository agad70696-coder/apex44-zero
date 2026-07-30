from IRRE.quantum.quantum_comm_evidence import QuantumCommEvidence

def test_secure_channel():
    link = QuantumCommEvidence("Q-LINK-CAIRO-DC", "Cairo", "Washington")
    link.add_qkd_session(0.02, 256, 2.7)  # QBER 2% آمن
    assert link.is_channel_secure() == True

def test_eavesdropper():
    link = QuantumCommEvidence("Q-LINK-02", "A", "B")
    link.add_qkd_session(0.15, 256, 2.7)  # QBER 15% = في حد بيتنصت
    assert link.is_channel_secure() == False
