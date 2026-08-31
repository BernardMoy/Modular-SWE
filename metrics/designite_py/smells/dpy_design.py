def get_metrics_from_dpy_design(dpy_design_smells):
    """
    1. Feature envy
    2. Intrusive coupling / Protected access
    3. Insufficient modularization
    """
    smells = []

    # Directly copy from the dpy metrics is fine here
    for entry in dpy_design_smells:
        if entry["Smell"] == "Feature envy":
            smells.append(
                {
                    "Category": "Design level",
                    "Package": entry["Package"],
                    "Module": entry["Module"],
                    "Class": entry["Class"],
                    "Smell": "Feature envy",
                    "Description": entry["Description"],
                }
            )

        if entry["Smell"] == "Deficient encapsulation":
            smells.append(
                {
                    "Category": "Design level",
                    "Package": entry["Package"],
                    "Module": entry["Module"],
                    "Class": entry["Class"],
                    "Smell": "Access to protected members",
                    "Description": entry["Description"],
                }
            )

        if entry["Smell"] == "Insufficient modularization":
            smells.append(
                {
                    "Category": "Design level",
                    "Package": entry["Package"],
                    "Module": entry["Module"],
                    "Class": entry["Class"],
                    "Smell": "Insufficient modularisation",
                    "Description": entry["Description"],
                }
            )

    return smells
