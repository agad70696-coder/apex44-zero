from dataclasses import dataclass
from typing import List, Dict
from enum import Enum

@dataclass
class Fact:
    predicate: str
    subject: str
    value: bool = True
    confidence: float = 1.0
    def __str__(self):
        neg = "" if self.value else "¬"
        return f"{neg}{self.predicate}({self.subject})"
    def key(self):
        return f"{self.predicate}:{self.subject}"

@dataclass
class Rule:
    name: str
    premises: List[str]
    conclusion: str
    description: str = ""
    formula: str = ""
    def __str__(self):
        pre = " ∧ ".join(self.premises)
        return f"{self.name}: {pre} → {self.conclusion}"

class KnowledgeBase:
    def __init__(self):
        self.facts: Dict[str, Fact] = {}
        self.rules: List[Rule] = []
    def add_fact(self, predicate: str, subject: str, value: bool = True, confidence: float = 1.0):
        fact = Fact(predicate, subject, value, confidence)
        self.facts[fact.key()] = fact
        return fact
    def add_rule(self, rule: Rule):
        self.rules.append(rule)
    def has_fact(self, predicate: str, subject: str, value: bool = True) -> bool:
        key = f"{predicate}:{subject}"
        if key in self.facts:
            return self.facts[key].value == value
        return False
