"""
Metrics related to agent token usages or their behaviours. 
"""

import argparse
import json
from collections import Counter


def get_report_metrics(report_path):
    """
    {
        "call_types": ...
        "exit_code_not_0_count": 0,
        "total_duration": 0,
    }
    """

    with open(report_path, "r") as f:
        graph = json.load(f)

    log = graph["log"]
    call_types = Counter(item.get("type") for item in log)
    exit_code_not_0_count = len(
        [x for x in log if "exit_code" in x and x["exit_code"] != 0]
    )
    total_duration = sum(x.get("duration_ms", 0) for x in log)

    return {
        "call_types": call_types,
        "exit_code_not_0_count": exit_code_not_0_count,
        "total_duration": total_duration,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("agent_report_path", help="Path to the agent report json")
    args = parser.parse_args()

    metrics = get_report_metrics(args.agent_report_path)
    print(metrics)


if __name__ == "__main__":
    main()
