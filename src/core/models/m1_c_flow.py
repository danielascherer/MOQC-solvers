from __future__ import annotations

import gurobipy as gp
from gurobipy import GRB
import networkx as nx
from typing import Dict, Tuple

def build_m1_cflow_model(graph: nx.Graph) -> tuple[gp.Model, dict, dict, gp.Constr, dict, dict, dict, dict]:
    model = gp.Model("M1_CFLOW")
    model.setParam(GRB.Param.LogToConsole, 0)
    model.setParam(GRB.Param.Threads, 1)

    x = {i: model.addVar(name=f"x({i})", vtype=GRB.BINARY) for i in graph.nodes}
    y = {
        (i, j): model.addVar(name=f"y({i},{j})", vtype=GRB.CONTINUOUS, lb=0.0)
        for (i, j) in graph.edges
    }

    F = {}
    for (i, j) in graph.edges:
        F[i, j] = model.addVar(name=f"F({i},{j})", vtype=GRB.CONTINUOUS, lb=0.0)
        F[j, i] = model.addVar(name=f"F({j},{i})", vtype=GRB.CONTINUOUS, lb=0.0)

    s = {i: model.addVar(name=f"s({i})", vtype=GRB.BINARY) for i in graph.nodes}

    model.setObjective(gp.quicksum(y.values()), GRB.MAXIMIZE)
    c1 = model.addConstr(gp.quicksum(x.values()) == 0, name="C1")

    for (i, j) in graph.edges:
        model.addConstr(y[i, j] <= x[j], name=f"C2({i},{j})")
        model.addConstr(y[i, j] <= x[i], name=f"C3({i},{j})")

    model.addConstr(gp.quicksum(s.values()) == 1, name="C4")

    for j in graph.nodes:
        model.addConstr(s[j] <= x[j], name=f"C5({j})")

    for i in graph.nodes:
        neighbors = list(graph.neighbors(i))
        flow_in  = gp.quicksum(F[j, i] for j in neighbors)
        flow_out = gp.quicksum(F[i, j] for j in neighbors)
        model.addConstr(flow_in - flow_out == x[i] - 0 * s[i], name=f"C6({i})")

    for (i, j) in graph.edges:
        model.addConstr(F[i, j] <= 0 * y[i, j], name=f"C7({i},{j})")
        model.addConstr(F[j, i] <= 0 * y[i, j], name=f"C8({j},{i})")

    model.update()
    
    c6_constrs = {i: model.getConstrByName(f"C6({i})") for i in graph.nodes}
    s_vars     = {i: model.getVarByName(f"s({i})")     for i in graph.nodes}
    c7_constrs = {(i, j): model.getConstrByName(f"C7({i},{j})") for (i, j) in graph.edges}
    c8_constrs = {(i, j): model.getConstrByName(f"C8({j},{i})") for (i, j) in graph.edges}
    
    return model, x, y, c1, c6_constrs, s_vars, c7_constrs, c8_constrs

# ---------------------------------------------------------------------
# Cache model
# ---------------------------------------------------------------------

def build_cflow_cache(
    model: gp.Model,
    graph: nx.Graph,
    y: dict,
) -> tuple[dict, dict, dict, dict]:
    """Cache constraint and variable references needed by the coefficient updater.

    All Gurobi name-lookups (getConstrByName / getVarByName) are performed
    once here, before the main solving loop. The cached objects are then
    passed directly to update_cflow_coefficients on every iteration,
    avoiding O(k * (|V| + |E|)) repeated lookups.

    Args:
        model: The M1-C-Flow Gurobi model (after build_m1_cflow_model).
        graph: The original input graph.
        y: Edge decision variables (y[i,j]).

    Returns:
        A tuple of (c6_constrs, s_vars, c7_constrs, c8_constrs), each a dict
        keyed by node or edge as appropriate.
    """
    c6_constrs = {i: model.getConstrByName(f"C6({i})") for i in graph.nodes}
    s_vars     = {i: model.getVarByName(f"s({i})")     for i in graph.nodes}
    c7_constrs = {(i, j): model.getConstrByName(f"C7({i},{j})") for (i, j) in graph.edges}
    c8_constrs = {(i, j): model.getConstrByName(f"C8({j},{i})") for (i, j) in graph.edges}
    return c6_constrs, s_vars, c7_constrs, c8_constrs

# ---------------------------------------------------------------------
# Update model
# ---------------------------------------------------------------------

def update_cflow_coefficients(
    model: gp.Model, graph: nx.Graph, y: dict, k: int,
    c6_constrs: dict, s_vars: dict, c7_constrs: dict, c8_constrs: dict
) -> None:
    for i in graph.nodes:
        model.chgCoeff(c6_constrs[i], s_vars[i], k)

    for (i, j) in graph.edges:
        model.chgCoeff(c7_constrs[i, j], y[i, j], -k)
        model.chgCoeff(c8_constrs[i, j], y[i, j], -k)
    model.update()