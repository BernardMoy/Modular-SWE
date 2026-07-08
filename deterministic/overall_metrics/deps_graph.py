import argparse 
import os 
import subprocess 
import shutil
import json 
from pathlib import Path
from ..helpers.deps_graph.visibility_matrix import get_visibility_matrix

def get_deps_graph_metrics(implementation_path): 
    """
    {
        "density": 0
    }
    """

    TEMP_FILE = Path("temp_graph")

    subprocess.run([
        "scripts/deps_graph.sh", 
        implementation_path / "circopt.py",  # hard code the entry point 
        TEMP_FILE
    ])

    with open(TEMP_FILE / "deps_graph.json", 'r') as f: 
        graph = json.load(f) 

    shutil.rmtree(TEMP_FILE)
    
    # density is the number of 1s in the visibility matrix / total number of entries (N2) 
    # +N because every module sees itself 
    visibility_matrix = get_visibility_matrix(graph)
    N = len(visibility_matrix)
    density = (sum([len(value) for value in visibility_matrix.values()])+N) / (N*N)
    
    return {
        "density": density
    }

