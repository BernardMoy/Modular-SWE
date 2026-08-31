# Return the original prompt, single agent, used in the SCB paper (modified).
# This assumes agent_workspace already contain the respective files of the respective problem.
def get_original_scb_prompt(checkpoint_number):
    """
    The agent can read:
    - checkpoint_N.md (instruction)
    - config.yaml
    - checkpoint_(N-1)/ (previous implementation, only when checkpoint_number >1)
    """

    venv_text = (
        """Use a virtual environment and ensure that a 'requirements.txt' is present with any dependencies
you need to solve the problem."""
        if checkpoint_number == 1
        else """Keep using the same virtual environment you started with,
update 'requirements.txt' with any new dependencies you need."""
    )

    return f"""
Implement a program that 100% solves the specification.
That is all you need to do.

{venv_text}

You are working on the following issue: checkpoint_{checkpoint_number}.md
Implement your solution in implementation/ folder.
{'Extend your solution based on previous_implementation/.' if checkpoint_number > 1 else ""}
"""
