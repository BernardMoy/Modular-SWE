import argparse 
import json

# Given a current design json file 
# Return all fat modules with a large public interface 
# with size greater than the below threshold 
NOPM_THRESHOLD = 7

def check_fat_module(json_object): 
    """
    Return in the format [
        {
            "Category": "Module level",  
            "Module": ..., 
            "Smell": "Fat module", 
            "Description": The module x has a high number of public methods ({entry['NOPM']}), indicating insufficient modularisation.
        }
    ]
    """
    smells = [] 
    for entry in json_object: 
        if "public_interface" in entry and len(entry["public_interface"]) >= NOPM_THRESHOLD: 
            smells.append(
                {
                    "Category": "Module level",  
                    "Module": entry["module_name"], 
                    "Smell": "Fat module", 
                    "Description": f"The module '{entry['module_name']}' has a high number of public methods ({entry['NOPM']}), indicating insufficient modularisation."
                }
            )
    return smells
    


# usage: check.py [abs-path]
def main(): 
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Abs path to the current design JSON file")
    args = parser.parse_args()

    # Read the JSON graph from the path 
    with open(args.path, 'r') as f: 
        graph_json = json.load(f)

    result = check_fat_module(json_object=graph_json) 
    print(result) 


if __name__ == "__main__": 
    main() 