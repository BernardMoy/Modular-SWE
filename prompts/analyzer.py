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

Your job is to evaluate the following {"modular design including kept, changed or new modules" if second_iteration else "existing modules"}: 
Project root: agent_workspace
Design: `current_design.json`
Dependency graph: `current_deps_graph.json`

Your evaluation is based on the following criteria to achieve best code quality and maintainability: 
- Modules should be able to independently evolve, with low coupling and high cohesion 
- The system should be easy to test by not having overly complex functions with lots of control paths that could be simplified
- The maintenance effort when introducing new features should be as low as possible by avoiding duplication and ensuring single responsibility

For each module, reason about the following: 
- Is the module likely to change when new features are added with later checkpoints? 
- If a new feature is added, how much effort would it take to ensure consistent behaviour, such as having to modify multiple unrelated files or extend complex logic? 
- Does the nature and complexity of the problem justifies some of the design decisions already made, or is that a code smell that should be removed before new features are added? 

If code smells have been given in `current_metrics`, you should use them as a reference to support the maintainability issue described above, and your goal is not to eliminate these metrics completely. 
Interpret the metrics using the following guidelines: 
- LCOM: Only flag if the methods have different responsibilities. It is acceptable if the methods are just sequential stages of the same functionality. 
- Cyclomatic complexity, WMC: Only flag if the complexity is caused by unrelated concerns, lead to low testability, or high maintenance effort when adding new features. It is acceptable if the complex problem logic justifies it. 
- Magic number: Only flag if the meaning of the number is not immediately obvious to the developer. 
- Number of public methods: Only flag if the methods share different responsibilities, or they expose too much internal state that lead to feature envy of another module.  

{"You are also given a list of previously suggested improvements that are rejected in `current_rejected_improvements.json`." if second_iteration else ""}

Write a JSON object to `current_analyzer_result.json`, decsribing improvement suggestions to the modules, using the following schema. If a module does not require refactoring, do not include it in the output. If no modules need refactoring, return an empty array. 
{get_json_string("analyzer")}

Also, return ONLY the JSON string below that evaluates the result that is either "pass" or "fail" and provide your explanation based on the evaluation criteria. 
Do not include any additional natural language descriptions in your response. 
{get_json_string("analyzer_pass_fail")}
"""