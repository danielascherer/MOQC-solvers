# MOQC-solvers

This repository contains implementations of algorithms for solving the **Multiobjective quasi-clique (MOQC)** problem.

The MOQC problem aims to identify quasi-cliques by simultaneously optimising the number of vertices and the density of the subgraph, without requiring a predefined density threshold or fixed cardinality.

## Problem Description

A detailed description of the MOQC problem, including its formal definition, input format, and illustrative examples, is available in:

`docs/moqc.md`

## Contents

This repository includes:

### Exact Solution Methods
- $\varepsilon$-constraint method (**e-DKS**)  
- **Two-phase** strategy  
- **Three-phase** strategy  

### Heuristic Method
- Path-relinking-based heuristic with local search refinement

## Requirements

- Python 3.8+
- `networkx`
- `gurobipy` *(requires a valid Gurobi licence)*

## Running the Code

The methods can be executed using the main command-line interface:

```bash
python3.8 -m exact_methods.main <graph_file> --method <method_name> [--connected]
```

```bash
python3.8 -m heuristic_methods.main <graph_file> <number_of_iterations> [--connected]
```

### Examples
```bash
python3.8 -m exact_methods.main /data/polbooks.mtx --method e_dks

python3.8 -m exact_methods.main /data/polbooks.mtx --method e_dks --connected

python3.8 -m heuristic_methods.main /data/polbooks.mtx 10

python3.8 -m heuristic_methods.main /data/polbooks.mtx 10 --connected
```

## Output of the Implementations

The implementations in this repository do not follow a standardised solution file format. Instead, the methods generate intermediate and final solutions internally and store relevant information about each solution found (such as number of vertices, number of edges, density, and efficiency status) during execution.

## Repository Structure

```text
docs/
├── moqc.md                     # Problem description
src/
├── core/
│   ├── models/                 # Mathematical models for MOQC
│   └── solvers/                # Solvers for the models
│
├── exact_methods/
│   ├── methods/
│   │   ├── e_dks.py            # E-DKS method
│   │   ├── two_phase.py        # Two-phase strategy
│   │   └── three_phase.py      # Three-phase strategy
│   └── main.py                 # Main interface for exact methods
│
└── heuristic_methods/
    ├── local_search/           # Local search strategies
    ├── trajectory_strategies/  # Trajectory-based strategies
    └── main.py                 # Main interface for heuristic method

```

## Related Publications

The methods implemented in this repository are based on the following works:

### Exact Methods
> D. S. dos Santos, K. Klamroth, P. Martins, and L. Paquete  
> *Solving the Multiobjective Quasi-clique Problem*  
> European Journal of Operational Research, 323(2):409–424, 2025  
> DOI: https://doi.org/10.1016/j.ejor.2024.12.018


These methods are available in:
`src/exact_methods/`

### Heuristic Method
> D. S. dos Santos, K. Klamroth, P. Martins, and L. Paquete  
> *A Path-Relinking-based Heuristic for the Multiobjective Subgraph Problem*  
> GECCO, 2025  
> DOI: https://doi.org/10.1145/3712256.3726386

This method is available in:
`src/heuristic_methods/`

### Connected Models and Constraints

> D. S. dos Santos, K. Klamroth, P. Martins, and L. Paquete  
> *Ensuring connectedness for the maximum quasi-clique and densest k-subgraph problems*  
> International Transactions in Operational Research, 2026  
> DOI: https://doi.org/10.1111/itor.70184

The MILP formulations implemented in this repository for the connected variant rely on the connectedness constraints introduced in this work.


## Important Note on the Implementation

This repository **does not contain the original source code** used to produce the computational results reported in the above publications.
Instead, it provides a **reimplementation** of the proposed methods based on the same algorithmic ideas and formulations, with improvements in **code structure, readability, and performance**. 

Therefore, results obtained with this code may **not exactly match** those reported in the publications.
Differences may arise due to implementation choices, refactoring and optimisations, solver configuration and behaviour, and parameter settings.

## Datasets

The graph instances used in our computational studies are available in a separate repository:
https://github.com/danielascherer/MOQC
This dataset repository has been used and referenced in the associated publications.

## License

MIT License

Copyright (c) 2024 Daniela S. dos Santos

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Citation

If you use this code for academic purposes, please cite the associated publications listed above.

```bibtex
@article{santos2025EJOR,
    title={Solving the multiobjective quasi-clique problem},
    author={Daniela Scherer dos Santos and Kathrin Klamroth and Pedro Martins and Luís Paquete},
    journal={European Journal of Operational Research},
    volume={323},
    number={2},
    pages={409--424},
    year={2025},
    publisher={Elsevier},
    doi = {10.1016/j.ejor.2024.12.018}
}

@inproceedings{santos2025GECCO,
    title = {A Path-Relinking-based Heuristic for the Multiobjective Subgraph Problem},
    author={Daniela Scherer dos Santos and Kathrin Klamroth and Pedro Martins and Luís Paquete},    
    booktitle = {Proceedings of the Genetic and Evolutionary Computation Conference},
    pages = {304–312},
    isbn = {9798400714658},    
    address = {New York, NY, USA},
    location = {NH Malaga Hotel, Malaga, Spain},
    series = {GECCO '25},
    year = {2025},
    publisher = {Association for Computing Machinery},
    doi = {10.1145/3712256.3726386}
}

@article{santos2026,
    title={Ensuring connectedness for the maximum quasi-clique and densest k-subgraph problems},
    author={Daniela Scherer dos Santos and Kathrin Klamroth and Pedro Martins and Luís Paquete},
    journal={International Transactions in Operational Research},
    volume={33},
    number={2},
    pages = {3800-3824},
    year={2026},
    doi={10.1111/itor.70184}
}
```



