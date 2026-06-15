import json 
import argparse 
from ...reusables.get_all_modules import get_all_modules

def bfs(deps_graph_json): 
    """
    This assumes the dependency graph has no cycles. 

    Return an array of array, each containing modules on a layer
    that can be implemented in parallel. 
    The implementation starts from the layer with no dependencies (out degree = 0)  
    """
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
    return modules 



# Usage: bfs [deps-graph-path] 
def main(): 
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Abs path to the dependency graph JSON file")
    args = parser.parse_args()

    # Read the JSON graph from the path 
    with open(args.path, 'r') as f: 
        graph_json = json.load(f)

    result = bfs(graph_json) 
    print(result) 


if __name__ == "__main__": 
    main() 