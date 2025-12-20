# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pypdf",
# ]
# ///

"""Extract and print bookmark information from a PDF file."""

import sys
from pypdf import PdfReader


def get_bookmarks(pdf_path: str) -> list[dict]:
    """Extract bookmark (table of contents) information from a PDF.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        List of bookmark info dicts (level, title, page)
    """
    reader = PdfReader(pdf_path)
    bookmarks = []

    def extract_bookmarks(outline, level=1):
        for item in outline:
            if isinstance(item, list):
                extract_bookmarks(item, level + 1)
            else:
                page_num = reader.get_destination_page_number(item) + 1
                bookmarks.append({
                    "level": level,
                    "title": item.title,
                    "page": page_num,
                })

    if reader.outline:
        extract_bookmarks(reader.outline)

    return bookmarks


def print_bookmarks(bookmarks: list[dict]) -> None:
    """Print bookmark information in a hierarchical structure."""
    for bm in bookmarks:
        indent = "  " * (bm["level"] - 1)
        print(f"{indent}{bm['title']} (p.{bm['page']})")


def main():
    if len(sys.argv) < 2:
        print("Usage: uv run get_bookmarks.py <pdf_file>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    bookmarks = get_bookmarks(pdf_path)

    if not bookmarks:
        print("No bookmarks found.")
        return

    print(f"Found {len(bookmarks)} bookmarks.\n")
    print_bookmarks(bookmarks)


if __name__ == "__main__":
    main()
