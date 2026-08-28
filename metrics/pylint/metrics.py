import argparse
import json

# Given a dependency graph in JSON
# Return all duplicate lines of code with lines >= 20
# Change this in the scb script, may refactor this later

# UNUSED - replaced by jscpd


def check_duplicated_lines_of_code(json_object):
    """
    Return in the format
    [
        {
            "Category": "Design level",
            "Module": "...",
            "Smell": "Duplicate code",
            "Description": copy the message field of pylint
        },
        ...
    ]
    """

    dups = []
    # for entry in json_object:
    #     dups.append({
    #         "Category": "Design level",
    #         "Module": entry["module"],
    #         "Smell": "Duplicate code",
    #         "Description": entry["message"]
    #     })

    return dups


# usage: check.py [pylint-json]
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Abs path to the Pylint JSON file")
    args = parser.parse_args()

    # Read the JSON graph from the path
    with open(args.path, "r") as f:
        graph_json = json.load(f)

    result = check_duplicated_lines_of_code(json_object=graph_json)
    print(result)


if __name__ == "__main__":
    main()
