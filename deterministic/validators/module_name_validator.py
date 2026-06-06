from ..helpers.get_all_modules import get_all_modules
import argparse
import json 

# Given a design modules with the field "module_name", 
# Validate that the module name appear in the dependenccy graph
# The opposite do not need to necessarily be true. 
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

        # At this stage, TOLERATE module and module.py and treat them as the same
        all_modules_no_suffix = [x.removesuffix(".py") for x in all_modules]
        if item["module_name"].removesuffix(".py") not in all_modules_no_suffix: 
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