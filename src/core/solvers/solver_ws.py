from __future__ import annotations

import gurobipy as gp
from gurobipy import GRB
import networkx as nx
import os
from core.utils import TIME_LIMIT, get_status
from core.models.ws import ws_connectedness_callback

# ---------------------------------------------------------------------
# Solve
# ---------------------------------------------------------------------
def solve_ws(
    model: gp.Model,
    graph: nx.Graph,
    x: dict,
    w_v: int,
    w_e: int,
    graph_basename: str,
    log_dir: str,
    connected: bool
) -> dict:
    model.params.LogFile = os.path.join(log_dir, f"SW_{graph_basename}_{w_v}_{w_e}.log")
    model.setParam('TimeLimit', TIME_LIMIT)
    model.setParam('MIPGap', 1e-8)
    
    if connected:
        model._G = graph.copy()
        model.Params.LazyConstraints = 1
        model.optimize(ws_connectedness_callback)
    else:
        model.optimize()
    
    result = {
        "Status": get_status(model),
        "wV": w_v,
        "wE": w_e,
    }
    
    if model.status == GRB.OPTIMAL:
        x_vals = model.getAttr("X", x)
        sol_vertices = {node for node, val in x_vals.items() if val > 0.1}
        optgraph_sol = nx.subgraph(graph, sol_vertices)
        
        result["NumberVertices"] = optgraph_sol.number_of_nodes()
        result["NumberEdges"] = optgraph_sol.number_of_edges()
        result["Obj"] = model.objVal
        result["Density"] = nx.density(optgraph_sol) if optgraph_sol.number_of_nodes() > 1 else 0.0
        result["Time"] = model.runtime
        if connected or optgraph_sol.number_of_nodes() <= 1:
            result["is_Connected"] = True if optgraph_sol.number_of_nodes() <= 1 else nx.is_connected(optgraph_sol)
        else:
            result["is_Connected"] = nx.is_connected(optgraph_sol) if optgraph_sol.number_of_nodes() > 0 else ""
        result["Solution"] = list(sol_vertices)
    else:
        result.update({
            "NumberVertices": "",
            "NumberEdges": "",
            "Obj": "",
            "Density": "",
            "Time": "",
            "is_Connected": "",
            "Solution": []
        })
        
    model.reset(1)
    return result


