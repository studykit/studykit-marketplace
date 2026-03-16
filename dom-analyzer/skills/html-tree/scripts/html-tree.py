# /// script
# requires-python = ">=3.10"
# dependencies = ["beautifulsoup4>=4.12", "lxml>=5.0"]
# ///
"""DOM Hierarchy Visualizer — tree visualization with depth control,
selector filtering, and parent context display.

Uses BeautifulSoup + lxml for robust parsing of real-world HTML including
inline CSS, <style>/<script>/<noscript> blocks without errors.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

from bs4 import BeautifulSoup, Tag, NavigableString, Comment


SUMMARY_TAGS = frozenset({"style", "script", "noscript"})
SUPPRESS_ATTR_TAGS = frozenset({"svg", "path"})


@dataclass
class Options:
    show_text: bool = False
    max_depth: float = float("inf")
    show_attributes: bool = True
    compact: bool = True
    output_file: str | None = None
    selector: str | None = None
    show_parents: int = 0
    highlight_path: bool = False
    match_index: int | None = None


@dataclass
class DOMVisualizer:
    options: Options = field(default_factory=Options)
    _lines: list[str] = field(default_factory=list, init=False)

    # -- public ---------------------------------------------------------------

    def visualize(self, html: str) -> str:
        soup = BeautifulSoup(html, "lxml")
        root = soup.find("html")
        if root is None:
            root = soup

        self._lines = []

        if self.options.selector:
            return self._visualize_selector(soup)

        self._header()
        self._traverse(root, 0)
        return "\n".join(self._lines)

    # -- selector mode --------------------------------------------------------

    def _visualize_selector(self, soup: BeautifulSoup) -> str:
        try:
            nodes: list[Tag] = soup.select(self.options.selector)
        except Exception as exc:
            self._header()
            self._lines.append(f'Invalid CSS selector: "{self.options.selector}" "{exc}"')
            return "\n".join(self._lines)

        self._header()
        self._lines.append(f'Selector: "{self.options.selector}"')
        self._lines.append(f"Found: {len(nodes)} match{'es' if len(nodes) != 1 else ''}")

        if not nodes:
            self._lines.append("")
            self._lines.append(f'No elements found matching selector: "{self.options.selector}"')
            return "\n".join(self._lines)

        if self.options.match_index is not None:
            idx = self.options.match_index - 1
            if idx < 0 or idx >= len(nodes):
                self._lines.append("")
                self._lines.append(
                    f"Invalid match index: {self.options.match_index}. Valid range: 1-{len(nodes)}"
                )
                return "\n".join(self._lines)
            show = [(idx, nodes[idx])]
        else:
            show = list(enumerate(nodes))

        for actual_idx, node in show:
            self._lines.append("")
            self._lines.append(f"=== Match {actual_idx + 1} of {len(nodes)} ===")
            self._lines.append(f"Path: {self._node_path(node)}")

            if self.options.highlight_path:
                self._lines.append(">>> SELECTED NODE <<<")

            if self.options.show_parents > 0:
                self._with_context(node, self.options.show_parents)
            else:
                self._traverse(node, 0)

        return "\n".join(self._lines)

    # -- traversal ------------------------------------------------------------

    def _traverse(self, node: Tag | NavigableString, depth: int) -> None:
        if depth > self.options.max_depth:
            return

        indent = "  " * depth

        if isinstance(node, Comment):
            return

        if isinstance(node, NavigableString):
            if self.options.show_text:
                text = str(node).strip()
                if text:
                    preview = text[:100] + ("..." if len(text) > 100 else "")
                    self._lines.append(f"{indent}[TEXT] {preview}")
            return

        if not isinstance(node, Tag):
            return

        tag = node.name
        line = f"{indent}<{tag}"

        # summarize style/script/noscript as single line
        if tag in SUMMARY_TAGS:
            content = node.string or ""
            size = len(content.strip())
            line += self._format_attrs(node)
            line += f"> [{size} chars]"
            self._lines.append(line)
            return

        # inline style attribute summary
        inline_style = node.get("style") if self.options.show_attributes else None

        line += self._format_attrs(node)
        line += ">"

        # inline text for leaf nodes
        if not node.find_all(recursive=False):
            direct_text = self._direct_text(node)
            if direct_text and self.options.show_text:
                preview = direct_text[:50] + ("..." if len(direct_text) > 50 else "")
                line += f" [TEXT: {preview}]"

        if inline_style and self.options.compact:
            style_str = inline_style if isinstance(inline_style, str) else str(inline_style)
            preview = style_str[:60] + ("..." if len(style_str) > 60 else "")
            line += f" [style: {preview}]"

        self._lines.append(line)

        for child in node.children:
            self._traverse(child, depth + 1)

    # -- context display ------------------------------------------------------

    def _with_context(self, node: Tag, levels: int) -> None:
        ancestors: list[Tag] = []
        current = node.parent
        for _ in range(levels):
            if current is None or not isinstance(current, Tag) or current.name == "[document]":
                break
            ancestors.insert(0, current)
            current = current.parent

        for i, anc in enumerate(ancestors):
            indent = "  " * i
            self._lines.append(f"{indent}<{anc.name}> (parent context)")

        self._traverse(node, len(ancestors))

    # -- helpers --------------------------------------------------------------

    def _header(self) -> None:
        self._lines.append("DOM Hierarchy Visualization")
        self._lines.append("─" * 50)

    def _format_attrs(self, tag: Tag) -> str:
        if not self.options.show_attributes or not tag.attrs:
            return ""
        if tag.name in SUPPRESS_ATTR_TAGS:
            return ""

        attrs: list[str] = []

        if tag.get("id"):
            attrs.append(f'id="{tag["id"]}"')

        classes = tag.get("class")
        if classes:
            cls_str = " ".join(classes) if isinstance(classes, list) else classes
            attrs.append(f'class="{cls_str}"')

        for key, val in tag.attrs.items():
            if key in ("id", "class", "style"):
                continue
            if key.startswith("data-"):
                v = " ".join(val) if isinstance(val, list) else val
                attrs.append(f'{key}="{v}"')
            elif not self.options.compact:
                v = " ".join(val) if isinstance(val, list) else val
                attrs.append(f'{key}="{v}"')

        if not attrs:
            return ""
        return " " + " ".join(attrs)

    def _node_path(self, node: Tag) -> str:
        parts: list[str] = []
        current: Tag | None = node
        while current and isinstance(current, Tag) and current.name != "[document]":
            tag = current.name
            classes = current.get("class")
            if classes:
                cls = ".".join(classes) if isinstance(classes, list) else classes
                tag += f".{cls}"
            idx = self._child_index(current)
            if idx > 0:
                tag += f"[{idx}]"
            parts.insert(0, tag)
            current = current.parent
        return " > ".join(parts)

    @staticmethod
    def _child_index(tag: Tag) -> int:
        if tag.parent is None:
            return 0
        idx = 1
        for sib in tag.previous_siblings:
            if isinstance(sib, Tag):
                idx += 1
        return idx

    @staticmethod
    def _direct_text(tag: Tag) -> str:
        return "".join(
            str(c).strip() for c in tag.children if isinstance(c, NavigableString) and not isinstance(c, Comment)
        ).strip()


def parse_args(argv: list[str] | None = None) -> tuple[str | None, Options]:
    parser = argparse.ArgumentParser(
        prog="html-tree",
        description="DOM Hierarchy Visualizer",
    )
    parser.add_argument("file", nargs="?", help="Input HTML file path")
    parser.add_argument("--show-text", action="store_true", help="Show text node content")
    parser.add_argument("--no-attributes", action="store_true", help="Hide all attributes")
    parser.add_argument("--full", action="store_true", help="Show all attributes (not just id, class, data-*)")
    parser.add_argument("--max-depth", type=int, default=None, help="Maximum traversal depth")
    parser.add_argument("--output", type=str, default=None, help="Output to file")
    parser.add_argument("--selector", type=str, default=None, help="CSS selector to filter elements")
    parser.add_argument("--show-parents", type=int, default=0, help="Show n ancestor levels above matched nodes")
    parser.add_argument("--highlight-path", action="store_true", help="Mark the path to selected nodes")
    parser.add_argument("--match-index", type=int, default=None, help="Show only the nth match (1-based)")

    args = parser.parse_args(argv)

    opts = Options(
        show_text=args.show_text,
        max_depth=args.max_depth if args.max_depth is not None else float("inf"),
        show_attributes=not args.no_attributes,
        compact=not args.full,
        output_file=args.output,
        selector=args.selector,
        show_parents=args.show_parents,
        highlight_path=args.highlight_path,
        match_index=args.match_index,
    )
    return args.file, opts


def main() -> None:
    file_path, opts = parse_args()

    if file_path is None:
        print("Error: Please provide an HTML file path", file=sys.stderr)
        sys.exit(1)

    p = Path(file_path).resolve()
    if not p.exists():
        print(f"Error: File not found: {p}", file=sys.stderr)
        sys.exit(1)

    html = p.read_text(encoding="utf-8")
    viz = DOMVisualizer(options=opts)
    result = viz.visualize(html)

    if opts.output_file:
        Path(opts.output_file).write_text(result, encoding="utf-8")
        print(f"Output written to: {opts.output_file}")
    else:
        print(result)


if __name__ == "__main__":
    main()
