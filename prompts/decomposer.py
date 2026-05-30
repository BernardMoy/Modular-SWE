import json
from .json_helper import get_json_string

# The implementation path is not needed. 
# Reading the existing code is not the responsibility of this agent. 

# Writes: current_design.json, current_deps_graph.json, current_rejected_improvements.json
def get_decomposer_prompt(checkpoint_number, analyzer_improvements = None, second_iteration = False): 
    # Whether current_designs and current_deps_graph exists 
    hasPrevDesign = checkpoint_number > 1 or second_iteration

    return f"""
You are a senior software engineer that specialises in modular software design.

You are working on the following issue:
Project root: agent_workspace
Issue path: checkpoint_{checkpoint_number}.md
{f"The issue is built on top of checkpoint_{checkpoint_number-1}/." if checkpoint_number > 1 else ""}

{"You are also given the current modules design in the file `current_designs.json`, prioritise reusing existing modules instead of creating a new module where possible." if hasPrevDesign else ""}
{"The current modular design is visualised by the following dependency graph in `current_deps_graph.json`." if hasPrevDesign else ""}
{"In addition, you are given a list of improvement suggestions on existing modules, please factor them in your design together with the new modules if the improvement would improve code quality in the long run, or reject it if the improvement is not applicable." if analyzer_improvements else ""}
{json.dumps(analyzer_improvements, indent=2) if analyzer_improvements else ""}

Propose a modular design, each with a single responsibility, that when integrated together, achieve the goal specified in the issue.

Overwrite the JSON object in `current_design.json` by including all modules in your design, that can either be kept, changed or new, using the following schema.
{get_json_string("decomposer")}

Also, {"update" if hasPrevDesign else "create"} the dependency graph in `current_deps_graph.json`. 

"""
