"""
Main entrypoint file for the entire workflow. 
"""

import asyncio
import os 
import shutil 
import argparse
from openai_codex import AsyncCodex, Codex, Sandbox, ApprovalMode
from .auth.codex_login import codex_login_gpt_subscription
from pathlib import Path
from .entry_files import ENTRY_FILES
import subprocess
from .BwrapExecutor import BwrapExecutor
from prompts.get_prompt import get_prompt
from .settings import AGENT, MODEL

# async def agent_test(model = "gpt-5.5"): 

#     task = """Create a file named fibonacci.py. 
# In the file, include a function named fibonacci(n) that returns the nth fibonacci number.
# """
#     async with AsyncCodex() as codex:  
#         thread = await codex.thread_start(model=model, sandbox=Sandbox.workspace_write, approval_mode=ApprovalMode.deny_all)
#         result = await thread.run(task)
#         print(result.final_response)

# asyncio.run(agent_test())


# Constants 
AGENT_WORKSPACE = Path("agent_workspace")
PROBLEMS_DIR = Path("datasets/slopCodeBench/scb-problems")
SOLS_TESTS_DIR= Path("datasets/slopCodeBench/scb-problems-sols-tests")
WORKSPACE_HELPERS = Path("modular_main/workspace_helpers")

# main entrypoint of the modular workflow 
# usage: python -m modular_main.main <problem_name> <checkpoint_number> 
def modular_workflow(): 
    parser = argparse.ArgumentParser()
    parser.add_argument("problem_name", help="Name of the problem")
    parser.add_argument("checkpoint_number", help="Checkpoint number")
    args = parser.parse_args()

    # Obtain the problem name and checkpoint no from arguments
    PROBLEM = args.problem_name 
    N = int(args.checkpoint_number) 

    # Get the entrypoint name 
    if PROBLEM not in ENTRY_FILES: 
        raise Exception(f"Invalid problem name: {PROBLEM}")
    ENTRY_FILE_NAME = ENTRY_FILES[PROBLEM]
    PROBLEM_DIR = PROBLEMS_DIR / PROBLEM 
    PREV_IMPL = PROBLEM_DIR / "implementations" / f"checkpoint_{N-1}"
    PROBLEM_INSTRUCTIONS = PROBLEM_DIR / f"checkpoint_{N}.md"

    # Step 1: Create the agent workspace 
    print("[MAIN 1/6] Creating agent workspace")
    shutil.rmtree(AGENT_WORKSPACE)  # rmdir -r 
    AGENT_WORKSPACE.mkdir(exist_ok=True)  # mkdir -p

    # Step 2: Copy the workspace_helpers folder to the agent workspace 
    print("[MAIN 2/6] Copying helper functions to agent workspace") 
    shutil.copytree(WORKSPACE_HELPERS, AGENT_WORKSPACE / "workspace_helpers")

    # Step 2: Copy the required files to the agent workspace 
    print("[MAIN 3/6] Copying files to agent workspace") 
    shutil.copy(PROBLEM_INSTRUCTIONS, AGENT_WORKSPACE)

    # Write an extra instruction specifying the entrypoint file 
    with open(AGENT_WORKSPACE / f"checkpoint_{N}.md", 'a') as f: 
        f.write("\n## Entrypoint file")
        f.write(f"\nThe entrypoint file must be named `{ENTRY_FILE_NAME}.py`")

    # if N>1, also copy the previous implementation, metrics (?) and deps graph 
    if N>1: 
        if PREV_IMPL.is_dir(): 
            shutil.copytree(PREV_IMPL, AGENT_WORKSPACE / "previous_implementation", symlinks=True)
        else: 
            raise Exception(f"Previous implementation for checkpoint {N-1} does not exist.")
        
        # copy the metrics (is it necessary?) 

        # Generate the deps graph 
        subprocess.run(
            [
                "scripts/deps_graph.sh",
                AGENT_WORKSPACE / "previous_implementation" / f"{ENTRY_FILE_NAME}.py",
                AGENT_WORKSPACE / "deps_graphs"
            ],
            check=True,
        )

        # Extract only the json and svg
        shutil.copy(AGENT_WORKSPACE / "deps_graphs" / "deps_graph.json", 
                    AGENT_WORKSPACE / "current_deps_graph.json")

        shutil.copy(AGENT_WORKSPACE / "deps_graphs" / "deps_graph.svg", 
                    AGENT_WORKSPACE / "original_deps_graph.svg")
        
        # Remove the temp deps_graph/ directory 
        shutil.rmtree(AGENT_WORKSPACE / "deps_graphs")

    # Step 3: Sign in to the agent 
    # subprocess.run([
    #     "python", "-m", "modular_main.login"
    # ], check=True)

    # Step 4: Volume mount 
    agent_workspace_abs = str(AGENT_WORKSPACE.resolve())
    executor = BwrapExecutor(agent_workspace_abs)

    # Step 5: Initial decomposer agent 
    # Run these inside the bind mounted space 
    prompt = get_prompt("decomposer", N)
    output = executor.run([
        "python3", "-m", "workspace_helpers.run_agent", 
        AGENT, MODEL, prompt
    ])

    print(output)
    

if __name__ == "__main__": 
    # Sign in the agent service
    # codex_login_gpt_subscription() 

    # run the modular workflow 
    modular_workflow() 

