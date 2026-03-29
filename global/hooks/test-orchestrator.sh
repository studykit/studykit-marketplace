#!/usr/bin/env bash
# test-orchestrator.sh — Unit tests for the agent orchestrator hooks
# Run from project root: bash global/hooks/test-orchestrator.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# --- Test infrastructure ---

pass=0
fail=0
total=0

assert_eq() {
  local label="$1" expected="$2" actual="$3"
  total=$((total + 1))
  if [[ "$expected" == "$actual" ]]; then
    echo "  ✓ $label"
    pass=$((pass + 1))
  else
    echo "  ✗ $label"
    echo "    expected: $expected"
    echo "    actual:   $actual"
    fail=$((fail + 1))
  fi
}

assert_contains() {
  local label="$1" needle="$2" haystack="$3"
  total=$((total + 1))
  if [[ "$haystack" == *"$needle"* ]]; then
    echo "  ✓ $label"
    pass=$((pass + 1))
  else
    echo "  ✗ $label"
    echo "    expected to contain: $needle"
    echo "    actual: $haystack"
    fail=$((fail + 1))
  fi
}

assert_exit() {
  local label="$1" expected_code="$2"
  shift 2
  total=$((total + 1))
  set +e
  "$@" >/dev/null 2>&1
  local actual_code=$?
  set -e
  if [[ "$expected_code" == "$actual_code" ]]; then
    echo "  ✓ $label"
    pass=$((pass + 1))
  else
    echo "  ✗ $label"
    echo "    expected exit code: $expected_code"
    echo "    actual exit code:   $actual_code"
    fail=$((fail + 1))
  fi
}

# --- Setup ---

TMPDIR=$(mktemp -d /tmp/orchestrator-test-XXXX)
export SESSION_TREE="$TMPDIR/session-tree.json"

cleanup() {
  rm -rf "$TMPDIR"
}
trap cleanup EXIT

# ============================================================
echo ""
echo "=== 1. session-tree.sh library ==="
echo ""

source "$SCRIPT_DIR/lib/session-tree.sh"

# 1a. st_read returns default when file doesn't exist
echo "[st_read] default on missing file"
result=$(st_read)
assert_eq "returns empty children array" "0" "$(echo "$result" | jq '.children | length')"
assert_eq "mainSession is null" "null" "$(echo "$result" | jq '.mainSession')"

# 1b. st_write creates and updates the file
echo "[st_write] create and update"
st_write '.mainSession = {"conversationId":"main-1","name":"test-session"}'
assert_eq "mainSession.name written" "test-session" "$(cat "$SESSION_TREE" | jq -r '.mainSession.name')"

# 1c. st_write adds a child entry
echo "[st_write] add child entry"
st_write '.children += [{"conversationId":"child-1","topic":"test topic","status":"pending","createdAt":"2026-03-29T00:00:00Z","pid":null,"skill":"co-think-domain","transcriptPath":null,"resultPatterns":["docs/*.md","A4/**/*.requirement.md"],"resultFiles":[],"referenceFiles":["/tmp/ref.md"],"contextSummary":"Context from main session about testing"}]'
assert_eq "children count is 1" "1" "$(cat "$SESSION_TREE" | jq '.children | length')"
assert_eq "child topic" "test topic" "$(cat "$SESSION_TREE" | jq -r '.children[0].topic')"

# 1d. st_find_child finds existing child
echo "[st_find_child] existing child"
found=$(st_find_child "child-1")
assert_eq "found child conversationId" "child-1" "$(echo "$found" | jq -r '.conversationId')"
assert_eq "found child status" "pending" "$(echo "$found" | jq -r '.status')"

# 1e. st_find_child returns non-zero for missing child
echo "[st_find_child] missing child"
assert_exit "returns non-zero for missing" 1 st_find_child "nonexistent"

# 1f. st_write with empty arg fails
echo "[st_write] empty arg"
assert_exit "returns non-zero for empty arg" 1 st_write ""

# ============================================================
echo ""
echo "=== 2. session-start-bootstrap.sh ==="
echo ""

# 2a. Exits silently when SESSION_TREE is unset
echo "[bootstrap] guard on SESSION_TREE"
output=$(SESSION_TREE="" bash "$SCRIPT_DIR/session-start-bootstrap.sh" < /dev/null 2>&1 || true)
assert_eq "no output when SESSION_TREE unset" "" "$output"

