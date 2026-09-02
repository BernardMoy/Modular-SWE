from pathlib import Path
import json
import argparse
import os
from reusables.version_sorting import version_key
from scripts.constants import SRC_DIR_DICT
from write_metrics.write_eval_metrics import get_eval_metrics

REFERENCES_DIR = Path("datasets/references")


def get_references_metrics_json():
    """
    Iterate over the references (github) problems
    and generate metrics json in the following format (so they dont have to be re-generated every time):

    {
        "cli": [{... eval metrics}, {...}] over strictly 8 checkpoints, linear interpolated,
        "flask": ...
    }
    """

    data_dict = {}

    for problem in os.listdir(REFERENCES_DIR):
        # ignore custom instructions md
        if problem == "instructions.md":
            continue

        problem_dir = REFERENCES_DIR / problem

        # join dirs with their version numbers
        dirs = sorted(
            [os.path.join(problem_dir, version) for version in os.listdir(problem_dir)],
            key=version_key,
        )

        # do further processing to isolate out the folder you want to analyze, see constants.py
        dirs = [os.path.join(x, SRC_DIR_DICT[problem]) for x in dirs]

        dirs = [Path(x) for x in dirs]

        data_problem = []
        # For each version inside dirs, generate eval metrics
        for dir in dirs:
            print(f"Getting metrics for: {dir}")
            data_problem.append(get_eval_metrics(dir))

        # Do the linear interpolation in the plot
        data_dict[str(problem)] = data_problem

    return data_dict


# usage: write.py [output_json]
# python -m write_metrics.write_references_metrics_json references_metrics.json
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", help="Output json file")
    args = parser.parse_args()

    with open(args.output_dir, "w") as f:
        data = get_references_metrics_json()
        json.dump(data, f, indent=2, default=str)


if __name__ == "__main__":
    main()
