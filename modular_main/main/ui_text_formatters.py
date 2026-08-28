"""
Format raw json files etc.
Into a more human readable format
Used to display in the UI

workspace parameter is the Agent workspace path. 
"""
from pathlib import Path 
import json 

def _format_public_interface(public_interface): 
    name = public_interface["name"]
    returns = public_interface.get("returns", "void")

    params = []
    for p in public_interface.get("parameters", []):
        param_str = f"{p['name']}: {p['type']}"
        if p.get("optional", False):
            param_str += "?"
        params.append(param_str)

    function_sig = f"{name}({', '.join(params)}) -> {returns}"

    return f"""- {function_sig}
Preconditions:
{'\n'.join(public_interface["preconditions"])}
Postconditions:
{'\n'.join(public_interface["postconditions"])}"""

def get_formatted_design(workspace):  
    # read from design file 
    design_path = Path(workspace) / "current_design.json"
    with open(design_path, 'r') as f: 
        design_json = json.load(f) 

        # For each design json: 
        # Key = (type) module name
        # Value = Responsibility \n\n public interface 1 \n public interface 2 \n ...

        d = {} 
        for entry in design_json: 
            key = f"({entry["type"]}) {entry["module_name"]}"
            value = f"{entry["responsibility"]}\n\n{'\n\n'.join(
                [_format_public_interface(x) for x in entry["public_interface"]]
            )}"

            d[key] = value 
    return d 

def get_formatted_implementation(workspace): 
    # read from impl directory 
    impl_path = Path(workspace) / "implementation"
    pass 

def get_formatted_analyzer_suggestions(workspace): 
    analyzer_suggestions_path = Path(workspace) / "current_analyzer_result.json"
    pass 



if __name__ == "__main__": 
    for name, doc in get_formatted_design(
        Path("agent_workspace")
    ).items():
        print(f"{'='*60}")
        print(name)
        print(f"{'='*60}")
        print(doc)
        print()