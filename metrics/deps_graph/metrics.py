from metrics.deps_graph.smells.circular_dependency_checker import check_circular_dependency
from metrics.deps_graph.smells.isolated_node_checker import check_isolated_node
from metrics.deps_graph.smells.unstable_dependency_checker import check_unstable_dependency
from metrics.deps_graph.smells.hub_like_modularisation_checker import check_hub_like_modularisation

def get_metrics_from_deps_graph(deps_graph_json): 
    """
    Get metrics from dependency graph using deterministic helper methods. 
    Prioritise getting metrics from dpy.

    Here are the metrics only obtainable from deps graph: 
    1. Unstable dependencies 
    2. Circular import 
    3. Isolated module 
    4. Hub like modularisation
    """

    deps_graph_metrics = [] 

    # Check circular dependency (Must fail) 
    deps_graph_metrics.extend(check_circular_dependency(deps_graph_json))
    
    # Check isolated node (Must fail)  
    deps_graph_metrics.extend(check_isolated_node(deps_graph_json))

    # Check unstable dependency
    deps_graph_metrics.extend(check_unstable_dependency(deps_graph_json))

    # check hub like 
    deps_graph_metrics.extend(check_hub_like_modularisation(deps_graph_json))

    return deps_graph_metrics