import os
import sys
import re
import argparse

def parse_hhc_regex(input_path, output_path):
    """
    Process HHC file using regular expressions instead of BeautifulSoup.
    Accurately parses even with broken HTML structure or unclosed tags.
    """
    
    # 1. Read file
    content = ""
    encodings = ['utf-8', 'cp949', 'euc-kr', 'cp1252', 'latin1']
    
    for enc in encodings:
        try:
            with open(input_path, 'r', encoding=enc) as f:
                content = f.read()
            print(f"[INFO] Encoding detected successfully: {enc}")
            break
        except UnicodeDecodeError:
            continue
            
    if not content:
        print(f"[ERROR] Unable to read encoding of file '{input_path}'.")
        return

    # Convert to lower to find tags ignoring case (keep original data for extraction)
    # Sequential search based on position index
    
    # Compile patterns to find
    # Match without case sensitivity using re.IGNORECASE
    # <param name="Name" value="..."> pattern
    name_pattern = re.compile(r'<param\s+name="?Name"?\s+value="([^"]*)"', re.IGNORECASE)
    # <param name="Local" value="..."> pattern
    local_pattern = re.compile(r'<param\s+name="?Local"?\s+value="([^"]*)"', re.IGNORECASE)
    
    # Token pattern for traversing entire structure
    # 1. <UL> (start indent)
    # 2. </UL> (end indent)
    # 3. <OBJECT ...> ... </OBJECT> (data block)
    token_pattern = re.compile(r'(<ul[^>]*>)|(</ul[^>]*>)|(<object[^>]*>.*?</object>)', re.IGNORECASE | re.DOTALL)

    markdown_lines = []
    level = -1 # Start from -1 so that first UL becomes 0, since root UL usually comes first
    
    # Search for patterns in entire string
    for match in token_pattern.finditer(content):
        token = match.group(0)
        token_lower = token.lower()
        
        if token_lower.startswith('<ul'):
            level += 1
        elif token_lower.startswith('</ul'):
            level = max(-1, level - 1)
        elif token_lower.startswith('<object'):
            # Process item according to current level
            # Extract Name and Local from Object block
            name_match = name_pattern.search(token)
            local_match = local_pattern.search(token)
            
            name = "Untitled"
            link = "#"
            
            if name_match:
                name = name_match.group(1).strip()
            
            if local_match:
                # Change backslashes to slashes and remove any HTML residue
                raw_link = local_match.group(1).replace('\\', '/')
                # Check if link ends with .htm, .html, or trim if strange characters (>, <) are included
                if '>' in raw_link: 
                    raw_link = raw_link.split('>')[0]
                if '"' in raw_link:
                    raw_link = raw_link.split('"')[0]
                link = raw_link

            # Generate Markdown
            # Treat level -1 (outside root) as 0
            current_indent = "  " * max(0, level)

            # name이 "Untitled"인 경우 건너뛰기
            if name == "Untitled":
                continue

            if link != "#" and link.strip():
                markdown_lines.append(f"{current_indent}- [{name}]({link})")
            else:
                markdown_lines.append(f"{current_indent}- {name}")

    # Save result
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# Table of Contents\n\n")
            f.write("\n".join(markdown_lines))
        print(f"[SUCCESS] Conversion complete! File created: {output_path}")
    except Exception as e:
        print(f"[ERROR] Error occurred while saving file: {e}")

def main():
    parser = argparse.ArgumentParser(description='Convert HHC file to Markdown (Regex-based Robust version)')
    parser.add_argument('input_file', help='Path to the .hhc file to convert')
    parser.add_argument('-o', '--output', help='Path to the output .md file')

    args = parser.parse_args()
    
    input_path = args.input_file
    if args.output:
        output_path = args.output
    else:
        output_path = os.path.splitext(input_path)[0] + ".md"

    if os.path.exists(input_path):
        parse_hhc_regex(input_path, output_path)
    else:
        print(f"[ERROR] Input file not found: {input_path}")

if __name__ == "__main__":
    main()