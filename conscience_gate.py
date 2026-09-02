

class ConscienceGate:
    def judge(self, ctx):
        ok_law, _rule = self.legal.check(ctx)
        if not ok_law:
            return {"allow": False}
        ok_eth, _score = self.ethical.decide(ctx)
        if not ok_eth:
            return {"allow": False}
        return {"allow": True}
