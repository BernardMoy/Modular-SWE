import argparse 
import os 
import subprocess 
import shutil
import json 
from pathlib import Path
from metrics.deps_graph.smells.visibility_matrix import get_visibility_matrix
from metrics.deps_graph.smells.circular_dependency_checker import check_circular_dependency

def get_propagation_cost(deps_graph): 
    """
    propagationCost is the number of 1s in the visibility matrix / total number of entries (N2) 
    +N because every module sees itself 

    Return: number 
    """

    visibility_matrix = get_visibility_matrix(deps_graph)
    N = len(visibility_matrix)
    propagation_cost = (sum([len(value) for value in visibility_matrix.values()])+N) / (N*N)
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
        impact_size += len(value)/N  # the average number of modules affected by the change = len(value)
    return impact_size

def get_deps_graph_metrics(implementation_path): 
    """
    {
        "hasCycles": False, 
        "propagationCost": 0, 
        "impactSize": 0, 
    }
    """

    TEMP_FILE = Path("temp_graph")

    subprocess.run([
        "scripts/deps_graph.sh", 
        implementation_path,
        TEMP_FILE
    ])

    with open(TEMP_FILE / "deps_graph.json", 'r') as f: 
        graph = json.load(f) 

    shutil.rmtree(TEMP_FILE)
    

    return {
        "hasCycles": len(check_circular_dependency(graph)) > 0, 
        "propagationCost": get_propagation_cost(graph), 
        "impactSize": get_impact_size(graph) 
    }

# def get_weighted_deps_graph_metrics(d, implementation_path): 
#     TEMP_FILE = Path("temp_graph")

#     subprocess.run([
#         "scripts/deps_graph.sh", 
#         implementation_path / "circopt.py",  # hard code the entry point 
#         TEMP_FILE
#     ])

#     with open(TEMP_FILE / "deps_graph.json", 'r') as f: 
#         graph = json.load(f) 

#     shutil.rmtree(TEMP_FILE)

#     visibility_matrix = get_visibility_matrix(graph)
#     N = len(visibility_matrix)

#     # obtain weights for each key 
#     weights = {} 
#     K = 1
#     for key in visibility_matrix.keys(): 
#         if key in d: 
#             weights[key] = K+d[key]
#         else: 
#             weights[key] = K 

#     # normalize the weights 
#     total = sum(x for x in weights.values())
    
#     density = 0 
#     for key, value in visibility_matrix.items(): 
#         raw_density = (len(value)/N)
#         density += raw_density*weights[key]/total if total>0 else 0
    
#     return {
#         "density": density
#     }
