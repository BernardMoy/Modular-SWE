from .json_helper import get_json_string

# custom smells are smells identified from the dependency graph, when real code is not available yet 
# designite python smells are smells identified by dpy on real code. 
# Only EITHER custom smells OR dpy smells should be provided. 

# If second iteration is true, then current design contains old + new modules
# as well as rejected designs 
def get_analyzer_prompt(checkpoint_number, second_iteration = False): 
    return f"""
You are a senior software code quality analyst. 

Your job is to analyse the following {"modular design including kept, changed or new modules" if second_iteration else "directory"}: 
Project root: agent_workspace
{"File: current_design.json" if second_iteration else f"Directory: checkpoint_{checkpoint_number-1}/"}
{"You are also given a list of previously suggested improvements that are rejected." if second_iteration else ""}

In addition, you are given the dependency graph in `current_deps_graph.json`, and a list of flagged code smells in `current_metrics/`. While they do not necessarily mean refactoring is needed, they may guide you in providing improvement suggestions. 

Output a JSON object decsribing improvement suggestions to the modules using the following schema. If a module does not require refactoring, do not include it in the output. If no modules need refactoring, return an empty array. 
{get_json_string("analyzer")}

Return only the JSON object, do not include any additional natural language text in your response.
"""