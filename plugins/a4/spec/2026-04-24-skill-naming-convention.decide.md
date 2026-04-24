---
type: decide
pipeline: spark
topic: "Skill Naming Convention"
date: 2026-04-24
updated: 2026-04-24
status: final
framework: "3-axis decomposition"
decision: "Plugin renamed from `think` to `a4`. Skill names follow a 3-axis convention (mode / scope / orchestration) with no plugin-name prefix; invocation form is `/a4:<skill>`."
tags: [a4-pipeline, plugin-naming, conventions, skill-naming]
---
# Decision Record: Skill Naming Convention

> Source: design conversation triggered while reviewing the a4-redesign handoff thread — observation that several naming axes had grown without explicit rules.

## Context

The a4-redesign thread (six handoffs from 2026-04-23 through 2026-04-24) landed per-item files, wiki pages, id allocator, drift detector, and `a4/INDEX.md` refresh. Along the way, skill names accumulated several different prefix styles:

- `think-usecase`, `think-arch`, `think-plan` — stuttering invocation `/think:think-*`
- `auto-usecase`, `auto-bootstrap` — mode prefix, no stutter
- `spark-brainstorm`, `spark-decide` — pipeline prefix
- `a4-drift`, `a4-index` — scope prefix
- `handoff`, `compass` — bare names

The existing ADR (`2026-04-23-spec-as-wiki-and-issues.decide.md`) had one rejected-alternatives entry forbidding plugin-name prefix (`think-handoff`), but did not cover the other axes. The actual convention was implicit, not documented.

## Success Criteria

Ranked:

1. **Invocation clarity** — no stutter (`/plugin:plugin-name` patterns).
2. **Semantic legibility** — the prefix (or absence of it) should communicate what class of skill this is.
3. **Extension rule** — future skills should have an obvious name slot without consulting the author.
4. **Consistency across the plugin** — mixed styles make it hard to remember invocation.

## Decision

### Plugin renamed: `think` → `a4`

The plugin's entire reason for existence is managing `a4/` workspaces. Aligning plugin name with workspace name:

- Removes `think-*` stutter (`/think:think-usecase` was redundant).
- Makes `a4-*` scope prefix redundant (the plugin IS `a4`, so `a4-drift` → `drift`).
- Shortens every invocation.
- Plugin namespace in invocation (`/a4:`) is self-describing.

All prior names migrated in the same commit as this ADR. No grandfathering — everything is under the new convention from 1.0.0 onward.

### The 3-axis naming model

Every skill falls into exactly one of three categories. The category determines the prefix form.

| Axis | What it signals | Prefix form | Examples |
|------|-----------------|-------------|----------|
| **Mode** | How the skill interacts with the user | `auto-` for autonomous; **no prefix** (bare) for interactive default | `auto-usecase`, `auto-bootstrap` vs. bare `usecase`, `arch`, `plan` |
| **Scope** | An internal pipeline or subsystem the skill belongs to | `<pipeline>-` | `spark-brainstorm`, `spark-decide` |
| **Orchestration** | Cross-cutting / session-level / workspace-wide — does not fit a single production stage | **No prefix** (bare) | `handoff`, `compass`, `drift`, `index` |

Three rules follow from the table:

1. **No plugin-name prefix, ever.** `/a4:a4-<x>` stutters the same way `/think:think-<x>` did. Reject at PR time.
2. **Interactive mode is the default; autonomous mode is the variant.** Bare name = interactive. `auto-` = autonomous. Other mode prefixes (`guided-`, `chat-`, `live-`) are not adopted.
3. **Pipeline prefix only when the pipeline has multiple stages.** `spark-` is justified because `spark-brainstorm` and `spark-decide` are distinct stages of the same pipeline. A one-skill pipeline does not need a prefix.

### Skill name mapping (1.0.0 migration)

| Old | New | Reason |
|-----|-----|--------|
| `think-usecase` | `usecase` | Interactive = default; drop mode prefix. |
| `think-arch` | `arch` | " |
| `think-plan` | `plan` | " |
| `auto-usecase` | `auto-usecase` | Autonomous = variant; `auto-` prefix retained. |
| `auto-bootstrap` | `auto-bootstrap` | " |
| `spark-brainstorm` | `spark-brainstorm` | Pipeline prefix retained (spark has two stages). |
| `spark-decide` | `spark-decide` | " |
| `a4-drift` | `drift` | Scope = workspace; plugin namespace already carries that. Orchestration bare form. |
| `a4-index` | `index` | " |
| `handoff` | `handoff` | Orchestration; bare already. |
| `compass` | `compass` | " |

### What "orchestration" means

Orchestration skills do not produce new domain content at a single stage. They:

