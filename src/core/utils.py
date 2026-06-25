
BASE_LOG_DIR = "./logs"
BASE_RESULTS_DIR = "./results"

SELECTION_THRESHOLD = 0.1

GUROBI_STATUS_NAMES = {
    1: "LOADED", 2: "OPTIMAL", 3: "INFEASIBLE", 4: "INF_OR_UNBD",
    5: "UNBOUNDED", 6: "CUTOFF", 7: "ITERATION_LIMIT", 8: "NODE_LIMIT",
    9: "TIME_LIMIT", 10: "SOLUTION_LIMIT", 11: "INTERRUPTED",
    12: "NUMERIC", 13: "SUBOPTIMAL", 14: "INPROGRESS",
    15: "USER_OBJ_LIMIT", 16: "WORK_LIMIT", 17: "MEM_LIMIT",
}

# Time limit (seconds) for Gurobi
TIME_LIMIT = 3600

def get_status(model):
    return GUROBI_STATUS_NAMES.get(model.status, f"UNKNOWN({model.status})")

def compute_slope(p1, p2):
    if p1[0] == p2[0]:
        return float("inf")
    return (p1[1] - p2[1]) / (p1[0] - p2[0])