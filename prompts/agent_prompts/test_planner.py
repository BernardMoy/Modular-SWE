from ..json_helper import get_json_string

def get_test_planner_prompt(checkpoint_number): 
    return f"""
You are a designer of test suites before the implementation of an issue.

You are working on the following issue:
Project root: agent_workspace
Issue path: checkpoint_{checkpoint_number}.md
{f"The issue is built on top of previous_implementation/." if checkpoint_number > 1 else ""}

Propose a plan of test suites that would solve the issue specification completely. You should only ensure the documented requirements are met, including any edge cases. 
Write to `current_test_plan.json` following the json schema below: 
{get_json_string("test_planner")}
"""