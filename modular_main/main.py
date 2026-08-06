"""
Main entrypoint file for the entire workflow. 
"""

import json 
import shutil 
import argparse
from pathlib import Path
from .entry_files import ENTRY_FILES
import subprocess
from .BwrapExecutor import BwrapExecutor
from prompts.get_prompt import get_prompt
from .settings import AGENT, MODEL
from validators.module_name_validator import module_name_validator
from write_metrics.write_metrics_from_design_and_deps_graph import write_metrics_from_design_and_deps_graph
from metrics.deps_graph.bfs import bfs_get_modules_to_implement
from concurrent.futures import ThreadPoolExecutor, as_completed
from write_metrics.write_metrics_from_dpy_pylint_and_deps_graph import write_metrics_from_dpy_pylint_and_deps_graph
from .settings import WORKFLOW_MODE 
from prompts.code_quality_pass_fail import code_quality_pass_fail

# Constants for directory and file paths 
AGENT_WORKSPACE = Path("agent_workspace")
PROBLEMS_DIR = Path("datasets/slopCodeBench/scb-problems")
SOLS_TESTS_DIR= Path("datasets/slopCodeBench/scb-problems-sols-tests")
WORKSPACE_HELPERS = Path("modular_main/workspace_helpers")

# Constants for the modular workflow 
DA_LOOP_THRESHOLD_BEFORE_IMPL = 3  # how many times can the D <> A Loop happen 
DA_LOOP_THRESHOLD_AFTER_IMPL = 1  # how many times can the A <> R loop happen - refers to how many times the RC agent can be invoked 


# Helper function to get prompt and run the agent by passing the prompt inside the bwrap executor 
def get_prompt_and_run_agent(executor, agent_name, *args): 
    prompt = get_prompt(agent_name, *args)
    output = executor.run([
        "python3", "-m", "workspace_helpers.run_agent", 
        AGENT, MODEL, prompt
    ])
    return output 


# Decomposer analyzer loop. 
# D first before A 
# for has impl = False only.
def decomposer_analyzer_loop(executor, checkpoint_number, threshold): 
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
        if v_output_list: 
            raise Exception("Validator failed.")
        print("Passed") 

        # Generate metrics from design and deps graph 
        print(f"========== [Iteration {iteration+1}] GENERATE METRICS ==========")
        write_metrics_from_design_and_deps_graph(
            AGENT_WORKSPACE / "current_design.json", 
            AGENT_WORKSPACE / "current_deps_graph.json", 
            AGENT_WORKSPACE / "current_metrics.json"
        )

        # If the iteration number == 0, also call the pre-analyzer agent 
        # if iteration == 0: 
        #     print(f"========== [Iteration {iteration+1}] PRE-ANALYZER AGENT ==========")
        #     pre_a_output = get_prompt_and_run_agent(executor, "pre_analyzer") 
        #     print(pre_a_output) 

        # Analyzer agent 
        print(f"========== [Iteration {iteration+1}] ANALYZER AGENT ==========")
        a_output = get_prompt_and_run_agent(executor, "analyzer", False)  # has impl = False  

        # If the analyzer return pass, set the passed flag to true 
        a_output_json = json.loads(a_output) 
        print(json.dumps(a_output_json, indent=2))
        if code_quality_pass_fail(a_output_json):  
            passed = True

        # Increment the iteration number 
        iteration += 1 

