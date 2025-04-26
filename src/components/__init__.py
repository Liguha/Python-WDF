from .circuit_elements import *
from .wdf_elelements import *

CIRCUIT_TO_WDF: dict[type, type] = {
    Resistor: WDFResistor,
    OpenCircuit: WDFOpenCircuit,
    Inductor: WDFInductor,
    Capacitor: WDFCapacitor,
    VoltageSource: WDFVoltageSource
}