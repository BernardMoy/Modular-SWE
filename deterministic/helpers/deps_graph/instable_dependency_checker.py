import argparse 
import json
from ...reusables.fan_in_fan_out import get_fan_in_fan_out

# Given a dependency graph in JSON
# Return all dependencies from A to B where B is less stable than A in terms of instability metrics 
def check_instable_dependency(json_object): 
    """
    Return in the format 
    [
        {
            "Category": "Design level",  
            "Module": "...", 
            "Smell": "Dependency on less stable modules",
            "Description": "Module _ is depending on module _, which is less stable. "
        }, 
        ...
    ]
    """

    data = get_fan_in_fan_out(json_object)
    instables = []
   
    for key, value in json_object.items(): 
        for v in value: 
            # Check each dependency from key --> v 
            # Flag if v is less stable than key 
            source_stability = data[key]["instability"]
            dest_stability = data[v]["instability"]

            if dest_stability > source_stability: 
                instables.append({
                    "Category": "Design level",  
                    "Module": key, 
                    "Smell": "Dependency on less stable modules",
                    "Description": f"Module '{key}' (instability: {source_stability}) is depending on module '{v}' (instability: {dest_stability}), which is less stable."
                })

    return instables

# usage: check.py [abs-path]
def main(): 
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Abs path to the dependency graph JSON file")
    args = parser.parse_args()

    # Read the JSON graph from the path 
    with open(args.path, 'r') as f: 
        graph_json = json.load(f)

    result = check_instable_dependency(json_object=graph_json) 
    print(result) 


if __name__ == "__main__": 
    main() 