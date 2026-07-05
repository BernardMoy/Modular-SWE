import argparse 
import json
import os 
from radon.metrics import mi_visit 
from radon.raw import analyze 

def get_overall_metrics(implementation_path): 
    """
    {
        "lloc": 0, 
        "weighted_maintainability_index": 0, 
        "function_cyclomatic_complexity_count": 0, 
        "function_cognitive_complexity_count": 0, 
        "duplicated_line_of_code_percent": 0, 
    }
    """

    weighted_mi = 0 
    total_sloc = 0 
    total_lloc = 0 

    # Iterate over all python files, read them and pass them to radon 
    for (root, dirs, files) in os.walk(implementation_path): 
        for f in files: 
            if f.endswith(".py"): 
                py_file_path = os.path.join(root, f) 

                # open the file 
                try: 
                    code = open(py_file_path, 'r').read() 
                    mi = mi_visit(code, multi=True) 
                    analyzed = analyze(code)
                    sloc = analyzed.sloc 
                    lloc = analyzed.lloc

                    total_sloc += sloc 
                    total_lloc += lloc
                    weighted_mi += mi*sloc

                except Exception as e: 
                    print(e)
    
    return {
        "lloc": total_lloc, 
        "weighted_maintainability_index": weighted_mi / total_sloc if total_sloc > 0 else -1, 
        "function_cyclomatic_complexity_count": 0, 
        "function_cognitive_complexity_count": 0, 
        "duplicated_line_of_code_percent": 0, 
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