# 2b. Exits silently when session_id not found
echo "[bootstrap] unknown session_id"
output=$(echo '{"session_id":"unknown-999","transcript_path":"/tmp/t.jsonl"}' | bash "$SCRIPT_DIR/session-start-bootstrap.sh" 2>&1 || true)
assert_eq "no output for unknown session" "" "$output"

# 2c. Injects context for known child
echo "[bootstrap] context injection"
output=$(echo '{"session_id":"child-1","transcript_path":"/tmp/transcript.jsonl"}' | bash "$SCRIPT_DIR/session-start-bootstrap.sh" 2>&1)
assert_contains "outputs topic" "test topic" "$output"
assert_contains "outputs reference file" "/tmp/ref.md" "$output"
assert_contains "outputs context summary" "Context from main session" "$output"
assert_contains "outputs result patterns" "docs/*.md" "$output"
assert_contains "outputs skill invocation" "co-think-domain" "$output"

# 2d. Writes back metadata and activates
echo "[bootstrap] metadata writeback"
tree=$(cat "$SESSION_TREE")
assert_eq "status changed to active" "active" "$(echo "$tree" | jq -r '.children[0].status')"
assert_eq "conversationId written" "child-1" "$(echo "$tree" | jq -r '.children[0].conversationId')"
assert_eq "transcriptPath written" "/tmp/transcript.jsonl" "$(echo "$tree" | jq -r '.children[0].transcriptPath')"
pid_val=$(echo "$tree" | jq '.children[0].pid')
assert_eq "pid is a number" "true" "$(echo "$pid_val" | jq 'type == "number"')"

# ============================================================
echo ""
echo "=== 3. post-tool-result-collector.sh ==="
echo ""

# 3a. Exits silently for non-Write tools
echo "[result-collector] ignores non-Write tools"
output=$(echo '{"session_id":"child-1","tool_name":"Read","tool_input":{"file_path":"docs/foo.md"}}' | bash "$SCRIPT_DIR/post-tool-result-collector.sh" 2>&1 || true)
files_before=$(cat "$SESSION_TREE" | jq '.children[0].resultFiles | length')
assert_eq "no files registered for Read tool" "0" "$files_before"

# 3b. Registers matching file for Write tool
echo "[result-collector] registers matching Write"
echo '{"session_id":"child-1","tool_name":"Write","tool_input":{"file_path":"docs/result.md"}}' | bash "$SCRIPT_DIR/post-tool-result-collector.sh" 2>&1 || true
files_after=$(cat "$SESSION_TREE" | jq -r '.children[0].resultFiles[0]')
assert_eq "result file registered" "docs/result.md" "$files_after"

# 3c. Does not duplicate existing file
echo "[result-collector] no duplicates"
echo '{"session_id":"child-1","tool_name":"Write","tool_input":{"file_path":"docs/result.md"}}' | bash "$SCRIPT_DIR/post-tool-result-collector.sh" 2>&1 || true
files_count=$(cat "$SESSION_TREE" | jq '.children[0].resultFiles | length')
assert_eq "no duplicate registration" "1" "$files_count"

# 3d. Ignores non-matching file
echo "[result-collector] ignores non-matching path"
echo '{"session_id":"child-1","tool_name":"Write","tool_input":{"file_path":"src/code.ts"}}' | bash "$SCRIPT_DIR/post-tool-result-collector.sh" 2>&1 || true
files_count=$(cat "$SESSION_TREE" | jq '.children[0].resultFiles | length')
assert_eq "non-matching file not registered" "1" "$files_count"

# 3e. Registers second matching pattern
echo "[result-collector] second pattern match"
echo '{"session_id":"child-1","tool_name":"Edit","tool_input":{"file_path":"A4/test/foo.requirement.md"}}' | bash "$SCRIPT_DIR/post-tool-result-collector.sh" 2>&1 || true
files_count=$(cat "$SESSION_TREE" | jq '.children[0].resultFiles | length')
assert_eq "second pattern match registered" "2" "$files_count"

# 3f. Guard on SESSION_TREE
echo "[result-collector] guard on SESSION_TREE"
output=$(SESSION_TREE="" bash "$SCRIPT_DIR/post-tool-result-collector.sh" <<< '{"session_id":"child-1","tool_name":"Write","tool_input":{"file_path":"docs/x.md"}}' 2>&1 || true)
assert_eq "no output when SESSION_TREE unset" "" "$output"

# ============================================================
echo ""
echo "=== 4. session-end-collector.sh ==="
echo ""

