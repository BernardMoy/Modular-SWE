def get_metrics_from_dpy_function(dpy_function_metrics): 
    """
    1. Complex method / High CC 
    1-10: Simple procedure, little risk
    11-20: More complex, moderate risk
    21-50: Complex, high risk
    > 50: Untestable code, very high risk

    Return in the format [
        {
            "Category": "Function level", 
            "Package": ..., 
            "Module": ..., 
            "Class": ..., 
            "Method": ..., 
            "Smell": "Complex method", 
            "Description": "The method has high cyclomatic complexity of 11".
        }
    ]
    """
    smells = [] 
    CC_THRESHOLD = 11 

    for entry in dpy_function_metrics: 
        if entry["CC"]>=CC_THRESHOLD: 
            smells.append({
                "Category": "Function level", 
                "Package": entry["Package"],
                "Module": entry["Module"], 
                "Class": entry["Class"], 
                "Method": entry["Method"], 
                "Smell": "Complex method", 
                "Description": f"The method has cyclomatic complexity of {entry['CC']}, worth inspecting its readability and testability." if entry["CC"] < 20 else f"The method has high cyclomatic complexity of {entry['CC']}, check if the logic can be refactored into smaller, more readable functions."
            })
        
    return smells 