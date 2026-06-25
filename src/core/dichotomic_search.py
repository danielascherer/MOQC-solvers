from __future__ import annotations

import networkx as nx
import gurobipy as gp

from core.models.ws import update_ws_objective
from core.solvers.solver_ws import solve_ws


def dichotomic_search(
    p1_v: int,
    p1_e: int,
    p2_v: int,
    p2_e: int,
    model: gp.Model,
    graph: nx.Graph,
    x: dict,
    y: dict,
    graph_basename: str,
    results_ws: list[dict],
    log_dir: str,
    connected: bool
) -> None:
    w_v = p2_e - p1_e
    w_e = p2_v - p1_v
    
    # calculate objective at endpoints
    obj_at_endpoints = w_e * p1_e - w_v * p1_v
    
    update_ws_objective(model, w_v, w_e)
    data_dict = solve_ws(model, graph, x, w_v, w_e, graph_basename, log_dir, connected)
    
    num_v = data_dict["NumberVertices"]
    num_e = data_dict["NumberEdges"]
    current_obj = data_dict["Obj"]
    
    # if no solution is found (time limit reached), return
    if (num_v == ""):
        return

    exact_current_obj = w_e * num_e - w_v * num_v
    if ((num_v == p1_v and num_e == p1_e) or 
        (num_v == p2_v and num_e == p2_e) or
        (exact_current_obj <= obj_at_endpoints)):
        return
        
    results_ws.append(data_dict)
    
    dichotomic_search(p1_v, p1_e, num_v, num_e, model, graph, x, y, graph_basename, results_ws, log_dir, connected)
    dichotomic_search(num_v, num_e, p2_v, p2_e, model, graph, x, y, graph_basename, results_ws, log_dir, connected)