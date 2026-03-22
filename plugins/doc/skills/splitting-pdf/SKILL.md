---
name: splitting-pdf
disable-model-invocation: true
description: This skill should be used when users want to split PDF files by bookmarks or page ranges. Common triggers include "split this PDF", "split /path/to/file.pdf by chapters", "extract pages from PDF", "break PDF into sections", "extract chapter from PDF", "split PDF by table of contents", and "get PDF bookmarks".
argument-hint: <path/to/file.pdf>
context: fork
allowed-tools: Bash(uv run *), Bash(mkdir *)
---

# PDF Split

Split `$ARGUMENTS` into separate files based on bookmarks or page ranges.

## Directory Structure After Split

```
/path/to/docs/
├── Computer Networks, 5th Edition.pdf    # Original PDF
└── Computer Networks, 5th Edition/       # Split output directory
    ├── 001_Cover_p1.pdf
    ├── 002_Preface_pi-vi.pdf                 # Roman numerals for front matter
    ├── 003_CONTENTS_pvii-xiv.pdf             # Roman numerals continue
    ├── 004_1_INTRODUCTION_p1-2.pdf           # Level 1 (Arabic numerals start)
    ├── 005_1.1_Uses_of_Computer_Networks_p2-11.pdf  # Level 2
    ├── 006_1.2_Network_Hardware_p11-40.pdf   # Level 2
    ├── 007_2_THE_PHYSICAL_LAYER_p41-42.pdf   # Level 1
    ├── 008_2.1_Guided_Transmission_p42-60.pdf  # Level 2
    └── ...
```

Filename format: `[number]_[title]_p[start]-[end].pdf`
- Title is sanitized and limited to 30 characters
- **Page numbers in filename = Book page numbers (exactly as printed)**

**Important**: Filename page numbers must match the book's original numbering system exactly:
- Roman numerals → Roman numerals: `002_Preface_pi-viii.pdf`
- Arabic numerals → Arabic numerals: `004_1_INTRODUCTION_p1-15.pdf`
- Chinese numerals → Chinese numerals: `003_序言_p一-五.pdf`

## Workflow

Scripts are located in this skill's directory. Set the base path first:

```bash
SCRIPT_DIR="$SKILL_DIR/scripts"
```

- `$SCRIPT_DIR/total_page.py` - Get total page count of a PDF
- `$SCRIPT_DIR/get_bookmarks.py` - Extract bookmark (TOC) info with PDF page numbers
- `$SCRIPT_DIR/pages_md.py` - Convert specific pages to markdown for TOC analysis
- `$SCRIPT_DIR/split_by_page.py` - Split by page ranges

### Pre-Check: Already Split?

**BEFORE starting any work**, verify if the PDF has already been split:

1. Check if output directory `<filename>/` exists
2. If exists, extract bookmarks or TOC from the original PDF
3. Compare with existing split files in the directory

If all chapters from bookmarks/TOC already have corresponding split PDF files → **Skip all steps. The workflow is already complete.**

### Step 1: Get Total Page Count

```bash
uv run "$SCRIPT_DIR/total_page.py" "$ARGUMENTS"
```

Output: `Total pages: 500`

### Step 2: Extract Bookmark Info

```bash
uv run "$SCRIPT_DIR/get_bookmarks.py" "$ARGUMENTS"
```

Output shows bookmark hierarchy with **PDF page numbers**:
```
Found 15 bookmarks.

Cover (p.1)
Title Page (p.2)
CONTENTS (p.3)
1 INTRODUCTION (p.15)
  1.1 Uses of Computer Networks (p.16)
  1.2 Network Hardware (p.25)
2 THE PHYSICAL LAYER (p.55)
...
```

### Step 3: Map PDF Pages to TOC Page Numbers

**CRITICAL**: This mapping step is essential. Do NOT skip or rush this step. Incorrect mapping will result in wrong page splits.

See `references/page-offset-mapping.md` for detailed mapping table format and offset calculation examples.

**Mapping Depth**: Up to 2 levels only
- Level 1: Main chapters (e.g., "1 INTRODUCTION")
- Level 2: Sub-sections (e.g., "1.1 Uses of Computer Networks")
- Skip deeper levels (e.g., "1.1.1", "1.2.3.4")

#### Case A: Bookmarks Exist

##### 3a-1. Use Bookmark Info to Find TOC Location

From Step 2 bookmark output, identify:
- Where "CONTENTS" or "TOC" bookmark is located (e.g., p.3)
- Where first chapter starts (e.g., "1 INTRODUCTION" at p.15)

##### 3a-2. Convert TOC Pages to Markdown for Verification

Convert the TOC pages (from bookmark info) to markdown:

```bash
# If CONTENTS is at p.3 and first chapter at p.15, convert p.3-14
uv run "$SCRIPT_DIR/pages_md.py" "$ARGUMENTS" 3-14 -o toc.md
```

##### 3a-3. Map Bookmark Pages to TOC Pages (Level 1 & 2)

Compare bookmark PDF pages with TOC page numbers in the markdown. Build a mapping table following the format in `references/page-offset-mapping.md`. Calculate offsets for front matter (Roman numerals) and main content (Arabic numerals) separately.

