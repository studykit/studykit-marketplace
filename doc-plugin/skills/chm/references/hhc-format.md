# CHM Skill References

## scripts/show_hhc.py

A script that parses HHC (HTML Help Contents) files and outputs the table of contents as a markdown table or TODO list format.

### Basic Usage

```bash
python3 scripts/show_hhc.py <input_file> [options]
```

### Options

| Option | Description |
|--------|-------------|
| `-o, --output <file>` | Output file path (prints to stdout if not specified) |
| `-n, --node-id <id>` | Node ID(s) to output (e.g., "5" or "4.2,5.1") |
| `-d, --max-depth <n>` | Maximum depth to output (relative to starting point) |
| `--just-name` | Output name as plain text instead of markdown link |
| `--has-link` | Only output nodes that have a link |
| `--todo` | Output as TODO list format |

### Examples

**Output entire TOC as table:**
```bash
python3 scripts/show_hhc.py toc.hhc
```

**Output specific node and its children:**
```bash
python3 scripts/show_hhc.py toc.hhc -n 5.2
```

**Specify multiple nodes:**
```bash
python3 scripts/show_hhc.py toc.hhc -n "4.2,5.1,6"
```

**Limit depth (first level only):**
```bash
python3 scripts/show_hhc.py toc.hhc -d 1
```

**Output as TODO list:**
```bash
python3 scripts/show_hhc.py toc.hhc --todo
```

**Output only items with links as TODO:**
```bash
python3 scripts/show_hhc.py toc.hhc --todo --has-link
```

**Save to file:**
```bash
python3 scripts/show_hhc.py toc.hhc -o output.md
```

**Use with pipe (first 20 lines):**
```bash
python3 scripts/show_hhc.py toc.hhc | head -20
```

### Output Formats

**Table format (default):**
```markdown
| node_id        | name |
|----------------|------|
| 1              | [Chapter 1](chapter1.md) |
| 1.1            | [Section 1.1](section1_1.md) |
```

**TODO format (`--todo`):**
```markdown
# HTML to Markdown conversion task list

- [ ] chapter1.htm -> chapter1.md
- [ ] section1_1.htm -> section1_1.md
```
