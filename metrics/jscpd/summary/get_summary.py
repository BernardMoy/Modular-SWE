
# Given the NEW and OLD dpy folder paths (NEW one comes first!) (Only the old one is available in the first checkpoint) 
# Return the summary 
from ..overall_metrics import get_duplicates

def get_jscpd_summary(implementation_new, implementation_old = None): 
    """
    Return in the format [
        {
            "duplicated_lines": {
                "new_value": 0.03, 
                "change": "+0.01"
            }
        }
    ]

    Change is only available if the design json new is available. 
    """
    
    new_value = get_duplicates(implementation_path=implementation_new)["lines"]
    summary = {
                    "duplicated_lines": {
                        "new_value": round(
                            get_duplicates(implementation_path=implementation_new)["lines"],
                            2
                        )
                    }
    }

    # if old impl is present then add the change 
    if implementation_old: 
        old_value = get_duplicates(implementation_path=implementation_old)["lines"]
        dup_change = round(new_value-old_value, 2)

        summary["duplicated_lines"]["change"]= f"+{dup_change}" if dup_change > 0 else 0

    return summary 