import argparse
import os
import subprocess
import shutil
import json
from pathlib import Path
import time


def get_dpy_metrics(implementation_path):
    """
    {
        "number_of_functions": 0,
        "cc_per_function": 0,
        "function_max_loc": 0,
        "function_max_cc": 0,
        "high_cc_functions_count": 0,
        "high_fan_out_classes_count": 0,
        "nopm_per_class": 0,
        "class_max_nopm": 0,
    }
    """

    TEMP_DIR = Path(f"temp_metrics_{str(time.time()).replace(".", "_")}")

    CC_THRESHOLD = 10
    FAN_OUT_THRESHOLD = 3

    counts = {
        "number_of_functions": 0,
        "cc_per_function": 0,
        "function_max_loc": 0,
        "function_max_cc": 0,
        "high_cc_functions_count": 0,
        "high_fan_out_classes_count": 0,
        "nopm_per_class": 0,
        "class_max_nopm": 0,
    }

    # Run the metrics script against the implementation path
    subprocess.run(["scripts/metrics.sh", implementation_path, TEMP_DIR])

    # Read the number of complex functions
    for json_file in os.listdir(TEMP_DIR / "dpy_metrics"):
        if json_file.endswith("class_module_metrics.json"):
            with open(TEMP_DIR / "dpy_metrics" / json_file, "r") as f:
                data = json.load(f)
                counts["high_fan_out_classes_count"] = len(
                    [x for x in data if x["Fan-Out"] >= FAN_OUT_THRESHOLD]
                )
                counts["nopm_per_class"] = sum(x["NOPM"] for x in data) / len(data)
                counts["class_max_nopm"] = max(x["NOPM"] for x in data)

        if json_file.endswith("function_metrics.json"):
            with open(TEMP_DIR / "dpy_metrics" / json_file, "r") as f:
                data = json.load(f)
                counts["high_cc_functions_count"] = len(
                    [x for x in data if x["CC"] >= CC_THRESHOLD]
                )
                counts["function_max_loc"] = max(x["LOC"] for x in data)
                counts["function_max_cc"] = max(x["CC"] for x in data)
                counts["number_of_functions"] = len(data)
                total_cc = sum(x["CC"] for x in data)
                counts["cc_per_function"] = total_cc / len(data)

    # Remove the temp dir
    shutil.rmtree(TEMP_DIR)

    return counts


# usage: write.py [implementation folder path]
# results are printed
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("implementation_path", help="Path to the impl folder")
    args = parser.parse_args()

    metrics = get_dpy_metrics(args.implementation_path)
    print(metrics)


if __name__ == "__main__":
    main()
