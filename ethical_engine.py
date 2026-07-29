class EthicalEngine:
    def evaluate(self, ctx):
        score = 1.0 - ctx.get("harm_risk",0)*0.5
        return max(0,score)
