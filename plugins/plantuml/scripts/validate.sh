#!/usr/bin/env bash
# Validate PlantUML syntax using local plantuml CLI (brew install plantuml)
# Usage: validate.sh <file.puml> [file2.puml ...]
# Exit code: 0 if all files are valid, 1 if any file has errors

set -euo pipefail

if [ $# -eq 0 ]; then
  echo "Usage: $0 <file.puml> [file2.puml ...]"
  exit 1
fi

if ! command -v plantuml &> /dev/null; then
  echo "Error: plantuml is not installed. Install with: brew install plantuml"
  exit 1
fi

errors=0
for file in "$@"; do
  if [ ! -f "$file" ]; then
    echo "SKIP: $file (file not found)"
    continue
  fi
  echo -n "Checking $file ... "
  output=$(plantuml -checkonly "$file" 2>&1) || true
  if echo "$output" | grep -qi "error"; then
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
