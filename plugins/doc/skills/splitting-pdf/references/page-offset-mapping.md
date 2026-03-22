# Page Offset Mapping

## Overview

Many books use two separate numbering systems:
- Front matter (preface, TOC, acknowledgments): Roman numerals (i, ii, iii, iv, v...)
- Main content: Arabic numerals (1, 2, 3...) starting fresh from page 1

This means the PDF may have: Cover (PDF p.1) → Preface p.i (PDF p.2) → ... → TOC p.vii (PDF p.8) → Chapter 1 p.1 (PDF p.15). Track both offsets separately if needed.

## Mapping Table Format

| Level | Section | TOC Page (in book) | PDF Page | Notes |
|-------|---------|-------------------|----------|-------|
| - | Cover | - | p.1 | Unnumbered |
| - | Preface | p.i | p.2 | Roman numerals start |
| - | CONTENTS | p.vii | p.8 | Roman numerals continue |
| 1 | 1 INTRODUCTION | p.1 | p.15 | Arabic numerals start (offset +14) |
| 2 | 1.1 Uses of Computer Networks | p.2 | p.16 | offset +14 |
| 2 | 1.2 Network Hardware | p.11 | p.25 | offset +14 |
| 1 | 2 THE PHYSICAL LAYER | p.41 | p.55 | offset +14 |
| 2 | 2.1 Guided Transmission | p.42 | p.56 | offset +14 |

## Two Offset Calculations (when Roman numerals exist)

- Front matter offset: `PDF page - Roman numeral value` (e.g., p.8 - vii(7) = +1)
- Main content offset: `PDF page - Arabic page` (e.g., p.15 - 1 = +14)

## Verification

Verify a few chapters by converting their first page to markdown:
```bash
# Verify "1 INTRODUCTION" at PDF page 15 shows "page 1" in book
uv run "$SCRIPT_DIR/pages_md.py" "$ARGUMENTS" 15 | head -50

# Verify "CONTENTS" at PDF page 8 shows "page vii" in book
uv run "$SCRIPT_DIR/pages_md.py" "$ARGUMENTS" 8 | head -50
```
