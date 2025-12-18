---
name: chm
description: Extract and read CHM (Compiled HTML Help) files with 7zz.
---

# CHM File Reading Skill

## Prerequisites

```bash
# macOS
brew install sevenzip

# Ubuntu/Debian
sudo apt install 7zip

# Fedora/RHEL
sudo dnf install p7zip
```

## Workflow

**IMPORTANT**:
- Before extracting, check if `<filename>/` folder already exists. Skip extraction if it exists.
- Before converting, check if the `.md` file already exists. Skip conversion if it exists.
- Preserve original HTML filename and only change the extension to `.md`.

### 1. Extract CHM file

```bash
cd "/path/to/chm/directory"
7zz x -y -o"<filename>" "<filename>.chm"
```

Example:
```
/docs/API Reference.chm -> /docs/API Reference/
```

### 2. Convert HTML to Markdown

```bash
# Create .md in the same location as the original HTML
uvx --from 'markitdown[all]' markitdown "/path/to/<filename>/topic.html" -o "/path/to/<filename>/topic.md"
```

### 3. Search Markdown files

```bash
grep -ri "search term" "/path/to/<filename>/"
```

## Directory Structure

```
/path/to/
├── User Manual.chm               # Original CHM file (may contain spaces)
└── User Manual/                  # Extracted CHM contents (same name as CHM)
    ├── *.html                    # Original HTML files
    ├── *.md                      # Converted Markdown files (same location)
    └── *.hhc                     # Table of contents
```

## Error Handling

- If CHM file not found: Ask user to verify the file path
- If no search results: Suggest alternative search terms
- If 7zz not installed: Guide user through installation (`brew install sevenzip`)