# 4a. Updates status to terminated
echo "[session-end] terminates child"
echo '{"session_id":"child-1"}' | bash "$SCRIPT_DIR/session-end-collector.sh" 2>&1 || true
status=$(cat "$SESSION_TREE" | jq -r '.children[0].status')
assert_eq "status is terminated" "terminated" "$status"

# 4b. Guard on SESSION_TREE
echo "[session-end] guard on SESSION_TREE"
output=$(SESSION_TREE="" bash "$SCRIPT_DIR/session-end-collector.sh" <<< '{"session_id":"child-1"}' 2>&1 || true)
assert_eq "no output when SESSION_TREE unset" "" "$output"

# 4c. Ignores unknown session
echo "[session-end] unknown session"
output=$(echo '{"session_id":"unknown-999"}' | bash "$SCRIPT_DIR/session-end-collector.sh" 2>&1 || true)
assert_eq "no error for unknown session" "" "$output"

# ============================================================
echo ""
echo "=== 5. session-monitor.sh ==="
echo ""

# Remove any leftover snapshot
rm -f "${SESSION_TREE%.json}.last"

# 5a. Detects terminated session
echo "[monitor] detects termination"
output=$(echo '{"session_id":"main-1","file_path":"'"$SESSION_TREE"'"}' | bash "$SCRIPT_DIR/session-monitor.sh" 2>&1 || true)
assert_contains "reports terminated" "terminated" "$output"
assert_contains "includes topic" "test topic" "$output"

# 5b. No output on second run (no changes)
echo "[monitor] no output when no changes"
output=$(echo '{"session_id":"main-1","file_path":"'"$SESSION_TREE"'"}' | bash "$SCRIPT_DIR/session-monitor.sh" 2>&1 || true)
assert_eq "no output on repeat" "" "$output"

# 5c. Guard on wrong file_path
echo "[monitor] ignores wrong file_path"
output=$(echo '{"session_id":"main-1","file_path":"/tmp/other.json"}' | bash "$SCRIPT_DIR/session-monitor.sh" 2>&1 || true)
assert_eq "no output for wrong path" "" "$output"

# 5d. Handshake timeout detection
echo "[monitor] handshake timeout"
rm -f "${SESSION_TREE%.json}.last"
# Add a child with pending status and old createdAt
st_write '.children += [{"conversationId":"child-timeout","topic":"stale child","status":"pending","createdAt":"2020-01-01T00:00:00Z","pid":null,"skill":null,"transcriptPath":null,"resultPatterns":[],"resultFiles":[],"referenceFiles":[],"contextSummary":null}]'
output=$(echo '{"session_id":"main-1","file_path":"'"$SESSION_TREE"'"}' | bash "$SCRIPT_DIR/session-monitor.sh" 2>&1 || true)
assert_contains "reports failed_to_start" "failed to start" "$output"
timeout_status=$(cat "$SESSION_TREE" | jq -r '.children[] | select(.conversationId == "child-timeout") | .status')
assert_eq "status updated to failed_to_start" "failed_to_start" "$timeout_status"

# 5e. Crash detection (use a known-dead PID)
echo "[monitor] crash detection"
rm -f "${SESSION_TREE%.json}.last"
st_write '.children += [{"conversationId":"child-crash","topic":"crashed child","status":"active","createdAt":"2026-03-29T00:00:00Z","pid":99999,"skill":null,"transcriptPath":null,"resultPatterns":[],"resultFiles":[],"referenceFiles":[],"contextSummary":null}]'
# PID 99999 is almost certainly not running
output=$(echo '{"session_id":"main-1","file_path":"'"$SESSION_TREE"'"}' | bash "$SCRIPT_DIR/session-monitor.sh" 2>&1 || true)
assert_contains "reports crashed" "crashed" "$output"
crash_status=$(cat "$SESSION_TREE" | jq -r '.children[] | select(.conversationId == "child-crash") | .status')
assert_eq "status updated to crashed" "crashed" "$crash_status"

# ============================================================
echo ""
echo "=== 6. iterm2.sh ==="
echo ""

# 6a. Missing required args
echo "[iterm2.sh] missing args"
iterm2_output=$(bash "$SCRIPT_DIR/lib/iterm2.sh" 2>&1 || true)
assert_contains "requires args" "required" "$iterm2_output"

# ============================================================
# Summary
echo ""
echo "========================================="
echo "Results: $pass passed, $fail failed, $total total"
echo "========================================="

if [[ $fail -gt 0 ]]; then
  exit 1
fi
