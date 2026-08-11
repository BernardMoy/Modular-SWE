#!/usr/bin/env bash 
# Usage: 
# ./deps_graph.sh <entrypoint_file> <output_dir>
# Writes the .dot, .svg and .json to that output directory. 

set -euo pipefail

# Incorrect number of params 
if [[ $# -ne 2 ]]; then
  echo "Usage: ./deps_graph.sh <impl_dir> <output_dir>" >&2
  exit 1
fi

# Obtain the impl path and the output dir 
IMPL_DIR="$1"
OUTPUT_DIR="$2"

# Paths constant
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Create the output directory 
mkdir -p "$OUTPUT_DIR"

ENTRYFILE_NAME="temp_entrypoint_123456789"

# 1. Generate missing __init__.py files so that pydeps can recognise them 
echo "[GRAPH 1/6] Generating missing init.py"
python "$ROOT/scripts/gen_missing_init_files.py" "$IMPL_DIR"

# 1. Generate a temporary entrypoint file that imports all python modules
echo "[GRAPH 2/6] Generating temp entrypoint file"
python "$ROOT/scripts/gen_deps_graph_entry.py" "$IMPL_DIR" "$ENTRYFILE_NAME"

# Obtain REAL_MODULES from the entry file (import A; import B) --> REAL_MODULES = (A,B)...
mapfile -t REAL_MODULES < <(sed -n 's/^import //p' "$IMPL_DIR/$ENTRYFILE_NAME.py")

# 2. Generate the dependency graph (dot, svg) using pydeps
# Reversed, meaning A -> B indicates A import B
# include missing, meaning module imports are still visualised in the graph even when they cannot be resolved
echo "[GRAPH 3/6] Generating dependency graph"

# generate the svg
pydeps "$IMPL_DIR/$ENTRYFILE_NAME.py" \
  -o "$OUTPUT_DIR/deps_graph.svg" \
  --noshow --max-bacon=0 --reverse \
  --only "${REAL_MODULES[@]}"

# generate the dot
pydeps "$IMPL_DIR/$ENTRYFILE_NAME.py" \
  -T dot \
  -o "$OUTPUT_DIR/deps_graph.dot" \
  --noshow --max-bacon=0 --reverse \
  --only "${REAL_MODULES[@]}"

# 3. Process the graph to generate the json format for the agent to read
echo "[GRAPH 4/6] Converting the dependency graphs to JSON"

PYTHONPATH="$ROOT" python "$ROOT/scripts/process_deps_graph.py" \
  "$OUTPUT_DIR/deps_graph.dot" \
  -o "$OUTPUT_DIR/deps_graph.json"

# 4. Generate the visibility matrix 
echo "[GRAPH 5/6] Generating visibility matrix"

PYTHONPATH="$ROOT" python "$ROOT/scripts/gen_visibility_matrix.py" \
  "$OUTPUT_DIR/deps_graph.json" \
  -o "$OUTPUT_DIR"

# 5. Remove the temp entry file 
echo "[GRAPH 6/6] Removing temp file"
rm -r $IMPL_DIR/$ENTRYFILE_NAME.py