# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pdfplumber",
# ]
# ///
"""Extract text from PDF files using pdfplumber."""

import argparse
import sys
from pathlib import Path


def parse_page_range(page_spec: str, total_pages: int) -> list[int]:
    """Parse page specification like '1-5,10,15-20' into list of page numbers."""
    pages = []
    for part in page_spec.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-", 1)
            start = int(start) if start else 1
            end = int(end) if end else total_pages
            pages.extend(range(start, min(end + 1, total_pages + 1)))
        else:
            page = int(part)
            if 1 <= page <= total_pages:
                pages.append(page)
    return sorted(set(pages))


def extract_text(pdf_path: str, pages: str | None = None) -> str:
    """Extract text from PDF file."""
    import pdfplumber

    texts = []

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)

        if pages:
            page_nums = parse_page_range(pages, total_pages)
        else:
            page_nums = list(range(1, total_pages + 1))

        for page_num in page_nums:
            page = pdf.pages[page_num - 1]  # 0-indexed
            text = page.extract_text()
            if text:
                texts.append(f"--- Page {page_num} ---\n{text}")

    return "\n\n".join(texts)


def main():
    parser = argparse.ArgumentParser(
        description="Extract text from PDF files using pdfplumber"
    )
    parser.add_argument("pdf_file", help="Path to PDF file")
    parser.add_argument(
        "--pages",
        help="Page range (e.g., '1-10', '5', '1,3,5-7')",
    )
    parser.add_argument(
        "-o", "--output",
        help="Output file path (default: stdout)",
    )

    args = parser.parse_args()

    if not Path(args.pdf_file).exists():
        print(f"Error: File not found: {args.pdf_file}", file=sys.stderr)
        sys.exit(1)

    try:
        text = extract_text(args.pdf_file, args.pages)

        if args.output:
            Path(args.output).write_text(text, encoding="utf-8")
            print(f"Text saved to: {args.output}")
        else:
            print(text)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
