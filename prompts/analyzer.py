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
Design: `current_design.json`
Dependency graph: `current_deps_graph.json`

A list of flagged code smells have been given in `current_metrics`. 
{"You are also given a list of previously suggested improvements that are rejected in `current_rejected_improvements.json`." if second_iteration else ""}

Interpret the metrics using the following guidelines: 
- LCOM: Only flag if the methods have different responsibilities. It is acceptable if the methods are just sequential stages of the same functionality. 
- Cyclomatic complexity, WMC: Only flag if the complexity is caused by unrelated concerns, lead to low testability, or high maintenance effort when adding new features. It is acceptable if the complex problem logic justifies it. 
- Magic number: Only flag if the meaning of the number is not immediately obvious to the developer. 
- Number of public methods: Only flag if the methods share different responsibilities, or they expose too much internal state that lead to feature envy of another module.  

Write a JSON object to `current_analyzer_result.json`, decsribing improvement suggestions to the modules, using the following schema. If a module does not require refactoring, do not include it in the output. If no modules need refactoring, return an empty array. 
{get_json_string("analyzer")}

Also, evaluate the result that is either "pass" or "fail", based on the following criteria: 
- Modules should be able to independently evolve, with low coupling and high cohesion 
- The system should be easy to test by not having complex functions that could be simplified
- The maintenance effort when introducing new features should be as low as possible by avoiding duplication and ensuring single responsibility

Return ONLY the JSON string below, do not include any additional natural language descriptions in your response. 
{get_json_string("analyzer_pass_fail")}
"""