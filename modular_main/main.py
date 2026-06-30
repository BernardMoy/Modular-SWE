"""
Main entrypoint file for the entire workflow. 
"""

import asyncio
import os 
import json 
import shutil 
import argparse
from .auth.codex_login import codex_login_gpt_subscription
from pathlib import Path
from .entry_files import ENTRY_FILES
import subprocess
from .BwrapExecutor import BwrapExecutor
from prompts.get_prompt import get_prompt
from .settings import AGENT, MODEL
from deterministic.validators.module_name_validator import module_name_validator
from deterministic.write_metrics.write_metrics_from_design_and_deps_graph import write_metrics_from_design_and_deps_graph
from deterministic.helpers.deps_graph.bfs import bfs
from concurrent.futures import ThreadPoolExecutor, as_completed
from deterministic.write_metrics.write_metrics_from_dpy_pylint_and_deps_graph import write_metrics_from_dpy_pylint_and_deps_graph

# async def agent_test(model = "gpt-5.5"): 

#     task = """Create a file named fibonacci.py. 
# In the file, include a function named fibonacci(n) that returns the nth fibonacci number.
# """
#     async with AsyncCodex() as codex:  
#         thread = await codex.thread_start(model=model, sandbox=Sandbox.workspace_write, approval_mode=ApprovalMode.deny_all)
#         result = await thread.run(task)
#         print(result.final_response)

# asyncio.run(agent_test())

# Constants for directory and file paths 
AGENT_WORKSPACE = Path("agent_workspace")
PROBLEMS_DIR = Path("datasets/slopCodeBench/scb-problems")
SOLS_TESTS_DIR= Path("datasets/slopCodeBench/scb-problems-sols-tests")
WORKSPACE_HELPERS = Path("modular_main/workspace_helpers")

# Constants for the modular workflow 
DA_LOOP_THRESHOLD_BEFORE_IMPL = 3  # how many times can the D <> A Loop happen 
DA_LOOP_THRESHOLD_AFTER_IMPL = 1 


# Helper function to get prompt and run the agent by passing the prompt inside the bwrap executor 
def get_prompt_and_run_agent(executor, agent_name, *args): 
    prompt = get_prompt(agent_name, *args)
    output = executor.run([
        "python3", "-m", "workspace_helpers.run_agent", 
        AGENT, MODEL, prompt
    ])
    return output 


