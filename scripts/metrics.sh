#!/usr/bin/env bash 
# Usage: 
# ./metrics.sh <implementation_path> <output_dir>
# Writes the dpy metrics, pylint metrics separately to the directory. 

set -euo pipefail

# Incorrect number of params 
if [[ $# -ne 2 ]]; then
  echo "Usage: ./metrics.sh <implementation_path> <output_dir>" >&2
  exit 1
fi

# Obtain the impl path and the output dir 
IMPL_DIR="$1"
OUTPUT_DIR="$2"

# Paths constant
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Create the output directory 
mkdir -p "$OUTPUT_DIR"

# 1. Generate the DPy metrics 
echo "[1/2] DPy metrics" 
$ROOT/scripts/DPy analyze -i $IMPL_DIR -o $OUTPUT_DIR/dpy_metrics

# 2. Generate the Pylint metrics 
echo "[2/2] Pylint metrics" 
pylint $IMPL_DIR --min-similarity-lines=20 --ignore=venv,.venv --recursive=y --disable=all --enable=R0801 --ignore-comments=yes --ignore-docstrings=yes --ignore-imports=yes --output-format=json \
>$OUTPUT_DIR/pylint_metrics.json || true

echo "Done."