Verify a few chapters by converting their first page to markdown:
```bash
# Verify "1 INTRODUCTION" at PDF page 15 shows "page 1" in book
uv run "$SCRIPT_DIR/pages_md.py" "$ARGUMENTS" 15 | head -50

# Verify "CONTENTS" at PDF page 8 shows "page vii" in book
uv run "$SCRIPT_DIR/pages_md.py" "$ARGUMENTS" 8 | head -50
```

#### Case B: No Bookmarks

##### 3b-1. Convert Front Pages to Markdown

Convert the first ~30 pages to find the table of contents:

```bash
uv run "$SCRIPT_DIR/pages_md.py" "$ARGUMENTS" 1-30 -o front.md
```

##### 3b-2. Find TOC in Markdown (Level 1 & 2)

Search for table of contents in the markdown. Look for patterns like:
```
Chapter 1: Introduction .......... 1
  1.1 Overview ................... 2
  1.2 Background ................. 10
Chapter 2: Methods ............... 25
  2.1 Data Collection ............ 26
  2.2 Analysis ................... 35
Chapter 3: Results ............... 51
```

Note: These are TOC page numbers (what the book shows), not PDF page numbers.
Extract only Level 1 (chapters) and Level 2 (sub-sections).

##### 3b-3. Verify Chapter Start Pages

For each chapter in TOC, convert candidate PDF pages to markdown to find the actual PDF page:

```bash
# If TOC says "Chapter 1" starts at page 1, try PDF pages around 10-20
uv run "$SCRIPT_DIR/pages_md.py" "$ARGUMENTS" 10-20 | grep -i "chapter 1"

# For front matter, check early PDF pages for Roman numeral markers
uv run "$SCRIPT_DIR/pages_md.py" "$ARGUMENTS" 2-10 | head -100
```

Once found, calculate offset and verify:
```bash
# If "Chapter 1" (TOC p.1) is at PDF page 15, offset = +14
# Verify "Chapter 2" (TOC p.25) is at PDF page 39 (25+14)
uv run "$SCRIPT_DIR/pages_md.py" "$ARGUMENTS" 39 | head -50

# Verify "Preface" (TOC p.i) is at PDF page 2
uv run "$SCRIPT_DIR/pages_md.py" "$ARGUMENTS" 2 | head -50
```

Build a mapping table following the format in `references/page-offset-mapping.md`. Calculate offsets for front matter (Roman numerals) and main content (Arabic numerals) separately.

### Step 4: Split by Chapters

**Split Depth**: Up to 2 levels only
- Level 1: Main chapters (e.g., "1 INTRODUCTION", "2 THE PHYSICAL LAYER")
- Level 2: Sub-sections (e.g., "1.1 Uses of Computer Networks", "1.2 Network Hardware")
- Skip deeper levels (e.g., "1.1.1", "1.2.3.4")

Use `scripts/split_by_page.py` with:
- **Filename**: TOC page numbers (what the book shows)
- **Page argument**: PDF page numbers (actual pages in file)

```bash
# Create output directory
mkdir -p "<filename>/"

# Split each chapter (Level 1 and Level 2)
# Filename uses TOC pages (Roman or Arabic), argument uses PDF pages

# Front matter (Roman numerals in filename)
uv run "$SCRIPT_DIR/split_by_page.py" "$ARGUMENTS" "<filename>/001_Cover_p1.pdf" "1"
uv run "$SCRIPT_DIR/split_by_page.py" "$ARGUMENTS" "<filename>/002_Preface_pi-vi.pdf" "2-7"
uv run "$SCRIPT_DIR/split_by_page.py" "$ARGUMENTS" "<filename>/003_CONTENTS_pvii-xiv.pdf" "8-15"

# Main content (Arabic numerals in filename)
uv run "$SCRIPT_DIR/split_by_page.py" "$ARGUMENTS" "<filename>/004_1_INTRODUCTION_p1-2.pdf" "16-17"
uv run "$SCRIPT_DIR/split_by_page.py" "$ARGUMENTS" "<filename>/005_1.1_Uses_of_Computer_Networks_p2-11.pdf" "17-26"
uv run "$SCRIPT_DIR/split_by_page.py" "$ARGUMENTS" "<filename>/006_1.2_Network_Hardware_p11-40.pdf" "26-55"
uv run "$SCRIPT_DIR/split_by_page.py" "$ARGUMENTS" "<filename>/007_2_THE_PHYSICAL_LAYER_p41-42.pdf" "56-57"
```


### Step 5: Verify Split Results

**CRITICAL**: Always verify that split files have correct page boundaries. Follow the detailed checklist in `references/verification-checklist.md`.

### Page Range Formats

```bash
uv run "$SCRIPT_DIR/split_by_page.py" "$ARGUMENTS" "<output.pdf>" "<pages>"
```

- `1-10` - Range of pages
- `1,3,5` - Specific pages
- `1-5,10,15-20` - Mixed ranges and pages


## Result Reporting

As the final output of this task, print a structured summary containing the following items. This summary is how the main agent receives the results of this work.

- **Input file**: the original PDF absolute path
- **Output directory**: absolute path of the split output directory
- **File count**: number of split PDF files generated
- **File list**: list each generated filename on its own line with page range

Do not include additional commentary, follow-up questions, or next-step suggestions beyond this summary.

## Dependencies

### uv (Python package manager)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with Homebrew
brew install uv
```
