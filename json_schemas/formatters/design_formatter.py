def get_design_summary(design_json):
    kept = []
    changed = []
    new = []

    for entry in design_json:
        if entry["type"] == "keep":
            kept.append(entry["module_name"])
        elif entry["type"] == "chanegd":
            changed.append(entry["module_name"])
        elif entry["type"] == "new":
            new.append(entry["module_name"])

    kept.sort()
    changed.sort()
    new.sort()

    return f"""
Kept modules ({len(kept)}): 
{'\n'.join([f"- {x}" for x in kept])}

Changed modules ({len(changed)}): 
{'\n'.join([f"- {x}" for x in changed])}

New modules ({len(new)}): 
{'\n'.join([f"- {x}" for x in new])}
"""
