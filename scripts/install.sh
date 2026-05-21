#!/usr/bin/env bash
# Bootstrap dotclaude into a project without the interactive /plugin flow.
#
# Adds the marketplace + enables the plugin via the Claude Code CLI (if present),
# then scaffolds the project-local layer with the bundled sync engine.
#
# Usage:  scripts/install.sh [target-project-dir] [-- <sync.py flags>]
# Run from a clone of this repo. Re-runnable.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLUGIN_DIR="$REPO_ROOT/plugins/dotclaude"
SYNC="$PLUGIN_DIR/skills/dotclaude-init/sync.py"

TARGET="${1:-$PWD}"
case "${1:-}" in --) TARGET="$PWD";; esac
shift || true
[ "${1:-}" = "--" ] && shift || true

echo "dotclaude bootstrap → $TARGET"

if command -v claude >/dev/null 2>&1; then
  claude plugin marketplace add "$REPO_ROOT" 2>/dev/null || true
  claude plugin install "dotclaude@dotclaude" 2>/dev/null || true
else
  echo "note: 'claude' CLI not found — skipping marketplace/plugin registration."
  echo "      The engine (hooks/agents/skills) needs the plugin installed; see README."
fi

CLAUDE_PROJECT_DIR="$TARGET" python3 "$SYNC" "$@"
