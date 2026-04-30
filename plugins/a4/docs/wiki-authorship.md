# Wiki Authorship & Cross-Stage Feedback Policy

Single source of truth for **who can write to each wiki page in `a4/`** and **what a stage should do when it discovers a problem in another stage's wiki page**. Every a4 skill's behavior with respect to a wiki page must conform to this document; if a SKILL.md disagrees, this document wins and the SKILL.md is updated to match.

Companion to [`frontmatter-schema.md`](./frontmatter-schema.md) (field-level rules), [`body-conventions.md`](./body-conventions.md) (heading form, `## Change Logs` / `## Log` rules, link form), [`skill-modes.md`](./skill-modes.md) (interactive vs autonomous, forward vs reverse — why some stages have only one mode), and [`pipeline-shapes.md`](./pipeline-shapes.md) (Full / Reverse / Minimal pipeline shapes — which stages run in which shape).

## Wiki page authorship

Each wiki page has exactly one **primary author skill**. Other skills may edit the page only under the limited in-situ rules in the table below; everything outside those rules flows through review items.

| Wiki page | Primary author | In-situ edit allowed (skill: change kinds) | Out-of-rule changes |
|---|---|---|---|
| `context.md` | `usecase` | `usecase`: any | review item, `target: [context]` |
| `actors.md` | `usecase` | `usecase`: any. `arch`: add a `system` actor that surfaces during component design (privilege/description text only); never modify a `person` actor | review item, `target: [actors]` |
| `domain.md` | `domain` | `arch`: simple changes only — see [`skills/arch/SKILL.md`](../skills/arch/SKILL.md) Phase 3 b3 decision table (add concept, 1:1 rename, definition wording). Structural changes (split / merge / relationship / state) → review item | review item, `target: [domain]` |
| `nfr.md` | `usecase` | `usecase`: any. `arch`: append a footnote pointing to the arch decision that *responds* to an existing NFR row (no new NFR rows, no NFR text edits) | review item, `target: [nfr]` |
| `architecture.md` | `arch` | `arch`: any. **No other skill edits in-situ.** | review item, `target: [architecture]` |
| `bootstrap.md` | `auto-bootstrap` | `auto-bootstrap` only (re-runs archive prior copy). **Single source of truth for Launch & Verify** — the `## Verify` section (verified commands, smoke scenario, test isolation flags) is read directly by `/a4:run`, `task-implementer`, and `test-runner`; never duplicated into other wikis | review item, `target: [bootstrap]` (rare — most bootstrap issues become arch issues that bootstrap re-runs cover) |
| `roadmap.md` | `roadmap` | `roadmap`: milestone narrative, dependency graph, Shared Integration Points (all inside `## Plan`). **Must not author Launch & Verify content** — that section is a one-line link pointer to `bootstrap.md` | review item, `target: [roadmap]` |

### Why architecture is more restrictive than domain

`domain.md` is downstream of UCs and upstream of arch. Term churn is normal — concept rename happens often during arch work, and forcing every rename through a review item is too much friction. Hence the b3 split (simple inline / structural deferred).

`architecture.md` is the **most depended-on wiki**: `bootstrap`, `roadmap`, every task across the four issue family folders (`task/`, `bug/`, `spike/`, `research/`), and `run` all read it directly. Allowing in-situ edits from other stages would let contract drift propagate before review. Architecture changes therefore stay single-author; the cost of a review-item round trip is justified by the size of the dependent surface.

### Why bootstrap, roadmap have a single in-situ owner

Both are near-terminal wikis (bootstrap drives roadmap; roadmap drives run). They are not normally edited by other interactive skills — instead they are *re-derived* (re-run `auto-bootstrap`, re-run `roadmap iterate`) when their inputs change. The in-situ owner is the only relevant editor.

## Cross-stage feedback policy

