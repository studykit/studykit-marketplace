#!/usr/bin/env python3
# /// script
# dependencies = ["pypdf"]
# ///
"""
Extract specific page ranges from a PDF file.

Usage:
    uv run split_by_page.py input.pdf output.pdf 1-10
    uv run split_by_page.py input.pdf output.pdf 1,3,5-10,15
"""

import argparse
import sys
from pathlib import Path

from pypdf import PdfReader, PdfWriter


def parse_page_range(page_range: str, max_pages: int) -> list[int]:
    """
    Parse page range string and return list of page numbers.

    Examples:
        "1-10" -> [0, 1, 2, ..., 9]
        "1,3,5" -> [0, 2, 4]
        "1-5,10,15-20" -> [0, 1, 2, 3, 4, 9, 14, 15, 16, 17, 18, 19]

    Note: Input is 1-indexed, output is 0-indexed (for pypdf).
    """
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


def extract_pages(input_path: str, output_path: str, page_range: str) -> None:
    """Extract specified page range and create a new PDF."""
    reader = PdfReader(input_path)
    max_pages = len(reader.pages)

    print(f"Input file: {input_path}")
    print(f"Total pages: {max_pages}")

    pages = parse_page_range(page_range, max_pages)
    print(f"Pages to extract: {[p + 1 for p in pages]}")

    writer = PdfWriter()
    for page_num in pages:
        writer.add_page(reader.pages[page_num])

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    with open(output, "wb") as f:
        writer.write(f)

    print(f"Output file: {output_path}")
    print(f"Extracted pages: {len(pages)}")


def main():
    parser = argparse.ArgumentParser(
        description="Extract specific page ranges from a PDF file.",
        epilog="Example: %(prog)s input.pdf output.pdf 1-10,15,20-25"
    )
    parser.add_argument("input", help="Input PDF file path")
    parser.add_argument("output", help="Output PDF file path")
    parser.add_argument(
        "pages",
        help="Page range to extract (e.g., 1-10, 1,3,5, 1-5,10,15-20)"
    )

    args = parser.parse_args()

    if not Path(args.input).exists():
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    try:
        extract_pages(args.input, args.output, args.pages)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: Failed to process PDF: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
