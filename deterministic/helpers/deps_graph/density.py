from ...reusables.get_all_modules import get_all_modules 

def get_density(json_object): 
    """
    Return 
    Number of edges in deps graph / 
    (Number of possible edges / 2) 
    (/2 because dependency is expected to flow in one direction only)
    """

    all_modules = get_all_modules(json_object) 
    N = len(all_modules)
    all_possible = N*(N-1)/4

    edges = 0 
    for key, value in json_object.items(): 
        edges += len(value) 
    
    return edges / all_possible