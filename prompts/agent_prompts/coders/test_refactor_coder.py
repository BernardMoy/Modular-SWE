def get_test_refactor_coder_prompt(checkpoint_number): 
    return f"""
Your job is to fix the code implementation based on failed tests. 

Project root: agent_workspace
Issue path: checkpoint_{checkpoint_number}.md
Implementation folder: implementation/

A list of pass and failed test names derived from the requirements, and their differing behaviour is given in `current_test_results.json`. 
Your task is to perform refactoring on the implementation code to fix the failed tests, while preserving the behaviour of passed tests. 
Focus on the functionality and avoid performing large refactoring on how the code is implemented. 
"""