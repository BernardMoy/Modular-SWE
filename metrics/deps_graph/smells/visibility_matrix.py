from reusables.get_all_modules import get_all_modules
import networkx as nx

"""
Obtain the visibility matrix of a dependency graph: 
it specifies what modules are transitively affected when one changes. 

Example: (A->B means A depends on B)
A -> B, D, B -> C

Note that A depends on B means that change in B affect A.

The matrix will be in the form: 
(It contains every node).
{
    A: []
    B: [A]
    C: [B, A]
    D: [A]
}
"""


def get_visibility_matrix(deps_graph):
    # Construct networkx graph
    G = nx.DiGraph()
    all_modules = get_all_modules(deps_graph)
    G.add_nodes_from(all_modules)
    for src, dests in deps_graph.items():
        for dest in dests:
            G.add_edge(dest, src)  # Add the reverse direction

    transitive_dependencies = {v: sorted(nx.descendants(G, v)) for v in G}
    return transitive_dependencies
