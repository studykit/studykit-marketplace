# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pdfplumber",
# ]
# ///
"""Extract tables from PDF files using pdfplumber."""

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


def get_table_settings(mode: str) -> dict:
    """Get pdfplumber table extraction settings."""
    if mode == "explicit":
        return {
            "vertical_strategy": "explicit",
            "horizontal_strategy": "explicit",
        }
    elif mode == "stream":
        return {
            "vertical_strategy": "text",
            "horizontal_strategy": "text",
        }
    else:  # default
        return {}


def table_to_markdown(table: list[list]) -> str:
    """Convert table to markdown format."""
    if not table or not table[0]:
        return ""

    # Clean cells
    rows = []
    for row in table:
        cleaned = [str(cell).replace("\n", " ").strip() if cell else "" for cell in row]
        rows.append(cleaned)

    # Calculate column widths
    num_cols = max(len(row) for row in rows)
    col_widths = [3] * num_cols
    for row in rows:
        for i, cell in enumerate(row):
            if i < num_cols:
                col_widths[i] = max(col_widths[i], len(cell))

    # Build markdown
    lines = []
    for i, row in enumerate(rows):
        # Pad row to have consistent columns
        while len(row) < num_cols:
            row.append("")
        cells = [cell.ljust(col_widths[j]) for j, cell in enumerate(row)]
        lines.append("| " + " | ".join(cells) + " |")

        # Add header separator after first row
        if i == 0:
            separator = ["-" * w for w in col_widths]
            lines.append("| " + " | ".join(separator) + " |")

    return "\n".join(lines)


def table_to_csv(table: list[list]) -> str:
    """Convert table to CSV format."""
    import csv
    import io

    output = io.StringIO()
    writer = csv.writer(output)

    for row in table:
        cleaned = [str(cell).replace("\n", " ").strip() if cell else "" for cell in row]
        writer.writerow(cleaned)

    return output.getvalue()


def extract_tables(
    pdf_path: str,
    pages: str | None = None,
    output_format: str = "markdown",
    settings_mode: str = "default",
) -> list[tuple[int, int, str]]:
    """Extract tables from PDF file.

    Returns list of (page_num, table_num, formatted_table) tuples.
    """
    import pdfplumber

    tables = []
    settings = get_table_settings(settings_mode)

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)

        if pages:
            page_nums = parse_page_range(pages, total_pages)
        else:
            page_nums = list(range(1, total_pages + 1))

        for page_num in page_nums:
            page = pdf.pages[page_num - 1]
            page_tables = page.extract_tables(settings) if settings else page.extract_tables()

            for table_num, table in enumerate(page_tables, 1):
                if table:
                    if output_format == "csv":
                        formatted = table_to_csv(table)
                    else:
                        formatted = table_to_markdown(table)
                    tables.append((page_num, table_num, formatted))

    return tables


def main():
    parser = argparse.ArgumentParser(
        description="Extract tables from PDF files using pdfplumber"
    )
    parser.add_argument("pdf_file", help="Path to PDF file")
    parser.add_argument(
        "--pages",
        help="Page range (e.g., '1-10', '5', '1,3,5-7')",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "csv"],
        default="markdown",
        help="Output format (default: markdown)",
    )
    parser.add_argument(
        "--settings",
        choices=["default", "explicit", "stream"],
        default="default",
        help="Table detection mode (default: default)",
    )
    parser.add_argument(
        "-o", "--output",
        help="Output path (file for md, directory for csv)",
    )

    args = parser.parse_args()

    if not Path(args.pdf_file).exists():
        print(f"Error: File not found: {args.pdf_file}", file=sys.stderr)
        sys.exit(1)

    try:
        tables = extract_tables(
            args.pdf_file,
            args.pages,
            args.format,
            args.settings,
        )

        if not tables:
            print("No tables found in the specified pages.")
            return

        if args.format == "csv" and args.output:
            # Save each table to separate CSV file
            output_dir = Path(args.output)
            output_dir.mkdir(parents=True, exist_ok=True)

            for page_num, table_num, content in tables:
                filename = f"page{page_num}_table{table_num}.csv"
                (output_dir / filename).write_text(content, encoding="utf-8")
                print(f"Saved: {output_dir / filename}")
        elif args.output:
            # Save all tables to single file
            output_parts = []
            for page_num, table_num, content in tables:
                output_parts.append(f"## Page {page_num}, Table {table_num}\n\n{content}")

            Path(args.output).write_text("\n\n".join(output_parts), encoding="utf-8")
            print(f"Tables saved to: {args.output}")
        else:
            # Print to stdout
            for page_num, table_num, content in tables:
                print(f"\n## Page {page_num}, Table {table_num}\n")
                print(content)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
