# IRRE - Evidence Law
# القانون: مفيش دليل = مفيش ادعاء


class Evidence:
    def __init__(self, source_url, quote, confidence=0.9) -> None:
        self.source_url = source_url
        self.quote = quote
        self.confidence = confidence

    def is_valid(self):
        return self.source_url.startswith("http") and len(self.quote) > 10


class Claim:
    def __init__(self, text, evidences) -> None:
        self.text = text
        self.evidences = evidences
        self.status = "pending"

    def verify(self) -> bool:
        if not self.evidences:
            self.status = "rejected"
            return False
        for ev in self.evidences:
            if not ev.is_valid():
                self.status = "rejected"
                return False
        self.status = "verified"
        return True


# اختبار سريع
if __name__ == "__main__":
    ev = Evidence("https://example.com", "دليل حقيقي للبحث", 0.9)
    claim = Claim("الروبوتات مفيدة", [ev])
    print("✅ VERIFIED" if claim.verify() else "❌ REJECTED")
