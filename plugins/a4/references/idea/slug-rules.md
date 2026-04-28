# Idea Slug Rules

Produce a URL-friendly slug from the title:

- Lowercase the entire string (ASCII letters only; Korean / CJK characters pass through untouched since they have no case).
- Replace whitespace runs with a single hyphen.
- Remove punctuation that is not a hyphen, alphanumeric, or a non-ASCII word character (keep Korean hangul, kanji, etc.).
- Collapse multiple consecutive hyphens to one.
- Trim leading and trailing hyphens.
- Truncate to 50 characters at a hyphen boundary where possible (never mid-word for ASCII; best-effort for CJK).

If the slug ends up empty after normalization (e.g., argument was pure punctuation), fall back to `untitled`.

## Examples

| Title | Slug |
|-------|------|
| `콜그래프에 주석 렌더링 넣기` | `콜그래프에-주석-렌더링-넣기` |
| `Add caching layer to API` | `add-caching-layer-to-api` |
| `!!!!???` | `untitled` |
| `Rename: the Foo module, v2.0` | `rename-the-foo-module-v20` |
