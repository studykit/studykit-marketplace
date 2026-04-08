---
name: register-result
description: Register deliverable files from this child session
disable-model-invocation: true
argument-hint: <file1> [file2] ...
---
!`uv run ${CLAUDE_SKILL_DIR}/scripts/register_result.py ${CLAUDE_SESSION_ID} $ARGUMENTS`
