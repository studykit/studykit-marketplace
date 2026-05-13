# Workflow Knowledge Wiki

This directory is the GitHub-backed knowledge backend for the workflow plugin dogfooding effort.

It intentionally uses a normal repository directory instead of the separate GitHub Wiki feature.

Runtime authoring contracts remain under [`plugins/workflow/authoring/`](../../plugins/workflow/authoring/). Wiki pages may link to those contracts, but should not duplicate their full rule bodies.

## Pages

- [Workflow Provider Model](workflow-provider-model.md)
- [Workflow Issue Relationship Policy](workflow-issue-relationship-policy.md)
- [Workflow Provider Reference Formats](workflow-provider-reference-formats.md)
- [GitHub Issue History Access](github-issue-history-access.md)
- [GitHub Issues Usage For Workflow](github-issues-usage-for-workflow.md)
- [Workflow Authoring Enforcement](workflow-authoring-enforcement.md)
- [Workflow Clean Break Decision](workflow-clean-break-decision.md)
- [Workflow Configuration](workflow-configuration.md)

## Tracking

- [Workflow plugin MVP issue](https://github.com/studykit/studykit-plugins/issues/28)
- [GitHub issue history research](https://github.com/studykit/studykit-plugins/issues/37)

## Change Log

- 2026-05-13 — [#28](https://github.com/studykit/studykit-plugins/issues/28) — Created repository `wiki/workflow/` directory as the GitHub knowledge backend for the workflow plugin.
- 2026-05-13 — [#29](https://github.com/studykit/studykit-plugins/issues/29) — Added the workflow configuration schema page.
