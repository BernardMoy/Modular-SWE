import os
import subprocess
import argparse
from pathlib import Path
import json


# Return in json format the summary:
# return --> { "passed": 46, "failed": 5, "total": 51, "collected": 51 },
def pytest_scb(problem_name, entrypoint_path, checkpoint_number_to_test_against):
    SOLS_TESTS_DIR = Path(
        f"datasets/slopCodeBench/scb-problems-sols-tests/{problem_name}"
    )
    TEST_SOURCE = (
        f"{SOLS_TESTS_DIR}/tests/test_checkpoint_{checkpoint_number_to_test_against}.py"
    )
    TEST_REPORT_FILE = Path(
        f"test_report_{problem_name}_{checkpoint_number_to_test_against}.json"
    )

    subprocess.run(
        [
            "uv",
            "run",
            "pytest",
            TEST_SOURCE,
            "--entrypoint",
            f"python {entrypoint_path}",
            "--checkpoint",
            f"checkpoint_{checkpoint_number_to_test_against}",
            "--json-report",
            "--json-report-file",
            TEST_REPORT_FILE,
        ],
        check=False,  # Suppress the error generated if pytest fails
        text=True,
    )

    if not TEST_REPORT_FILE.exists():
        print("Failed to run tests.")

    # Read the test report generated to obtain the test pass / fail summary for further processing
    with open(TEST_REPORT_FILE, "r") as f:
        report = json.load(f)
        test_summary = report["summary"]

    # Remove the generated test report file
    TEST_REPORT_FILE.unlink()

    # Return the test summary
    return test_summary


# pytest_scb.py <problem> <entrypoint_path> <checkpoint_number_to_test_against>
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("problem_name", help="Name of the scb problem")
    parser.add_argument(
        "entrypoint_path", help="abs path to the entrypoint of the scb problem"
    )
    parser.add_argument(
        "checkpoint_no",
        help="Checkpoint number to test against, can be different from that in the path",
    )
    args = parser.parse_args()

    result = pytest_scb(args.problem_name, args.entrypoint_path, args.checkpoint_no)
    print(result)


if __name__ == "__main__":
    main()
