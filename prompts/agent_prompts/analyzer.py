from ..json_helper import get_json_string

# custom smells are smells identified from the dependency graph, when real code is not available yet 
# designite python smells are smells identified by dpy on real code. 
# Only EITHER custom smells OR dpy smells should be provided. 

"""
Input: current_design, current_deps_graph, current_rejected_improvements
has_implementation: Whether the analyzer is working on the current design before impl, or the implementation of checkpoint N/ after impl 
Output: current_analyzer_result, analyzer code quality results 
"""

IMPROVEMENTS_CRITERIA = """
- Modules should only be split when they carry distinct responsibilities with different reasons to change or is duplicated, and the length of code and the public interface is growing to a size that would justify a split.
- The problem is evidenced in the code today, and does not only make sense when something hypothetically changes in the future.
- The suggestion should not be previously suggested, to prevent running into loops. """

def get_analyzer_prompt(has_implementation): 
    
    return f"""
You are a senior software code quality analyst. 
Your job is to evaluate the following {'modular design' if not has_implementation else "implementation"} including kept, changed or new modules.
Project root: agent_workspace
{'Design: `current_design.json`' if not has_implementation else 'Implementation: implementation/'}
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

When evaluating and giving improvement suggestions, you should follow these criteria: {IMPROVEMENTS_CRITERIA}

First, add (do NOT delete) to the JSON object in `current_analyzer_result.json`, decsribing improvement suggestions only to modules that require refactoring, using the following schema.
Minimize the ambiguity when implementing them later by including a detailed enough improvement instruction. 
There should also be an attempt of simulation by implementing all of them at once, making sure that this should not create new design issues and the software quality in the 5 above aspects should improve after the implementation. 
{get_json_string("analyzer")}

Second, return in the output ONLY the JSON string below for your software quality evaluation, using the following schema. 
Do not include any additional natural language descriptions in your response. 
{get_json_string("analyzer_code_quality")}
"""