from IRRE.neuro.neural_evidence import NeuralEvidence


def test_neural_evidence_creation() -> None:
    eeg = "alpha 10hz beta 20hz gamma 40hz"

    evidence = NeuralEvidence(
        eeg,
        "subject-1",
        "session-1",
    )

    assert evidence.eeg_data == eeg
    assert evidence.subject_id == "subject-1"
    assert evidence.session_id == "session-1"
    assert evidence.verify()
