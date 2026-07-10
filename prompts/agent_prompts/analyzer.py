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

CODE_SMELLS_INST_HAS_IMPL = """
- LCOM: Only flag if this is caused by methods having different responsibilities.
- Cyclomatic complexity, WMC, long methods: Only flag if the complexity is caused by unrelated concerns, or cause the code to become difficult to understand or test.
- Feature envy: Only flag if moving the method to another class would not drastically reduce reusability or introduce tight coupling."""

CODE_SMELLS_INST_NO_IMPL = """
- Number of public methods: Only flag if the methods share different responsibilities, or they expose too much internal state that lead to feature envy of another module.  

Apart from the code smells provided, consider the design semantics to identify issues before implementation: 
- Module responsibility: Consider if a module has multiple concerns by inspecting if it has multiple responsibilities, or too many pre and postconditions in its design.
- Duplicated or wrongly located methods: Consider if some methods are duplicated somewhere else, or if they should belong to another class."""

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

[CODE SMELLS]
Consider the code smells identified in `current_metrics` under the following guidelines. The code smells should only be used to support your suggestions and not to be eliminated completely as there may be false positives. {CODE_SMELLS_INST_HAS_IMPL if has_implementation else CODE_SMELLS_INST_NO_IMPL}

If a list of previously suggested improvements are present in `current_rejected_improvements.json`, consider not suggesting the same improvements if they still apply.

[YOUR TASK]
First, write a JSON object to `current_analyzer_result.json`, decsribing improvement suggestions only to modules that require refactoring, using the following schema. 
Each suggestion should be backed up by a reason in the format of "When <parts of code changes>, because of <code smell>, <effect that downgrades maintainability>."
{get_json_string("analyzer")}

Second, return in the output ONLY the JSON string below that evaluates the result that is either "pass" or "fail" based on the master criteria, and provide explanation. 
Do not include any additional natural language descriptions in your response. 
{get_json_string("analyzer_pass_fail")}
"""