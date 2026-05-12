# a4 — ci wiki authoring

`a4/ci.md` is the workspace's reference for **how the LLM (or a human) verifies any feature change**: which test commands to run, where tests live, how tier isolation is configured. Anything implementing or modifying behavior reads this file as the test-execution contract.

There is exactly one ci page per workspace: `a4/ci.md`. No per-topic / per-slug variant.

Frontmatter contract: `./frontmatter-wiki.md`. Body conventions: `./wiki-body.md` (`## Change Logs`, Wiki Update Protocol).

## Body shape

**Required:**

- `## How to run tests` — the per-tier executable contract. The verified literal commands that exited 0 during setup. Each row covers one tier (unit / integration / E2E). May include a `### Multi-tier run` subsection capturing the single command (or short script) that exercises every in-scope tier — the smoke check used after implementation.
- `## Test layout` — where tests live and how they are organized: per-tier path, naming convention, runner config file. Lets the LLM put new tests in the right place without guessing.

**Optional H2:**

- `## Smoke scenario` — a single minimal user-observable interaction the running app produces. Used as the post-implementation smoke check.
- `## Issues` — links to `./review-authoring.md` review items emitted during the setup run that produced this page, grouped by classification (architecture / environment) and status (open / resolved). Omit when no review items were emitted.
- `## Change Logs` — append-only audit trail (dated bullets with backlinks to the causing review item or architecture spec). Format: `./wiki-body.md`.

Free-form additional H2 sections are tolerated.

### Canonical H3 subsections

When partitioning a section into named subsections (rather than free-form prose / a single table), use these canonical H3 names:

- Under `## How to run tests`: `### Multi-tier run`, `### Test isolation flags`.

Unknown H2 / H3 headings are tolerated.

### Why `## How to run tests` lives only here

`## How to run tests` is the single executable contract that drives implementation verification. Duplicating it into `architecture.md` (Test Strategy) would create drift. Architecture's `## Test Strategy` describes the **strategy** (which tiers, what isolation philosophy, what the framework family is); ci's `## How to run tests` records the **executable contract** (the actual commands that exited 0). The two are complementary.

## Change Log triggers

Most bullets that land here cite either a `target: architecture` review item that triggered a test-contract refresh, or a test-strategy adjustment (new tier, new runner, isolation change).

## Common mistakes (ci-specific)

- **Required section missing** (`## How to run tests`, `## Test layout`).
- **Recording unverified commands.** ci.md records what exited 0 during ci-setup. Speculative commands belong in research, not here.
- **Per-task content leaking in.** Per-task verification belongs in the task's `## Unit Test Strategy`, not in ci.md.

## Don't

- **Don't write commands that have not been verified.** ci.md records what *succeeded*; speculative commands belong in a spec or research artifact.
- **Don't duplicate `## How to run tests` content into `architecture.md`.** It references, it does not duplicate.
- **Don't write architecture rationale here.** The why behind the test strategy lives in `architecture.md` and the spec(s) that shaped it.
- **Don't write task-level information here.** Per-task verification belongs in the task's body.
- **Don't append `## Change Logs` bullets without a backlink path.**
