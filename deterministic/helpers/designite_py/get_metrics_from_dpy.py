def get_metrics_from_dpy_function(dpy_function_metrics): 
    """
    1. Complex method / High CC 
    2. Hub like modularisation
    Return in the format [
        {
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
                "Package": entry["Package"],
                "Module": entry["Module"], 
                "Class": entry["Class"], 
                "Method": entry["Method"], 
                "Smell": "Complex method", 
                "Description": f"The method has high cyclomatic complexity of {entry["CC"]}"
            })
    return smells 

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

def get_metrics_from_dpy_class(dpy_class_module_metrics): 
    """
    1. High LCOM 
    2. Complex class (WMC) 
    3. Fat class (NOPM) 
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
    LCOM_THRESHOLD = 0.8
    WMC_THRESHOLD = 30 
    NOPM_THRESHOLD = 20 
    smells = [] 
    for entry in dpy_class_module_metrics: 
        if entry["LCOM"] >= LCOM_THRESHOLD: 
            smells.append({
                "Package": entry["Package"],
                "Module": entry["Module"], 
                "Class": entry["Class"], 
                "Smell": "High LCOM", 
                "Description": f"The module {entry["Module"]} has a high LCOM value of {entry["LCOM"]}, indicating it might be violating single responsibility."
            })
        
        if entry["WMC"] >= WMC_THRESHOLD: 
            smells.append({
                "Package": entry["Package"],
                "Module": entry["Module"], 
                "Class": entry["Class"], 
                "Smell": "Complex class", 
                "Description": f"The module {entry["Module"]} has a high WMC value of {entry["WMC"]}, making it difficult to maintain and test"
            })
        
        if entry["NOPM"] >= NOPM_THRESHOLD: 
            smells.append({
                "Package": entry["Package"],
                "Module": entry["Module"], 
                "Class": entry["Class"], 
                "Smell": "Fat class", 
                "Description": f"The module {entry["Module"]} has a high number of public methods ({entry["NOPM"]}), indicating insufficient modularisation."
            })
    return smells

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

def get_duplicated_lines_of_code(pylint_output): 
    pass 