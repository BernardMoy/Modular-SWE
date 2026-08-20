# This assumes the convention that dist/ is the distributable (compiled code) 
# and tests/ are pytest library
# both are safe to ignore otherwise it contains many files 
IGNORED_DIRS = {".venv", "__pycache__", ".git", "dist", "node_modules", ".pytest_cache", "tests"}

# If these characters are present in the module names, importing them will crash
# The imports wont resolve in the temp entrypoint 
number_imports = [f".{x}" for x in range(10)]
INVALID_CHARS = ["-"] + number_imports