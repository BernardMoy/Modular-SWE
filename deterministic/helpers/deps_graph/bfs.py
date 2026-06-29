import json 
import argparse 
from ...reusables.get_all_modules import get_all_modules

def bfs(deps_graph_path, design_path): 
    """
    This assumes the dependency graph has no cycles. 
    This also assumes the design json strictly follow the rules below for keep, changed or new modules: 
    (1) HAS CONCRETE IMPLEMENTATION? --> YES GOTO (2) NO 'new' 
    (2) CHANGED? --> YES 'changed' NO 'keep' 
    Modules not found in the design would be treated as new. 

    Return an array of array, each containing modules on a layer
    that can be implemented in parallel. 
    The implementation starts from the layer with no dependencies (out degree = 0)  
    """

    # Read the JSON graph from the path 
    with open(deps_graph_path, 'r') as f: 
        deps_graph_json = json.load(f)
    
    with open(design_path, 'r') as f: 
        design_json = json.load(f)

    all_modules = get_all_modules(deps_graph_json)
    
    visited = set()
    s = set(all_modules)

    modules = []

    # while there are unvisited modules,
    # repeatedly find unvisited nodes whose dependencies are ALL visited
    # thats when we can implement that module and mark it as visited 
    while len(visited) != len(all_modules):
        cur = []

        # for each unvisited module, if all its dependencies 
        for module in s - visited:
            if all(x in visited for x in deps_graph_json.get(module, [])):
                cur.append(module)

        # after processing all the new modules, then mark them as visited 
        for x in cur:
            visited.add(x)

        modules.append(cur)
    
    # filter all_modules by only keeping the new or changed modules that need to be implemented 
    # do this at the end to ensure all bfs paths are covered first 
    types = {} 
    for module in design_json: 
        types[module["module_name"]] = module["type"]
    
    for i, module_list in enumerate(modules): 
        modules[i] = [x for x in module_list if types[x] in ["changed", "new"]]
    
    # remove all empty arrays after doing this 
    return [x for x in modules if len(x) > 0]



# Usage: bfs [deps-graph-path] [design-path]
def main(): 
    parser = argparse.ArgumentParser()
    parser.add_argument("deps_graph_path", help="Abs path to the dependency graph JSON file")
    parser.add_argument("design_path", help="Abs path to the design JSON file")
    args = parser.parse_args()

    result = bfs(args.deps_graph_path, args.design_path) 
    print(result) 


if __name__ == "__main__": 
    main() 