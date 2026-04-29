"""Cross-file status consistency validator (library).

Some status enum values are semantically derived from cross-file state:

  - ``spec.status = "superseded"`` iff another ``spec/*.md`` at
    ``status: active`` declares ``supersedes: [<this-path>]``.
  - ``usecase.status = "superseded"`` iff another ``usecase/*.md`` at
    ``status: shipped`` declares ``supersedes: [<this-path>]``.
  - ``task.status = "discarded"`` iff every UC in the task's
    ``implements:`` is at ``status: discarded``.
  - ``review.status = "discarded"`` iff the review's ``target:`` points
    at a usecase with ``status: discarded``.
  - ``idea.status = "promoted"`` iff own ``promoted:`` list is
    non-empty.
  - ``spark/*.brainstorm.md`` ``status = "promoted"`` iff own
    ``promoted:`` list is non-empty.

These are normally materialized by ``scripts/transition_status.py``.
This validator is the safety net — it catches drift left behind if a
writer was skipped, bypassed, or ran before the successor reached its
terminal-active state. Report-only; no file is mutated.

Two modes:

  Workspace mode — scan every spec/usecase/idea/brainstorm file and
  report all mismatches.

  File-scoped mode — report only mismatches involving the given file's
  "related set":

    - ``idea/<id>-<slug>.md``       — that file only.
    - ``spark/<...>.brainstorm.md`` — that file only.
    - ``spec/<id>-<slug>.md``       — that file + files it supersedes
                                      + files that supersede it
                                      (connected component via
                                      ``supersedes:``).
    - ``usecase/<id>-<slug>.md``    — same as spec, walked via
                                      usecase-to-usecase
                                      ``supersedes:``.
    - anything else                 — no output.

Pure library — no stdout / stderr / exit. The unified CLI
``scripts/validate.py`` adapts ``run`` output to ``Issue`` via
``markdown_validator.registry`` and owns presentation / exit codes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from common import (
    is_non_empty_list as _is_non_empty_list,
    iter_issue_files,
)
from markdown import extract_preamble

from .refs import RefIndex


@dataclass(frozen=True)
class Mismatch:
    path: str
    rule: str
    message: str


def _fm(path: Path) -> dict | None:
    return extract_preamble(path).fm


# Families for which a `superseded` status is actively materialized by
# transition_status.py when a successor reaches its terminal-active
# state. Both sides must be same-family — a spec does not supersede
# a usecase and vice versa.
SUPERSEDES_FAMILIES: dict[str, str] = {
    "spec": "active",
    "usecase": "shipped",
}


def collect_family(a4_dir: Path, family: str) -> dict[str, dict]:
    """Map ``<family>/<id>-<slug>`` → frontmatter for every .md in folder.

    For nested issue folders (e.g. ``task/{feature,bug,spike}/``),
    descends into kind subfolders. The reference-key form drops the
    kind segment so refs stay stable when a task is moved between
    kinds.
    """
    out: dict[str, dict] = {}
    for p in iter_issue_files(a4_dir, family):
        fm = _fm(p)
        if fm is None:
            continue
        key = f"{family}/{p.stem}"
        out[key] = fm
    return out


def collect_specs(a4_dir: Path) -> dict[str, dict]:
    """Back-compat alias for ``collect_family(a4_dir, "spec")``."""
    return collect_family(a4_dir, "spec")


def collect_with_promoted(
    a4_dir: Path, subfolder: str, file_glob: str
) -> list[tuple[str, dict]]:
    """Return ``(rel_ref, frontmatter)`` for items in a folder.

    ``rel_ref`` is the reference form
    (``folder/<basename-without-.md>``).
    """
    out: list[tuple[str, dict]] = []
    folder = a4_dir / subfolder
    if not folder.is_dir():
        return out
    for p in sorted(folder.glob(file_glob)):
        fm = _fm(p)
        if fm is None:
            continue
        out.append((f"{subfolder}/{p.stem}", fm))
    return out


def check_superseded(
    items: dict[str, dict], family: str, index: RefIndex
) -> list[Mismatch]:
    """Check supersedes-↔-status consistency within a single family.

    A target artifact is expected to be at ``status: superseded`` iff
    it is named in the ``supersedes:`` list of another artifact in the
    same family that is itself at its terminal-active status
    (spec=active, usecase=shipped). Draft/implementing successors do
    NOT yet render their targets superseded.

    All ref comparisons go through ``index.canonical`` so the new
    short forms (``#<id>``, ``<folder>/<id>``) match the canonical
    ``<folder>/<id>-<slug>`` keys in ``items``.
    """
    mismatches: list[Mismatch] = []
    terminal_active = SUPERSEDES_FAMILIES.get(family)
    if terminal_active is None:
        return mismatches

    # Build: for each target key (canonical), the list of live-successor
    # keys that claim to supersede it.
    superseded_by: dict[str, list[str]] = {}
    for key, fm in items.items():
        supersedes = fm.get("supersedes")
        if not isinstance(supersedes, list):
            continue
        successor_status = fm.get("status")
        if successor_status != terminal_active:
            continue
        for entry in supersedes:
            canon = index.canonical(entry)
            if canon is None:
                continue
            superseded_by.setdefault(canon, []).append(key)

    for key, fm in items.items():
        status = fm.get("status")
        is_targeted = key in superseded_by

        if status == "superseded" and not is_targeted:
            mismatches.append(
                Mismatch(
                    path=f"{key}.md",
                    rule=f"stale-superseded-status-{family}",
                    message=(
                        f"status=superseded but no {terminal_active!r} "
                        f"{family} declares `supersedes: [{key}]`"
                    ),
                )
            )
        elif status != "superseded" and is_targeted:
            superseders = sorted(superseded_by[key])
            mismatches.append(
                Mismatch(
                    path=f"{key}.md",
                    rule=f"missing-superseded-status-{family}",
                    message=(
                        f"status={status!r} but superseded by {superseders} "
                        f"(each at {terminal_active!r}). Expected "
                        "status=superseded — transition_status.py should "
                        "have flipped this; re-run it against the successor."
                    ),
                )
            )

    for key, fm in items.items():
        supersedes = fm.get("supersedes")
        if not isinstance(supersedes, list):
            continue
        for entry in supersedes:
            canon = index.canonical(entry)
            if canon is None or canon not in items:
                # Show the original entry in the message so the user can
                # find it; canonical may be None when the ref does not
                # resolve at all (also caught by frontmatter
                # `unresolved-ref`).
                shown = canon if canon is not None else entry
                mismatches.append(
                    Mismatch(
                        path=f"{key}.md",
                        rule=f"superseded-target-missing-{family}",
                        message=(
                            f"`supersedes: [{shown}]` points at a {family} "
                            "that does not exist in the workspace"
                        ),
                    )
                )

    return mismatches


def check_discarded_cascade(
    a4_dir: Path,
    usecases: dict[str, dict],
    index: RefIndex,
) -> list[Mismatch]:
    """Flag drift when a UC is ``discarded`` but its cascades did not run.

    - task: each task with ``implements: [usecase/<discarded>]`` where
      all implemented UCs are discarded is expected at ``discarded``
      too.
    - review: each review with ``target:`` containing a discarded UC at
      ``open`` or ``in-progress`` is expected at ``discarded``.
    """
    mismatches: list[Mismatch] = []
    discarded_uc_keys = {
        key for key, fm in usecases.items()
        if fm.get("status") == "discarded"
    }
    if not discarded_uc_keys:
        return mismatches

    task_files = iter_issue_files(a4_dir, "task")
    if task_files:
        for p in task_files:
            fm = _fm(p)
            if fm is None:
                continue
            implements = fm.get("implements") or []
            if not isinstance(implements, list) or not implements:
                continue
            implemented_keys = {index.canonical(x) for x in implements}
            implemented_keys.discard(None)
            if not implemented_keys or not implemented_keys.issubset(discarded_uc_keys):
                continue
            status = fm.get("status")
            if status == "discarded":
                continue
            mismatches.append(
                Mismatch(
                    path=f"task/{p.stem}.md",
                    rule="missing-discarded-status-task",
                    message=(
                        f"status={status!r} but every UC this task "
                        f"implements is discarded. Expected "
                        "status=discarded — transition_status.py should "
                        "have cascaded from the UC discard."
                    ),
                )
            )

    for p in iter_issue_files(a4_dir, "review"):
        fm = _fm(p)
        if fm is None:
            continue
        target_raw = fm.get("target")
        target_entries: list = []
        if isinstance(target_raw, list):
            target_entries = target_raw
        elif isinstance(target_raw, str):
            target_entries = [target_raw]
        canon_targets = {index.canonical(t) for t in target_entries}
        canon_targets.discard(None)
        hit = canon_targets & discarded_uc_keys
        if not hit:
            continue
        status = fm.get("status")
        if status in {"discarded", "resolved"}:
            continue
        mismatches.append(
            Mismatch(
                path=f"review/{p.stem}.md",
                rule="missing-discarded-status-review",
                message=(
                    f"status={status!r} but target {sorted(hit)!r} is "
                    f"discarded. Expected status=discarded — "
                    "transition_status.py should have cascaded."
                ),
            )
        )

    return mismatches


def check_promoted(items: list[tuple[str, dict]], kind: str) -> list[Mismatch]:
    mismatches: list[Mismatch] = []
    for key, fm in items:
        status = fm.get("status")
        has_entries = _is_non_empty_list(fm.get("promoted"))

        if status == "promoted" and not has_entries:
            mismatches.append(
                Mismatch(
                    path=f"{key}.md",
                    rule=f"empty-promoted-list-{kind}",
                    message=(
                        "status=promoted but `promoted:` list is empty. "
                        "Populate with the target artifact path(s) or revert "
                        "the status."
                    ),
                )
            )
        elif status != "promoted" and has_entries:
            mismatches.append(
                Mismatch(
                    path=f"{key}.md",
                    rule=f"missing-promoted-status-{kind}",
                    message=(
                        f"status={status!r} but `promoted:` is populated. "
                        "Expected status=promoted."
                    ),
                )
            )
    return mismatches


def collect_workspace_mismatches(
    a4_dir: Path, index: RefIndex | None = None
) -> list[Mismatch]:
    if index is None:
        index = RefIndex(a4_dir)
    ideas = collect_with_promoted(a4_dir, "idea", "*.md")
    brainstorms = collect_with_promoted(a4_dir, "spark", "*.brainstorm.md")

    mismatches: list[Mismatch] = []
    usecases: dict[str, dict] = {}
    for family in SUPERSEDES_FAMILIES:
        items = collect_family(a4_dir, family)
        mismatches.extend(check_superseded(items, family, index))
        if family == "usecase":
            usecases = items
    if usecases:
        mismatches.extend(check_discarded_cascade(a4_dir, usecases, index))
    mismatches.extend(check_promoted(ideas, "idea"))
    mismatches.extend(check_promoted(brainstorms, "brainstorm"))
    return mismatches


def _supersedes_component(
    items: dict[str, dict], key: str, index: RefIndex
) -> set[str]:
    """Walk the supersedes chain within a single family, both directions."""
    component = {key}
    fm = items.get(key)
    if fm is not None:
        for entry in fm.get("supersedes") or []:
            canon = index.canonical(entry)
            if canon:
                component.add(canon)
    for other_key, other_fm in items.items():
        for entry in other_fm.get("supersedes") or []:
            if index.canonical(entry) == key:
                component.add(other_key)
                break
    return component


def collect_file_mismatches(a4_dir: Path, rel_file: str) -> list[Mismatch]:
    """Return mismatches in the connected component of ``rel_file``.

    ``rel_file`` is workspace-relative: ``spec/1-x.md``,
    ``idea/3-y.md``, ``spark/2026-04-24-1200-z.brainstorm.md``.
    Anything else returns ``[]``.
    """
    parts = rel_file.split("/", 1)
    if len(parts) < 2:
        return []
    folder, basename = parts[0], parts[1]

    if folder == "idea":
        if not basename.endswith(".md"):
            return []
        abs_path = a4_dir / rel_file
        if not abs_path.is_file():
            return []
        fm = _fm(abs_path)
        if fm is None:
            return []
        return check_promoted([(f"idea/{abs_path.stem}", fm)], "idea")

    if folder == "spark":
        if not basename.endswith(".brainstorm.md"):
            return []
        abs_path = a4_dir / rel_file
        if not abs_path.is_file():
            return []
        fm = _fm(abs_path)
        if fm is None:
            return []
        return check_promoted([(f"spark/{abs_path.stem}", fm)], "brainstorm")

    if folder in SUPERSEDES_FAMILIES:
        if not basename.endswith(".md"):
            return []
        index = RefIndex(a4_dir)
        items = collect_family(a4_dir, folder)
        stem = basename[:-3]
        key = f"{folder}/{stem}"
        component = _supersedes_component(items, key, index)
        component_paths = {f"{k}.md" for k in component}
        return [
            m
            for m in check_superseded(items, folder, index)
            if m.path in component_paths
        ]

    return []


def run(a4_dir: Path, file: str | None = None) -> list[Mismatch]:
    """Library API: workspace or file-scoped consistency check.

    When ``file`` is given, restrict to the connected component of that
    workspace-relative path (file-scope semantics in
    ``markdown_validator.registry``). Pure — no stdout/stderr/exit.
    """
    if file:
        return collect_file_mismatches(a4_dir, file)
    return collect_workspace_mismatches(a4_dir)
