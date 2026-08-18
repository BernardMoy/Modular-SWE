import os 
from radon.metrics import mi_visit 
from radon.raw import analyze 
import argparse

def get_radon_metrics(implementation_path): 
    """
    {
        "lloc": 0,
        "comments_percentage": 0,
        "weighted_maintainability_index": 0, 
    }
    """

    weighted_mi = 0 
    total_sloc = 0 
    total_lloc = 0 
    total_loc = 0 
    total_comments = 0 

    # Iterate over all python files, read them and pass them to radon 
    for (root, dirs, files) in os.walk(implementation_path): 
        # ignore certain files 
        dirs[:] = [d for d in dirs if d not in {"dist", "node_modules", "__pycache__", ".venv"}]
        for f in files: 
            if f.endswith(".py"): 
                py_file_path = os.path.join(root, f) 

                # open the file 
                try: 
                    code = open(py_file_path, 'r').read() 
                    mi = mi_visit(code, multi=True) 
                    analyzed = analyze(code) # Module(loc=49, lloc=59, sloc=36, comments=0, multi=0, blank=13, single_comments=0)
                    total_sloc += analyzed.sloc
                    total_lloc += analyzed.lloc
                    total_loc += analyzed.loc 
                    total_comments += analyzed.comments 
                    weighted_mi += mi*analyzed.sloc

                except Exception as e: 
                    print(e)

    return {
        "lloc": total_lloc, 
        "comments_percentage": 100*total_comments / total_loc if total_loc > 0 else 0, 
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

