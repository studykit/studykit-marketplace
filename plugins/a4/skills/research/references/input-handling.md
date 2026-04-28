# Input Handling + Working File Path

## Resolve the argument

Resolve the argument to `(mode, candidates)`:

1. **File path** (`a4/spark/...brainstorm.md`, `a4/idea/<id>-<slug>.md`, any `.md`): read the file, extract candidates. Present to the user: "Here's what I found. Which do you want to research?" The user's answer determines the final list; 2+ items → `comparative`, 1 → `single`.
2. **Comma / `vs` separated list** (e.g., `React vs Svelte vs Vue`, `Postgres, MySQL, SQLite`): parse into a list, confirm, `comparative`.
3. **Single topic or question** (e.g., `gRPC streaming semantics`, `how does RocksDB handle compaction`): confirm the question, `single`.

If the input is ambiguous, ask the user for mode + scope before creating the file.

## Working file path

1. Derive the slug from the topic (kebab-case, ASCII + CJK allowed, trim to ~40 chars).
2. Ensure `./research/` exists; create with `mkdir -p` if missing.
3. Resolve collisions: if `./research/<slug>.md` exists, try `-2`, `-3`, … until free. Tell the user about the suffix.
4. File path: `./research/<slug>.md` relative to the current working directory.

Report the full path as soon as the file is created: "Research file started at `<path>`. It will update as we go."
