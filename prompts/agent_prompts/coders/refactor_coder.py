
from ...criteria import DECOMPOSER_SUGGESTIONS_CRITERIA

# This assumes the coding instructions already are met - hence they are not provided here again
# As no major refactoring involving those parts (import styles, venv) should be involved. 
def get_refactor_coder_prompt(checkpoint_number): 
    return f"""
You are a senior software engineer that specialises in modular software design.

You are working on the following issue:
Project root: agent_workspace
Issue path: checkpoint_{checkpoint_number}.md
Implementation folder: implementation/

If a list of improvement suggestions for the current design is provided in `current_analyzer_result.json`, please consider accepting or rejecting them based on: {DECOMPOSER_SUGGESTIONS_CRITERIA}

Your task is to perform refactoring on the implementation code while preserving its functionality based on the improvement suggestions and your evaluation. 
Additionally, update any improvements listed in `current_analyzer_result.json` if present by changing the status field to either "accepted" or "rejected" and provide a reason if rejected. 
"""