"""a4 hook subcommand package.

The thin dispatcher script (`../a4_hook.py`) routes each subcommand to the
matching `a4_hook.<name>` module. Subcommand modules are imported lazily
from the dispatcher so a single hook invocation only pays the import cost
of the modules it actually uses (the `post-edit` fast path fires on every
Write/Edit/MultiEdit, so this matters).

Module map:
- `_runtime`       — runtime Strategy implementations for Claude Code and
                     Codex payload shapes / output behavior.
- `_state`         — module-level constants (`PLUGIN_ROOT`, `AUTHORING_DIR`),
                     shared helpers (`record_dir`, `display_rel`, `emit`,
                     `read_status_from_disk`, `resolve_type_from_path`,
                     `unlink_silent`), and all session-state IO
                     (prestatus / injected / resolved-ids / edited).
- `_pre_edit`      — PreToolUse subcommand and authoring-contract injection.
- `_post_edit`     — PostToolUse subcommand: cascade + consistency.
- `_stop`          — Stop subcommand: validators + decision-block emission.
- `_user_prompt`   — UserPromptSubmit subcommand: `#<id>` resolution.
- `_session_start` — SessionStart subcommand: type→location map injection.

Backward-compatible aliases (resolved lazily via PEP 562 ``__getattr__``):
``a4_hook._pre_edit`` / ``_post_edit`` / ``_stop`` / ``_user_prompt`` /
``_session_start`` resolve to the matching subcommand entry-point function,
so existing tests that call ``hook_module._pre_edit()`` keep working
without an eager import that would defeat the lazy dispatcher.
"""

from __future__ import annotations

# Re-exported so tests can do `monkeypatch.setattr(hook_module.sys, ...)`.
# `sys` is a singleton, so patching its attributes affects subcommand
# modules too — they import the same `sys` object.
import sys  # noqa: F401


_SUBCOMMAND_ENTRY = {
    "_pre_edit": ("a4_hook._pre_edit", "pre_edit"),
    "_post_edit": ("a4_hook._post_edit", "post_edit"),
    "_stop": ("a4_hook._stop", "stop"),
    "_user_prompt": ("a4_hook._user_prompt", "user_prompt"),
    "_session_start": ("a4_hook._session_start", "session_start"),
}


def __getattr__(name: str):
    """Lazy alias resolver for the legacy ``hook_module._pre_edit()``-style
    test API. Each lookup imports the relevant submodule on demand and
    returns the entry-point function — no eager import of unrelated
    subcommands.
    """
    entry = _SUBCOMMAND_ENTRY.get(name)
    if entry is None:
        raise AttributeError(f"module 'a4_hook' has no attribute {name!r}")
    import importlib

    module_name, fn_name = entry
    return getattr(importlib.import_module(module_name), fn_name)
