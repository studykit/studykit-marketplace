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
- Before extracting, check if `.extracted/<filename>/` already exists. Skip extraction if it exists.
- Before converting, check if the `.md` file already exists. Skip conversion if it exists.
- Preserve original HTML filename and only change the extension to `.md`.

### 1. Extract CHM file

```bash
cd "/path/to/chm/directory"
7zz x -y -o".extracted/<filename>" "<filename>.chm"
```

Example:
```
/docs/API Reference.chm -> /docs/.extracted/API Reference/
```

### 2. Convert HTML to Markdown

Output directory: `.extracted/<filename>/.converted/`

```bash
mkdir -p "/path/to/.extracted/<filename>/.converted"
uvx --from 'markitdown[all]' markitdown "/path/to/.extracted/<filename>/topic.html" > "/path/to/.extracted/<filename>/.converted/topic.md"
```

### 3. Search Markdown files

```bash
grep -ri "search term" "/path/to/.extracted/<filename>/.converted/"
```

## Directory Structure

```
/path/to/
├── User Manual.chm               # Original CHM file (may contain spaces)
└── .extracted/
    └── User Manual/              # Extracted CHM contents
        ├── *.html                # Original HTML files
        ├── *.hhc                 # Table of contents
        └── .converted/                   # Converted Markdown files
            └── *.md              # Markdown versions (same structure)
```

## Error Handling

- If CHM file not found: Ask user to verify the file path
- If no search results: Suggest alternative search terms
- If 7zz not installed: Guide user through installation (`brew install sevenzip`)
