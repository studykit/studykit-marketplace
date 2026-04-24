#!/bin/bash
# Stop hook: validate all a4/ .md files edited during this session.
#   - Violations (validator rc 2) → exit 2 with stderr so Claude retries.
#   - Internal failures (missing scripts, uv errors, unexpected rc) → exit 0
#     with a stderr warning so the Stop flow is never blocked by hook bugs.
#   - stop_hook_active → exit 0 silently (avoid tight retry loops).
set -u

input=$(cat 2>/dev/null)
[[ -z "${input:-}" ]] && exit 0

session_id=$(printf '%s' "$input" | jq -r '.session_id // empty' 2>/dev/null)
[[ -z "${session_id:-}" ]] && exit 0

stop_hook_active=$(printf '%s' "$input" | jq -r '.stop_hook_active // false' 2>/dev/null)
[[ "$stop_hook_active" == "true" ]] && exit 0

project_dir="${CLAUDE_PROJECT_DIR:-}"
[[ -z "$project_dir" ]] && exit 0

a4_dir="$project_dir/a4"
[[ ! -d "$a4_dir" ]] && exit 0

record_file="$project_dir/.claude/tmp/a4-edited/a4-edited-${session_id}.txt"
[[ ! -f "$record_file" ]] && exit 0

# Collect unique still-existing files.
edited_files=()
while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  [[ ! -f "$line" ]] && continue
  case "$line" in
    "$a4_dir/"*) edited_files+=("$line") ;;
  esac
done < <(sort -u "$record_file" 2>/dev/null)

if [[ ${#edited_files[@]} -eq 0 ]]; then
  rm -f "$record_file"
  exit 0
fi

plugin_root="${CLAUDE_PLUGIN_ROOT:-}"
fm_script="$plugin_root/scripts/validate_frontmatter.py"
body_script="$plugin_root/scripts/validate_body.py"

internal_fail() {
  printf 'validate-edited-a4.sh: %s — skipping validation\n' "$1" >&2
  exit 0
}

[[ -n "$plugin_root" ]] || internal_fail "CLAUDE_PLUGIN_ROOT not set"
[[ -f "$fm_script" ]] || internal_fail "script not found: $fm_script"
[[ -f "$body_script" ]] || internal_fail "script not found: $body_script"

# Run validators once per edited file (the scripts accept a single optional
# positional file after <a4-dir>). Workspace-wide id-uniqueness is skipped in
# single-file mode — that is the user-triggered /a4:validate's job.
fm_output=""
fm_any_violation=0
body_output=""
body_any_violation=0
set +e
for f in "${edited_files[@]}"; do
  out=$(uv run "$fm_script" "$a4_dir" "$f" 2>&1)
  rc=$?
  if [[ "$rc" -eq 2 ]]; then
    fm_output+="$out"$'\n'
    fm_any_violation=1
  elif [[ "$rc" -ne 0 ]]; then
    set -u
    internal_fail "validate_frontmatter.py failed with rc=$rc on $f"
  fi

  out=$(uv run "$body_script" "$a4_dir" "$f" 2>&1)
  rc=$?
  if [[ "$rc" -eq 2 ]]; then
    body_output+="$out"$'\n'
    body_any_violation=1
  elif [[ "$rc" -ne 0 ]]; then
    set -u
    internal_fail "validate_body.py failed with rc=$rc on $f"
  fi
done
set -u

if [[ "$fm_any_violation" -eq 0 && "$body_any_violation" -eq 0 ]]; then
  rm -f "$record_file"
  exit 0
fi

{
  echo "a4/ validators found issues in files edited this session:"
  if [[ "$fm_any_violation" -ne 0 ]]; then
    echo
    echo "--- validate_frontmatter.py ---"
    printf '%s' "$fm_output"
  fi
  if [[ "$body_any_violation" -ne 0 ]]; then
    echo
    echo "--- validate_body.py ---"
    printf '%s' "$body_output"
  fi
  echo
  echo "Fix the issues above before stopping. See plugins/a4/references/frontmatter-schema.md and obsidian-conventions.md."
  echo "For a full workspace sweep (id uniqueness etc.), run /a4:validate."
} >&2
exit 2
