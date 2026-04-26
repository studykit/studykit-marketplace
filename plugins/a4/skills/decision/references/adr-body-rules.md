# ADR Body Rules and Frontmatter Fields

Authoritative guidance for the body and frontmatter of `a4/decision/<id>-<slug>.md` files written by the `decision` skill at Step 5. Read before drafting the file body and frontmatter.

## Body structure rules

- **Required (enforced by `transition_status.py` on `draft → final`):** `## Context`, `## Decision`.
- **Commonly used examples (not prescribed):** `## Options Considered`, `## Rejected Alternatives`, `## Consequences`, `## Open Questions`.
- **Free-form principle:** additional sections may be added when the session content warrants them. All prose must live under a headed section (`##` or `###`); never leave free-form prose outside a section.
- **`## Consequences` is descriptive prose, not a work list.** Describe the resulting state after the decision is applied — how the system, team, or downstream choices are shaped (positive, negative, neutral effects, accepted trade-offs). Do **not** embed `[[task/<id>-<slug>]]` wikilinks; task→decision linkage flows the other direction via `task.justified_by:` (forward, user-input) and is queried derive-on-demand. A reader should understand the decision's downstream impact without opening any task file.
- **No `## Next Steps` or `## Migration Plan` sections.** ADR is a frozen descriptive record, not a project plan. Implications belong in `## Consequences` as prose; executable work belongs in `task/<id>-<slug>.md` (with `task.justified_by: [decision/<this>]` providing the forward link). If the conversation produced procedural detail, mirror it into a task before recording the decision.
- **Decision content, not implementation.** An ADR captures *what* was chosen and *why* — context, options, rationale, trade-offs, consequences. *How* to build it (code samples, function signatures, schema definitions, file layouts, command sequences, step-by-step procedures, sample diffs) belongs in `task/<id>-<slug>.md` or `spike/<task-id>-<slug>/`. If `## Consequences` drifts into a how-to guide, lift it back to implication-level prose or extract the procedural content into a task. A reader should be able to validate the decision without reading any code.

### Implications for non-goals

The two ADR-content rules above translate into hard non-goals for the `decision` skill:

- **Do not write implementation.** If the conversation has been heavy on implementation detail, mirror that content into a task (`/a4:task`) before recording the decision; the ADR body must not contain procedural how-to.
- **Do not render reverse views.** Never write a `## Justifies` body section or a `justifies:` frontmatter field on a decision. Task→decision linkage is captured exclusively as a forward link in `task.justified_by:`; the reverse view is derived on demand (see [`frontmatter-schema.md §Relationships`](../../../references/frontmatter-schema.md)). Do not list downstream tasks in `## Consequences` or anywhere else in the ADR body.

## Frontmatter fields

Authoritative schema: [`frontmatter-schema.md §Decision`](../../../references/frontmatter-schema.md). Field-by-field meaning as used by the `decision` skill:

- `id` — integer from `allocate_id.py`.
- `title` — the title from Step 2.
- `status` — always `draft` at first write; Step 6 flips to `final` if the user signaled commitment.
- `decision` — the one-liner from Step 2.
- `supersedes` — if this replaces prior decisions, list their workspace-root-relative paths (`decision/<id>-<slug>`). Usually empty. Non-empty here triggers the `transition_status.py` cascade on `→ final`, which flips each listed target from `final → superseded`.
- `research` — research artifacts informing this decision (`research/<slug>` paths). Initially empty at first write; populated by `scripts/register_research_citation.py` in Step 5b. Never hand-edit.
- `related` — soft cross-references to other issues inside `a4/` (other decisions, UCs, tasks). For research, use the dedicated `research:` field via the registrar; do **not** use `related:`.
- `tags` — free-form labels.
- `created` / `updated` — today (`YYYY-MM-DD`).
