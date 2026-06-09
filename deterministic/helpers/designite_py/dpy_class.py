def get_metrics_from_dpy_class(dpy_class_module_metrics): 
    """
    1. High LCOM 
    2. Complex class (WMC) 
    3. Fat module (NOPM) 
    4. Hub like modularisation
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
    FAN_IN_THRESHOLD = 7 
    FAN_OUT_THRESHOLD = 7

    smells = [] 
    for entry in dpy_class_module_metrics: 
        if entry["LCOM"] >= LCOM_THRESHOLD: 
            smells.append({
                "Package": entry["Package"],
                "Module": entry["Module"], 
                "Class": entry["Class"], 
                "Smell": "High LCOM", 
                "Description": f"The module {entry['Module']} has a high LCOM value of {entry['LCOM']}, indicating it might be violating single responsibility."
            })
        
        if entry["WMC"] >= WMC_THRESHOLD: 
            smells.append({
                "Package": entry["Package"],
                "Module": entry["Module"], 
                "Class": entry["Class"], 
                "Smell": "Complex class", 
                "Description": f"The module {entry['Module']} has a high WMC value of {entry['WMC']}, making it difficult to maintain and test."
            })
        
        if entry["NOPM"] >= NOPM_THRESHOLD: 
            smells.append({
                "Package": entry["Package"],
                "Module": entry["Module"], 
                "Class": entry["Class"], 
                "Smell": "Fat module", 
                "Description": f"The module {entry['Module']} has a high number of public methods ({entry['NOPM']}), indicating insufficient modularisation."
            })
        
        if entry["Fan-In"] >= FAN_IN_THRESHOLD and entry["Fan-Out"] >= FAN_OUT_THRESHOLD: 
            smells.append({
                "Package": entry["Package"],
                "Module": entry["Module"], 
                "Class": entry["Class"], 
                "Smell": "Hub-like Modularisation", 
                "Description": f"Module {entry['Module']} may have hub-like modularization with fan-in={entry['fan-in']}, fan-out={entry['fan-out']}. "
            })
        
    return smells