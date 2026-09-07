from pathlib import Path
import json
import argparse
import os
from write_metrics.write_eval_metrics import get_eval_metrics

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



def get_scb_metrics_json():
    """
    {
        "problem": {
            "impl_dir_name": [{} {} ] one for each checkpoint
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

            # skip if not starting with implementations_ or not dir
            if not os.path.isdir(impl_path) or not impl_name.startswith(
                "implementations_"
            ):
                continue

            # Iterate over all the checkpoints
            impl_checkpoints_paths = sorted(
                [os.path.join(impl_path, n) for n in os.listdir(impl_path)]
            )

            eval_metrics = []
            for p in impl_checkpoints_paths:
                eval_metrics.append(get_eval_metrics(p))

            data_problem[impl_name] = eval_metrics
        data_dict[problem] = data_problem

    return data_dict


# usage: write.py [output_json]
# python -m write_metrics.write_references_metrics_json references_metrics.json
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", help="Output json file")
    args = parser.parse_args()

    with open(args.output_dir, "w") as f:
        data = get_scb_metrics_json()
        json.dump(data, f, indent=2, default=str)


if __name__ == "__main__":
    main()