# Decomposer analyzer loop. 
def decomposer_analyzer_loop(executor, checkpoint_number, has_implementation, threshold): 
    iteration = 0 
    passed = False 

    # Initial decomposer agent 
    # Run these inside the bind mounted space 
    while (not passed and iteration < threshold): 
        print(f"========== [Iteration {iteration+1}] DECOMPOSER AGENT ==========")
        d_output = get_prompt_and_run_agent(executor, "decomposer", checkpoint_number)
        print(d_output)

        # Validator for the module names 
        print(f"========== [Iteration {iteration+1}] VALIDATOR FOR MODULE NAMES ==========")
        v_output = module_name_validator(AGENT_WORKSPACE / "current_design.json", AGENT_WORKSPACE / "current_deps_graph.json")
        
        # Currently, if this array is non empty, throw an error 
        v_output_list = list(v_output) 
        print(v_output_list)
        if v_output_list: 
            raise Exception("Validator failed.")

        # Generate metrics from design and deps graph 
        print(f"========== [Iteration {iteration+1}] GENERATE METRICS ==========")
        write_metrics_from_design_and_deps_graph(
            AGENT_WORKSPACE / "current_design.json", 
            AGENT_WORKSPACE / "current_deps_graph.json", 
            AGENT_WORKSPACE / "current_metrics.json"
        )

        # Analyzer agent 
        print(f"========== [Iteration {iteration+1}] ANALYZER AGENT ==========")
        a_output = get_prompt_and_run_agent(executor, "analyzer", has_implementation) 

        # If the analyzer return pass, set the passed flag to true 
        a_output_json = json.loads(a_output) 
        print(json.dumps(a_output_json, indent=2))
        if a_output_json["result"] == "pass": 
            passed = True

        # Increment the iteration number 
        iteration += 1 


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
    print("[MAIN 1/8] Creating agent workspace")
    shutil.rmtree(AGENT_WORKSPACE)  # rmdir -r 
    AGENT_WORKSPACE.mkdir(exist_ok=True)  # mkdir -p

    # Step 2: Copy the workspace_helpers folder to the agent workspace 
    print("[MAIN 2/8] Copying helper functions to agent workspace") 
    shutil.copytree(WORKSPACE_HELPERS, AGENT_WORKSPACE / "workspace_helpers")

    # Step 3: Copy the required files to the agent workspace 
    print("[MAIN 3/8] Copying files to agent workspace") 
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

    # Step 4: Sign in to the agent 
    print("[MAIN 4/8] Coding agent sign in")
    subprocess.run([
        "python", "-m", "modular_main.login"
    ], check=True)

    # Step 5: Volume mount 
    print("[MAIN 5/8] Agent workspace volume mount")
    agent_workspace_abs = str(AGENT_WORKSPACE.resolve())
    executor = BwrapExecutor(agent_workspace_abs)

    # ================ MAIN WORKFLOW BEGINS ================
    print("[MAIN 6/8] Main workflow")
    # Initial decomposer agent 
    # Run these inside the bind mounted space 
    decomposer_analyzer_loop(
        executor=executor, 
        checkpoint_number=N, 
        has_implementation=False, 
        threshold=DA_LOOP_THRESHOLD_BEFORE_IMPL
    )
    
    # Run the BFS 
    print(f"========== MODULES TO CODE ==========")
    modules_array = bfs(
        AGENT_WORKSPACE / "current_deps_graph.json", 
        AGENT_WORKSPACE / "current_design.json"
    )
    print(modules_array)

    # For each layer of the bfs tree, implement the modules in parallel 
    for layer in modules_array: 
        print(f"========== CODING: {layer} ==========")
        with ThreadPoolExecutor() as exec: 
            # Submit the task of coding each module to the thread pool
            futures = [
                exec.submit(get_prompt_and_run_agent, executor, "modular_coder", N, module)  # Pass the args after the function call name 
                for module in layer
            ]

            for future in as_completed(futures): 
                print(future.result())
    
    # Generate new dependency graph
    print(f"========== UPDATE DEPENDENCY GRAPH ==========")
    subprocess.run(
        [
            "scripts/deps_graph.sh",
            AGENT_WORKSPACE / "implementation" / f"{ENTRY_FILE_NAME}.py",
            AGENT_WORKSPACE / "deps_graphs"
        ],
        check=True,
    )

    # Extract only the json and svg
    shutil.copy(AGENT_WORKSPACE / "deps_graphs" / "deps_graph.json", 
                AGENT_WORKSPACE / "current_deps_graph.json")  # Replace the current deps graph json

    shutil.copy(AGENT_WORKSPACE / "deps_graphs" / "deps_graph.svg", 
                AGENT_WORKSPACE / "current_deps_graph.svg")  # Generate a new svg file 
        
    # Remove the temp deps_graph/ directory 
    shutil.rmtree(AGENT_WORKSPACE / "deps_graphs")


    # Generate metrics 
    print(f"========== GENERATE METRICS ==========")
    subprocess.run(
        [
            "scripts/metrics.sh",
            AGENT_WORKSPACE / "implementation",
            AGENT_WORKSPACE / "metrics"
        ],
        check=True,
    )

    # Write metrics from dpy pylint and deps graph 
    write_metrics_from_dpy_pylint_and_deps_graph(
        AGENT_WORKSPACE / "metrics" / "dpy_metrics", 
        AGENT_WORKSPACE / "metrics" / "pylint_metrics.json", 
        AGENT_WORKSPACE / "current_deps_graph.json", 
        AGENT_WORKSPACE / "current_metrics.json"
    )

    # Run an initial analyzer
    print(f"========== ANALYZER AGENT AFTER IMPL ==========")
    a_output = get_prompt_and_run_agent(executor, "analyzer", True) 
    a_output_json = json.loads(a_output) 
    print(json.dumps(a_output_json, indent=2))

    # If the analyzer returns fail, run the decomposer analyzer loop with has implementation = True 
    # if a_output_json["result"] == "fail": 
    #     decomposer_analyzer_loop(
    #         executor=executor, 
    #         checkpoint_number=N, 
    #         has_implementation=True, 
    #         threshold=DA_LOOP_THRESHOLD_AFTER_IMPL
    #     )

    # Re-run the modular coder 
    # (Inspect what is returned in the current design json first) 

    # Move the solution back from the agent workspace to the problem directory 
    # under problem_name / implementations / checkpoint_N (folder) 
    print(f"========== [MAIN 7/8] MOVING SOLUTION BACK ==========")
    
    # Check if the implementation exists 
    implementation = AGENT_WORKSPACE / "implementation"
    if implementation.is_dir(): 
        # Copy back to the problem implementations folder 
        shutil.copytree(
            implementation, 
            PROBLEM_DIR / "implementations" / f"checkpoint_{N}", 
            dirs_exist_ok=True, 
            ignore=shutil.ignore_patterns(".venv", "__pycache__", "*.pyc")
        )
    else: 
        raise Exception(f"Missing implementation for checkpoint {N}.")


    # Run the tests and exit 
    print(f"========== [MAIN 8/8] RUNNING TESTS ==========")
    entrypoint = PROBLEM_DIR / "implementations" / f"checkpoint_{N}" / f"{ENTRY_FILE_NAME}.py"

    # Run tests for all previous checkpoints from 1 to N: all of them should still pass 
    for test_no in range(N, 0, -1): 
        print(f"========== TEST FOR CHECKPOINT {test_no} ==========")
        subprocess.run(
            [
                "uv", "run", "pytest", 
                SOLS_TESTS_DIR / PROBLEM / "tests" / f"test_checkpoint_{test_no}.py", 
                "--entrypoint", 
                f"python {entrypoint}", 
                "--checkpoint", 
                f"checkpoint_{N}"
            ], 
            check=True
        )

    # Rank the code quality using some metrics (?) 
    # Probably most accurately using a human controlled method. 

if __name__ == "__main__": 
    # Sign in the agent service
    # codex_login_gpt_subscription() 

    # run the modular workflow 
    modular_workflow() 

