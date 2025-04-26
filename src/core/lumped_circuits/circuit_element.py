from abc import ABC, abstractmethod
from dataclasses import dataclass

__all__ = ["CircuitElement"]

@dataclass(frozen=True)
class CircuitElement:
    pass

class ReplaceableElement(ABC):
    @staticmethod
    @abstractmethod
    def replacement(element: 'LumpedElement', free_node: int) -> list['LumpedElement']: # type: ignore
        pass

class MNAStampedElement(ABC):
    pass