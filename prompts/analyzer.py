from .json_helper import get_json_string

# custom smells are smells identified from the dependency graph, when real code is not available yet 
# designite python smells are smells identified by dpy on real code. 
# Only EITHER custom smells OR dpy smells should be provided. 

# Second iteration simply refers to whether it is the first call to the analyzer. 
# If second iteration is true, then current design contains old + new modules
# as well as rejected designs 

"""
Input: current_design, current_deps_graph, current_rejected_improvements
has_implementation: Whether the analyzer is working on the current design before impl, or the implementation of checkpoint N/ after impl 
Output: current_analyzer_result, pass / fail string (Returned) 
"""
def get_analyzer_prompt(has_implementation): 
    
    return f"""
You are a senior software code quality analyst.

Your job is to evaluate the following modular design including kept, changed or new modules.
Project root: agent_workspace
Design: `current_design.json`
Dependency graph: `current_deps_graph.json`

Your evaluation is based on the following master criteria to achieve long term code quality and maintainability: 
- Modules should be able to independently evolve, each having only a single responsibility with clear boundaries between them. 
- The system should be easy to test by avoiding overly complex functions with lots of control paths that could be simplified if possible.
- The maintenance effort when introducing new features should be as low as possible, by avoiding tight coupling by minimising duplication and directly accessing private elements. 

For each module, reason about the following: 
- Is the module likely to change when new features are added with later checkpoints? 
- If a new feature is added, how much effort would it take to ensure consistent behaviour, such as having to modify multiple unrelated files or extend complex logic? 
- Does the nature and complexity of the problem justifies some of the complexity in design decisions? 

If code smells have been given in `current_metrics`, you should use them as a reference to support the maintainability issue described above, and your goal is not to eliminate these metrics completely. 
Interpret some metrics using the following guidelines: 
- LCOM: Only flag if the methods have different responsibilities. It is acceptable if the methods are just sequential stages of the same functionality. 
- Cyclomatic complexity, WMC: Only flag if the complexity is caused by unrelated concerns, lead to low testability, or high maintenance effort when adding new features. It is acceptable if the complex problem logic justifies it. 
- Magic number: Only flag if the meaning of the number is not immediately obvious to the developer. 
- Number of public methods: Only flag if the methods share different responsibilities, or they expose too much internal state that lead to feature envy of another module.  

If a list of previously suggested improvements are present in `current_rejected_improvements.json`, consider not suggesting the same improvements.

First, write a JSON object to `current_analyzer_result.json`, decsribing improvement suggestions to the modules, using the following schema. If a module does not require refactoring, do not include it. If no modules need refactoring, return an empty array. 
{get_json_string("analyzer")}

Second, return in the output ONLY the JSON string below that evaluates the result that is either "pass" or "fail" based on the master criteria, and provide explanation. 
Do not include any additional natural language descriptions in your response. 
{get_json_string("analyzer_pass_fail")}
"""