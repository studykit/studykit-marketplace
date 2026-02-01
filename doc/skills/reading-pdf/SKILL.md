---
name: reading-pdf
disable-model-invocation: true
description: This skill should be used when users want to extract text or tables from PDF files, read PDF content, parse PDF documents, or work with scanned PDFs using OCR. Common triggers include "extract text from PDF", "read this PDF", "get tables from PDF", "parse PDF content", "OCR this scanned PDF", and "convert PDF to text".
---

# Reading PDF

Extract text and tables from PDF files using pdfplumber (primary) or OCR for scanned documents.

## Library Selection

| Use Case | Library | Script |
|----------|---------|--------|
| General text extraction | pdfplumber | `scripts/extract_text.py` |
| Table extraction | pdfplumber | `scripts/extract_tables.py` |
| Scanned PDF (OCR) | pytesseract + pdf2image | `scripts/ocr_pdf.py` |

## Prerequisites

### uv (Python package manager)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with Homebrew
brew install uv
```

### For OCR (scanned PDFs only)

```bash
# macOS
brew install tesseract poppler

# Ubuntu/Debian
sudo apt-get install tesseract-ocr poppler-utils
```

## Text Extraction

Extract text from PDF pages using pdfplumber.

### Extract All Text

```bash
uv run scripts/extract_text.py "<input.pdf>"
```

Output: Plain text content from all pages.

### Extract Specific Pages

```bash
# Single page
uv run scripts/extract_text.py "<input.pdf>" --pages 5

# Page range
uv run scripts/extract_text.py "<input.pdf>" --pages 1-10

# Multiple ranges
uv run scripts/extract_text.py "<input.pdf>" --pages 1-5,10,15-20
```

### Save to File

```bash
uv run scripts/extract_text.py "<input.pdf>" -o output.txt
```

## Table Extraction

Extract tables from PDF and output as CSV or markdown.

### Extract All Tables

```bash
uv run scripts/extract_tables.py "<input.pdf>"
```

Output: All tables found, formatted as markdown.

### Extract from Specific Pages

```bash
uv run scripts/extract_tables.py "<input.pdf>" --pages 5-10
```

### Output Formats

```bash
# Markdown (default)
uv run scripts/extract_tables.py "<input.pdf>" --format markdown

# CSV (separate files per table)
uv run scripts/extract_tables.py "<input.pdf>" --format csv -o tables/
```

### Table Settings

For better table detection:

```bash
# Adjust table detection sensitivity
uv run scripts/extract_tables.py "<input.pdf>" --settings explicit

# Settings options:
#   default  - Standard detection (works for most PDFs)
#   explicit - Only detect tables with visible borders
#   stream   - Text-based detection for borderless tables
```

## OCR for Scanned PDFs

Extract text from scanned PDFs or image-based PDFs using OCR.

### Basic OCR

```bash
uv run scripts/ocr_pdf.py "<scanned.pdf>"
```

### OCR Specific Pages

```bash
uv run scripts/ocr_pdf.py "<scanned.pdf>" --pages 1-5
```

### Language Support

```bash
# English (default)
uv run scripts/ocr_pdf.py "<scanned.pdf>" --lang eng

# Korean
uv run scripts/ocr_pdf.py "<scanned.pdf>" --lang kor

# Multiple languages
uv run scripts/ocr_pdf.py "<scanned.pdf>" --lang eng+kor
```

### Save OCR Output

```bash
uv run scripts/ocr_pdf.py "<scanned.pdf>" -o output.txt
```

## Detecting PDF Type

To determine if a PDF is text-based or scanned:

```bash
uv run scripts/extract_text.py "<input.pdf>" --pages 1
```

- If output contains readable text → Use `extract_text.py` or `extract_tables.py`
- If output is empty or garbled → Use `ocr_pdf.py`

## Workflow Examples

### Extract Report Content

```bash
# 1. Check if text-based or scanned
uv run scripts/extract_text.py "report.pdf" --pages 1

# 2a. If text-based, extract all text
uv run scripts/extract_text.py "report.pdf" -o report.txt

# 2b. If scanned, use OCR
uv run scripts/ocr_pdf.py "report.pdf" -o report.txt
```

### Extract Financial Tables

```bash
# Extract tables from specific pages
uv run scripts/extract_tables.py "financials.pdf" --pages 10-20 --format csv -o tables/

# List extracted tables
ls tables/
```

### Process Multi-Language Document

```bash
# OCR with multiple language support
uv run scripts/ocr_pdf.py "multilingual.pdf" --lang eng+kor+jpn -o output.txt
```

## Script Reference

### extract_text.py

```
Usage: uv run scripts/extract_text.py <pdf_file> [options]

Options:
  --pages RANGE    Page range (e.g., "1-10", "5", "1,3,5-7")
  -o, --output     Output file path (default: stdout)
```

### extract_tables.py

```
Usage: uv run scripts/extract_tables.py <pdf_file> [options]

Options:
  --pages RANGE    Page range (e.g., "1-10", "5", "1,3,5-7")
  --format FORMAT  Output format: markdown, csv (default: markdown)
  --settings MODE  Table detection: default, explicit, stream
  -o, --output     Output path (file for md, directory for csv)
```

### ocr_pdf.py

```
Usage: uv run scripts/ocr_pdf.py <pdf_file> [options]

Options:
  --pages RANGE    Page range (e.g., "1-10", "5", "1,3,5-7")
  --lang LANG      Tesseract language code (default: eng)
  --dpi DPI        Resolution for OCR (default: 300)
  -o, --output     Output file path (default: stdout)
```

## Dependencies

All scripts use inline dependencies via `uv run`. No manual installation required.

- **pdfplumber**: Text and table extraction
- **pytesseract**: OCR interface
- **pdf2image**: PDF to image conversion for OCR
- **Pillow**: Image processing
