#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import os
import sys
import signal
import re
import argparse
import html

# Handle broken pipe error when piping to head, etc.
signal.signal(signal.SIGPIPE, signal.SIG_DFL)


class TreeNode:
    """Represents a node in the TOC tree."""
    def __init__(self, name: str, link: str | None = None) -> None:
        self.name: str = name
        self.link: str | None = link
        self.children: list[TreeNode] = []
        self.number: str = ""

    def add_child(self, child: TreeNode) -> TreeNode:
        self.children.append(child)
        return child


def parse_hhc(input_path: str) -> TreeNode | None:
    """
    Parse HHC file and return a tree structure.

    Args:
        input_path: Path to input .hhc file

    Returns:
        TreeNode: Root node of the TOC tree, or None on error
    """
    # Read file with encoding detection
    content = ""
    encodings = ['utf-8', 'cp949', 'euc-kr', 'cp1252', 'latin1']

    for enc in encodings:
        try:
            with open(input_path, 'r', encoding=enc) as f:
                content = f.read()
            break
        except UnicodeDecodeError:
            continue

    if not content:
        print(f"[ERROR] Unable to read encoding of file '{input_path}'.", file=sys.stderr)
        return None

    # Regex patterns
    name_pattern = re.compile(r'<param\s+name="?Name"?\s+value="([^"]*)"', re.IGNORECASE)
    local_pattern = re.compile(r'<param\s+name="?Local"?\s+value="([^"]*)"', re.IGNORECASE)
    token_pattern = re.compile(r'(<ul[^>]*>)|(</ul[^>]*>)|(<object[^>]*>.*?</object>)', re.IGNORECASE | re.DOTALL)

    # Build tree structure
    root = TreeNode("ROOT")
    stack = [root]  # Stack to track parent nodes
    last_node = root  # Track last added node for UL nesting

    for match in token_pattern.finditer(content):
        token = match.group(0)
        token_lower = token.lower()

        if token_lower.startswith('<ul'):
            # Go deeper - last node becomes parent for next items
            if last_node and last_node != stack[-1]:
                stack.append(last_node)
        elif token_lower.startswith('</ul'):
            # Go back up
            if len(stack) > 1:
                stack.pop()
        elif token_lower.startswith('<object'):
            name_match = name_pattern.search(token)
            local_match = local_pattern.search(token)

            name = None
            link = None

            if name_match:
                name = html.unescape(name_match.group(1)).strip()
                if name == "Untitled" or not name:
                    name = None

            if local_match:
                raw_link = local_match.group(1).replace('\\', '/')
                if '>' in raw_link:
                    raw_link = raw_link.split('>')[0]
                if '"' in raw_link:
                    raw_link = raw_link.split('"')[0]
                if raw_link.strip():
                    link = raw_link

            if name:
                node = TreeNode(name, link)
                stack[-1].add_child(node)
                last_node = node

    # Assign hierarchical numbers
    def assign_numbers(node: TreeNode, prefix: str = "") -> None:
        for i, child in enumerate(node.children, 1):
            child.number = f"{prefix}{i}" if not prefix else f"{prefix}.{i}"
            assign_numbers(child, child.number)

    assign_numbers(root)

    return root


def find_node_by_number(root: TreeNode, number: str) -> TreeNode | None:
    """Find a node by its hierarchical number (e.g., '5.2')."""
    def search(node: TreeNode) -> TreeNode | None:
        if node.number == number:
            return node
        for child in node.children:
            result = search(child)
            if result:
                return result
        return None
    return search(root)


def collect_rows(
    root: TreeNode | None,
    node_ids: list[str] | None = None,
    max_depth: int | None = None
) -> list[tuple[str, str, str | None]]:
    """
    Collect rows from tree structure.

    Args:
        root: TreeNode root of the tree
        node_ids: List of node IDs to output (e.g., ['5', '5.2'])
        max_depth: Max depth to output (1=starting level only, 2=+children, etc.)

    Returns:
        List of (node_id, name, link) tuples
    """
    if root is None:
        return []

    rows: list[tuple[str, str, str | None]] = []

    def traverse(node: TreeNode, depth: int, base_depth: int) -> None:
        """Traverse tree from a node."""
        # relative_depth: 1 for starting node, 2 for children, etc.
        relative_depth = depth - base_depth + 1

        if depth > 0:  # Skip root node
            # Apply max_depth filter (1-based)
            if max_depth is not None and relative_depth > max_depth:
                return

            rows.append((node.number, node.name, node.link))

        for child in node.children:
            traverse(child, depth + 1, base_depth)

    if node_ids:
        for node_id in node_ids:
            target_node = find_node_by_number(root, node_id)
            if target_node is None:
                print(f"[ERROR] Node ID '{node_id}' not found.", file=sys.stderr)
                continue
            base_depth = node_id.count('.') + 1
            traverse(target_node, base_depth, base_depth)
    else:
        # When no node ID specified, start at depth 1 (children of root)
        traverse(root, 0, 1)

    return rows