# Refactor analyzer loop - happens after implementation. 
# A first before R
# For has impl = True only. 
def analyzer_refactor_loop(executor, checkpoint_number, threshold): 
    iteration = 0 
    passed = False 

    # Initial decomposer agent 
    # Run these inside the bind mounted space 
    while (not passed and iteration < threshold): 
        # Update the dependency graph
        print(f"========== [Iteration {iteration+1}] UPDATE DEPENDENCY GRAPH ==========")
        subprocess.run(
            [
                "scripts/deps_graph.sh",
                AGENT_WORKSPACE / "implementation",
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
        
        # Generate metrics using the actual implementation
        print(f"========== [Iteration {iteration+1}] GENERATE METRICS ==========")
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

        # Remove the temporary metrics directory 
        shutil.rmtree(AGENT_WORKSPACE / "metrics")

        # Analyzer agent 
        print(f"========== [Iteration {iteration+1}] ANALYZER AGENT ==========")
        a_output = get_prompt_and_run_agent(executor, "analyzer", True) 

        # If the analyzer return pass, set the passed flag to true 
        a_output_json = json.loads(a_output) 
        print(json.dumps(a_output_json, indent=2))
        if code_quality_pass_fail(a_output_json):  
            passed = True
        
        # if passed, return
        if passed: 
            return 

        # if not passed, then call the refactor agent 
        print(f"========== [Iteration {iteration+1}] REFACTOR CODER AGENT ==========")
        result = get_prompt_and_run_agent(executor, "refactor_coder", checkpoint_number)
        print(result)

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
    PROBLEM_IMPL_DIR = PROBLEM_DIR / f"implementations_{WORKFLOW_MODE}"  # Previous implementation depend on the workflow mode 
    REPORT_DIR = PROBLEM_DIR / f"report_{WORKFLOW_MODE}"  # agent reports 
    PREV_IMPL = PROBLEM_IMPL_DIR / f"checkpoint_{N-1}"
    PROBLEM_INSTRUCTIONS = PROBLEM_DIR / f"checkpoint_{N}.md"

    # Create the problem impl dir and report dir 
    PROBLEM_IMPL_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    # Step 1: Create the agent workspace 
    print("[MAIN 1/8] Creating agent workspace")
    if AGENT_WORKSPACE.exists(): 
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
                AGENT_WORKSPACE / "previous_implementation",
                AGENT_WORKSPACE / "deps_graphs",
            ],
            check=True,
        )

        # Extract only the json and svg
        shutil.copy(AGENT_WORKSPACE / "deps_graphs" / "deps_graph.json", 
                    AGENT_WORKSPACE / "current_deps_graph.json")

        shutil.copy(AGENT_WORKSPACE / "deps_graphs" / "deps_graph.svg", 
                    AGENT_WORKSPACE / "original_deps_graph.svg")
        
        shutil.copy(AGENT_WORKSPACE / "deps_graphs" / "deps_graph.json", 
                    AGENT_WORKSPACE / "original_deps_graph.json")
        
        # Remove the temp deps_graph/ directory 
        shutil.rmtree(AGENT_WORKSPACE / "deps_graphs")

    # copy the rubrics md file 
    shutil.copy("prompts/agent_prompts/rubrics.md", AGENT_WORKSPACE / "rubrics.md")

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

    # if the mode is no design, jump straight to implementation
    if WORKFLOW_MODE == "noDesign": 
        print(f"========== CODING ALL MODULES ==========")
        result = get_prompt_and_run_agent(executor, "no_design_coder", N) 

        # Create a snapshot of the agent report at this point (We want to know the agent's log when IMPLEMENTING the code) 
        # as the agent_report would get overridden below 
        shutil.copy(AGENT_WORKSPACE / "agent_report.json", AGENT_WORKSPACE / "implementation_report.json")

        
        print(result)
    
    else: 
        # Initial decomposer agent 
        # Run these inside the bind mounted space 
        decomposer_analyzer_loop(
            executor=executor, 
            checkpoint_number=N, 
            threshold=DA_LOOP_THRESHOLD_BEFORE_IMPL
        )
        
        # Run the BFS 
        print(f"========== MODULES TO CODE ==========")
        with open(AGENT_WORKSPACE / "current_deps_graph.json", 'r') as f: 
            deps_graph_json = json.load(f)
        
        with open(AGENT_WORKSPACE / "current_design.json", 'r') as f: 
            design_json = json.load(f)

        modules_array = bfs_get_modules_to_implement(
            deps_graph_json, 
            design_json
        )
        print(modules_array)

        # for the all at once mode, implement all modules 
        if WORKFLOW_MODE == "allAtOnce" or WORKFLOW_MODE == "5aspects": 
            result = get_prompt_and_run_agent(executor, "all_at_once_coder", N)
            print(result)
        
        else: 
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
    
        # After implementation: 
        # clear all items inside the current_analyzer_result so the modifications here are not the design level ones we have previously addressed 
        current_analyzer_json = AGENT_WORKSPACE / "current_analyzer_result.json"
        if current_analyzer_json.exists(): 
            current_analyzer_json.unlink() 
        current_analyzer_json.touch() 

        # Create a snapshot of the agent report at this point (We want to know the agent's log when IMPLEMENTING the code) 
        # as the agent_report would get overridden below 
        shutil.copy(AGENT_WORKSPACE / "agent_report.json", AGENT_WORKSPACE / "implementation_report.json")

        # Refactor - Analyzer loop 
        analyzer_refactor_loop(executor, N, DA_LOOP_THRESHOLD_AFTER_IMPL)

    print(f"========== [MAIN 7/8] MOVING SOLUTION BACK ==========")
    
    # Check if the implementation exists 
    implementation = AGENT_WORKSPACE / "implementation"
    IMPLEMENTATION_DEST = PROBLEM_IMPL_DIR / f"checkpoint_{N}"
    REPORT_DEST = REPORT_DIR / f"checkpoint_{N}.json"
    if implementation.is_dir(): 
        # Remove the existing implementation if it exists, otherwise the new one will be merged 
        if IMPLEMENTATION_DEST.exists(): 
            shutil.rmtree(IMPLEMENTATION_DEST) 
        
        # Copy back to the problem implementations folder 
        shutil.copytree(
            implementation, 
            IMPLEMENTATION_DEST, 
            dirs_exist_ok=True, 
            ignore=shutil.ignore_patterns(".venv", "__pycache__", "*.pyc")
        )
        # Also copy the agent report generated after it do its work 
        shutil.copy(
            AGENT_WORKSPACE / "implementation_report.json", 
            REPORT_DEST
        )
    else: 
        raise Exception(f"Missing implementation for checkpoint {N}.")


    # Run the tests and exit 
    print(f"========== [MAIN 8/8] RUNNING TESTS ==========")
    entrypoint = IMPLEMENTATION_DEST / f"{ENTRY_FILE_NAME}.py"

    # Run tests for all previous checkpoints from 1 to N: all of them should still pass 
    for test_no in range(N, 0, -1): 
        print(f"========== TEST FOR CHECKPOINT {test_no} ==========")
        subprocess.run(
            [
                "scripts/pytest.sh",
                PROBLEM,
                entrypoint,
                str(test_no)
            ], 
            check=False  # Allow previous checkpoints to still run even when tests fail 
        )

    # Rank the code quality using some metrics (?) 
    # Probably most accurately using a human controlled method. 

if __name__ == "__main__": 
    # run the modular workflow 
    modular_workflow() 

