from ..json_helper import get_json_string

# The implementation path is not needed. 
# Reading the existing code is not the responsibility of this agent. 

"""
Input: new instruction, prev implementation (if checkpoint >1), current_design, current_deps_graph, current_analyzer_result
Output: current_design, current_deps_graph, current_rejected_improvements
"""

ANALYZER_CRITERIA="""
- Whether the suggestion lead to reduced future effort when adding new features.
- Whether the nature of the problem and the size of the file justifies the complexity without the refactoring. 
- Whether the suggestion conflict with issue requirements.
"""

MODULE_CODE_PRACTICES = """
- A module should only expose the minimum amount of knowledge in its public interface.
- Each module should only have a single responsibility and follow high cohesion low coupling. They should not have unrelated methods, or methods that should belong to another class. 
"""

def get_decomposer_prompt(checkpoint_number): 
    # Whether current_design and current_deps_graph exists 
    # hasPrevDesign = checkpoint_number > 1 or second_iteration

    return f"""
You are a senior software engineer that specialises in modular software design.

You are working on the following issue:
Project root: agent_workspace
Issue path: checkpoint_{checkpoint_number}.md
{f"The issue is built on top of previous_implementation/." if checkpoint_number > 1 else ""}

If a design is provided in `current_design.json` with the dependency graph in `current_deps_graph.json`, prioritise reusing existing modules instead of creating a new module where possible.
If a list of improvement suggestions for the current design is provided in `current_analyzer_result.json`, please consider accepting or rejecting them based on: {ANALYZER_CRITERIA}

Propose a modular design that achieves the goal specified in the issue when integrated together. 
You should follow best code practices, including: {MODULE_CODE_PRACTICES}

First, create or overwrite the JSON object in `current_design.json` by including all modules in your design using the following schema. Rules:
- Follow strictly the decision tree below to decide the 'type' field of the module: 
(1) Does the module have a previous, concrete implementation in the code apart from the design? YES -> GOTO (2). NO -> 'new'
(2) Has the module design been changed from its previous implementation? YES -> 'changed'. NO -> 'keep'
- The module_name field should follow pydeps conventions, stripping the .py extension for modules and specify the file path separated by dots (.) 
{get_json_string("decomposer")}

Second, create or update the dependency graph in `current_deps_graph.json`, using the following schema of an adjacency list. Rules: 
- Arrows point to the modules that they import. 
- Include all lazy imports. 
- Do not include standard python libraries. 
- The names used in the dependency graph must match exactly the `module_name` field in `current_design.json`. 
{get_json_string("dependency_graph")}

Third, update any improvements listed in `current_analyzer_result.json` if present by changing the status field to either "accepted" or "rejected" and provide a reason if rejected. 
"""
