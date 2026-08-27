from .coding_instructions import get_coding_instructions

# Follow design and implement a list of modules at once. 
# For the modular coder one module per agent scenario, pass modules with length == 1 
def get_modular_coder_prompt(checkpoint_number, modules): 
    # if the module has length = 0, raise exception
    if len(modules) == 0: 
        raise Exception("Empty module array passed to the modular coder.")

    return get_coding_instructions(checkpoint_number) + f"""
Your job is to implement the changes to the following modules. Follow the design specified in `current_design.json` and the module dependencies in `current_deps_graph.json`, import existing modules where possible.
{'\n'.join([f'- {module}' for module in modules])}
"""


#  the following {len(modules_to_implement)} modules: 
# {''.join([(f'- {x}\n') for x in modules_to_implement])}