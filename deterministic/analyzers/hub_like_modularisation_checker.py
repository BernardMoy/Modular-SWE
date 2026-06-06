import argparse 
import json
from ..helpers.fan_in_fan_out import get_fan_in_fan_out

# Given a dependency graph in JSON
# Return all hub-like nodes with fan in, fan out > threshold 
THRESHOLD = 7

def check_hub_like_modularisation(json_object): 
    """
    Return in the format 
    [
        {
            "Module": "...", 
            "Smell": "Hub-like Modularization",
            "Description": "Module _ may have hub-like modularization with fan-in=A, fan-out=B. "
        }, 
        ...
    ]
    """

    # obtain the fan in fan out data 
    data = get_fan_in_fan_out(json_object)
    hub_likes = []

    for module, d in data.items(): 
        # Report hub like if fan in and fan out both >= threshold
        if d["fan-in"] >= THRESHOLD and d["fan-out"] >= THRESHOLD: 
            hub_likes.append({
                "Module": module, 
                "Smell": "Hub-like Modularization", 
                "Description": f"Module {module} may have hub-like modularization with fan-in={d['fan-in']}, fan-out={d['fan-out']}. "
            })
    
    return hub_likes
    


# usage: check.py [abs-path]
def main(): 
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Abs path to the dependency graph JSON file")
    args = parser.parse_args()

    # Read the JSON graph from the path 
    with open(args.path, 'r') as f: 
        graph_json = json.load(f)

    result = check_hub_like_modularisation(json_object=graph_json) 
    print(result) 


if __name__ == "__main__": 
    main() 