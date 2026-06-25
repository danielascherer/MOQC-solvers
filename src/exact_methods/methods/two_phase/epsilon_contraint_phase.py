from __future__ import annotations

import gurobipy as gp
import networkx as nx
import numpy as np
import time

from core.models.m1_c_flow import update_cflow_coefficients
from core.solvers.solver_m1_and_m1_cflow import solve_model_m1_and_m1_cflow

def epsilon_constraint(
    points: np.ndarray,
    model: gp.Model,
    graph: nx.Graph,
    x: dict,
    y: dict,
    c1,
    graph_basename: str,
    log_dir: str,
    connected: bool,
    results_m1_or_m1_cflow: list[dict],
    cflow_cache: tuple | None = None    
) -> float:
    """
    Phase 2 of Two-phase method: epsilon-constraint approach.
    Iterates over intervals defined by WS points and solves M1
    for intermediate values of k.

    Returns:
        elapsed time for this phase
    """
    m1_start_time = time.time()
    # Unpach cache if needed
    if connected and cflow_cache is not None:
        c6_constrs, s_vars, c7_constrs, c8_constrs = cflow_cache

    # Iterate over consecutive WS points    
    for i in range(len(points) - 1):
        point_a = points[i]
        point_b = points[i + 1]
        
        num_v_a = point_a[0]
        num_e_a = point_a[1]
        
        density = num_e_a / ((num_v_a * (num_v_a - 1)) / 2) if num_v_a > 1 else 0.0
        
        if density >= 1.0:
            break
            
        interval = num_v_a - point_b[0]
        k = num_v_a - 1
        
        # Solve for intermediate k values    
        for _ in range(interval - 1):
            c1.RHS = k
            if connected:
                update_cflow_coefficients(model, graph, y, k, c6_constrs, s_vars, c7_constrs, c8_constrs)

            # Solve M1 model   
            result = solve_model_m1_and_m1_cflow(
                model,                 
                x, 
                k, 
                graph_basename,
                log_dir, 
                graph, 
                "M1_C-FLOW" if connected else "M1"
            )
            k -= 1
            
            if result.get("Density", 0) >= 1.0:
                break
            results_m1_or_m1_cflow.append(result)
                
    return time.time() - m1_start_time
