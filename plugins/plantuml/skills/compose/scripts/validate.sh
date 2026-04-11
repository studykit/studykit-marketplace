#!/usr/bin/env bash
# Validate PlantUML syntax using bundled jar or system plantuml CLI
# Usage: validate.sh <file.puml> [file2.puml ...]
# Exit code: 0 if all files are valid, 1 if any file has errors

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ $# -eq 0 ]; then
  echo "Usage: $0 <file.puml> [file2.puml ...]"
  exit 1
fi

# Resolve plantuml command: bundled jar > system CLI
PLANTUML_CMD=""
JAR_FILE=$(find "$SCRIPT_DIR" -maxdepth 1 -name 'plantuml*.jar' | head -1)

if [ -n "$JAR_FILE" ]; then
  if ! command -v java &> /dev/null; then
    echo "Warning: Found $JAR_FILE but java is not installed, falling back to system plantuml"
  else
    PLANTUML_CMD="java -jar $JAR_FILE"
  fi
fi

if [ -z "$PLANTUML_CMD" ]; then
  if command -v plantuml &> /dev/null; then
    PLANTUML_CMD="plantuml"
  else
    echo "Error: No plantuml available. Either place a plantuml*.jar in skills/compose/scripts/ or install with: brew install plantuml"
    exit 1
  fi
fi

errors=0
for file in "$@"; do
  if [ ! -f "$file" ]; then
    echo "SKIP: $file (file not found)"
    continue
  fi
  echo -n "Checking $file ... "
  output=$($PLANTUML_CMD -checkonly "$file" 2>&1) || true
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
