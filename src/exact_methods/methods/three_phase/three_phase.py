from __future__ import annotations

import os
import time
import pandas as pd
import numpy as np
import networkx as nx

from core.utils import BASE_LOG_DIR, BASE_RESULTS_DIR
from core.graph_utils import read_graph

from core.models.ws import build_ws_model
from core.models.m1 import build_m1_model
from core.models.m1_c_flow import build_m1_cflow_model
from core.dichotomic_search import dichotomic_search
from exact_methods.methods.three_phase.local_search_phase import explore_weakly_efficient_solutions

def run_three_phase(graph_path: str, connected: bool) -> None:
    """
    Main pipeline execution.

    Steps:
        1. Read graph
        2. Run Phase 1 (WS search)
        3. Run Phase 2 (heuristics)
        4. Run Phase 3 (exact M1)
        5. Export results to CSV files
    """
    total_time_start = time.time()
    graph_basename = os.path.basename(graph_path)
    
    method_name = "three_phase"

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
    
    graph, num_vertices, num_edges, degrees_graph, degrees_zero = read_graph(graph_path)
    lcc_graph = graph

    if connected:
        components = list(nx.connected_components(graph))
        if len(components) > 1:
            largest_cc = max(components, key=len)
            lcc_graph = graph.subgraph(largest_cc)
            num_vertices = lcc_graph.number_of_nodes()
            num_edges = lcc_graph.number_of_edges()
            
    max_degree_val = max(degrees_graph.values()) if degrees_graph else 0

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
        "Status": "OPTIMAL", 
        "NumberVertices": num_vertices, 
        "NumberEdges": num_edges, 
        "Density": nx.density(lcc_graph),
        "Time": 0.0,
        "is_Connected": nx.is_connected(lcc_graph), 
        "Solution": list(lcc_graph.nodes())
    }
    new_row_min = {
        "Status": "OPTIMAL", 
        "NumberVertices": 0, 
        "NumberEdges": 0, 
        "Density": 0.0,
        "Time": 0.0, 
        "Solution": []
    }
    
    results_ws_df = pd.concat([results_ws_df, pd.DataFrame([new_row_max, new_row_min])], ignore_index=True)
    results_ws_df.sort_values(by=["NumberVertices"], inplace=True, ascending=False)
    
    total_time_ws_gurobi = results_ws_df.get("Time", pd.Series([0])).sum()
    
    csv_prefix = "ThreePhase_connectedness_" if connected else "ThreePhase_"
    results_ws_df.to_csv(os.path.join(results_dir, f"{csv_prefix}WS_{graph_basename}.csv"), index=False)
    
   
    # ---------------- Phase 2 & 3: Heuristics & M1 ----------------
    points = np.array(list(zip(results_ws_df["NumberVertices"], results_ws_df["NumberEdges"])))
    
    if connected:
        m1_model, m1_x, m1_y, c1, c6_constrs, s_vars, c7_constrs, c8_constrs = build_m1_cflow_model(graph)
        m1_components = {
            'model': m1_model, 'x': m1_x, 'y': m1_y,
            'c6_constrs': c6_constrs, 's_vars': s_vars,
            'c7_constrs': c7_constrs, 'c8_constrs': c8_constrs
        }
    else:
        m1_model, m1_x, m1_y, c1 = build_m1_model(graph)
        m1_components = {'model': m1_model, 'x': m1_x, 'y': m1_y}
        
    df_a, df_d, results_m1 = explore_weakly_efficient_solutions(
        points, num_vertices, num_edges, max_degree_val, graph, degrees_zero, degrees_graph,
        results_ws_df, m1_components, connected, log_dir, graph_basename
    )
    
    df_d.to_csv(os.path.join(results_dir, f"{csv_prefix}minDegreeLS_{graph_basename}.csv"), index=False)
    df_a.to_csv(os.path.join(results_dir, f"{csv_prefix}maxDegreeLS_{graph_basename}.csv"), index=False)
    
    total_time_m1_gurobi = 0.0
    if results_m1:
        results_m1_df = pd.DataFrame(results_m1)
        results_m1_df.sort_values(by=["NumberVertices"], inplace=True, ascending=False)
        total_time_m1_gurobi = results_m1_df.get("Time", pd.Series([0])).sum()
        results_m1_df.to_csv(os.path.join(results_dir, f"{csv_prefix}M1_{graph_basename}.csv"), index=False)
        
    elapsed_total_time = time.time() - total_time_start
    
    # ---------------- Summary File ----------------
    summary_path = os.path.join(results_dir, f"{csv_prefix}summary_{graph_basename}.txt")
    with open(summary_path, "w") as f:
        f.write("=========================================\n")
        f.write("      THREE-PHASE OPTIMIZATION SUMMARY\n")
        f.write("=========================================\n\n")

        f.write("GENERAL\n")
        f.write("-----------------------------------------\n")
        f.write(f"Total execution time      : {elapsed_total_time:.4f} seconds\n")
        f.write(f"Total points found        : {len(results_ws_df) + len(df_a) + len(df_d) + len(results_m1)}\n\n")

        f.write("PHASE 1 - WEIGHTED SUM (WS)\n")
        f.write("-----------------------------------------\n")
        f.write(f"Gurobi optimization time  : {total_time_ws_gurobi:.4f} seconds\n")
        f.write(f"Total WS phase time       : {ws_elapsed_time:.4f} seconds\n")
        f.write(f"Number of WS points found : {len(results_ws_df)}\n\n")

        f.write("PHASE 2 - LOCAL SEARCH HEURISTICS\n")
        f.write("-----------------------------------------\n")
        f.write(f"minD heuristic points : {len(df_d)}\n")
        f.write(f"maxD heuristic points : {len(df_a)}\n\n")

        f.write("PHASE 3 - EXACT SOLVER (M1 or M1+C-Flow)\n")
        f.write("-----------------------------------------\n")
        f.write(f"Gurobi optimization time  : {total_time_m1_gurobi:.4f} seconds\n")
        f.write(f"Number of M1 solutions    : {len(results_m1)}\n\n")

        f.write("=========================================\n")
