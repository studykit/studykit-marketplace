# Verification Checklist

## Chapter Boundary Verification

For each split file, check that:
1. **First page** contains the chapter title (e.g., "CHAPTER ONE", "Chapter 1")
2. **Last page** shows the correct book page number in header/footer

```bash
# Check first page of a split file
uv run "$SCRIPT_DIR/pages_md.py" "<split_file>.pdf" 1 | head -10

# Check last page of a split file (get total pages first)
uv run "$SCRIPT_DIR/total_page.py" "<split_file>.pdf"
# → Total pages: 33
uv run "$SCRIPT_DIR/pages_md.py" "<split_file>.pdf" 33 | head -5
```

**Example verification**:
```bash
# Verify Ch2 file (003_Ch02_BSpline_Basis_p47-79.pdf)
uv run "$SCRIPT_DIR/pages_md.py" 003_Ch02_BSpline_Basis_p47-79.pdf 1 | head -5
# Expected: "CHAPTER TWO" or "CHAPTER 2"

uv run "$SCRIPT_DIR/pages_md.py" 003_Ch02_BSpline_Basis_p47-79.pdf 33 | head -3
# Expected: Page number "79" visible in content (e.g., "Exercises 79")
```

## Common Issues

| Issue | Symptom | Cause |
|-------|---------|-------|
| Chapter overlap | Ch2 file ends with "CHAPTER THREE" | End page too late (includes next chapter start) |
| Missing pages | Ch3 starts at page 82, not 81 | Start page too late (skipped chapter title page) |
| Offset drift | Pages off by 1-2 after certain chapter | Missing/blank pages in PDF not accounted for |

## Detecting Offset Changes

Some books have **inconsistent offsets** due to missing or blank pages. Always verify offset at multiple points:

```bash
# Check offset at beginning (Ch1)
uv run "$SCRIPT_DIR/pages_md.py" "$ARGUMENTS" 14 | head -2
# → "2 Curve and Surface Basics" (book page 2, PDF 14 → offset 12)

# Check offset at middle (Ch5)
uv run "$SCRIPT_DIR/pages_md.py" "$ARGUMENTS" 238 | head -2
# → "228 Fundamental Geometric Algorithms" (book page 228, PDF 238 → offset 10)

# If offsets differ, find where the change occurs and adjust accordingly
```

## Quick Checklist

- [ ] First split file starts with Front Matter/Cover
- [ ] Each chapter file starts with "CHAPTER" keyword
- [ ] Last page of each chapter shows expected book page number
- [ ] No chapter title appears at the end of another chapter's file
- [ ] Total pages of all split files equals original PDF total pages
