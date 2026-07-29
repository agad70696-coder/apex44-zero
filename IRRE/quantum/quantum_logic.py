import math, random
from dataclasses import dataclass

@dataclass
class Qubit:
    alpha: complex = 1+0j
    beta: complex = 0+0j
    def __post_init__(self):
        norm = math.sqrt(abs(self.alpha)**2 + abs(self.beta)**2)
        if norm>0:
            self.alpha/=norm; self.beta/=norm
    def is_zero(self): return abs(self.beta)<0.01
    def is_one(self): return abs(self.alpha)<0.01
    def is_superposition(self): return not self.is_zero() and not self.is_one()
    def measure(self) -> int:
        prob_zero = abs(self.alpha)**2
        result = 0 if random.random()<prob_zero else 1
        self.alpha=1+0j if result==0 else 0+0j
        self.beta=0+0j if result==0 else 1+0j
        return result
    def __str__(self):
        if self.is_zero(): return "|0⟩-No Evidence"
        if self.is_one(): return "|1⟩-Has Evidence"
        return f"{self.alpha:.2f}|0⟩+{self.beta:.2f}|1⟩-Schrödinger"

class QuantumState:
    def __init__(self, num_qubits: int):
        self.num_qubits=num_qubits
        self.qubits=[Qubit(1+0j,0+0j) for _ in range(num_qubits)]
    def put_superposition(self):
        for q in self.qubits:
            q.alpha=complex(1/math.sqrt(2),0); q.beta=complex(1/math.sqrt(2),0)
    def measure_all(self): return [q.measure() for q in self.qubits]

class Hadamard:
    @staticmethod
    def apply(qubit: Qubit) -> Qubit:
        na=(qubit.alpha+qubit.beta)/math.sqrt(2)
        nb=(qubit.alpha-qubit.beta)/math.sqrt(2)
        return Qubit(na,nb)

class CNOT:
    @staticmethod
    def apply(control: Qubit, target: Qubit):
        if control.is_one() or (control.is_superposition() and random.random()<abs(control.beta)**2):
            return control, Qubit(target.beta, target.alpha)
        return control, target
