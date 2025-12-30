# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pytesseract",
#     "pdf2image",
#     "Pillow",
# ]
# ///
"""Extract text from scanned PDFs using OCR (pytesseract + pdf2image)."""

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


def get_pdf_page_count(pdf_path: str) -> int:
    """Get total number of pages in PDF."""
    from pdf2image import pdfinfo_from_path

    info = pdfinfo_from_path(pdf_path)
    return info["Pages"]


def ocr_pdf(
    pdf_path: str,
    pages: str | None = None,
    lang: str = "eng",
    dpi: int = 300,
) -> str:
    """Extract text from PDF using OCR."""
    import pytesseract
    from pdf2image import convert_from_path

    total_pages = get_pdf_page_count(pdf_path)

    if pages:
        page_nums = parse_page_range(pages, total_pages)
    else:
        page_nums = list(range(1, total_pages + 1))

    texts = []

    for page_num in page_nums:
        # Convert specific page to image
        images = convert_from_path(
            pdf_path,
            dpi=dpi,
            first_page=page_num,
            last_page=page_num,
        )

        if images:
            image = images[0]
            text = pytesseract.image_to_string(image, lang=lang)
            if text.strip():
                texts.append(f"--- Page {page_num} ---\n{text.strip()}")

    return "\n\n".join(texts)


def main():
    parser = argparse.ArgumentParser(
        description="Extract text from scanned PDFs using OCR"
    )
    parser.add_argument("pdf_file", help="Path to PDF file")
    parser.add_argument(
        "--pages",
        help="Page range (e.g., '1-10', '5', '1,3,5-7')",
    )
    parser.add_argument(
        "--lang",
        default="eng",
        help="Tesseract language code (default: eng). Use + for multiple (e.g., eng+kor)",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="Resolution for OCR (default: 300)",
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
        text = ocr_pdf(args.pdf_file, args.pages, args.lang, args.dpi)

        if not text:
            print("No text extracted. The PDF may be empty or OCR failed.")
            return

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
