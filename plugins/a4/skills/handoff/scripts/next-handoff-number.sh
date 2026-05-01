#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
handoff_dir="$repo_root/.handoff"

mkdir -p "$handoff_dir"

largest="$(
  find "$handoff_dir" -maxdepth 1 -type f -name '[0-9]*-*.md' -exec basename {} \; |
    sed -n 's/^\([0-9][0-9]*\)-.*\.md$/\1/p' |
    sort -n |
    tail -1
)"

echo $(( ${largest:-0} + 1 ))
