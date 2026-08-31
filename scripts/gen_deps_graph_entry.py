"""
Given a directory, write an entrypoint file directly inside it
that imports all python files inside that directory.
"""

import argparse
from pathlib import Path
import os
from constants import IGNORED_DIRS, INVALID_CHARS, BASE_REFERENCE_DIR, IMPL_DIR_DICT


def write_entrypoint(implementation_path, deps_graph_path, entryfile_name):
    target_dir = Path(deps_graph_path)

    with open(target_dir / Path(entryfile_name), "w") as f:
        # walk through the target directory
        for root, dirs, files in os.walk(target_dir):
            # skip the venv directory
            # node_modules contain modules with invalid names (@..). This will cause the graph to break and return an empty graph.
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]

            for pyfile in files:
                if not pyfile.endswith(".py"):
                    continue

                # skip the entrypoint name file
                if pyfile == entryfile_name:
                    continue

                pyfile_path = Path(root) / pyfile
                rel_path = pyfile_path.relative_to(target_dir)
                module = ".".join(rel_path.with_suffix("").parts)

                if module in {"__init__", "__main__"}:
                    continue

                # Convert package.__init__ to "import package"
                if module.endswith(".__init__"):
                    module = module.removesuffix(".__init__")

                # if the module starts with ".agents" (start with .)
                # ignore it because it would cause an import error
                if module.startswith("."):
                    continue

                # if the module name contains invalid characters such as '-',  ignore this as it will crash on import
                if any(chars in module for chars in INVALID_CHARS):
                    continue

                # Apply problem-specific rules if the problem is coming from the base directory
                # Use the original implementation path instead of deps graph graph
                # See constants: the dict: keys are the impl paths, values are the deps graph paths
                if implementation_path.startswith(BASE_REFERENCE_DIR):
                    # Remove the base dir, process through the dict, then join back
                    problem_dir = implementation_path.removeprefix(
                        BASE_REFERENCE_DIR
                    ).removesuffix("/")
                    if problem_dir in IMPL_DIR_DICT:
                        fn = IMPL_DIR_DICT[problem_dir]["processing_fn"]

                        # if the fn returns false, then ignore the module
                        if not fn(module):
                            continue

                f.write(f"import {module}\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("implementation_path", help="directory to the implementation")
    parser.add_argument(
        "deps_graph_path",
        help="the path to generate dependency graph, different for reference problems.",
    )
    parser.add_argument(
        "entryfile_name",
        help="Entryfile name for the temp file that imports all modules",
    )
    args = parser.parse_args()

    write_entrypoint(
        args.implementation_path, args.deps_graph_path, args.entryfile_name
    )


if __name__ == "__main__":
    main()
