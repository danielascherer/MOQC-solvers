# MOQC-solvers
This repository contains implementations of algorithms for solving the **Multiobjective quasi-clique (MOQC)** problem.

It includes:
- Exact solution methods: e-DKS epsilon constraint, Two-phase and Three-phase strategies.
- A path-relinking-based heuristic

---

## Related Publications

The methods implemented in this repository are based on the following works:

### Exact Methods
> D. S. dos Santos, K. Klamroth, P. Martins, and L. Paquete  
> *Solving the Multiobjective Quasi-clique Problem*  
> European Journal of Operational Research, 323(2):409–424, 2025  
> DOI: https://doi.org/10.1016/j.ejor.2024.12.018

These methods are available in:
src/exact_methods/

### Heuristic Method
> D. S. dos Santos, K. Klamroth, P. Martins, and L. Paquete  
> *Ensuring connectedness for the maximum quasi-clique and densest k-subgraph problems*  
> International Transactions in Operational Research, 2026  
> DOI: https://doi.org/10.1111/itor.70184

This method is available in:
src/heuristic_methods/three_phase

---

## Important Note on the Implementation

This repository **does not contain the original code** used to produce the computational results reported in the papers above.
Instead, it provides a **reimplementation** of the proposed methods based on the same algorithmic ideas and formulations, with improvements in **code structure, readability, and performance**. Therefore, results obtained with this code may **not exactly match** those reported in the papers. Differences may arise due to implementation choices, refactoring and optimisations, solver behaviour, and parameter settings.

## Datasets

The graph instances used in our computational studies are available in a separate repository:
https://github.com/danielascherer/MOQC
This dataset repository has been used and referenced in the associated publications.

