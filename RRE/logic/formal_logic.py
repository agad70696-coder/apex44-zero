from dataclasses import dataclass


@dataclass
class Fact:
    predicate: str
    subject: str
    value: bool = True
    confidence: float = 1.0

    def __str__(self) -> str:
        neg = "" if self.value else "¬"
        return f"{neg}{self.predicate}({self.subject})"

    def key(self) -> str:
        return f"{self.predicate}:{self.subject}"


@dataclass
class Rule:
    name: str
    premises: list[str]
    conclusion: str
    description: str = ""
    formula: str = ""

    def __str__(self) -> str:
        pre = " ∧ ".join(self.premises)
        return f"{self.name}: {pre} → {self.conclusion}"


class KnowledgeBase:
    def __init__(self) -> None:
        self.facts: dict[str, Fact] = {}
        self.rules: list[Rule] = []

    def add_fact(self, predicate: str, subject: str, value: bool = True, confidence: float = 1.0):
        fact = Fact(predicate, subject, value, confidence)
        self.facts[fact.key()] = fact
        return fact

    def add_rule(self, rule: Rule) -> None:
        self.rules.append(rule)

    def has_fact(self, predicate: str, subject: str, value: bool = True) -> bool:
        key = f"{predicate}:{subject}"
        if key in self.facts:
            return self.facts[key].value == value
        return False
