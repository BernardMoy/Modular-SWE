#!/usr/bin/env bash 
# Usage: 
# ./deps_graph.sh <problem> <checkpoint_number> 
# This assumes the implementation already exists for the checkpoint number for the problem. 

set -euo pipefail

# Incorrect number of params 
if [[ $# -ne 2 ]]; then
  echo "Usage: ./deps_graph.sh <problem> <checkpoint_number> " >&2
  exit 1
fi

# Obtain the problem and checkpoint number 
PROBLEM="$1"
N="$2"  # checkpoint number 

# Paths constant
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# implementation dir to copy from 
PROBLEM_DIR=$ROOT/datasets/slopCodeBench/scb-problems/$PROBLEM
IMPL_DIR="$PROBLEM_DIR/implementations/checkpoint_$N"
DEPS_GRAPHS_DIR=$PROBLEM_DIR/deps_graphs

# Obtain the entrypoint file name from entry_files.json 
ENTRY_FILE=$(jq -r --arg p "$PROBLEM" '.[$p]' $ROOT/datasets/slopCodeBench/entry_files.json)

# 1. Generate the dependency graph (dot, svg) using pydeps
echo "[1/2] Generating dependency graph..."

mkdir -p $DEPS_GRAPHS_DIR

# generate the svg 
pydeps $IMPL_DIR/$ENTRY_FILE.py \
  -o $DEPS_GRAPHS_DIR/checkpoint_$N.svg \
  --noshow --max-bacon=0

# generate the dot 
pydeps $IMPL_DIR/$ENTRY_FILE.py \
  -T dot --noshow --max-bacon=0 \
  -o $DEPS_GRAPHS_DIR/checkpoint_$N.dot

# 2. Process the graph to generate the json format for the agent to read 
echo "[2/2] Converting the dependency graphs to JSON..."

python process_deps_graph.py \
  $DEPS_GRAPHS_DIR/checkpoint_$N.dot \
  -o $DEPS_GRAPHS_DIR/checkpoint_$N.json

echo "Done."