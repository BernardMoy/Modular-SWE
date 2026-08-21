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


"""Backup code for running multiple instances at once: 

(By Module mode) 
with ThreadPoolExecutor() as exec: 
    # Submit the task of coding each module to the thread pool
    futures = [
        exec.submit(get_prompt_and_run_agent, executor, "modular_coder", N, [module])  # Pass the args after the function call name 
        for module in layer
    ]

    for future in as_completed(futures): 
        print(future.result())

(By Layer mode) 
# For each layer of the bfs tree, implement the modules in parallel 
for layer in modules_array: 
    print(f"========== CODING: {layer} ==========")
    if WORKFLOW_MODE == "byLayer": 
        # Submit a single prompt to the modular coder agent, passing all modules of the layer to it 
        result = get_prompt_and_run_agent(executor, "modular_coder", N, layer)
        print(result) 

    elif WORKFLOW_MODE == "byModule": 
        with ThreadPoolExecutor() as exec: 
        # Submit the task of coding each module to the thread pool
        futures = [
            exec.submit(get_prompt_and_run_agent, executor, "modular_coder", N, [module])  # Pass the args after the function call name 
            for module in layer
        ]

        for future in as_completed(futures): 
            print(future.result())
"""