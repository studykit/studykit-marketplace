---
name: epub-extract
disable-model-invocation: true
description: This skill should be used when the user asks to "extract EPUB to markdown", "convert EPUB to md", "extract chapters from EPUB", "EPUB 마크다운 변환", "EPUB 챕터 추출", or wants to convert an EPUB file into chapter-by-chapter markdown files while preserving the book's logical reading order.
---

# EPUB to Markdown Extraction

Extract chapter-by-chapter markdown files from EPUB files using metadata-based extraction. This approach parses the EPUB's `content.opf` to maintain the book's logical reading order (spine) rather than relying on filename sorting.

## Output Structure

```
output_dir/
├── metadata.json              # Chapter mapping information
├── images/                    # Extracted images (original folder name preserved)
│   ├── image1.jpg
│   └── image2.png
├── 008_CH1-WHY_CALCULUS.md               # Chapter abbreviated (CH1, CH2, ...)
├── 009_CH2-THE_DERIVATIVE.md
└── ...
```

**Filename format**: `{sequence}_CH{number}-{chapter_title}.md`
- Chapter numbers are abbreviated (e.g., "CHAPTER EIGHTEEN" → "CH18", "CHAPTER TWENTY-ONE" → "CH21")
- Titles are truncated to 50 characters for filesystem compatibility
- Image folder name is preserved from the EPUB (e.g., `images/`, `Images/`, `img/`)

Each markdown file includes YAML frontmatter:
```yaml
---
title: Chapter Title
sequence: 1
source: OEBPS/Text/chapter01.xhtml
---
```

## Workflow

### Step 1: Extract EPUB to Markdown

Run the extraction script:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/epub-extract/scripts/extract_epub.py "<input.epub>" -o "<output_dir>"
```

Options:
- `-o, --output` - Output directory (default: `<epub_name>/`)
- `--no-images` - Skip image extraction
- `--no-frontmatter` - Skip YAML frontmatter in markdown files

### Step 2: Verify Extraction Results

After extraction:

1. Check `metadata.json` for chapter mapping
2. Verify chapter count matches expected TOC
3. Spot-check a few markdown files for content quality
4. Verify images are properly linked (folder name preserved from EPUB)

### Step 3: Rename Generic Filenames

Some files may have generic names without chapter info (e.g., `001_untitled.md`, `002_section1.md`). For these files:

1. Open the markdown file and check the content for chapter information
2. Look for chapter headings, titles, or context clues within the text
3. Rename the file to match the `{sequence}_CH{number}-{title}.md` format
4. Update the YAML frontmatter title if needed

Example:
- `005_split_000.md` contains "Introduction" → rename to `005_Introduction.md`
- `012_part2.md` contains "Chapter 7: Advanced Topics" → rename to `012_CH7-Advanced_Topics.md`

### Step 4: Post-Processing (Optional)

Common post-processing tasks:

- **Merge chapters**: Combine related chapters if needed
- **Fix formatting**: Adjust headers, lists, or code blocks
- **Update links**: Modify internal links between chapters
- **Add metadata**: Enhance YAML frontmatter with additional fields

## Technical Details

### EPUB Structure

EPUB files contain:
- `mimetype` - File format identifier
- `META-INF/container.xml` - Points to content.opf location
- `content.opf` - Manifest (file list) and Spine (reading order)
- `OEBPS/Text/` - XHTML chapter files
- `OEBPS/Images/` - Image resources

### Spine-Based Ordering

The script uses `content.opf`'s spine element to determine chapter order:
```xml
<spine>
  <itemref idref="chapter01"/>
  <itemref idref="chapter02"/>
</spine>
```

This ensures correct reading order regardless of filename patterns.

### HTML to Markdown Conversion

Uses `markdownify` library for HTML to markdown conversion:
- Preserves heading hierarchy (h1-h6)
- Converts lists, tables, and code blocks
- Handles inline formatting (bold, italic, links)
- Image paths remain unchanged (original folder structure preserved)

## Dependencies

### Required Python Packages

The script uses inline dependencies with `uv`:
- `lxml` - XML/HTML parsing
- `markdownify` - HTML to markdown conversion

### uv (Python Package Manager)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with Homebrew
brew install uv
```

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Missing chapters | Non-standard EPUB structure | Check container.xml and content.opf paths |
| Broken images | Different image folder location | Verify image paths in XHTML files |
| Wrong chapter order | Non-standard spine | Manually check content.opf spine element |
| Encoding errors | Non-UTF8 content | Script handles most encodings automatically |

### Manual Inspection

To manually inspect EPUB structure:

```bash
# Unzip EPUB (it's a ZIP file)
unzip -l "<input.epub>"

# Extract and examine content.opf
unzip -p "<input.epub>" "OEBPS/content.opf" | head -100
```
