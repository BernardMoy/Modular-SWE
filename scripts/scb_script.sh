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
cp "$PROBLEM_DIR/checkpoint_${N}.md" "$AGENT_WORKSPACE"

# Add an extra instruction specifying the entrypoint file 
echo "" >> "$AGENT_WORKSPACE/checkpoint_${N}.md"
echo "## Entrypoint file" >> "$AGENT_WORKSPACE/checkpoint_${N}.md"
echo "The entrypoint file must be named \`${ENTRY_FILE}.py\`" >> "$AGENT_WORKSPACE/checkpoint_${N}.md"

# if N > 1, also copy the previous implementation
if [[ "$N" -gt 1 ]]; then
  PREV_IMPLEMENTATION="$PROBLEM_DIR/implementations/checkpoint_$((N - 1))"
  if [[ -d "$PREV_IMPLEMENTATION" ]]; then
    echo "[2.1/6] Previous Implementation"  
    cp -r "$PREV_IMPLEMENTATION" "$AGENT_WORKSPACE/previous_implementation"
  else
    echo "Missing previous implementation when working on checkpoint ${N}" >&2
  fi

  # Generate the dependency graph of checkpoint N-1
  echo "[2.2/6] Dependency Graph"  
  $ROOT/scripts/deps_graph.sh "$PREV_IMPLEMENTATION/$ENTRY_FILE.py" "$AGENT_WORKSPACE/deps_graphs"

  # Generate the DPy and Pylint metrics from the previous impl 
  echo "[2.3/6] DPy and Pylint metrics"
  $ROOT/scripts/metrics.sh $PREV_IMPLEMENTATION "$AGENT_WORKSPACE/metrics"

  # Update the current deps graph json, and copy the svg also 
  echo "[2.4/6] Updating current_deps_graph.json"
  cp -r "$AGENT_WORKSPACE/deps_graphs/deps_graph.json" "$AGENT_WORKSPACE/current_deps_graph.json"
  cp -r "$AGENT_WORKSPACE/deps_graphs/deps_graph.svg" "$AGENT_WORKSPACE/original_deps_graph.svg"  # this wont get updated by the agent 

  # Update the current metrics json 
  echo "[2.5/6] Updating current_metrics.json"
  python -m write_metrics.write_metrics_from_dpy_pylint_and_deps_graph \
  "$AGENT_WORKSPACE/metrics/dpy_metrics" "$AGENT_WORKSPACE/metrics/pylint_metrics.json" "$AGENT_WORKSPACE/current_deps_graph.json" \
  "$AGENT_WORKSPACE/current_metrics.json"

  # Delete the copied directories above, to limit what the agent can see 
  echo "[2.6/6] Deleting unnecessary directories"
  rm -rf "$AGENT_WORKSPACE/deps_graphs"
  rm -rf "$AGENT_WORKSPACE/metrics"
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
  --workdir /agent_workspace \
  scb bash

# ==== Implement solution (print the command)====
# 4. Move solution back to the implementation folder 
echo "[4/6] Moving solution back..."

# check if solution is implemented in checkpoint_N/ 
# the solution must be renamed from previous_implementation/ to implementation/ 
CUR_IMPLEMENTATION="$AGENT_WORKSPACE/implementation"
if [[ -d "$CUR_IMPLEMENTATION" ]]; then
  # Copy the implementation back to the datasets folder
  mkdir -p "$PROBLEM_DIR/implementations/checkpoint_${N}"
  cp -r "$CUR_IMPLEMENTATION/." "$PROBLEM_DIR/implementations/checkpoint_${N}"
else
  echo "Missing implementation." >&2
fi

# 5. Run tests against the implementation for the current checkpoint only 
echo "[5/6] Running tests..."

uv run pytest "$SOLS_TESTS_DIR/tests/test_checkpoint_${N}.py"  \
  --entrypoint "python $PROBLEM_DIR/implementations/checkpoint_${N}/$ENTRY_FILE.py" \
  --checkpoint "checkpoint_${N}" # || true

# 6. Remove the agent_workspace folder 
# echo "[6/6] Removing the agent workspace..."
# rm -rf "$AGENT_WORKSPACE"
