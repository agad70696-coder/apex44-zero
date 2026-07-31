class Reasoner:
    """
    Simple reasoning engine.
    """

    def infer(self, facts: list[str]) -> dict:
        if not facts:
            return {
                "status": "empty",
                "conclusion": None,
            }

        return {
            "status": "ok",
            "conclusion": facts[-1],
            "facts_count": len(facts),
        }
