from .coding_instructions import get_coding_instructions

# Follow design, but ask the model to implement everything at once
# THIS IS CURRENTLY UNUSED - AS IT FOLLOWS DESIGN, THERE IS A LIST OF MODULE TO IMPLEMENT, HENCE MODULAR CODER IS USED INSTEAD.
def get_all_at_once_coder_prompt(checkpoint_number):
    return get_coding_instructions(checkpoint_number) + f"""
Implement a program that 100% solves the specification.
That is all you need to do.
Follow the design specified in `current_design.json` and the module dependencies in `current_deps_graph.json`, import existing modules where possible.
"""
