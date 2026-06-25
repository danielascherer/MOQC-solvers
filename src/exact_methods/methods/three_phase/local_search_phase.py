from __future__ import annotations

import networkx as nx
import pandas as pd
import random
import numpy as np

from core.ws_results import read_solution_ws
from core.solvers.solver_m1_and_m1_cflow import solve_model_m1_and_m1_cflow
from core.models.m1_c_flow import update_cflow_coefficients

def remove_v_with_min_degree_neighbour_tb(opt_temp: nx.Graph, connected: bool) -> tuple[nx.Graph, int | None, float | None]:
    degrees = dict(opt_temp.degree())
    
    if connected:
        articulation_points = set(nx.articulation_points(opt_temp))
    else:
        articulation_points = set()
        
    unique_degrees = sorted(set(degrees.values()))

    vertex_to_remove = None
    best_neighbour_degree = float('inf')
    max_neighbour_count = -1

    for deg in unique_degrees:
        candidates = [v for v, d in degrees.items() if d == deg and v not in articulation_points]
        if not candidates:
            continue
            
        if len(candidates) == 1:
            vertex_to_remove = candidates[0]
            neighbours = list(opt_temp.neighbors(vertex_to_remove))
            if neighbours:
                best_neighbour_degree = min([degrees[n] for n in neighbours])
            else:
                best_neighbour_degree = 0
            break
            
        for vertex in candidates:
            neighbours = list(opt_temp.neighbors(vertex))
            if not neighbours:
                continue

            neighbour_degrees = [degrees[n] for n in neighbours]
            min_neighbour_degree = min(neighbour_degrees)
            neighbours_with_min_degree = [n for n in neighbours if degrees[n] == min_neighbour_degree]
            
            if (min_neighbour_degree < best_neighbour_degree) or \
               (min_neighbour_degree == best_neighbour_degree and len(neighbours_with_min_degree) > max_neighbour_count):
                vertex_to_remove = vertex
                best_neighbour_degree = min_neighbour_degree
                max_neighbour_count = len(neighbours_with_min_degree)

        if vertex_to_remove is not None:
            break

    if vertex_to_remove is None:
        if not connected and opt_temp.number_of_nodes() > 0:
            vertex_to_remove = list(opt_temp.nodes())[0]
            best_neighbour_degree = 0
            opt_temp.remove_node(vertex_to_remove)
            return opt_temp, vertex_to_remove, best_neighbour_degree
        return opt_temp, None, None

    opt_temp.remove_node(vertex_to_remove)
    return opt_temp, vertex_to_remove, best_neighbour_degree

def add_max_degree_vertex(
    opt_temp_reverse: nx.Graph, optgraph: nx.Graph, degrees_zero: dict, degrees_graph: dict
) -> tuple[nx.Graph, int | None, int]:
    degrees = degrees_zero.copy()
    flag = 0    
    
    for vertex in opt_temp_reverse.nodes():
        for neighbor in optgraph.neighbors(vertex):
            if neighbor not in opt_temp_reverse.nodes():
                degrees[neighbor] += 1
                flag = 1
    
    if flag == 1:
        max_degree = max(degrees.values())
        max_degree_vertices = [v for v, d in degrees.items() if d == max_degree]
        
        if len(max_degree_vertices) > 1:
            list_max = [(v, degrees_graph[v]) for v in max_degree_vertices]
            max_degree_vertex = max(list_max, key=lambda x: x[1])[0]
        else:
            max_degree_vertex = max_degree_vertices[0]
            
        opt_temp_reverse.add_node(max_degree_vertex)
        for neighbor in optgraph.neighbors(max_degree_vertex):
            if neighbor in opt_temp_reverse.nodes():
                opt_temp_reverse.add_edge(max_degree_vertex, neighbor)
    else: # there is no node in the reverse subgraph that has a neighbor in the original graph
        return opt_temp_reverse, None, 0
            
    return opt_temp_reverse, max_degree_vertex, max_degree

