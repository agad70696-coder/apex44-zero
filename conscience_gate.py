from .legal_rules import LegalEngine
from .ethical_engine import EthicalEngine

class ConscienceGate:
    def judge(self, ctx):
        ok_law, rule = self.legal.check(ctx)
        if not ok_law: return {"allow":False}
        ok_eth, score = self.ethical.decide(ctx)
        if not ok_eth: return {"allow":False}
        return {"allow":True}
