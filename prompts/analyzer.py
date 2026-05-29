from .json_helper import get_json_string

# custom smells are smells identified from the dependency graph, when real code is not available yet 
# designite python smells are smells identified by dpy on real code. 
# Only EITHER custom smells OR dpy smells should be provided. 
def get_analyzer_prompt(checkpoint_number, modules, custom_smells = None, dpy_smells = None, rejected_improvements = None): 
    return f"""
You are a senior software code quality analyst. 

Your job is to analyse the following directory: 
Project root: agent_workspace
Directory: checkpoint_{checkpoint_number-1}/

You are given a list of existing or new modules below. Some includes suggested improvements. 
{modules}

In addition, you are given the dependency graph and a list of flagged code smells. While they do not necessarily mean refactoring is needed, they may guide you in providing improvement suggestions: 
Dependency graph: checkpoint_{checkpoint_number-1}_graph.json

Flagged code smells: 
{dpy_smells if dpy_smells is not None else (custom_smells if custom_smells is not None else "None.")}

{"The following improvements have been rejected, so please don't consider them in your solution." if rejected_improvements is not None else ""}
{rejected_improvements if rejected_improvements is not None else ""}

Output a JSON object decsribing improvement suggestions to the modules using the following schema. If a module does not require refactoring, do not include it in the output. If no modules need refactoring, return an empty array. 
{get_json_string("analyzer")}

Return only the JSON object, do not include any additional natural language text in your response.
"""