- Coordinate across stages (`compass` routes to the right production skill).
- Manage cross-session / cross-workspace state (`handoff`, `index`).
- Verify workspace integrity (`drift`).

Contrast with production skills (`usecase`, `arch`, `plan`, `auto-*`, `spark-*`) which author or transform artifacts at a specific pipeline stage.

### Invocation form

All skills are invoked as `/a4:<skill>`. No prefix appears twice:

- `/a4:usecase`
- `/a4:auto-usecase`
- `/a4:spark-brainstorm`
- `/a4:drift`
- `/a4:index`
- `/a4:handoff`
- `/a4:compass`

## Rejected Alternatives

| Option | Reason |
|--------|--------|
| Keep `think` plugin name, only rename skills | The stutter source is the plugin name itself. Renaming only skills would force a fresh mode prefix (`guided-`, `live-`, etc.) that adds syllables without solving the root cause. |
| Replace `think-` with a different mode prefix (`guided-usecase`, `live-usecase`) | Adds length and requires a new concept ("guided") that users have to learn. Bare interactive / `auto-` autonomous is the minimal, most direct framing. |
| Keep `a4-` scope prefix on maintenance skills (`a4-drift`, `a4-index`) | The plugin is now `a4`. `a4-` inside the skill slug duplicates what the plugin namespace already provides at invocation time. |
| Drop `spark-` pipeline prefix (bare `brainstorm`, `decide`) | `brainstorm` and `decide` are generic English words; pipeline prefix disambiguates them as spark-pipeline stages. Pipeline prefixes are retained when the pipeline has ≥2 stages. |
| Verb-first naming convention (`write-usecase`, `check-drift`, `refresh-index`) | Attractive but collapses the mode/scope/orchestration axes into a single verb dimension. The 3-axis model is more expressive; verb-first loses the "who's driving" (mode) information. |
| Individual `plugin.json` `name` field kept as `think` while marketplace renames | Inconsistent — users would see two different names depending on which manifest they read. Renamed both `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json`. |
| Version bump to 0.21.0 instead of 1.0.0 | The breaking rename is a natural milestone. Semantic versioning says major-version bumps on breaking changes; 1.0.0 marks the convention lockin. |

## Next Steps

The rename itself is this session's work; no further action items are required for the convention itself. Downstream items that reference the old names:

- [ ] Any new skill added post-1.0.0 must follow this convention. A future PR review can block names that stutter (`a4-<x>`) or use unrecognized mode prefixes.
- [ ] If the plugin ever grows a second pipeline beyond `spark` (e.g., a review or audit pipeline), choose the prefix deliberately — this ADR does not pre-commit to a naming scheme for hypothetical pipelines.

## Discussion Log

<details>
<summary>Conversation summary</summary>

**Trigger.** While reviewing the six a4-redesign handoffs, the author noticed the skill-name prefix system had grown organically: `think-`, `auto-`, `spark-`, `a4-`, and bare names all coexisted. The 2026-04-23 ADR's rejected-alternatives entry addressed only one sliver (plugin-name prefix) and did not document the broader system.

**Mental model.** Discussion surfaced three independent axes: **mode** (interactive vs. autonomous), **scope** (which internal pipeline / subsystem), and **orchestration** (cross-cutting). These are orthogonal — a skill sits in exactly one category but multiple axes can apply in principle. In practice each skill has a dominant category that determines its prefix form.

**`think` → `a4` rename.** The author accepted that the plugin's single purpose is `a4/` management and that renaming the plugin to match the workspace produces cascading simplifications: `think-*` stutter vanishes, `a4-*` scope prefix becomes redundant. The rename is a breaking change; marked as the 1.0.0 migration milestone. Breaking changes to invocation paths in downstream projects are accepted as part of the migration.

**`auto-` retained.** Symmetric rename of `auto-usecase` → `usecase` and `auto-bootstrap` → `bootstrap` was considered but rejected: it collides with the bare-name (interactive) slot, erasing the mode distinction. Bare = interactive default, `auto-` = autonomous variant is the cleanest asymmetric rule.

**Verb-first alternative considered.** `write-usecase` / `check-drift` / `refresh-index` reads naturally but collapses the mode/scope/orchestration axes into one dimension (the verb), losing information about who drives the skill. Rejected as over-simplifying.

**Authoritative outcome.** Record as a follow-up ADR; same folder as `2026-04-23-spec-as-wiki-and-issues.decide.md`. Pre-ADR-layout filename (date-slug, `.decide.md` suffix) matches the precedent of the plugin's own `a4/` — which still uses the legacy layout by design (the plugin's own workspace predates its own redesign).

</details>
