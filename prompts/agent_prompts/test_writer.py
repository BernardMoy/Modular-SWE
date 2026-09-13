from ..json_helper import get_json_string

# Writer for NON black box tests: custom problems / non CLI problems. 
# Takes in a blueprint and an implementation, then write tests based on the BLUEPRINT 
def get_test_writer_prompt(checkpoint_number):
    return f"""
You are writing tests for the software.  

You are working on the following issue:
Project root: agent_workspace
Issue path: checkpoint_{checkpoint_number}.md
Implementation path: implementation/ 
Tests blueprint: test_blueprint.json

Your job is to write to or modify from the executable tests in a separate `tests/` folder under the project root following the tests blueprint, using an appropriate testing framework.
Black-box testing should be preferred where possible. However, to make the tests runnable, you are allowed to perform minimal modification of the implementation, such as by adding data-testid. 
Test failures should be due to the functionality and the code behaviour, not its syntax or how the code is written.

Hard constraints: 
- Do not modify the testing blueprint. 
- Do not include tests not specified in the blueprint. 
- Do not modify the implementation for reasons other than making tests runnable; do not modify its internal logic in order to 'pass' more test cases. 

After the tests are present, you should run them to make sure they works as expected and report the result. 
Write to `current_test_results.json` decsribing tests executed following the json schema below.
{get_json_string("test_results")}
"""
