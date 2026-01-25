# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "lxml",
#     "markdownify",
# ]
# ///
"""
EPUB to Markdown Extractor

Extracts chapter-by-chapter markdown files from EPUB using metadata-based extraction.
Uses content.opf spine for correct reading order.

Usage:
    uv run extract_epub.py <input.epub> [-o output_dir] [--no-images] [--no-frontmatter]
"""

import argparse
import json
import re
import zipfile
from pathlib import Path
from urllib.parse import unquote

from lxml import etree
from markdownify import markdownify as md


def sanitize_filename(title: str, max_length: int = 50) -> str:
    """Sanitize title for use as filename."""
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', title)
    # Replace multiple spaces/underscores with single underscore
    sanitized = re.sub(r'[\s_]+', '_', sanitized)
    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')
    # Truncate to max length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rstrip('_')
    return sanitized or 'untitled'


def find_opf_path(epub_zip: zipfile.ZipFile) -> str:
    """Find the path to content.opf from container.xml."""
    try:
        container_xml = epub_zip.read('META-INF/container.xml')
        tree = etree.fromstring(container_xml)

        # Handle namespaces
        ns = {'container': 'urn:oasis:names:tc:opendocument:xmlns:container'}
        rootfile = tree.find('.//container:rootfile', ns)

        if rootfile is not None:
            return rootfile.get('full-path')
    except Exception:
        pass

    # Fallback: search for content.opf
    for name in epub_zip.namelist():
        if name.endswith('content.opf') or name.endswith('.opf'):
            return name

    raise FileNotFoundError("Could not find content.opf in EPUB")


def parse_opf(epub_zip: zipfile.ZipFile, opf_path: str) -> tuple[dict, list, str]:
    """
    Parse content.opf to get manifest and spine.

    Returns:
        manifest: dict mapping id -> {href, media_type}
        spine: list of item ids in reading order
        opf_dir: directory containing the OPF file
    """
    opf_content = epub_zip.read(opf_path)
    tree = etree.fromstring(opf_content)

    # Get OPF directory for resolving relative paths
    opf_dir = str(Path(opf_path).parent)
    if opf_dir == '.':
        opf_dir = ''

    # Define namespaces
    ns = {
        'opf': 'http://www.idpf.org/2007/opf',
        'dc': 'http://purl.org/dc/elements/1.1/'
    }

    # Parse manifest
    manifest = {}
    for item in tree.findall('.//opf:manifest/opf:item', ns):
        item_id = item.get('id')
        href = item.get('href')
        media_type = item.get('media-type', '')
        if item_id and href:
            manifest[item_id] = {
                'href': unquote(href),
                'media_type': media_type
            }

    # Parse spine (reading order)
    spine = []
    for itemref in tree.findall('.//opf:spine/opf:itemref', ns):
        idref = itemref.get('idref')
        if idref:
            spine.append(idref)

    return manifest, spine, opf_dir


def word_to_number(word: str) -> int | None:
    """Convert English number word to integer.

    Handles: ONE-FIFTY, TWENTY-ONE through FIFTY-NINE
    """
    word = word.upper().strip()

    base_numbers = {
        'ONE': 1, 'TWO': 2, 'THREE': 3, 'FOUR': 4, 'FIVE': 5,
        'SIX': 6, 'SEVEN': 7, 'EIGHT': 8, 'NINE': 9, 'TEN': 10,
        'ELEVEN': 11, 'TWELVE': 12, 'THIRTEEN': 13, 'FOURTEEN': 14,
        'FIFTEEN': 15, 'SIXTEEN': 16, 'SEVENTEEN': 17, 'EIGHTEEN': 18,
        'NINETEEN': 19, 'TWENTY': 20, 'THIRTY': 30, 'FORTY': 40, 'FIFTY': 50
    }

    # Direct match
    if word in base_numbers:
        return base_numbers[word]

    # Compound numbers like TWENTY-ONE, THIRTY-FIVE
    if '-' in word:
        parts = word.split('-')
        if len(parts) == 2 and parts[0] in base_numbers and parts[1] in base_numbers:
            tens = base_numbers[parts[0]]
            ones = base_numbers[parts[1]]
            if tens >= 20 and ones <= 9:
                return tens + ones

    return None


