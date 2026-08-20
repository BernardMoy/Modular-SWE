import argparse 
import os 
from constants import IMPL_DIR_DICT, BASE_IMPL_DIR
import subprocess 

def main(): 
    parser = argparse.ArgumentParser() 
    parser.add_argument("problem", help="Reference problem, e.g. tqdm")
    parser.add_argument("output", help="Output directory")
    args = parser.parse_args()

    # obtain the impl dir from the dict 
    if args.problem not in IMPL_DIR_DICT: 
        raise Exception(f"Invalid problem: {args.problem}")
    IMPL_DIR = os.path.join(BASE_IMPL_DIR, IMPL_DIR_DICT[args.problem]) 

    # call the deps graph sh script 
    subprocess.run([
        "scripts/deps_graph.sh", 
        IMPL_DIR,
        args.output
    ])

    
# usage: python scripts/references_deps_graph.py <problem> <output> 
# the problem is the PROBLEM NAME not the entrypoint directory (src) 
if __name__ == "__main__":
    main()