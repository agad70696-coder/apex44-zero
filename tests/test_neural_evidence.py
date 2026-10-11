"""Tests for the synthetic neural evidence record."""
from IRRE.neuro.neural_evidence import NeuralEvidence

EXPECTED_HASH_HEX_LENGTH = 128


def test_neural_evidence_creation_and_verification() -> None:
    evidence = NeuralEvidence("alpha 10hz beta 20hz gamma 40hz", "subject-01", "session-01")
    assert evidence.verify()
    assert len(evidence.hash) == EXPECTED_HASH_HEX_LENGTH


def test_neural_evidence_detects_mutated_record() -> None:
    evidence = NeuralEvidence("alpha 10hz beta 20hz gamma 40hz", "subject-01", "session-01")
    evidence.eeg_data = "tampered eeg signal"
    assert not evidence.verify()


def test_flat_signal_is_flagged_by_demo_heuristic() -> None:
    evidence = NeuralEvidence("aaaaaaaaaaaaaaaa", "subject-01", "session-01")
    assert evidence.detect_fake_consciousness()


def test_varied_signal_is_not_flagged_by_demo_heuristic() -> None:
    evidence = NeuralEvidence("alpha beta gamma 10hz 20hz", "subject-01", "session-01")
    assert not evidence.detect_fake_consciousness()
