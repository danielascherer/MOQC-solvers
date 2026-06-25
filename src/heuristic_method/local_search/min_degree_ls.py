from __future__ import annotations

import networkx as nx

from exact_methods.methods.three_phase.local_search_phase import (
    remove_v_with_min_degree_neighbour_tb
)


def min_degree_local_search(
    pointA: tuple,
    pointB: tuple,
    slopeAB: float,
    points_not_proved: list[int],
    connected: bool,
    graph: nx.Graph,
    results: list
) -> list[int]:
    """
    Local search (destructive): removes vertices from candidate solutions.
    """

    new_points_not_proved = []

    for k in reversed(points_not_proved):

        # Previous solution (k+1)
        solution = results[k + 1]["solution"]
        subgraph_temp = nx.subgraph(graph,solution).copy()

        # Apply removal
        subgraph_temp, vertex_removed, degree_removed = \
            remove_v_with_min_degree_neighbour_tb(subgraph_temp, connected)

        if vertex_removed is None:
            new_points_not_proved.append(k)
            continue

        new_k = subgraph_temp.number_of_nodes()
        edges = subgraph_temp.number_of_edges()

        solution = list(subgraph_temp.nodes())
        
        # Calculate an upper bound on the number of edges based on the slope
        projected_number_of_edges = int(pointA[1] + slopeAB * (new_k - pointA[0]))
        maximum_number_of_edges = (new_k*(new_k-1))/2
        if projected_number_of_edges > maximum_number_of_edges:
            projected_number_of_edges = maximum_number_of_edges
        

        if edges > results[new_k]["number_of_edges"]:

            if nx.density(subgraph_temp) >= 1.0:
                results[new_k] = {
                    "is_weakly_efficient": True,
                    "phase": "LS",
                    "method": "min_degree",
                    "number_of_vertices": new_k,
                    "number_of_edges": edges,
                    "vertex_added_or_removed": vertex_removed,
                    "degree_of_added_removed_vertex": degree_removed,
                    "type": "clique",
                    "upper_bound": projected_number_of_edges,
                    "solution": solution,
                    "is_connected": nx.is_connected(subgraph_temp)
                }

            else:
                improved_point = (new_k, edges + 1)
                if improved_point[1] > pointB[1] + slopeAB * (improved_point[0] - pointB[0]):
                    results[new_k] = {
                    "is_weakly_efficient": True,
                    "phase": "LS",
                    "method": "min_degree",
                    "number_of_vertices": new_k,
                    "number_of_edges": edges,
                    "vertex_added_or_removed": vertex_removed,
                    "degree_of_added_removed_vertex": degree_removed,
                    "type": "aboveWsSegment",
                    "upper_bound": projected_number_of_edges,
                    "solution": solution,
                    "is_connected": nx.is_connected(subgraph_temp)
                    }
                else:
                    results[new_k] = {
                    "is_weakly_efficient": False,
                    "phase": "LS",
                    "method": "min_degree",
                    "number_of_vertices": new_k,
                    "number_of_edges": edges,
                    "vertex_added_or_removed": vertex_removed,
                    "degree_of_added_removed_vertex": degree_removed,
                    "type": "notProven",
                    "upper_bound": projected_number_of_edges,
                    "solution": solution,
                    "is_connected": nx.is_connected(subgraph_temp)
                    }
                    new_points_not_proved.append(new_k)

        else:
            new_points_not_proved.append(k)

    return new_points_not_proved