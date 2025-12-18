---
name: markitdown
description: Convert documents (PDF, PPTX, DOCX, XLSX, XLS, HTML, images, audio) to Markdown using `uvx markitdown`.
---

# MarkItDown Skill

Convert various document formats to Markdown for easy reading and analysis using `uvx markitdown`.

## Prerequisites

### uv (Python package manager)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with Homebrew
brew install uv
```

## Supported Formats

| Format | Extensions | Description |
|--------|------------|-------------|
| PDF | `.pdf` | PDF documents |
| PowerPoint | `.pptx` | Microsoft PowerPoint presentations |
| Word | `.docx` | Microsoft Word documents |
| Excel | `.xlsx`, `.xls` | Microsoft Excel spreadsheets |
| HTML | `.html`, `.htm` | HTML web pages |
| Images | `.jpg`, `.jpeg`, `.png` | Image files (with EXIF data) |
| Audio | `.mp3`, `.wav` | Audio files (with metadata) |

## Usage

**IMPORTANT**:
- Before converting, always check if the converted file already exists in `.converted/`. Skip conversion if it exists.
- Preserve the original filename and only change the extension to `.md`.

```bash
# Always create .converted/ directory first
mkdir -p ".converted/"

# Convert document: preserve original filename, change extension to .md
# Example: "Computer Networks, 5th Edition.pdf" -> ".converted/Computer Networks, 5th Edition.md"
uvx --from 'markitdown[all]' markitdown "/path/to/<original_filename>.pdf" -o ".converted/<original_filename>.md"

# Convert from URL (domain--path format)
uvx --from 'markitdown[all]' markitdown "https://example.com/docs/page.html" -o ".converted/example.com--docs--page.md"
```

## Examples

```bash
mkdir -p ".converted/"

# PDF (filename with spaces)
uvx --from 'markitdown[all]' markitdown "Computer Networks, 5th Edition.pdf" -o ".converted/Computer Networks, 5th Edition.md"

# PowerPoint
uvx --from 'markitdown[all]' markitdown "Q4 Sales Report.pptx" -o ".converted/Q4 Sales Report.md"

# Word
uvx --from 'markitdown[all]' markitdown "Project Proposal.docx" -o ".converted/Project Proposal.md"

# Excel
uvx --from 'markitdown[all]' markitdown "Budget 2024.xlsx" -o ".converted/Budget 2024.md"

# HTML
uvx --from 'markitdown[all]' markitdown "API Documentation.html" -o ".converted/API Documentation.md"

# URL
uvx --from 'markitdown[all]' markitdown "https://example.com/blog/article" -o ".converted/example.com--blog--article.md"
```

## Search Markdown Content

```bash
# Search for keyword in all markdown files
grep -r "keyword" ".converted/"

# Search with context (show surrounding lines)
grep -r -C 3 "keyword" ".converted/"

# Case-insensitive search
grep -ri "keyword" ".converted/"

# Search recursively in all subdirectories
grep -r --include="*.md" "keyword" ".converted/"
```

## Read Markdown Files

```bash
# Read entire file
cat ".converted/document.md"

# Read first 50 lines
head -n 50 ".converted/document.md"

# Read last 50 lines
tail -n 50 ".converted/document.md"

# Read specific line range (lines 100-150)
sed -n '100,150p' ".converted/document.md"

# List all converted markdown files
ls ".converted/"*.md
```
