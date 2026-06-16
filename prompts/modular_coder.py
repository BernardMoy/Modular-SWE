# Return the original prompt, single agent, used in the SCB paper (modified). 
# This assumes agent_workspace already contain the respective files of the respective problem. 
def get_modular_coder_prompt(checkpoint_number, modules_to_implement): 
    """
    The agent can read: 
    - whatever is in the agent workspace folder! 
    """ 

    venv_text = """Use a virtual environment and ensure that a 'requirements.txt' is present with any dependencies
you need to solve the problem.""" if checkpoint_number == 1 else """Keep using the same virtual environment you started with,
update 'requirements.txt' with any new dependencies you need."""

    code_quality_text = """Ensure your code a good quality, below are a list of practices you should follow but not limited to them. 
- Avoids functions that are too complex with too much nested if/else statements.
- Avoid the use of magic numbers when their meanings are not obvious.
- Do not access the private elements of another class.
"""

    return f"""
You are working on the following issue:
Issue path: checkpoint_{checkpoint_number}.md
Implement your solution in: checkpoint_{checkpoint_number}/
{f"Extend your solution based on: checkpoint_{checkpoint_number-1}/\n" if checkpoint_number>1 else ""}

{venv_text}

{code_quality_text}

Your job is to implement parts of the design specified in `current_design.json`, and you should import existing modules. 
You should ONLY implement the following {len(modules_to_implement)} modules: 
{''.join([(f'- {x}\n') for x in modules_to_implement])}
"""