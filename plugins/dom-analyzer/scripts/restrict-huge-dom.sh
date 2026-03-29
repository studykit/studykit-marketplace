#!/bin/bash
# Block Read tool on large, minified DOM-structured files (HTML, CSS, XML).
# Only rejects when file is >4KB AND has very few lines (<=2), indicating minified content.

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

[[ -z "$FILE_PATH" ]] && exit 0

# Check file extension for DOM-structured content
case "${FILE_PATH##*.}" in
  html|htm|xhtml|css|xml|xsl|xslt|svg|rss|atom) ;;
  *) exit 0 ;;
esac

# Check file exists, size > 4KB, and minified (<=2 lines)
if [ -f "$FILE_PATH" ]; then
  SIZE=$(stat -f%z "$FILE_PATH" 2>/dev/null || stat -c%s "$FILE_PATH" 2>/dev/null)
  LINES=$(wc -l < "$FILE_PATH" | tr -d ' ')
  if [ "${SIZE:-0}" -gt 4096 ] && [ "${LINES:-0}" -le 2 ]; then
    cat >&2 <<EOF
Blocked: ${FILE_PATH##*/} is ${SIZE} bytes in only ${LINES} line(s) — likely minified. Reading wastes context.

Instead, analyze the structure first:
  1. dom-analyzer plugin: use the html-analyzer agent or html-tree skill
     uv run \${CLAUDE_PLUGIN_ROOT}/skills/html-tree/scripts/html-tree.py "${FILE_PATH}" --max-depth 3
  2. Python with BeautifulSoup:
     from bs4 import BeautifulSoup; soup = BeautifulSoup(open("${FILE_PATH}"), "lxml"); print(soup.prettify()[:2000])
  3. Read a specific portion with offset/limit parameters
EOF
    exit 2
  fi
fi

exit 0
