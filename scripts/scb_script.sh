#!/usr/bin/env bash 
# Usage: 
# ./scb_script.sh <problem> <checkpoint_number> 

set -euo pipefail

# Incorrect number of params 
if [[ $# -ne 2 ]]; then
  echo "Usage: ./scb_script.sh <problem> <checkpoint_number> " >&2
  exit 1
fi

# Obtain the problem and checkpoint number 
PROBLEM="$1"
N="$2"  # checkpoint number 

# Paths constant
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# problem dir to copy from 
PROBLEM_DIR="$ROOT/datasets/slopCodeBench/scb-problems/$PROBLEM"
SOLS_TESTS_DIR="$ROOT/datasets/slopCodeBench/scb-problems-sols-tests/$PROBLEM"
AGENT_WORKSPACE="$ROOT/agent_workspace"

# Obtain the entrypoint file name from entry_files.json 
ENTRY_FILE=$(jq -r --arg p "$PROBLEM" '.[$p]' $ROOT/datasets/slopCodeBench/entry_files.json)

# 1. Make agent workspace dir, and copy to there 
echo "[1/6] Creating agent workspace..."
rm -rf "$AGENT_WORKSPACE"
mkdir -p "$AGENT_WORKSPACE" 

# 2. Copy the required files to the agent workspace folder 
echo "[2/6] Copying files to agent workspace..."
# cp "$PROBLEM_DIR/config.yaml" "$AGENT_WORKSPACE"
cp "$PROBLEM_DIR/checkpoint_${N}.md" "$AGENT_WORKSPACE"

# if N > 1, also copy the previous implementation, deps graph and DPy metrics 
if [[ "$N" -gt 1 ]]; then
  PREV_IMPLEMENTATION="$PROBLEM_DIR/implementations/checkpoint_$((N - 1))"
  if [[ -d "$PREV_IMPLEMENTATION" ]]; then
    echo "[2.1/6] Previous Implementation"  
    cp -r "$PREV_IMPLEMENTATION" "$AGENT_WORKSPACE/"
  else
    echo "Missing previous implementation when working on checkpoint ${N}" >&2
  fi

  # Generate the dependency graph of checkpoint N-1
  # Copy only the JSON file 
  echo "[2.2/6] Dependency Graph"  
  $ROOT/scripts/deps_graph.sh $PROBLEM $((N - 1))
  cp -r "$PROBLEM_DIR/deps_graphs/checkpoint_$((N - 1))_graph.json" "$AGENT_WORKSPACE/"

  # Generate the DPy metrics of checkpoint N-1
  echo "[2.3/6] DPy metrics"  
  $ROOT/scripts/DPy analyze -i $PREV_IMPLEMENTATION -o $PROBLEM_DIR/dpy_metrics/checkpoint_$(((N-1)))_dpy_metrics
  cp -r "$PROBLEM_DIR/dpy_metrics/checkpoint_$((N - 1))_dpy_metrics" "$AGENT_WORKSPACE/"
fi

# 3. Docker volume mount 
# Copy the files in the agent workspace to docker 
echo "[3/6] Running docker container. exit when done..."
docker run --rm -it \
  --user "$(id -u):$(id -g)" \
  -e HOME=/home/bernardmoy \
  -e CHECKPOINT_N="$N" \
  -v "$HOME/.claude:/home/bernardmoy/.claude" \
  -v "$HOME/.claude.json:/home/bernardmoy/.claude.json" \
  -v "$AGENT_WORKSPACE:/agent_workspace" \
  scb bash

# ==== Implement solution (print the command)====
# 4. Move solution back to the implementation folder 
echo "[4/6] Moving solution back..."

# check if solution is implemented in checkpoint_N/ 
CUR_IMPLEMENTATION="$AGENT_WORKSPACE/checkpoint_${N}"
if [[ -d "$CUR_IMPLEMENTATION" ]]; then
  mkdir -p "$PROBLEM_DIR/implementations"
  mv "$CUR_IMPLEMENTATION" "$PROBLEM_DIR/implementations"
else
  echo "Missing implementation for checkpoint_${N} folder" >&2
fi

# 5. Run tests against the implementation for the current checkpoint only 
echo "[5/6] Running tests..."

uv run pytest "$SOLS_TESTS_DIR/tests/test_checkpoint_${N}.py"  \
  --entrypoint "python $PROBLEM_DIR/implementations/checkpoint_${N}/$ENTRY_FILE.py" \
  --checkpoint "checkpoint_${N}"

# 6. Remove the agent_workspace folder 
echo "[6/6] Removing the agent workspace..."
rm -rf "$AGENT_WORKSPACE"
