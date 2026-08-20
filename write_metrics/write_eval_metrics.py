import json 
import argparse 
from metrics.deps_graph.metrics import get_metrics_from_deps_graph
from metrics.design.summary.get_summary import get_summary
from metrics.design.metrics import get_metrics_from_design
from reusables.sort_smells import sort_smells
from metrics.radon.overall_metrics import get_radon_metrics
from metrics.deps_graph.overall_metrics import get_deps_graph_metrics
from metrics.designite_py.overall_metrics import get_dpy_metrics
from metrics.jscpd.overall_metrics import get_duplicates

# Given an impl path (by agent), output eval metrics 
def get_eval_metrics(implementation_path): 
    """
    Return: 
    {
        "lloc": 0, 
        "loc": 0, 
        "lloc_per_function": 0, 
        "lloc_per_modules": 0, 
        "max_loc_function": 0, 
        "max_loc_modules": 0, 

        "cc_per_function": 0, 
        "high_cc_function_numbers": 0, 
        "max_cc_function": 0, 

        "number_of_modules": 0, 
        "weighted_mi": 0, 
        "prop_cost": 0, 

        "nopm_per_module": 0, 
        "max_nopm_module": 0, 
        
        "duplicated_lines": 0
    }
    """

    radon_metrics = [] 
    deps_graph_metrics = [] 
    dpy_metrics = [] 
    jscpd_metrics = [] 

# Given a reference problem, output eval metrics 
# This differs in the deps graph generation 
def get_eval_metrics_reference(reference_problem): 
    """
    Return: 
    {
        "lloc": 0, 
        "loc": 0, 
        "lloc_per_function": 0, 
        "lloc_per_modules": 0, 
        "max_loc_function": 0, 
        "max_loc_modules": 0, 

        "cc_per_function": 0, 
        "high_cc_function_numbers": 0, 
        "max_cc_function": 0, 

        "number_of_modules": 0, 
        "weighted_mi": 0, 
        "prop_cost": 0, 

        "nopm_per_module": 0, 
        "max_nopm_module": 0, 
        
        "duplicated_lines": 0
    }
    """



# usage: write.py [implementation_path] 
def main(): 
    parser = argparse.ArgumentParser()
    parser.add_argument("design_path", help="Current design file, should be in the second iter only to ensure the public_interface field exists")
    parser.add_argument("deps_graph_path", help="Abs path to the dependency graph JSON file")
    parser.add_argument("current_metrics_path", help="Abs path to write the metrics to")
    args = parser.parse_args()

    write_metrics_from_design_and_deps_graph(args.design_path, args.deps_graph_path, args.current_metrics_path)

if __name__ == "__main__": 
    main() 