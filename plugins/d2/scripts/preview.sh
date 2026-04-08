#!/bin/bash
# Render a D2 file to PNG
# Usage: bash preview.sh <path-to-d2-file> [theme-id] [layout-engine]
#
# theme-id: 3 (default, Flagship Terrastruct). Run `d2 themes` for full list.
# layout-engine: elk (default), dagre
# Prerequisites: brew install d2

set -e

D2_FILE="${1:?Usage: preview.sh <path-to-d2-file> [theme-id] [layout-engine]}"
THEME="${2:-3}"
LAYOUT="${3:-elk}"

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

echo "Rendering $D2_FILE to PNG (theme: $THEME, layout: $LAYOUT) ..."
d2 --theme "$THEME" --layout "$LAYOUT" "$D2_FILE" "$OUTPUT"

echo ""
echo "Rendered diagram: $OUTPUT"
