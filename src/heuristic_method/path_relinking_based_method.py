from __future__ import annotations

import pandas as pd
import networkx as nx
import sys
import time
import os
import numpy as np

from core.graph_utils import read_graph
from core.models.ws import build_ws_model
from core.dichotomic_search import dichotomic_search
from core.utils import BASE_LOG_DIR, BASE_RESULTS_DIR

from heuristic_method.path_relinking_phase import run_path_relinking_phase


def run_path_relinking_based_method(
    graph_file: str,
    run_number: int,
    connected: bool
) -> None:

    total_start = time.time()

    # =========================
    # READ GRAPH
    # =========================
    graph, num_vertices, num_edges, degrees_graph, degrees_zero = read_graph(graph_file)
    lcc_graph = graph

    if graph.number_of_nodes() == 0:
        print("Warning: The graph is empty. Exiting.")
        sys.exit(1)

    max_degree_vertex = max(graph.degree, key=lambda x: x[1])
    #best_solution_nodes = set(graph.nodes())

    if connected:
        components = list(nx.connected_components(graph))
        if len(components) > 1:
            largest_component = max(components, key=len)
            lcc_graph = graph.subgraph(largest_component).copy()
            num_vertices = lcc_graph.number_of_nodes()
            num_edges = lcc_graph.number_of_edges()
    best_solution_nodes = set(lcc_graph.nodes())

    # =========================
    # INITIALIZE RESULTS
    # =========================
    results = [
        {
            "is_weakly_efficient": False,
            "phase": "",
            "method": "",
            "number_of_vertices": k,
            "number_of_edges": 0,
            "vertex_added_or_removed": None,
            "degree_of_added_removed_vertex": None,
            "type": "",
            "upper_bound": None,
            "is_connected": None,
            "solution": []
        }
        for k in range(num_vertices + 1)
    ]
    results[0] = {
        "is_weakly_efficient": True,
        "phase": "WS",
        "method": "endpoint",
        "number_of_vertices": 0,
        "number_of_edges": 0,
        "solution": [],
        "is_connected": True
    }

    
    results[num_vertices] = {
        "is_weakly_efficient": True,
        "phase": "WS",
        "method": "endpoint",
        "number_of_vertices": num_vertices,
        "number_of_edges": num_edges,
        "solution": list(best_solution_nodes),
        "is_connected": True
    }

    graph_name = os.path.basename(graph_file)

    method_name = "path_relinking"
    log_dir = os.path.join(BASE_LOG_DIR, f"{method_name}_{'connected' if connected else 'plain'}")
    results_dir = os.path.join(BASE_RESULTS_DIR, f"{method_name}_{'connected' if connected else 'plain'}")

    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)

    # =========================
    # WS PHASE
    # =========================
    ws_start = time.time()

    base_model, x, y = build_ws_model(graph, connected)

    results_ws = []
    dichotomic_search(
        0, 0, num_vertices, num_edges,
        base_model, graph, x, y,
        graph_name, results_ws, log_dir, connected
    )

    ws_elapsed = time.time() - ws_start

    df_ws = pd.DataFrame(results_ws)

    if df_ws.empty:
        df_ws = pd.DataFrame(columns=[
            "Status", "NumberEdges", "NumberVertices", "Density", "Obj"
            "Time", "Solution", "is_Connected"
        ])

    # Add endpoints
    df_ws = pd.concat([
        df_ws,
        pd.DataFrame([
            {"Status": "OPTIMAL", "NumberVertices": num_vertices, "NumberEdges": num_edges, "Density":nx.density(lcc_graph),"Time": 0.0, "is_connected": nx.is_connected(lcc_graph), "Solution": list(best_solution_nodes)},
            {"Status": "OPTIMAL", "NumberVertices": 0, "NumberEdges": 0, "Density": 0.0, "is_connected": True, "Time": 0.0, "Solution": []}
        ])
    ], ignore_index=True)

    df_ws.sort_values(by="NumberVertices", ascending=False, inplace=True)

    total_ws_gurobi_time = df_ws["Time"].sum()

    # Fill results structure
    for _, row in df_ws.iterrows():
        k = int(row["NumberVertices"])
        edges = int(row["NumberEdges"])
        sol = list(row["Solution"])

        if not results[k]["is_weakly_efficient"]:
            results[k] = {
                "is_weakly_efficient": True,
                "phase": "WS",
                "method": "ws_solution",
                "number_of_vertices": k,
                "number_of_edges": edges,
                "solution": sol,
                "is_connected": nx.is_connected(graph.subgraph(sol)) if k > 0 else True
            }

    # =========================
    # PR + LS PHASE
    # =========================
    if len(df_ws) <= 2:
        print("Graph has only two extreme points. Heuristic not applied.")
        sys.exit(1)

    extreme_points = list(zip(
        df_ws["NumberVertices"],
        df_ws["NumberEdges"],
        df_ws["Solution"]
    ))
    extreme_points = np.array(extreme_points, dtype=object)

    heu_start = time.time()

    pr_max_time, pr_min_time, ls_min_time, ls_max_time = run_path_relinking_phase(
        extreme_points,
        max_degree_vertex[1],
        connected,
        graph,
        results,
        degrees_zero,
        degrees_graph
    )

    heu_elapsed = time.time() - heu_start
    total_elapsed = time.time() - total_start

    # =========================
    # SAVE RESULTS
    # =========================
    columns = [
        "is_weakly_efficient",
        "phase",
        "method",
        "number_of_vertices",
        "number_of_edges",
        "vertex_added_or_removed",
        "degree_of_added_removed_vertex",
        "type",
        "upper_bound",
        "is_connected",
        "solution"
    ]

    df_results = pd.DataFrame(results)
    df_results = df_results[
        df_results["is_connected"].notna()
    ]
    df_results.sort_values(by="number_of_vertices", inplace=True)

    con_str = "connected_" if connected else ""

    df_ws.to_csv(os.path.join(results_dir, f"WS_{con_str}{graph_name}_{run_number}.csv"), index=False)
    df_results.to_csv(os.path.join(results_dir, f"results_{con_str}{graph_name}_{run_number}.csv"), index=False)

    # =========================
    # SUMMARY
    # =========================
    num_pr_max = ((df_results["phase"] == "PR") & (df_results["method"] == "max_degree")).sum()
    num_pr_min = ((df_results["phase"] == "PR") & (df_results["method"] == "min_degree")).sum()
    num_ls_max = ((df_results["phase"] == "LS") & (df_results["method"] == "max_degree")).sum()
    num_ls_min = ((df_results["phase"] == "LS") & (df_results["method"] == "min_degree")).sum()

    summary_file = os.path.join(results_dir, f"summary_{con_str}{graph_name}_{run_number}.txt")
    
    with open(summary_file, "w") as f:
        f.write("=========================================\n")
        f.write("     PATH RELINKING HEURISTIC SUMMARY\n")
        f.write("=========================================\n\n")

        # -------------------------
        # GENERAL
        # -------------------------
        f.write("GENERAL\n")
        f.write("-----------------------------------------\n")
        f.write(f"Total execution time        : {total_elapsed:.4f} seconds\n")
        f.write(f"Total points found          : {len(df_results)}\n\n")

        # -------------------------
        # PHASE 1 - WS
        # -------------------------
        f.write("PHASE 1 - WEIGHTED SUM (WS)\n")
        f.write("-----------------------------------------\n")
        f.write(f"Gurobi optimization time    : {total_ws_gurobi_time:.4f} seconds\n")
        f.write(f"Total WS phase time         : {ws_elapsed:.4f} seconds\n")
        f.write(f"Number of WS points found   : {len(df_ws)}\n\n")

        # -------------------------
        # PHASE 2 - PATH RELINKING
        # -------------------------
        f.write("PHASE 2 - PATH RELINKING (TRAJECTORY STRATEGIES)\n")
        f.write("-----------------------------------------\n")
        f.write(f"Min-degree trajectory time  : {pr_min_time:.4f} seconds\n")
        f.write(f"Max-degree trajectory time  : {pr_max_time:.4f} seconds\n")
        f.write(f"PR min-degree points        : {num_pr_min}\n")
        f.write(f"PR max-degree points        : {num_pr_max}\n\n")

        # -------------------------
        # PHASE 3 - LOCAL SEARCH
        # -------------------------
        f.write("PHASE 3 - LOCAL SEARCH (REFINEMENT)\n")
        f.write("-----------------------------------------\n")
        f.write(f"Min-degree LS time          : {ls_min_time:.4f} seconds\n")
        f.write(f"Max-degree LS time          : {ls_max_time:.4f} seconds\n")
        f.write(f"LS min-degree points        : {num_ls_min}\n")
        f.write(f"LS max-degree points        : {num_ls_max}\n\n")

        # -------------------------
        # HEURISTIC TOTAL
        # -------------------------
        f.write("HEURISTIC TOTAL\n")
        f.write("-----------------------------------------\n")
        f.write(f"Total heuristic time        : {heu_elapsed:.4f} seconds\n\n")

        f.write("=========================================\n")
    print("Path relinking heuristic completed.")