def change_ext_to_md(link: str) -> str:
    """Change file extension to .md"""
    if '.' in link:
        base = link.rsplit('.', 1)[0]
        return f"{base}.md"
    return link


def format_as_todo(
    rows: list[tuple[str, str, str | None]],
    has_link: bool = False,
    just_name: bool = False
) -> str:
    """
    Format rows as markdown todo list.

    Args:
        rows: List of (node_id, name, link) tuples
        has_link: If True, only include nodes that have a link
        just_name: If True, output name without markdown link
    """
    LINK_WIDTH = 40
    lines: list[str] = []
    lines.append("# HTML to Markdown conversion task list")
    lines.append("")
    for node_id, name, link in rows:
        if has_link and not link:
            continue
        if link and not just_name:
            md_link = change_ext_to_md(link)
            lines.append(f"- [ ] {link} -> {md_link}")
        else:
            lines.append(f"- [ ] {name}")
    return "\n".join(lines)


def format_as_table(
    rows: list[tuple[str, str, str | None]],
    has_link: bool = False,
    just_name: bool = False
) -> str:
    """
    Format rows as markdown table.

    Args:
        rows: List of (node_id, name, link) tuples
        has_link: If True, only include nodes that have a link
        just_name: If True, output name without markdown link
    """
    NODE_ID_WIDTH = 14
    lines: list[str] = []
    lines.append(f"| {'node_id':<{NODE_ID_WIDTH}} | name |")
    lines.append(f"|{'-' * (NODE_ID_WIDTH + 2)}|------|")
    for node_id, name, link in rows:
        if has_link and not link:
            continue
        if link and not just_name:
            md_link = change_ext_to_md(link)
            lines.append(f"| {node_id:<{NODE_ID_WIDTH}} | [{name}]({md_link}) |")
        else:
            lines.append(f"| {node_id:<{NODE_ID_WIDTH}} | {name} |")
    return "\n".join(lines)


def output_result(output_content: str, output_path: str | None) -> None:
    """Output content to file or stdout."""
    if output_path:
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(output_content)
            print(f"[SUCCESS] Conversion complete! File created: {output_path}", file=sys.stderr)
        except Exception as e:
            print(f"[ERROR] Error occurred while saving file: {e}", file=sys.stderr)
    else:
        print(output_content)

def main() -> None:
    parser = argparse.ArgumentParser(description='Convert HHC file to Markdown (Regex-based Robust version)')
    parser.add_argument('input_file', help='Path to the .hhc file to convert')
    parser.add_argument('-o', '--output', help='Path to the output .md file')
    parser.add_argument('-n', '--node-id', type=str, default=None,
                        help='Node ID(s) to output, comma-separated (e.g., "5" or "4.2,5.1")')
    parser.add_argument('-d', '--max-depth', type=int, default=None,
                        help='Max depth of children to include (relative to starting point)')
    parser.add_argument('--just-name', action='store_true',
                        help='Output name as plain text instead of markdown link')
    parser.add_argument('--has-link', action='store_true',
                        help='Select only nodes that have a link')
    parser.add_argument('--todo', action='store_true',
                        help='Output as markdown todo list format')

    args = parser.parse_args()

    input_path = args.input_file
    output_path = args.output  # None if not specified (will print to stdout)

    # Parse node IDs from comma-separated string
    node_ids = None
    if args.node_id:
        node_ids = [s.strip() for s in args.node_id.split(',')]

    if os.path.exists(input_path):
        tree = parse_hhc(input_path)
        rows = collect_rows(tree, node_ids=node_ids, max_depth=args.max_depth)

        if args.todo:
            output_content = format_as_todo(rows, has_link=args.has_link, just_name=args.just_name)
        else:
            output_content = format_as_table(rows, has_link=args.has_link, just_name=args.just_name)

        output_result(output_content, output_path)
    else:
        print(f"[ERROR] Input file not found: {input_path}")

if __name__ == "__main__":
    main()