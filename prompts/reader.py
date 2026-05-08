from .json_helper import get_json_string

def get_reader_prompt(issue_title, issue_body, working_dir): 
    return f"""
You are a senior software engineer that analyses modules in a software project.

You are working on the following issue:
Issue title: {issue_title}
Issue body: {issue_body}
Working directory: {working_dir}

Identify the existing modules in the codebase. For each module, decide if it can be reused or adapted to help achieve the goal specified in the issue. Do not propose new modules.

Output a JSON object including only the relevant modules, using the following schema. If there are no relevant modules, return an empty JSON array.

{get_json_string("reader")}

Return only the JSON object, do not include any additional natural language text in your response.
"""
