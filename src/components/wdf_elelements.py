import numpy as np
from typing import override
from ..core import WDFLinearElement, WDFDynamicElement
from .circuit_elements import (Resistor, Inductor, 
                               Capacitor, VoltageSource)

__all__ = ["WDFResistor", "WDFOpenCircuit", "WDFInductor", "WDFCapacitor", "WDFVoltageSource"]

class WDFResistor(WDFLinearElement):
    def __init__(self, samplerate: int, resistor: Resistor):
        super().__init__(samplerate)
        self._a: np.ndarray = np.zeros(1, dtype=float)
        self._b: np.ndarray = np.zeros(1, dtype=float)
        self._Rp: float = resistor.R
    
    @WDFLinearElement.incident_wave.setter
    def incident_wave(self, value: float | np.ndarray) -> None:
        if not isinstance(value, float):
            value = value[0]
        self._a[0] = value


class WDFOpenCircuit(WDFLinearElement):
    def __init__(self, samplerate: int, open_circuit: Resistor):
        super().__init__(samplerate)
        self._a: np.ndarray = np.zeros(1, dtype=float)
        self._b: np.ndarray = np.zeros(1, dtype=float)
        self._Rp: float = 1e20

    @WDFLinearElement.incident_wave.setter
    def incident_wave(self, value: float | np.ndarray) -> None:
        if not isinstance(value, float):
            value = value[0]
        # add delay to ensure computability
        self._a[0] = self._b[0]
        self._b[0] = value


class WDFInductor(WDFLinearElement):
    def __init__(self, samplerate: int, inductor: Inductor):
        super().__init__(samplerate)
        self._a: np.ndarray = np.zeros(1, dtype=float)
        self._b: np.ndarray = np.zeros(1, dtype=float)
        self._Rp: float = 2 * inductor.L * samplerate

    @WDFLinearElement.incident_wave.setter
    def incident_wave(self, value: float | np.ndarray) -> None:
        if not isinstance(value, float):
            value = value[0]
        self._b[0] = -value
        self._a[0] = value


class WDFCapacitor(WDFLinearElement):
    def __init__(self, samplerate: int, capacitor: Capacitor):
        super().__init__(samplerate)
        self._a: np.ndarray = np.zeros(1, dtype=float)
        self._b: np.ndarray = np.zeros(1, dtype=float)
        self._Rp: float = 1 / (2 * samplerate * capacitor.C)

    @WDFLinearElement.incident_wave.setter
    def incident_wave(self, value: float | np.ndarray) -> None:
        if not isinstance(value, float):
            value = value[0]
        self._b[0] = value
        self._a[0] = value


class WDFVoltageSource(WDFLinearElement, WDFDynamicElement):
    def __init__(self, samplerate: int, voltage_source: VoltageSource):
        super().__init__(samplerate)
        self._a: np.ndarray = np.zeros(1, dtype=float)
        self._b: np.ndarray = np.zeros(1, dtype=float)
        self._Rp: float = voltage_source.R
        self._vs: float = voltage_source.Vs

    @WDFLinearElement.incident_wave.setter
    def incident_wave(self, value: float | np.ndarray) -> None:
        if not isinstance(value, float):
            value = value[0]
        if self._vs is None:
            raise ValueError("Voltage of source is not defined")
        self._a[0] = value
        self._b[0] = self._vs

    @override
    def set_sample_data(self, data: float) -> None:
        self._vs = data
        self._b[0] = self._vs