from __future__ import annotations
import numpy as np
from typing import override, TYPE_CHECKING
from .wdf_nodes import WDFAdaptor
from ...utils import construct_scattering, construct_thevenin
if TYPE_CHECKING: from .wdf_tree import WDFTreeNode

__all__ = ["STypeAdaptor", "PTypeAdaptor", "RTypeAdaptor"]

class STypeAdaptor(WDFAdaptor):
    @override
    def update_scaterring_matrix(self, node: WDFTreeNode) -> None:
        resistances: list = [child.port_resistance for child in node.childs]
        self._Rp = np.sum(resistances, dtype=float)
        if not node.is_root:
            resistances = [self._Rp] + resistances
        denom: float = np.sum(resistances, dtype=float)
        n_ports: int = len(resistances)
        self._S_matrix = np.zeros((n_ports, n_ports), dtype=float)
        for i in range(n_ports):
            for j in range(n_ports):
                self._S_matrix[i, j] = -2 * resistances[i] / denom
        for i in range(n_ports):
            self._S_matrix[i, i] += 1
        self._a = np.zeros(n_ports, dtype=float)
        self._b = np.zeros(n_ports, dtype=float)


class PTypeAdaptor(WDFAdaptor):
    @override
    def update_scaterring_matrix(self, node: WDFTreeNode) -> None:
        inv_resistances = [1 / child.port_resistance for child in node.childs]
        self._Rp = 1 / np.sum(inv_resistances, dtype=float)
        if not node.is_root:
            inv_resistances = [1 / self._Rp] + inv_resistances
        denom: float = np.sum(inv_resistances, dtype=float)
        n_ports: int = len(inv_resistances)
        self._S_matrix = np.zeros((n_ports, n_ports), dtype=float)
        for i in range(n_ports):
            for j in range(n_ports):
                self._S_matrix[i, j] = 2 * inv_resistances[j] / denom
        for i in range(n_ports):
            self._S_matrix[i, i] -= 1
        self._a = np.zeros(n_ports, dtype=float)
        self._b = np.zeros(n_ports, dtype=float)


class RTypeAdaptor(WDFAdaptor):
    @override
    def update_scaterring_matrix(self, node: WDFTreeNode) -> None:
        thevenin = construct_thevenin(node)
        self._S_matrix, self._Rp = construct_scattering(thevenin)
        n_ports: int = self._S_matrix.shape[0]
        self._a = np.zeros(n_ports, dtype=float)
        self._b = np.zeros(n_ports, dtype=float)