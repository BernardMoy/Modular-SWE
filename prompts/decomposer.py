from .json_helper import get_json_string

def get_decomposer_prompt(issue_title, issue_body, working_dir): 
    return f"""
You are a senior software engineer that specialises in modular software design.

You are working on the following issue:
Issue title: {issue_title}
Issue body: {issue_body}
Working directory: {working_dir}

Propose a modular design, each with a single responsibility, that when integrated together, achieve the goal specified in the issue.

Output strictly a JSON object using the following schema.

{get_json_string("decomposer")}

Return only the JSON object, do not include any additional natural language text in your response.

"""
