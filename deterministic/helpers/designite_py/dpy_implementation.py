def get_metrics_from_dpy_implementation(dpy_implementation_smells): 
    """
    1. Magic number 
    Return in the same format.
    """
    # Ignored due to too many false positives. 
    
    smells = [] 
    # for entry in dpy_implementation_smells: 
    #     if entry["Smell"] == "Magic number": 
    #         smells.append({
    #             "Category": "Function level", 
    #             "Package": entry["Package"],
    #             "Module": entry["Module"], 
    #             "Class": entry["Class"], 
    #             "Method": entry["Method"], 
    #             "Smell": "Magic number", 
    #             "Description": entry["Description"]
    #         })
    return smells 