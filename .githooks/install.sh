#!/usr/bin/env bash
#
# Install git hooks for this repository
#
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"

git config core.hooksPath "$REPO_ROOT/.githooks"
chmod +x "$REPO_ROOT/.githooks/commit-msg"
chmod +x "$REPO_ROOT/.githooks/pre-commit"

echo "Git hooks installed. Using .githooks/ as hooks directory."
