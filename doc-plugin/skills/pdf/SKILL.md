---
name: pdf-split
version: 1.0.0
description: This skill should be used when users want to split PDF files by bookmarks or page ranges, convert PDF pages to markdown, or search PDF content. Common triggers include "split this PDF", "extract pages from PDF", "break PDF into sections", "convert PDF to markdown", "search the PDF for", "find in PDF", "look for X in the PDF", "extract chapter from PDF", and "get PDF bookmarks".
---

# PDF Split

Split PDF files into separate files based on bookmarks or page ranges.

## Directory Structure After Split and Markdown Conversion

```
/path/to/docs/
├── Computer Networks, 5th Edition.pdf    # Original PDF
└── Computer Networks, 5th Edition/       # Split output directory
    ├── .CONVERTED                             # Indicates converting is done
    ├── .SPLITTED                             # Indicates splitting is done
    ├── 001_Cover_p1.pdf
    ├── 001_Cover_p1.md                       # Converted Markdown
    ├── 002_CONTENTS_p3-14.pdf
    ├── 002_CONTENTS_p3-14.md                 # Converted Markdown
    ├── 003_1_INTRODUCTION_p1-2.pdf           # Level 1
    ├── 003_1_INTRODUCTION_p1-2.md            # Converted Markdown
    ├── 004_1.1_Uses_of_Computer_Networks_p2-11.pdf  # Level 2
    ├── 004_1.1_Uses_of_Computer_Networks_p2-11.md   # Converted Markdown
    ├── 005_1.2_Network_Hardware_p11-40.pdf   # Level 2
    ├── 005_1.2_Network_Hardware_p11-40.md    # Converted Markdown
    ├── 006_2_THE_PHYSICAL_LAYER_p41-42.pdf   # Level 1
    ├── 006_2_THE_PHYSICAL_LAYER_p41-42.md    # Converted Markdown
    ├── 007_2.1_Guided_Transmission_p42-60.pdf  # Level 2
    ├── 007_2.1_Guided_Transmission_p42-60.md # Converted Markdown
    └── ...
```

Filename format: `[number]_[title]_p[start]-[end].pdf`
- Title is sanitized and limited to 30 characters
- **Page numbers in filename = TOC/book page numbers**
- **Page range in script argument = actual PDF page numbers**

## Workflow Decision

### Content Searching

**Note**: Content searching is only available when Markdown files exist. If no Markdown files are present, use the "Split PDF" or "Convert to Markdown" sections first.

Use grep or Claude's Grep tool to search across all converted Markdown files:

```bash
grep -r "search term" "<filename>/" --include="*.md"
```

### Convert to Markdown

**Note**: Conversion to Markdown is only available when PDF files are split. If no split PDF files are present, use the "Split PDF" section first.

Use the following command to convert each split PDF file to Markdown:

```bash
uv run scripts/page_md.py "<filename>/<splitted_file>.pdf" -o "<filename>/<splitted_file>.md"
```

After converting all split PDF files to Markdown, create a `.CONVERTED` file to mark the conversion as complete:

```bash
touch "<filename>/.CONVERTED"
```


### Split PDF

- `scripts/total_page.py` - Get total page count of a PDF
- `scripts/get_bookmarks.py` - Extract bookmark (TOC) info with PDF page numbers
- `scripts/pages_md.py` - Convert specific pages to markdown for TOC analysis
- `scripts/split_by_page.py` - Split by page ranges

**NOTE**: If `<filename>/.SPLITTED` file exists, the workflow is complete. Skip all steps.

#### Step 1: Get Total Page Count

```bash
uv run scripts/total_page.py "<input.pdf>"
```

Output: `Total pages: 500`

### Step 2: Extract Bookmark Info

```bash
uv run scripts/get_bookmarks.py "<input.pdf>"
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

### Step 3: Map PDF Pages ↔ TOC Page Numbers

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
uv run scripts/pages_md.py "<input.pdf>" 3-14 -o toc.md
```

