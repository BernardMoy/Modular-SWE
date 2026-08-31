import argparse
import json


# Given a dependency graph in JSON
# Return whether or not it contains a cycle (= circular dependency)
def check_circular_dependency(json_object):
    """
    Return in the format
    [
        {
            "Category": "Design level",
            "Smell": "Circular dependency",
            "Description": "Module A -> Module B -> ... ."
        },
    ]

    """

    def dfs(graph, node, visited, recStack, path):
        # Base case: node already visited
        if node in recStack:
            if node not in path:
                return None

            # find the pos of the node in the path
            start = path.index(node)
            return path[start:] + [node]

        # If the node has been previously processed return False
        if node in visited:
            return None

        visited.add(node)

        # Add to the stack before rec
        recStack.add(node)

        # Add to the path
        path.append(node)

        if node not in graph:
            return False

        for neighbour in graph[node]:
            res = dfs(graph, neighbour, visited, recStack, path)
            if res:
                return res

        # Remove after rec
        recStack.remove(node)

        # Remove from the path
        path.pop()
        return None

    visited = set()
    recStack = set()

    # For every node, check if a cycle is reachable from there
    nodes = set()
    for key, value in json_object.items():
        nodes.add(key)
        for v in value:
            nodes.add(v)

    circulars = []
    for n in nodes:
        res = dfs(json_object, n, visited, recStack, [])
        if res:
            circulars.append(
                {
                    "Category": "Design level",
                    "Smell": "Circular dependency",
                    "Description": " -> ".join(res),
                }
            )

    return circulars


# usage: check.py [abs-path]
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Abs path to the dependency graph JSON file")
    args = parser.parse_args()

    # Read the JSON graph from the path
    with open(args.path, "r") as f:
        graph_json = json.load(f)

    result = check_circular_dependency(json_object=graph_json)
    print(result)


if __name__ == "__main__":
    main()
