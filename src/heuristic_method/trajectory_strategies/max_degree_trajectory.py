from __future__ import annotations

import networkx as nx
import random

def max_degree_trajectory(
    pointA: tuple,
    pointB: tuple,
    slopeAB: float,
    max_degree_val: int,
    initial_solution: list,
    guiding_solution: list,
    graph: nx.Graph,
    results: list
):
    """
    Path Relinking trajectory (constructive direction).
    Adds vertices from guiding solution into initial solution.
    """

    points_not_proved = []

    initial_nodes = list(initial_solution)
    guiding_nodes = set(guiding_solution)

    candidates = list(guiding_nodes - set(initial_nodes))

    current_graph = graph.subgraph(initial_nodes).copy()

    while len(candidates) > 1:

        # --- select max degree wrt current solution ---
        current_nodes_set = set(current_graph.nodes())

        best_vertex = None
        best_degree = -1
        best_index = 0

        for idx, v in enumerate(candidates):
            degree = sum(1 for n in graph.neighbors(v) if n in current_nodes_set)

            if degree > best_degree:
                best_degree = degree
                best_vertex = v
                best_index = idx

        if best_degree == 0:
            best_index = random.randint(0, len(candidates) - 1)
            best_vertex = candidates[best_index]

        # move vertex
        candidates[best_index], candidates[-1] = candidates[-1], candidates[best_index]
        candidates.pop()

        # add vertex
        current_graph.add_node(best_vertex)

        for n in graph.neighbors(best_vertex):
            if n in current_graph:
                current_graph.add_edge(best_vertex, n)

        k = current_graph.number_of_nodes()
        edges = current_graph.number_of_edges()

        solution = list(current_graph.nodes())
        
        # --- evaluate ---
        projected_number_of_edges = int(pointA[1] + slopeAB * (k - pointA[0]))
        maximum_number_of_edges = (k*(k-1))/2
        if projected_number_of_edges > maximum_number_of_edges:
            projected_number_of_edges = maximum_number_of_edges

        if not results[k]["is_weakly_efficient"] and edges > results[k]["number_of_edges"]:

            if nx.density(current_graph) >= 1.0:
                results[k] = {
                    "is_weakly_efficient": True,
                    "phase": "PR",
                    "method": "max_degree",
                    "number_of_vertices": k,
                    "number_of_edges": edges,
                    "vertex_added_or_removed": best_vertex,
                    "degree_of_added_removed_vertex": best_degree,
                    "type": "clique",
                    "upper_bound": projected_number_of_edges,
                    "solution": solution,
                    "is_connected": nx.is_connected(current_graph)
                }

            elif best_degree == max_degree_val and results[k - 1]["is_weakly_efficient"]:
                results[k] = {
                    "is_weakly_efficient": True,
                    "phase": "PR",
                    "method": "max_degree",
                    "number_of_vertices": k,
                    "number_of_edges": edges,
                    "vertex_added_or_removed": best_vertex,
                    "degree_of_added_removed_vertex": best_degree,
                    "type": "maxDegree",
                    "upper_bound": projected_number_of_edges,
                    "solution": solution,
                    "is_connected": nx.is_connected(current_graph)
                }

            else:
                improved_point = (k, edges + 1)
                if improved_point[1] > pointB[1] + slopeAB * (improved_point[0] - pointB[0]):
                    results[k] = {
                        "is_weakly_efficient": True,
                        "phase": "PR",
                        "method": "max_degree",
                        "number_of_vertices": k,
                        "number_of_edges": edges,
                        "vertex_added_or_removed": best_vertex,
                        "degree_of_added_removed_vertex": best_degree,
                        "type": "aboveWsSegment",
                        "upper_bound": projected_number_of_edges,
                        "solution": solution,
                        "is_connected": nx.is_connected(current_graph)
                    }

                else:
                    results[k] = {
                        "is_weakly_efficient": False,
                        "phase": "PR",
                        "method": "max_degree",
                        "number_of_vertices": k,
                        "number_of_edges": edges,
                        "vertex_added_or_removed": best_vertex,
                        "degree_of_added_removed_vertex": best_degree,
                        "type": "notProven",
                        "upper_bound": projected_number_of_edges,
                        "solution": solution,
                        "is_connected": nx.is_connected(current_graph)
                    }
                    points_not_proved.append(k)

        else:
            if not results[k]["is_weakly_efficient"]:
                points_not_proved.append(k)

    return points_not_proved