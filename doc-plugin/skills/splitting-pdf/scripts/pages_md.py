#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pymupdf", "markitdown[pdf]"]
# ///
"""
Convert specific PDF pages to markdown for TOC analysis.

Usage:
    uv run pages_md.py input.pdf              # Convert all pages
    uv run pages_md.py input.pdf 1-10         # Convert pages 1-10
    uv run pages_md.py input.pdf 1-10 -o out.md  # Save to file
"""

import argparse
import sys
import tempfile
from pathlib import Path

import fitz  # pymupdf
from markitdown import MarkItDown


def parse_page_range(page_range: str, max_pages: int) -> list[int]:
    """Parse page range string and return list of 0-indexed page numbers."""
    pages = set()

    for part in page_range.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-", 1)
            start = int(start.strip())
            end = int(end.strip())

            if start < 1 or end > max_pages:
                raise ValueError(f"Page range out of bounds: {start}-{end} (total pages: {max_pages})")
            if start > end:
                raise ValueError(f"Start page greater than end page: {start}-{end}")

            pages.update(range(start - 1, end))
        else:
            page = int(part)
            if page < 1 or page > max_pages:
                raise ValueError(f"Page number out of bounds: {page} (total pages: {max_pages})")
            pages.add(page - 1)

    return sorted(pages)


def extract_pages_to_temp(input_path: str, pages: list[int]) -> str:
    """Extract specified pages to a temporary PDF file using pymupdf."""
    doc = fitz.open(input_path)
    new_doc = fitz.open()

    for page_num in pages:
        new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

    temp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    new_doc.save(temp_file.name)
    new_doc.close()
    doc.close()

    return temp_file.name


def convert_to_markdown(pdf_path: str) -> str:
    """Convert PDF to markdown using markitdown."""
    md = MarkItDown()
    result = md.convert(pdf_path)
    return result.text_content


def main():
    parser = argparse.ArgumentParser(
        description="Convert specific PDF pages to markdown for TOC analysis.",
        epilog="Example: %(prog)s input.pdf 1-20 -o toc.md"
    )
    parser.add_argument("input", help="Input PDF file path")
    parser.add_argument(
        "pages",
        nargs="?",
        help="Page range to convert (e.g., 1-10). If omitted, converts all pages."
    )
    parser.add_argument(
        "-o", "--output",
        help="Output markdown file path. If omitted, prints to stdout."
    )

    args = parser.parse_args()

    if not Path(args.input).exists():
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    try:
        doc = fitz.open(args.input)
        max_pages = len(doc)
        doc.close()
        print(f"Total pages: {max_pages}", file=sys.stderr)

        if args.pages:
            pages = parse_page_range(args.pages, max_pages)
            print(f"Converting pages: {[p + 1 for p in pages]}", file=sys.stderr)
            temp_pdf = extract_pages_to_temp(args.input, pages)
            markdown = convert_to_markdown(temp_pdf)
            Path(temp_pdf).unlink()  # Clean up temp file
        else:
            print("Converting all pages...", file=sys.stderr)
            markdown = convert_to_markdown(args.input)

        if args.output:
            Path(args.output).write_text(markdown, encoding="utf-8")
            print(f"Saved to: {args.output}", file=sys.stderr)
        else:
            print(markdown)

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: Failed to process PDF: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
