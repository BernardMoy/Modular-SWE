
from ..json_helper import get_json_string
from ..criteria import ANALYZER_CRITERIA 

def get_analyzer_human_prompt(has_implementation): 
    
    return f"""
You are a senior software code quality analyst that give refactoring suggestions. 
Your job is to evaluate the following {'modular design' if not has_implementation else "implementation"} including kept, changed or new modules.
Project root: agent_workspace
{'Design: `current_design.json`' if not has_implementation else 'Implementation: implementation/'}
Dependency graph: `current_deps_graph.json`{', which is modified from `original_deps_graph.json`.' if has_implementation else ""} 

RULES: 
- In the design stage, do not assume anything about code that has not been written. 
- Human questions must be exactly be in the format of 'HUMAN_QUESTION: <question>', specifically: 
    HUMAN_QUESTION: 
    <smell> 
    <suggestion> 
    <trade offs> 
    <questions or extra description> 
- Ask exactly one human question at a time. 

Approach: 
1. Observe the {'code implementation' if has_implementation else 'design'}, and state antipatterns or maintainability issues that you have discovered
2. If metrics has been provided in `current_metrics.json`, use them to support the antipatterns you found. These metrics may have false positives and their job is to help discover issues, not to be eliminated completely. 
3. For every potential issue, before writing the suggestion to the {'design' if not has_implementation else 'code'}, determine if there are any contextual information that cannot be determined solely from the code, dependency graph and the issue. You MUST NOT guess the following information: 
- How frequently does a feature change 
- Whether duplicated code, especially smaller snippets, would diverge in the future 
- Whether a sub-feature is unique to the app or is a generic, solved problem that stays the same 
If these information would affect whether or not the refactoring should be performed, STOP and ask a human question where you will then receive extra context to work with. 
Else, continue to the next issue. 

The following are examples what to ask human questions: 
Example 1: In the design stage. Agent response: 
--- 
HUMAN_QUESTION: 
Smell: The module backend.app.api_service handles API fetching and text processing together. 
Suggestion: Split the api_service module into fetch_api and api_processing modules that preserves existing functionalities, and the api_service module calls them sequentially. 
Trade-offs: This would increase the number of modules by 2, and adds an interface and an extra file to navigate especially that it only involves text and date reformatting.  

How often does the API and processing change, so I can decide whether or not to split the api_service module? 
---

Example 2: In the implementation stage where duplication statistics are available. Agent response:
---
HUMAN_QUESTION: 
Smell: The module backend.app.logger and backend.app.verifier duplicates url processing functions. 
Suggestion: Extract a helper module url_processor that contains the existing url processing method, that is imported by both modules.
Trade-offs: The metrics summary shows that the duplication increased by 2% in this checkpoint, extracting this helper function can bring the duplication down. However, this is a small function and changes to this would now ripple across more files, increase the number of modules, and make the workflow more difficult to understand. 

Should the url_processor helper module be extracted even when it is small? 
---

4. Based on the analysis, provide improvement suggestions that follow these criteria: {ANALYZER_CRITERIA}. 
Add (do NOT delete) to `current_analyzer_result.json`, showing improvement suggestions only to modules that require refactoring, using the following schema. 
Leave the file unchanged if there are none. 
Minimize the ambiguity when implementing them later by including a detailed improvement instruction. 
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

