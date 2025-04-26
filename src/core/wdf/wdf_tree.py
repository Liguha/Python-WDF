import numpy as np
from typing import Any, Self
from uuid import uuid4
from weakref import proxy, ProxyType
from .wdf_nodes import WDFElement, WDFLinearElement, WDFNonlinearElement, WDFAdaptor
from .wdf_adaptors import STypeAdaptor, PTypeAdaptor, RTypeAdaptor
from ...components import CIRCUIT_TO_WDF
from ...utils import unproxy, SPQRTree, SPQRTreeNode

__all__ = ["WDFTreeNode", "WDFTree"]

class WDFTreeNode:
    def __init__(self, key: str,
                 element: WDFElement,
                 childs: list[Self] | None = None) -> None:
        self._parent: ProxyType | None = None
        self._element: WDFElement = element
        self._key: str = key
        self._childs: list[WDFTreeNode] = childs if childs is not None else []
        self.spqr_node: SPQRTreeNode | None = None

    @property
    def dtype(self) -> type:
        return type(self._element)

    @property
    def key(self) -> str:
        return self._key

    @property
    def parent(self) -> Self | None:
        return self._parent
    
    @parent.setter
    def parent(self, value: Self | NotImplementedError) -> None:
        if value is not None:
            self._parent = proxy(value)
        else:
            self._parent = None
    
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
    def port_resistance(self) -> float:
        return self._element.port_resistance
    
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
    def __init__(self, samplerate: int, spqr: SPQRTree) -> None:
        self._root: WDFTreeNode = None
        self._nodes: dict[str, WDFTreeNode] = {}
        self._parse_spqr_tree(samplerate, spqr)
        # root select
        priorities = [WDFNonlinearElement, RTypeAdaptor, WDFAdaptor]
        rooted: bool = False
        for dtype in priorities:
            if rooted:
                break
            for node in self._nodes.values():
                if not issubclass(node.dtype, dtype):
                    continue
                self._set_root(node)
                rooted = True
                break
        self._post_init()

    def __getitem__(self, key: str) -> WDFTreeNode:
        return self._nodes[key]
    
    def _parse_spqr_tree(self, samplerate: int, spqr: SPQRTree) -> None:
        adaptors = {
            "S": STypeAdaptor,
            "P": PTypeAdaptor,
            "R": RTypeAdaptor
        }
        def parse_node(prev: SPQRTree, node: SPQRTreeNode) -> WDFTreeNode:
            element: WDFAdaptor = adaptors[node.node_type](samplerate)
            childs: list[WDFTreeNode] = []
            for ports in node.elements.values():
                for port in ports:
                    if port.n_nodes != 2:
                        continue
                    child = WDFTreeNode(port.key, CIRCUIT_TO_WDF[type(port.element)](samplerate, port.element))
                    self._nodes[port.key] = child
                    childs.append(child)
            for child_node in spqr.adjacency_list[node]:
                if child_node == prev:
                    continue
                child = parse_node(node, child_node)
                childs.append(child)
            parsed_node = WDFTreeNode(str(uuid4()), element, childs)
            parsed_node.spqr_node = node
            self._nodes[parsed_node.key] = parsed_node
            for child in childs:
                child.parent = parsed_node
            return parsed_node
        self._root = parse_node(None, list(spqr.adjacency_list.keys())[0])
    
    def _set_root(self, new_root: WDFTreeNode) -> None:
        def dfs(node: WDFTreeNode) -> bool:
            if node == new_root:
                if node.parent is not None:
                    node._childs.append(unproxy(node.parent))
                node.parent = None
                return True
            for child in node.childs:
                if dfs(child):
                    node._childs.remove(child)
                    if node.parent is not None:
                        node._childs.append(unproxy(node.parent))
                    node.parent = child
                    return True
            return False
        dfs(self.root)
        self._root = new_root

    def _post_init(self) -> None:
        # TODO: port adapatation
        pass
    
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