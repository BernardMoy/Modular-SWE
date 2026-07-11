import os 
from radon.metrics import mi_visit 
from radon.raw import analyze 
import argparse

def get_radon_metrics(implementation_path): 
    """
    {
        "lloc": 0,
        "weighted_maintainability_index": 0, 
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
                    analyzed = analyze(code) # Module(loc=49, lloc=59, sloc=36, comments=0, multi=0, blank=13, single_comments=0)
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
    }

def main(): 
    parser = argparse.ArgumentParser()
    parser.add_argument("implementation_path", help="Path to the impl folder")
    args = parser.parse_args()

    metrics = get_radon_metrics(args.implementation_path)
    print(metrics) 
   

if __name__ == "__main__": 
    main() 

