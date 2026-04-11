# D2 Compose Skill Map

Use this file first to choose the right reference document for the request.

## Mode Hints

| User intent | Mode |
|---|---|
| "draw", "create", "generate", "make a diagram", "add to markdown", "insert into file" | `create` |
| "syntax", "how do I write", "example for", "reference" | `reference` |
| "check", "validate", "lint", "syntax check", "is this valid", "why does this fail" | `check` |

## Primary References

| Request cues | Reference file |
|---|---|
| general, flowchart, architecture, shapes, connections, containers, styling, icons, layout | `d2-language.md` |
| sequence diagram, message flow, interaction, lifeline, actor, spans | `special-diagrams.md` |
| sql_table, ERD, database schema, entity relationship, foreign key | `special-diagrams.md` |
| class diagram, UML class, fields, methods, visibility | `special-diagrams.md` |
| grid diagram, grid layout, dashboard layout, rows, columns | `special-diagrams.md` |
| theme, color scheme, dark mode, sketch, hand-drawn | `themes.md` |

## Composition Rules

1. Pick one primary reference first.
2. Add `themes.md` if the request mentions a specific theme, color scheme, or visual style.
3. Add `special-diagrams.md` if the diagram uses a special shape type (sql_table, sequence_diagram, class, grid).
4. In `reference` mode, answer from the selected docs without writing files.
5. In `create` mode, preview after any file write.
