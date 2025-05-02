from uuid import uuid4
from copy import deepcopy
from typing import Any
from .wdf_tree import WDFTree
from ..lumped_circuits import Netlist, LumpedElement
from ...components import OpenCircuit
from ..spqr_tree import SPQRTree

__all__ = ["WDFScheme"]

class WDFScheme:
    def __init__(self, samplerate: int, netlist: Netlist, 
                 outputs: list[tuple] | None = None) -> None:
        if outputs is None:
            outputs = []
        self._output_ids: list[str] = [str(uuid4()) for _ in outputs]
        modified_netlist: Netlist = deepcopy(netlist)
        for id, nodes in zip(self._output_ids, outputs):
            modified_netlist.add_element(LumpedElement(id, OpenCircuit(), nodes))
        modified_netlist.perform_replacements()
        # trick to avoid constrcution of R-adaptors with only 2 ports
        for element in modified_netlist.values():
            if element.n_nodes <= 2:
                continue
            i, j, k, *_ = element.nodes
            modified_netlist.add_element(LumpedElement(str(uuid4()), OpenCircuit(), (i, j)))
            modified_netlist.add_element(LumpedElement(str(uuid4()), OpenCircuit(), (j, k)))
            modified_netlist.add_element(LumpedElement(str(uuid4()), OpenCircuit(), (i, k)))
        self._wdf_tree: WDFTree = WDFTree(samplerate, SPQRTree(modified_netlist))

    def process_sample(self, sample: dict[str, Any], 
                       keys: list[str] | None = None) -> dict[int | str, float]:
        if keys is None:
            keys = []
        keys = list(range(len(self._output_ids))) + keys
        outputs: dict[int | str, float] = {}
        for key, value in sample.items():
            wdf_key: str = key if isinstance(key, str) else self._output_ids[key]
            self._wdf_tree[wdf_key].set_sample_data(value)
        self._wdf_tree.wave_up()
        self._wdf_tree.wave_down()
        for key in keys:
            wdf_key: str = key if isinstance(key, str) else self._output_ids[key]
            a = self._wdf_tree[wdf_key].incident_wave[0]
            b = self._wdf_tree[wdf_key].reflected_wave[0]
            outputs[key] = (a + b) / 2
        return outputs

    def process_signal(self, signal: dict[str, list[Any]], 
                       keys: list[str] | None = None) -> dict[int | str, list[float]]:
        '''Process signal from output.
        
        Args:
            signal: Dictionary with inputs: key - key of the dynamic element,
                value - list of its values.
            keys: Optional. It determines which elements besides outputs should
                be in the output. Defaults to None.
        
        Returns:
            It returns dictionary which contains all `keys` and voltages on it, also
            it includes outputs, their keys are corresponding integers.
        '''
        outputs: dict[int | str, list[float]] = {}
        n_samples: int = max([len(x) for x in signal.values()])
        self.reset()
        for i in range(n_samples):
            sample_input: dict[str, Any] = {k: v[i] for k, v in signal.items() if len(v) > i}
            sample_output: dict[int | str, float] = self.process_sample(sample_input, keys)
            for key, value in sample_output.items():
                if key not in outputs:
                    outputs[key] = []
                outputs[key].append(value)
        return outputs

    def reset(self) -> None:
        self._wdf_tree.reset()