def minD_LS(
    interval: int,
    point_b: tuple[int, int],
    slope_ab: float,
    subgraphs_list: list,
    opt_temp: nx.Graph,
    connected: bool,
    result_heuristic_d: list
) -> tuple[list, tuple]:

    """
    Min-Degree Local Search (Phase 2, destructive phase).

    This procedure iteratively removes vertices from a current solution (subgraph), following a minimum-degree strategy.

    At each step:
        1. A vertex with minimum degree is removed (using a tie-breaking rule 
           based on neighbors' degrees).
        2. A new solution (point = (#vertices, #edges)) is generated.
        3. The solution is evaluated using:
            - Clique condition (density = 1)
            - Degree-zero condition (special case for disconnected setting)
            - Slope-based dominance condition (comparison with segment AB)

    The goal is to:
        - Generate intermediate solutions between two extreme supported points A and B,
        - Identify solutions that can be *proved* (i.e., guaranteed to be weakly-efficient),
        - Collect "unproven" points that require further refinement.

    Outputs:
        - points_not_proved: list of candidate solutions that cannot be validated 
          by local conditions and must be further explored (or solved exactly).
        - clique: first clique found (if any), used to prune later exploration.

    Key ideas:
        - Works in a *descending* manner (reducing solution size).
        - Uses structural properties (degree, density) to avoid expensive exact solving.
        - Filters only promising points to pass to the next phase (max-degree LS or M1).

    Notes:
        - If 'connected=True', articulation points are avoided to preserve connectedness.
        - The slope condition ensures consistency with the Pareto frontier obtained in Phase 1.
    """
    points_not_proved = []
    clique = ()    
    for _ in range(interval - 1):  
        opt_temp, vertex_removed, degree_removed = remove_v_with_min_degree_neighbour_tb(opt_temp, connected)
        if vertex_removed is None:
            point = (opt_temp.number_of_nodes(), opt_temp.number_of_edges())
            points_not_proved.append((point[0], point[1], list(opt_temp.nodes())))
            continue
            
        point = (opt_temp.number_of_nodes(), opt_temp.number_of_edges())
        density = nx.density(opt_temp) if point[0] > 1 else 0.0
        solution = list(opt_temp.nodes())        
        
        if density >= 1.0:
            result_heuristic_d.append([point[0], point[1], vertex_removed, degree_removed, 'clique', nx.is_connected(opt_temp), solution]) 
            subgraphs_list[point[0]] = solution
            clique = point
            break
        else:  
            if not connected and degree_removed == 0 and point[0] + 1 < len(subgraphs_list) and subgraphs_list[point[0]+1] is not None:
                result_heuristic_d.append([point[0], point[1], vertex_removed, degree_removed, 'degreeZero', nx.is_connected(opt_temp), solution])                            
                subgraphs_list[point[0]] = solution
            else:                        
                improved_point = (point[0], point[1] + 1)
                slope_improved_point_b = (improved_point[1] - point_b[1]) / (improved_point[0] - point_b[0]) if (improved_point[0] - point_b[0]) != 0 else float('inf')
                
                if slope_improved_point_b > slope_ab:
                    result_heuristic_d.append([point[0], point[1], vertex_removed, degree_removed, 'aboveWsSegment', nx.is_connected(opt_temp), solution])                            
                    subgraphs_list[point[0]] = solution
                else: 
                    points_not_proved.append((point[0], point[1], solution))  
              
    return points_not_proved, clique

def _run_m1_for_k(
    k: int,
    m1_components: dict,
    connected: bool,
    optgraph: nx.Graph,
    graph_basename: str,
    log_dir: str,
    results_m1: list,
    subgraphs_list: list
) -> None:
    model = m1_components['model']
    x = m1_components['x']
    c1 = model.getConstrByName('C1')
    c1.RHS = k

    if connected:
        update_cflow_coefficients(
            model, optgraph, m1_components['y'], k,
            m1_components['c6_constrs'], m1_components['s_vars'],
            m1_components['c7_constrs'], m1_components['c8_constrs']
        )

    data_dict_m1 = solve_model_m1_and_m1_cflow(
        model, x, k, graph_basename, log_dir, optgraph,
        'M1_C-FLOW' if connected else 'M1'
    )

    results_m1.append(data_dict_m1)
    if data_dict_m1['NumberVertices'] != 0:
        subgraphs_list[data_dict_m1['NumberVertices']] = list(data_dict_m1['Solution'])


