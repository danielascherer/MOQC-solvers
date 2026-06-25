from __future__ import annotations

import os
import time
import gurobipy as gp
from gurobipy import GRB
import pandas as pd
import numpy as np
import networkx as nx

from core.utils import BASE_LOG_DIR, BASE_RESULTS_DIR, TIME_LIMIT
from core.graph_utils import read_graph
from core.models.m1 import build_m1_model
from core.models.m1_c_flow import build_m1_cflow_model, update_cflow_coefficients, build_cflow_cache
from core.solvers.solver_m1_and_m1_cflow import solve_model_m1_and_m1_cflow


def run_e_dks(graph_path: str, connected: bool) -> None:
    """Run the epsilon-constraint DKS procedure on a graph file.

    Iterates k from |V| (or |LCC| in connected mode) down to 2, solving the
    chosen formulation at each step and stopping as soon as a clique
    (density == 1) is reached. Results are written to a CSV and a summary
    text file.

    Args:
        graph_path: Path to the graph file.
        connected: If True, use M1-C-Flow to enforce connected solutions.
            The search is restricted to the largest connected component when
            the input graph is disconnected.
    """

    total_time_start = time.time()
    
    method_name = "edks"

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

    results: list[dict] = []

    # --- Read graph ---
    graph, num_vertices, num_edges, _, _ = read_graph(graph_path)
    graph_basename = os.path.basename(graph_path)
    lcc_graph = graph

    # Find the size of the largest connected component to set the initial k and starting stats.
    # The solver will still use the entire original graph.
    components = list(nx.connected_components(graph))
    if len(components) > 1:
        largest_cc = max(components, key=len)
        lcc_graph = graph.subgraph(largest_cc)
        num_vertices = lcc_graph.number_of_nodes()
        num_edges = lcc_graph.number_of_edges()

    density = nx.density(lcc_graph) if num_vertices > 1 else 0.0
    # Record full-graph (or LCC) statistics as the first data point.
    first_row: dict = {
        "NumberVertices": num_vertices,
        "NumberEdges": num_edges,
        "Density": density,
        "Status": "OPTIMAL",
        "Time": 0.0,
        "is_Connected": nx.is_connected(lcc_graph) if connected else nx.is_connected(graph),
        "Solution": list(lcc_graph.nodes())        
    }
    results.append(first_row)
    
    time_limit: float | None = TIME_LIMIT

    # --- Build model once; update constraints in each iteration ---
    k = num_vertices
    if connected:        
        model, x, y, c1, c6_constrs, s_vars, c7_constrs, c8_constrs = build_m1_cflow_model(graph)
        # Cache all constraint/variable references before the loop so each
        # iteration avoids O(|V| + |E|) Gurobi name lookups.
        c6_constrs, s_vars, c7_constrs, c8_constrs = build_cflow_cache(model, graph, y)
    else:
        model, x, y, c1 = build_m1_model(graph)
    

    while density < 1:
        k -= 1

        # Update the cardinality constraint RHS for the new k.
        c1.RHS = k
        model.update()

        # In connected mode, C6/C7/C8 contain k-dependent coefficients.
        if connected:
            update_cflow_coefficients(
                model, graph, y, k,
                c6_constrs, s_vars, c7_constrs, c8_constrs,
            )

        result_dict = solve_model_m1_and_m1_cflow(
            model, 
            x, 
            k, 
            graph_basename, 
            log_dir, 
            graph, 
            "M1_C-FLOW" if connected else "M1"
        )
        results.append(result_dict)

        density = result_dict["Density"]  

    elapsed_time = time.time() - total_time_start

    # --- Persist results ---
    os.makedirs(results_dir, exist_ok=True)

    results_df = pd.DataFrame(results)
    results_df.sort_values(by=["NumberVertices"], ascending=False, inplace=True)

    total_gurobi_time = results_df["Time"].sum()
    
    csv_prefix = "e_dks_connectedness_" if connected else "e_dks_"
    csv_path = os.path.join(results_dir, f"{csv_prefix}{graph_basename}.csv")
    summary_path = os.path.join(results_dir, f"{csv_prefix}summary_{graph_basename}.txt")

    results_df.to_csv(csv_path)

    with open(summary_path, "w") as f:
        f.write("=========================================\n")
        f.write("       E-DKS OPTIMIZATION SUMMARY\n")
        f.write("=========================================\n\n")

        f.write("GENERAL\n")
        f.write("-----------------------------------------\n")
        f.write(f"Total execution time      : {elapsed_time:.4f} seconds\n")
        f.write(f"Gurobi optimization time  : {total_gurobi_time:.4f} seconds\n")
        f.write(f"Total points found        : {len(results)} \n\n")
