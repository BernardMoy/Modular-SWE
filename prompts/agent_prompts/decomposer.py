from ..json_helper import get_json_string
from ..criteria import DECOMPOSER_SUGGESTIONS_CRITERIA
from modular_main.settings import WORKFLOW_MODE 

# The implementation path is not needed. 
# Reading the existing code is not the responsibility of this agent. 

"""
Input: new instruction, prev implementation (if checkpoint >1), current_design, current_deps_graph, current_analyzer_result
Output: current_design, current_deps_graph, current_rejected_improvements
"""

# Follows the 5 criteria for modular design. For the decomposer. 
MODULE_CODE_PRACTICES = """
- The number of modules should be minimized. 
- A module should only have a single responsibility, not to have multiple distinct reasons to change. 
- A module should expose the minimum public interface for others to work with. 
- A module should have a proper reason to exist, such as hiding complex logic. Avoid wrapper modules, or duplication of existing logic or data without adding much value. 
- Do not make assumptions about code that has not been implemented, start small and simple. 
- There should be minimum dependency with other modules, following high cohesion low coupling. 
"""

def get_decomposer_prompt(checkpoint_number): 
    # Whether current_design and current_deps_graph exists 
    # hasPrevDesign = checkpoint_number > 1 or second_iteration

    return f"""
You are a senior software engineer that decomposes requirements into modular design schemas.

You are working on the following issue:
Project root: agent_workspace
Issue path: checkpoint_{checkpoint_number}.md
{f"The issue is built on top of previous_implementation/." if checkpoint_number > 1 else ""}

If a design is provided in `current_design.json` with the dependency graph in `current_deps_graph.json`, prioritise reusing existing modules instead of creating a new module where possible.
If a list of improvement suggestions for the current design is provided in `current_analyzer_result.json`, {"implement the changes in the design" if True else f"consider accepting or rejecting them based on: {DECOMPOSER_SUGGESTIONS_CRITERIA}"}. 

Propose a modular design that achieves the goal specified in the issue when integrated together. Follow the design principles: {MODULE_CODE_PRACTICES}

Example: 
Issue: Build a order app that allows users to purchase items from our store online. Discounts can be applied using specified discount codes. The user should be able to pay with an online payment service. 
Reasoning: 
Identify modular boundaries that encapsulate the most information: Order, price calculation, discounts, payment. 
Define domain entiries: Order, Item, User, Payment. 
Propose modules: 
- ProductRepository that returns the price for a given item; 
- OrderValidator (Whether or not the order can proceed by checking stock and purchase limits);
- PricingEngine that computes the price before discount using a dictionary of items and quantity;
- DiscountService that applies discount based on the user, discount code, and the price;
- PaymentService that connects to an external provider, that only takes the final amount and charge it; 
- OrderService lead that executes the sequence. 
Each module in this design encapsulates business logic with high cohesion, and with low coupling where modules only depend on simple data types with well-defined public interfaces that are small, not on the internals. 
Each of them have a strong and single responsibility, not wrapper modules that simply reuse other's data. 
I will also mention that PaymentService does not know how the pricing and discount calculation works, and the discount service does not know how the price is calculated in my response. 
About whether or not it is complex after the code implementation and how the private methods work, I would not make any assumptions at this stage. 

Task: 
1. create or overwrite the JSON object in `current_design.json` by including all modules in your design using the following schema. Rules:
- Follow strictly the decision tree below to decide the 'type' field of the module: 
(1) Does the module have a previous, concrete implementation in the code apart from the design? YES -> GOTO (2). NO -> 'new'
(2) Has the module design been changed from its previous implementation? YES -> 'changed'. NO -> 'keep'
- The module_name field should follow pydeps conventions, stripping the .py extension for modules and specify the file path separated by dots (.) 
{get_json_string("decomposer")}

2. create or update the dependency graph in `current_deps_graph.json`, using the following schema of an adjacency list. Rules: 
- Arrows point to the modules that they import. 
- Include all lazy imports. 
- Do not include standard python libraries. 
- The names used in the dependency graph must match exactly the `module_name` field in `current_design.json`. 
{get_json_string("dependency_graph")}

3. update any improvements listed in `current_analyzer_result.json` if present: by changing the status field to {'"accepted"' if True else f'either "accepted" or "rejected" and provide a reason if rejected. '}
"""