def normalize_title(title: str) -> str:
    """Normalize title by adding spaces in concatenated words.

    Handles patterns like:
    - "CHAPTERTWO" -> "CHAPTER TWO"
    - "CHAPTERTWENTY-ONE" -> "CHAPTER TWENTY-ONE"
    """
    # Add space before common chapter number words
    number_words = ['ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'SIX', 'SEVEN',
                    'EIGHT', 'NINE', 'TEN', 'ELEVEN', 'TWELVE', 'THIRTEEN',
                    'FOURTEEN', 'FIFTEEN', 'SIXTEEN', 'SEVENTEEN', 'EIGHTEEN',
                    'NINETEEN', 'TWENTY', 'THIRTY', 'FORTY', 'FIFTY']

    for word in number_words:
        # Match word at the end or before a hyphen, without space before it
        title = re.sub(rf'([A-Za-z])({word})(?=[-\s]|$)', rf'\1 \2', title)

    return title


def abbreviate_chapter_for_filename(title: str) -> str:
    """Convert 'CHAPTER EIGHTEEN' to 'CH18' for shorter filenames.

    Examples:
    - "CHAPTER ONE - WHY CALCULUS" -> "CH1 - WHY CALCULUS"
    - "Chapter Twenty-One - Title" -> "CH21 - Title"
    - "CHAPTER 5 - TITLE" -> "CH5 - TITLE"
    """
    # Pattern: CHAPTER followed by number word or digit
    def replace_chapter(match):
        chapter_word = match.group(1)  # e.g., "EIGHTEEN" or "21"
        rest = match.group(2)  # e.g., " - WHY CALCULUS"

        # Try to convert word to number
        num = word_to_number(chapter_word)
        if num is not None:
            return f"CH{num}{rest}"

        # Already a digit
        if chapter_word.isdigit():
            return f"CH{chapter_word}{rest}"

        # Can't convert, return original
        return match.group(0)

    # Match "CHAPTER " followed by word/number, then rest of string
    result = re.sub(
        r'(?i)CHAPTER\s+([A-Z]+-?[A-Z]*|\d+)(.*)',
        replace_chapter,
        title
    )

    return result


def is_chapter_number_heading(text: str) -> bool:
    """Check if text is a chapter number heading (e.g., 'CHAPTER ONE', 'Chapter 1')."""
    text_lower = text.lower().strip()
    # Match patterns like "chapter one", "chapter 1", "ch. 1", etc.
    return bool(re.match(r'^(chapter|ch\.?)\s*(\d+|[a-z]+(-[a-z]+)?)$', text_lower))


def extract_title_from_html(html_content: str) -> str:
    """Extract title from HTML content.

    Combines chapter number heading with chapter title when both exist.
    E.g., "CHAPTER TWO" + "THE DERIVATIVE" -> "CHAPTER TWO - THE DERIVATIVE"
    """
    try:
        tree = etree.HTML(html_content)

        # Collect all headings (h1, h2, h3) in order
        headings = []
        for tag in ['h1', 'h2', 'h3']:
            for elem in tree.findall(f'.//{tag}'):
                text = etree.tostring(elem, method='text', encoding='unicode').strip()
                if text:
                    headings.append(normalize_title(text))

        if not headings:
            # Fallback to <title> tag
            title_elem = tree.find('.//title')
            if title_elem is not None and title_elem.text:
                return title_elem.text.strip()
            return ''

        # If first heading is a chapter number and there's a second heading,
        # combine them as "CHAPTER X - Title"
        if len(headings) >= 2 and is_chapter_number_heading(headings[0]):
            return f"{headings[0]} - {headings[1]}"

        # Otherwise return just the first heading
        return headings[0]

    except Exception:
        pass

    return ''


