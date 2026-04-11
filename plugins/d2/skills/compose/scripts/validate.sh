#!/usr/bin/env bash
# Validate D2 syntax without producing output files
# Usage: validate.sh <file.d2> [file2.d2 ...]
# Exit code: 0 if all files are valid, 1 if any file has errors
# Prerequisites: brew install d2

set -euo pipefail

if [ $# -eq 0 ]; then
  echo "Usage: $0 <file.d2> [file2.d2 ...]"
  exit 1
fi

if ! command -v d2 &>/dev/null; then
  echo "Error: d2 not found. Install with: brew install d2"
  exit 1
fi

errors=0
for file in "$@"; do
  if [ ! -f "$file" ]; then
    echo "SKIP: $file (file not found)"
    continue
  fi
  echo -n "Checking $file ... "
  WORK_DIR=$(mktemp -d)
  output=$(d2 "$file" "$WORK_DIR/out.svg" 2>&1) && status=0 || status=$?
  rm -rf "$WORK_DIR"
  if [ $status -ne 0 ]; then
    echo "FAIL"
    echo "$output"
    errors=$((errors + 1))
  else
    echo "OK"
  fi
done

if [ $errors -gt 0 ]; then
  echo ""
  echo "$errors file(s) with errors"
  exit 1
else
  echo ""
  echo "All files valid"
  exit 0
fi
