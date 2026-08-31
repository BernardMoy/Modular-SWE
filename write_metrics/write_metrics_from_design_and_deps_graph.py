import json
import argparse
from metrics.deps_graph.metrics import get_metrics_from_deps_graph
from metrics.design.summary.get_summary import get_summary
from metrics.design.metrics import get_metrics_from_design
from reusables.sort_smells import sort_smells


def write_metrics_from_design_and_deps_graph(
    design_path, deps_graph_path, current_metrics_path
):
    # Read the JSON design from the path
    with open(design_path, "r") as f:
        design_json = json.load(f)

    # Read the JSON graph from the path
    with open(deps_graph_path, "r") as f:
        graph_json = json.load(f)

    # Concat the deps graph and the design metrics
    smells = get_metrics_from_deps_graph(graph_json) + get_metrics_from_design(
        design_json
    )

    # Sort smells
    smells = sort_smells(smells)

    # # Obtain the summary json
    # summary = get_summary(design_json)

    # # Combine summary and smells into the output json
    # output_json = {
    #     "summary": summary,
    #     "smells": smells
    # }

    # Write the smells to current metrics
    with open(current_metrics_path, "w") as f:
        f.write(json.dumps(smells, indent=2))


# usage: write.py [current_design_path] [current_deps_graph_path] [current_metrics_output_path]
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "design_path",
        help="Current design file, should be in the second iter only to ensure the public_interface field exists",
    )
    parser.add_argument(
        "deps_graph_path", help="Abs path to the dependency graph JSON file"
    )
    parser.add_argument("current_metrics_path", help="Abs path to write the metrics to")
    args = parser.parse_args()

    write_metrics_from_design_and_deps_graph(
        args.design_path, args.deps_graph_path, args.current_metrics_path
    )


if __name__ == "__main__":
    main()
