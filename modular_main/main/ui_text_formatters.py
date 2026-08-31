"""
Format raw json files etc.
Into a more human readable format
Used to display in the UI

workspace parameter is the Agent workspace path.


FOLLOW CONVENTION: THE DICT HERE {KEY, VALUE}
MEANS THE KEYS (EXACT) ARE DISPLAYED ON THE LEFT PANEL
VALUES ON THE RIGHT
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
    formatted.append("\nPostconditions: ")
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
    l = []
    if analyzer_path.exists(): 
        with open(analyzer_path, "r") as f:
            analyzer_json = json.load(f)

            # For each design json:
            # { module_name, description, status }

            for i, entry in enumerate(analyzer_json):
                description = entry["smell"] + "\n\n" + entry["improvement_instruction"]
                l.append(
                    {
                        # "index": i,
                        "modules": entry["module_name"],
                        "description": description,
                        "status": entry["status"],
                        "feedback": entry.get("feedback", ""),
                    }
                )
    return l


# Obtain deps graph formatted into dict with keys "Current graph" and "Original graph"
def get_formatted_deps_graph(workspace):
    current = Path(workspace) / "current_deps_graph.svg"
    original = Path(workspace) / "original_deps_graph.svg"

    result = {}
    if current.exists():
        result["Current graph"] = current
    if original.exists():
        result["Original graph"] = original

    return result


# Function to process the human question and write it to the human response
def write_formatted_human_question_response(workspace, request_id, response):
    response_path = Path(workspace) / "human_response.json"

    # if the response is empty, change it to 'a'
    if not response.strip():
        response = "a"

    with open(response_path, "w") as f:
        json.dump({"request_id": request_id, "response": response}, f, indent=2)


# Function to process the table of analyzer results and write it to human response
# and also update the analyzer result.json to reflect the changes
def write_formatted_human_analyzer_approval(
    workspace, request_id, response_list, additional_feedback
):
    """
    Write a single string to the human reply in the format

    Modules: ...
    Description: ...
    Feedback: ...

    Modules: ...
    Description: ...
    Feedback: ...

    Additional feedback: ...
    """

    workspace = Path(workspace)
    analyzer_path = workspace / "current_analyzer_result.json"

    if analyzer_path.exists():
        with open(analyzer_path, "r") as f:
            analyzer_json = json.load(f)
    else:
        analyzer_json = []

    # 1: Iterate the response list, AND DEPENDING ON THE INDEX (THE LITERAL ORDER, NOT THE INDEX FIELD FOR NOW)
    # update its status.
    # This index dependent order cause the list to not be able to be sorted in display: to be fixed. See ui.py, same message.
    for i, response in enumerate(response_list):
        if "status" in response:
            analyzer_json[i]["status"] = response["status"]

    with open(analyzer_path, "w") as f:
        json.dump(analyzer_json, f, indent=2)

    # 2. Generate a feedback string that is fed back to the LLM
    # Extract all analyzer results with feedback present
    human_responses = []
    for i, entry in enumerate(response_list):
        feedback = entry.get("feedback", "").strip()
        if feedback:
            human_responses.append(f"""Modules: {entry["modules"]}
Description: {entry["description"]}
Feedback: {entry["feedback"]}""")

    # append the additional feedback if it is present, else leave human responses empty
    if additional_feedback.strip():
        human_responses.append(f"Additional feedback: {additional_feedback}")

    response_text = (
        "\n\n".join(human_responses) if human_responses else "a"
    )  # return a if none has feedback

    with open(workspace / "human_response.json", "w") as f:
        json.dump({"request_id": request_id, "response": response_text}, f, indent=2)


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
