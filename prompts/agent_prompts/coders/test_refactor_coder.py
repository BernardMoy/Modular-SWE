from ...criteria import TEST_WRITER_CRITERIA


def get_test_refactor_coder_prompt(checkpoint_number):
    return f"""
Your job is to verify and fix the code implementations based on tests. 

Project root: agent_workspace
Issue path: checkpoint_{checkpoint_number}.md
Implementation folder: implementation/
Tests: tests/

You should run pytest against the implementation by setting up a virtual environment and installing the required packages. 
Your job is to perform the minimal modification to implementation/ to fix the failed tests. 
ONLY when you discovered that a majority of tests failed because of test configuration issues, then you are allowed to perform modification to the test suite, but they must follow the rules: {TEST_WRITER_CRITERIA}. 
OTHERWISE, never modify the tests to suit the behaviour of the implementation. 
"""


# A list of pass and failed test names derived from the requirements, and their differing behaviour is given in `current_test_results.json`.
# Your task is to perform refactoring on the implementation code to fix the failed tests, while preserving the behaviour of passed tests.
# Focus on the functionality and avoid performing large refactoring on how the code is implemented.
