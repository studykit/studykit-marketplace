# Issue Reference Links

## In markdown files (GitHub file preview)

- ID-to-issue mappings are managed in `A4/issues.yml`. Read this file to look up `repo` and issue numbers for each ID.
- Add a `<!-- references -->` section at the end of the file using the mappings from `issues.yml`:
  ```
  <!-- references -->
  [FR-1]: https://github.com/{repo}/issues/16
  [STORY-1]: https://github.com/{repo}/issues/7
  ```
- To make an ID clickable in GitHub file preview, write it as a markdown reference link `[FR-1]` or `[STORY-1]` in the body.

## In GitHub issue/PR bodies

- Reference links don't work in issue/PR bodies. Use inline links with the full issue URL instead: `[FR-1](https://github.com/{repo}/issues/16)`, `[STORY-1](https://github.com/{repo}/issues/7)`.
