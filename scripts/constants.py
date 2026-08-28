import os
from pathlib import Path
import time

# This assumes the convention that dist/ is the distributable (compiled code)
# and tests/ are pytest library
# both are safe to ignore otherwise it contains many files
IGNORED_DIRS = {
    ".venv",
    "__pycache__",
    ".git",
    "dist",
    "node_modules",
    ".pytest_cache",
    "tests",
}

# If these characters are present in the module names, importing them will crash
# The imports wont resolve in the temp entrypoint
number_imports = [f".{x}" for x in range(10)]
INVALID_CHARS = ["-"] + number_imports

# The base directory for all implementations for reference modules
BASE_REFERENCE_DIR = "datasets/references/"


# Version numbers for directory matching.
# Given a dataset reference source dir, return a list of direct subfolder names
# e.g. ["v2_0_0", "v3_0_0", ...]
def _get_reference_versions(problem):
    problem_dir = Path(BASE_REFERENCE_DIR) / problem
    return [entry.name for entry in os.scandir(problem_dir) if entry.is_dir()]


# The IMPLEMENTATION DIRECTORY (i.e. src) must be provided
# THIS is the directory you want to analyze metrics (LOC...) on
# which gets mapped to the directory (may be same or different) for generating deps graph
# For example, while we want to analyze tqdm/tqdm, because of how the modules are imported,
# the graph must be called from tqdm/ (path) and then filter modules starting with 'tqdm.' (processing fn)
# Keys (IMPLEMENTATION PATHS) are the paths you want to ANALYZE (they count towards module counts);
# Values (DEPS GRAPH PATHS) are the path used for deps graph generation
IMPL_DIR_DICT = {
    **{
        f"flask/{version}/src": {
            "path": f"flask/{version}",
            "processing_fn": lambda name: name.startswith("src.flask."),
        }
        for version in _get_reference_versions("flask")
    },
    **{
        f"click/{version}/src": {
            "path": f"click/{version}/src",
            "processing_fn": lambda name: name,
        }
        for version in _get_reference_versions("click")
    },
    **{
        f"cli/{version}/httpie/cli": {
            "path": f"cli/{version}",
            "processing_fn": lambda name: name.startswith("httpie.cli"),
        }
        for version in _get_reference_versions("cli")
    },
    **{
        f"fastapi/{version}/fastapi": {
            "path": f"fastapi/{version}",
            "processing_fn": lambda name: name.startswith("fastapi.")
            and ".." not in name,  # avoid fastapi..agents
        }
        for version in _get_reference_versions("fastapi")
    },
    **{
        f"python-dotenv/{version}/src": {
            "path": f"python-dotenv/{version}/src",
            "processing_fn": lambda name: name,
        }
        for version in _get_reference_versions("python-dotenv")
    },
    **{
        f"tqdm/{version}/tqdm": {
            "path": f"tqdm/{version}",
            "processing_fn": lambda name: name.startswith("tqdm."),
        }
        for version in _get_reference_versions("tqdm")
    },
    **{
        f"uvicorn/{version}/uvicorn": {
            "path": f"uvicorn/{version}",
            "processing_fn": lambda name: name.startswith("uvicorn."),
        }
        for version in _get_reference_versions("uvicorn")
    },
    **{
        f"requests/{version}/requests": {
            "path": f"requests/{version}",
            "processing_fn": lambda name: name.startswith("requests."),
        }
        for version in _get_reference_versions("requests")
    },
}