When a stage discovers a problem in another stage's primary wiki page, it must decide between two responses: **stop** (halt this stage's work and surface the dependency) or **continue** (finish this stage's work, leaving a review item for the upstream stage).

### Decision rule

The choice is determined by **whether this stage's output is valid before the upstream issue is fixed**:

- **Strong dependency** — this stage's result depends directly on the upstream wiki being correct. Continuing produces output that will be invalidated by the upstream fix. → **stop**.
- **Weak dependency** — this stage's result is independently meaningful. The upstream fix may suggest a re-run, but the current output is still useful. → **continue + review item**.

### Stage-by-stage policy

| Stage | Upstream of concern | Strength | Policy |
|---|---|---|---|
| `roadmap` | `architecture.md`, `usecase/*.md` | strong (component → task split, UC → AC source) | **stop**, recommend `/a4:arch iterate` or `/a4:usecase iterate` |
| `roadmap-reviewer` | `architecture.md`, `usecase/*.md` | strong | emit review item targeting upstream; `roadmap` Step 4 stops |
| `run` Step 4 | `architecture.md`, `usecase/*.md` | strong (task contract / AC source) | **stop**, recommend `/a4:arch iterate` or `/a4:usecase iterate` |
| `auto-bootstrap` | `architecture.md` | weak (verified env is valid as recorded; arch fix triggers re-bootstrap, not invalidation) | **continue + review item**, `target: [architecture]` |
| `usecase iterate` | `architecture.md`, `domain.md` | weak (UC text is independent of arch / domain) | **continue + review item** |
| `domain` (`/a4:domain`) | `architecture.md` | weak (concept extraction is independent; arch references domain, not the reverse) | **continue + review item** |
| `auto-usecase` | `architecture.md`, `domain.md` | weak (drafts UCs from input; downstream stages handle alignment) | **continue + review item** |
| `arch iterate` | `usecase/*.md`, `domain.md` | weak (arch reads UC/domain; if they change mid-arch, walk new review items separately) | **continue + review item** |

### How an arch fix flows back downstream

When `/a4:arch iterate` resolves a review whose `target:` lists `architecture`:

1. `architecture.md` is edited; the resolved review item's `status:` and `updated:` are flipped by `transition_status.py` (the writer does not touch `## Log` — that section is optional and hand-maintained); a new bullet in `architecture.md`'s `## Change Logs` cites the resolved item.
2. The wiki close guard (per `body-conventions.md`) ensures the change-log bullet is well-formed.
3. **Downstream staleness propagation** — when present, the drift detector emits new `kind: gap` review items targeting the downstream wikis (`bootstrap`, `roadmap`, related `task/*/*.md`) whose `updated:` predates the new architecture change-log entry. *(This propagation rule is currently a planned addition; see the open follow-up under "Pipeline restructure backlog".)*
4. `compass` Layer 2 / Layer 3 routes the user to the correct downstream `iterate` skill based on the new review-item targets.

Until staleness propagation lands, the user remains responsible for re-running `/a4:auto-bootstrap`, `/a4:roadmap iterate`, or `/a4:run iterate` after a substantial architecture fix. SKILL.md wrap-ups recommend the right next step.

### Examples

**Example 1 — `auto-bootstrap` finds an arch issue (continue).**
```
1. auto-bootstrap Step 4: build command fails because the chosen
   framework version is incompatible with the chosen runtime.
2. Diagnose: this is an architecture choice, not an environment issue.
3. Emit: a4/review/<id>-arch-version-incompatibility.md
   target: [architecture],
   priority: high, source: auto-bootstrap
4. Continue: write a4/bootstrap.md with the partial verification
   results (Build: FAIL, others: skipped or PASS where independent).
5. Wrap-up message: "Architecture issues were flagged — run
   /a4:arch iterate first, then re-run /a4:auto-bootstrap."
```

**Example 2 — `roadmap` finds an arch issue (stop).**
```
1. roadmap Step 4: roadmap-reviewer reports that the SessionService
   contract has no error-response shape, so task AC for UC-3 is
   ambiguous.
2. Emit: a4/review/<id>-arch-missing-error-shape.md
   target: [architecture],
   priority: high, source: roadmap-reviewer
3. Stop. Do NOT commit a partial roadmap.md.
4. Wrap-up message: "Roadmap halted — architecture has an open
   issue. Run /a4:arch iterate; resume /a4:roadmap iterate after."
```

**Example 3 — `domain iterate` notices a concept rename affecting arch component name (continue).**
```
1. /a4:domain Phase 1 confirms a rename: "Conversation" -> "Session".
2. domain.md is updated (in-situ, this skill's primary wiki).
3. Notice: a4/architecture.md uses "ConversationService" — out of sync.
4. Emit: a4/review/<id>-arch-rename-cascade.md
   target: [architecture, domain],
   priority: medium, source: self
5. Continue domain wrap-up. The architecture rename will be picked
   up at /a4:arch iterate (compass Layer 3 routes the user).
```

## Compliance

The cross-area-consistency check does not yet enforce authorship rules. Until it does, conformance is the responsibility of:

- SKILL.md authors — wrap-up steps explicitly cite this document.
- Reviewer agents — `arch-reviewer`, `domain-reviewer`, `usecase-reviewer` flag clear violations as findings (e.g., `architecture.md` edited by something other than arch, `domain.md` structural edit bypassing review item).
- The drift detector — surfaces stale `## Change Logs` links and close-guard violations.

When this document is updated, the changelog of every dependent SKILL.md should be checked for inline copies that drifted.
