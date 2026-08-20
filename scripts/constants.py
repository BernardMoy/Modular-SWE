# This assumes the convention that dist/ is the distributable (compiled code) 
# and tests/ are pytest library
# both are safe to ignore otherwise it contains many files 
IGNORED_DIRS = {".venv", "__pycache__", ".git", "dist", "node_modules", ".pytest_cache", "tests"}

# If these characters are present in the module names, importing them will crash
# The imports wont resolve in the temp entrypoint 
number_imports = [f".{x}" for x in range(10)]
INVALID_CHARS = ["-"] + number_imports

BASE_IMPL_DIR = "datasets/references"

"""
Instructions on adding a new reference module: 
1. Add to the impl dir dict which is the directory that the deps graph script should point to
2. Sometimes due to how the modules are imported, the directory has to be the outer one. However this may include some directories we are not interested in, such as docs / tests. 
In this case, add a rule to filter them in reference_rules.py 
"""
IMPL_DIR_DICT = {
    "tqdm": "tqdm", 
    "python-dotenv": "python-dotenv/src/"
}

