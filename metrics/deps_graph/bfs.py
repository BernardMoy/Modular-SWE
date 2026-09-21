"""
Perform a BFS of the dependency graph.
Starting at the node that depends on nothing, 
BFS layer by layer where modules in one layer only depends on modules in previous layers. 
This way the implementation can be done layer by layer. 
"""

import json
import argparse
from reusables.get_all_modules import get_all_modules


def bfs(deps_graph_json):
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

    all_modules = get_all_modules(deps_graph_json)

    visited = set()
    s = set(all_modules)

    modules = []

    # while there are unvisited modules, - this also handles the case where the graph is disconnected
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


def bfs_get_modules_to_implement(deps_graph_json, design_json):
    """
    Also return bfs, but filtered from the design json
    that only returns CHANGED or NEW modules.
    """

    bfs_modules = bfs(deps_graph_json)

    # filter all_modules by only keeping the new or changed modules that need to be implemented
    # do this at the end to ensure all bfs paths are covered first
    types = {}
    for module in design_json:
        types[module["module_name"]] = module["type"]

    for i, module_list in enumerate(bfs_modules):
        bfs_modules[i] = [x for x in module_list if types.get(x, "keep") != "keep"]

    # remove all empty arrays after doing this
    return [x for x in bfs_modules if len(x) > 0]


# Usage: bfs [deps-graph-path] [design-path]
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "deps_graph_path", help="Abs path to the dependency graph JSON file"
    )
    parser.add_argument("design_path", help="Abs path to the design JSON file")
    args = parser.parse_args()

    # Read the JSON graph from the path
    with open(args.deps_graph_path, "r") as f:
        deps_graph_json = json.load(f)

    with open(args.design_path, "r") as f:
        design_json = json.load(f)

    result = bfs_get_modules_to_implement(deps_graph_json, design_json)
    print(result)


if __name__ == "__main__":
    main()
