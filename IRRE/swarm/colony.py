from .agent import BaseAnt, Pheromone
import random

class AntColony:
    def __init__(self, n=25):
        self.ants=[]
        self.pheromones=[]
        self.locs=["ROOT","IRRE/","evidence/","behavioral/"]
        for i in range(n*4):
            self.ants.append(BaseAnt(f"Ant-{i}", "evidence", random.choice(self.locs)))
    def run(self, steps=20):
        for _ in range(steps):
            for ant in self.ants:
                r=ant.act(self.pheromones, self.locs)
                if r: self.pheromones.append(r)
            self.pheromones=[p for p in self.pheromones if p.strength>0.05]
        return {"found": len(self.pheromones)}
