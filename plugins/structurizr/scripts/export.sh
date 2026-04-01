#!/bin/bash
# Export a Structurizr DSL file to various formats locally
# Usage: bash export.sh <path-to-dsl-file> [format]
#
# Formats: png (default), svg, plantuml, mermaid
# Prerequisites: brew install structurizr plantuml

set -e

DSL_FILE="${1:?Usage: export.sh <path-to-dsl-file> [png|svg|plantuml|mermaid]}"
FORMAT="${2:-png}"

if [ ! -f "$DSL_FILE" ]; then
    echo "Error: File not found: $DSL_FILE"
    exit 1
fi

if ! command -v structurizr &>/dev/null; then
    echo "Error: structurizr not found. Install with: brew install structurizr"
    exit 1
fi

DSL_DIR="$(cd "$(dirname "$DSL_FILE")" && pwd)"
DSL_NAME="$(basename "$DSL_FILE")"

case "$FORMAT" in
    png|svg)
        if ! command -v plantuml &>/dev/null; then
            echo "Error: plantuml not found. Install with: brew install plantuml"
            exit 1
        fi
        WORK_DIR=$(mktemp -d)
        structurizr export -w "$DSL_DIR/$DSL_NAME" -format plantuml -output "$WORK_DIR"
        plantuml -t"$FORMAT" "$WORK_DIR"/*.puml
        mv "$WORK_DIR"/*."$FORMAT" "$DSL_DIR/" 2>/dev/null
        rm -rf "$WORK_DIR"
        echo "Exported $FORMAT files to: $DSL_DIR"
        ;;
    plantuml)
        structurizr export -w "$DSL_DIR/$DSL_NAME" -format plantuml -output "$DSL_DIR"
        echo "Exported PlantUML files to: $DSL_DIR"
        ;;
    mermaid)
        structurizr export -w "$DSL_DIR/$DSL_NAME" -format mermaid -output "$DSL_DIR"
        echo "Exported Mermaid files to: $DSL_DIR"
        ;;
    *)
        echo "Unknown format: $FORMAT (supported: png, svg, plantuml, mermaid)"
        exit 1
        ;;
esac

ls "$DSL_DIR"/*."${FORMAT}" "$DSL_DIR"/*.puml "$DSL_DIR"/*.mmd 2>/dev/null
