from IRRE.ai.ai_evidence import AIModelEvidence

def test_ai_evidence():
    ev = AIModelEvidence("gpt-4", "hello", "hi")
    assert ev.verify() == True

def test_ai_tamper():
    ev = AIModelEvidence("gpt-4", "hello", "hi")
    ev.output = "hacked"
    assert ev.verify() == False
