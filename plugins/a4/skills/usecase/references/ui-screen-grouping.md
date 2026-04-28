# UI Screen Grouping

After UCs are confirmed, group UI-related UCs by screen.

## Procedure

For each screen:

1. Propose a group label (e.g., `screen-dashboard`) and add it to `labels:` in the involved UCs.
2. Record the screen-navigation narrative inside `context.md`'s `<screens>` section (creating the section if absent — it is optional per `references/context-authoring.md`), with markdown links back to the participating UCs.

## Mock generation (optional)

For each confirmed screen group, optionally generate an HTML mock at `a4/mock/<screen-slug>/`:

1. Invoke `Agent(subagent_type: "a4:mock-html-generator")` with UCs in the group, layout requirements, and output path.
2. Present the mock and gather feedback.
3. Refine UCs from mock feedback.

Mocks are suggested, not required.
