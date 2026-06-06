# Given a dependency graph in JSON
# Output the fan in and fan out for each node 
def get_fan_in_fan_out(json_object): 
    """
    Return fan in fan out dict in the format: 
    {
        node1: {
            "fan-in": 5, 
            "fan-out": 5
        }, 
        node2: {
            "fan-in": 5, 
            "fan-out": 5
        }
    }
    """
    d = {} 

    # Initialise the dict with fanin, fanout = 0, 0 
    for key, value in json_object.items(): 
        if key not in d: 
            d[key] = {
                "fan-in": 0, 
                "fan-out": 0
            }
        
        for v in value: 
            if v not in d: 
                d[v] = {
                    "fan-in": 0, 
                    "fan-out": 0
                }

    # Add the fan in (in-degree) and the fan out (out-degree) 
    for key, value in json_object.items(): 
        # value length = fan out of key 
        d[key]["fan-out"] = len(value) 

        # For the in degree of value, increment 
        for v in value: 
            d[v]["fan-in"] += 1   # The 1 fan in is from the key
    
    return d 
    
