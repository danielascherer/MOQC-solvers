from __future__ import annotations

import gurobipy as gp
from gurobipy import GRB
import networkx as nx

# ---------------------------------------------------------------------
# Build model
# ---------------------------------------------------------------------

def build_ws_model(graph: nx.Graph, connected: bool) -> tuple[gp.Model, dict, dict]:
    model = gp.Model("WS")
    model.setParam(GRB.Param.LogToConsole, 0)
    model.setParam(GRB.Param.Threads, 1)

    vtype_x = GRB.BINARY if connected else GRB.CONTINUOUS

    x = {i: model.addVar(name=f"x({i})", vtype=vtype_x, lb=0.0, ub=1.0) for i in graph.nodes}
    y = {
        (i, j): model.addVar(name=f"y({i},{j})", vtype=GRB.CONTINUOUS, lb=0.0, ub=1.0)
        for (i, j) in graph.edges
    }
    
    if connected:
        model._xvars = x
        
        orig_components = list(nx.connected_components(graph))
        if len(orig_components) > 1:
            z = {}
            for idx, comp in enumerate(orig_components):
                z[idx] = model.addVar(name=f'z_comp({idx})', vtype=GRB.BINARY)
                
            model.addConstr(gp.quicksum(z.values()) <= 1, name="OneComponentActive")
            
            for idx, comp in enumerate(orig_components):
                for i in comp:
                    model.addConstr(x[i] <= z[idx], name=f'LinkComp_x({i})')

    model.update()

    for (i, j) in graph.edges:
        model.addConstr(y[i, j] <= x[j], name=f"C1({i},{j})")
        model.addConstr(y[i, j] <= x[i], name=f"C2({i},{j})")

    model.update()
    return model, x, y


# ---------------------------------------------------------------------
# Objective
# ---------------------------------------------------------------------
def update_ws_objective(model: gp.Model, w_v: int, w_e: int) -> None:
    obj_e = gp.quicksum(var for var in model.getVars() if 'y' in var.VarName)
    obj_v = gp.quicksum(var for var in model.getVars() if 'x' in var.VarName)
    model.setObjective((w_e * obj_e) - (w_v * obj_v), GRB.MAXIMIZE)


# ---------------------------------------------------------------------
# Connectedness callback
# ---------------------------------------------------------------------
def ws_connectedness_callback(model, where):
    if where == GRB.Callback.MIPSOL:
        xvars_dict = model._xvars
        nodes = list(xvars_dict.keys())
        xvals = model.cbGetSolution([xvars_dict[i] for i in nodes])
        
        selected = [nodes[idx] for idx, val in enumerate(xvals) if val > 0.5]
        if not selected:
            return
            
        subgraph = model._G.subgraph(selected)
        if not nx.is_connected(subgraph):
            components = list(nx.connected_components(subgraph))
            for c in components:
                comp_nodes = set(c)
                neigh = set()
                for i in comp_nodes:
                    neigh.update(model._G.neighbors(i))
                
                neigh.difference_update(comp_nodes)
                if not neigh:
                    continue
                
                sum_neighbors = gp.quicksum(xvars_dict[j] for j in neigh)
                for i in comp_nodes:
                    model.cbLazy(sum_neighbors >= xvars_dict[i])

