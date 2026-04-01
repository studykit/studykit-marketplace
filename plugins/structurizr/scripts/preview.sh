#!/bin/bash
# Render a Structurizr DSL file to PNG images locally
# Usage: bash preview.sh <path-to-dsl-file>
#
# Pipeline: structurizr (export to PlantUML) -> plantuml (render to PNG)
# Prerequisites: brew install structurizr plantuml

set -e

DSL_FILE="${1:?Usage: preview.sh <path-to-dsl-file>}"

if [ ! -f "$DSL_FILE" ]; then
    echo "Error: File not found: $DSL_FILE"
    exit 1
fi

# Check dependencies
if ! command -v structurizr &>/dev/null; then
    echo "Error: structurizr not found. Install with: brew install structurizr"
    exit 1
fi

if ! command -v plantuml &>/dev/null; then
    echo "Error: plantuml not found. Install with: brew install plantuml"
    exit 1
fi

DSL_DIR="$(cd "$(dirname "$DSL_FILE")" && pwd)"
DSL_NAME="$(basename "$DSL_FILE")"
WORK_DIR=$(mktemp -d)

echo "1/3 Exporting DSL to PlantUML ..."
structurizr export -w "$DSL_DIR/$DSL_NAME" -format plantuml -output "$WORK_DIR"

PUML_COUNT=$(ls "$WORK_DIR"/*.puml 2>/dev/null | wc -l | tr -d ' ')
if [ "$PUML_COUNT" -eq 0 ]; then
    echo "Error: No PlantUML files generated"
    rm -rf "$WORK_DIR"
    exit 1
fi

echo "2/3 Rendering $PUML_COUNT diagram(s) to PNG ..."
plantuml -tpng "$WORK_DIR"/*.puml

echo "3/3 Moving outputs ..."
OUTPUT_DIR="$DSL_DIR"
mv "$WORK_DIR"/*.png "$OUTPUT_DIR/" 2>/dev/null

echo ""
echo "Rendered diagrams:"
for png in "$OUTPUT_DIR"/*.png; do
    [ -f "$png" ] && echo "  $png"
done

# Open all rendered PNGs
for png in "$OUTPUT_DIR"/*.png; do
    [ -f "$png" ] && open "$png"
done

# Cleanup
rm -rf "$WORK_DIR"
