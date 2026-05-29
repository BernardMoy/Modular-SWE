from .json_helper import get_json_string

# Give the CURRENT checkpoint number (the one you are working on)! 
def get_reader_prompt(checkpoint_number): 
    return f"""
You are a senior software engineer that analyses modules in a software project.

Your job is to understand the following directory: 
Project root: agent_workspace
Directory: checkpoint_{checkpoint_number-1}/
Dependency graph: checkpoint_{checkpoint_number-1}_graph.json

Identify the existing modules in the codebase, using the dependency graph as reference. For each module, identify its responsibility. Do not propose new modules.

Output a JSON object that describes each module, using the following schema. If there are no modules, return an empty JSON array.

{get_json_string("reader")}

Return only the JSON object, do not include any additional natural language text in your response.
"""
