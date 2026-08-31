from ..criteria import TEST_WRITER_CRITERIA


def get_black_box_test_writer_prompt(checkpoint_number):
    return f"""
You are a designer of test suites before the implementation as part of test-driven-development for the following issue. 

Project root: agent_workspace
Issue path: checkpoint_{checkpoint_number}.md
{f"The issue is built on top of previous_implementation/." if checkpoint_number > 1 else ""}

Write a pytest test suite inside the `tests/` folder for the new checkpoint requirements before implementation, following the rules below: {TEST_WRITER_CRITERIA}. 

The tests will live in the following folder structure: 
├── tests/
└── implementation/ {"or previous_implementation/" if checkpoint_number > 1 else ""}
    └── <entrypoint_file>.py 

{"After writing the tests, you should run them on previous_implementation/ to ensure they fail before the implementation of the current issue." if checkpoint_number > 1 else ""}
"""
