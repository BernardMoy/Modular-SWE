def get_metrics_from_dpy_design(dpy_design_smells): 
    """
    1. Feature envy
    2. Intrusive coupling / Protected access
    Return in the format [
        {
            "Package": ..., 
            "Module": ..., 
            "Class": ..., 
            "Smell": "High LCOM", 
            "Description": "The module _ has a high LCOM value of _, indicating it might be violating single responsibility."
        }
    ]
    """
    smells = [] 

    # Directly copy from the dpy metrics is fine here 
    for entry in dpy_design_smells: 
        if entry["Smell"] == "Feature envy": 
            smells.append({
                "Package": entry["Package"],
                "Module": entry["Module"], 
                "Class": entry["Class"], 
                "Smell": "Feature envy",
                "Description": entry["Description"]
            })


        if entry["Smell"] == "Deficient encapsulation":
            smells.append({
                "Package": entry["Package"],
                "Module": entry["Module"],
                "Class": entry["Class"],
                "Smell": "Access to protected members",
                "Description": entry["Description"]
            })

    return smells 

