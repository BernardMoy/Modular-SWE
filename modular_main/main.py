"""
Main entrypoint file for the entire workflow. 
"""

import asyncio
import os 
import shutil 
import argparse
from openai_codex import AsyncCodex, Codex, Sandbox, ApprovalMode
from .codex_login import codex_login_gpt_subscription
from pathlib import Path
from .entry_files import ENTRY_FILES

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
    ENTRY_FILE = ENTRY_FILES[PROBLEM]

    PROBLEM_DIR = PROBLEMS_DIR / PROBLEM 

    # Step 1: Create the agent workspace 
    print("[MAIN 1/6] Creating agent workspace")
    shutil.rmtree(AGENT_WORKSPACE)  # rmdir -r 
    AGENT_WORKSPACE.mkdir(exist_ok=True)  # mkdir -p

    # Step 2: Copy the required files to the agent workspace 
    print("[MAIN 2/6] Copying files to agent workspace") 
    problem_instructions = PROBLEM_DIR / f"checkpoint_{N}.md"
    shutil.copy(problem_instructions, AGENT_WORKSPACE)

    # Write an extra instruction specifying the entrypoint file 
    workspace_instruction_file = AGENT_WORKSPACE / f"checkpoint_{N}.md"
    with open(workspace_instruction_file, 'a') as f: 
        f.write("\n## Entrypoint file")
        f.write(f"\nThe entrypoint file must be named `{ENTRY_FILE}.py`")

    # if N>1, also copy the previous implementation and the metrics 
    if N>1: 
        prev_impl = PROBLEM_DIR / "implementations" / f"checkpoint_{N-1}"
        impl_dest = AGENT_WORKSPACE / "previous_implementation"

        if prev_impl.is_dir(): 
            shutil.copytree(prev_impl, impl_dest, symlinks=True)
        else: 
            raise Exception(f"Previous implementation for checkpoint {N-1} does not exist.")
        
        # copy the metrics (is it necessary?) 

        # Generate the deps graph 
    
    # Step 3: 

if __name__ == "__main__": 
    # Sign in the agent service
    # codex_login_gpt_subscription() 

    # run the modular workflow 
    modular_workflow() 

