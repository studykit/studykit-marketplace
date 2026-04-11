#!/usr/bin/env bash
# Validate Structurizr DSL syntax without producing output files
# Usage: validate.sh <file.dsl> [file2.dsl ...]
# Exit code: 0 if all files are valid, 1 if any file has errors
# Prerequisites: brew install structurizr

set -euo pipefail

if [ $# -eq 0 ]; then
  echo "Usage: $0 <file.dsl> [file2.dsl ...]"
  exit 1
fi

if ! command -v structurizr &>/dev/null; then
  echo "Error: structurizr not found. Install with: brew install structurizr"
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
  ABS_FILE="$(cd "$(dirname "$file")" && pwd)/$(basename "$file")"
  output=$(structurizr export -w "$ABS_FILE" -format plantuml -output "$WORK_DIR" 2>&1) && status=0 || status=$?
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
