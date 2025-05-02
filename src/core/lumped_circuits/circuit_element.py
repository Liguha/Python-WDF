from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from sage.all import Rational
from typing import TYPE_CHECKING
if TYPE_CHECKING: from .netlist import LumpedElement

__all__ = ["CircuitElement", "ReplaceableElement", "MNAStampedElement"]

@dataclass(frozen=True)
class CircuitElement:
    pass

class ReplaceableElement(ABC):
    @abstractmethod
    def replacement(self, element: LumpedElement, free_node: int) -> list[LumpedElement]:
        '''Return list of new lumped elements, which should be used instead old one.'''
        pass

class MNAStampedElement(ABC):
    @abstractmethod
    def mna_stamp(self, nodes: tuple[int, ...], port: int, 
                  num_nodes: int, num_ports: int) -> dict[tuple[int, int], int | Rational]:
        '''Return element of MNA matrxi with corresponding position.'''
        pass