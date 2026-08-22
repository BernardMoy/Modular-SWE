from ..criteria import TEST_WRITER_CRITERIA

def get_black_box_test_writer_prompt(checkpoint_number): 
    return f"""
You are a designer of test suites before the implementation of the following issue: 

Project root: agent_workspace
Issue path: checkpoint_{checkpoint_number}.md
{f"The issue is built on top of previous_implementation/." if checkpoint_number > 1 else ""}

Write a pytest test suite inside the `tests/` folder for the new checkpoint requirements before implementation, following the rules below: {TEST_WRITER_CRITERIA}
"""