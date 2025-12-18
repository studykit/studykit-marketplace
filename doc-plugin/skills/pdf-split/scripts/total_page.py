#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pypdf"]
# ///
"""PDF 파일의 전체 페이지 수를 계산하는 스크립트."""

import sys
from pathlib import Path

from pypdf import PdfReader


def get_total_pages(pdf_path: str) -> int:
    """PDF 파일의 전체 페이지 수를 반환합니다."""
    reader = PdfReader(pdf_path)
    return len(reader.pages)


def main():
    if len(sys.argv) < 2:
        print("Usage: uv run total_page.py <pdf_file>")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])
    if not pdf_path.exists():
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)

    total_pages = get_total_pages(str(pdf_path))
    print(f"Total pages: {total_pages}")


if __name__ == "__main__":
    main()
