from pathlib import Path
import json
import argparse
import os
from write_metrics.write_eval_metrics import get_eval_metrics
from modular_main.entry_files import ENTRY_FILES
from scripts.pytest_scb import pytest_scb

# Problems - modes mapping.
# Some modes such as auto by layer only exists in some problems.
# PROBLEMS = {
#     "code_search": ["noDesign", "auto", "autoNoMetric", "autoTest"],
#     "circuit_eval": ["noDesign", "auto", "autoNoMetric", "autoTest", "autoByLayer"],
#     "mocked_http": ["noDesign", "auto", "autoNoMetric", "autoTest"],
#     "recli": ["noDesign", "auto", "autoNoMetric", "autoTest", "autoByLayer"],
#     "sheeteval": ["noDesign", "auto", "autoNoMetric", "autoTest"],
#     "sith": ["noDesign", "auto", "autoNoMetric", "autoTest"],
#     "eve_industry": ["noDesign", "auto", "autoNoMetric", "autoTest"],
#     "metric_transform_lang": ["noDesign", "auto", "autoNoMetric", "autoTest"],
# }

# For simplicity, the keys used are simply the implementation folders
SCB_DIR = Path("datasets/slopCodeBench/scb-problems")
PROBLEMS = [
     "code_search", "circuit_eval", "etl_pipeline", "meshctl", "mocked_http", "recli", "sheeteval", "sith"
    ]


def get_scb_test_metrics_json():
    """
    {
        "problem": {
            "impl_dir_name": [
                {
                    "current": 0, 
                    "prev": 0, 
                    "all": 0 
                }, 
                {} 
            ]  one for each checkpoint
        }
    }
    """

    data_dict = {}

    for problem in PROBLEMS:
        problem_path = SCB_DIR / problem

        data_problem = {}

        # Iterate over all the impl modes
        for impl_name in os.listdir(problem_path):
            impl_path = problem_path / impl_name

            # skip if not starting with implementation_ or not dir
            if not os.path.isdir(impl_path) or not impl_name.startswith("implementations_"):
                continue

            # Iterate over all the checkpoints
            impl_checkpoints_paths = sorted(
                [os.path.join(impl_path, n) for n in os.listdir(impl_path)]
            )

            tests_metrics = [] 

            # walk through each checkpoint 
            for i, impl_dir in enumerate(impl_checkpoints_paths): 
                # build the entrypoint path 
                entrypoint_path = Path(f"{impl_dir}/{ENTRY_FILES[problem]}.py")
    
                # run tests for checkpoint from N to 1 
                current_tests_ran = 0 
                current_tests_success = 0 
                prev_tests_ran = 0 
                prev_tests_success = 0 

                current_checkpoint = i+1
                for cp in range(current_checkpoint, 0, -1): 
                    result = pytest_scb(
                        problem_name=problem, 
                        entrypoint_path=entrypoint_path, 
                        checkpoint_number_to_test_against=cp
                    )
    
                    # append to current if it is the latest checkpoint test, else append to prev 
                    if cp == current_checkpoint: 
                        current_tests_ran += result.get("total", 0)
                        current_tests_success += result.get("passed", 0)
                    else: 
                        prev_tests_ran += result.get("total", 0)
                        prev_tests_success += result.get("passed", 0)

                # add to test data after running all current + prev tests 
                tests_metrics.append({
                    "current": current_tests_success/current_tests_ran if current_tests_ran>0 else 1,
                    "prev": prev_tests_success/prev_tests_ran if prev_tests_ran>0 else 1, 
                    "all": (current_tests_success + prev_tests_success)/(current_tests_ran + prev_tests_ran) if (current_tests_ran + prev_tests_ran)>0 else 1

                })

            data_problem[impl_name] = tests_metrics
        data_dict[problem] = data_problem
    return data_dict


# usage: write.py [output_json]
# python -m write_metrics.write_references_metrics_json references_metrics.json
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", help="Output json file")
    args = parser.parse_args()

    with open(args.output_dir, "w") as f:
        data = get_scb_test_metrics_json()
        json.dump(data, f, indent=2, default=str)


if __name__ == "__main__":
    main()