def extract_epub(
    epub_path: str,
    output_dir: str,
    extract_images: bool = True,
    add_frontmatter: bool = True
) -> dict:
    """
    Extract EPUB to markdown files.

    Args:
        epub_path: Path to EPUB file
        output_dir: Output directory
        extract_images: Whether to extract images
        add_frontmatter: Whether to add YAML frontmatter

    Returns:
        Metadata dict with chapter information
    """
    epub_path = Path(epub_path)
    output_dir = Path(output_dir)

    # Create output directories
    output_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        'source': str(epub_path),
        'chapters': []
    }

    with zipfile.ZipFile(epub_path, 'r') as epub_zip:
        # Find and parse content.opf
        opf_path = find_opf_path(epub_zip)
        manifest, spine, opf_dir = parse_opf(epub_zip, opf_path)

        # Extract images preserving folder name as referenced in HTML
        # (e.g., if HTML references "images/img.jpg", extract to "images/")
        if extract_images:
            for item_id, item_info in manifest.items():
                if item_info['media_type'].startswith('image/'):
                    href = item_info['href']
                    # Resolve full path in EPUB
                    if opf_dir:
                        full_path = f"{opf_dir}/{href}"
                    else:
                        full_path = href

                    # Use just the immediate parent folder and filename
                    # e.g., "html/images/img.jpg" -> "images/img.jpg"
                    href_path = Path(href)
                    if len(href_path.parts) > 1:
                        # Keep parent folder + filename (e.g., images/img.jpg)
                        relative_path = Path(href_path.parts[-2]) / href_path.name
                    else:
                        # Just filename if no parent folder
                        relative_path = Path(href_path.name)

                    output_image_path = output_dir / relative_path
                    output_image_path.parent.mkdir(parents=True, exist_ok=True)

                    try:
                        image_data = epub_zip.read(full_path)
                        output_image_path.write_bytes(image_data)
                    except KeyError:
                        print(f"Warning: Could not find image: {full_path}")

        # Process chapters in spine order
        for seq, item_id in enumerate(spine, 1):
            if item_id not in manifest:
                print(f"Warning: Spine item '{item_id}' not found in manifest")
                continue

            item_info = manifest[item_id]

            # Only process HTML/XHTML files
            if item_info['media_type'] not in ('application/xhtml+xml', 'text/html'):
                continue

            href = item_info['href']

            # Resolve full path
            if opf_dir:
                full_path = f"{opf_dir}/{href}"
            else:
                full_path = href

            try:
                html_content = epub_zip.read(full_path).decode('utf-8')
            except KeyError:
                print(f"Warning: Could not find file: {full_path}")
                continue
            except UnicodeDecodeError:
                # Try other encodings
                raw_content = epub_zip.read(full_path)
                for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                    try:
                        html_content = raw_content.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    print(f"Warning: Could not decode file: {full_path}")
                    continue

            # Extract title
            title = extract_title_from_html(html_content)
            if not title:
                title = Path(href).stem

            # Convert to markdown (image paths remain unchanged)
            markdown_content = md(html_content, heading_style='ATX', strip=['script', 'style'])

            # Clean up markdown
            # Remove excessive blank lines
            markdown_content = re.sub(r'\n{3,}', '\n\n', markdown_content)
            markdown_content = markdown_content.strip()

            # Add YAML frontmatter
            if add_frontmatter:
                frontmatter = f"""---
title: "{title.replace('"', '\\"')}"
sequence: {seq}
source: {full_path}
---

"""
                markdown_content = frontmatter + markdown_content

            # Generate filename (abbreviate CHAPTER X -> CHX)
            abbreviated_title = abbreviate_chapter_for_filename(title)
            sanitized_title = sanitize_filename(abbreviated_title)
            sanitized_title = sanitized_title.replace('_-_', '-')
            filename = f"{seq:03d}_{sanitized_title}.md"

            # Write markdown file
            output_file = output_dir / filename
            output_file.write_text(markdown_content, encoding='utf-8')

            # Add to metadata
            metadata['chapters'].append({
                'sequence': seq,
                'title': title,
                'source': full_path,
                'output': filename
            })

            print(f"Extracted: {filename}")

    # Write metadata.json
    metadata_file = output_dir / 'metadata.json'
    metadata_file.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding='utf-8')

    print(f"\nExtraction complete!")
    print(f"  Chapters: {len(metadata['chapters'])}")
    print(f"  Output: {output_dir}")
    print(f"  Metadata: {metadata_file}")

    return metadata


def main():
    parser = argparse.ArgumentParser(
        description='Extract EPUB to chapter-by-chapter markdown files'
    )
    parser.add_argument('epub', help='Input EPUB file')
    parser.add_argument(
        '-o', '--output',
        help='Output directory (default: <epub_name>/)'
    )
    parser.add_argument(
        '--no-images',
        action='store_true',
        help='Skip image extraction'
    )
    parser.add_argument(
        '--no-frontmatter',
        action='store_true',
        help='Skip YAML frontmatter in markdown files'
    )

    args = parser.parse_args()

    epub_path = Path(args.epub)
    if not epub_path.exists():
        print(f"Error: File not found: {epub_path}")
        return 1

    if not epub_path.suffix.lower() == '.epub':
        print(f"Warning: File may not be an EPUB: {epub_path}")

    # Default output directory
    output_dir = args.output
    if not output_dir:
        output_dir = epub_path.stem

    extract_epub(
        str(epub_path),
        output_dir,
        extract_images=not args.no_images,
        add_frontmatter=not args.no_frontmatter
    )

    return 0


if __name__ == '__main__':
    exit(main())
