from __future__ import annotations
from sage.all import var
from uuid import uuid4
from .spqr_tree import SPQRTreeNode
from ..core import LumpedElement, Netlist, WDFAdaptor
from ..components import Resistor, IdealVoltageSource
from typing import TYPE_CHECKING
if TYPE_CHECKING: from ..core.wdf.wdf_tree import WDFTreeNode

__all__ = ["construct_thevenin"]

def common_edge(node1: SPQRTreeNode, node2: SPQRTreeNode) -> tuple:
    edges1: set[tuple] = set(node1.subgraph.edges())
    edges2: set[tuple] = set(node2.subgraph.edges())
    common: set[tuple] = edges1.intersection(edges2)
    return list(common)[0]

def map_nodes(nodes: tuple, mapping: dict[int, int]) -> tuple:
    return tuple([mapping[node] for node in nodes])

# some bullshit
def construct_thevenin(node: WDFTreeNode) -> Netlist:
    up_resistor: str = str(uuid4())
    up_voltage: str = str(uuid4())
    r_suffix: str = "_r"
    v_suffix: str = "_v"
    free_node: int = max(list(node.spqr_node.subgraph.to_dictionary().keys())) + 1
    unordered_netlist: Netlist = Netlist()
    child_keys: dict[str, WDFTreeNode] = {child.key: child for child in node.childs}
    for elements in node.spqr_node.elements.values():
        for element in elements:
            if element.key not in child_keys and element.n_nodes == 2:
                continue
            if element.n_nodes != 2:
                unordered_netlist.add_element(element)
            else:
                unordered_netlist.add_element(LumpedElement(f"{element.key}{r_suffix}", 
                                              Resistor(child_keys[element.key].port_resistance),
                                              (free_node, element.nodes[0])))
                unordered_netlist.add_element(LumpedElement(f"{element.key}{v_suffix}", IdealVoltageSource(), 
                                              (free_node, element.nodes[1])))
                free_node += 1
    for child in node.childs:
        if not issubclass(child.dtype, WDFAdaptor):
            continue
        nodes = common_edge(node.spqr_node, child.spqr_node)
        unordered_netlist.add_element(LumpedElement(f"{child.key}{r_suffix}", 
                                      Resistor(child.port_resistance),
                                      (free_node, nodes[0])))
        unordered_netlist.add_element(LumpedElement(f"{child.key}{v_suffix}", IdealVoltageSource(), 
                                      (free_node, nodes[1])))
        free_node += 1
    if not node.is_root:
        nodes: tuple | None = None
        if issubclass(node.parent.dtype, WDFAdaptor):
            *nodes, _ = common_edge(node.spqr_node, node.parent.spqr_node)
        else:
            for elements in node.spqr_node.elements.values():
                for element in elements:
                    if element.key not in child_keys and element.n_nodes == 2:
                        nodes = element.nodes
                        break
        unordered_netlist.add_element(LumpedElement(up_resistor, Resistor(var("Rp")), (free_node, nodes[0])))
        unordered_netlist.add_element(LumpedElement(up_voltage, IdealVoltageSource(), (free_node, nodes[1])))
        free_node += 1
    node_mapping: dict[int, int] = {}
    cur_node: int = 0
    for element in unordered_netlist.values():
        for old_node in element.nodes:
            if old_node in node_mapping:
                continue
            node_mapping[old_node] = cur_node
            cur_node += 1
    port_number: int = 0
    thevenin: Netlist = Netlist()
    if not node.is_root:
        thevenin.add_element(LumpedElement(f"{port_number}r", unordered_netlist[up_resistor].element,
                             map_nodes(unordered_netlist[up_resistor].nodes, node_mapping)))
        thevenin.add_element(LumpedElement(f"{port_number}v", unordered_netlist[up_voltage].element,
                             map_nodes(unordered_netlist[up_voltage].nodes, node_mapping)))
        port_number += 1
    for child in node.childs:
        thevenin.add_element(LumpedElement(f"{port_number}r", unordered_netlist[f"{child.key}{r_suffix}"].element,
                             map_nodes(unordered_netlist[f"{child.key}{r_suffix}"].nodes, node_mapping)))
        thevenin.add_element(LumpedElement(f"{port_number}v", unordered_netlist[f"{child.key}{v_suffix}"].element,
                             map_nodes(unordered_netlist[f"{child.key}{v_suffix}"].nodes, node_mapping)))
        port_number += 1
    multiports: list[LumpedElement] = []
    for element in unordered_netlist.values():
        if element.n_nodes == 2:
            continue
        multiports.append(element)
    for idx, multiport in enumerate(multiports):
        thevenin.add_element(LumpedElement(f"{idx}mp", multiport.element,
                                           map_nodes(multiport.nodes, node_mapping)))
    return thevenin