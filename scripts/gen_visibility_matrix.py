"""
Given a deps graph json and an output, 
write to the output png or output json the visibility matrix. 
"""
import argparse
import json 
import sys
from pathlib import Path
from matplotlib import pyplot as plt 
import numpy as np 
import os 

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from metrics.deps_graph.smells.visibility_matrix import get_visibility_matrix


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="json path to the deps graph")
    parser.add_argument("-o", required=True, help="output path for the visibility matrix")
    args = parser.parse_args()

    # read the json graph 
    with open(args.path, 'r') as f: 
        graph_json = json.load(f) 
    matrix = get_visibility_matrix(graph_json)

    # write the matrix json to the output 
    with open(os.path.join(args.o, "matrix.json"), 'w') as f: 
        json.dump(matrix, f, indent=2, sort_keys=True)

    # Create a set containing all modules 
    modules = set() 
    for key, values in matrix.items(): 
        modules.add(key) 
        for value in values:
            modules.add(value) 

    # Convert the modules into a sorted list to display the modules in order
    modules = sorted(list(modules))
    n = len(modules)
    idx = {m: i for i, m in enumerate(modules)}
    
    # Build np matrix where left = from, top = to
    adj_matrix = np.zeros((n, n), dtype=int)
    for src, targets in matrix.items():
        for tgt in targets:
            adj_matrix[idx[src], idx[tgt]] = 1
    
    fig, ax = plt.subplots(figsize=(n,n))
    
    # highlight in blue if the matrix is connected, else gray 
    for i in range(n):
        for j in range(n):
            color = "#76bdff" if adj_matrix[i, j] else "#f2f2f2"
            ax.add_patch(plt.Rectangle((j, n-1-i), 1, 1, facecolor=color,
                                        edgecolor="white", linewidth=1.5))
    
    ax.set_xlim(0, n)
    ax.set_ylim(0, n)
    ax.set_aspect("equal")
    
    # Top are modules that are affected by the change on left 
    ax.set_xticks(np.arange(n) + 0.5)
    ax.set_xticklabels(modules, rotation=45, ha="left", fontsize=11)
    ax.xaxis.set_ticks_position("top")
    ax.xaxis.set_label_position("top")
    
    # Left are the modules that changes 
    ax.set_yticks(np.arange(n) + 0.5)
    ax.set_yticklabels(list(reversed(modules)), fontsize=11)
    
    ax.set_xlabel("Modules affected", fontsize=13, labelpad=45)
    ax.set_ylabel("Change in module", fontsize=13)
    
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    
    plt.title("Visibility Matrix", fontsize=15, pad=60)
    plt.tight_layout()
    plt.savefig(os.path.join(args.o, "matrix.png"), dpi=200, bbox_inches="tight")

if __name__ == "__main__":
    main()
