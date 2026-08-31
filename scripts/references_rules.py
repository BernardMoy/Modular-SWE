"""
Define the rules for keeping which modules under deps graph
dependent on the reference problem being used.
"""


def _is_problem(directory, problem):
    return directory.endswith(f"/{problem}/") or directory.endswith(f"/{problem}")


# The modules here are the modules in the temp entrypoint file
# Which controls which modules to be excluded
def validate_reference_entrypoint_modules(module, directory):

    # identify the problem from directory
    if _is_problem(directory, "tqdm"):
        # Filter only modules with the tqdm. prefix as that folder is the real implementation
        return module.startswith("tqdm.")
