from __future__ import annotations

import networkx as nx

def min_degree_trajectory(
    pointA: tuple,
    pointB: tuple,
    slopeAB: float,
    initial_solution: list,
    guiding_solution: list,
    connected: bool,
    graph: nx.Graph,
    results: list
):
    """
    Path Relinking trajectory (destructive direction).
    Removes vertices from guiding solution toward initial solution.
    """

    points_not_proved = []
    clique = None

    guiding_nodes = list(guiding_solution)
    initial_nodes = set(initial_solution)

    # Nodes that must be removed
    candidates = list(set(guiding_nodes) - initial_nodes)

    current_graph = nx.subgraph(graph,guiding_nodes).copy()
    k = current_graph.number_of_nodes() 
    while len(candidates) > 1:
        # --- select min-degree vertex ---
        degrees = dict(current_graph.degree())

        if connected:
            articulation = set(nx.articulation_points(current_graph))
            valid_nodes = [v for v in candidates if v not in articulation]
            # If all candidates are articulation nodes, we can't continue with this trajectory
            if not valid_nodes:
                for i in range(1, k-len(initial_nodes)):
                    results[k-i] = {
                        "is_weakly_efficient": False,
                        "phase": "PR",
                        "method": "min_degree",
                        "number_of_vertices": k-i,
                        "number_of_edges": 0,
                        "vertex_added_or_removed": None,
                        "degree_of_added_removed_vertex": None,
                        "type": "notProven",
                        "upper_bound": None,
                        "solution": None,
                        "is_connected": None
                    }
                    points_not_proved.append(k-i)
                break
        else:
            valid_nodes = candidates

        selected = min(valid_nodes, key=lambda v: degrees[v])
        degree_removed = degrees[selected]

        # remove
        current_graph.remove_node(selected)
        candidates.remove(selected)

        k = current_graph.number_of_nodes()
        edges = current_graph.number_of_edges()

        solution = list(current_graph.nodes())
        
        # --- evaluate ---
        projected_number_of_edges = int(pointA[1] + slopeAB * (k - pointA[0]))
        maximum_number_of_edges = (k * (k - 1)) / 2
        if projected_number_of_edges > maximum_number_of_edges:
            projected_number_of_edges = maximum_number_of_edges

        if nx.density(current_graph) >= 1.0:
            results[k] = {
                "is_weakly_efficient": True,
                "phase": "PR",
                "method": "min_degree",
                "number_of_vertices": k,
                "number_of_edges": edges,
                "vertex_added_or_removed": selected,
                "degree_of_added_removed_vertex": degree_removed,
                "type": "clique",
                "upper_bound": projected_number_of_edges,
                "solution": solution,
                "is_connected": nx.is_connected(current_graph)
            }
            clique = (k, edges, set(solution))
            break

        else:
            improved_point = (k, edges+1)
            if improved_point[1] > pointB[1] + slopeAB * (improved_point[0] - pointB[0]):
                results[k] = {
                    "is_weakly_efficient": True,
                    "phase": "PR",
                    "method": "min_degree",
                    "number_of_vertices": k,
                    "number_of_edges": edges,
                    "vertex_added_or_removed": selected,
                    "degree_of_added_removed_vertex": degree_removed,
                    "type": "aboveWsSegment",
                    "upper_bound": projected_number_of_edges,
                    "solution": solution,
                    "is_connected": nx.is_connected(current_graph)
                }
            else:
                results[k] = {
                    "is_weakly_efficient": False,
                    "phase": "PR",
                    "method": "min_degree",
                    "number_of_vertices": k,
                    "number_of_edges": edges,
                    "vertex_added_or_removed": selected,
                    "degree_of_added_removed_vertex": degree_removed,
                    "type": "notProven",
                    "upper_bound": projected_number_of_edges,
                    "solution": solution,
                    "is_connected": nx.is_connected(current_graph)
                }
                points_not_proved.append(k)
    
    return points_not_proved, clique