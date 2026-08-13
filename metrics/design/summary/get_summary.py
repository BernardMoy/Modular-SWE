"""
IMPORTANT INFORMATION

THE DESIGN JSON OLD IS CURRENTLY UNUSED HERE
AND THE SUMMARY IS NOT USED, 

MAINLY BECAUSE ANALYZING THE NEW / OLD INFO
REQUIRES COMPARING INFO ACROSS 2 DIFFERENT TOOLS
AGENT <> DPY
AGENT <> PYDEPS

WHICH IS NOT A FAIR COMPARISON. 
"""

# Given the NEW and OLD design json (NEW one comes first!) (Only the old one is available in the first checkpoint) 
# Return the summary 
def get_summary(design_json_new, design_json_old = None): 
    """
    Return in the format [
        {
            "number_of_modules": {
                "new_value": 20, 
                "change": "+4"
            }, 
            "number_of_public_methods_per_module": {
                "new_value": 20, 
                "change": "+4"
            }
        }
    ]

    Change is only available if the design json new is available. 
    """
    summary = {
                "number_of_modules": {
                    "new_value": 0, 
                }, 
                "number_of_public_methods_per_module": {
                    "new_value": 0, 
                }
            }

    new_total_modules = 0 
    new_total_public_methods = 0 

    for entry in design_json_new: 
        if "public_interface" in entry: 
            new_total_modules += 1 
            new_total_public_methods += len(entry["public_interface"])

    summary["number_of_modules"]["new_value"] = new_total_modules
    summary["number_of_public_methods_per_module"]["new_value"] = new_total_public_methods / new_total_modules if new_total_modules > 0 else "NA"

    if design_json_old: 
        old_total_modules = 0 
        old_total_public_methods = 0 
        for entry in design_json_old: 
            if "public_interface" in entry: 
                old_total_modules += 1 
                old_total_public_methods += len(entry["public_interface"])

        summary["number_of_modules"]["change"] = f"+{new_total_modules-old_total_modules}" if new_total_modules-old_total_modules > 0 else str(new_total_modules-old_total_modules)
        summary["number_of_public_methods_per_module"]["change"] = old_total_public_methods / old_total_modules - new_total_public_methods / new_total_modules if old_total_modules > 0 and new_total_modules > 0 else "NA"

    return summary 