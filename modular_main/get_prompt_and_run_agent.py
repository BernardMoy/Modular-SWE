from .settings import AGENT, MODEL
from prompts.get_prompt import get_prompt

# Helper function to get prompt and run the agent by passing the prompt inside the bwrap executor 
def get_prompt_and_run_agent(executor, agent_name, *args): 
    """
    executor: the BWrap executor 
    agent_name: Name of your agents (decomposer, analyzer), must be defined in get_prompt.py. NOT the codex / claude code etc. which is configured in settings.py
    *args: the arguments required by the agents get prompt method 
    """
    prompt = get_prompt(agent_name, *args)
    output = executor.run([
        "python3", "-m", "workspace_helpers.run_agent", 
        AGENT, MODEL, prompt
    ])
    return output 