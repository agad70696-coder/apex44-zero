import hashlib
import time


def quantum_hash(d):
    return hashlib.sha256(d.encode()).hexdigest()


class AIModelEvidence:
    def __init__(self, model_id, prompt, output) -> None:
        self.model_id = model_id
        self.prompt = prompt
        self.output = output
        self.timestamp = str(time.time())
        self.hash = quantum_hash(f"{model_id}{prompt}{output}{self.timestamp}")

    def verify(self):
        e = quantum_hash(f"{self.model_id}{self.prompt}{self.output}{self.timestamp}")
        return self.hash == e
