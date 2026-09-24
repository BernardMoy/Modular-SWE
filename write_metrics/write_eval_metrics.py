"""
Write evaluation metrics (Those used in notebook) 
from an implementation dir 
"""

import json
import argparse
from metrics.radon.overall_metrics import get_radon_metrics
from metrics.deps_graph.overall_metrics import get_deps_graph_metrics
from metrics.designite_py.overall_metrics import get_dpy_metrics
from metrics.jscpd.overall_metrics import get_duplicates

# Given an impl path (by agent), output eval metrics
def get_eval_metrics(implementation_path):

    radon_metrics = get_radon_metrics(implementation_path)
    deps_graph_metrics = get_deps_graph_metrics(implementation_path)
    dpy_metrics = get_dpy_metrics(implementation_path)
    jscpd_metrics = get_duplicates(implementation_path)

    # organised into the 5 aspects we care about
    result = {
        "implementation_path": implementation_path,
        "lloc": 0,
        "loc": 0,
        "lloc_per_function": 0,
        "lloc_per_module": 0,
        "function_max_loc": 0,
        "modules_max_lloc": 0,
        "comments_percentage": 0,
        "cc_per_function": 0,
        "high_cc_functions_count": 0,
        "function_max_cc": 0,
        "weighted_mi": 0,
        "propagation_cost": 0,
        "impact_size": 0,
        "average_degree": 0,
        "has_cycles": 0,
        "number_of_modules": 0,
        "number_of_functions": 0,
        "number_of_functions_per_module": 0,
        "nopm_per_class": 0,
        "class_max_nopm": 0,
        "duplicated_lines": 0,
        "duplicated_tokens": 0,
    }

    result["lloc"] = radon_metrics["lloc"]
    result["loc"] = radon_metrics["loc"]
    result["lloc_per_function"] = (
        result["lloc"] / dpy_metrics["number_of_functions"]
        if dpy_metrics["number_of_functions"] > 0
        else 0
    )
    result["lloc_per_module"] = (
        result["lloc"] / radon_metrics["number_of_py_files"]
        if radon_metrics["number_of_py_files"] > 0
        else 0
    )
    result["function_max_loc"] = dpy_metrics["function_max_loc"]
    result["modules_max_lloc"] = radon_metrics["modules_max_lloc"]
    result["comments_percentage"] = radon_metrics["comments_percentage"]

    result["cc_per_function"] = dpy_metrics["cc_per_function"]
    result["high_cc_functions_count"] = dpy_metrics["high_cc_functions_count"]
    result["function_max_cc"] = dpy_metrics["function_max_cc"]

    result["weighted_mi"] = radon_metrics["weighted_maintainability_index"]
    result["propagation_cost"] = deps_graph_metrics["propagation_cost"]
    result["impact_size"] = deps_graph_metrics["impact_size"]
    result["average_degree"] = deps_graph_metrics["average_degree"]

    result["has_cycles"] = deps_graph_metrics["has_cycles"]
    result["number_of_modules"] = radon_metrics["number_of_py_files"]
    result["number_of_functions"] = dpy_metrics["number_of_functions"]
    result["number_of_functions_per_module"] = (
        dpy_metrics["number_of_functions"] / radon_metrics["number_of_py_files"]
        if radon_metrics["number_of_py_files"] > 0
        else 0
    )
    result["nopm_per_class"] = dpy_metrics["nopm_per_class"]
    result["class_max_nopm"] = dpy_metrics["class_max_nopm"]

    result["duplicated_lines"] = jscpd_metrics["lines"]
    result["duplicated_tokens"] = jscpd_metrics["tokens"]

    # trim all results to round 3 dp
    for key, value in result.items():
        if key in ["has_cycles", "implementation_path"]:
            continue
        result[key] = round(value, 3)

    return result


# usage: write.py [implementation_path]
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("implementation_path", help="Impl folder path")
    args = parser.parse_args()

    result = get_eval_metrics(args.implementation_path)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
