import argparse 
import json

# Given a dependency graph in JSON
# Return whether or not it contains an isolated node 
# May change this to "whether it is reachable from the ENTRYPOINT NODE" 
# If we can confirm that the SCB dataset will be used and is the only dataset used. 
# UNUSED - too many false positives, and it has never been flagged as a real issue 
def check_isolated_node(json_object): 
    return [] 
    # """
    # Return in the format, for all isolated modules.
    # [
    #     {
    #         "Category": "Design level",  
    #         "Module": "...", 
    #         "Smell": "This module is isolated."
    #     }, 
    #     ...
    # ]
    # """
    # isolated = [] 

    # # Set of nodes reachable by others 
    # reached = set() 
    # for value in json_object.values():
    #     for v in value: 
    #         reached.add(v) 
    
    # # For any key, if not reachable and have no reaching nodes, then it is isolated 
    # for key, value in json_object.items(): 
    #     if key not in reached and len(value) == 0: 
    #         isolated.append({
    #             "Category": "Design level",  
    #             "Module": key, 
    #             "Smell": "This module is isolated."
    #         }, 
    #     )

    # return isolated 
    


# usage: check.py [abs-path]
def main(): 
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Abs path to the dependency graph JSON file")
    args = parser.parse_args()

    # Read the JSON graph from the path 
    with open(args.path, 'r') as f: 
        graph_json = json.load(f)

    result = check_isolated_node(json_object=graph_json) 
    print(result) 


if __name__ == "__main__": 
    main() 