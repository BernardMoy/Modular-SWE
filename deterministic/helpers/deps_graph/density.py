from ...reusables.get_all_modules import get_all_modules 
import networkx as nx 

def get_density(json_object): 
    """
    Return 
    Number of edges and transitive dependencies / Number of possible edges
    """

    # Construct networkx graph 
    G = nx.DiGraph() 
    all_modules = get_all_modules(json_object) 
    N = len(all_modules)
    G.add_nodes_from(all_modules) 
    for src, dests in json_object.items(): 
        for dest in dests: 
            G.add_edge(src, dest) 
    
    # Count the number of transitive dependencies
    transitive_dependencies = {v: nx.descendants(G, v) for v in G}
    transitive_dependencies_n = sum(len(d) for d in transitive_dependencies.values())

    all_possible = N*(N-1)  # Undirected graph

    return transitive_dependencies_n / all_possible