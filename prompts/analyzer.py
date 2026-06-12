from .json_helper import get_json_string

# custom smells are smells identified from the dependency graph, when real code is not available yet 
# designite python smells are smells identified by dpy on real code. 
# Only EITHER custom smells OR dpy smells should be provided. 

# Second iteration simply refers to whether it is the first call to the analyzer. 
# If second iteration is true, then current design contains old + new modules
# as well as rejected designs 

"""
Input: current_design, current_deps_graph, current_rejected_improvements
Output: current_analyzer_result, pass / fail string (Returned) 
"""
def get_analyzer_prompt(second_iteration = False): 
    
    return f"""
You are a senior software code quality analyst. 

Your job is to analyse the following {"modular design including kept, changed or new modules" if second_iteration else "existing modules"}: 
Project root: agent_workspace
File: `current_design.json`

In addition, you are given the dependency graph in `current_deps_graph.json`, and a list of flagged code smells in `current_metrics`. While they do not necessarily mean refactoring is needed, they may guide you in providing improvement suggestions. 
{"You are also given a list of previously suggested improvements that are rejected in `current_rejected_improvements.json`." if second_iteration else ""}

Write a JSON object to `current_analyzer_result.json`, decsribing improvement suggestions to the modules, using the following schema. If a module does not require refactoring, do not include it in the output. If no modules need refactoring, return an empty array. 
{get_json_string("analyzer")}

Also, evaluate the result that is either "pass" or "fail", on whether the current design is suitable for implementation by having good code quality and long term maintainability. Return ONLY the result and reason if it fails, following the schema below, do not include other natural language descriptions in your response. 
{get_json_string("analyzer_pass_fail")}
"""