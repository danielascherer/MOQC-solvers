from __future__ import annotations

import gurobipy as gp
from gurobipy import GRB
import networkx as nx
import os
from core.utils import get_status
from core.utils import SELECTION_THRESHOLD, BASE_LOG_DIR, TIME_LIMIT


# ---------------------------------------------------------------------
# Solve
# ---------------------------------------------------------------------
def solve_model_m1_and_m1_cflow(
    model: gp.Model,
    x: dict,
    k: int,
    graph_basename: str,
    log_dir: str,
    graph: nx.Graph,
    model_type: str 
) -> dict:
    """
    Solves the M1 or M1-C-Flow model.
    
    Args:
        model: The Gurobi model.
        x: The decision variables for the nodes.
        k: The size of the clique.
        graph_basename: The basename of the graph.
        log_dir: The directory to save the log files.
        graph: The graph.
    Returns:
        A dictionary with the results.
    """
    model.params.LogFile = os.path.join(log_dir, f"{model_type}_{graph_basename}_{k}.log")
    model.setParam('TimeLimit', TIME_LIMIT)
    model.setParam('MIPGap', 1e-8)
    
    model.optimize()
    
    result = {"Status": get_status(model)}
    
    if model.status == GRB.OPTIMAL:
        x_vals = model.getAttr("X", x)
        sol_vertices = {node for node, val in x_vals.items() if val > SELECTION_THRESHOLD}
        subgraph = nx.subgraph(graph, sol_vertices)
        
        num_edges = model.getObjective().getValue()
        result["NumberVertices"] = k
        result["NumberEdges"] = num_edges
        result["Density"] = nx.density(subgraph)
        result["Time"] = model.runtime
        result["is_Connected"] = nx.is_connected(subgraph) if len(subgraph) > 0 else ""
        result["Solution"] = list(sol_vertices)
    else:
        result.update({
            "NumberVertices": k,
            "NumberEdges": 0,
            "Density": 0.0,
            "Time": 0.0,
            "is_Connected": "",
            "Solution": []
        })
        
    model.reset(1)
    return result
