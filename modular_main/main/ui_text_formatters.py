"""
Format raw json files etc.
Into a more human readable format
Used to display in the UI

workspace parameter is the Agent workspace path.
"""

from pathlib import Path
import json
import os
from rich.text import Text

# highlight the design public interface in a different color
PUBLIC_INTERFACE_STYLE = "bold #b8baff"

# Files (ignored) that are not displayed on the impl
IGNORED_DIRS = {".venv", "__pycache__", ".git", "dist", "node_modules", ".pytest_cache"}


def _format_public_interface(public_interface) -> Text:
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

    formatted = Text()
    formatted.append("- ")
    formatted.append(function_sig, style=PUBLIC_INTERFACE_STYLE)
    formatted.append("\n")
    formatted.append(public_interface["description"])
    formatted.append("\n\nPreconditions: ")
    formatted.append("\n".join(precond) if precond else "None")
    formatted.append("\nPostconditions:")
    formatted.append("\n".join(postcond) if postcond else "None")
    return formatted


def get_formatted_design(workspace) -> dict[str, Text]:
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
            value = Text(entry.get("responsibility", ""))
            value.append("\n\n")
            for index, public_interface in enumerate(entry.get("public_interface", [])):
                if index:
                    value.append("\n\n")
                value.append(_format_public_interface(public_interface))

            d[key] = value
    return d


def get_formatted_implementation(workspace):
    # read from impl directory
    impl_path = Path(workspace) / "implementation"
    d = {}

    # Add all the old files to the dictionary
    for root, dirs, files in os.walk(impl_path):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        for f in files:
            file_path = Path(root) / f

            # open the file
            try:
                code = open(file_path, "r").read()
                rel_path = str(
                    file_path.relative_to(impl_path)
                )  # keys need to be a string
                # Keep UI keys renderable and consistent with design keys.
                d[rel_path] = Text(code)
            except Exception as e:
                continue
    return d


# Obtain analyzer suggestions formatted to a list
# order matters for the modification from users later
def get_formatted_analyzer_suggestions(workspace):
    analyzer_path = Path(workspace) / "current_analyzer_result.json"

    # read from analyzer
    with open(analyzer_path, "r") as f:
        analyzer_json = json.load(f)

        # For each design json:
        # { module_name, description, status }

        l = []
        for i, entry in enumerate(analyzer_json):
            description = entry["smell"] + "\n\n" + entry["improvement_instruction"]
            l.append(
                {
                    "index": i,  # store the original index inside the json file: For modification. This way the DISPLAYED analyzer suggestions can be sorted.
                    "module_name": entry["module_name"],
                    "description": description,
                    "status": entry["status"],
                }
            )
    return l

# Function to process the human question and write it to the human response 
def write_formatted_human_question_response(workspace, request_id, response): 
    response_path = Path(workspace) / "human_response.json"

    with open(response_path, 'w') as f: 
        json.dump({
            "request_id": request_id, 
            "response": response
        }, f, indent=2)

    

# Function to process the table of analyzer results and write it to human response 
# and also update the analyzer result.json to reflect the changes 
def write_formatted_human_analyzer_approval(workspace): 
    pass 


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
