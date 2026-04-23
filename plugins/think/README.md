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

## Document Layout (`a4/`)

All think-pipeline artifacts live under `a4/` (lowercase) at the workspace root. The layout follows a few conventions:

### Pipeline stage files (flat, topic-keyed)

```
a4/<topic-slug>.usecase.md       # think-usecase / auto-usecase
a4/<topic-slug>.arch.md          # think-arch
a4/<topic-slug>.bootstrap.md     # auto-bootstrap
a4/<topic-slug>.plan.md          # think-plan
a4/<topic-slug>.spec.md          # (spec-producing flows)
```

Each stage file owns frontmatter with `topic`, `revision`, `status`, `revised`, and `reflected_files`. The `reflected_files` list is the canonical record of which derivative reports (reviews, research, explorations, test reports) have already been incorporated — so a stage file plus the glob of `a4/<topic>.*.md` is sufficient to compute "what is pending" without reading derivative bodies.

### Spark sessions (session-scoped)

```
a4/spark/<YYYY-MM-DD-HHmm>-<slug>.brainstorm.md
a4/spark/<YYYY-MM-DD-HHmm>-<slug>.decide.md
```

Spark and pipeline are **parallel tools**, not a funnel. Spark files may opt in to a lightweight lifecycle via optional frontmatter:

- `status: open | promoted | discarded` (default: `open`)
- `graduated_to: <topic-slug>` (when promoted to a pipeline topic)
- `discarded_reason: <short reason>` (when discarded)

A pipeline `usecase.md` can optionally record its spark origin with `origin: spark/<filename>`. These fields are **read when present, never required** — skill flows do not fail if they are absent.

### Archive

```
a4/archive/<topic>.<stage>.md
```

A topic is archived simply by moving all of its files into `a4/archive/` (via `git mv`). There is no `archived:` frontmatter field — folder location is the flag. Compass offers to perform the move when a topic reaches `status: complete` or `status: final`; the move itself is always user-confirmed.

### Workspace dashboard

```
a4/INDEX.md
```

Regenerated on every `compass` invocation from stage-file frontmatter and directory globs. The table uses a five-state icon vocabulary — `✗` blocked, `!` unreflected derivatives, `⟳` in progress, `✓` complete, `—` absent — with priority `✗ > ! > ⟳ > ✓ > —`. INDEX is a **view** (source of truth = stage files), so regenerating it is always safe. It is committed to git by whichever session-closing runs next; compass does not auto-commit it.

INDEX answers "which topic needs attention?" The per-topic narrative ("what should I do next?") stays in compass's on-demand diagnosis (Step 3) — INDEX deliberately has no "next action" column to avoid duplicating that role.
