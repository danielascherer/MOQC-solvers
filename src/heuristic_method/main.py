import argparse
from heuristic_method.path_relinking_based_method import run_path_relinking_based_method

def main():
    parser = argparse.ArgumentParser(
        description="Multiobjective Quasi-clique problem heuristic methods."
    )
    parser.add_argument(
        "graph_file", 
        help="Path to the graph file."
    )
    parser.add_argument(
        "run_number",
        help="Run number to append to output files."
    )
    parser.add_argument(
        "--connected", 
        action="store_true", 
        help="Ensure connectedness constraints"
    )
    args = parser.parse_args()
    
    print(f"Running path_relinking_based heuristic method on {args.graph_file} (run {args.run_number})")
    run_path_relinking_based_method(args.graph_file, args.run_number, args.connected)

if __name__ == "__main__":
    main()
