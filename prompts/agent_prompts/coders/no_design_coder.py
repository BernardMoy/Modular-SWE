"""
Code directly. 
"""

from .coding_instructions import get_coding_instructions

# Return the original prompt, single agent, used in the SCB paper (modified).
def get_no_design_coder_prompt(checkpoint_number):
    return get_coding_instructions(checkpoint_number) + f"""
Implement a program that 100% solves the specification.
That is all you need to do.
"""
