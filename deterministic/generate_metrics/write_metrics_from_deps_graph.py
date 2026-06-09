import json 
import argparse 
from ..helpers.deps_graph.circular_dependency_checker import check_circular_dependency
from ..helpers.deps_graph.isolated_node_checker import check_isolated_node
from ..helpers.deps_graph.hub_like_modularisation_checker import check_hub_like_modularisation
from ..helpers.deps_graph.instable_dependency_checker import check_instable_dependency

def get_metrics_from_deps_graph(deps_graph_json): 
    """
    Get metrics from dependency graph using deterministic helper methods. 
    Write to the current_designs.json file. 
    """

    all_metrics = [] 

    # Check circular dependency (Must fail) 
    all_metrics.extend(check_circular_dependency(deps_graph_json))
    
    # Check isolated node (Must fail)  
    all_metrics.extend(check_isolated_node(deps_graph_json))

    # Check hub like 
    all_metrics.extend(check_hub_like_modularisation(deps_graph_json))

    # Check instable dependency
    all_metrics.extend(check_instable_dependency(deps_graph_json))

    return all_metrics
    
# usage: write.py [deps-graph-path] [current-metrics-path]
def main(): 
    parser = argparse.ArgumentParser()
    parser.add_argument("deps_graph_path", help="Abs path to the dependency graph JSON file")
    parser.add_argument("current_metrics_path", help="Abs path to write the metrics to")
    args = parser.parse_args()

    # Read the JSON graph from the path 
    with open(args.deps_graph_path, 'r') as f: 
        graph_json = json.load(f)

    result = get_metrics_from_deps_graph(graph_json)
    result_json = json.dumps(result, indent=2)
    
    # Write the result to current metrics 
    with open(args.current_metrics_path, 'w') as f: 
        f.write(result_json)

if __name__ == "__main__": 
    main() 