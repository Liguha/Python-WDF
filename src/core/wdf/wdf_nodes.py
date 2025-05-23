from __future__ import annotations
import numpy as np
from abc import ABC, abstractmethod
from typing import Any, override, TYPE_CHECKING
if TYPE_CHECKING: from .wdf_tree import WDFTreeNode

__all__ = ["WDFElement", "WDFLinearElement", "WDFNonlinearElement", "WDFAdaptor", "WDFDynamicElement"]

class WDFElement(ABC):
    def __init__(self, samplerate: int) -> None:
        self._samplerate: int  = samplerate
        self._a: np.ndarray | None = None           # shortcur for incident waves
        self._b: np.ndarray | None = None           # shortcut for reflected waves
        self._tree_node: WDFTreeNode | None = None  # wrapped at property to ensure overriding

    @property
    def tree_node(self) -> WDFTreeNode:
        return self._tree_node
    
    @tree_node.setter
    def tree_node(self, node: WDFTreeNode) -> None:
        self._tree_node = node

    @property
    def reflected_wave(self) -> np.ndarray:
        return self._b

    @property
    def incident_wave(self) -> np.ndarray:
        return self._a
    
    @incident_wave.setter
    @abstractmethod
    def incident_wave(self, value: Any) -> None:
        pass

    @property
    @abstractmethod
    def port_resistance(self) -> float:
        pass

    def reset(self) -> None:
        self._a = np.zeros(self._a.shape, dtype=float)
        self._b = np.zeros(self._b.shape, dtype=float)


class WDFLinearElement(WDFElement):
    def __init__(self, samplerate: int) -> None:
        super().__init__(samplerate)
        self._Rp: float | None = None               # shortcut for port resistance

    @property
    @override
    def port_resistance(self) -> float:
        return self._Rp
    

class WDFNonlinearElement(WDFElement):
    pass


class WDFAdaptor(WDFLinearElement):
    def __init__(self, samplerate: int) -> None:
        super().__init__(samplerate)
        self._S_matrix: np.ndarray | None = None    # shortcut for scattering matrix

    @WDFLinearElement.incident_wave.setter
    def incident_wave(self, value: np.ndarray | float) -> None:
        if isinstance(value, np.ndarray):
            shift: int = len(self._a) - len(value)
            self._a[shift:] = value
        else:
            self._a[0] = value
        self._b = np.dot(self._S_matrix, self._a)

    @abstractmethod
    def update_scaterring_matrix(self, *args, **kwds) -> None:
        pass


class WDFDynamicElement(WDFElement):
    @abstractmethod
    def set_sample_data(self, data: Any) -> None:
        pass

    def store_defaults(self, dynamics: list[str]) ->  None:
        self._defaults: dict[str] = {}
        for param in dynamics:
            self._defaults[param] = getattr(self, param)
    
    @override
    def reset(self) -> None:
        super().reset()
        if not hasattr(self, "_defaults"):
            return
        for name, value in self._defaults.items():
            setattr(self, name, value)