import argparse
import subprocess
import shutil
import json
from pathlib import Path
from metrics.deps_graph.smells.visibility_matrix import get_visibility_matrix
from metrics.deps_graph.smells.circular_dependency_checker import (
    check_circular_dependency,
)
import time


def get_n(deps_graph):
    """
    Return the number of modules in the graph
    """
    visibility_matrix = get_visibility_matrix(deps_graph)
    N = len(visibility_matrix)
    return N


def get_propagation_cost(deps_graph):
    """
    propagationCost is the number of 1s in the visibility matrix / total number of entries (N2)
    +N because every module sees itself

    Return: number
    """

    visibility_matrix = get_visibility_matrix(deps_graph)
    N = len(visibility_matrix)
    propagation_cost = (
        (sum([len(value) for value in visibility_matrix.values()]) + N) / (N * N)
        if N > 0
        else 1
    )
    return propagation_cost


def get_impact_size(deps_graph):
    """
    Measure the average reachability of each module from the visibility matrix.
    Return: number
    """
    visibility_matrix = get_visibility_matrix(deps_graph)
    N = len(visibility_matrix)
    impact_size = 0
    for key, value in visibility_matrix.items():
        impact_size += (
            len(value) / N
        )  # the average number of modules affected by the change = len(value)
    return impact_size

# sum of fan in = sum of fan out  / number of modules 
def get_average_degree(deps_graph, n): 
    s = 0 
    for key, value in deps_graph.items(): 
        s += len(value) 
    
    return s / n if n > 0 else 0 

def get_deps_graph_metrics(implementation_path):
    """
    {
        "number_of_modules": 0,
        "has_cycles": False,
        "propagation_cost": 0,
        "impact_size": 0,
        "average_degree": 0, 
    }
    """

    TEMP_FILE = Path(f"temp_graph_{str(time.time()).replace(".", "_")}")

    subprocess.run(["python", "scripts/deps_graph.py", implementation_path, TEMP_FILE])

    with open(TEMP_FILE / "deps_graph.json", "r") as f:
        graph = json.load(f)

    shutil.rmtree(TEMP_FILE)

    n = get_n(graph)

    return {
        "number_of_modules": n,
        "has_cycles": len(check_circular_dependency(graph)) > 0,
        "propagation_cost": get_propagation_cost(graph),
        "impact_size": get_impact_size(graph),
        "average_degree": get_average_degree(graph, n), 
    }


# Same as get deps graph metrics, except that it accepts a problem
# and calls a separate deps graph generation script
def get_deps_graph_metrics_reference(problem):
    """
    {
        "number_of_modules": 0,
        "has_cycles": False,
        "propagation_cost": 0,
        "impact_size": 0,
        "average_degree": 0, 
    }
    """

    TEMP_FILE = Path(f"temp_graph_{str(time.time()).replace(".", "_")}")

    subprocess.run(["python scripts/references_deps_graph.py", problem, TEMP_FILE])

    with open(TEMP_FILE / "deps_graph.json", "r") as f:
        graph = json.load(f)

    shutil.rmtree(TEMP_FILE)
    n = get_n(graph)
    return {
        "number_of_modules": n,
        "has_cycles": len(check_circular_dependency(graph)) > 0,
        "propagation_cost": get_propagation_cost(graph),
        "impact_size": get_impact_size(graph),
        "average_degree": get_average_degree(graph, n), 
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("implementation_path", help="Path to the impl folder")
    args = parser.parse_args()

    metrics = get_deps_graph_metrics(args.implementation_path)
    print(metrics)


if __name__ == "__main__":
    main()
