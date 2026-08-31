import json
import subprocess
from pathlib import Path
import argparse
import shutil
import os


def _subprocess_env():
    """
    Set the env PATH to the node in the linux machine
    as it would try to call the one in the underlying windows machine.

    If env = _subprocess_env() is not passed,
    when run in a notebook or inside the linux environment
    the temp file would not be generated under the project root modular_swe/.
    """
    env = dict(os.environ)

    nvm_dir = Path.home() / ".nvm" / "versions" / "node"
    if nvm_dir.is_dir():
        for node_version_dir in sorted(nvm_dir.iterdir(), reverse=True):
            bin_dir = node_version_dir / "bin"
            if (bin_dir / "jscpd").exists():
                env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
                break

    return env


## INCONSISTENT with other overall_metrics file: Fix later. Function name should be get_jscpd_metrics
def get_duplicates(implementation_path):
    """
    Return duplicated lines and tokens percentage
    Only duplicates more than 7 lines are added here
    {
        "lines": 0-1,
        "tokens": 0-1,
        "duplicates": [
            {
                "firstFile": "... (line 32-40)",
                "secondFile": "... (line 48-59)",
                "lines_duplicated": 9
            },
            {
                ...
            }
        ]
    }
    """

    duplicates = {"lines": 0, "tokens": 0}

    duplicated_content = []

    subprocess.run(
        # Run jscpd with the default min tokens 50 and min lines 5
        # https://www.npmjs.com/package/jscpd
        [
            "jscpd",
            implementation_path,
            "--reporters",
            "json",
            "--output",
            "temp_duplicates",  # Output is in temp_duplicates / jscpd-report.json
            "--ignore",
            "**/__pycache__/**,**/.venv/**",
            "--silent",
        ],
        capture_output=True,
        text=True,
        shell=False,
        env=_subprocess_env(),
    )

    # Read the temp duplicates folder
    REPORT_PATH = Path("temp_duplicates") / "jscpd-report.json"
    with open(REPORT_PATH, "r") as f:
        report_json = json.load(f)

        # See which lines are the duplicated ones
        # print(json.dumps(report_json, indent=2))

        # Only return the percentage duplicated for lines and tokens
        duplicates["lines"] = report_json["statistics"]["total"]["percentage"] / 100
        duplicates["tokens"] = (
            report_json["statistics"]["total"]["percentageTokens"] / 100
        )

        # Add the duplicated contents
        for entry in report_json["duplicates"]:
            # skip if lines <= 7
            lines = int(entry["lines"])
            if lines <= 7:
                continue

            first = f"{entry["firstFile"]["name"]} (line {entry["firstFile"]["start"]}-{entry["firstFile"]["end"]})"
            second = f"{entry["secondFile"]["name"]} (line {entry["secondFile"]["start"]}-{entry["secondFile"]["end"]})"
            duplicated_content.append(
                {"firstFile": first, "secondFile": second, "lines_duplicated": lines}
            )

    # Now remove the temp duplicates folder
    shutil.rmtree("temp_duplicates")

    # sort and add the duplicated content
    duplicated_content.sort(key=lambda x: x["lines_duplicated"], reverse=True)
    duplicates["duplicates"] = duplicated_content
    return duplicates


# usage: duplicated_lines_density [implementation folder path]
# results are printed
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("implementation_path", help="Path to the impl folder")
    args = parser.parse_args()

    density = get_duplicates(args.implementation_path)

    # print the result
    print(json.dumps(density, indent=2))


if __name__ == "__main__":
    main()
