---
name: markitdown
disable-model-invocation: true
description: This skill should be used when users want to convert documents to Markdown using markitdown. Common triggers include "convert this PPTX to markdown", "convert DOCX to md", "turn this spreadsheet into markdown", "markitdown this file", "convert HTML page to markdown", "convert this URL to markdown", and "read this PowerPoint as markdown". Supported formats: PPTX, DOCX, XLSX, XLS, HTML, images (JPG/PNG), and audio (MP3/WAV).
argument-hint: <path/to/file-or-url>
context: fork
allowed-tools: Bash(uvx *)
---

# MarkItDown Skill

Convert `$ARGUMENTS` to Markdown for easy reading and analysis using `uvx markitdown`.

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

### Local File

```bash
# Convert local document: create .md in the same location as original
# Example: "/path/to/Q4 Sales Report.pptx" -> "/path/to/Q4 Sales Report.md"
uvx --from 'markitdown[all]' markitdown "$ARGUMENTS" -o "/path/to/<original_filename>.md"
```

### URL

```bash
# Convert from URL: save to webmd/ folder (domain--path format)
# Example: "https://example.com/docs/page.html" -> "webmd/example.com--docs--page.md"
mkdir -p "webmd/"
uvx --from 'markitdown[all]' markitdown "$ARGUMENTS" -o "webmd/<domain--path>.md"
```

## Result Reporting

As the final output of this task, print a structured summary containing the following items. This summary is how the main agent receives the results of this work.

- **Input**: the original file path or URL
- **Output file**: absolute path of the generated `.md` file
- **Format converted**: which document format was converted (e.g., PPTX, DOCX, HTML, URL)

Do not include additional commentary, follow-up questions, or next-step suggestions beyond this summary.
