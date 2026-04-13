# think

Co-thinking plugin — usecase/spec/implementation-plan design, autonomous code execution, brainstorming, decision-making, and GitHub automation.

## Prerequisites

The `find-docs` skill must be installed. Set it up via [ctx7 CLI](https://context7.com/docs/clients/cli):

```bash
ctx7 setup --cli --claude       # Claude Code (~/.claude/skills)
```

The shared `get-api-docs` skill must also be available in the global skills set. Think agents use this shared skill for current third-party API and SDK documentation lookup.

## Components

### Skills

| Name | Purpose |
|------|---------|
| `think-usecase` | Collaborative usecase specification design |
| `think-arch` | Architecture design and review |
| `think-plan` | Implementation plan creation and review |
| `auto-bootstrap` | Autonomous project bootstrap with research |
| `auto-usecase` | Autonomous usecase generation |
| `spark-brainstorm` | Structured brainstorming sessions |
| `spark-decide` | Decision-making with ADR output |
| `compass` | Project direction and next-step guidance |
| `web-design-mock` | Web design mock generation |
| `get-api-docs` | Shared global skill for current API/SDK documentation lookup |

### Agents

| Name | Purpose |
|------|---------|
| `api-researcher` | Find and return current API documentation |
| `arch-reviewer` | Review architecture designs |
| `decision-reviewer` | Review decision records |
| `domain-updater` | Update domain models |
| `iu-implementer` | Implement IUs and write unit tests |
| `mock-html-generator` | Generate HTML mockups |
| `plan-reviewer` | Review implementation plans |
| `test-runner` | Run tests and produce reports |
| `usecase-composer` | Compose usecase specifications |
| `usecase-explorer` | Explore and discover usecases |
| `usecase-reviewer` | Review usecase specifications |
| `usecase-reviser` | Revise usecases based on feedback |
