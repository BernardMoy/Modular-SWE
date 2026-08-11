def code_quality_pass_fail(analyzer_output_json): 
    """
    Based on the analyzer result (returns 5 software quality aspects in scale of 1-5)
    Decide pass / fail. 
    
    1. None of the aspects should fall below 3 
    2. Sum of scores should be greater than a threshold (18) out of 25
    """

    THRESHOLD_ANY_ASPECT = 4   # Cant be less than this 
    THRESHOLD_SUM = 20  # Sum has to be greater or equal to this 

    aspects = ["Readability", "Simplicity", "Maintainability", "Modularity", "Reusability"]
    scores = [int(analyzer_output_json[x]["score"]) for x in aspects]

    return (not any(x<THRESHOLD_ANY_ASPECT for x in scores) and sum(scores) >= THRESHOLD_SUM)