from pathlib import Path 
import subprocess 
import shutil 
import argparse 
from ..BwrapExecutor import BwrapExecutor
from ..settings import WORKFLOW_MODE, AGENT, MODEL
from ..get_prompt_and_run_agent import get_prompt_and_run_agent

AGENT_WORKSPACE = Path("agent_workspace_test")


def workflow(): 
    parser = argparse.ArgumentParser()
    parser.add_argument("problem_name", help="Name of the problem")
    parser.add_argument("checkpoint_number", help="Checkpoint number")
    args = parser.parse_args()

    # Obtain the problem name and checkpoint no from arguments
    PROBLEM = args.problem_name 
    N = int(args.checkpoint_number) 

    # Identify the tests directory here
    # If the problem does not have a corresponding testing directory, skip 
    TEST_FILE = Path(f"datasets/custom/tests/{PROBLEM}/test_checkpoint_{N}.py")
    CONFTEST_FILE = Path(f"datasets/custom/tests/{PROBLEM}/conftest.py")
    if not TEST_FILE.exists(): 
        print(f"Tests does not exist for {PROBLEM} checkpoint {N}: exiting.")
        return 

    print("[1/3] CREATING AGENT WORKSPACE")
    if AGENT_WORKSPACE.exists(): 
        shutil.rmtree(AGENT_WORKSPACE)  # rmdir -r 
    AGENT_WORKSPACE.mkdir(exist_ok=True)  # mkdir -p

    # Copy the implementation 
    IMPL_PATH = Path(f"datasets/custom/problems/{PROBLEM}/implementations_{WORKFLOW_MODE}_{AGENT}_{MODEL}/checkpoint_{N}")
    CHECKPOINT_PATH = Path(f"datasets/custom/problems/{PROBLEM}/checkpoint_{N}.md")
    WORKSPACE_HELPERS = Path("modular_main/workspace_helpers")
    shutil.copytree(WORKSPACE_HELPERS, AGENT_WORKSPACE / "workspace_helpers")
    shutil.copytree(IMPL_PATH, AGENT_WORKSPACE / "implementation")
    shutil.copy(CHECKPOINT_PATH, AGENT_WORKSPACE / f"checkpoint_{N}.md")

    # Copy the test file 
    if CONFTEST_FILE.exists(): 
        shutil.copy(CONFTEST_FILE, AGENT_WORKSPACE / "conftest.py")
    shutil.copy(TEST_FILE, AGENT_WORKSPACE / "test_script.py")

    # Agent sign in 
    print("[2/3] Agent sign in")
    subprocess.run([
            "python", "-m", "modular_main.login"
        ], check=True)

    # Single agent prompt to allow the agent to run tests + Fix issues
    # Target is to see how much effort is required to fix the tests + whether code quality is preserved after that 
    print("[3/3] Agent prompt")
    agent_workspace_abs = str(AGENT_WORKSPACE.resolve())
    executor = BwrapExecutor(agent_workspace_abs)
    get_prompt_and_run_agent(executor, "test_refactor_coder", N)

if __name__ == "__main__": 
    workflow() 