import argparse 
import json
import os 
from ..helpers.designite_py.dpy_class import get_overall_metrics 


def write_overall_metrics(dpy_path): 
    dpy_folder_path = dpy_path

    for json_file in os.listdir(dpy_folder_path): 
        # arch smells (skipped) 
        # class module metrics 
        if (json_file.endswith("class_module_metrics.json")): 
            with open(os.path.join(dpy_folder_path, json_file), 'r') as f: 
                print(get_overall_metrics(json.load(f))) 

# usage: write.py [dpy_folder_path]
def main(): 
    parser = argparse.ArgumentParser()
    parser.add_argument("dpy_path", help="Abs path to the dpy folder")
    args = parser.parse_args()

    write_overall_metrics(args.dpy_path) 
   

if __name__ == "__main__": 
    main() 