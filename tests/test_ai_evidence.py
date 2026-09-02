from IRRE.ai.ai_evidence import AIModelEvidence


def test_ai_evidence() -> None:
    ev = AIModelEvidence("gpt-4", "hello", "hi")
    assert ev.verify()


def test_ai_tamper() -> None:
    ev = AIModelEvidence("gpt-4", "hello", "hi")
    ev.output = "hacked"
    assert not ev.verify()
