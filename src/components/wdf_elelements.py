from __future__ import annotations
import numpy as np
from typing import override, TYPE_CHECKING
from ..core import WDFLinearElement, WDFNonlinearElement, WDFDynamicElement
if TYPE_CHECKING: from ..core.wdf.wdf_tree import WDFTreeNode
from .circuit_elements import (Resistor, Inductor, 
                               Capacitor, VoltageSource,
                               Trimmer, Diode)

__all__ = ["WDFResistor", "WDFOpenCircuit", "WDFInductor", "WDFCapacitor", 
           "WDFVoltageSource", "WDFTrimmer", "WDFDiode"]

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
        self.store_defaults(["_vs"])

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


class WDFTrimmer(WDFNonlinearElement, WDFDynamicElement):
    def __init__(self, samplerate: int, trimmer: Trimmer):
        super().__init__(samplerate)
        self._a: np.ndarray = np.zeros(1, dtype=float)
        self._b: np.ndarray = np.zeros(1, dtype=float)
        self._Rp: float = trimmer.R
        self._R: float = trimmer.R
        self.store_defaults(["_R"])

    @WDFNonlinearElement.incident_wave.setter
    def incident_wave(self, value: float | np.ndarray) -> None:
        if not isinstance(value, float):
            value = value[0]
        if self._R is None:
            raise ValueError("Trimmer resistance is not defined")
        self._a[0] = value

    @override
    @property
    def port_resistance(self) -> float:
        return self._Rp

    @override
    def set_sample_data(self, data: float) -> None:
        self._R = data
        self._Rp = data


class WDFDiode(WDFNonlinearElement):
    '''WDF diode implemented with formulas from 
    [pywdf GitHub](https://github.com/gusanthon/pywdf/blob/main/pywdf/core/wdf.py)'''
    def __init__(self, samplerate: int, diode: Diode):
        super().__init__(samplerate)
        self._a: np.ndarray = np.zeros(1, dtype=float)
        self._b: np.ndarray = np.zeros(1, dtype=float)
        self._Is: float = diode.Is
        self._Vt: float = diode.Vt
        self._one_over_Vt: float = 1.0 / self._Vt

    @WDFNonlinearElement.incident_wave.setter
    def incident_wave(self, value: float | np.ndarray) -> None:
        if not isinstance(value, float):
            value = value[0]
        self._a[0] = value
        self._b[0] = value + self._two_R_Is - (2.0 * self._Vt) * self._omega(
            self._logR_Is_over_Vt + value * self._one_over_Vt + self._R_Is_over_Vt
        )

    @WDFNonlinearElement.tree_node.setter   
    def tree_node(self, node: WDFTreeNode) -> None:
        self._tree_node = node
        next_Rp: float = node.childs[0].port_resistance
        self._two_R_Is: float = 2.0 * next_Rp * self._Is
        self._R_Is_over_Vt: float = next_Rp * self._Is * self._one_over_Vt
        self._logR_Is_over_Vt: float = np.log(self._R_Is_over_Vt)

    @override
    @property
    def port_resistance(self) -> float:
        return np.nan

    @staticmethod
    def _omega(x: float) -> float:
        '''4th order approximation of Wright Omega function'''
        x1 = -3.341459552768620
        x2 = 8.0
        a = -1.314293149877800e-3
        b = 4.775931364975583e-2
        c = 3.631952663804445e-1
        d = 6.313183464296682e-1
        if x < x1:
            y = 0
        elif x < x2:
            y = d + x * (c + x * (b + x * a))
        else:
            y = x - np.log(x)
        return y - (y - np.exp(x - y)) / (y + 1)