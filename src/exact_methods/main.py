import argparse
import os
from exact_methods.methods.three_phase.three_phase import run_three_phase
from exact_methods.methods.two_phase.two_phase import run_two_phase
from exact_methods.methods.e_dks.e_dks import run_e_dks

def main():
    parser = argparse.ArgumentParser(
        description="Multiobjective Quasi-clique problem exact methods."
    )
    parser.add_argument(
        "graph_file", 
        help="Path to the graph file."
    )
    parser.add_argument(
        "--method", 
        default="three_phase", 
        choices=["three_phase", "two_phase", "e_dks"],
        help="Method to run (default: three_phase)"
    )  
    parser.add_argument(
        "--connected", 
        action="store_true", 
        help="Ensure connectedness"
    )
    args = parser.parse_args()
    
    if args.method == "three_phase":
        print("Running three_phase")
        run_three_phase(args.graph_file, args.connected)
    elif args.method == "two_phase":
        print("Running two_phase")
        run_two_phase(args.graph_file, args.connected)
    elif args.method == "e_dks":
        print("Running e_dks")
        run_e_dks(args.graph_file, args.connected)
    else:
        raise ValueError(f"Unknown method: {args.method}")

if __name__ == "__main__":
    main()
