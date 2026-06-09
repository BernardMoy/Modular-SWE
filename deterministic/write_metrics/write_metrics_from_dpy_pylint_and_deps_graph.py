import argparse 
import json
import os 
from ..helpers.designite_py.dpy_class import get_metrics_from_dpy_class
from ..helpers.designite_py.dpy_design import get_metrics_from_dpy_design
from ..helpers.designite_py.dpy_function import get_metrics_from_dpy_function
from ..helpers.designite_py.dpy_implementation import get_metrics_from_dpy_implementation
from ..helpers.deps_graph.circular_dependency_checker import check_circular_dependency
from ..helpers.deps_graph.isolated_node_checker import check_isolated_node
from ..helpers.deps_graph.unstable_dependency_checker import check_unstable_dependency
from ..reusables.sort_smells import sort_smells
from ..helpers.pylint.duplicate_loc_checker import check_duplicated_lines_of_code

def get_metrics_from_deps_graph(deps_graph_json): 
    """
    Get metrics from dependency graph using deterministic helper methods. 
    Prioritise getting metrics from dpy.

    Here are the metrics only obtainable from deps graph: 
    1. Unstable dependencies 
    2. Circular import 
    3. Isolated module 
    """

    deps_graph_metrics = [] 

    # Check circular dependency (Must fail) 
    deps_graph_metrics.extend(check_circular_dependency(deps_graph_json))
    
    # Check isolated node (Must fail)  
    deps_graph_metrics.extend(check_isolated_node(deps_graph_json))

    # Check unstable dependency
    deps_graph_metrics.extend(check_unstable_dependency(deps_graph_json))

    return deps_graph_metrics

# usage: write.py [dpy_folder_path] [pylint_metrics_json_path] [current_deps_graph_path] [current_metrics_output_path]
def main(): 
    parser = argparse.ArgumentParser()
    parser.add_argument("dpy_path", help="Abs path to the dpy folder")
    parser.add_argument("pylint_path", help="Abs path to the pylint folder")
    parser.add_argument("deps_graph_path", help="Abs path to the deps graph json file")
    parser.add_argument("current_metrics_path", help="Abs path to write the metrics to")
    args = parser.parse_args()

    smells = []

    dpy_folder_path = args.dpy_path

    # Read the JSON graph from the path 
    with open(args.deps_graph_path, 'r') as f: 
        deps_graph_json = json.load(f) 
    
    # Read the pylint json path 
    with open(args.pylint_path, 'r') as f: 
        pylint_json = json.load(f) 

    # Try to read each of the JSON file of the designite python metrics 
    # Identify which dpy metric file using the end string 
    # Skip if they do not exist 
    for json_file in os.listdir(dpy_folder_path): 
        # arch smells (skipped) 
        # class module metrics 
        if (json_file.endswith("class_module_metrics.json")): 
            with open(os.path.join(dpy_folder_path, json_file), 'r') as f: 
                smells.extend(get_metrics_from_dpy_class(json.load(f)))

        # design smells 
        if (json_file.endswith("design_smells.json")): 
            with open(os.path.join(dpy_folder_path, json_file), 'r') as f: 
                smells.extend(get_metrics_from_dpy_design(json.load(f)))

        # function metrics 
        if (json_file.endswith("function_metrics.json")): 
            with open(os.path.join(dpy_folder_path, json_file), 'r') as f: 
                smells.extend(get_metrics_from_dpy_function(json.load(f)))

        # implementation smells 
        if (json_file.endswith("implementation_smells.json")): 
            with open(os.path.join(dpy_folder_path, json_file), 'r') as f: 
                smells.extend(get_metrics_from_dpy_implementation(json.load(f)))

    # Obtain the remaining metrics from deps graph 
    # Which cannot be obtained from dpy metrics
    smells.extend(get_metrics_from_deps_graph(deps_graph_json))

    # Obtain the duplicated loc smell from pylint 
    smells.extend(check_duplicated_lines_of_code(pylint_json))

    # Sort smells 
    smells = sort_smells(smells) 

    # Write the smells to current_design.json 
    result_json = json.dumps(smells, indent=2)
    with open(args.current_metrics_path, 'w') as f: 
        f.write(result_json)


if __name__ == "__main__": 
    main() 