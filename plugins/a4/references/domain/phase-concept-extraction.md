# Phase 1: Concept Extraction

Populate `<concepts>` in `a4/domain.md` — the canonical glossary of cross-cutting domain terms.

## Procedure

1. **Scan all UCs horizontally** for nouns appearing across multiple UCs — entities, value objects, configurations, signals.

2. **Filter** — drop:
   - Actor-shaped nouns (already in `actors.md`).
   - Implementation/UI nouns (button, screen, response). The Domain Model is "what exists", not "how it's presented".
   - One-off nouns appearing in only one UC unless they are clearly central to the domain.

3. **Present the candidate list** to the user. For each concept: confirm name, one-line definition, 1–2 key attributes, and the UCs that reference it.

4. **Write the Glossary table** to `a4/domain.md` after the list is confirmed.

## Constraints

- Concepts use **domain language**, not implementation types. No `VARCHAR(255)`, `INT`, `string` — just attribute names.
- No API endpoints or serialization formats.
- Concept names become **canonical terms**. Architecture component names, schema fields, and contract parameters reuse them.
