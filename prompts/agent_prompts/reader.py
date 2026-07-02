from ..json_helper import get_json_string

# Give the CURRENT checkpoint number (the one you are working on)! 
"""
Input: Prev implementation, prev dependency graph
Output: current_design
"""
def get_reader_prompt(checkpoint_number): 
    if checkpoint_number <= 1: 
        return "ERROR - This agent is not needed for the first checkpoint, please return nothing."
    return f"""
You are a senior software engineer that analyses modules in a software project.

Your job is to understand the following directory: 
Project root: agent_workspace
Directory: checkpoint_{checkpoint_number-1}/
Dependency graph: checkpoint_{checkpoint_number-1}_graph.json

Identify the existing modules in the codebase, using the dependency graph as reference. For each module, identify its responsibility. Do not propose new modules.

Write a JSON object to `current_design.json`, that describes each module using the following schema. If there are no modules, write an empty JSON array.
{get_json_string("reader")}

"""
