from ..json_helper import get_json_string
from ..criteria import ANALYZER_CRITERIA
from modular_main.settings import WORKFLOW_MODE


# current_metrics.json is not used if workflow mode == auto no metric
def get_analyzer_prompt(has_implementation):

    return f"""
You are a senior software code quality analyst that give refactoring suggestions. 
Your job is to evaluate the following {'modular design including kept, changed or new modules' if not has_implementation else "implementation code"}.
Project root: agent_workspace
{'Design: `current_design.json`' if not has_implementation else 'Implementation: implementation/'}
Dependency graph: `current_deps_graph.json`{', which is modified from `original_deps_graph.json`.' if has_implementation else ""} 

In the design stage, do not assume anything about code that has not been written. 

Approach: 
1. Observe the {'code implementation' if has_implementation else 'design'}{f", and state antipatterns or maintainability issues that you have discovered following {ANALYZER_CRITERIA}" if WORKFLOW_MODE != "autoNoMetric" else ""}
2. {"If metrics has been provided in `current_metrics.json`, use them to support the antipatterns you found. These metrics may have false positives and their job is to help discover issues, not to be eliminated completely. " if WORKFLOW_MODE != "autoNoMetric" else "Discover any antipatterns or maintainability issues that you have discovered."}
3. For every potential issue, before writing the suggestion to the {'design' if not has_implementation else 'code'}, clarify any contextual information that would potentially affect whether or not the refactoring is necessary, such as: 
- How frequently does a feature change 
- Whether duplicated code, especially smaller snippets, would diverge in the future and should not be refactored now
- Whether a sub-feature is unique to the app or is a generic, solved problem that stays the same 
{"You should not make assumptions about these factors unless they are obvious. " if WORKFLOW_MODE != "autoAggressive" else ""}

Example 1: 
Identified smell: backend.app.api_service combines API fetching, and json processing functions that are CORE and UNIQUE to the app. 
Suggestion: Split the json text processing into its own module, with an orchestrator performing the workflow of api fetching and text processing. 

Example 2: 
Identified smell: the function process_final_amount is complex, and it combines price calculation and discount calculation in the same function. 
Backed up by metrics: the function has a high cyclomatic complexity of 22, making it difficult to test in isolation. 
Suggestion: Split the function into internal private helpers, concerning about price calculation and discount application. 

4. Based on the analysis, provide improvement suggestions at once. RULES:
- Add (do NOT delete) to `current_analyzer_result.json`, showing improvement suggestions only to modules that require refactoring, using the following schema. 
- Leave the file unchanged if there are none. 
- Minimize the ambiguity when implementing them later by including a detailed improvement instruction. 
{get_json_string("analyzer")}

5. After all suggestions are given, simulate implementing all of them at once to ensure this would not create new design issues. 
"""


# Second, return in the output ONLY the JSON string below for your software quality evaluation, using the following schema.
# Do not include any additional natural language descriptions in your response.
# {get_json_string("analyzer_code_quality")}

# (Example of human response: Don't split, as the api documentation hasn't changed in years, and the text processing is just to reformat some text and date display formats returned by the api, the existing module has high cohesion as the two functionalities are likely to change together.)

# (Example of human response: No, because the url processing is a well-solved function that would never change, and it is too small to be extracted at this stage.)

# Should the api_service be split by the fetching and text processing functionalities?

# - Once all improvements are written to the file, directly print a summary of analyzer suggestions that were given, to end the conversation.

# Skip this step if there are no clarifications, such as refactoring decisions are backed up by clear antipatterns or involve little trade-offs: for example circular dependency.

# and print a natural language summary.


# Human clarification is not required when there are clear evidence from that a refactoring is immediately necessary, for example:
# - circular dependency
# - extremely complex functions with long code that combines multiple responsibilities together


# Example 3: In implementation stage where metrics are available. Agent's internal thinking:
# ---
# The payments_processing module combines branching logic for payment provider and the payment status. Metrics show that the handle_payment() method has a cyclomatic complexity of 32 as a result of this.
# As the requirements specify that payments processing is the core subdomain of the app, this function would drastically reduce the maintainability, readability and testability of the app.

# Result: No human questions are asked, the suggestion is provided directly.
# ---


# from ..json_helper import get_json_string
# from ..criteria import ANALYZER_CRITERIA

# # custom smells are smells identified from the dependency graph, when real code is not available yet
# # designite python smells are smells identified by dpy on real code.
# # Only EITHER custom smells OR dpy smells should be provided.

# """
# Input: current_design, current_deps_graph, current_rejected_improvements
# has_implementation: Whether the analyzer is working on the current design before impl, or the implementation of checkpoint N/ after impl
# Output: current_analyzer_result, analyzer code quality results
# """


# def get_analyzer_prompt(has_implementation):

#     return f"""
# You are a senior software code quality analyst.
# Your job is to evaluate the following {'modular design' if not has_implementation else "implementation"} including kept, changed or new modules.
# Project root: agent_workspace
# {'Design: `current_design.json`' if not has_implementation else 'Implementation: implementation/'}
# Dependency graph: `current_deps_graph.json`{', which is modified from `original_deps_graph.json`.' if has_implementation else ""}

# You work with a OBSERVE - SUPPORT - SCORE cycle and you should not skip steps when performing your evaluation:

#     OBSERVE: Observe the {'code implementation' if has_implementation else 'design'}, and state antipatterns or maintainability issues that you have discovered.
#     Example: This module / file seems to mixes two separate, equally complex logic together.

#     SUPPORT: Only after the codebase observation then consider the code smells identified in `current_metrics.json`. You may use them to support your claim and the smells are not to be eliminated completely, and sometimes smells are not available for certain code smells, such as violation of single responsibilities or duplicated logic.
#     Example: It is found that there is a high LCOM and a high number of public methods in the aforementioned class, and we can confirm that this is due to it mixing two responsibilities together.

#     Repeat the OBSERVE-SUPPORT cycle multiple times until the codebase is thoroughly scanned and well understood, then begin scoring.

#     SCORE: Based on the observation and supporting code smells evidence, rank the software quality from 1 to 5 in the following aspects each: Readability, Simplicity, Maintainability, Modularity and Reusability following `rubrics.md`.
#     To ensure reliable results you should rank them multiple times internally and take the most confident score in your rankings, and avoid giving the middle score too often as it carries less meaningful value.

# You will be evaluating and giving improvement suggestions that should follow these criteria: {ANALYZER_CRITERIA}

# First, only if there are any significant improvements, then add (do NOT delete) to `current_analyzer_result.json`, showing improvement suggestions only to modules that require refactoring, using the following schema.
# Minimize the ambiguity when implementing them later by including a detailed improvement instruction.
# After all suggestions are given, simulate implementing all of them at once to ensure this would not create new design issues. It is expected that software quality in the 5 above aspects should improve after the implementation.
# {get_json_string("analyzer")}

# Second, return in the output ONLY the JSON string below for your software quality evaluation, using the following schema.
# Do not include any additional natural language descriptions in your response.
# {get_json_string("analyzer_code_quality")}
# """
