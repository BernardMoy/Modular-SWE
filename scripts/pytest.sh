#!/usr/bin/env bash 
# Usage: 
# ./pytest.sh <problem> <entrypoint_path> <checkpoint_number_to_test_against>
# Give the entrypoint path, not the implementation/ folder. 
set -euo pipefail

# Incorrect number of params 
if [[ $# -ne 3 ]]; then
  echo "Usage: ./pytest.sh <problem> <entrypoint_path> <checkpoint_number_to_test_against>" >&2
  exit 1
fi

# Obtain the problem impl path and the checkpoint number  
PROBLEM=$1
ENTRYPOINT_PATH=$2
CHECKPOINT_NO=$3

# Paths constant
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOLS_TESTS_DIR="$ROOT/datasets/slopCodeBench/scb-problems-sols-tests/$PROBLEM"

# Run the pytest command 
uv run pytest "$SOLS_TESTS_DIR/tests/test_checkpoint_${CHECKPOINT_NO}.py"  \
  --entrypoint "python $ENTRYPOINT_PATH" \
  --checkpoint "checkpoint_${CHECKPOINT_NO}"
