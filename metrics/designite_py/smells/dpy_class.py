def get_metrics_from_dpy_class(dpy_class_module_metrics):
    """
    1. High LCOM
    2. Complex class (WMC) - IGNORED because too many false positives
    3. Fat module (NOPM) - IGNORED because handled in design stage
    4. Hub like modularisation - IGNORED because handled in design stage
    Return in the format [
        {
            "Category": "Module level",
            "Package": ...,
            "Module": ...,
            "Class": ...,
            "Smell": "High LCOM",
            "Description": "The module _ has a high LCOM value of _, indicating it might be violating single responsibility."
        }
    ]
    """
    LCOM_THRESHOLD = 0.7
    LCOM_NOM_THRESHOLD = 5
    WMC_THRESHOLD = 50
    NOPM_THRESHOLD = 20
    FAN_IN_THRESHOLD = 7
    FAN_OUT_THRESHOLD = 7

    smells = []
    for entry in dpy_class_module_metrics:
        # LCOM high is considered a smell only when its number of methods is also greater than a threshold
        if entry["LCOM"] >= LCOM_THRESHOLD and entry["NOM"] >= LCOM_NOM_THRESHOLD:
            smells.append(
                {
                    "Category": "Module level",
                    "Package": entry["Package"],
                    "Module": entry["Module"],
                    "Class": entry["Class"],
                    "Smell": "High LCOM",
                    "Description": f"The module '{entry['Module']}' has a high LCOM of {entry['LCOM']}. Only flag this as a problem if it combines distinct responsibilities.",
                }
            )

        # if entry["WMC"] >= WMC_THRESHOLD:
        #     smells.append({
        #         "Category": "Module level",
        #         "Package": entry["Package"],
        #         "Module": entry["Module"],
        #         "Class": entry["Class"],
        #         "Smell": "Complex class",
        #         "Description": f"The module '{entry['Module']}' has a high WMC value of {entry['WMC']}, check if it can be simplified."
        #     })

        # if entry["NOPM"] >= NOPM_THRESHOLD:
        #     smells.append({
        #         "Category": "Module level",
        #         "Package": entry["Package"],
        #         "Module": entry["Module"],
        #         "Class": entry["Class"],
        #         "Smell": "Fat module",
        #         "Description": f"The module '{entry['Module']}' has a high number of public methods ({entry['NOPM']}), indicating insufficient modularisation."
        #     })

        # if entry["Fan-In"] >= FAN_IN_THRESHOLD and entry["Fan-Out"] >= FAN_OUT_THRESHOLD:
        #     smells.append({
        #         "Category": "Design level",
        #         "Package": entry["Package"],
        #         "Module": entry["Module"],
        #         "Class": entry["Class"],
        #         "Smell": "Hub-like Modularisation",
        #         "Description": f"Module '{entry['Module']}' may have hub-like modularization with fan-in={entry['fan-in']}, fan-out={entry['fan-out']}. "
        #     })

    return smells
