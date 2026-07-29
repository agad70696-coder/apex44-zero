class LegalEngine:
    def check(self, ctx):
        if ctx.get("private") and not ctx.get("warrant"):
            return False, "R1"
        return True, "OK"
