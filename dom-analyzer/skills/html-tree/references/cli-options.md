# DOM Hierarchy Visualizer - CLI Options Reference

## Option Details

### --max-depth `<n>`

Limits how deep the tree traversal goes. Useful for getting a high-level overview of complex pages without overwhelming output.

**Example:**
```bash
npx ts-node html-tree.ts page.html --max-depth 3
```

**Output sample:**
```
DOM Hierarchy Visualization
──────────────────────────────────────────────────
<html>
  <head>
    <meta>
    <title>
    <link>
  <body>
    <header class="site-header">
      <nav class="main-nav">
    <main id="content">
      <article class="post">
    <footer class="site-footer">
```

### --selector `<css>`

Filters visualization to only elements matching the given CSS selector. Supports any valid CSS selector syntax.

**Simple tag selector:**
```bash
npx ts-node html-tree.ts page.html --selector "article"
```

**Class selector:**
```bash
npx ts-node html-tree.ts page.html --selector ".story-content"
```

**Complex selector:**
```bash
npx ts-node html-tree.ts page.html --selector "main > article.post"
```

**Output sample:**
```
DOM Hierarchy Visualization
──────────────────────────────────────────────────
Selector: "article"
Found: 2 matches

=== Match 1 of 2 ===
Path: html > body > main#content > article.post[2]
<article class="post">
  <h2 class="title">
  <div class="content">
    <p>
    <p>
  <footer class="meta">
```

### --show-parents `<n>`

Shows n levels of ancestor context above each matched node. Essential for understanding where a matched element sits in the page hierarchy.

**Example:**
```bash
npx ts-node html-tree.ts page.html --selector ".story-content" --show-parents 3
```

**Output sample:**
```
=== Match 1 of 1 ===
Path: html > body > main > div.container > article > div.story-content
<main> (parent context)
  <div class="container"> (parent context)
    <article> (parent context)
      <div class="story-content">
        <h1>
        <p>
        <p>
        <figure>
```

### --highlight-path

Marks the selected node path in the output. Use together with `--selector` and `--show-parents` for visual clarity.

### --match-index `<n>`

When a selector matches multiple elements, show only the nth match (1-based index). Useful for examining specific instances.

**Example:**
```bash
npx ts-node html-tree.ts page.html --selector "article" --match-index 2
```

Shows only the second article on the page.

### --show-text

Includes text node content in the visualization. By default, text nodes are hidden to keep output clean.

**Without --show-text:**
```
<h1 class="title">
```

**With --show-text:**
```
<h1 class="title"> [TEXT: Breaking News: Major Event Unfolds]
```

Text content is truncated to 50 characters for inline display, 100 characters for standalone text nodes.

### --no-attributes

Hides all element attributes, showing only tag names. Useful when focusing on document structure rather than specific element properties.

### --full

Shows all HTML attributes, not just the default set (id, class, data-*). Reveals href, src, style, role, aria-* and other attributes.

**Default (compact) mode:**
```
<a class="nav-link">
```

**Full mode:**
```
<a class="nav-link" href="/about" role="menuitem" aria-label="About us">
```

### --compact

Compact mode (default). Shows only id, class, and data-* attributes. Provides clean output focused on structural identification.

### --output `<file>`

Writes the visualization output to a file instead of console. Useful for saving analysis results.

**Example:**
```bash
npx ts-node html-tree.ts page.html --selector "article" --output article-structure.md
```

## Attribute Display Behavior

SVG and path elements always have their attributes suppressed regardless of display mode, as SVG attributes tend to be very long and not useful for structural analysis.

## Common Usage Patterns

### Initial exploration
```bash
npx ts-node html-tree.ts page.html --max-depth 4
```

### Finding article content
```bash
npx ts-node html-tree.ts page.html --selector "article, .article, .story, .post, main" --show-text
```

### Building stable selectors
```bash
npx ts-node html-tree.ts page.html --selector ".target" --show-parents 3 --highlight-path --full
```

### Comparing across pages
```bash
for f in data/*.html; do echo "=== $f ===" && npx ts-node html-tree.ts "$f" --selector "article" 2>/dev/null | head -5; done
```
