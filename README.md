# Python WDF

## General
Pythow WDF is a object-oriented implementation of the wave digital filters paradigm proposed by Alfred Fettweis in 1986 on Python. You can find a lot of theoretical details in the [Kurt Werner's research](https://stacks.stanford.edu/file/druid:jy057cz8322/KurtJamesWernerDissertation-augmented.pdf).\
Greatest feature of the proposed implementation is constructing WDF scheme directly from the circuit. It can build S-, P- and R- type adaptors and connect them to the tree by itself.

## Circuits
You can define your circuit using `Netlist` class. It has a lot of common with [usual netlist](https://en.wikipedia.org/wiki/Netlist) syntax. But structure was simplify a bit. Each record (row) has 3 values - unique key, element with its own parameters and connections.
```py
# example of the usage Netlist class
bandpass: Netlist = Netlist(
    LumpedElement("v_in", VoltageSource(1e-3), (0, 1)),
    LumpedElement("c1", Capacitor(100 * 1e-9), (0, 2)),
    LumpedElement("r1", Resistor(15924), (2, 1)),
    LumpedElement("c2", Capacitor(1e-9), (3, 1)),
    LumpedElement("r2", Resistor(15924), (2, 3))
)
```
If you need to add your own element you should simply inherit from `CircuitElement` class. There are 2 available modificators: `ReplaceableElement` and `MNAStampedElement` - first shows that element should be replaced by equivalent circuit, second defines MNA stamp of the element.\
You can find netlist examples in the corresponding folder. Examples of the circuit elements are placed at the `src/components/circuit_elements.py`.

## Wave digital filters
Class `WDFScheme` describes wave digital scheme of the corresponding circuit. You can construct it from the `Netlist`. Also its construct applies sampling rate (Hertz) and list of pairs, which should be interpreted as outputs. Last argument is optional - you can use key of the any element to receive signal.
```py
wdf: WDFScheme = WDFScheme(samplerate, bandpass, outputs=[(3, 1)])
```
To process signal you can use `process_signal` method or `process_sample` in the loop. Both methods applies dictionary, where keys - keys of the dynamic elements, values - their new values. They return dictionary - integer keys are correspond to selected outputs, others keys - selected elements (see second example below).
```py
# example of the receiving filter impulse response
delta = [1] + [0] * 30000
impulse_response = wdf.process_signal({"v_in": delta})[0]
```
Outputs add extra open wires in the circuit. To avoid it just ignore `outputs` argument and use `keys` argument of the `process_signal` and `process_sample` methods.
```py
# example without outputs arg
lowpass: Netlist = Netlist(
    LumpedElement("v_in", VoltageSource(1e-3), (0, 1)),
    LumpedElement("r", Resistor(10), (0, 2)),
    LumpedElement("c", Capacitor(3.5e-5), (2, 1))
)

lowpass_wdf: WDFScheme = WDFScheme(samplerate, lowpass)
impulse_response = lowpass_wdf.process_signal({"v_in": delta}, keys=["c"])["c"]
```
If you would like to add new element, which might appears in the WDF representation, you should add new class inherited from `WDFLinearElement` or `WDFNonlinearElement` classes. There are also some some modificators - see source code to more details.
You can find more usage examples in the corresponding folder. Examples of the WDF elements are placed at the `src/components/wdf_elements.py`.

## Installation
Just create Conda (or Mamba) virtual environment from the `conda-env.yml` file.