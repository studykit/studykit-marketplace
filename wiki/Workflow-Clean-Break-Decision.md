# Workflow Clean Break Decision

Source document: [`plugins/workflow/doc/clean-break-plan.md`](../plugins/workflow/doc/clean-break-plan.md)

## Decision

Create a new `plugins/workflow` plugin instead of turning `plugins/a4` into a remote-native provider workflow system.

`plugins/a4` remains the existing local Markdown workflow plugin. `plugins/workflow` is the clean-break implementation for provider-backed workflow over GitHub, Jira, repository `wiki/` directories, and Confluence.

## Rationale

The legacy `plugins/a4` design is local-file oriented:

- Local Markdown files are the source of truth.
- Local paths determine artifact type and authoring contracts.
- Local integer ids and validators assume filesystem-backed artifacts.

The workflow direction is materially different:

- Issue and knowledge providers are separate.
- GitHub or Jira can be the issue source of truth.
- Repository `wiki/` directories or Confluence can be the knowledge source of truth.
- Local files are optional projections, not required canonical state.
- Authoring is resolved by artifact type, role, and provider, not by local path.

Keeping both models in `plugins/a4` would require broad compatibility shims and would risk breaking the stable local Markdown workflow.

## Boundary

### `plugins/a4`

Use for the local Markdown workflow.

### `plugins/workflow`

Use for provider-backed workflow:

- `workflow.config.yml` at repository root.
- Issue provider: GitHub Issues or Jira.
- Knowledge provider: repository `wiki/` directory or Confluence.
- Provider-native references in body text.
- Native transports first, MCP fallback.
- Authoring resolver with absolute plugin-bundled authoring file paths.
- Session read ledger and write guard.
- `workdoc-finder` as remote provider search agent.

## Design Decisions

1. Mixed providers are preferred over a single global backend.
2. Issue and knowledge providers are separate abstractions.
3. Local files are optional projections in provider-backed mode.
4. Provider-native identities replace local workflow ids.
5. Frontmatter becomes a normalized view, not canonical storage.
6. `spec` belongs in the knowledge backend.
7. `review` is always issue-backed.
8. `review.target` should be metadata when possible and always visible in the body.
9. `usecase` and `research` are issue-first dual artifacts.
10. Knowledge pages contain curated content only.
11. Knowledge pages include concise change logs linking to causing workflow artifacts.
12. Authoring contracts are plugin-bundled Markdown files.
13. The resolver returns absolute authoring file paths.
14. The session read ledger records which authoring files were read.
15. Skills are explicit commands and should not auto-trigger.
16. Native transports are primary; MCP is fallback.
17. `workdoc-finder` is the remote provider search agent.
18. GitHub workflow type uses plain artifact-type labels by default.
19. Provider-native relationships and ordering should not be duplicated in body sections.
20. GitHub knowledge backend uses the main repository `wiki/` directory, not the separate GitHub Wiki feature.

## Tracking

Implementation is tracked by [#28](https://github.com/studykit/studykit-plugins/issues/28) and its sub-issues.

## Change Log

- 2026-05-13 — [#28](https://github.com/studykit/studykit-plugins/issues/28) — Published clean-break decision in repository `wiki/` directory.
