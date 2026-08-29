"""
Format raw json files etc.
Into a more human readable format
Used to display in the UI

workspace parameter is the Agent workspace path.
"""

from pathlib import Path
import json
import os


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

    precond = public_interface["preconditions"]
    postcond = public_interface["postconditions"]

    return f"""- {function_sig}
{public_interface["description"]}

Preconditions: {'\n'+'\n'.join(precond) if len(precond) > 0 else "None"}
Postconditions:{'\n'+'\n'.join(postcond) if len(postcond) > 0 else "None"}"""


def get_formatted_design(workspace):
    # read from design file
    design_path = Path(workspace) / "current_design.json"
    with open(design_path, "r") as f:
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
    d = {}

    # Add all the old files to the dictionary
    for root, dirs, files in os.walk(impl_path):
        for f in files:
            if f.endswith(".py"):
                py_file_path = Path(root) / f

                # open the file
                try:
                    code = open(py_file_path, "r").read()
                    rel_path = py_file_path.relative_to(impl_path)
                    d[rel_path] = code
                except Exception as e:
                    continue
    return d


def get_formatted_analyzer_suggestions(workspace):
    analyzer_path = Path(workspace) / "current_analyzer_result.json"

    # read from analyzer
    with open(analyzer_path, "r") as f:
        analyzer_json = json.load(f)

        # For each design json:
        # { module_name, description, status }

        l = []
        for entry in analyzer_json:
            description = entry["smell"] + "\n\n" + entry["improvement_instruction"]
            l.append(
                {
                    "module_name": entry["module_name"],
                    "description": description,
                    "status": entry["status"],
                }
            )
    return l


if __name__ == "__main__":
    # for name, doc in get_formatted_design(
    #     Path("agent_workspace")
    # ).items():
    #     print(f"{'='*60}")
    #     print(name)
    #     print(f"{'='*60}")
    #     print(doc)
    #     print()

    # for name, doc in get_formatted_implementation(
    #     Path("agent_workspace")
    # ).items():
    #     print(f"{'='*60}")
    #     print(name)
    #     print(f"{'='*60}")
    #     print(doc)
    #     print()
    pass
