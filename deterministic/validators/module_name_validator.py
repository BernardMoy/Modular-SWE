from ..reusables.get_all_modules import get_all_modules
import argparse
import json 

# Given a design modules with the field "module_name", 
# Validate that the module name appear in the dependenccy graph

# the design file must come from an agent, so we can instruct it to follow the format in dependency graph 
# the dependency graph come from pydeps (1st iteration, N>1 checkpoint) or from agent (>1 iteration) 
def module_name_validator(design_json, deps_graph_json): 
    """
    Return an array of module names in the design file in the format 
    (In the future, hard code the file names as well - change by including `current_design.json` below once thats confirmed)
    [
        {
            "Module": "...", 
            "Description": "Module __, while exist in the current design file, does not exist in the dependency graph."
        }, 
    ]
    that isnt present in the deps graph file 
    """
    # Obtain all modules in the deps graph 
    all_modules = get_all_modules(deps_graph_json) 
    result = [] 

    # For each item in the design json extract the module name 
    for item in design_json: 
        if item["module_name"] not in all_modules: 
            result.append({
                "Module": item['module_name'], 
                "Description": f"Module {item['module_name']}, while exist in the current design file, does not exist in the dependency graph."
            })
    
    return result 

# usage: check.py [abs-design-path] [abs-deps-graph-path]
def main(): 
    parser = argparse.ArgumentParser()
    parser.add_argument("design", help="Abs path to the design JSON file")
    parser.add_argument("deps_graph", help="Abs path to the dependency graph JSON file")
    args = parser.parse_args()

    # Read the JSON graph from the path 
    with open(args.design, 'r') as f:
        design_json = json.load(f)
    with open(args.deps_graph, 'r') as f:
        graph_json = json.load(f)

    result = module_name_validator(design_json=design_json, deps_graph_json=graph_json) 
    print(result) 


if __name__ == "__main__": 
    main() 