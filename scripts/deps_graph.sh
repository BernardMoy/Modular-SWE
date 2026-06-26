#!/usr/bin/env bash 
# Usage: 
# ./deps_graph.sh <problem> <implementation_path> <output_dir>
# Writes the .dot, .svg and .json to that output directory. 

set -euo pipefail

# Incorrect number of params 
if [[ $# -ne 2 ]]; then
  echo "Usage: ./deps_graph.sh <entrypoint_file> <output_dir>" >&2
  exit 1
fi

# Obtain the impl path and the output dir 
ENTRY_FILE="$1"
OUTPUT_DIR="$2"

# Paths constant
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Create the output directory 
mkdir -p "$OUTPUT_DIR"

# 1. Generate the dependency graph (dot, svg) using pydeps
# Reversed, meaning A -> B indicates A import B
# include missing, meaning module imports are still visualised in the graph even when they cannot be resolved
echo "[GRAPH 1/2] Generating dependency graph..."

# generate the svg
pydeps "$ENTRY_FILE" \
  -o "$OUTPUT_DIR/deps_graph.svg" \
  --noshow --max-bacon=0 --reverse

# generate the dot
pydeps "$ENTRY_FILE" \
  -T dot --noshow --max-bacon=0 \
  -o "$OUTPUT_DIR/deps_graph.dot" --reverse

# 2. Process the graph to generate the json format for the agent to read
echo "[GRAPH 2/2] Converting the dependency graphs to JSON..."

python "$ROOT/scripts/process_deps_graph.py" \
  "$OUTPUT_DIR/deps_graph.dot" \
  -o "$OUTPUT_DIR/deps_graph.json"
