from IRRE.neuro.neural_evidence import NeuralEvidence

def test_neural_evidence_creation():
    eeg = "alpha 10hz beta 20hz gamma 40hz"
    evidence = NeuralEvidence(eeg, "subject
