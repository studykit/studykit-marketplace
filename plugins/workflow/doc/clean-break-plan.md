# Workflow Plugin Clean Break Plan

Date: 2026-05-13

## Decision

Create a new `plugins/workflow` plugin instead of turning `plugins/a4` into a remote-native provider workflow system.

`plugins/a4` should remain the existing local Markdown workflow plugin. `plugins/workflow` should be a clean-break implementation for provider-backed workflow over GitHub, Jira, GitHub Wiki, and Confluence.

## Rationale

The current `plugins/a4` design is deeply local-file oriented:

- Local `a4/` Markdown files are the source of truth.
- Local paths determine artifact type and authoring contracts.
- Local id allocation, validation, and hook behavior assume filesystem-backed artifacts.

The new direction is materially different:

- Issue and knowledge providers are separate.
- GitHub or Jira can be the issue source of truth.
- GitHub Wiki or Confluence can be the knowledge source of truth.
- Local files are optional projections, not required canonical state.
- Authoring is resolved by artifact type, role, and provider, not by local path.

Keeping this inside `plugins/a4` would require broad compatibility shims and would risk breaking the stable local Markdown workflow. A new plugin allows the provider-native model to be designed directly.

## Boundary

### `plugins/a4`

Keep as-is for the local Markdown workflow:

- `a4/` filesystem source of truth.
- Local issue and wiki Markdown files.
- Local ids.
- Local validators and status cascades.
- Existing skills and hooks.

### `plugins/workflow`

New provider-backed workflow plugin:

- `workflow.config.yml` at repository root.
- Issue provider: GitHub Issues or Jira.
- Knowledge provider: GitHub Wiki or Confluence.
- Native provider references in body text.
- Provider wrapper commands for reads and writes.
- Native transports first, MCP fallback.
- Authoring resolver with absolute plugin-bundled authoring file paths.
- Session read ledger for authoring files.
- `workdoc-finder` read-only remote provider search agent.

## Carry Forward from a4

Bring over only the parts that remain useful.

### Authoring concepts

Copy and adapt selected authoring documents from `plugins/a4/authoring/`:

- `task-authoring.md`
- `bug-authoring.md`
- `spike-authoring.md`
- `review-authoring.md`
- `epic-authoring.md`
- `spec-authoring.md`
- `usecase-authoring.md`
- `research-authoring.md`
- `architecture-authoring.md`
- `domain-authoring.md`
- `context-authoring.md`
- `actors-authoring.md`
- `nfr-authoring.md`
- `ci-authoring.md`
- `body-conventions.md`

These files must be revised for workflow provider semantics. Do not blindly preserve local-only assumptions such as local integer ids, path-based frontmatter references, or local `a4/` file locations.

### Workflow concepts

Carry forward these concepts:

- Issue-backed work items.
- Knowledge-backed curated documents.
- Review items as feedback workflow artifacts.
- Change logs on knowledge documents.
- Usecase and research as dual artifacts.
- Relationship fields such as `target`, `implements`, `related`, and `supersedes`.

### Agent concepts

Create a new `workdoc-finder` agent rather than reusing `workspace-assistant`.

- `workspace-assistant` remains for local `a4/` filesystem search.
- `workdoc-finder` searches configured remote providers.
- `api-researcher` stays unchanged and remains for external API/SDK documentation research.

### Hook concepts

Carry forward the idea of lightweight SessionStart policy injection, but not the full a4 hook implementation.

New workflow hooks should focus on:

- Detecting `workflow.config.yml`.
- Injecting the authoring resolver policy only in configured projects.
- Recording authoring file reads in a session ledger.
- Guarding writes until required authoring files have been read.

## Do Not Carry Forward Directly

The new plugin should not directly inherit these a4-local mechanisms:

- Local global integer id allocation.
- Path-based authoring resolution.
- Local Markdown frontmatter as canonical storage.
- Local status cascade implementation.
- Local validator assumptions tied to `a4/**/*.md`.
- SessionStart location maps such as `a4/task/<id>-<slug>.md`.

Similar capabilities may be rebuilt later against provider-native metadata and APIs.

## Naming

Use workflow terminology in the new plugin:

- Config file: `workflow.config.yml`.
- Plugin path: `plugins/workflow`.
- Provider wrapper: workflow provider wrapper.
- Artifact: workflow artifact.
- Authoring resolver: workflow authoring resolver.

Avoid naming new remote-native pieces `a4.*` unless compatibility with the old local plugin is intentional.

## Initial Work Order

1. Keep documenting the design under root `doc/`.
2. Create `plugins/workflow` only after the main decisions are captured.
3. Scaffold plugin metadata.
4. Copy selected authoring documents from `plugins/a4/authoring/`.
5. Rewrite copied authoring documents for provider-backed semantics.
6. Add provider-specific authoring contracts.
7. Add `workflow.config.yml` schema documentation.
8. Add authoring resolver skeleton.
9. Add provider wrapper skeleton.
10. Add `workdoc-finder` agent.
11. Add SessionStart/read-ledger/write-guard hook skeletons.

## Design Decisions to Preserve

The clean-break plugin should preserve these decisions from the provider abstraction discussion:

1. Mixed providers are preferred over a single global backend.
2. Issue and knowledge providers are separate abstractions.
3. Local files are optional projections in provider-backed mode.
4. Provider-native identities replace local a4 ids.
5. Frontmatter becomes a normalized view, not canonical storage.
6. `spec` belongs in the knowledge backend.
7. `review` is always issue-backed.
8. `review.target` should be metadata when possible and always present in body text.
9. `usecase` and `research` are issue-first dual artifacts.
10. Knowledge pages contain curated content only.
11. Knowledge pages include concise change logs linking to causing workflow artifacts.
12. Authoring contracts are plugin-bundled Markdown files.
13. The resolver returns absolute authoring file paths.
14. The session read ledger records which authoring files were read.
15. Skills are explicit commands and should not auto-trigger.
16. Native transports are primary; MCP is fallback.
17. `workdoc-finder` is the remote provider search agent.

## Open Questions

1. Which authoring files should be copied first for the minimum viable workflow plugin?
2. How much of the a4 lifecycle model should be retained for provider-backed status mapping?
3. What should the first `workflow.config.yml` schema support?
4. Should GitHub and Jira support ship together, or should one issue provider come first?
5. Should Confluence be the first knowledge provider, with GitHub Wiki added later?
6. How should legacy a4 projects migrate, if at all?

