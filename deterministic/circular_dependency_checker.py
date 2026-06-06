import argparse 
import json

# Given a dependency graph in JSON
# Return whether or not it contains a cycle (= circular dependency) 
def check_circular_dependency(json_object): 
    def dfs(graph, node, visited, recStack): 
        # Base case: node already visited 
        if node in recStack: 
            return True 
        
        # If the node has been previously processed return False 
        if node in visited: 
            return False 
        
        visited.add(node) 

        # Add to the stack before rec 
        recStack.add(node) 
        
        if node not in graph: 
            return False 
        
        for neighbour in graph[node]:
            if dfs(graph, neighbour, visited, recStack): 
                return True 
            
        # Remove after rec 
        recStack.remove(node) 
        return False 
    
    visited = set() 
    recStack = set() 

    # For every node, check if a cycle is reachable from there 
    nodes = set() 
    for key, value in json_object.items(): 
        nodes.add(key) 
        for v in value: 
            nodes.add(v) 
    
    for n in nodes: 
        if (dfs(json_object, n, visited, recStack)): 
            return True 
    
    return False 


# usage: check.py [abs-path]
def main(): 
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Abs path to the dependency graph JSON file")
    args = parser.parse_args()

    # Read the JSON graph from the path 
    with open(args.path, 'r') as f: 
        graph_json = json.load(f)

    result = check_circular_dependency(json_object=graph_json) 
    print(result) 


if __name__ == "__main__": 
    main() 