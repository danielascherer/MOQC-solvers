from __future__ import annotations

import networkx as nx

from exact_methods.methods.three_phase.local_search_phase import (
    add_max_degree_vertex
)


def max_degree_local_search(
    pointA: tuple,
    pointB: tuple,
    slopeAB: float,
    max_degree_val: int,
    points_not_proved: list[int],
    graph: nx.Graph,
    results: list,
    degrees_zero: dict,
    degrees_graph: dict
) -> None:
    """
    Local search (constructive phase).

    Starting from solutions of size k-1, this procedure tries to build
    better solutions of size k by adding a vertex with maximum contribution.

    Updates 'results' in place.
    """

    for k in reversed(points_not_proved):

        # --- Get solution of size k-1 ---
        prev_solution = results[k - 1]["solution"]
        subgraph = nx.subgraph(graph, prev_solution).copy()
        
        # --- Add vertex ---
        subgraph, vertex_added, degree_added = add_max_degree_vertex(
            subgraph, graph, degrees_zero, degrees_graph
        )

        if vertex_added is None:
            continue

        new_k = subgraph.number_of_nodes()
        edges = subgraph.number_of_edges()

        solution = list(subgraph.nodes())
        
        # Project the number of edges based on the slope from pointA to the current point
        projected_number_of_edges = int(pointA[1] + slopeAB * (new_k - pointA[0]))
        maximum_number_of_edges = (new_k * (new_k - 1)) / 2
        if projected_number_of_edges > maximum_number_of_edges:
            projected_number_of_edges = int(maximum_number_of_edges)
        
        # --- Improvement condition ---
        if edges > results[new_k]["number_of_edges"]:

            # Clique found
            if nx.density(subgraph) >= 1.0:
                results[new_k] = {
                    "is_weakly_efficient": True,
                    "phase": "LS",
                    "method": "max_degree",
                    "number_of_vertices": new_k,
                    "number_of_edges": edges,
                    "vertex_added_or_removed": vertex_added,
                    "degree_of_added_removed_vertex": degree_added,
                    "type": "clique",
                    "upper_bound": projected_number_of_edges,
                    "solution": solution,
                    "is_connected": nx.is_connected(subgraph)
                }

            # Max-degree improvement condition
            elif degree_added == max_degree_val and results[new_k - 1]["is_weakly_efficient"]:
                results[new_k] = {
                    "is_weakly_efficient": True,
                    "phase": "LS",
                    "method": "max_degree",
                    "number_of_vertices": new_k,
                    "number_of_edges": edges,
                    "vertex_added_or_removed": vertex_added,
                    "degree_of_added_removed_vertex": degree_added,
                    "type": "maxDegree",
                    "upper_bound": projected_number_of_edges,
                    "solution": solution,
                    "is_connected": nx.is_connected(subgraph)
                }

            # segment-based condition
            else:
                improved_point = (new_k, edges + 1)

                if (improved_point[1] > pointB[1] + slopeAB * (improved_point[0] - pointB[0])):
                    results[new_k] = {
                        "is_weakly_efficient": True,
                        "phase": "LS",
                        "method": "max_degree",
                        "number_of_vertices": new_k,
                        "number_of_edges": edges,
                        "vertex_added_or_removed": vertex_added,
                        "degree_of_added_removed_vertex": degree_added,
                        "type": "aboveWsSegment",
                        "upper_bound": projected_number_of_edges,
                        "solution": solution,
                        "is_connected": nx.is_connected(subgraph)
                    }
                else:
                    # Not proven 
                    results[new_k] = {
                        "is_weakly_efficient": False,
                        "phase": "LS",
                        "method": "max_degree",
                        "number_of_vertices": new_k,
                        "number_of_edges": edges,
                        "vertex_added_or_removed": vertex_added,
                        "degree_of_added_removed_vertex": degree_added,
                        "type": "notProven",
                        "upper_bound": projected_number_of_edges,
                        "solution": solution,
                        "is_connected": nx.is_connected(subgraph)
                    }                