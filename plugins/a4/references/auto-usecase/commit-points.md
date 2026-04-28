# auto-usecase Commit Points

All commit subjects follow `../commit-message-convention.md`. Stage files under `a4/`.

## Timing

- **After Step 2** — research / code-analysis reports, one commit:
  ```
  docs(a4): research similar systems for <topic>
  ```
  (ID-less: research reports under `a4/research/` carry no a4 workspace id.)

- **After Step 3a (each compose)** — UC files + wiki pages + any `kind: question` review items:
  ```
  #<uc-ids> [#<question-review-ids>] docs(a4): auto-usecase compose growth <N>
  ```
  Body bullet: `- UCs: <total> (<added> added)`.

- **After each quality round** — reviewer-emitted review items + reviser edits to UC files:
  ```
  #<revised-uc-ids> #<written-review-ids> docs(a4): auto-usecase growth <N> review <round>
  ```
  Body bullets: `- UCs: <total> (<revised> revised)` / `- Review items: <written>/<resolved>/<deferred>`.

- **After Step 3d exploration** — exploration report + any new `kind: gap` review items:
  ```
  #<gap-review-ids> docs(a4): auto-usecase exploration growth <N>
  ```
  (ID-less subject when zero gap items were emitted; the exploration report itself is under `a4/research/` and carries no id.)
  Body bullet: `- UC candidates: <count>`.

- **Final** — summary commit if anything remains unstaged. Subject form depends on what's staged; default to `chore(a4): auto-usecase wrap up` when only ambient updates remain.
