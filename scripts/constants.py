# This assumes the convention that dist/ is the distributable (compiled code) 
# and tests/ are pytest library
# both are safe to ignore otherwise it contains many files 
IGNORED_DIRS = {".venv", "__pycache__", ".git", "dist", "node_modules", ".pytest_cache", "tests"}

# If these characters are present in the module names, importing them will crash
# The imports wont resolve in the temp entrypoint 
number_imports = [f".{x}" for x in range(10)]
INVALID_CHARS = ["-"] + number_imports

# temp entrypoint file containing imports to all modules 
ENTRYFILE_NAME="temp_entrypoint_123456789.py"

# The base directory for all implementations for reference modules 
BASE_REFERENCE_DIR = "datasets/references/"

# Version numbers for directory matching. 
# These should be inferred by reading the files instead of being hard coded here 
FLASK_VERSIONS = ["v2_0_0", "v2_3_0", "v3_0_0", "v3_1_3"]

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
            "processing_fn": lambda name: name.startswith("src.flask.")
        } for version in FLASK_VERSIONS
    }
}
#     "tqdm/tqdm": {
#         "path": "tqdm", 
#         "processing_fn": lambda name: name.startswith("tqdm.")
#     }, 
#     "python-dotenv/src": {
#         "path": "python-dotenv/src", 
#         "processing_fn": lambda name: name
#     }, 
#     "click/src": {
#         "path": "click/src", 
#         "processing_fn": lambda name: name
#     }, 
#     "fastapi/fastapi": {
#         "path": "fastapi", 
#         "processing_fn": lambda name: name.startswith("fastapi.") and ".." not in name  # avoid fastapi..agents 
#     }, 
#     "flask/2.0.0/src": {
#         "path": "flask/2.0.0", 
#         "processing_fn": lambda name: name.startswith("src.flask.")
#     }, 
#     "uvicorn/uvicorn": {
#         "path": "uvicorn", 
#         "processing_fn": lambda name: name.startswith("uvicorn.")
#     }, 
#     "requests/src": {
#         "path": "requests/src", 
#         "processing_fn": lambda name: name
#     }, 
#     "cli/httpie/cli": {
#         "path": "cli", 
#         "processing_fn": lambda name: name.startswith("httpie.cli.")
#     }
# }

