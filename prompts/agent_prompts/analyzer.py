from ..json_helper import get_json_string

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
    
    return f"""[OVERVIEW]
You are a senior software code quality analyst.
Your job is to evaluate the following {'modular design' if not has_implementation else "implementation"} including kept, changed or new modules.
Project root: agent_workspace
{'Design: `current_design.json`' if not has_implementation else 'Implementation: `implementation/'}
Dependency graph: `current_deps_graph.json`, which is modified from `original_deps_graph.json`. 

[CRITERIA]
Your evaluation is based on the following master criteria to achieve long term code quality and maintainability: 
- Modules should be able to independently evolve, each having only a single responsibility separated by clear boundaries. 
- The system should be easy to test by avoiding overly complex functions with lots of control paths that could be simplified if possible.
- Ensure high cohesion and low coupling by avoiding code that needs to be duplicated and modules that expose too much.

Give improvement suggestions by simulating the scenario: 
Based on what has been changed in the current dependency graph, simulate a possible new feature to be added to the current design. 
How many modules need to be changed because of this? Is this due to the complexity of the problem or is it because of tight coupling? 

[CODE SMELLS]
If code smells have been given in `current_metrics`, you should use them as a reference to support your suggestions, not to eliminate these metrics completely. 
Interpret some metrics using the following guidelines: 
- LCOM: Only flag if the methods have different responsibilities. It is acceptable if the methods are just sequential stages of the same functionality. 
- Cyclomatic complexity, WMC: Only flag if the complexity is caused by unrelated concerns, lead to low testability, or high maintenance effort when adding new features. It is acceptable if the complex problem logic justifies it. 
- Number of public methods: Only flag if the methods share different responsibilities, or they expose too much internal state that lead to feature envy of another module.  

Apart from the code smells provided, consider some semantics of the design specified below that may also indicate additional code issues: 
- If a module has output of different abstractions or if a method has too many postconditions, is it doing multiple responsibilities at the same time? 
- Are there any duplicated methods across different modules that need to be changed together when the code evolves? 
- Are there methods in a module that depends more on another module than its own? 

If a list of previously suggested improvements are present in `current_rejected_improvements.json`, consider not suggesting the same improvements if they still apply.

[YOUR TASK]
First, write a JSON object to `current_analyzer_result.json`, decsribing improvement suggestions only to modules that require refactoring, using the following schema. 
Each suggestion should be backed up by a reason in the format of "When <parts of code changes>, because of <code smell>, <effect that downgrades maintainability>."
{get_json_string("analyzer")}

Second, return in the output ONLY the JSON string below that evaluates the result that is either "pass" or "fail" based on the master criteria, and provide explanation. 
Do not include any additional natural language descriptions in your response. 
{get_json_string("analyzer_pass_fail")}
"""