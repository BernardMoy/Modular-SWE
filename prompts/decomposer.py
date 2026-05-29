from .json_helper import get_json_string

# The implementation path is not needed. 
# Reading the existing code is not the responsibility of this agent. 
def get_decomposer_prompt(checkpoint_number, existing_modules, analyzer_improvements): 
    return f"""
You are a senior software engineer that specialises in modular software design.

You are working on the following issue:
Project root: agent_workspace
Issue path: checkpoint_{checkpoint_number}.md
The issue is built on top of checkpoint_{checkpoint_number-1}/. 

You are also given a list of existing modules below, prioritise reusing them instead of creating a new module where possible: 
{existing_modules}

The existing modules are visualised by the following dependency graph. 
Dependency graph: checkpoint_{checkpoint_number-1}_graph.json

In addition, you are given a list of improvement suggestions on existing modules, please factor them in your design together with the new modules. 
{analyzer_improvements}

Propose a modular design, each with a single responsibility, that when integrated together, achieve the goal specified in the issue.

Output a JSON object including all modules, that can either be kept, changed or new, and describes what each module depends on using a new dependency graph, using the following schema. 
{get_json_string("decomposer")}

Return only the JSON object, do not include any additional natural language text in your response.

"""
