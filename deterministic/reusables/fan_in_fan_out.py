from deterministic.reusables.get_all_modules import get_all_modules

# Given a dependency graph in JSON
# Output the fan in and fan out for each node 
def get_fan_in_fan_out(json_object): 
    """
    Return dict with fanin, fanout, instability in the format: 
    {
        node1: {
            "fan-in": 5, 
            "fan-out": 5, 
            "instability": 0.5
        }, 
        node2: {
            "fan-in": 5, 
            "fan-out": 5, 
            "instability": 0.5
        }
    }
    """
    d = {} 

    # Initialise the dict with fanin, fanout = 0, 0 for all modules 
    all_modules = get_all_modules(json_object)
    for module in all_modules: 
        d[module] = {
                "fan-in": 0, 
                "fan-out": 0,
                "instability": 0
            }

    # Add the fan in (in-degree) and the fan out (out-degree) 
    for key, value in json_object.items(): 
        # value length = fan out of key 
        d[key]["fan-out"] = len(value) 

        # For the in degree of value, increment 
        for v in value: 
            d[v]["fan-in"] += 1   # The 1 fan in is from the key
    
    # For each of the items in the dict, calculate the instability 
    # Defaults to 0 if both fan in and fan out is 0 
    for key, value in d.items(): 
        if value["fan-in"]+value["fan-out"]>0: 
            d[key]["instability"] = value["fan-out"]/(value["fan-in"]+value["fan-out"])

    return d 
    
