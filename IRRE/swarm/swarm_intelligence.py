from .colony import AntColony

class SwarmIntelligence:
    def **init**(self, n=100):
        self.colony = AntColony(n//4)
    def verify(self):
        r = self.colony.run(20)
        return r
