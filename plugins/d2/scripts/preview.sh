#!/bin/bash
# Render a D2 file to PNG and open it
# Usage: bash preview.sh <path-to-d2-file> [theme-id] [layout-engine]
#
# theme-id: 3 (default, Flagship Terrastruct). Run `d2 themes` for full list.
# layout-engine: dagre (default), elk
# Prerequisites: brew install d2

set -e

D2_FILE="${1:?Usage: preview.sh <path-to-d2-file> [theme-id] [layout-engine]}"
THEME="${2:-3}"
LAYOUT="${3:-}"

if [ ! -f "$D2_FILE" ]; then
    echo "Error: File not found: $D2_FILE"
    exit 1
fi

if ! command -v d2 &>/dev/null; then
    echo "Error: d2 not found. Install with: brew install d2"
    exit 1
fi

D2_DIR="$(cd "$(dirname "$D2_FILE")" && pwd)"
D2_NAME="$(basename "$D2_FILE" .d2)"

OUTPUT="$D2_DIR/${D2_NAME}.png"

LAYOUT_FLAG=""
if [ -n "$LAYOUT" ]; then
    LAYOUT_FLAG="--layout $LAYOUT"
fi

echo "Rendering $D2_FILE to PNG (theme: $THEME, layout: ${LAYOUT:-dagre}) ..."
d2 --theme "$THEME" $LAYOUT_FLAG "$D2_FILE" "$OUTPUT"

echo ""
echo "Rendered diagram: $OUTPUT"

open "$OUTPUT"
