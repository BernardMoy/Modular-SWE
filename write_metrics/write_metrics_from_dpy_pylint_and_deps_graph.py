import argparse 
import json
import os 
from metrics.deps_graph.metrics import get_metrics_from_deps_graph
from metrics.designite_py.metrics import get_metrics_from_dpy
from metrics.pylint.metrics import check_duplicated_lines_of_code
from reusables.sort_smells import sort_smells

def write_metrics_from_dpy_pylint_and_deps_graph(dpy_path, pylint_path, deps_graph_path, current_metrics_path): 
    smells = []

    # Read the JSON graph from the path 
    with open(deps_graph_path, 'r') as f: 
        deps_graph_json = json.load(f) 
    
    # Read the pylint json path 
    with open(pylint_path, 'r') as f: 
        pylint_json = json.load(f) 

    # Add dpy smells 
    smells.extend(get_metrics_from_dpy(dpy_path))

    # Obtain the remaining metrics from deps graph 
    # Which cannot be obtained from dpy metrics
    # CURRENTLY IGNORED: THOSE ARE HANDLED IN THE DESIGN STAGE. 
    # smells.extend(get_metrics_from_deps_graph(deps_graph_json))

    # Obtain the duplicated loc smell from pylint 
    smells.extend(check_duplicated_lines_of_code(pylint_json))

    # Sort smells 
    smells = sort_smells(smells) 

    # Write the smells to current_design.json 
    result_json = json.dumps(smells, indent=2)
    with open(current_metrics_path, 'w') as f: 
        f.write(result_json)


# usage: write.py [dpy_folder_path] [pylint_metrics_json_path] [current_deps_graph_path] [current_metrics_output_path]
def main(): 
    parser = argparse.ArgumentParser()
    parser.add_argument("dpy_path", help="Abs path to the dpy folder")
    parser.add_argument("pylint_path", help="Abs path to the pylint folder")
    parser.add_argument("deps_graph_path", help="Abs path to the deps graph json file")
    parser.add_argument("current_metrics_path", help="Abs path to write the metrics to")
    args = parser.parse_args()

    write_metrics_from_dpy_pylint_and_deps_graph(
        args.dpy_path, args.pylint_path, args.deps_graph_path, args.current_metrics_path
    )

if __name__ == "__main__": 
    main() 