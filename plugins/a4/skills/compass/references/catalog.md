# Skill Catalog (compass routing)

Reference table presented to the user in Step 2.1 (Fresh Start) when they answer "What are you trying to do?". Group order matches the typical decision flow: Ideation (pre-pipeline) → Pipeline (interactive) → Pipeline (autonomous) → Standalone.

After the user picks one, invoke via the Skill tool:

```
Skill({ skill: "a4:<skill-name>", args: "<user's topic or file path>" })
```

## Ideation

| Skill | What it does |
|-------|-------------|
| `spark-brainstorm` | Generate ideas with structured creative techniques |
| `research` | Investigate options or a topic; produces an investigation task at `a4/research/<id>-<slug>.md` whose body holds sources, findings, and (in comparative mode) per-option subsections |
| `research-review` | Review a research task at `a4/research/<id>-<slug>.md` for source quality, option balance, bias, and neutrality |
| `spec` | Record a spec reached through conversation as `a4/spec/<id>-<slug>.md`, soft-link related research tasks, nudge affected wiki pages |

## Pipeline (interactive)

| Skill | What it does |
|-------|-------------|
| `usecase` | Shape a vague idea into concrete Use Cases through dialogue (writes `context.md`, `actors.md`, `nfr.md`, per-UC files) |
| `domain` | Extract cross-cutting concepts, relationships, and state transitions into `domain.md` |
| `arch` | Design architecture — tech stack, components, interfaces, test strategy |
| `roadmap` | Author the implementation roadmap and per-task files |
| `task` / `bug` / `spike` / `research` | Author a single task in the matching family — UC-derived or spec-justified |
| `discard` | Discard a task across any family by id / path / slug fragment |
| `run` | Run the agent loop — implement and test until all pass |

## Pipeline (autonomous)

| Skill | What it does |
|-------|-------------|
| `auto-usecase` | Reverse-engineer or batch-shape UCs from a codebase, idea, or brainstorm input (no interview) |
| `auto-bootstrap` | Set up project structure, dependencies, build, and test infrastructure |

Mode rationale (why some stages have only an interactive or only an autonomous form, and why `auto-usecase` is not a twin of `usecase`): see [`skill-modes.md`](${CLAUDE_PLUGIN_ROOT}/dev/skill-modes.md).

## Standalone

| Skill | What it does |
|-------|-------------|
| `web-design-mock` | Create HTML/CSS mockups and prototypes |
