from dataclasses import dataclass
from .circuit_element import CircuitElement, ReplaceableElement

__all__ = ["Netlist", "LumpedElement"]

@dataclass(frozen=True)
class LumpedElement:
    key: str
    element: CircuitElement
    nodes: tuple[int]

    def __post_init__(self) -> None:
        if not isinstance(self.nodes, tuple):
            object.__setattr__(self, "nodes", tuple(self.nodes))

    @property
    def n_nodes(self) -> int:
        return len(self.nodes)

class Netlist:
    def __init__(self, *elements: tuple[LumpedElement]) -> None:
        self._elements: dict[str, LumpedElement] = {}
        for element in elements:
            self.add_element(element)

    def __getitem__(self, key: str) -> LumpedElement:
        return self._elements[key]

    def add_element(self, element: LumpedElement) -> None:
        if element.key in self._elements:
            raise IndexError(f"Key '{element.key}' already presented in netlist")
        self._elements[element.key] = element

    def remove_element(self, key: str | LumpedElement) -> None:
        if isinstance(key, LumpedElement):
            key = key.key
        if key not in self._elements:
            raise IndexError(f"Key '{key}' is not presented in netlist")
        self._elements.pop(key)

    def keys(self) -> list[str]:
        return list(self._elements.keys())
    
    def values(self) -> list[LumpedElement]:
        return list(self._elements.values())

    def free_node(self) -> int:
        node: int = -1
        for element in self.values():
            node = max(node, *element.nodes)
        return node + 1
    
    def perform_replacements(self) -> None:
        changed: bool = True
        while changed:
            changed = False
            for element in self.values():
                elem: CircuitElement = element.element
                if not isinstance(elem, ReplaceableElement):
                    continue
                changed = True
                replacement = elem.replacement(element, self.free_node())
                self.remove_element(element)
                for new_elem in replacement:
                    self.add_element(new_elem)