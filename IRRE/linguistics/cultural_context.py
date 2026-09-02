from dataclasses import dataclass
from enum import Enum


class SocialIntent(Enum):
    BUILD_REQUEST = "build_request"
    LOCATION_QUERY = "location_query"
    PHILOSOPHICAL_EXAMPLE = "philosophical_example"
    TRUTH_SEEKING = "truth_seeking"
    STATUS_CLAIM = "status_claim"


@dataclass
class CulturalExpression:
    phrase: str
    literal_en: str
    social_meaning: str
    intent: SocialIntent
    formal_logic: str = ""


class EgyptianCulturalContext:
    def __init__(self) -> None:
        self.expressions: dict[str, CulturalExpression] = {}
        self._build()

    def _build(self) -> None:
        self.expressions["ابنى"] = CulturalExpression(
            "ابنى",
            "my son",
            "أمر تنفيذي سريع بثقة - ابن الطبقة كاملة حالاً",
            SocialIntent.BUILD_REQUEST,
            "BuildAction(layers=ALL, urgency=HIGH, lang=EG)",
        )
        self.expressions["فين 3"] = CulturalExpression(
            "فين 3",
            "where is 3",
            "فين الملف التالت؟ بنينا 2 وناقص التالت",
            SocialIntent.LOCATION_QUERY,
            "Query(file=3, context=prev2)",
        )
        self.expressions["القاهرة مش كلمة"] = CulturalExpression(
            "القاهرة مش كلمة",
            "Cairo not word",
            "القاهرة كيان جغرافي له علاقات داخل مصر، ليست String",
            SocialIntent.PHILOSOPHICAL_EXAMPLE,
            "Entity(Cairo,City)!= String('القاهرة')",
        )
        self.expressions["مشروعي 6.0 ثوري"] = CulturalExpression(
            "مشروعي 6.0 ثوري",
            "my project 6.0",
            "ادعاء مكانة بدون دليل - ثقة مفرطة",
            SocialIntent.STATUS_CLAIM,
            "Claim(6.0, ev=0, bias=overconfidence)",
        )
        self.expressions["فين الدليل"] = CulturalExpression(
            "فين الدليل",
            "where evidence",
            "طلب تحقق - دافع حقيقة",
            SocialIntent.TRUTH_SEEKING,
            "Request(Evidence, motive=truth)",
        )

    def interpret(self, phrase: str) -> CulturalExpression | None:
        phrase = phrase.strip()
        if phrase in self.expressions:
            return self.expressions[phrase]
        for k, v in self.expressions.items():
            if k in phrase or phrase in k:
                return v
        return None
