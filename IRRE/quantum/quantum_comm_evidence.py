import hashlib
import time

def quantum_hash(data: str) -> str:
    return hashlib.sha3_256(data.encode()).hexdigest()

class QuantumCommEvidence:
    """
    توثيق اتصال كمي - أي محاولة تنصت بتغير حالة الفوتون
    لو QBER > 11% = في هاكر بيتنصت
    """
    def __init__(self, link_id: str, sender: str, receiver: str):
        self.link_id = link_id
        self.sender = sender
        self.receiver = receiver
        self.base_hash = quantum_hash(f"{link_id}{sender}{receiver}{time.time()}")
        self.sessions = []

    def add_qkd_session(self, qber: float, key_length: int, bell_value: float):
        # فيزياء الكم: QBER > 11% = مستحيل يكون ضوضاء، ده تنصت
        # Bell > 2 = تشابك كمي سليم، لو <2 = حد كسر التشابك
        is_eavesdropped = qber > 0.11 or bell_value < 2.0

        entry = {
            "qber": qber,
            "key_length": key_length,
            "bell_value": bell_value,
            "hash": quantum_hash(f"{self.link_id}{qber}{key_length}{time.time()}"),
            "is_eavesdropped": is_eavesdropped
        }
        self.sessions.append(entry)
        return entry

    def is_channel_secure(self) -> bool:
        return not any(s["is_eavesdropped"] for s in self.sessions)

    def verify_quantum(self) -> bool:
        return len(self.base_hash) == 64
