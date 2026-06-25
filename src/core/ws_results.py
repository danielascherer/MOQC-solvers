from __future__ import annotations
import networkx as nx
import pandas as pd

def read_solution_ws(point: tuple[int, int], results_ws_df: pd.DataFrame, optgraph: nx.Graph) -> nx.Graph:
    filtered_df = results_ws_df[(results_ws_df['NumberVertices'] == point[0]) & (results_ws_df['NumberEdges'] == point[1])]
    if filtered_df.empty:
        return nx.Graph()
    sol_vertices = filtered_df['Solution'].iloc[0]
    return nx.subgraph(optgraph, sol_vertices).copy()