import json 
import argparse 
from pathlib import Path 

# usage: deps_graph.py [entry_file] [output_dir]
def main(): 
    parser = argparse.ArgumentParser()
    parser.add_argument("entry_file", help="Problem entry file python file")
    parser.add_argument("output_dir", help="Output dir containing the svg, dot and json")
    args = parser.parse_args()

    # Create the output directory 
    OUTPUT_DIR = Path(args.output_dir)
    OUTPUT_DIR.mkdir(exist_ok=True) 
    
    # Generate the svg 

    # Generate the dot 

    # Process the graph to json format 

    

if __name__ == "__main__": 
    main() 