import json 
import argparse 
from ..helpers.deps_graph.circular_dependency_checker import check_circular_dependency
from ..helpers.deps_graph.isolated_node_checker import check_isolated_node
from ..helpers.deps_graph.hub_like_modularisation_checker import check_hub_like_modularisation
from ..helpers.deps_graph.unstable_dependency_checker import check_unstable_dependency
from ..helpers.design.fat_module_checker import check_fat_module
from ..reusables.sort_smells import sort_smells

def get_metrics_from_deps_graph(deps_graph_json): 
    """
    Get metrics from dependency graph using deterministic helper methods. 
    Write to the current_designs.json file. 

    Metrics: 
    1. Unstable dependencies 
    2. Circular import 
    3. Isolated module 
    4. Hub like modularisation
    """

    deps_graph_metrics = [] 

    # Check circular dependency (Must fail) 
    deps_graph_metrics.extend(check_circular_dependency(deps_graph_json))
    
    # Check isolated node (Must fail)  
    deps_graph_metrics.extend(check_isolated_node(deps_graph_json))

    # Check hub like 
    deps_graph_metrics.extend(check_hub_like_modularisation(deps_graph_json))

    # Check unstable dependency
    deps_graph_metrics.extend(check_unstable_dependency(deps_graph_json))

    return deps_graph_metrics

def get_metrics_from_design(design_json): 
    """
    Metrics: 
    1. Fat module (large public interface)
    """
    design_metrics = [] 
    design_metrics.extend(check_fat_module(design_json))
    return design_metrics

def write_metrics_from_design_and_deps_graph(design_path, deps_graph_path, current_metrics_path): 
    # Read the JSON design from the path 
    with open(design_path, 'r') as f: 
        design_json = json.load(f)

    # Read the JSON graph from the path 
    with open(deps_graph_path, 'r') as f: 
        graph_json = json.load(f)

    # Concat the deps graph and the design metrics 
    smells = get_metrics_from_deps_graph(graph_json) + get_metrics_from_design(design_json)

    # Sort smells 
    smells = sort_smells(smells) 

    smells_json = json.dumps(smells, indent=2)
    
    # Write the smells to current metrics 
    with open(current_metrics_path, 'w') as f: 
        f.write(smells_json)

# usage: write.py [current_design_path] [current_deps_graph_path] [current_metrics_output_path]
def main(): 
    parser = argparse.ArgumentParser()
    parser.add_argument("design_path", help="Current design file, should be in the second iter only to ensure the public_interface field exists")
    parser.add_argument("deps_graph_path", help="Abs path to the dependency graph JSON file")
    parser.add_argument("current_metrics_path", help="Abs path to write the metrics to")
    args = parser.parse_args()

    write_metrics_from_design_and_deps_graph(args.design_path, args.deps_graph_path, args.current_metrics_path)

if __name__ == "__main__": 
    main() 