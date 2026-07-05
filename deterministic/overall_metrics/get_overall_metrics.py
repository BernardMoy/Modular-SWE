import argparse 
from .radon import get_radon_metrics
from .dpy import get_dpy_metrics
from .jscpd import get_duplicates

# Given a single implementation path return its overall metrics for evaluation
def get_overall_metrics(implementation_path): 
    """
    {
        "lloc": 0,
        "duplicated_code_percent": 0, 
        "weighted_maintainability_index": 0, 
        "function_cyclomatic_complexity_count": 0, 
        "high_fan_out_classes_count": 0, 
    }
    """
    radon = get_radon_metrics(implementation_path) 
    dpy = get_dpy_metrics(implementation_path) 
    jscpd = get_duplicates(implementation_path) 

    return {
        "lloc": radon["lloc"],
        "duplicated_code_percent": jscpd["lines"], 
        "weighted_maintainability_index": radon["weighted_maintainability_index"], 
        "function_cyclomatic_complexity_count": dpy["function_cyclomatic_complexity_count"], 
        "high_fan_out_classes_count": dpy["high_fan_out_classes_count"], 
    }

# usage: write.py [implementation folder path]
# results are printed 
def main(): 
    parser = argparse.ArgumentParser()
    parser.add_argument("implementation_path", help="Path to the impl folder")
    args = parser.parse_args()

    overall_metrics = get_overall_metrics(args.implementation_path)
    print(overall_metrics) 
   

if __name__ == "__main__": 
    main() 

