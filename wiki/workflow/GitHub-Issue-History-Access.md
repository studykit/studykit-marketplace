# GitHub Issue History Access

Source document: [`plugins/workflow/doc/github-issue-history.md`](../../plugins/workflow/doc/github-issue-history.md)

Date: 2026-05-13

## Purpose

Research issue: [#37](https://github.com/studykit/studykit-plugins/issues/37)

Record how workflow can read GitHub Issue history when GitHub Issues are used as the issue provider.

This matters because provider-backed workflow should prefer provider-native history over duplicating logs in issue bodies.

## Summary

Use different GitHub APIs for different history needs:

| Need | API | Notes |
| --- | --- | --- |
| Current issue body | `gh issue view --json body` or REST issue API | Current description only. |
| Relationship, label, dependency, and timeline events | REST timeline/events APIs | Good for workflow event history. |
| Description/body edit history | GraphQL `userContentEdits` | Provides body edit timestamps and diffs. |

## REST timeline

Command shape:

```bash
gh api repos/OWNER/REPO/issues/ISSUE_NUMBER/timeline --paginate
```

Observed event examples:

- `cross-referenced`
- `sub_issue_added`
- `labeled`
- `unlabeled`

Use timeline when workflow needs a broad activity stream.

## REST events

Command shape:

```bash
gh api repos/OWNER/REPO/issues/ISSUE_NUMBER/events --paginate
```

Observed event examples:

- `parent_issue_added`
- `sub_issue_added`
- `blocked_by_added`
- `blocking_added`
- `labeled`
- `unlabeled`

Use events when workflow needs structured issue event history without the full conversation timeline.

## GraphQL body edit history

REST timeline/events do not expose issue description edit diffs in the observed output.

Use GraphQL `userContentEdits` for body edit history.

Command shape:

```bash
gh api graphql \
  -f owner=OWNER \
  -f repo=REPO \
  -F number=ISSUE_NUMBER \
  -f query='
query($owner:String!, $repo:String!, $number:Int!) {
  repository(owner:$owner, name:$repo) {
    issue(number:$number) {
      number
      title
      updatedAt
      lastEditedAt
      editor { login }
      userContentEdits(first: 20) {
        nodes {
          editedAt
          editor { login }
          deletedAt
          diff
        }
      }
    }
  }
}'
```

Observed fields:

- `lastEditedAt`
- `editor.login`
- `userContentEdits.nodes[].editedAt`
- `userContentEdits.nodes[].editor.login`
- `userContentEdits.nodes[].deletedAt`
- `userContentEdits.nodes[].diff`

The `diff` field contains the edited body content diff supplied by GitHub GraphQL.

## Dogfooding observations

Issue [#28](https://github.com/studykit/studykit-plugins/issues/28) showed:

- Sub-issue additions in REST timeline/events.
- Label add/remove events in REST timeline/events.
- Body edits in GraphQL `userContentEdits`, including edits that removed duplicate `## Children` and `## Suggested Order` sections.

Issue [#30](https://github.com/studykit/studykit-plugins/issues/30) showed:

- Parent relationship history as `parent_issue_added`.
- Dependency history as `blocked_by_added` and `blocking_added`.
- Label changes as `labeled` and `unlabeled`.

## Workflow implications

- Do not duplicate routine history in `## Log` when GitHub already stores native history.
- Use comments for human discussion and work notes.
- Use timeline/events for relationship, label, status, and dependency history.
- Use GraphQL `userContentEdits` when an agent needs to inspect description/body changes.
- Provider wrappers should expose body edit history as a read operation, not as body content.
- `workdoc-finder` can use current body for summaries and timeline/events for recent activity.

## Related Guidance

- [GitHub Issues Usage For Workflow](GitHub-Issues-Usage-For-Workflow.md)

## References

- GitHub REST issue timeline events: https://docs.github.com/en/rest/issues/timeline
- GitHub REST issue events: https://docs.github.com/en/rest/issues/events
- GitHub GraphQL objects and connections: https://docs.github.com/en/graphql/reference/objects

## Change Log

- 2026-05-13 — [#37](https://github.com/studykit/studykit-plugins/issues/37) — Published curated knowledge page in repository `wiki/` directory.
