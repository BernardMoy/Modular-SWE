"""
Given a directory, create an empty __init__.py in every subfolder if it does not exist.
Otherwise pydeps wont recognise it
"""

import argparse
from pathlib import Path
import os
from constants import IGNORED_DIRS


def gen_missing_init_files(directory):
    target_dir = Path(directory)

    for root, dirs, files in os.walk(target_dir):
        # skip the venv directory
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]

        if root == str(target_dir):
            continue

        if "__init__.py" not in files:
            (Path(root) / "__init__.py").touch()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", help="directory to the implementation")
    args = parser.parse_args()

    gen_missing_init_files(args.directory)


if __name__ == "__main__":
    main()
