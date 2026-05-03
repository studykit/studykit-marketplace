"""UserPromptSubmit subcommand: resolve `#<id>` references to a4/ paths.

Scans the prompt for `#<id>` references and injects resolved
`a4/<type>/<id>-<slug>.md` paths as ``additionalContext`` so Claude reads
the file directly instead of searching for it.

Dedupes within a session via a record file at
`.claude/tmp/a4-edited/a4-resolved-ids-<sid>.txt`: an id whose path
was already injected this session is skipped on subsequent prompts.
Cleanup is handled by the same SessionEnd / SessionStart-sweep hooks
that manage `a4-edited-<sid>.txt`.
"""

from __future__ import annotations

import sys
from pathlib import Path

from a4_hook._state import (
    emit,
    project_dir_from_payload,
    read_resolved_ids,
    record_resolved_ids,
)


_MAX_IDS = 20
_LOOKUP_FOLDERS: tuple[str, ...] = (
    "usecase",
    "task",
    "bug",
    "spike",
    "research",
    "review",
    "spec",
    "idea",
)


def user_prompt() -> int:
    """UserPromptSubmit entry point. Always exits 0."""
    import json
    import os
    import re

    raw = sys.stdin.read()
    if not raw:
        return 0
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return 0

    prompt = payload.get("prompt") or ""
    session_id = payload.get("session_id") or ""
    if not prompt or not session_id:
        return 0

    project_dir = project_dir_from_payload(payload)
    if not project_dir:
        return 0
    a4_dir = Path(project_dir) / "a4"
    if not a4_dir.is_dir():
        return 0

    # `#<id>`. Negative lookbehind `(?<![\w#])` rejects markdown headings
    # (`##h`, `#####`) and word-attached `#` (`abc#42`). `\b` after `\d+`
    # rejects `#42x`.
    id_pattern = re.compile(r"(?<![\w#])#(\d+)\b")

    # Dedupe in first-occurrence order; cap to bound work.
    seen: set[str] = set()
    ids: list[str] = []
    for m in id_pattern.finditer(prompt):
        token = m.group(1)
        if token in seen:
            continue
        seen.add(token)
        ids.append(token)
        if len(ids) >= _MAX_IDS:
            break
    if not ids:
        return 0

    already = read_resolved_ids(project_dir, session_id)
    fresh = [t for t in ids if t not in already]
    if not fresh:
        return 0

    project_prefix = project_dir + os.sep
    resolved: list[tuple[str, list[str]]] = []
    for token in fresh:
        matches: list[str] = []
        for folder in _LOOKUP_FOLDERS:
            sub = a4_dir / folder
            if not sub.is_dir():
                continue
            pattern = f"{token}-*.md"
            matches.extend(str(p) for p in sorted(sub.glob(pattern)))
        archive = a4_dir / "archive"
        if archive.is_dir():
            matches.extend(
                str(p) for p in sorted(archive.rglob(f"{token}-*.md"))
            )
        if matches:
            display = [
                p[len(project_prefix):] if p.startswith(project_prefix) else p
                for p in matches
            ]
            resolved.append((token, display))

    if not resolved:
        return 0

    record_resolved_ids(project_dir, session_id, [t for t, _ in resolved])

    # Terse on purpose — only the path is actionable. No header / footer:
    # `#<id> → path` is self-explanatory in context, and meta-explanation
    # (folder=type, dedupe behavior) is not re-injected on every prompt.
    lines = []
    for token, paths in resolved:
        joined = ", ".join(paths)
        lines.append(f"- #{token} → {joined}")
    emit(
        {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": "\n".join(lines),
            }
        }
    )
    return 0