def maxD_LS(
    point_b: tuple[int, int],
    slope_ab: float,
    subgraphs_list: list,
    points_not_proved: list,
    clique: tuple,
    optgraph: nx.Graph,
    degrees_zero: dict,
    degrees_graph: dict,
    max_degree_val: int,
    results_ws_df: pd.DataFrame,
    result_heuristic_a: list,
    results_m1: list,
    m1_components: dict,
    connected: bool,
    log_dir: str,
    graph_basename: str
) -> None:

    """
    MaxDegree Local Search (Phase 2, constructive phase).

    This procedure complements minD_LS by exploring solutions in the *reverse direction*:
    starting from smaller subgraphs, it iteratively adds vertices to improve solutions.

    For each "unproven" point generated by minD_LS:
        1. A candidate solution is reconstructed.
        2. A vertex with maximum contribution (highest degree toward current solution)
           is added using a greedy strategy.
        3. The new solution is evaluated using:
            - Clique condition (density = 1)
            - Max-degree dominance condition
            - Slope-based dominance condition (relative to WS segment AB)

    If a solution cannot be validated by heuristic conditions:
        → An exact M1 (or M1_CFLOW) model is solved for the corresponding cardinality k.

    The goal is to:
        - Recover missed efficient solutions,
        - Improve heuristic solutions using constructive steps,
        - Guarantee completeness by invoking exact optimization when needed.

    Key ideas:
        - Works in an *ascending* manner (increasing solution size).
        - Uses greedy addition guided by degree to improve density.
        - Ensures correctness by falling back to exact methods (Phase 3).

    Important mechanisms:
        - Pruning based on previously found clique solutions.
        - Reuse of stored subgraphs (subgraphs_list) to avoid recomputation.
        - Adaptive switch between heuristic and exact solving depending on confidence.

    Outputs (updated in-place):
        - result_heuristic_a: list of validated solutions found by heuristic addition.
        - results_m1: list of solutions obtained via exact M1 solving.
        - subgraphs_list: updated repository of best-known solutions per size.

    Notes:
        - If 'connected=True', the M1 model uses flow constraints to enforce connectedness.
        - This phase ensures that no promising point (from Phase 2) is left unexplored.
    """
    if clique:
        points_not_proved = [p for p in points_not_proved if p[0] > clique[0]]
        
    for p in reversed(points_not_proved):
        keep_max_degree_sol = False
        solution = subgraphs_list[p[0] - 1]
        
        if solution is not None:
            opt_temp_reverse = nx.subgraph(optgraph, solution).copy()
        else:
            opt_temp_reverse = read_solution_ws(point_b, results_ws_df, optgraph)
            
        opt_temp_reverse, vertex_added, degree_added = add_max_degree_vertex(opt_temp_reverse, optgraph, degrees_zero, degrees_graph)
        
        if vertex_added is None:
            _run_m1_for_k(p[0], m1_components, connected, optgraph, graph_basename, log_dir, results_m1, subgraphs_list)
            continue
            
        point_reverse = (opt_temp_reverse.number_of_nodes(), opt_temp_reverse.number_of_edges())
        density = nx.density(opt_temp_reverse) if point_reverse[0] > 1 else 0.0
        
        if density >= 1.0:
            solution = list(opt_temp_reverse.nodes())
            result_heuristic_a.append([point_reverse[0], point_reverse[1], vertex_added, degree_added, 'clique', True, solution])
            subgraphs_list[point_reverse[0]] = solution
        else:
            if point_reverse[1] < p[1]:
                opt_temp_reverse = nx.subgraph(optgraph, p[2]).copy()
                keep_max_degree_sol = True
            elif point_reverse[1] == p[1]:
                keep_max_degree_sol = True

            if not keep_max_degree_sol:
                if degree_added == max_degree_val and subgraphs_list[point_reverse[0] - 1] is not None:
                    solution = list(opt_temp_reverse.nodes())
                    result_heuristic_a.append([point_reverse[0], point_reverse[1], vertex_added, degree_added, 'maxDegree', nx.is_connected(opt_temp_reverse), solution])
                    subgraphs_list[point_reverse[0]] = solution
                else:
                    improved_point = (point_reverse[0], point_reverse[1] + 1)
                    slope_improved_point_reverse_b = (improved_point[1] - point_b[1]) / (improved_point[0] - point_b[0]) if (improved_point[0] - point_b[0]) != 0 else float('inf')
                    
                    if slope_improved_point_reverse_b > slope_ab:
                        solution = list(opt_temp_reverse.nodes())
                        result_heuristic_a.append([point_reverse[0], point_reverse[1], vertex_added, degree_added, 'aboveWsSegment', nx.is_connected(opt_temp_reverse), solution])
                        subgraphs_list[point_reverse[0]] = solution
                    else:
                        p = (point_reverse[0], point_reverse[1], list(opt_temp_reverse.nodes()))
            
            # If not proved, run M1
            if subgraphs_list[p[0]] is None:
                _run_m1_for_k(p[0], m1_components, connected, optgraph, graph_basename, log_dir, results_m1, subgraphs_list)
            '''   
                k = p[0]
                model = m1_components['model']
                x = m1_components['x']
                c1 = model.getConstrByName('C1')
                c1.RHS = k
                
                if connected:
                    update_cflow_coefficients(
                        model, optgraph, m1_components['y'], k,
                        m1_components['c6_constrs'], m1_components['s_vars'],
                        m1_components['c7_constrs'], m1_components['c8_constrs']
                    )
                
                data_dict_m1 = solve_model_m1_and_m1_cflow(model, x, k, graph_basename, log_dir, optgraph, 'M1_C-FLOW' if connected else 'M1')
                
                if data_dict_m1['NumberVertices'] != 0:
                    results_m1.append(data_dict_m1)
                    subgraphs_list[data_dict_m1['NumberVertices']] = list(data_dict_m1['Solution'])
                else:
                    results_m1.append(data_dict_m1)
            '''


