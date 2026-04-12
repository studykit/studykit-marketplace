# PlantUML Plugin

A plugin for composing, referencing, and validating PlantUML diagrams.

## Components

| Type | Name | Purpose |
|------|------|---------|
| Skill | `plantuml:compose` | Create, reference, or validate PlantUML from natural language |
| Script | `skills/compose/scripts/validate.sh` | Local validation using the bundled PlantUML jar |
| Script | `skills/compose/scripts/validate_online.py` | Online validation fallback |

## Features

- **Create mode** — generate standalone `.puml` files or PlantUML fenced blocks for Markdown
- **Reference mode** — explain syntax and provide minimal examples without modifying files
- **Check mode** — validate `.puml` files or embedded Markdown blocks and explain failures
- **Bundled references** — includes diagram-specific references and advanced syntax notes under `skills/compose/references/`
- **Local + online validation** — use the bundled jar locally or fall back to the online validator

## Supported Reference Topics

The bundled references currently cover:

- Sequence, class, activity, use case, component, deployment, object, state, ER, Gantt, mindmap, WBS, network, timing, JSON/YAML, C4, and other specialized diagrams
- Supplemental topics such as Creole formatting, links, sprites, and sprite names

## Prerequisites

For local validation, Java is required because the plugin bundles `skills/compose/scripts/plantuml.1.2026.2.jar`.

```bash
java -version
```

Online validation requires no local PlantUML installation.

## Usage

### Explicit Skill

```text
/plantuml:compose create sequence diagram of order processing
/plantuml:compose reference class diagram syntax for generics
/plantuml:compose check docs/architecture.md
```

### Inferred Mode

You can also ask naturally:

> Draw a sequence diagram showing the login flow
> Show me the PlantUML syntax for a deployment diagram
> Validate this PlantUML block in my Markdown file

## Validation

```bash
# Local
bash plugins/plantuml/skills/compose/scripts/validate.sh diagram.puml

# Online fallback
uv run plugins/plantuml/skills/compose/scripts/validate_online.py diagram.puml
```

## Plugin Structure

```text
plantuml/
├── .claude-plugin/
├── .codex-plugin/
├── README.md
└── skills/
    └── compose/
        ├── SKILL.md
        ├── references/
        └── scripts/
```
