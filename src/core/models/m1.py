from __future__ import annotations

import gurobipy as gp
from gurobipy import GRB
import networkx as nx

# ---------------------------------------------------------------------
# Build model
# ---------------------------------------------------------------------

def build_m1_model(graph: nx.Graph) -> tuple[gp.Model, dict, dict, gp.Constr]:
    """Build the plain M1 MIP model

    Objective: maximise the number of edges in the selected subgraph of size k.

    Variables:
        x[i] ∈ {0, 1}   — node i is in the subgraph.
        y[i,j] ∈ [0, 1] — edge (i,j) is in the subgraph.

    Constraints:
        C1: Σ x[i] = k
        C2: y[i,j] ≤ x[j]  for all (i,j) ∈ E
        C3: y[i,j] ≤ x[i]  for all (i,j) ∈ E

    Args:
        graph: The input graph.
    Returns:
        A tuple of (model, x_vars, y_vars, c1_constr).
    """
    model = gp.Model("M1")
    model.setParam(GRB.Param.LogToConsole, 0)
    model.setParam(GRB.Param.Threads, 1)

    x = {i: model.addVar(name=f"x({i})", vtype=GRB.BINARY) for i in graph.nodes}
    y = {
        (i, j): model.addVar(name=f"y({i},{j})", vtype=GRB.CONTINUOUS, lb=0.0)
        for (i, j) in graph.edges
    }
    model.update()

    model.setObjective(gp.quicksum(y.values()), GRB.MAXIMIZE)

    c1 = model.addConstr(gp.quicksum(x.values()) == 0, name="C1")

    for (i, j) in graph.edges:
        model.addConstr(y[i, j] <= x[j], name=f"C2({i},{j})")
        model.addConstr(y[i, j] <= x[i], name=f"C3({i},{j})")

    model.update()
    return model, x, y, c1

