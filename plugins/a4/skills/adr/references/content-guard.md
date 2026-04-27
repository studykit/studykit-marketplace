# ADR content guard — examples and false-positive carve-outs

Reference for the `adr-content-guard` agent. The descriptive-not-prescriptive rule lives in [`references/frontmatter-schema.md §ADR`](../../../references/frontmatter-schema.md). This file gives concrete leakage vs. clean prose so the guard does not over- or under-flag.

The rule, restated: an ADR body captures *what* was chosen and *why*. *How* to execute the choice lives in `task/<id>-<slug>.md` files linked via `task.adr:`. The reverse view of `task.adr:` is derived on demand and never written into the ADR body.

## Section-by-section policy

| Section | Policy |
|---------|--------|
| `## Context` | **Exempt.** Constraints, environment, history, prior art are *required*. Concrete tech names and even file paths are fine when they document the situation that prompted the decision. |
| `## Decision` | **Strict.** What was chosen, in one or two paragraphs of prose. Naming the chosen technology is fine; configuring or operating it is a leak. |
| `## Options Considered` | **Strict.** Each option characterized — strengths, limits, fit. Not a work plan. |
| `## Rejected Alternatives` | **Strict.** Why each was set aside. Not a "would have required steps X, Y, Z" sequence. |
| `## Consequences` | **Strict.** Pure prose; no `[[task/...]]` wikilinks; no imperative verbs. |
| `## Open Questions` | **Strict.** Each question is a question, not a deferred TODO. |
| `## Research` | **Auto-managed.** Never flag. |
| `## Cited By` | **Auto-managed.** Never flag. |
| `## Log` | **Auto-managed.** Never flag. |
| `<details>...</details>` | **Exempt.** Raw excerpts preserved verbatim. |
| Forbidden sections | **Block.** `## Next Steps`, `## Migration Plan`, `## Action Items`, `## TODO`, `## Implementation Plan`, `## Tasks` — flag the heading itself. |

## Worked examples — `## Decision`

**Leak — prescriptive verb + implementation detail.**

```markdown
## Decision

We will adopt Postgres 16 as the primary store. Install PgBouncer in
transaction pooling mode in front of every service. Set `max_connections`
to 200 and run the schema migration with `psql -f migrations/0042.sql`.
```

The first sentence is the decision. The rest is implementation work disguised as decision content — when the operator picks a different pooler or sets a different `max_connections`, the ADR rots.

**Clean.**

```markdown
## Decision

Adopt Postgres 16 as the primary store. Connection pooling is in scope
because the projected workload exceeds Postgres' native connection ceiling
(see [[research/8-store-options]]); the pooling tool and configuration are
deferred to implementation.
```

The decision and its rationale are explicit. The pooling commitment is captured ("in scope") without prescribing the tool. Implementation is acknowledged as belonging elsewhere.

## Worked examples — `## Options Considered`

**Leak — option-as-task.**

```markdown
### Option B — MySQL 8

1. Provision MySQL 8 on RDS.
2. Run `mysqldump` from the legacy database.
3. Configure read replicas in two AZs.
4. Cut over reads after 48h of monitoring.
```

This is a runbook, not an option. It says nothing about why MySQL 8 is or is not the right choice.

**Clean.**

```markdown
### Option B — MySQL 8

Mature replication tooling and operator familiarity are strengths. JSON
indexing capabilities lag Postgres for our query shape (see
[[research/8-store-options]]). Read-replica topology fits the AZ layout
without architectural change.
```

Each sentence characterizes the option. A reader weighing this against Option A understands the trade-offs without re-doing the work.

## Worked examples — `## Consequences`

**Leak — task wikilink + prescriptive verb.**

```markdown
## Consequences

Connection pool sizing must be tuned per service. Schema migrations need
to run before the cutover. See [[task/87-add-pgbouncer-config]] and
[[task/88-cutover-runbook]].
```

Two leaks. The wikilinks render the reverse view of `task.adr:` into the body — that view is derived on demand. The "must be tuned" / "need to run" verbs prescribe action.

**Clean.**

```markdown
## Consequences

Service-level connection-pool tuning becomes a recurring concern; service
owners take ownership at deploy time. Schema migration is sequenced ahead
of cutover, with the schema-shape commitment owned by the data team. The
existing in-process connection cache becomes redundant and is removed
under the same change.
```

The same content, re-cast as state-of-the-world after the decision lands. Tasks the consequences imply are tracked separately and surface via the derived reverse of `task.adr:`, not via hand-written wikilinks.

## Worked examples — `## Context` (the exempt section)

**Allowed — concrete tech and file references in Context.**

```markdown
## Context

The current store is SQLite on the application host (`./data/app.db`).
Read traffic has grown 6× year-over-year; write contention surfaces in
the `sessions` table during peak hours. The team has Postgres operational
experience from the platform tier; MySQL is unfamiliar.
```

`./data/app.db`, `sessions`, "Postgres", "MySQL" all appear here without triggering the guard. Context describes the situation that prompted the decision; concrete naming is correct here.

## Allowed wikilinks vs. flagged wikilinks

| Wikilink | In `## Decision` | In `## Consequences` | In `## Context` |
|----------|------------------|----------------------|------------------|
| `[[research/<slug>]]` | OK | OK | OK |
| `[[adr/<id>-<slug>]]` | OK | OK | OK |
| `[[usecase/<id>-<slug>]]` | OK | OK | OK |
| `[[architecture#section]]` | OK | OK | OK |
| `[[task/<id>-<slug>]]` | OK | **FLAG** | OK |

Only one wikilink shape is forbidden, and only inside `## Consequences`: task wikilinks. Every other reference shape — research, prior ADRs, UCs, architecture sections — is a legitimate cross-reference.

## When in doubt

The guard's job is to catch leaks the user did not notice. It is **not** the guard's job to enforce a house style. If a phrase is borderline (e.g., "the implementation team will need to consider connection-pool sizing"), prefer not to flag — the user retains override and a noisy guard erodes signal.

The clearest leak signals, in order of severity:

1. **Forbidden section heading** — heading itself is the leak; the prose underneath is irrelevant.
2. **Prescriptive verb in `## Decision`** — "we will install", "the team will configure", "next step is".
3. **`[[task/...]]` in `## Consequences`** — explicit reverse-view pollution.
4. **Implementation detail** (function names, file paths, CLI commands) **outside `## Context`**.
5. **Option-as-task framing** in `## Options Considered` or `## Rejected Alternatives`.

A clean ADR file rarely fails any of these. A file failing two or more is almost certainly leaking implementation thinking that belongs in `task/`.
