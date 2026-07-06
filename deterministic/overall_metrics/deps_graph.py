import argparse 
import os 
import subprocess 
import shutil
import json 
from pathlib import Path

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

    with open(TEMP_FILE, 'r') as f: 
        graph = json.load(f) 
