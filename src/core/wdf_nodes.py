import numpy as np
from abc import ABC, abstractmethod
from typing import Any

__all__ = ["WDFElement", "WDFLinearElement", "WDFnonlinearElement", "WDFAdaptor"]

class WDFElement(ABC):
    def __init__(self, samplerate: int) -> None:
        self._samplerate: int  = samplerate
        self._a: np.ndarray | None = None           # shortcur for incident waves
        self._b: np.ndarray | None = None           # shortcut for reflected waves

    @property
    def reflected_wave(self) -> np.ndarray:
        return self._b

    @property
    def incident_wave(self) -> np.ndarray:
        return self._a
    
    @abstractmethod
    @incident_wave.setter
    def incident_wave(self, value: Any) -> None:
        pass

    @abstractmethod
    @property
    def port_resistance(self) -> float:
        pass

    @abstractmethod
    def reset(self) -> None:
        pass


class WDFLinearElement(WDFElement):
    def __init__(self, samplerate: int) -> None:
        super().__init__(samplerate)
        self._Rp: float | None = None               # shortcut for port resistance

    @property
    def port_resistance(self) -> float:
        return self._Rp
    

class WDFNonlinearElement(WDFElement):
    pass


class WDFAdaptor(WDFLinearElement):
    def __init__(self, samplerate: int) -> None:
        super().__init__(samplerate)
        self._S_matrix: np.ndarray | None = None    # shortcut for scattering matrix
        self.update_scaterring_matrix()

    @abstractmethod
    def update_scaterring_matrix(self, *args, **kwds) -> None:
        pass