#!/usr/bin/env bash 
# Usage: 
# ./pytest_custom.sh <custom_problem> <implementation_path> <checkpoint_number_to_test_against>
# Give the entrypoint path, not the implementation/ folder. 
set -euo pipefail

# Incorrect number of params 
if [[ $# -ne 3 ]]; then
  echo "Usage: ./pytest.sh <problem> <implementation_path> <checkpoint_number_to_test_against>" >&2
  exit 1
fi

# Obtain the problem impl path and the checkpoint number  
PROBLEM=$1
IMPLEMENTATION_PATH=$2
CHECKPOINT_NO=$3

# Paths constant
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TESTS_DIR="$ROOT/datasets/custom/tests/$PROBLEM"

# Run the pytest command 
pytest "$TESTS_DIR/test_checkpoint_${CHECKPOINT_NO}.py"  \
  --implementation $IMPLEMENTATION_PATH
