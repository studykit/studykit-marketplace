---
name: chm
disable-model-invocation: true
description: This skill handles CHM (Compiled HTML Help) files, the Windows help file format with .chm extension. Use for extracting CHM contents, converting CHM to Markdown, reading compiled help documentation, parsing .hhc table of contents files, searching within help files, or working with Microsoft HTML Help. Applies when users say "extract CHM", "convert CHM to markdown", "read help file", "open .chm", "parse CHM documentation", "search CHM content", or reference Windows help documentation.
---

# CHM File Extraction and Conversion

Extract CHM contents and convert them to searchable Markdown format.

## Key Files After Extraction

- `*.hhc` (HTML Help Contents): Table of contents file defining hierarchical navigation structure
- `*.html`, `*.htm`: HTML document files containing the actual content


## Directory Structure After Convert HTML to Markdown

```
APIGuide.chm                 # Original CHM file
APIGuide/                    # Extracted directory
├── APIGuide.hhc             # Table of contents source
├── TOC.md                   # Generated table of contents
├── TODO.md                  # Completed task list
└── HTML/
    ├── A.htm
    ├── A.md    # Converted Markdown
    ├── BD.htm
    ├── BD.md      # Converted Markdown
    └── ...
```


## Workflow Decision Tree

### Analyze TOC Structure

Only available when CHM file has been extracted. For extraction, see "Step 1: Extract CHM File" section below.

1. Check if `TOC.md` exists in the extracted directory
2. If exists, use `TOC.md` directly
3. If not, analyze `*.hhc` file with `scripts/show_hhc.py` (see [references/hhc-format.md](references/hhc-format.md))

### Content Searching

**Note**: Content searching is only available when Markdown files exist. If no Markdown files are present, use the "Convert HTML to Markdown" section first.

Use grep or Claude's Grep tool to search across all converted Markdown files:

```bash
grep -r "search term" "<converted-folder>/" --include="*.md"
```


### Convert HTML to Markdown

#### Prerequisites Check

- If `<filename>/TOC.md` exists, the workflow is complete. Skip all steps.
- If `<filename>/` directory exists, skip extraction step.
- If `TODO.md` exists, skip TODO generation step.

#### Step 1: Extract CHM File

```bash
extract_chmLib "<filename>.chm" "<filename>/"
```

**Common Errors**:
- `extract_chmLib: command not found` - Install chmlib (see Dependencies section)
- `Cannot open file` - Check file path and permissions

#### Step 2: Generate TODO List

```bash
python3 scripts/show_hhc.py --has-link --todo "<path/to/file.hhc>" -o "<path/to>/TODO.md"
```

Output example:

```markdown
# HTML to Markdown conversion task list

- [ ] HTML/UserManualIndex_UM.htm -> HTML/UserManualIndex_UM.md
- [ ] HTML/AddInAutomation.htm -> HTML/AddInAutomation.md
```

#### Step 3: Convert HTML Files to Markdown

Convert each HTML file from the TODO list using `uvx markitdown`:

```bash
uvx markitdown "<path/to/file.htm>" -o "<path/to/file.md>"
```

Update the TODO list after each conversion by marking items as complete `[x]`.

**IMPORTANT**: Skip files that already exist as Markdown.

#### Step 4: Create Table of Contents

After completing all tasks in TODO.md, generate the final TOC:

```bash
python3 scripts/show_hhc.py "<path/to/file.hhc>" -o "<path/to>/TOC.md"
```

## Dependencies

### macOS

```bash
brew install chmlib
```

### Linux (Debian/Ubuntu)

```bash
sudo apt-get install libchm-bin
```

### Linux (Fedora/RHEL)

```bash
sudo dnf install chmlib
```

## References

- [references/hhc-format.md](references/hhc-format.md) - `show_hhc.py` script options and usage
