# workflows/ — contributor guardrails

## Audiences

- **This file (`CLAUDE.md`):** plugin contributors editing files in this directory.
- **Other files in this directory (`*.md`):** skill runtimes — files here are cited by `../skills/` and `../agents/` at runtime. They hold **cross-skill workflow contracts** that span multiple skills — modes (interactive vs autonomous), pipeline shapes (Full / Reverse / Minimal), iterate mechanics (review-item walks), wiki-authorship policy (which skill writes which wiki page).

The remainder of this file describes the rules that govern the *other files in this directory*; if you are editing `CLAUDE.md` itself, the contributor-guardrail framing applies to you.

## Citation rules (binding)

- Cite `./` siblings — `./<file>.md` for files in this directory.
- May cite `../authoring/<file>.md` when forwarding to the frontmatter / body contract.
- **Never** cite `../scripts/` or `../dev/`. Skill runtime must not pull plugin internals into end-user task contexts.

## When to add a file here

- A new orchestration concern that affects **two or more** skills. Examples: a new pipeline shape, a new cross-stage feedback policy, a new shared-state convention.

## When NOT to add content here

- A single skill's stage-specific procedure → `../skills/<name>/references/`.
- Frontmatter / body contract (binding for workspace authors) → `../authoring/`.
- Plugin internals (hook flow, cascade engine, validator modules) → `../dev/`.

## Tone

Workflow contracts describe *choices that span multiple skills* and the rationale. Use prescriptive voice when the rule is binding ("the writer for `architecture.md` is `/a4:arch`") and explanatory voice for rationale ("because the upstream wiki must precede dependent stages").

The full audience routing and plugin directory layout lives in `../CLAUDE.md`.
