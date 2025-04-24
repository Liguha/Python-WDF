import numpy as np
from typing import Any, Self
from .wdf_nodes import WDFElement
from weakref import proxy, ProxyType


class WDFTreeNode:
    def __init__(self, parent: Self | None,
                 element: WDFElement,
                 childs: list[Self],
                 key: str) -> None:
        self._parent: ProxyType | None = None if parent is None else proxy(parent)
        self._element: WDFElement = element
        self._key: str = key
        self._childs: list[WDFTreeNode] = childs

    @property
    def key(self) -> str:
        return self._key

    @property
    def parent(self) -> Self | None:
        return self._parent
    
    @property
    def childs(self) -> list[Self]:
        return self._childs

    @property
    def is_root(self) -> bool:
        return self.parent is None
    
    @property
    def is_leaf(self) -> bool:
        return len(self.childs) == 0
    
    @property
    def reflected_wave(self) -> np.ndarray:
        return self._element.reflected_wave
    
    @property
    def incident_wave(self) -> np.ndarray:
        return self._element.incident_wave
    
    @incident_wave.setter
    def incident_wave(self, value: Any) -> None:
        self._element.incident_wave = value
    
    def wave_up(self) -> None:
        # index 0 is for upward port
        incident: list = [child.reflected_wave[0] for child in self.childs]
        self.incident_wave = np.array(incident, dtype=float)
        
    def wave_down(self) -> None:
        # idx + 1 because of 0 is reserved for parent if it exists
        shift: int = int(not self.is_root)
        for idx, child in enumerate(self.childs):
            child.incident_wave = self.reflected_wave[idx + shift]

    
class WDFTree:
    def __init__(self) -> None:
        # TODO: construct, root select
        self._root: WDFTreeNode = None
        self._nodes: dict[str, WDFTreeNode] = {}

    def __getitem__(self, key: str) -> WDFTreeNode:
        return self._nodes[key]
    
    @property
    def root(self) -> WDFTreeNode:
        return self._root

    def wave_up(self) -> None:
        def propogate_wave(node: WDFTreeNode) -> None:
            for child in node.childs:
                if child.is_leaf:
                    continue
                propogate_wave(child)
            node.wave_up()
        propogate_wave(self._root)
        
    def wave_down(self) -> None:
        def propogate_wave(node: WDFTreeNode) -> None:
            node.wave_down()
            for child in node.childs:
                propogate_wave(child)
        propogate_wave(self._root)