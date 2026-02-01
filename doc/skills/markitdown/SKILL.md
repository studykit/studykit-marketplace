---
name: markitdown
disable-model-invocation: true
description: Convert documents (HTML, PPTX, DOCX, XLSX, XLS, images, audio) to Markdown using `uvx markitdown`.
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
| PowerPoint | `.pptx` | Microsoft PowerPoint presentations |
| Word | `.docx` | Microsoft Word documents |
| Excel | `.xlsx`, `.xls` | Microsoft Excel spreadsheets |
| HTML | `.html`, `.htm` | HTML web pages |
| Images | `.jpg`, `.jpeg`, `.png` | Image files (with EXIF data) |
| Audio | `.mp3`, `.wav` | Audio files (with metadata) |

## Usage

**IMPORTANT**:
- **Always use `--from 'markitdown[all]'` option.** Without this option, dependencies for images, audio, and other formats will not be installed, causing conversion to fail.
- Before converting, always check if the `.md` file already exists. Skip conversion if it exists.
- Preserve the original filename and only change the extension to `.md`.
- For local files: create `.md` in the same directory as the original file.
- For HTTP URLs: create `.md` in the `webmd/` folder.

```bash
# Convert local document: create .md in the same location as original
# Example: "/path/to/Q4 Sales Report.pptx" -> "/path/to/Q4 Sales Report.md"
uvx --from 'markitdown[all]' markitdown "/path/to/<original_filename>.pptx" -o "/path/to/<original_filename>.md"

# Convert from URL: save to webmd/ folder (domain--path format)
mkdir -p "webmd/"
uvx --from 'markitdown[all]' markitdown "https://example.com/docs/page.html" -o "webmd/example.com--docs--page.md"
```

## Examples

```bash
# PowerPoint
uvx --from 'markitdown[all]' markitdown "Q4 Sales Report.pptx" -o "Q4 Sales Report.md"

# Word
uvx --from 'markitdown[all]' markitdown "Project Proposal.docx" -o "Project Proposal.md"

# Excel
uvx --from 'markitdown[all]' markitdown "Budget 2024.xlsx" -o "Budget 2024.md"

# HTML
uvx --from 'markitdown[all]' markitdown "API Documentation.html" -o "API Documentation.md"

# URL - output to webmd/ folder
mkdir -p "webmd/"
uvx --from 'markitdown[all]' markitdown "https://example.com/blog/article" -o "webmd/example.com--blog--article.md"
```

## Search Markdown Content

```bash
# Search for keyword in markdown files (current directory)
grep "keyword" *.md

# Search for keyword in web-converted files
grep "keyword" webmd/*.md

# Search with context (show surrounding lines)
grep -C 3 "keyword" *.md

# Case-insensitive search
grep -i "keyword" *.md

# Search recursively in all subdirectories
grep -r --include="*.md" "keyword" .
```

## Read Markdown Files

```bash
# Read entire file
cat "document.md"

# Read first 50 lines
head -n 50 "document.md"

# Read last 50 lines
tail -n 50 "document.md"

# Read specific line range (lines 100-150)
sed -n '100,150p' "document.md"

# List converted markdown files from URLs
ls webmd/*.md
```
