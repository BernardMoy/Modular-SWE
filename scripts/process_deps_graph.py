import networkx as nx
import json
import argparse
from reusables.get_all_modules import get_all_modules

# clean the graphviz names containing \\
def clean(name): 
    return name.strip('"').replace("\\n", "").replace("\\", "")

def get_name(G, node): 
    # label only exists when networkX cleans the string in a way that is different to the original
    # pipeline --> Label = None 
    # pipeline.a --> pipeline_a 
    name = G.nodes[node].get("label", node)  
    name = clean(name) 
    return name 

# Given a dot file path and an output path, convert the .dot graph into more agent-readable JSON adjacency list format. 
# when doing this make sure to explain what the arrow means (A --> B means B imports A by default)
def main(): 
    parser = argparse.ArgumentParser()

    # path is the path of the graph (in .dot format), 
    # -o is the output file destination 
    parser.add_argument("path")
    parser.add_argument("-o")

    args = parser.parse_args()

    # Read the graphviz path .dot file 
    try: 
        G = nx.nx_pydot.read_dot(args.path) 
    except FileNotFoundError:
        print(f"File not found: {args.path}")
    
    # build the adjacency list 
    graph = {} 
    for n in G.nodes: 
        # get the name of the node 
        name = get_name(G, n) 
        graph[name] = [get_name(G, x) for x in list(G.successors(n))]
    
    # Count the number of modules in the deps graph
    # Warning if it is empty 
    module_count = len(get_all_modules(graph))
    if module_count >0: 
        print(f"Dependency graph has {module_count} modules.")
    else: 
        print("WARNING: DEPENDENCY GRAPH IS EMPTY.")

    # Write as JSON 
    output = args.o
    with open(output, 'w') as f: 
        json.dump(graph, f, indent=2, sort_keys=True)
        # print(f"Written to {output}.")

if __name__ == "__main__":
    main()