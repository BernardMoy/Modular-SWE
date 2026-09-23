"""
Smells sorting for better formatting 
"""

d = {"Function level": 0, "Module level": 1, "Design level": 2}

def sort_smells(smells):
    """
    Sort smells by category: Function level --> Module level --> Design level --> No or unrecognised category
    """
    return sorted(
        smells,
        key=lambda s: (
            50 if ("Category" not in s or s["Category"] not in d) else d[s["Category"]]
        ),
    )
