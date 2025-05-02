from uuid import uuid4
from dataclasses import dataclass
from sage.all import Rational, var
from typing import override
from ..core import CircuitElement, ReplaceableElement, MNAStampedElement, LumpedElement

__all__ = ["Resistor", "OpenCircuit", "Capacitor", "Inductor", 
           "IdealVoltageSource", "VoltageSource", "VCVS"]

@dataclass(frozen=True)
class Resistor(CircuitElement, MNAStampedElement):
    R: float | Rational

    @override
    def mna_stamp(self, nodes: tuple[int, ...], port: int, 
                  num_nodes: int, num_ports: int) -> dict[tuple[int, int], int | Rational]:
        r = self.R
        if isinstance(self.R, int | float):
            r = Rational(float(self.R))
        i, j = nodes
        res = {}
        res[(i, i)] = 1 / r
        res[(j, j)] = 1 / r
        res[(i, j)] = -1 / r
        res[(j, i)] = -1 / r
        return res


@dataclass(frozen=True)
class OpenCircuit(CircuitElement):
    pass


@dataclass(frozen=True)
class Capacitor(CircuitElement):
    C: float


@dataclass(frozen=True)
class Inductor(CircuitElement):
    L: float


@dataclass(frozen=True)
class IdealVoltageSource(CircuitElement, MNAStampedElement):
    Vs: float | None = None

    @override
    def mna_stamp(self, nodes: tuple[int, ...], port: int, 
                  num_nodes: int, num_ports: int) -> dict[tuple[int, int], int | Rational]:
        res: dict = {}
        i, j = nodes
        k = num_nodes + port
        res[(k, i)] = 1
        res[(k, j)] = -1
        res[(i, k)] = 1
        res[(j, k)] = -1
        return res


@dataclass(frozen=True)
class VoltageSource(CircuitElement):
    R: float
    Vs: float | None = None


@dataclass(frozen=True)
class VCVS(CircuitElement, MNAStampedElement):
    '''Voltage controlled voltage source. Nodes should be ordered as IN+, IN-, OUT+, OUT-.'''
    gain: float

    @override
    def mna_stamp(self, nodes: tuple[int, ...], port: int, 
                  num_nodes: int, num_ports: int) -> dict[tuple[int, int], int | Rational]:
        i, j, k, l = nodes
        n = num_nodes + num_ports + port
        res = {}
        res[(n, i)] = Rational(-self.gain)
        res[(n, j)] = Rational(self.gain)
        res[(n, k)] = 1
        res[(n, l)] = -1
        res[(k, n)] = 1
        res[(l, n)] = -1
        return res
