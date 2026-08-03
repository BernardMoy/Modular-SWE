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

IMPROVEMENTS_CRITERIA = """
- The problem is evidenced in the code today, and does not only make sense when something hypothetically changes in the future: Example includes modules that clearly mixes 2+ responsibilities, or a large chunk of duplicated code logic that needs to be modified together.
- The suggestion should not be previously suggested, to prevent running into loops. """

# CODE_SMELLS_INST_HAS_IMPL = """
# - LCOM: Only flag if this is caused by methods having different responsibilities.
# - Cyclomatic complexity, WMC, long methods: Only flag if the complexity is caused by unrelated concerns, or cause the code to become difficult to understand or test.
# - Feature envy: Only flag if moving the method to another class would not drastically reduce reusability or introduce tight coupling."""

# CODE_SMELLS_INST_NO_IMPL = """
# - Number of public methods: Only flag if the methods share different responsibilities, or they expose too much internal state that lead to feature envy of another module.  

# Apart from the code smells provided, consider the design semantics to identify issues before implementation: 
# - Module responsibility: Consider if a module has multiple concerns by inspecting if it has multiple responsibilities, or too many pre and postconditions in its design.
# - Duplicated or wrongly located methods: Consider if some methods are duplicated somewhere else, or if they should belong to another class."""

def get_analyzer_prompt(has_implementation): 
    
    return f"""
You are a senior software code quality analyst. 
Your job is to evaluate the following {'modular design' if not has_implementation else "implementation"} including kept, changed or new modules.
Project root: agent_workspace
{'Design: `current_design.json`' if not has_implementation else 'Implementation: `implementation/'}
Dependency graph: `current_deps_graph.json`{', which is modified from `original_deps_graph.json`.' if has_implementation else ""} 

You work with a OBSERVE - SUPPORT - SCORE cycle and you should not skip steps when performing your evaluation: 
    
    OBSERVE: Observe the {'code implementation' if has_implementation else 'design'}, and state antipatterns or maintainability issues that you have discovered. 
    Example: This module / file seems to mixes two separate, equally complex logic together. 

    SUPPORT: Only after the codebase observation then consider the code smells identified in `current_metrics.json`. You may use them to support your claim and the smells are not to be eliminated completely, and sometimes smells are not available for certain code smells, such as violation of single responsibilities or duplicated logic. 
    Example: It is found that there is a high LCOM in the aforementioned class, and we can confirm that this is due to it mixing two responsibilities together. 

    Repeat the OBSERVE-SUPPORT cycle multiple times until the codebase is thoroughly scanned and well understood, then begin scoring. 

    SCORE: Based on the observation and supporting code smells evidence, rank the software quality from 1 to 5 in the following aspects each: Readability, Simplicity, Maintainability, Modularity and Reusability. 
    To ensure reliable results you should rank them multiple times internally and take the most confident score in your rankings. 
    Your score should be based on the rubrics in `rubrics.md`, and avoid giving the middle score too often as it carries less meaningful value.

First, add (do NOT delete) to the JSON object in `current_analyzer_result.json`, decsribing improvement suggestions only to modules that require refactoring, using the following schema. These suggestions should follow these rules: {IMPROVEMENTS_CRITERIA}
Each improvement should be detailed enough that implementing them won't create new maintainability issues due to bad designs. 
There should also be an attempt of simulation by implementing all of them at once, making sure that this should not create new design issues and the software quality in the 5 above aspects should improve after the implementation. 
{get_json_string("analyzer")}

Second, return in the output ONLY the JSON string below for your software quality evaluation, using the following schema. 
Do not include any additional natural language descriptions in your response. 
{get_json_string("analyzer_code_quality")}
"""

#  in the format of "When <parts of code changes>, because of <code smell>, <effect that downgrades maintainability>."

# [CRITERIA]
# Your evaluation is based on the following master criteria to achieve long term code quality and maintainability: 
# - Modules should be able to independently evolve, each having only a single responsibility separated by clear boundaries. 
# - The system should be easy to test by avoiding overly complex functions with lots of control paths that could be simplified if possible.
# - Ensure high cohesion and low coupling by avoiding code that needs to be duplicated and modules that expose too much.

# [CODE SMELLS]
# Consider the code smells identified in `current_metrics` under the following guidelines. The code smells should only be used to support your suggestions and not to be eliminated completely as there may be false positives. {CODE_SMELLS_INST_HAS_IMPL if has_implementation else CODE_SMELLS_INST_NO_IMPL}

# If a list of previously suggested improvements are present in `current_rejected_improvements.json`, consider not suggesting the same improvements if they still apply.
