# PlantUML Plugin

A Claude Code plugin for creating, referencing, and validating PlantUML diagrams.

## Features

- **16 diagram reference skills** — Comprehensive syntax references for all major PlantUML diagram types, sourced from official documentation
- **Diagram creation agent** — Proactively creates PlantUML diagrams from natural language descriptions
- **`/plantuml:create` command** — Explicit diagram creation with support for `.puml` files and Markdown fenced code block injection
- **Syntax validation** — Local (`plantuml -checkonly`) and online (PlantUML server API) validation scripts

## Supported Diagram Types

| Category | Diagrams |
|----------|----------|
| UML Structural | Class, Object, Component, Deployment |
| UML Behavioral | Sequence, Activity, State, Use Case, Timing |
| Non-UML | ER, Gantt, MindMap, WBS, Network (nwdiag) |
| Data | JSON, YAML visualization |
| Other | Salt wireframes, Archimate, Ditaa, EBNF, Regex |

## Prerequisites

For local validation:

```bash
brew install plantuml
```

Online validation requires no local dependencies.

## Usage

### Automatic (Agent)

Simply ask Claude to create a diagram:

> "Draw a sequence diagram showing the login authentication flow"
> "Add a class diagram of the User model to docs/architecture.md"

The `plantuml-writer` agent will trigger automatically.

### Explicit (Command)

```
/plantuml:create sequence diagram of order processing
```

### Output Modes

1. **Standalone `.puml` file** — Default when no target file is specified
2. **Markdown injection** — Inserts a `plantuml` fenced code block into an existing `.md` file

### Validation

```bash
# Local (requires plantuml CLI)
bash scripts/validate.sh diagram.puml

# Online (no local deps)
uv run scripts/validate_online.py diagram.puml
```

## Plugin Structure

```
plantuml/
├── .claude-plugin/
│   └── plugin.json
├── agents/
│   └── plantuml-writer.md
├── scripts/
│   ├── validate.sh
│   └── validate_online.py
└── skills/
    ├── create/SKILL.md
    ├── sequence-diagram/SKILL.md
    ├── class-diagram/SKILL.md
    ├── activity-diagram/SKILL.md
    ├── use-case-diagram/SKILL.md
    ├── component-diagram/SKILL.md
    ├── state-diagram/SKILL.md
    ├── object-diagram/SKILL.md
    ├── deployment-diagram/SKILL.md
    ├── er-diagram/SKILL.md
    ├── gantt-diagram/SKILL.md
    ├── mindmap-diagram/SKILL.md
    ├── wbs-diagram/SKILL.md
    ├── network-diagram/SKILL.md
    ├── timing-diagram/SKILL.md
    ├── json-yaml/SKILL.md
    └── other-diagrams/SKILL.md
```