##### 3a-3. Map Bookmark Pages to TOC Pages (Level 1 & 2)

Compare bookmark PDF pages with TOC page numbers in the markdown:

| Level | Chapter | TOC Page (in book) | Bookmark (PDF Page) | Offset |
|-------|---------|-------------------|---------------------|--------|
| 1 | 1 INTRODUCTION | p.1 | p.15 | +14 |
| 2 | 1.1 Uses of Computer Networks | p.2 | p.16 | +14 |
| 2 | 1.2 Network Hardware | p.11 | p.25 | +14 |
| 1 | 2 THE PHYSICAL LAYER | p.41 | p.55 | +14 |
| 2 | 2.1 Guided Transmission | p.42 | p.56 | +14 |

Calculate: `Offset = PDF page - TOC page`

Verify a few chapters by converting their first page to markdown:
```bash
# Verify "1 INTRODUCTION" at PDF page 15 shows "page 1" in book
uv run scripts/pages_md.py "<input.pdf>" 15 | head -50
```

#### Case B: No Bookmarks

##### 3b-1. Convert Front Pages to Markdown

Convert the first ~30 pages to find the table of contents:

```bash
uv run scripts/pages_md.py "<input.pdf>" 1-30 -o front.md
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
uv run scripts/pages_md.py "<input.pdf>" 10-20 | grep -i "chapter 1"
```

Once found, calculate offset and verify:
```bash
# If "Chapter 1" (TOC p.1) is at PDF page 15, offset = +14
# Verify "Chapter 2" (TOC p.25) is at PDF page 39 (25+14)
uv run scripts/pages_md.py "<input.pdf>" 39 | head -50
```

Build the mapping table (Level 1 & 2):

| Level | Chapter | TOC Page | PDF Page | Offset |
|-------|---------|----------|----------|--------|
| 1 | Chapter 1: Introduction | p.1 | p.15 | +14 |
| 2 | 1.1 Overview | p.2 | p.16 | +14 |
| 2 | 1.2 Background | p.10 | p.24 | +14 |
| 1 | Chapter 2: Methods | p.25 | p.39 | +14 |
| 2 | 2.1 Data Collection | p.26 | p.40 | +14 |
| 2 | 2.2 Analysis | p.35 | p.49 | +14 |
| 1 | Chapter 3: Results | p.51 | p.65 | +14 |

### Step 4: Split by Chapters

**IMPORTANT**: Before splitting, check if `<filename>/DONE` file already exists. Skip if it exists.

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
# Filename uses TOC pages, argument uses PDF pages
uv run scripts/split_by_page.py "doc.pdf" "<filename>/001_Cover_p1.pdf" "1"
uv run scripts/split_by_page.py "doc.pdf" "<filename>/002_CONTENTS_p3-14.pdf" "3-14"
uv run scripts/split_by_page.py "doc.pdf" "<filename>/003_1_INTRODUCTION_p1-2.pdf" "15-16"
uv run scripts/split_by_page.py "doc.pdf" "<filename>/004_1.1_Uses_of_Computer_Networks_p2-11.pdf" "16-25"
```

### Step 5: Mark as Done
Create a `.SPLITTED` file in the output directory to indicate splitting is complete:

```bash
touch "<filename>/.SPLITTED"
```


### Fallback: No Bookmarks or TOC

If neither bookmarks nor TOC exist, split into 20-page chunks:

```bash
# For a 100-page document
uv run scripts/split_by_page.py "doc.pdf" "<filename>/001_Part_1_p1-20.pdf" "1-20"
uv run scripts/split_by_page.py "doc.pdf" "<filename>/002_Part_2_p21-40.pdf" "21-40"
```

### Page Range Formats

```bash
uv run scripts/split_by_page.py "<input.pdf>" "<output.pdf>" "<pages>"
```

- `1-10` - Range of pages
- `1,3,5` - Specific pages
- `1-5,10,15-20` - Mixed ranges and pages


## Dependencies

### uv (Python package manager)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with Homebrew
brew install uv
```
