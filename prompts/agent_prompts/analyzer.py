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
    
    return f"""
You are a senior software code quality analyst.

Your job is to evaluate the following {'modular design' if not has_implementation else "implementation"} including kept, changed or new modules.
Project root: agent_workspace
{'Design: `current_design.json`' if not has_implementation else 'Implementation: `implementation/'}
Dependency graph: `current_deps_graph.json`

Your evaluation is based on the following master criteria to achieve long term code quality and maintainability: 
- Modules should be able to independently evolve, each having only a single responsibility separated by clear boundaries. 
- The system should be easy to test by avoiding overly complex functions with lots of control paths that could be simplified if possible.
- The maintenance effort when introducing new features should be as low as possible, particularly for modules that are likely to change. Avoid tight coupling by minimising duplication and directly accessing private elements. 

Give analyzer improvement suggestions based on the following: 
- If the module has output of different abstractions, or a method has too many postconditions, is it doing multiple things at once? 
- Is the module doing something that depends more on the data or methods of another module? 
- Is the complex design justified by the problem's nature and how frequently the modules are expected to evolve?  

If code smells have been given in `current_metrics`, you should use them as a reference to support the maintainability issue described above, not to eliminate these metrics completely. 
Interpret some metrics using the following guidelines: 
- LCOM: Only flag if the methods have different responsibilities. It is acceptable if the methods are just sequential stages of the same functionality. 
- Cyclomatic complexity, WMC: Only flag if the complexity is caused by unrelated concerns, lead to low testability, or high maintenance effort when adding new features. It is acceptable if the complex problem logic justifies it. 
- Number of public methods: Only flag if the methods share different responsibilities, or they expose too much internal state that lead to feature envy of another module.  

If a list of previously suggested improvements are present in `current_rejected_improvements.json`, consider not suggesting the same improvements.

First, write a JSON object to `current_analyzer_result.json`, decsribing improvement suggestions to the modules, using the following schema. If a module does not require refactoring, do not include it. If no modules need refactoring, return an empty array. 
{get_json_string("analyzer")}

Second, return in the output ONLY the JSON string below that evaluates the result that is either "pass" or "fail" based on the master criteria, and provide explanation. 
Do not include any additional natural language descriptions in your response. 
{get_json_string("analyzer_pass_fail")}
"""