def explore_weakly_efficient_solutions(
    points: np.ndarray,
    v: int,
    e: int,
    max_degree_val: int,
    optgraph: nx.Graph,
    degrees_zero: dict,
    degrees_graph: dict,
    results_ws_df: pd.DataFrame,
    m1_components: dict,
    connected: bool,
    log_dir: str,
    graph_basename: str
) -> tuple[pd.DataFrame, pd.DataFrame, list]:

    """
    Phase 2: Hybrid local search for weakly efficient solutions.

    This function orchestrates the exploration of intermediate solutions between
    consecutive extreme supported points obtained in Phase 1 (Weighted Sum).

    For each pair of adjacent WS solutions (A, B):
        1. A *destructive search* (minD_LS) is applied:
            - Iteratively removes minimum-degree vertices.
            - Generates candidate subgraphs with decreasing cardinality.
            - Uses structural conditions (density, slope) to detect weakly efficient points.
            - Returns a set of "unproven" points that require further validation.

        2. A *constructive search* (maxD_LS) is applied:
            - Starts from smaller solutions and incrementally adds vertices.
            - Uses maximum-degree criteria to improve density.
            - Attempts to validate remaining candidate points.

        3. Exact refinement (Phase 3 - M1 model):
            - For any point that cannot be validated by local conditions,
              an exact optimization model is solved to guarantee correctness.

    
    Inputs:
        points: WS solutions sorted by decreasing number of vertices.
        v, e: number of vertices and edges of the graph.
        max_degree_val: maximum degree in the original graph.
        optgraph: original graph.
        degrees_zero, degrees_graph: auxiliary degree structures.
        results_ws_df: WS solution set (Phase 1 output).
        m1_components: pre-built exact model components.
        connected: whether connectedness is required.
        log_dir, graph_basename: logging utilities.

    Outputs:
        df_a: solutions found by the max-degree (constructive) heuristic.
        df_d: solutions found by the min-degree (destructive) heuristic.
        results_m1: solutions obtained through exact M1 solving.

    """
    subgraphs_list = [None] * (v + 1)
    
    result_heuristic_d = []
    result_heuristic_a = []
    results_m1 = []

    for i in range(len(points) - 1):
        point_a = points[i]
        point_b = points[i + 1]
        
        slope_ab = (point_a[1] - point_b[1]) / (point_a[0] - point_b[0]) if (point_a[0] - point_b[0]) != 0 else float('inf')
        
        if point_a[0] == v and point_a[1] == e:
            if connected:
                largest_component = max(nx.connected_components(optgraph), key=len)
                opt_temp = optgraph.subgraph(largest_component).copy()
            else:
                opt_temp = optgraph.copy()
        else:
            opt_temp = read_solution_ws(point_a, results_ws_df, optgraph)
            if not opt_temp: continue
            density = nx.density(opt_temp) if opt_temp.number_of_nodes() > 1 else 0.0
            if density >= 1.0:
                break 
        
        interval = point_a[0] - point_b[0]
        
        points_not_proved, clique = minD_LS(
            interval, point_b, slope_ab, subgraphs_list, opt_temp, connected, result_heuristic_d
        )
        
        if points_not_proved:
            maxD_LS(
                point_b, slope_ab, subgraphs_list, points_not_proved, clique,
                optgraph, degrees_zero, degrees_graph, max_degree_val,
                results_ws_df, result_heuristic_a, results_m1, m1_components,
                connected, log_dir, graph_basename
            )
            
        subgraphs_list = [None] * (v + 1)

    cols = ['NumberVertices', 'NumberEdges', 'VertexRemovedAdded', 'DegreeVertexRemovedAdded', 'SufficientCondition', 'is_Connected', 'Solution']
    
    df_d = pd.DataFrame(result_heuristic_d, columns=cols)
    df_a = pd.DataFrame(result_heuristic_a, columns=cols)

    return df_a, df_d, results_m1
