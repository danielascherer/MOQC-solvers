from __future__ import annotations

import networkx as nx
import pandas as pd

def read_graph(path):
    data = pd.read_csv(path, sep=" ", header=None, skiprows=2, usecols=[0, 1])
    edges = data.values
    edges = edges[edges[:, 0] != edges[:, 1]]

    G = nx.Graph()
    G.add_edges_from(edges)

    degrees = {v: G.degree(v) for v in G.nodes}
    zeros = {v: 0 for v in G.nodes}

    return G, G.number_of_nodes(), G.number_of_edges(), degrees, zeros
