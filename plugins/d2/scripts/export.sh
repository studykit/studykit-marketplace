#!/bin/bash
# Export a D2 file to various formats
# Usage: bash export.sh <path-to-d2-file> [format] [theme-id] [layout-engine]
#
# Formats: svg (default), png, pdf, pptx
# theme-id: 3 (default, Flagship Terrastruct). Run `d2 themes` for full list.
# layout-engine: dagre (default), elk
# Prerequisites: brew install d2

set -e

D2_FILE="${1:?Usage: export.sh <path-to-d2-file> [svg|png|pdf|pptx] [theme-id] [layout-engine]}"
FORMAT="${2:-svg}"
THEME="${3:-3}"
LAYOUT="${4:-}"

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

LAYOUT_FLAG=""
if [ -n "$LAYOUT" ]; then
    LAYOUT_FLAG="--layout $LAYOUT"
fi

case "$FORMAT" in
    svg|png|pdf|pptx)
        OUTPUT="$D2_DIR/${D2_NAME}.${FORMAT}"
        echo "Exporting $D2_FILE to $FORMAT (theme: $THEME, layout: ${LAYOUT:-dagre}) ..."
        d2 --theme "$THEME" $LAYOUT_FLAG "$D2_FILE" "$OUTPUT"
        echo "Exported: $OUTPUT"
        ;;
    *)
        echo "Unknown format: $FORMAT (supported: svg, png, pdf, pptx)"
        exit 1
        ;;
esac
