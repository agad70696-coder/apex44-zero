import hashlib
import time

def predict_hash(data: str) -> str:
    return hashlib.sha3_256(data.encode()).hexdigest()

class PredictiveEvidence:
    """
    توثيق تنبؤات الذكاء الاصطناعي - يمنع تزوير توقعات البورصة أو الأوبئة
    """
    def __init__(self, model_id: str, dataset_hash: str, phenomenon: str):
        self.model_id = model_id
        self.dataset_hash = dataset_hash
        self.phenomenon = phenomenon  # stock_crash, pandemic, earthquake
        self.base_hash = predict_hash(f"{model_id}{dataset_hash}{time.time()}")
        self.predictions = []

    def add_prediction(self, prediction: str, probability: float, impact: str):
        # كشف التلاعب: احتمالية 100% في الاقتصاد/الأوبئة = كذب
        # مفيش حاجة مؤكدة 100% في الأنظمة المعقدة
        is_fake = probability == 1.0 or probability > 0.99 and
