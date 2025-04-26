from dataclasses import dataclass
from ..core import CircuitElement

__all__ = ["Resistor", "Capacitor", "Inductor"]

@dataclass(frozen=True)
class Resistor(CircuitElement):
    R: float

@dataclass(frozen=True)
class Capacitor(CircuitElement):
    C: float

@dataclass(frozen=True)
class Inductor(CircuitElement):
    L: float