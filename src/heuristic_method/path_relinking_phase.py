from __future__ import annotations

import time
import networkx as nx

from heuristic_method.trajectory_strategies.min_degree_trajectory import min_degree_trajectory
from heuristic_method.trajectory_strategies.max_degree_trajectory import max_degree_trajectory
from heuristic_method.local_search.min_degree_ls import min_degree_local_search
from heuristic_method.local_search.max_degree_ls import max_degree_local_search


def run_path_relinking_phase(
    extreme_points: list,
    max_degree: int,
    connected: bool,
    graph: nx.Graph,
    results: list,
    degrees_zero: dict,
    degrees_graph: dict
) -> tuple[float, float, float, float]:

    # Timing
    pr_min_time = 0.0
    pr_max_time = 0.0
    ls_min_time = 0.0
    ls_max_time = 0.0

    for i in range(len(extreme_points) - 1):

        # --- Points ---
        pointA = extreme_points[i]
        pointB = extreme_points[i + 1]

        slopeAB = (
            (pointA[1] - pointB[1]) / (pointA[0] - pointB[0])
            if pointA[0] != pointB[0]
            else float("inf")
        )

        # --- Solutions ---
        initialP = pointB
        guidingP = pointA

        initial_solution = initialP[2]
        guiding_solution = guidingP[2]

        # =======================
        # PATH RELINKING (trajectory strategies)
        # =======================
        is_nested = set(initial_solution).issubset(set(guiding_solution)) or set(guiding_solution).issubset(set(initial_solution))

        if not connected or is_nested:
            t0 = time.time()

            points_np, clique = min_degree_trajectory(
                pointA, pointB, slopeAB,
                initial_solution,
                guiding_solution,
                connected,
                graph,
                results
            )

            pr_min_time += time.time() - t0

            if points_np:
                if clique:
                    initial_solution = list(clique[2])

                t0 = time.time()

                points_np = max_degree_trajectory(
                    pointA, pointB, slopeAB,
                    max_degree,
                    initial_solution,
                    guiding_solution,
                    graph,
                    results
                )

                pr_max_time += time.time() - t0
        else:
            min_k = min(pointA[0], pointB[0])
            max_k = max(pointA[0], pointB[0])
            points_np = list(range(min_k + 1, max_k))

        if not points_np:
            continue

        # =======================
        # LOCAL SEARCH (min degree local search strategy)
        # =======================
        t0 = time.time()

        points_np = min_degree_local_search(
            pointA, pointB, slopeAB,
            points_np,
            connected,
            graph,
            results
        )

        ls_min_time += time.time() - t0

        if not points_np:
            continue

        # =======================
        # LOCAL SEARCH (max degree local search strategy)
        # =======================
        t0 = time.time()

        max_degree_local_search(
            pointA, pointB, slopeAB,
            max_degree,
            points_np,
            graph,
            results,
            degrees_zero,
            degrees_graph
        )

        ls_max_time += time.time() - t0

    return pr_max_time, pr_min_time, ls_min_time, ls_max_time