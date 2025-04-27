import re
import numpy as np
from sage.all import SR, Expression, identity_matrix, matrix, solve
from sage.matrix.matrix0 import Matrix
from ..core import Netlist, LumpedElement, MNAStampedElement, CircuitElement
from ..components import Resistor

__all__ = ["construct_scattering"]

def netlist_meta(thevenin: Netlist) -> tuple[int, int, int]:
    num_ports: int = 0
    num_nodes: int = 0
    num_extras: int = 0
    for key in thevenin.keys():
        if re.match(r"\d+[r, v]", key):
            num_ports += 1
        else:
            num_extras += 1
    num_ports //= 2
    num_nodes: int = thevenin.free_node()
    return num_nodes, num_ports, num_extras

def construct_mna_matrix(thevenin: Netlist) -> Matrix:
    num_nodes, num_ports, num_extras = netlist_meta(thevenin)
    x_mat: Matrix = matrix(SR, num_nodes + num_ports + num_extras,
                           num_nodes + num_ports + num_extras)
    for element in thevenin.values():
        elem: MNAStampedElement = element.element
        port: int = int(re.match(r"\d+", element.key)[0])
        changes: dict = elem.mna_stamp(element.nodes, port, num_nodes, num_ports)
        for idx, value in changes.items():
            x_mat[*idx] += value
    return x_mat

def remove_datum_node(x_mat: Matrix, datum: int) -> Matrix:
    indicies: list[int] = [x for x in range(x_mat.nrows()) if x != datum]
    return matrix(x_mat[indicies, indicies])

def s_rp_matrices(x_inv: Matrix, thevenin: Netlist) -> tuple[Matrix, Matrix]:
    num_nodes, num_ports, num_extras = netlist_meta(thevenin)
    start_ports: int = -(num_ports + num_extras)
    end_ports: int = -num_extras if num_extras > 0 else x_inv.ncols()
    vertical = matrix(SR, x_inv.nrows(), num_ports)
    vertical[start_ports:end_ports, :] = identity_matrix(num_ports)
    horizontal = matrix(SR, num_ports, x_inv.ncols())
    horizontal[:, start_ports:end_ports] = identity_matrix(num_ports)
    rp_diag = matrix(SR, num_ports, num_ports)
    for element in thevenin.values():
        elem: CircuitElement = element.element
        if not isinstance(elem, Resistor):
            continue
        port: int = int(re.match(r"\d+", element.key)[0])
        rp_diag[port, port] = elem.R
    s_mat: Matrix = identity_matrix(num_ports) + 2 * rp_diag * horizontal * x_inv * vertical
    return s_mat, rp_diag

def adapt_port(s_mat: Matrix, rp_diag: Matrix, port: int) -> tuple[Matrix, Expression]:
    if port < 0 or port >= s_mat.nrows():
        raise IndexError(f"Port index {port} is largder than number of available ports {s_mat.nrows()}")
    s_nn = s_mat[port, port]
    r_n = rp_diag[port, port]
    r_n_solves = solve(s_nn == 0, r_n)
    r_n_solve_expr = r_n_solves[0]
    return s_mat, r_n_solve_expr

def construct_scattering(thevenin: Netlist, adapted_port: int) -> tuple[np.ndarray, float]:
    x_mat = construct_mna_matrix(thevenin)
    x_mat = x_mat.simplify_rational()
    x_mat = remove_datum_node(x_mat, 0)
    x_inv = x_mat.inverse()
    s_mat, rp_diag = s_rp_matrices(x_inv, thevenin)
    adapted_port = int(adapted_port)
    adapt_expr = None
    if adapted_port >= 0:
        s_mat, adapt_expr = adapt_port(s_mat, rp_diag, adapted_port)
    resistance_arg = {}
    resistance: float = -1
    if adapted_port >= 0:
        resistance_arg[adapt_expr.left()] = adapt_expr.right().simplify_rational()
        resistance = float(resistance_arg[adapt_expr.left()])
    s_mat = s_mat.subs(resistance_arg).numerical_approx(digits=100)
    return np.array(s_mat, dtype=float), resistance