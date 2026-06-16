#!/usr/bin/env bash 
# Usage: 
# ./deps_graph.sh <problem> <checkpoint_number> 
# This assumes the implementation already exists for the checkpoint number for the problem.
# the generated deps graph overwrite any existing ones.  

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
# Reversed, meaning A -> B indicates A import B
# include missing, meaning module imports are still visualised in the graph even when they cannot be resolved
echo "[1/2] Generating dependency graph..."

mkdir -p $DEPS_GRAPHS_DIR

# generate the svg 
pydeps $IMPL_DIR/$ENTRY_FILE.py \
  -o $DEPS_GRAPHS_DIR/checkpoint_${N}_graph.svg \
  --noshow --max-bacon=0 --reverse 

# generate the dot 
pydeps $IMPL_DIR/$ENTRY_FILE.py \
  -T dot --noshow --max-bacon=0 \
  -o $DEPS_GRAPHS_DIR/checkpoint_${N}_graph.dot --reverse 

# 2. Process the graph to generate the json format for the agent to read 
echo "[2/2] Converting the dependency graphs to JSON..."

python $ROOT/scripts/process_deps_graph.py \
  $DEPS_GRAPHS_DIR/checkpoint_${N}_graph.dot \
  -o $DEPS_GRAPHS_DIR/checkpoint_${N}_graph.json

echo "Done."