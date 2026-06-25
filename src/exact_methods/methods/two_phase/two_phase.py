from __future__ import annotations

import os
import time
import pandas as pd
import gurobipy as gp
from gurobipy import GRB
import numpy as np
import networkx as nx

from core.utils import BASE_LOG_DIR, BASE_RESULTS_DIR
from core.graph_utils import read_graph
from core.models.m1 import build_m1_model
from core.models.m1_c_flow import build_m1_cflow_model, build_cflow_cache
from core.dichotomic_search import dichotomic_search
from core.models.ws import build_ws_model
from exact_methods.methods.two_phase.epsilon_contraint_phase import epsilon_constraint


def run_two_phase(graph_path: str, connected: bool) -> None:
    total_time_start = time.time()
    graph_basename = os.path.basename(graph_path)
    
    method_name = "two_phase"

    log_dir = os.path.join(
        BASE_LOG_DIR,
        f"{method_name}_{'connected' if connected else 'plain'}"
    )

    results_dir = os.path.join(
        BASE_RESULTS_DIR,
        f"{method_name}_{'connected' if connected else 'plain'}"
    )
    
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)
    
    graph, num_vertices, num_edges, _, _ = read_graph(graph_path)
    
    # Default: full graph
    lcc_graph = graph
    
    if connected:
        components = list(nx.connected_components(graph))
        if len(components) > 1:
            largest_cc = max(components, key=len)
            lcc_graph = graph.subgraph(largest_cc)
            num_vertices = lcc_graph.number_of_nodes()
            num_edges = lcc_graph.number_of_edges()
            
    # ---------------- Phase 1: Weighted Sum ----------------
    ws_start_time = time.time()
    
    ws_model, ws_x, ws_y = build_ws_model(graph, connected)
    results_ws: list[dict] = []
        
    dichotomic_search(
        0, 0, num_vertices, num_edges,
        ws_model, graph, ws_x, ws_y,
        graph_basename, results_ws,
        log_dir, connected
    )
    
    ws_elapsed_time = time.time() - ws_start_time
    
    if results_ws:
        results_ws_df = pd.DataFrame(results_ws)
    else:
        results_ws_df = pd.DataFrame(columns=["NumberVertices", "NumberEdges", "Time"])
    
    new_row_max = {
        "NumberVertices": num_vertices,
        "NumberEdges": num_edges,
        "Density": nx.density(lcc_graph),
        "Status": "OPTIMAL",
        "Time": 0.0,        
        "is_Connected": nx.is_connected(lcc_graph),
        "Solution": list(lcc_graph.nodes())
    }

    new_row_min = {
        "NumberVertices": 0,
        "NumberEdges": 0, 
        "Density": 0.0,
        "Status": "OPTIMAL", 
        "Time": 0.0, 
        "is_Connected": "",
        "Solution": []
    }
    
    results_ws_df = pd.concat([results_ws_df, pd.DataFrame([new_row_max, new_row_min])], ignore_index=True)
    results_ws_df.sort_values(by=["NumberVertices"], inplace=True, ascending=False)
    
    total_time_ws_gurobi = results_ws_df.get("Time", pd.Series([0])).sum()
    
    csv_prefix = "TwoPhase_WS_connectedness_" if connected else "TwoPhase_WS_"
    results_ws_df.to_csv(os.path.join(results_dir, f"{csv_prefix}{graph_basename}.csv"), index=False)
            
    # ---------------- Phase 2: M1 Epsilon Constraint ----------------
    points = np.array(list(zip(results_ws_df["NumberVertices"], results_ws_df["NumberEdges"])))
    
    if connected:
        eps_model, eps_x, eps_y, c1, c6_constrs, s_vars, c7_constrs, c8_constrs = build_m1_cflow_model(graph)
        cflow_cache = build_cflow_cache(eps_model, graph, eps_y)
    else:
        eps_model, eps_x, eps_y, c1 = build_m1_model(graph)
        cflow_cache = None

    results_m1_or_m1_cflow: list[dict] = []
    
    m1_elapsed_time = epsilon_constraint(
        points, 
        eps_model, 
        graph, 
        eps_x, 
        eps_y, 
        c1,
        graph_basename,  
        log_dir, 
        connected, 
        results_m1_or_m1_cflow,
        cflow_cache
    )
    
    elapsed_total_time = time.time() - total_time_start
    total_time_m1_gurobi = 0.0
    
    if results_m1_or_m1_cflow:
        results_m1_or_m1_cflow_df = pd.DataFrame(results_m1_or_m1_cflow)
        results_m1_or_m1_cflow_df.sort_values(by=["NumberVertices"], inplace=True, ascending=False)
        total_time_m1_gurobi = results_m1_or_m1_cflow_df.get("Time", pd.Series([0])).sum()
        m1_csv_prefix = "TwoPhase_M1_connectedness_" if connected else "TwoPhase_M1_"
        results_m1_or_m1_cflow_df.to_csv(os.path.join(results_dir, f"{m1_csv_prefix}{graph_basename}.csv"), index=False)
        
    # ---------------- Summary File ----------------
    summary_prefix = "TwoPhase_summary_connectedness_" if connected else "TwoPhase_summary_"
    summary_path = os.path.join(results_dir, f"{summary_prefix}{graph_basename}.txt")
    with open(summary_path, "w") as f:
        f.write("=========================================\n")
        f.write("      TWO-PHASE OPTIMIZATION SUMMARY\n")
        f.write("=========================================\n\n")

        f.write("GENERAL\n")
        f.write("-----------------------------------------\n")
        f.write(f"Total execution time      : {elapsed_total_time:.4f} seconds\n")
        f.write(f"Total points found        : {len(results_ws_df) + len(results_m1_or_m1_cflow)}\n\n")

        f.write("PHASE 1 - WEIGHTED SUM (WS)\n")
        f.write("-----------------------------------------\n")
        f.write(f"Gurobi optimization time  : {total_time_ws_gurobi:.4f} seconds\n")
        f.write(f"Total WS phase time       : {ws_elapsed_time:.4f} seconds\n")
        f.write(f"Number of WS points found : {len(results_ws_df)}\n\n")

        f.write("PHASE 2 - EXACT SOLVER (M1 or M1+C-Flow)\n")
        f.write("-----------------------------------------\n")
        f.write(f"Gurobi optimization time  : {total_time_m1_gurobi:.4f} seconds\n")
        f.write(f"Total M1 phase time       : {m1_elapsed_time:.4f} seconds\n")
        f.write(f"Number of M1 points found : {len(results_m1_or_m1_cflow)}\n\n")

        f.write("=========================================\n")
