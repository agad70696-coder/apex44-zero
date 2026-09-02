import hashlib
import time


def quantum_hash(data: str) -> str:
    return hashlib.shake_256(data.encode()).hexdigest(64)

class AIModelEvidence:
    """
    دليل قرار ذكاء اصطناعي - بيوثق أن الـ AI قال ايه وامتى
    """
    def __init__(self, model_id: str, prompt: str, output: str):
        self.model_id = model_id
        self.prompt = prompt
        self.output = output
        self.timestamp = str(time.time())
        self.hash = quantum_hash(f"{model_id}{prompt}{output}{self.timestamp}")

    def verify(self) -> bool:
        expected = quantum_hash(f"{self.model_id}{self.prompt}{self.output}{self.timestamp}")
        return self.hash == expected

    def detect_prompt_injection(self) -> bool:
        # كشف لو حد حاول يلعب في البرومبت بحقن أوامر خبيثة
        suspicious = ["ignore previous", "system:", "DAN", "jailbreak"]
        prompt_lower = self.prompt.lower()
        for word in suspicious:
            if word.lower() in prompt_lower:
                return True
        return False
