# Structurizr Compose Skill Map

Use this file first to choose the right reference document for the request.

## Mode Hints

| User intent | Mode |
|---|---|
| "draw", "create", "generate", "make a diagram", "add to markdown", "insert into file" | `create` |
| "syntax", "how do I write", "example for", "reference" | `reference` |
| "check", "validate", "is this valid", "why does this fail" | `check` |

## Primary View References

| Request cues | Reference file |
|---|---|
| system landscape, all systems overview, high-level architecture | `system-context-view.md` |
| system context, software system in its environment, external dependencies | `system-context-view.md` |
| container, zoom into a system, applications, services, databases, APIs | `container-view.md` |
| component, zoom into a container, controllers, services, repositories | `component-view.md` |
| deployment, infrastructure, cloud, AWS, Docker, servers, nodes | `deployment-view.md` |
| dynamic, runtime behavior, interaction flow, sequence, step-by-step | `dynamic-view.md` |

## Supplemental References

| Need | Reference file |
|---|---|
| DSL syntax, workspace structure, model elements, relationships, identifiers, groups | `dsl-language.md` |
| styles, colors, shapes, borders, fonts, relationship appearance, themes | `styles.md` |
| color theme, C4 Blue, dark, monochrome, custom palette | `themes.md` |
| complete example, multi-view workspace, cookbook patterns | `cookbook.md` |

## Composition Rules

1. Pick one primary view reference first.
2. Add `dsl-language.md` if the request needs general DSL syntax beyond what the view reference covers.
3. Add `styles.md` or `themes.md` if the request mentions specific styling, colors, or themes.
4. Add `cookbook.md` for complete multi-view workspace examples or advanced patterns.
5. In `reference` mode, answer from the selected docs without writing files.
6. In `create` mode, preview after any file write.
