# Additional Analysis Workflows

> **Note:** All examples below use shorthand `... html-tree.ts`. The full command is:
> `deno run --allow-read ${CLAUDE_PLUGIN_ROOT}/skills/html-tree/scripts/html-tree.ts <html-file> [options]`

## Selector Debugging

Use when a CSS selector is not matching expected elements.

1. Start from a broader selector that does match
2. Progressively narrow with child selectors
3. Use `--full` to see all attributes, not just id/class/data-*
4. Check for dynamic class names or attributes that vary across pages
5. Use `--highlight-path` to trace from root to the target element

**Example:**
```bash
# Broad selector that works
... html-tree.ts page.html --selector "div" --max-depth 2

# Narrow down step by step
... html-tree.ts page.html --selector "div.content" --full
... html-tree.ts page.html --selector "div.content > article" --full --highlight-path
```

## Cross-Page Validation

Use when verifying selectors work across different page variants.

1. Collect multiple HTML samples of the same site/type
2. Run the same selector against each sample
3. Compare match counts and paths
4. Identify stable vs. variable structural patterns
5. Choose selectors based on the most stable elements

**Example:**
```bash
for f in data/*.html; do
  echo "=== $f ==="
  ... html-tree.ts "$f" --selector "article" 2>/dev/null | head -5
done
```

## Content Selector Discovery

Use when building a scraper/converter and need to find the right selectors.

1. Start with broad semantic selectors: `article`, `main`, `section`
2. If no match, try common class patterns: `.content`, `.story`, `.post`, `.entry`
3. Use `--show-parents 3` to understand context around matches
4. Use `--match-index` to examine individual matches when multiple found
5. Use `--show-text` to verify the matched elements contain expected content

**Example:**
```bash
# Try semantic elements first
... html-tree.ts page.html --selector "article, main, section" --show-text --max-depth 2

# Then class-based patterns
... html-tree.ts page.html --selector ".content, .story, .post" --show-text --max-depth 2

# Examine a match in detail
... html-tree.ts page.html --selector ".story" --show-parents 3 --match-index 1
```
