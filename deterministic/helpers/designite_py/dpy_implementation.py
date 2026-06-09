def get_metrics_from_dpy_implementation(dpy_implementation_smells): 
    """
    1. Magic number 
    Return in the same format.
    """
    smells = [] 
    for entry in dpy_implementation_smells: 
        if entry["Smell"] == "Magic number": 
            smells.append({
                "Package": entry["Package"],
                "Module": entry["Module"], 
                "Class": entry["Class"], 
                "Method": entry["Method"], 
                "Smell": "Magic number", 
                "Description": entry["Description"]  # copy the desc is fine 
            })
    return smells 