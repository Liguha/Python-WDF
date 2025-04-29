import warnings
from dataclasses import dataclass
from typing import Literal, Self
from sage.all import Graph
from sage.graphs.connectivity import TriconnectivitySPQR
from .lumped_circuits import Netlist, LumpedElement

__all__ = ["SPQRTreeNode", "SPQRTree"]

@dataclass(unsafe_hash=False)
class SPQRTreeNode:
    node_type: Literal["S", "P", "Q", "R"]
    subgraph: Graph
    elements: dict[tuple, list[LumpedElement]]

    def __hash__(self) -> int:
        nodes: tuple = tuple(sorted(self.elements.keys()))
        return hash((self.node_type, self.subgraph, nodes))
    
    def __eq__(self, other: Self) -> bool:
        if not isinstance(other, type(self)):
            return False
        nodes_self: tuple = tuple(sorted(self.elements.keys()))
        nodes_other: tuple = tuple(sorted(other.elements.keys()))
        ok: bool = self.node_type == other.node_type
        ok = ok and self.subgraph == other.subgraph
        ok = ok and nodes_self == nodes_other
        return ok


class SPQRTree:
    def __init__(self, netlist: Netlist) -> None:
        # Notion: virtual edges are not removed
        self.adjacency_list: dict[SPQRTreeNode, list[SPQRTreeNode]] = {}
        self._netlist: Netlist = netlist
        tree: dict = self._build_sage_spqr()
        self._parse_sage_spqr(tree)

    def _build_sage_spqr(self) -> dict[tuple[str, Graph], list[tuple[str, Graph]]]:
        free_node: int = self._netlist.free_node()
        edges: list[tuple[int, int]] = []
        for element in self._netlist.values():
            # incorrect
            if element.n_nodes < 2:
                warnings.warn(f"Element {element} had only 1 connection and was ignored")
                continue
            # is single port
            elif element.n_nodes == 2:
                edges.append(sorted(element.nodes))
            # is multiport
            else:
                artificials = list(range(free_node, free_node + 3))
                free_node += 3
                for artificial_node in artificials:
                    for node in element.nodes:
                        edges.append((node, artificial_node))
        graph: Graph = Graph(edges, multiedges=True)
        tric: TriconnectivitySPQR = TriconnectivitySPQR(graph)
        return tric.get_spqr_tree().to_dictionary() 

    def _parse_sage_spqr(self, tree: dict[tuple[str, Graph], list[tuple[str, Graph]]]) -> None:
        elements: dict[tuple, list[LumpedElement]] = {}
        for element in self._netlist.values():
            key = tuple(sorted(element.nodes))
            if key not in elements:
                elements[key] = []
            elements[key].append(element)
        free_node: int = self._netlist.free_node()
        
        def parse_node(node_type: str, graph: Graph) -> SPQRTreeNode:
            real_verticies = [v for v in graph.vertices() if v < free_node]
            subgraph = graph.subgraph(real_verticies)
            edges = set(graph.edges())
            node_elements = {k: v for k, v in elements.items() if (*k, None) in edges}
            node = SPQRTreeNode(node_type, subgraph, node_elements)
            if node not in self.adjacency_list:
                self.adjacency_list[node] = []
                for t, g in tree[(node_type, graph)]:
                    self.adjacency_list[node].append(parse_node(t, g))
            return node
        parse_node(*(list(tree.keys())[0]))